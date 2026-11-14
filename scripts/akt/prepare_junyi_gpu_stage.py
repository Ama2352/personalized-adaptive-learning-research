"""CPU local đóng băng input và đối chiếu A0/A1 trước khi cho phép gọi GPU."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'experiments/akt'))


def validate_baseline_metadata(worker,reference,peers):
    from knowledge_tracing.akt.comparison_contract import TRAINING_FIELDS
    for field in TRAINING_FIELDS:
        if (worker['config'][field]!=reference['training_config'][field]
                or any(worker['config'][field]!=peer['metadata']['identity']['config'][field] for peer in peers)):
            raise ValueError('Cấu hình học khác A0/A1: '+field)
    numeric=lambda profile:{key:value for key,value in profile.items() if key!='max_vram_bytes'}
    profiles=[reference['numeric_profile'],*(peer['metadata']['identity']['profile'] for peer in peers)]
    if any(numeric(worker['profile'])!=numeric(profile) for profile in profiles):
        raise ValueError('Cấu hình số học CUDA khác A0/A1')
    names={'roles':'roles_sha256','selected_manifest':'selected_cache_manifest_sha256',
           'encoding':'encoding_sha256','encoding_receipt':'encoding_receipt_sha256',
           'window_manifest':'train_window_manifest_sha256'}
    if any(reference['data_pins'][key]!=worker['inputs'][value] for key,value in names.items()):
        raise ValueError('Data pins khác baseline')
    if worker['validation_batch_size']!=128:
        raise ValueError('Giữ validation batch128 đã nghiệm thu trên A0 epoch9/A1')
    return len(TRAINING_FIELDS)


def validate_recipe(root,request):
    from junyi_staged_io import owned_input,sha
    from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
    from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
    from knowledge_tracing.akt.research_junyi_confidence_binding import load_binding
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition
    from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession
    from knowledge_tracing.akt.research_junyi_prepared import prepared_cache_options
    from knowledge_tracing.akt.research_junyi_graph_cache import GraphContextCache
    from knowledge_tracing.akt.research_junyi_selection_cache import SelectionCacheSession
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphPhaseSession
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    from knowledge_tracing.akt.config import AKTConfig,ResearchCUDAExecutionProfile,validate_config
    from knowledge_tracing.edge_confidence import EdgeConfidenceRecipe
    worker=request['worker']
    local_config=dict(worker['config'])
    local_config.update(project_root=root,source_root=root/'artifacts/akt/dependencies/upstream',
                        output_dir=root/'experiments/akt/results'/worker['logical_run_id'])
    local_config['betas']=tuple(local_config['betas'])
    if local_config.get('recovery') is not None:
        raise ValueError('Resume được cấp riêng theo checkpoint, không nhận recovery config khác')
    validate_config(AKTConfig(**local_config),cuda_profile=ResearchCUDAExecutionProfile(**worker['profile']))
    if worker['variant'] not in ('A2','A3') or worker['validation_batch_size']!=128:
        raise ValueError('Chỉ chuẩn bị A2/A3 expert theo batch128')
    def original(name):
        pin=request['local_files'].get(name)
        path=owned_input(root,pin['path'] if pin is not None else name)
        if pin is not None and sha(path)!=pin['sha256']:
            raise ValueError('Input local thay đổi')
        return path
    reference_path=original(worker['comparison_reference_file'])
    if sha(reference_path)!=worker['comparison_reference_sha256']:
        raise ValueError('A0 reference sai SHA')
    reference=json.loads(reference_path.read_text())['reference']
    peers=[]
    for name in ('a0_model_index','a1_model_index'):
        index_path=original(worker[name])
        peer=json.loads(index_path.read_text())
        checkpoint=index_path.parent/peer['checkpoint_file']
        if not checkpoint.is_file() or sha(checkpoint)!=peer['checkpoint_sha256']:
            raise ValueError('Không xác minh được model A0/A1 đã nghiệm thu')
        peers.append(peer)
    matched_fields=validate_baseline_metadata(worker,reference,peers)
    data=worker['inputs']
    inputs=load_full_selected_cache(original(data['selected_cache_root']),original(data['roles_path']),
        expected_manifest_sha256=data['selected_cache_manifest_sha256'],expected_roles_sha256=data['roles_sha256'])
    encoding=load_prepared_junyi_encoding(original(data['encoding_file']),original(data['encoding_receipt']),
        view=inputs.train,source_data_sha256=inputs.source_identity,
        expected_file_sha256=data['encoding_sha256'],expected_receipt_sha256=data['encoding_receipt_sha256'])
    confidence=load_binding(original(worker['confidence_file']),expected_sha256=worker['confidence_sha256'])
    recipe=EdgeConfidenceRecipe('train-lagged-edge-confidence-v1',42,3,1.,5.,1.,1e-6,200,1e-6,200,20)
    if confidence.recipe_identity!=recipe.identity:
        raise ValueError('Confidence khác recipe đã chốt')
    fit=original(worker['confidence_fit_artifact'])
    if sha(fit)!=confidence.fit_artifact_sha256:
        raise ValueError('Artifact fit confidence không khớp lineage')
    if fit.stat().st_size>8*1024**2:
        raise ValueError('Fit manifest phải là metadata hữu hạn')
    fitted=json.loads(fit.read_text())
    if (fitted.get('status')!='COMPLETE_FULL_TRAIN80_CONFIDENCE'
            or fitted.get('train_view_identity')!=inputs.train.identity
            or fitted.get('encoding_identity')!=encoding.identity
            or fitted.get('recipe_identity')!=recipe.identity
            or fitted.get('all_train_targets_seen')!=inputs.train_targets
            or fitted.get('window_manifest_sha256')!=data['train_window_manifest_sha256']
            or fitted.get('topology_source_sha256')!=worker['graph_sha256']
            or fitted.get('history_scope')!='effective_native_window_prefix'
            or fitted.get('semantics')!='conditional_predictive_stability_not_edge_truth_probability'
            or fitted.get('uses_oracle_labels') is not False
            or fitted.get('full_role_coverage') is not True):
        raise ValueError('Confidence chưa có bằng chứng fit đầy đủ TRAIN80')
    graph=original(worker['graph_file'])
    if sha(graph)!=worker['graph_sha256']:
        raise ValueError('Topology sai SHA')
    topology=json.loads(graph.read_text())
    condition=JunyiGraphCondition(encoding,
        PrerequisiteGraph.from_edges(topology['nodes'],topology['corrected_edges']),worker['graph_sha256'],
        variant=worker['variant'],confidence=confidence)
    admitted=JunyiWindowCacheSession(original(data['train_window_cache']),inputs.train,encoding,
        inputs.source_identity,inputs.train_targets,data['train_window_manifest_sha256'],
        admission_receipt=original(worker['train_admission_file']),
        expected_admission_sha256=worker['train_admission_sha256'])
    cache_options,cache_pins=prepared_cache_options(worker,original)
    selection=SelectionCacheSession(cache_options['selection_window_cache'],view=inputs.selection,
        encoding=encoding,source_sha256=inputs.source_identity,expected_targets=inputs.selection_targets,
        expected_manifest_sha256=cache_options['expected_selection_cache_manifest_sha256'],
        admission_file=cache_options['selection_cpu_admission_file'],
        expected_admission_sha256=cache_options['expected_selection_cpu_admission_sha256'],
        window_admission_file=cache_options['selection_window_admission_file'],
        expected_window_admission_sha256=cache_options['expected_selection_window_admission_sha256'])
    if selection.manifest['population_sha256']!=reference['selection_population_sha256']:
        raise ValueError('Selection CPU cache population differs from A0/A1')
    for scope,view,manifest,targets in (
        ('train',inputs.train,data['train_window_manifest_sha256'],inputs.train_targets),
        ('selection',inputs.selection,selection.manifest['window_manifest_sha256'],
         inputs.selection_targets-dict(selection.windows._summary)['unseen_targets'])):
        cached=GraphContextCache.open(cache_options[scope+'_graph_context_cache'],
            cache_options['expected_'+scope+'_graph_context_cache_sha256'],
            JunyiGraphPhaseSession(condition,view),dataset_sha256=inputs.source_identity,
            window_manifest_sha256=manifest)
        if cached.targets!=targets:
            raise ValueError('Graph context cache target population differs')
    if (inputs.train_targets!=reference['train_targets'] or inputs.selection_targets!=reference['selection_targets']
            or inputs.train.identity!=reference['train_view_identity'] or encoding.identity!=reference['encoding_identity']):
        raise ValueError('Population hoặc encoding khác baseline')
    if worker['config']['run_id']!=worker['logical_run_id']:
        raise ValueError('Logical run khác config')
    if worker['config']['output_dir']!='/opt/kltn/experiments/akt/results/'+worker['logical_run_id']:
        raise ValueError('GPU output phải thuộc đúng logical run mới')
    if any(worker['logical_run_id']==peer['metadata']['identity']['config']['run_id'] for peer in peers):
        raise ValueError('Không tái sử dụng output A0/A1')
    if worker['config']['project_root']!='/opt/kltn' or worker['config']['execution_enabled'] is not True:
        raise ValueError('Config GPU phải trỏ project đã mount và có execution flag')
    if worker['config']['source_root']!='/opt/kltn/artifacts/akt/dependencies/upstream':
        raise ValueError('GPU phải dùng đúng upstream đã ghim')
    if worker['purpose']=='main_selected' and worker['workload_epochs']!=20:
        raise ValueError('Main selected giữ workload tối đa20epoch như A0/A1')
    return dict(training_fields_matched=matched_fields,train_targets=inputs.train_targets,
        selection_targets=inputs.selection_targets,condition_identity=condition.identity,
        confidence_identity=confidence.identity,admitted_records=admitted.strict_records_verified,
        prepared_cache_pins=cache_pins,
        a0_epoch_ranking_batch128_replayed=False)


def main():
    from junyi_staged_io import prepare_project,sha,write_new
    from knowledge_tracing.akt.authorization import require_gate2_evidence
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--snapshot',type=Path,required=True)
    args=parser.parse_args()
    request=json.loads(args.request.read_text(encoding='utf-8'))
    checked=validate_recipe(ROOT,request)
    prepared=prepare_project(ROOT,request,args.snapshot)
    project=args.snapshot.resolve()/'project'
    worker=request['worker']
    gate=require_gate2_evidence(SimpleNamespace(source_commit=worker['config']['source_commit']),
        project_root=project,gate2_report=project/'artifacts/akt/preflight/gate2-current.json',
        lock_file=project/worker['runtime_lock_file'])
    if sha(project/worker['runtime_lock_file'])!=worker['runtime_lock_sha256']:
        raise ValueError('Runtime lock sai SHA')
    checked.update(status='PASS_LOCAL_STAGE_INPUTS',gate_report_sha256=gate['report_sha256'],
        inputs_sha256=sha(args.snapshot/'INPUTS.json'),
        worker_request_sha256=sha(project/'gpu-stage-request.json'),gpu_started=False)
    write_new(args.snapshot/'CPU_CHECK.json',checked)
    print(json.dumps(checked,ensure_ascii=False))


if __name__=='__main__':
    main()
