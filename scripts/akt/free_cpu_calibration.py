"""Launcher Colab CPU, source KT và thuật toán V1 giữ nguyên."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

ACCOUNT = 'honguyenminhsang2005@gmail.com'
PARENT = '1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7'
VOLUME = Path('/__modal/volumes/vo-dv1975utRQbmagCjA0brSe')
RUN = 'junyi-calibration-real-20261117-01'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def need(value, reason):
    if not value:
        raise ValueError(reason)


def physical_inside(path, root):
    path, root = Path(path).absolute(), Path(root).resolve(strict=True)
    need(path.is_relative_to(root) and path.resolve() == path, 'Noncanonical scratch path')
    for component in (path, *path.parents):
        if component == root:
            break
        need(not component.is_symlink(), 'Scratch alias rejected')
    return path


def publication_source(publication):
    match = re.fullmatch(r'(a[23])-(raw|fit)-freecpu-\1-\d{3}', publication['tranche_id'])
    need(publication['run_id'] == RUN and match, 'Publication identity rejected')
    files = set(publication['files'])
    raw = {'config.json', 'RAW_EXPORT.zip', 'COMPLETE.json'}
    fit = {'config.json', 'fit/temperature.json', 'fit/manifest.json', 'resource.json', 'COMPLETE.json'}
    expected = raw if match[2] == 'raw' else fit
    need(len(files) == len(publication['files']) and files == expected, 'Publication file allowlist rejected')
    source = physical_inside(VOLUME / RUN / publication['tranche_id'] / 'payloads', VOLUME)
    for name in files:
        physical_inside(source / name, VOLUME)
    return source


def download(session, pin, destination):
    """Range resume chỉ trên scratch Colab, kiểm SHA trước công bố."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        need(destination.stat().st_size == pin['bytes'] and sha(destination) == pin['sha256'], 'Existing download changed')
        return destination
    partial = destination.with_name(destination.name + '.part')
    offset = partial.stat().st_size if partial.exists() else 0
    need(0 <= offset <= pin['bytes'], 'Partial exceeds source size')
    if offset < pin['bytes']:
        headers = {'Range': f'bytes={offset}-'} if offset else {}
        with session.get('https://www.googleapis.com/drive/v3/files/' + pin['file_id'],
                         params={'alt': 'media'}, headers=headers, stream=True, timeout=90) as response:
            need(response.status_code == (206 if offset else 200), 'Drive download status mismatch')
            if offset:
                need(response.headers.get('Content-Range') == f"bytes {offset}-{pin['bytes'] - 1}/{pin['bytes']}", 'Drive Range mismatch')
            with partial.open('ab') as output:
                for block in response.iter_content(1024**2):
                    if not block:
                        continue
                    offset += len(block)
                    need(offset <= pin['bytes'], 'Download exceeds pin')
                    output.write(block)
    need(partial.stat().st_size == pin['bytes'] and sha(partial) == pin['sha256'], 'Download size/SHA mismatch')
    os.replace(partial, destination)
    return destination


def extract_numeric(archive_path, pin, root, variant):
    need(sha(archive_path) == pin['sha256'], 'Numeric archive SHA changed')
    Path(root).mkdir(parents=True, exist_ok=True)
    prefix = f'{RUN}/{variant.lower()}-numeric/payloads/'
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        need(len(members) == pin['source_members'] and len({m.filename for m in members}) == len(members), 'Numeric member count mismatch')
        for info in members:
            path = PurePosixPath(info.filename)
            need(info.filename.startswith(prefix) and str(path) == info.filename
                 and not path.is_absolute() and '..' not in path.parts and '\\' not in info.filename
                 and not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16)
                 and 0 < info.file_size <= 2 * 1024**2, 'Unsafe numeric member')
            destination = physical_inside(Path(root) / info.filename, root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            data = archive.read(info)
            if destination.exists():
                need(destination.read_bytes() == data, 'Restaged numeric changed')
            else:
                destination.write_bytes(data)


def publish(session, publication, state_root):
    """Reuse uploader, URI tiếp tục chỉ giữ trong state Drive riêng."""
    import drive_resumable_upload as core
    source = publication_source(publication)
    rows = [dict(path=name, **core.hashes(source / name)) for name in publication['files']]
    total = sum(row['bytes'] for row in rows)
    need(0 < total <= publication['max_total_bytes'] <= 2 * 1024**3, 'Publication exceeds byte contract')
    plan = dict(source=str(source), files=rows, bytes=total,
                folder_name=publication['tranche_id'], parent_id=PARENT, account=ACCOUNT)
    private = Path(state_root) / '.sessions' / publication['tranche_id']
    evidence = Path(state_root) / 'publications' / publication['tranche_id']
    private.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    state_path = private / 'state.json'
    with core.single_writer(private / 'upload.lock'):
        if state_path.exists():
            previous = core.read_json(state_path)
            strip = lambda p: dict(p, files=[{k: v for k, v in r.items() if k != 'mtime_ns'} for r in p['files']])
            need(strip(previous['plan']) == strip(plan), 'Persisted upload payload changed')
            previous['plan'] = plan
            for entry in previous['files'].values():
                entry.pop('local', None)
            core.atomic_json(state_path, previous)
        uploader = core.Uploader(session, plan, state_path, evidence, chunk_bytes=8 * 1024**2, retries=2)
        uploader.run()
    files = []
    for row in rows:
        meta = uploader.metadata(uploader.state['files'][row['path']]['remote_id'])
        parent = uploader.state['folders']['.'] if '/' not in row['path'] else uploader.state['folders'][str(Path(row['path']).parent)]
        need(uploader.matches(meta, row, parent) and meta.get('sha256Checksum') == row['sha256'], 'Drive strict SHA readback failed')
        files.append(dict(path=row['path'], file_id=meta['id'], folder_id=parent,
                          bytes=row['bytes'], sha256=row['sha256']))
    return dict(status='DRIVE_SHA256_VERIFIED', tranche_id=publication['tranche_id'], files=files)


def verify_publication(session, receipt):
    """Đọc lại metadata Drive trước khi dùng checkpoint vận hành đã hoàn tất."""
    need(receipt['status'] == 'DRIVE_SHA256_VERIFIED' and receipt['files'], 'Publication was not verified')
    for pin in receipt['files']:
        response = session.get('https://www.googleapis.com/drive/v3/files/' + pin['file_id'],
            params={'fields': 'id,name,size,sha256Checksum,parents,trashed'}, timeout=60)
        need(response.status_code == 200, 'Published artifact unavailable')
        meta = response.json()
        need(not meta.get('trashed') and meta.get('sha256Checksum') == pin['sha256']
             and int(meta.get('size', -1)) == pin['bytes']
             and pin['folder_id'] in meta.get('parents', [])
             and meta.get('name') == Path(pin['path']).name, 'Published artifact changed')


def publication_pins(publication):
    source = publication_source(publication)
    return {name: {'bytes': (source / name).stat().st_size, 'sha256': sha(source / name)}
            for name in publication['files']}


def pending_exists(publication, expected):
    source = publication_source(publication)
    if not all((source / name).is_file() for name in publication['files']):
        return False
    need(publication_pins(publication) == expected, 'Pending artifact bytes changed')
    return True


def restore_raw(session, publication):
    need(re.fullmatch(r'a[23]-raw-freecpu-a[23]-\d{3}', publication['tranche_id']), 'Raw tranche rejected')
    payloads = physical_inside(VOLUME / RUN / publication['tranche_id'] / 'payloads', VOLUME)
    raw = payloads / 'raw'
    pin = next(row for row in publication['files'] if row['path'] == 'RAW_EXPORT.zip')
    archive = download(session, pin, payloads / 'RAW_EXPORT.zip')
    with zipfile.ZipFile(archive) as zipped:
        infos = zipped.infolist()
        need(len(infos) <= 16000 and len({row.filename for row in infos}) == len(infos)
             and sum(row.file_size for row in infos) <= 2 * 1024**3
             and all(0 < row.file_size <= 64 * 1024**2 and not stat.S_ISLNK(row.external_attr >> 16)
                     for row in infos), 'Raw archive size/type coverage rejected')
        need(zipped.getinfo('INVENTORY.json').file_size <= 8 * 1024**2, 'Raw inventory exceeds budget')
        inventory = json.loads(zipped.read('INVENTORY.json'))
        need(set(zipped.namelist()) == {'INVENTORY.json'} | {'raw/' + name for name in inventory}, 'Raw archive coverage changed')
        for name, pin in inventory.items():
            need(Path(name).name == name and 0 < pin['bytes'] <= 64 * 1024**2, 'Bounded raw basename required')
            data = zipped.read('raw/' + name)
            need(len(data) == pin['bytes'] and hashlib.sha256(data).hexdigest() == pin['sha256'], 'Raw archive member changed')
            raw.mkdir(exist_ok=True)
            target = physical_inside(raw / name, VOLUME)
            if target.exists():
                need(sha(target) == pin['sha256'], 'Existing raw shard changed')
            else:
                target.write_bytes(data)
    return raw


def run_variant(request, gpu_result, cache, session, state_root):
    """Nối/audit/fit V1, tiếp tục từ raw đã kiểm và lưu trên Drive."""
    from dataclasses import asdict
    from knowledge_tracing.akt.config import DataPaths, PROJECT_ROOT
    from knowledge_tracing.akt.research_junyi_inference import JunyiCPUInferenceBudget, inspect_cpu_refit_export, _identity
    from knowledge_tracing.akt.research_junyi_calibration import CalibrationFitArtifactRoot, inference_source_identity
    from knowledge_tracing.akt.research_junyi_numeric_predictions import NumericBinding
    from knowledge_tracing.akt.cloud_calibration_numeric_join import join_numeric_calibration_snapshot
    from knowledge_tracing.akt.cloud_calibration_fit import fit_volume_calibration
    from knowledge_tracing.akt.research_junyi_graph_cache import _digest, FORMAT
    from knowledge_tracing.response_calibration import PredictionBinding
    from calibration_audit_transaction import transactional_expected_insert
    import drive_resumable_upload as core
    variant = request['variant']
    need(variant in ('A2', 'A3') and request['mode'] == 'full' and request['full_cohort_approved'], 'Approved full calibration A2/A3 required')
    need(inference_source_identity() == request['source_identity'], 'Frozen inference source changed')
    need(hashlib.sha256(json.dumps(cache).encode()).hexdigest() == request['cache_receipt']['sha256'], 'Cache receipt changed')
    for entry in [*request['exports'].values(), *request['data_paths'].values(), request['population']]:
        need(sha(entry['path']) == entry['sha256'], 'Input pin changed')
    index = request['exports'][variant]
    assets = inspect_cpu_refit_export(Path(index['path']).parent, expected_index_sha256=index['sha256'],
        output=PROJECT_ROOT / 'experiments/akt/results' / ('free-cpu-' + variant.lower()),
        run_id='free-cpu-' + variant.lower(), budget=JunyiCPUInferenceBudget(**request['cpu_budget']))
    paths = DataPaths(**{key: Path(pin['path']) for key, pin in request['data_paths'].items()})
    population = json.loads(Path(request['population']['path']).read_text())
    need(population['source_pins'] == request['source_pins'] and population == cache['population'], 'Population/source mismatch')
    receipt_path = Path(gpu_result['receipt_path'])
    need(sha(receipt_path) == gpu_result['receipt_sha256'], 'GPU receipt changed')
    numeric = json.loads(receipt_path.read_text())
    binding = PredictionBinding(assets['index']['model'], assets['index']['checkpoint_sha256'],
        assets['encoding'].identity, assets['calibration'].roles.identity,
        _identity(dict(domain='junyi_exercises', values=assets['encoding'].native.vocabulary.values)),
        _identity(dict(domain='junyi_logged_response', reference_bank='not_applicable')),
        request['source_identity'], cache['source_data_sha256'])
    graph = cache['graphs'][variant]
    graph_identity = _digest((FORMAT, graph['sha256'], json.dumps(graph['binding'], sort_keys=True)))
    root = CalibrationFitArtifactRoot(VOLUME)
    state_file = Path(state_root) / (variant + '_PROGRESS.json')
    fingerprint = _identity(dict(request=request, cache=cache, binding=asdict(binding), gpu_result=gpu_result))
    state = core.read_json(state_file) if state_file.exists() else dict(variant=variant, fingerprint=fingerprint,
        gpu_receipt_sha256=gpu_result['receipt_sha256'], attempts=0)
    need(state['gpu_receipt_sha256'] == gpu_result['receipt_sha256']
         and state['fingerprint'] == fingerprint, 'Progress belongs to different inputs')
    if state.get('fit_verified'):
        verify_publication(session, state['raw_publication'])
        verify_publication(session, state['fit_publication'])
        return state
    if state.get('pending_fit') and pending_exists(state['pending_fit'], state['pending_fit_files']):
        verify_publication(session, state['raw_publication'])
        state.update(fit_verified=True, fit_publication=publish(session, state['pending_fit'], state_root))
        state.pop('pending_fit')
        state.pop('pending_fit_files')
        core.atomic_json(state_file, state)
        return state
    if state.get('pending_raw'):
        publication = state['pending_raw']
        if pending_exists(publication, state['pending_raw_files']):
            state.update(raw_verified=True, raw_publication=publish(session, publication, state_root))
            state.pop('pending_raw')
            state.pop('pending_raw_files')
            core.atomic_json(state_file, state)
    state['attempts'] += 1
    attempt = f"freecpu-{variant.lower()}-{state['attempts']:03d}"
    core.atomic_json(state_file, state)
    fit_tranche = variant.lower() + '-fit-' + attempt
    if state.get('raw_verified'):
        verify_publication(session, state['raw_publication'])
        raw = restore_raw(session, state['raw_publication'])
        manifest = json.loads((raw / 'manifest.json').read_text())
        fitted = fit_volume_calibration(raw, paths, assets['calibration'], binding=binding,
            population=population, expected_population_identity=population['identity'],
            expected_manifest_sha256=sha(raw / 'manifest.json'),
            shard_sha256={row['path']: sha(raw / row['path']) for row in manifest['shards']},
            source_pins=request['source_pins'], max_targets=population['targets'],
            max_learner_events=request['cpu_budget']['max_learner_events'],
            artifact_root=root, run_id=RUN, tranche_id=fit_tranche)
        fit_request = fitted['publish_request']
    else:
        def raw_ready(publication):
            state['pending_raw'] = publication
            state['pending_raw_files'] = publication_pins(publication)
            core.atomic_json(state_file, state)
            receipt = publish(session, publication, state_root)
            state.update(raw_verified=True, raw_publication=receipt)
            state.pop('pending_raw', None)
            state.pop('pending_raw_files', None)
            core.atomic_json(state_file, state)
        win = cache['windows']
        with transactional_expected_insert():
            result = join_numeric_calibration_snapshot(paths, assets['calibration'], assets['encoding'],
                binding=binding, numeric_binding=NumericBinding(**numeric['binding']),
                gpu_receipt=receipt_path, expected_gpu_receipt_sha256=gpu_result['receipt_sha256'],
                window_manifest=Path(win['path']) / 'manifest.json', window_admission=Path(win['admission_path']),
                expected_window_admission_sha256=win['admission_sha256'], population=population,
                expected_population_identity=population['identity'], source_pins=request['source_pins'],
                max_targets=population['targets'], max_learner_events=request['cpu_budget']['max_learner_events'],
                artifact_root=root, run_id=RUN, raw_tranche_id=variant.lower() + '-raw-' + attempt,
                fit_tranche_id=fit_tranche, expected_graph_cache_identity=graph_identity,
                on_raw_ready=raw_ready)
        fit_request = result['publish_requests'][1]
    state.update(pending_fit=fit_request, pending_fit_files=publication_pins(fit_request))
    core.atomic_json(state_file, state)
    state.update(fit_verified=True, fit_publication=publish(session, fit_request, state_root))
    state.pop('pending_fit')
    state.pop('pending_fit_files')
    core.atomic_json(state_file, state)
    return state
