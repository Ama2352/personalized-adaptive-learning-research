"""Nối shard numeric GPU với metadata calibration trên CPU, xuất raw rồi fit V1.

Caller cung cấp snapshot GPU đã đóng và pin SHA bên ngoài. Module không dựng
model, không nhập Torch, không tạo cloud resource hoặc gọi Drive.
"""
from dataclasses import asdict
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

from .cloud_calibration_fit import fit_volume_calibration, _identifier, _volume_input
from .prediction import export_predictions, _write_json_atomic
from .filesystem import publish_new_file
from .prediction_batch import prepare_prediction_windows
from .provenance import sha256_file
from .research_junyi_calibration import (
    CalibrationFitArtifactRoot, iter_calibration_observations, _source_pins)
from .research_junyi_data import iter_junyi_phase_learners
from .research_junyi_numeric_predictions import (
    NumericBinding, NumericShard, iter_numeric_prediction_records)
from .research_junyi_window_cache import window_cache_key
from knowledge_tracing.response_calibration import PredictionBinding


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _pinned_json(path, expected_sha256, root):
    path = _volume_input(path, root)
    _need(sha256_file(path) == expected_sha256, 'immutable CPU join input changed')
    return json.loads(path.read_text(encoding='utf-8'))


def join_numeric_calibration_snapshot(raw_paths, view, encoding, *, binding, numeric_binding,
        gpu_receipt, expected_gpu_receipt_sha256, window_manifest, window_admission,
        expected_window_admission_sha256, population, expected_population_identity,
        source_pins, max_targets, max_learner_events, artifact_root,
        run_id, raw_tranche_id, fit_tranche_id, expected_graph_cache_identity,
        max_archive_bytes=2*1024**3, on_raw_ready=None):
    """Kiểm snapshot hoàn chỉnh, replay numeric trên CPU và trả hai publish requests."""
    _need(type(artifact_root) is CalibrationFitArtifactRoot, 'typed Volume artifact root required')
    run_id, raw_tranche_id, fit_tranche_id = map(_identifier, (run_id, raw_tranche_id, fit_tranche_id))
    _need(raw_tranche_id != fit_tranche_id, 'raw and fit require distinct immutable tranches')
    payloads = Path(artifact_root.root) / run_id / raw_tranche_id / 'payloads'
    artifact_root.validate_output(payloads)
    root = Path(artifact_root.root).resolve(strict=True)
    _need(type(binding) is PredictionBinding and type(numeric_binding) is NumericBinding,
          'typed prediction and numeric bindings required')
    numeric_binding.validate()
    _need(on_raw_ready is None or callable(on_raw_ready), 'raw snapshot callback must be callable')
    _need(type(max_archive_bytes) is int and 0 < max_archive_bytes <= 2*1024**3,
          'bounded raw archive size required')
    _need((numeric_binding.variant == 'A0' and expected_graph_cache_identity is None)
          or (numeric_binding.variant != 'A0' and type(expected_graph_cache_identity) is str
              and len(expected_graph_cache_identity) == 64), 'explicit graph cache identity required')
    encoding.assert_for(view)
    _need(view.scope == 'calibration_predict' and view.full_role_coverage,
          'full calibration10 phase required')
    _need(binding.model_id == numeric_binding.variant + '_JUNYI_REFIT'
          and numeric_binding.checkpoint_id == numeric_binding.checkpoint_sha256 == binding.checkpoint_sha256
          and numeric_binding.phase_sha256 == view.identity
          and numeric_binding.encoding_sha256 == encoding.identity == binding.vocabulary_sha256
          and numeric_binding.source_sha256 == binding.model_source_sha256
          and binding.split_sha256 == view.roles.identity,
          'numeric/refit checkpoint phase encoding source binding mismatch')
    _need(population['identity'] == expected_population_identity
          and population['source_pins'] == source_pins, 'calibration population pin mismatch')
    for name in ('canonical', 'assignments', 'canonical_manifest', 'split_manifest'):
        _volume_input(getattr(raw_paths, name), root)
    _source_pins(raw_paths, source_pins)
    source_manifest = json.loads(raw_paths.canonical_manifest.read_text(encoding='utf-8'))
    _need(source_manifest.get('purpose') == 'JUNYI_REFIT90_RESPONSE_CALIBRATION_SOURCE'
          and source_manifest.get('roles_identity') == view.roles.identity
          and source_manifest.get('phase_identity') == view.identity
          and source_manifest.get('encoding_identity') == encoding.identity
          and all(source_manifest.get(name) is False for name in ('train_events_included',
              'selection_events_included', 'outer_events_included', 'holdout_events_included')),
          'calibration10-only source required before numeric join')
    source_sha256 = sha256_file(raw_paths.canonical)
    _need(binding.domain_sha256 == source_sha256, 'canonical inference domain binding mismatch')
    manifest = _pinned_json(window_manifest, numeric_binding.window_manifest_sha256, root)
    admission = _pinned_json(window_admission, expected_window_admission_sha256, root)
    expected_key = window_cache_key(view, encoding, source_sha256,
                                    expected_target_rows=population['targets'])
    _need(manifest['status'] == 'COMPLETE' and manifest['key'] == expected_key
          and admission['kind'] == 'JUNYI_CPU_WINDOW_ADMISSION_V1'
          and admission['manifest_sha256'] == numeric_binding.window_manifest_sha256
          and admission['key'] == expected_key and admission['summary'] == manifest['summary']
          and admission['shards'] == manifest['shards']
          and admission['strict_records_verified'] == manifest['summary']['records'],
          'window manifest/admission binding mismatch')
    receipt = _pinned_json(gpu_receipt, expected_gpu_receipt_sha256, root)
    _need(receipt['kind'] == 'JUNYI_CACHED_NUMERIC_INFERENCE_V1' and receipt['status'] == 'COMPLETE'
          and receipt['binding'] == asdict(numeric_binding)
          and receipt['roles_sha256'] == view.roles.identity
          and receipt['source_data_sha256'] == source_sha256
          and receipt['dataset_sha256'] == population['identity']
          and receipt['graph_cache_identity'] == expected_graph_cache_identity
          and receipt['window_admission_sha256'] == expected_window_admission_sha256,
          'GPU receipt binding mismatch')
    summary, counts = manifest['summary'], receipt['counts']
    _need(all(type(counts[name]) is int and counts[name] >= 0
              for name in ('records', 'windows', 'targets', 'fitted_targets', 'oov_targets'))
          and counts['records'] == summary['records']
          and counts['windows'] == summary['windows']
          and counts['targets'] == summary['target_rows'] == population['targets']
          and counts['oov_targets'] == summary['unseen_targets']
          and counts['fitted_targets'] + counts['oov_targets'] == counts['targets'],
          'GPU numeric coverage counts mismatch')
    shards = tuple(NumericShard(_volume_input(row['manifest_path'], root), row['manifest_sha256'])
                   for row in receipt['shards'])
    _need(len(shards) > 0 or counts['windows'] == 0, 'numeric shards missing')
    adapter = SimpleNamespace(config=SimpleNamespace(context=100, target_block=100, batch_size=128),
                              encoding=encoding.native, checkpoint_id=binding.checkpoint_sha256)
    factory = lambda: iter_junyi_phase_learners(raw_paths, view)
    records = iter_numeric_prediction_records(adapter, prepare_prediction_windows(adapter, factory()), shards,
        binding=numeric_binding, expected_records=counts['targets'], expected_windows=counts['windows'],
        expected_targets=counts['fitted_targets'])
    observations = iter_calibration_observations(records, factory(), view=view, binding=binding,
        population=population, max_targets=max_targets, max_learner_events=max_learner_events)
    config = dict(kind='JUNYI_CPU_NUMERIC_CALIBRATION_JOIN_V1', binding=asdict(binding),
        numeric_binding=asdict(numeric_binding), gpu_receipt_sha256=expected_gpu_receipt_sha256,
        window_admission_sha256=expected_window_admission_sha256,
        population_identity=expected_population_identity, source_pins=source_pins, counts=counts)
    payloads.mkdir(parents=True, exist_ok=False)
    _write_json_atomic(payloads / 'config.json', config)

    def checked_records():
        for record, _, _ in observations:
            yield record
        _source_pins(raw_paths, source_pins)
        _need(sha256_file(raw_paths.canonical) == source_sha256, 'canonical source changed during CPU join')
        _pinned_json(gpu_receipt, expected_gpu_receipt_sha256, root)
        _pinned_json(window_manifest, numeric_binding.window_manifest_sha256, root)
        _pinned_json(window_admission, expected_window_admission_sha256, root)

    raw = payloads / 'raw'
    identity = dict(phase='junyi_response_calibration', population=expected_population_identity,
        checkpoint=binding.checkpoint_sha256, inference_source=binding.model_source_sha256,
        prediction_batch_size=128)
    exported = export_predictions(checked_records(), raw, expected_learners_factory=factory,
                                  identity=identity, artifact_root=artifact_root)
    names = ['manifest.json', *(row['path'] for row in exported['shards'])]
    inventory = {name: dict(bytes=(raw / name).stat().st_size,
                           sha256=sha256_file(raw / name)) for name in names}
    inventory_json = json.dumps(inventory, sort_keys=True)
    estimated_archive_bytes = (sum(pin['bytes'] for pin in inventory.values())
        + len(inventory_json.encode()) + sum(2*len(('raw/' + name).encode()) + 200 for name in names) + 512)
    _need(estimated_archive_bytes <= max_archive_bytes, 'raw archive exceeds declared byte cap')
    partial = payloads / 'RAW_EXPORT.zip.partial'
    with zipfile.ZipFile(partial, 'x', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for name in names:
            archive.write(raw / name, 'raw/' + name)
            _need(sha256_file(raw / name) == inventory[name]['sha256'], 'raw shard changed during packing')
        archive.writestr('INVENTORY.json', inventory_json)
    archive_path = payloads / 'RAW_EXPORT.zip'
    _need(partial.stat().st_size <= max_archive_bytes, 'raw archive actual byte cap exceeded')
    publish_new_file(partial, archive_path)
    _write_json_atomic(payloads / 'COMPLETE.json', dict(status='JUNYI_CPU_NUMERIC_RAW_COMPLETE',
        gpu_receipt_sha256=expected_gpu_receipt_sha256, raw_manifest_sha256=sha256_file(raw / 'manifest.json'),
        archive_sha256=sha256_file(archive_path), archive_bytes=archive_path.stat().st_size, counts=counts))
    files = ['config.json', 'RAW_EXPORT.zip', 'COMPLETE.json']
    raw_publish = dict(run_id=run_id, tranche_id=raw_tranche_id, files=files,
                       max_total_bytes=sum((payloads / name).stat().st_size for name in files))
    _need(raw_publish['max_total_bytes'] <= 2*1024**3, 'raw publish tranche exceeds Drive byte cap')
    if on_raw_ready is not None:
        on_raw_ready(json.loads(json.dumps(raw_publish)))
    fitted = fit_volume_calibration(raw, raw_paths, view, binding=binding, population=population,
        expected_population_identity=expected_population_identity,
        expected_manifest_sha256=sha256_file(raw / 'manifest.json'),
        shard_sha256={row['path']: sha256_file(raw / row['path']) for row in exported['shards']},
        source_pins=source_pins, max_targets=max_targets, max_learner_events=max_learner_events,
        artifact_root=artifact_root, run_id=run_id, tranche_id=fit_tranche_id)
    return dict(status='CPU_NUMERIC_RAW_AND_FIT_READY_FOR_VOLUME_COMMIT',
        raw_payloads=str(payloads), calibration_identity=fitted['calibration_identity'],
        publish_requests=[raw_publish, fitted['publish_request']])
