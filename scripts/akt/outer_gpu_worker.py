"""WorkerouterH100 ngoàiKT, chỉcacheCPU-admitted và numericoutput không nhãn."""
from contextlib import contextmanager
import json
import math
from pathlib import Path, PurePosixPath
import re
import time

SOURCE = '7c72414eedf9507d514430aed4734f0a192ab14914a4984b17fdfcbfebd39123'


def validate_outer_request(request):
    fields = {'kind','workspace','run_id','variant','source_identity','exports','calibrators',
        'compatibility','calibration_data_sha256','cache_receipt','window_location','admission_location',
        'graph_locations','numeric_budget','cpu_budget','gpu_output','full_cohort_approved','max_cost_usd'}
    if (type(request) is not dict or set(request) != fields
            or request['kind'] != 'JUNYI_OUTER_GPU_REQUEST_V1'
            or request['workspace'] != 'honguyenminhsang2016'
            or request['variant'] not in ('A0','A1','A2','A3')
            or request['source_identity'] != SOURCE
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,70}',request['run_id'])):
        raise ValueError('Exact approved outer request required')
    if request['full_cohort_approved'] is not True:
        raise PermissionError('Explicit full outer allocation required')
    if type(request['max_cost_usd']) not in (int,float) or not 0 < request['max_cost_usd'] <= .75:
        raise ValueError('Per-model reservation at most USD0.75 required')
    if any(set(request[name]) != {'A0','A1','A2','A3'} for name in ('exports','calibrators','compatibility')):
        raise ValueError('Four frozen model/calibrator/compatibility pins required')
    if set(request['graph_locations']) != {'A1','A2','A3'}:
        raise ValueError('Three staged graph cache locations required')
    entries = [(request['cache_receipt'],False)]
    entries += [(entry,False) for group in ('exports','compatibility') for entry in request[group].values()]
    entries += [(entry,True) for entry in request['calibrators'].values()]
    for entry, calibrator in entries:
        keys = {'path','sha256','identity'} if calibrator else {'path','sha256'}
        if (type(entry) is not dict or set(entry) != keys or type(entry['path']) is not str
                or not PurePosixPath(entry['path']).is_absolute() or '..' in PurePosixPath(entry['path']).parts
                or '\\' in entry['path'] or ':' in entry['path']
                or any(type(entry[name]) is not str or not re.fullmatch('[0-9a-f]{64}',entry[name])
                       for name in keys-{'path'})):
            raise ValueError('Complete physical input path/SHA/identity pins required')
    if not re.fullmatch('[0-9a-f]{64}',request['calibration_data_sha256']):
        raise ValueError('Calibration domain pin required')
    budget = request['numeric_budget']
    required = {'max_seconds','max_rss_bytes','max_vram_bytes','expected_records','expected_windows',
                'expected_targets','expected_oov_targets','batch_size'}
    if type(budget) is not dict or set(budget) != required:
        raise ValueError('Exact numeric budget schema required')
    if (type(budget['max_seconds']) not in (int,float) or not math.isfinite(budget['max_seconds'])
            or not 0 < budget['max_seconds'] <= 240
            or any(type(value) is not int or value <= 0 for name,value in budget.items() if name!='max_seconds')
            or budget['expected_targets'] != 4137050 or budget['expected_oov_targets'] != 144
            or budget['expected_records'] != 72567 or budget['expected_windows'] != 72423
            or budget['batch_size'] != 128):
        raise ValueError('Full outer counts, FP32batch128 and childcap240 required')
    cpu = request['cpu_budget']
    if (cpu.get('max_targets') != 4137050 or cpu.get('max_users') != 39616
            or cpu.get('max_learner_events') != 21908 or cpu.get('prediction_batch_size') != 128
            or type(cpu.get('max_seconds')) not in (int,float) or not math.isfinite(cpu['max_seconds'])
            or not 0 < cpu['max_seconds'] <= 240):
        raise ValueError('CPU metadata budget must match full outer population')
    if request['gpu_output'] != request['run_id']+'/'+request['variant'].lower()+'-outer-numeric/payloads':
        raise ValueError('Explicit new run-owned numeric output required')
    return request


@contextmanager
def admitted_predictor_builder(inference, *, admit, view, graph_cache, phase,
        calibration, compatibility, source_sha256, outer_data_sha256,
        calibration_data_sha256, admission_output):
    """Bọc đúng publicbuilder, actualadmittrướcforward vàrestorekểcảlỗi."""
    original = inference.build_cuda_refit_predictor
    def build(*args,**kwargs):
        predictor = original(*args,**kwargs)
        if phase is not None:
            predictor.adapter.set_phase(phase,context_cache=graph_cache)
        result = admit(predictor,view=view,expected_source_sha256=source_sha256,
            outer_data_sha256=outer_data_sha256,calibration_data_sha256=calibration_data_sha256,
            calibration=calibration,compatibility=compatibility)
        admission_output.update(result)
        return predictor
    inference.build_cuda_refit_predictor = build
    try:
        yield
    finally:
        inference.build_cuda_refit_predictor = original


def gpu_outer_predict(request, root, *, volume_commit):
    started = time.monotonic()
    validate_outer_request(request)
    from calibration_cloud_worker import pinned, sha
    from free_outer_evaluation import admit_outer, validate_compatibility
    from run_junyi_refit import configure_cuda
    from knowledge_tracing.akt.config import PROJECT_ROOT, ResearchCUDAExecutionProfile
    from knowledge_tracing.akt import research_junyi_inference as inference
    from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_graph_cache import GraphContextCache
    from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession
    from knowledge_tracing.akt.cache_artifacts import JunyiCacheArtifactRoot
    from knowledge_tracing.akt.research_junyi_numeric_predictions import NumericBinding
    from knowledge_tracing.akt.research_junyi_cached_numeric import CachedNumericBudget, run_cuda_cached_numeric
    from knowledge_tracing.response_calibration import PredictionBinding, TemperatureCalibration
    if inference_source_identity() != SOURCE:
        raise ValueError('Actual runtime must match exact guard release')
    cloud = JunyiCacheArtifactRoot(Path(root).resolve(strict=True))
    cache_info = json.loads(pinned(request['cache_receipt'],root).read_text())
    index_entry = request['exports'][request['variant']]
    index = pinned(index_entry,root)
    profile = ResearchCUDAExecutionProfile(max_vram_bytes=request['numeric_budget']['max_vram_bytes'],
                                           recipe_id='cgakt-cuda-fp32-batch128-v2')
    assets = inference.inspect_cuda_refit_export(index.parent,expected_index_sha256=index_entry['sha256'],
        output=PROJECT_ROOT/'experiments/akt/results'/request['run_id'],run_id=request['run_id'],
        budget=inference.JunyiCPUInferenceBudget(**request['cpu_budget']),cuda_profile=profile)
    encoding = assets['encoding']
    if assets['index']['model'] != request['variant']+'_JUNYI_REFIT':
        raise ValueError('Selected export variant differs from request')
    roles = encoding.fit_view.roles
    view = JunyiPhaseView(roles,'outer_evaluation',roles.outer_validation_users,roles.identity)
    if (cache_info['status'] != 'JUNYI_OUTER_CPU_CACHES_COMPLETE'
            or cache_info['phase'] != 'outer_evaluation' or cache_info['phase_identity'] != view.identity
            or cache_info['roles_identity'] != roles.identity or cache_info['encoding_identity'] != encoding.identity
            or len(view.users) != 39616):
        raise ValueError('CPU-admitted full outer population differs')
    temperatures, compatibility = {},{}
    for variant in ('A0','A1','A2','A3'):
        entry = request['calibrators'][variant]
        payload = json.loads(pinned(dict(path=entry['path'],sha256=entry['sha256']),root).read_text())
        fitted = TemperatureCalibration.from_payload(payload,binding=PredictionBinding(**payload['binding']))
        exported = json.loads(pinned(request['exports'][variant],root).read_text())
        expected = dict(model_id=variant+'_JUNYI_REFIT',checkpoint_sha256=exported['checkpoint_sha256'],
            vocabulary_sha256=encoding.identity,split_sha256=roles.identity,
            bank_sha256=inference._identity(dict(domain='junyi_exercises',values=encoding.native.vocabulary.values)),
            reference_sha256=inference._identity(dict(domain='junyi_logged_response',reference_bank='not_applicable')),
            model_source_sha256='d22f6d2e3d6bb4a6c2d7f72da748e55c5c647ce8b41a7ab46b25c82290a4c96c',
            domain_sha256=request['calibration_data_sha256'])
        if fitted.binding != PredictionBinding(**expected) or fitted.identity != entry['identity']:
            raise ValueError('Frozen four-model calibrator binding mismatch')
        receipt = json.loads(pinned(request['compatibility'][variant],root).read_text())
        validate_compatibility(receipt,checkpoint_sha256=fitted.binding.checkpoint_sha256,
            calibration_identity=fitted.identity,calibrated_source=fitted.binding.model_source_sha256,
            current_source=SOURCE)
        temperatures[variant],compatibility[variant] = fitted,receipt
    win = cache_info['windows']
    budget = request['numeric_budget']
    summary = win['summary']
    if ((summary['records'],summary['windows'],summary['target_rows'],summary['unseen_targets'])
            != (budget['expected_records'],budget['expected_windows'],4137050,144)):
        raise ValueError('Actual cache coverage differs from request')
    cache = JunyiWindowCacheSession(cloud.validate(Path(request['window_location'])),view,encoding,
        cache_info['source_data_sha256'],4137050,win['manifest_sha256'],prefetch=True,
        admission_receipt=pinned(dict(path=request['admission_location'],sha256=win['admission_sha256']),root),
        expected_admission_sha256=win['admission_sha256'],artifact_root=cloud)
    phase = graph = None
    variant = request['variant']
    if variant != 'A0':
        phase = JunyiGraphPhaseSession(assets['condition'],view)
        info = cache_info['graphs'][variant]
        graph = GraphContextCache.open(request['graph_locations'][variant],info['sha256'],phase,
            dataset_sha256=cache_info['dataset_sha256'],window_manifest_sha256=win['manifest_sha256'],artifact_root=cloud)
    numeric = NumericBinding(variant,assets['index']['checkpoint_sha256'],assets['index']['checkpoint_sha256'],
        view.identity,encoding.identity,win['manifest_sha256'],SOURCE)
    configure_cuda(profile,assets['config'].threads)
    import torch
    if torch.cuda.device_count() != 1 or 'H100' not in torch.cuda.get_device_name(0):
        raise ValueError('Exactly one H100 is required')
    output = cloud.validate(Path(root)/request['gpu_output'])
    admission = {}
    setup_seconds = time.monotonic()-started
    with admitted_predictor_builder(inference,admit=admit_outer,view=view,phase=phase,graph_cache=graph,
            calibration=temperatures[variant],compatibility=compatibility[variant],source_sha256=SOURCE,
            outer_data_sha256=cache_info['source_data_sha256'],
            calibration_data_sha256=request['calibration_data_sha256'],admission_output=admission):
        result = run_cuda_cached_numeric(assets,cache,graph_cache=graph,phase=phase,binding=numeric,
            dataset_sha256=cache_info['dataset_sha256'],output_root=output,budget=CachedNumericBudget(**budget))
    for name,value in (('config.json',request),('MODEL_ADMISSION.json',admission),
            ('HOST_TIMING.json',dict(setup_seconds=setup_seconds,worker_seconds=time.monotonic()-started))):
        with (output/name).open('x',encoding='utf-8') as stream:
            json.dump(value,stream,sort_keys=True,allow_nan=False)
    volume_commit()
    return dict(status='OUTER_NUMERIC_COMMITTED_RELEASE_H100',**result,
        admission_sha256=sha(output/'MODEL_ADMISSION.json'),worker_seconds=time.monotonic()-started)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--request',required=True)
    parser.add_argument('--request-sha256',required=True)
    parser.add_argument('--result',required=True)
    args = parser.parse_args()
    from calibration_cloud_worker import pinned
    root = Path('/artifacts').resolve(strict=True)
    request = json.loads(pinned(dict(path=args.request,sha256=args.request_sha256),root).read_text())
    path = Path(args.result)
    if (not path.is_absolute() or not path.is_relative_to(root) or path.resolve()!=path or path.exists()):
        raise ValueError('New physical result required')
    import modal
    volume = modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1',environment_name='main')
    result = gpu_outer_predict(request,root,volume_commit=volume.commit)
    with path.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,sort_keys=True)
    volume.commit()


if __name__ == '__main__':
    main()
