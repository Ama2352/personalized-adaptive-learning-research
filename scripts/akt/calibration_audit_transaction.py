"""Wrapper CPU audit trong process riêng, giữ nguyên source KT và validation.

Audit raw đã có chỉ dùng sau khi writer cũ kết thúc. Source SHA của wrapper
được ghi riêng vì inference_source_identity tiếp tục ghim source KT đã frozen.
"""
from contextlib import contextmanager
import json
import re
from pathlib import Path
import time

from knowledge_tracing.akt import prediction
from knowledge_tracing.akt.provenance import sha256_file
from knowledge_tracing.akt.cloud_calibration_fit import _volume_input
from knowledge_tracing.akt.research_junyi_calibration import CalibrationFitArtifactRoot, _source_pins
from knowledge_tracing.akt.research_junyi_data import iter_junyi_phase_learners


@contextmanager
def transactional_expected_insert():
    """Dùng helper gốc trong một transaction, restore hook khi thoát."""
    original = prediction._expected_insert

    def insert(con, factory):
        con.execute('BEGIN TRANSACTION')
        try:
            count = original(con, factory)
            con.execute('COMMIT')
            return count
        except BaseException:
            con.execute('ROLLBACK')
            raise

    prediction._expected_insert = insert
    try:
        yield
    finally:
        prediction._expected_insert = original


def resume_completed_raw_audit(raw, paths, view, *, binding, population, source_pins,
        expected_manifest_sha256, writer_closed_marker, expected_writer_closed_sha256,
        artifact_root, receipt_output):
    """Tiếp tục audit cùng Parquet bytes sau writer-stop, không phát sinh predictions."""
    if type(artifact_root) is not CalibrationFitArtifactRoot:
        raise ValueError('typed cloud artifact root required')
    receipt_output = artifact_root.validate_output(receipt_output)
    root = Path(artifact_root.root).resolve(strict=True)
    raw = Path(raw).absolute()
    manifest_path = _volume_input(raw / 'manifest.json', root)
    marker = _volume_input(writer_closed_marker, root)
    if sha256_file(marker) != expected_writer_closed_sha256:
        raise ValueError('pinned closed writer receipt required')
    match = re.fullmatch(r'(a[0-3])-raw-([A-Za-z0-9][A-Za-z0-9._-]{0,47})', raw.parent.parent.name)
    if match is None or raw.name != 'raw' or raw.parent.name != 'payloads':
        raise ValueError('run-owned raw recovery path required')
    expected_operation = raw.parents[2] / (match[1] + '-cpu-join-operation-' + match[2]) / 'payloads'
    closed = json.loads(marker.read_text(encoding='utf-8'))
    if closed.get('kind') == 'MODAL_CPU_WRITER_STOPPED_V1':
        config_path = _volume_input(expected_operation / 'config.json', root)
        config = json.loads(config_path.read_text(encoding='utf-8'))
        authorization = config['authorization']
        if (closed.get('status') != 'APP_STOPPED' or type(closed.get('tasks')) is not int
                or closed['tasks'] != 0 or closed.get('stage') != 'cpu-join'
                or not re.fullmatch(r'ap-[A-Za-z0-9]+', closed.get('app_id', ''))
                or closed.get('run_id') != raw.parents[2].name
                or closed.get('operation_tranche') != expected_operation.parent.name
                or closed.get('allocation_id') != match[2]
                or closed.get('request_sha256') != authorization['request_sha256']
                or closed.get('operation_config_sha256') != sha256_file(config_path)
                or authorization['allocation_id'] != match[2] or authorization['stage'] != 'cpu-join'
                or config['stage'] != 'cpu-join' or config['request']['run_id'] != raw.parents[2].name
                or config['request']['variant'] != match[1].upper()):
            raise ValueError('external stop receipt must bind stopped app tasks0 and original writer authorization')
    elif (marker.name not in ('FAILED.json', 'COMPLETE.json')
            or marker.parent != expected_operation or closed.get('stage') != 'cpu-join'):
        raise ValueError('closed marker must belong to this raw writer attempt')
    if sha256_file(manifest_path) != expected_manifest_sha256:
        raise ValueError('raw manifest changed before recovery')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    identity = manifest['identity']
    view.assert_integrity()
    if (view.scope != 'calibration_predict' or not view.full_role_coverage
            or manifest['status'] not in ('incomplete', 'complete') or identity['phase'] != 'junyi_response_calibration'
            or identity['checkpoint'] != binding.checkpoint_sha256
            or identity['inference_source'] != binding.model_source_sha256
            or identity['population'] != population['identity']
            or manifest['prediction_rows'] != population['targets']
            or len(manifest['completed_users']) != len(view.users)
            or set(manifest['completed_users']) != set(view.users)):
        raise ValueError('complete learner population and frozen raw identity required')
    if (manifest['status'] == 'complete'
            and (manifest.get('expected_rows') != population['targets']
                 or manifest.get('unique_users') != len(view.users)
                 or manifest.get('output_coverage') != 1.0)):
        raise ValueError('completed raw export lacks full audited coverage')
    for name in ('canonical', 'assignments', 'canonical_manifest', 'split_manifest'):
        _volume_input(getattr(paths, name), root)
    _source_pins(paths, source_pins)
    source = json.loads(paths.canonical_manifest.read_text(encoding='utf-8'))
    if (source.get('purpose') != 'JUNYI_REFIT90_RESPONSE_CALIBRATION_SOURCE'
            or source.get('roles_identity') != view.roles.identity
            or source.get('phase_identity') != view.identity
            or source.get('encoding_identity') != binding.vocabulary_sha256
            or any(source.get(name) is not False for name in ('train_events_included',
                'selection_events_included', 'outer_events_included', 'holdout_events_included'))):
        raise ValueError('calibration10-only source required before recovery reader')
    shards = {}
    for entry in manifest['shards']:
        name = entry['path']
        if Path(name).name != name or name in shards or not name.endswith('.parquet'):
            raise ValueError('unique raw shard basename required')
        path = _volume_input(raw / name, root)
        shards[name] = dict(bytes=path.stat().st_size, sha256=sha256_file(path))
    if sum(entry['rows'] for entry in manifest['shards']) != population['targets']:
        raise ValueError('raw shard target count mismatch')
    if {path.name for path in raw.glob('part-*.parquet')} != set(shards):
        raise ValueError('unlisted raw Parquet must be preserved for separate review')
    if any((raw / '.pending').glob('*.parquet.tmp')):
        raise ValueError('unlisted pending artifacts must be preserved for separate review')
    receipt_output.mkdir(parents=True, exist_ok=False)
    prediction._write_json_atomic(receipt_output / 'BEFORE_MANIFEST.json', manifest)
    prediction._write_json_atomic(receipt_output / 'config.json', dict(
        method='original_export_predictions_empty_stream_with_expected_transaction',
        worker_source_sha256=sha256_file(Path(__file__)),
        writer_closed_sha256=expected_writer_closed_sha256,
        before_manifest_sha256=expected_manifest_sha256, source_pins=source_pins, shards=shards))
    scratch = {}
    for name in ('.audit.tmp.duckdb', '.audit.tmp.duckdb.wal'):
        path = raw / name
        if path.exists():
            _volume_input(path, root)
            scratch[name] = dict(bytes=path.stat().st_size, sha256=sha256_file(path))
    if scratch:
        saved = receipt_output / 'before-audit'
        saved.mkdir()
        for name, pin in scratch.items():
            (raw / name).rename(saved / name)
            if sha256_file(saved / name) != pin['sha256']:
                raise ValueError('prior audit scratch changed during preservation')
    prediction._write_json_atomic(receipt_output / 'BEFORE_AUDIT_FILES.json', scratch)
    prepare = prediction._prepare_output

    def prepare_pinned(output_dir, *, artifact_root=None):
        if Path(output_dir).absolute() != raw or artifact_root is not None:
            raise ValueError('recovery output hook only admits the pinned physical raw directory')
        if sha256_file(manifest_path) != expected_manifest_sha256:
            raise ValueError('raw manifest changed before expected-row audit')
        return raw, manifest_path

    started = time.monotonic()
    prediction._prepare_output = prepare_pinned
    try:
        with transactional_expected_insert():
            result = prediction.export_predictions(iter(()), raw,
                expected_learners_factory=lambda: iter_junyi_phase_learners(paths, view), identity=identity)
        for name, pin in shards.items():
            if sha256_file(raw / name) != pin['sha256']:
                raise ValueError('raw shard bytes changed during recovery')
        _source_pins(paths, source_pins)
        receipt = dict(status='CPU_RAW_AUDIT_RECOVERED_IDENTICAL_PARQUET',
            raw_manifest_sha256=sha256_file(manifest_path), prediction_rows=result['prediction_rows'],
            shards=len(shards), seconds=time.monotonic()-started)
        prediction._write_json_atomic(receipt_output / 'COMPLETE.json', receipt)
        return receipt
    except BaseException as exc:
        prediction._write_json_atomic(receipt_output / 'FAILED.json', dict(
            error_type=type(exc).__name__, seconds=time.monotonic()-started))
        raise
    finally:
        prediction._prepare_output = prepare


def recover_cpu_calibration(request, root, *, gpu_result, raw_source_pin, closed_marker_pin,
        attempt_id, publish, volume_commit):
    """Recovery CPU audit→archives→V1 từ raw đã có, dùng metadata và callback CPU."""
    import zipfile
    from dataclasses import asdict
    from calibration_cloud_worker import (validate_request, load_inputs, pinned,
        cpu_tranches, archive_numeric_snapshot)
    from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
    from knowledge_tracing.akt.research_junyi_numeric_predictions import NumericBinding
    from knowledge_tracing.akt.research_junyi_inference import _identity
    from knowledge_tracing.akt.cloud_calibration_fit import fit_volume_calibration
    from knowledge_tracing.akt.filesystem import publish_new_file
    from knowledge_tracing.response_calibration import PredictionBinding

    validate_request(request, 'cpu-join')
    if not callable(publish) or not callable(volume_commit):
        raise ValueError('CPU publication and durable Volume callbacks required')
    root = Path(root).resolve(strict=True)
    assets_by_variant, paths, population = load_inputs(request, root)
    assets = assets_by_variant[request['variant']]
    if inference_source_identity() != request['source_identity']:
        raise ValueError('frozen inference source changed before CPU recovery')
    raw_manifest = pinned(raw_source_pin, root)
    if raw_manifest.name != 'manifest.json':
        raise ValueError('existing raw manifest pin required')
    raw = raw_manifest.parent
    if not raw.parent.parent.name.startswith(request['variant'].lower()+'-raw-'):
        raise ValueError('recovery raw variant differs from request')
    close = pinned(closed_marker_pin, root)
    gpu_receipt = pinned(dict(path=gpu_result['receipt_path'], sha256=gpu_result['receipt_sha256']), root)
    numeric = json.loads(gpu_receipt.read_text(encoding='utf-8'))
    numeric_binding = NumericBinding(**numeric['binding'])
    numeric_binding.validate()
    cache = json.loads(pinned(request['cache_receipt'], root).read_text(encoding='utf-8'))
    encoding, view = assets['encoding'], assets['calibration']
    binding = PredictionBinding(assets['index']['model'], assets['index']['checkpoint_sha256'],
        encoding.identity, view.roles.identity,
        _identity(dict(domain='junyi_exercises', values=encoding.native.vocabulary.values)),
        _identity(dict(domain='junyi_logged_response', reference_bank='not_applicable')),
        request['source_identity'], cache['source_data_sha256'])
    old_config_path = _volume_input(raw.parent / 'config.json', root)
    old_config = json.loads(old_config_path.read_text(encoding='utf-8'))
    expected_graph = None
    if request['variant'] != 'A0':
        from knowledge_tracing.akt.research_junyi_graph_cache import _digest, FORMAT
        graph = cache['graphs'][request['variant']]
        expected_graph = _digest((FORMAT, graph['sha256'], json.dumps(graph['binding'], sort_keys=True)))
    if (old_config['binding'] != asdict(binding) or old_config['numeric_binding'] != asdict(numeric_binding)
            or old_config['gpu_receipt_sha256'] != gpu_result['receipt_sha256']
            or old_config['population_identity'] != population['identity']
            or old_config['source_pins'] != request['source_pins']
            or old_config['counts'] != numeric['counts']
            or old_config['window_admission_sha256'] != cache['windows']['admission_sha256']
            or numeric['status'] != 'COMPLETE' or numeric['kind'] != 'JUNYI_CACHED_NUMERIC_INFERENCE_V1'
            or numeric_binding.variant != request['variant']
            or numeric_binding.checkpoint_sha256 != binding.checkpoint_sha256
            or numeric_binding.checkpoint_id != binding.checkpoint_sha256
            or numeric_binding.source_sha256 != request['source_identity']
            or numeric_binding.encoding_sha256 != encoding.identity
            or numeric_binding.phase_sha256 != view.identity
            or numeric_binding.window_manifest_sha256 != cache['windows']['manifest_sha256']
            or numeric['dataset_sha256'] != population['identity']
            or numeric['source_data_sha256'] != cache['source_data_sha256']
            or numeric['source_data_sha256'] != sha256_file(paths.canonical)
            or numeric['roles_sha256'] != view.roles.identity
            or numeric['window_admission_sha256'] != cache['windows']['admission_sha256']
            or numeric['graph_cache_identity'] != expected_graph):
        raise ValueError('original raw/GPU/cache/refit recovery bindings mismatch')
    cloud = CalibrationFitArtifactRoot(root)
    tranches = cpu_tranches(request['variant'], attempt_id)
    audit_output = root / request['run_id'] / (request['variant'].lower()+'-audit-'+attempt_id) / 'payloads'
    audited = resume_completed_raw_audit(raw, paths, view, binding=binding, population=population,
        source_pins=request['source_pins'], expected_manifest_sha256=raw_source_pin['sha256'],
        writer_closed_marker=close, expected_writer_closed_sha256=closed_marker_pin['sha256'],
        artifact_root=cloud, receipt_output=audit_output)
    volume_commit()
    publications = []

    def durable_publish(publication):
        volume_commit()
        receipt = publish(publication)
        publications.append(receipt)
        return receipt

    durable_publish(archive_numeric_snapshot(request, numeric, gpu_receipt, root, attempt_id=attempt_id))
    payloads = root / request['run_id'] / tranches['raw'] / 'payloads'
    cloud.validate_output(payloads)
    payloads.mkdir(parents=True, exist_ok=False)
    prediction._write_json_atomic(payloads/'config.json', dict(request=request,
        recovery_source_raw=str(raw), before_raw_manifest_sha256=raw_source_pin['sha256'],
        old_raw_config_sha256=sha256_file(old_config_path), audit=audited,
        worker_source_sha256=sha256_file(Path(__file__))))
    manifest = json.loads(raw_manifest.read_text(encoding='utf-8'))
    names = ['manifest.json', *(entry['path'] for entry in manifest['shards'])]
    inventory = {name: dict(bytes=(raw/name).stat().st_size, sha256=sha256_file(raw/name)) for name in names}
    encoded = json.dumps(inventory, sort_keys=True)
    estimated = sum(pin['bytes'] for pin in inventory.values()) + len(encoded.encode()) + 512
    estimated += sum(2*len(('raw/'+name).encode())+200 for name in names)
    if estimated > 2*1024**3:
        raise ValueError('recovered raw archive exceeds2GiB cap')
    partial = payloads/'RAW_EXPORT.zip.partial'
    with zipfile.ZipFile(partial, 'x', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for name in names:
            archive.write(raw/name, 'raw/'+name)
            if sha256_file(raw/name) != inventory[name]['sha256']:
                raise ValueError('recovered raw bytes changed while packing')
        archive.writestr('INVENTORY.json', encoded)
    archive_path = payloads/'RAW_EXPORT.zip'
    if partial.stat().st_size > 2*1024**3:
        raise ValueError('recovered raw archive actual byte cap exceeded')
    publish_new_file(partial, archive_path)
    prediction._write_json_atomic(payloads/'COMPLETE.json', dict(status='RECOVERED_RAW_ARCHIVE_COMPLETE',
        raw_manifest_sha256=sha256_file(raw_manifest), archive_sha256=sha256_file(archive_path),
        total_targets=manifest['prediction_rows'], original_raw_path=str(raw)))
    files = ['config.json', 'RAW_EXPORT.zip', 'COMPLETE.json']
    total = sum((payloads/name).stat().st_size for name in files)
    if total > 2*1024**3:
        raise ValueError('recovery raw publish exceeds2GiB cap')
    durable_publish(dict(run_id=request['run_id'], tranche_id=tranches['raw'], files=files, max_total_bytes=total))
    fitted = fit_volume_calibration(raw, paths, view, binding=binding, population=population,
        expected_population_identity=population['identity'], expected_manifest_sha256=sha256_file(raw_manifest),
        shard_sha256={entry['path']:sha256_file(raw/entry['path']) for entry in manifest['shards']},
        source_pins=request['source_pins'], max_targets=population['targets'],
        max_learner_events=request['cpu_budget']['max_learner_events'], artifact_root=cloud,
        run_id=request['run_id'], tranche_id=tranches['fit'])
    durable_publish(fitted['publish_request'])
    return dict(status='CPU_CALIBRATION_RECOVERY_PUBLISHED', calibration_identity=fitted['calibration_identity'],
        audit=audited, publish_receipts=publications)
