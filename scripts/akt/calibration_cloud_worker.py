"""Điều phối calibration cloud theo stage riêng; không tự tạo tài nguyên.

Request và inputs đã stage trên Volume bởi CPU. GPU chỉ nhận cache đã admit.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import zipfile


def runtime_preflight(project):
    """Đọc runtime CPU/source thật, chưa model/data hoặc CUDA initialization."""
    import platform
    from knowledge_tracing.akt.config import SOURCE_COMMIT
    from knowledge_tracing.akt.provenance import verify_upstream
    from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
    project = Path(project)
    upstream = verify_upstream(project/'artifacts/akt/dependencies/upstream', SOURCE_COMMIT)
    scripts = ('calibration_cloud_worker.py', 'modal_junyi_calibration.py',
        'prepare_junyi_calibration_caches.py', 'run_junyi_refit.py',
        'drive_artifact_sink.py', 'drive_resumable_upload.py', 'calibration_audit_transaction.py')
    sources = {name: sha(project/'scripts/akt'/name) for name in scripts}
    import torch
    if (platform.python_version() != '3.13.18' or str(torch.__version__) != '2.7.1+cu126'
            or torch.version.cuda != '12.6' or torch.cuda.is_initialized() is not False):
        raise ValueError('CPU preflight runtime differs from verified image or CUDA already initialized')
    identity = inference_source_identity()
    if torch.cuda.is_initialized() is not False:
        raise ValueError('CPU source preflight unexpectedly initialized CUDA')
    return dict(status='CALIBRATION_RUNTIME_SOURCE_PREFLIGHT_PASS', python=sys.version,
        python_executable=sys.executable, torch=str(torch.__version__), cuda_build=torch.version.cuda,
        cuda_initialized=False, upstream=upstream, source_identity=identity, worker_sources=sources,
        models_loaded=False, real_data_read=False, gpu_started=False)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pinned(entry, root):
    if not isinstance(entry, dict) or set(entry) != {'path', 'sha256'}:
        raise ValueError('pinned path/SHA required')
    path, root = Path(entry['path']), Path(root).resolve(strict=True)
    if (not path.is_absolute() or not path.is_relative_to(root) or path.resolve(strict=True) != path
            or any(part.is_symlink() or getattr(part, 'is_junction', lambda: False)()
                   for part in (path, *path.parents) if part != root.parent)):
        raise ValueError('physical Volume input required')
    if sha(path) != entry['sha256']:
        raise ValueError('staged input SHA changed')
    return path


def validate_request(request, stage):
    required = {'kind', 'workspace', 'mode', 'run_id', 'variant', 'exports', 'data_paths',
                'population', 'source_pins', 'cache_receipt', 'numeric_budget', 'cpu_budget',
                'gpu_output', 'full_cohort_approved', 'max_cost_usd', 'source_identity'}
    if not isinstance(request, dict) or set(request) != required:
        raise ValueError('exact calibration request schema required')
    if (request['kind'] != 'JUNYI_CLOUD_CALIBRATION_REQUEST_V1'
            or request['workspace'] != 'honguyenminhsang2016'
            or request['variant'] not in ('A0', 'A1', 'A2', 'A3')
            or request['mode'] not in ('pilot', 'full')
            or stage not in ('cpu-cache', 'gpu', 'cpu-join')
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,70}', request['run_id'])):
        raise ValueError('invalid stage/workspace/mode/variant')
    if set(request['exports']) != {'A0', 'A1', 'A2', 'A3'}:
        raise ValueError('four matched export indexes required')
    if set(request['data_paths']) != {'canonical', 'assignments', 'canonical_manifest', 'split_manifest'}:
        raise ValueError('calibration-only DataPaths required')
    if type(request['full_cohort_approved']) is not bool:
        raise ValueError('explicit full-cohort decision required')
    if request['mode'] == 'full' and request['full_cohort_approved'] is not True:
        raise PermissionError('full cohort is not approved')
    if type(request['max_cost_usd']) not in (int, float) or not 0 < request['max_cost_usd'] <= .75:
        raise ValueError('bounded per-stage allocation at most USD0.75 required')
    budget = request['numeric_budget']
    if not isinstance(budget, dict) or not 0 < budget.get('max_seconds', 0) <= 240:
        raise ValueError('GPU child cap at most240 seconds required')
    from knowledge_tracing.akt.research_junyi_cached_numeric import CachedNumericBudget
    CachedNumericBudget(**budget)
    if (request['mode'] == 'pilot'
            and (budget.get('expected_targets', 0) > 4096 or budget.get('expected_windows', 0) > 64)):
        raise ValueError('pilot requires dedicated bounded cache, never truncate full cache')
    if request['mode'] == 'pilot' and stage == 'cpu-join':
        raise PermissionError('technical pilot cannot produce full-cohort temperature fit')
    if not re.fullmatch('[0-9a-f]{64}', request['source_identity']):
        raise ValueError('external inference source identity required')
    if request['gpu_output'] != request['run_id']+'/'+request['variant'].lower()+'-numeric/payloads':
        raise ValueError('explicit run-owned numeric payloads path required')
    return request


def load_inputs(request, root, *, cuda=False):
    from knowledge_tracing.akt.config import DataPaths, ResearchCUDAExecutionProfile, PROJECT_ROOT
    from knowledge_tracing.akt.research_junyi_inference import (
        JunyiCPUInferenceBudget, inspect_cuda_refit_export)
    from prepare_junyi_calibration_caches import inspect_calibration_exports
    budget = JunyiCPUInferenceBudget(**request['cpu_budget'])
    exports = {variant: dict(path=str(pinned(entry, root)), sha256=entry['sha256'])
               for variant, entry in request['exports'].items()}
    # GPU không mở hoặc hash canonical data, chỉ nhận cache CPU đã admit.
    paths = None if cuda else DataPaths(**{
        name: pinned(entry, root) for name, entry in request['data_paths'].items()})
    population = json.loads(pinned(request['population'], root).read_text())
    if population['source_pins'] != request['source_pins']:
        raise ValueError('population source pins changed')
    if cuda:
        profile = ResearchCUDAExecutionProfile(max_vram_bytes=request['numeric_budget']['max_vram_bytes'],
                                                recipe_id='cgakt-cuda-fp32-batch128-v2')
        index = exports[request['variant']]
        assets = inspect_cuda_refit_export(Path(index['path']).parent,
            expected_index_sha256=index['sha256'], output=PROJECT_ROOT/'experiments/akt/results'/request['run_id'],
            run_id=request['run_id'], budget=budget, cuda_profile=profile)
    else:
        assets = inspect_calibration_exports(exports, run_id=request['run_id'], budget=budget)
    return assets, paths, population


def cpu_prepare(request, root, *, volume_commit):
    validate_request(request, 'cpu-cache')
    if request['mode'] != 'full':
        raise PermissionError('pilot cache must be prepared by separately reviewed bounded CPU recipe')
    from knowledge_tracing.akt.cache_artifacts import JunyiCacheArtifactRoot
    from prepare_junyi_calibration_caches import prepare_calibration_caches
    assets, paths, population = load_inputs(request, root)
    cache_output = Path(request['cache_receipt']['path']).parent
    return prepare_calibration_caches(assets, paths, request['source_pins'], population,
        output_root=cache_output, artifact_root=JunyiCacheArtifactRoot(Path(root).resolve(strict=True)),
        max_seconds=1800, max_rss_bytes=12*1024**3, volume_commit=volume_commit)


def gpu_predict(request, root, *, volume_commit):
    started = time.monotonic()
    host_phase_seconds = {}
    phase_started = started
    def mark_phase(name):
        nonlocal phase_started
        current = time.monotonic()
        host_phase_seconds[name] = current-phase_started
        phase_started = current
    validate_request(request, 'gpu')
    mark_phase('request_validation')
    from knowledge_tracing.akt.cache_artifacts import JunyiCacheArtifactRoot
    from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
    from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession
    from knowledge_tracing.akt.research_junyi_graph_cache import GraphContextCache
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_numeric_predictions import NumericBinding
    from knowledge_tracing.akt.research_junyi_cached_numeric import CachedNumericBudget, run_cuda_cached_numeric
    from run_junyi_refit import configure_cuda
    mark_phase('imports')
    cache_info = json.loads(pinned(request['cache_receipt'], root).read_text())
    mark_phase('cache_receipt_read')
    assets, _, population = load_inputs(request, root, cuda=True)
    mark_phase('load_inputs')
    if inference_source_identity() != request['source_identity']:
        raise ValueError('image inference source identity mismatch')
    view, encoding = assets['calibration'], assets['encoding']
    if (cache_info['population']['identity'] != population['identity']
            or cache_info['source_pins'] != request['source_pins']):
        raise ValueError('CPU cache population/source mismatch')
    cloud = JunyiCacheArtifactRoot(Path(root).resolve(strict=True))
    win = cache_info['windows']
    mark_phase('source_checks')
    cache = JunyiWindowCacheSession(Path(win['path']), view, encoding,
        cache_info['source_data_sha256'], cache_info['population']['targets'], win['manifest_sha256'],
        prefetch=True, admission_receipt=Path(win['admission_path']),
        expected_admission_sha256=win['admission_sha256'], artifact_root=cloud)
    mark_phase('window_session')
    phase = graph = None
    if request['variant'] != 'A0':
        phase = JunyiGraphPhaseSession(assets['condition'], view)
        info = cache_info['graphs'][request['variant']]
        graph = GraphContextCache.open(info['path'], info['sha256'], phase,
            dataset_sha256=population['identity'], window_manifest_sha256=win['manifest_sha256'], artifact_root=cloud)
    mark_phase('graph_cache')
    binding = NumericBinding(request['variant'], assets['index']['checkpoint_sha256'],
        assets['index']['checkpoint_sha256'], view.identity, encoding.identity,
        win['manifest_sha256'], request['source_identity'])
    mark_phase('numeric_binding')
    configure_cuda(assets['cuda_profile'], assets['config'].threads)
    mark_phase('configure_cuda')
    result = run_cuda_cached_numeric(assets, cache, graph_cache=graph, phase=phase, binding=binding,
        dataset_sha256=population['identity'], output_root=cloud.validate(Path(root)/request['gpu_output']),
        budget=CachedNumericBudget(**request['numeric_budget']))
    mark_phase('numeric_core')
    with (Path(root)/request['gpu_output']/'config.json').open('x', encoding='utf-8') as stream:
        json.dump(request, stream, sort_keys=True, allow_nan=False)
    mark_phase('config_write')
    volume_commit()
    mark_phase('volume_commit')
    return dict(status='GPU_NUMERIC_COMMITTED_RELEASE_GPU', **result,
        worker_seconds=phase_started-started, volume_commit_seconds=host_phase_seconds['volume_commit'],
        host_phase_seconds=host_phase_seconds)


def attempt_identifier(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,47}', value):
        raise ValueError('bounded attempt identifier required')
    return value


def cpu_tranches(variant, attempt_id):
    attempt_id = attempt_identifier(attempt_id)
    if variant not in ('A0', 'A1', 'A2', 'A3'):
        raise ValueError('explicit AKT variant required')
    prefix = variant.lower()
    return dict(raw=f'{prefix}-raw-{attempt_id}', fit=f'{prefix}-fit-{attempt_id}',
                archive=f'{prefix}-numeric-archive-{attempt_id}')


def archive_numeric_snapshot(request, numeric, receipt, root, *, attempt_id='initial', max_archive_bytes=2*1024**3):
    """Đóng gói CPU sau full join; số file Drive luôn ba dù có nhiều shard."""
    from knowledge_tracing.akt.filesystem import publish_new_file
    if type(max_archive_bytes) is not int or not 0 < max_archive_bytes <= 2*1024**3:
        raise ValueError('bounded numeric archive bytes required')
    root = Path(root).resolve(strict=True)
    receipt = Path(receipt)
    names = ['config.json', 'RECEIPT.json']
    if receipt.name != 'RECEIPT.json' or receipt.parent != root/request['gpu_output']:
        raise ValueError('numeric archive must use run-owned receipt root')
    if (json.loads(receipt.read_text()) != numeric
            or json.loads((receipt.parent/'config.json').read_text()) != request):
        raise ValueError('numeric archive receipt/config changed')
    expected_hashes = {}
    for shard in numeric['shards']:
        manifest = Path(shard['manifest_path'])
        if manifest.parent != receipt.parent or manifest.suffix != '.json':
            raise ValueError('numeric archive shard path mismatch')
        names.extend((manifest.name, manifest.with_suffix('.npz').name))
        expected_hashes[manifest.name] = shard['manifest_sha256']
        checked_manifest = pinned(dict(path=str(manifest), sha256=shard['manifest_sha256']), root)
        expected_hashes[manifest.with_suffix('.npz').name] = json.loads(checked_manifest.read_text())['payload_sha256']
    if len(names) != len(set(names)) or len(names) > 100000:
        raise ValueError('unique bounded numeric archive members required')
    inventory = {}
    for name in names:
        path = receipt.parent/name
        digest = expected_hashes.get(name) or sha(path)
        pinned(dict(path=str(path), sha256=digest), root)
        inventory[name] = dict(bytes=path.stat().st_size, sha256=digest)
    encoded_inventory = json.dumps(inventory, sort_keys=True)
    estimated = sum(item['bytes'] for item in inventory.values()) + len(encoded_inventory.encode()) + 512
    estimated += sum(2*len(name.encode()) + 200 for name in (*names, 'INVENTORY.json'))
    if estimated > max_archive_bytes:
        raise ValueError('numeric archive exceeds declared byte cap')
    tranche = cpu_tranches(request['variant'], attempt_id)['archive']
    payloads = root/request['run_id']/tranche/'payloads'
    if payloads.resolve() != payloads or not payloads.is_relative_to(root):
        raise ValueError('physical numeric archive output required')
    payloads.mkdir(parents=True, exist_ok=False)
    with (payloads/'config.json').open('x', encoding='utf-8') as stream:
        json.dump(dict(request=request, source_receipt_sha256=sha(receipt)), stream, sort_keys=True)
    partial = payloads/'NUMERIC.zip.partial'
    with zipfile.ZipFile(partial, 'x', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for name in names:
            source = receipt.parent/name
            archive.write(source, name)
            if sha(source) != inventory[name]['sha256']:
                raise ValueError('numeric source changed while archiving')
        archive.writestr('INVENTORY.json', encoded_inventory)
    if partial.stat().st_size > max_archive_bytes:
        raise ValueError('numeric archive actual byte cap exceeded')
    completed = payloads/'NUMERIC.zip'
    publish_new_file(partial, completed)
    with (payloads/'COMPLETE.json').open('x', encoding='utf-8') as stream:
        json.dump(dict(status='CPU_NUMERIC_ARCHIVE_COMPLETE', inventory=inventory,
            archive_bytes=completed.stat().st_size, archive_sha256=sha(completed),
            source_receipt_sha256=sha(receipt)), stream, sort_keys=True)
    files = ['config.json', 'NUMERIC.zip', 'COMPLETE.json']
    total = sum((payloads/name).stat().st_size for name in files)
    if total > 2*1024**3:
        raise ValueError('numeric publication exceeds Drive tranche cap')
    return dict(run_id=request['run_id'], tranche_id=tranche, files=files, max_total_bytes=total)


def cpu_join_fit(request, root, *, gpu_result, volume_commit, publish, attempt_id='initial'):
    validate_request(request, 'cpu-join')
    tranches = cpu_tranches(request['variant'], attempt_id)
    from knowledge_tracing.akt.research_junyi_calibration import CalibrationFitArtifactRoot, inference_source_identity
    from knowledge_tracing.akt.research_junyi_numeric_predictions import NumericBinding
    from knowledge_tracing.akt.cloud_calibration_numeric_join import join_numeric_calibration_snapshot
    from knowledge_tracing.response_calibration import PredictionBinding
    from knowledge_tracing.akt.research_junyi_inference import _identity
    assets_by_variant, paths, population = load_inputs(request, root)
    assets = assets_by_variant[request['variant']]
    cache_info = json.loads(pinned(request['cache_receipt'], root).read_text())
    if inference_source_identity() != request['source_identity']:
        raise ValueError('CPU/GPU inference source drift')
    receipt = pinned(dict(path=gpu_result['receipt_path'], sha256=gpu_result['receipt_sha256']), root)
    numeric = json.loads(receipt.read_text())
    binding = NumericBinding(**numeric['binding'])
    vocabulary = assets['encoding'].native.vocabulary.values
    predicted = PredictionBinding(assets['index']['model'], assets['index']['checkpoint_sha256'],
        assets['encoding'].identity, assets['calibration'].roles.identity,
        _identity(dict(domain='junyi_exercises', values=vocabulary)),
        _identity(dict(domain='junyi_logged_response', reference_bank='not_applicable')),
        request['source_identity'], cache_info['source_data_sha256'])
    cloud = CalibrationFitArtifactRoot(Path(root).resolve(strict=True))
    win = cache_info['windows']
    expected_graph_identity = None
    if request['variant'] != 'A0':
        from knowledge_tracing.akt.research_junyi_graph_cache import _digest, FORMAT
        graph = cache_info['graphs'][request['variant']]
        expected_graph_identity = _digest((FORMAT, graph['sha256'], json.dumps(graph['binding'], sort_keys=True)))
    def committed_publish(publication):
        volume_commit()
        return publish(publication)
    def publish_verified_raw(publication):
        # Snapshot số đã được CPU join kiểm đầy đủ trước callback này.
        committed_publish(archive_numeric_snapshot(request, numeric, receipt, root, attempt_id=attempt_id))
        return committed_publish(publication)
    result = join_numeric_calibration_snapshot(paths, assets['calibration'], assets['encoding'],
        binding=predicted, numeric_binding=binding, gpu_receipt=receipt,
        expected_gpu_receipt_sha256=gpu_result['receipt_sha256'],
        window_manifest=Path(win['path'])/'manifest.json', window_admission=Path(win['admission_path']),
        expected_window_admission_sha256=win['admission_sha256'], population=population,
        expected_population_identity=population['identity'], source_pins=request['source_pins'],
        max_targets=population['targets'], max_learner_events=request['cpu_budget']['max_learner_events'],
        artifact_root=cloud, run_id=request['run_id'], raw_tranche_id=tranches['raw'],
        fit_tranche_id=tranches['fit'], expected_graph_cache_identity=expected_graph_identity,
        on_raw_ready=publish_verified_raw)
    committed_publish(result['publish_requests'][1])
    return dict(status='CALIBRATION_RAW_AND_FIT_PUBLISHED', calibration_identity=result['calibration_identity'])


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', required=True, choices=('cpu-cache', 'gpu', 'cpu-join'))
    parser.add_argument('--request', required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--result', required=True)
    parser.add_argument('--attempt-id', required=True)
    parser.add_argument('--gpu-result')
    parser.add_argument('--raw-source')
    parser.add_argument('--writer-closed')
    args = parser.parse_args()
    attempt_identifier(args.attempt_id)
    root = Path('/artifacts').resolve(strict=True)
    project = Path('/opt/kltn')
    sys.path.insert(0, str(project/'src'))
    sys.path.insert(0, str(project/'scripts/akt'))
    request = json.loads(pinned(dict(path=args.request, sha256=args.request_sha256), root).read_text())
    validate_request(request, args.stage)
    result_path = Path(args.result)
    if not result_path.is_absolute() or not result_path.is_relative_to(root) or result_path.exists():
        raise ValueError('new Volume result path required')
    import warnings
    warnings.filterwarnings('ignore', message=r'Your Modal token .*')
    import modal
    volume = modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1', environment_name='main')
    if args.stage == 'gpu':
        result = gpu_predict(request, root, volume_commit=volume.commit)
    elif args.stage == 'cpu-cache':
        result = cpu_prepare(request, root, volume_commit=volume.commit)
    else:
        if not args.gpu_result:
            raise ValueError('CPU join requires pinned GPU result entry')
        gpu_entry = json.loads(args.gpu_result)
        gpu_result = json.loads(pinned(gpu_entry, root).read_text())
        import drive_artifact_sink as sink
        sink.CLOUD_ROOT = root
        def publish(publication):
            return sink.publish_from_environment(
                source_root=root/publication['run_id']/publication['tranche_id']/'payloads',
                files=publication['files'], run_id=publication['run_id'], tranche_id=publication['tranche_id'],
                max_total_bytes=publication['max_total_bytes'], volume_commit=volume.commit,
                chunk_bytes=32*1024**2, retries=2)
        if bool(args.raw_source) != bool(args.writer_closed):
            raise ValueError('raw recovery requires both source and closed writer pins')
        from calibration_audit_transaction import transactional_expected_insert, recover_cpu_calibration
        if args.raw_source:
            result = recover_cpu_calibration(request, root, gpu_result=gpu_result,
                raw_source_pin=json.loads(args.raw_source), closed_marker_pin=json.loads(args.writer_closed),
                attempt_id=args.attempt_id, publish=publish, volume_commit=volume.commit)
        else:
            with transactional_expected_insert():
                result = cpu_join_fit(request, root, gpu_result=gpu_result, volume_commit=volume.commit,
                                      publish=publish, attempt_id=args.attempt_id)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    with result_path.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, sort_keys=True, allow_nan=False)
    volume.commit()


if __name__ == '__main__':
    main()
