"""Outer numeric→raw/calibrated compact bằng2learner tổng hợp."""
from dataclasses import asdict,replace
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from knowledge_tracing.akt.config import DataPaths
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
from knowledge_tracing.akt.prediction_batch import prepare_prediction_windows
from knowledge_tracing.akt.research_junyi_numeric_predictions import NumericBinding,NumericWindow,write_numeric_shard
from knowledge_tracing.akt.research_junyi_window_cache import window_cache_key
from knowledge_tracing.akt.types import KTEvent,LearnerEvents,UnseenTarget
from knowledge_tracing.response_calibration import PredictionBinding,TemperatureCalibration,implementation_identity,calibrate_probability
from knowledge_tracing.shared_kt import StableVocabulary
from scripts.akt import outer_numeric_cpu_export as worker


def write(path,value):
    path.write_text(json.dumps(value),encoding='utf-8')
    return worker.sha(path)


@pytest.fixture
def outer_case(tmp_path,monkeypatch):
    roles=JunyiResearchRoles(('t',),('s',),('c',),('o','o2'))
    fit=JunyiPhaseView(roles,'refit_union90',('s','t'),roles.identity)
    view=JunyiPhaseView(roles,'outer_evaluation',('o','o2'),roles.identity)
    encoding=JunyiResearchEncoding(ExerciseEncoding(StableVocabulary(('known',)),{'known':1}),fit)
    learners=tuple(LearnerEvents(user,4,tuple(KTEvent(user,item,10+i,1+index*3+i,i%2,i%2,4)
        for i,item in enumerate(('known','new','known')))) for index,user in enumerate(view.users))
    from knowledge_tracing.akt import research_junyi_data as reader
    monkeypatch.setattr(reader,'iter_junyi_phase_learners',lambda paths,view:iter(learners))
    paths=DataPaths(*(tmp_path/name for name in ('canonical.parquet','assignments.parquet','source.json','split.json')))
    paths.canonical.write_bytes(b'synthetic canonical source');paths.assignments.write_bytes(b'synthetic roles')
    source_sha=worker.sha(paths.canonical)
    source=dict(status='FULL_OUTER_SOURCE_PREPARED',purpose='JUNYI_REFIT90_OUTER_EVALUATION_SOURCE',
        phase_identity=view.identity,roles_identity=roles.identity,encoding_identity=encoding.identity,
        holdout_events_included=False,
        counts=dict(targets=6,oov_targets=2,learners=2),outputs={p.name:dict(bytes=p.stat().st_size,sha256=worker.sha(p))
        for p in (paths.canonical,paths.assignments)})
    write(paths.canonical_manifest,source);write(paths.split_manifest,{'synthetic':True})
    pins={name:worker.sha(getattr(paths,name)) for name in ('canonical_manifest','split_manifest')}
    source_id=inference_source_identity()
    binding=PredictionBinding('A0_JUNYI_REFIT','a'*64,encoding.identity,roles.identity,'b'*64,'c'*64,source_id,source_sha)
    calibration=TemperatureCalibration(replace(binding,domain_sha256='e'*64),'f'*64,'1'*64,implementation_identity(),
        'fitted_response_temperature',2.,5,2,2,(1,1),(),.5,.4)
    adapter=SimpleNamespace(config=SimpleNamespace(context=100,target_block=100,batch_size=128),
        encoding=encoding.native,checkpoint_id=binding.checkpoint_sha256)
    prepared=list(prepare_prediction_windows(adapter,learners));windows=[entry[0] for entry in prepared if not isinstance(entry,UnseenTarget)]
    summary=dict(records=len(prepared),windows=len(windows),unseen_targets=2,target_rows=6,
        window_tokens=sum(len(w.target_mask) for w in windows),learners=2)
    key=window_cache_key(view,encoding,source_sha,expected_target_rows=6)
    manifest=tmp_path/'manifest.json';manifest_sha=write(manifest,dict(status='COMPLETE',key=key,summary=summary,shards=[]))
    admission=tmp_path/'admission.json';admission_sha=write(admission,dict(kind='JUNYI_CPU_WINDOW_ADMISSION_V1',
        key=key,manifest_sha256=manifest_sha,summary=summary,shards=[],strict_records_verified=summary['records']))
    cache=dict(status='JUNYI_OUTER_CPU_CACHES_COMPLETE',phase='outer_evaluation',phase_identity=view.identity,
        roles_identity=roles.identity,encoding_identity=encoding.identity,source_pins=pins,
        source_data_sha256=source_sha,dataset_sha256=worker.sha(paths.canonical_manifest),
        windows=dict(path=str(tmp_path),manifest_sha256=manifest_sha,summary=summary,
            admission_path=str(admission),admission_sha256=admission_sha),graphs={})
    cache_path=tmp_path/'cache.json';cache_sha=write(cache_path,cache)
    numeric=NumericBinding('A0',binding.checkpoint_sha256,binding.checkpoint_sha256,view.identity,encoding.identity,manifest_sha,source_id)
    shard=write_numeric_shard(tmp_path,'numeric',[NumericWindow.from_window(w) for w in windows],
        [np.full(len(w.target_mask),.8,dtype=np.float64) for w in windows],binding=numeric,shard_index=0)
    gpu=dict(kind='JUNYI_CACHED_NUMERIC_INFERENCE_V1',status='COMPLETE',binding=asdict(numeric),roles_sha256=roles.identity,
        source_data_sha256=source_sha,dataset_sha256=cache['dataset_sha256'],window_admission_sha256=admission_sha,
        graph_cache_identity=None,counts=dict(records=len(prepared),windows=len(windows),targets=6,fitted_targets=4,oov_targets=2),
        shards=[dict(manifest_path=str(shard.manifest_path),manifest_sha256=shard.manifest_sha256)])
    gpu_path=tmp_path/'GPU.json';gpu_sha=write(gpu_path,gpu)
    arguments=dict(binding=binding,calibration=calibration,calibration_data_sha256='e'*64,compatibility=None,
        cache_receipt=cache_path,cache_sha256=cache_sha,gpu_receipt=gpu_path,gpu_sha256=gpu_sha,source_pins=pins,
        expected_source_sha256=source_id,output=tmp_path/'export',max_learner_events=3,rows_per_shard=2)
    return paths,view,encoding,arguments


def test_export_known_oov_and_public_calibration_exact(outer_case):
    import pyarrow.parquet as pq
    paths,view,encoding,args=outer_case
    result=worker.export_outer_numeric(paths,view,encoding,**args)
    assert (result['targets'],result['fitted_targets'],result['oov_targets'],result['learners'])==(6,4,2,2)
    assert len(result['files'])==3 and all(row['rows']<=2 for row in result['files'])
    rows=pq.read_table([str(args['output']/row['path']) for row in result['files']]).to_pylist()
    assert [row['source_row'] for row in rows]==list(range(1,7))
    for row in rows:
        assert row['prediction']==row['raw_prediction']
        if row['prediction_kind']=='unseen':
            assert row['raw_prediction'] is None and row['calibrated_prediction'] is None
        else:
            assert row['calibrated_prediction']==calibrate_probability(row['raw_prediction'],
                calibration=args['calibration'],binding=args['calibration'].binding)
    metrics=worker.score_export(args['output'],expected_complete_sha256=worker.sha(args['output']/'COMPLETE.json'))
    assert metrics['predicted_targets']==4 and metrics['oov_targets']==2
    assert metrics['raw']['log_loss']!=metrics['calibrated']['log_loss']


@pytest.mark.parametrize('damage',['source','calibrator','phase','counts','cache','numeric_payload','checkpoint','source_bytes','roles'])
def test_mismatch_never_complete(outer_case,damage):
    paths,view,encoding,args=outer_case
    if damage=='source': args['expected_source_sha256']='9'*64
    if damage=='calibrator': args['calibration']=replace(args['calibration'],binding=replace(args['calibration'].binding,checkpoint_sha256='9'*64))
    if damage in ('phase','counts'):
        gpu=json.loads(args['gpu_receipt'].read_text())
        if damage=='phase': gpu['binding']['phase_sha256']='9'*64
        else: gpu['counts']['targets']+=1
        args['gpu_sha256']=write(args['gpu_receipt'],gpu)
    if damage=='cache': args['cache_sha256']='9'*64
    if damage=='checkpoint': args['binding']=replace(args['binding'],checkpoint_sha256='9'*64)
    if damage=='source_bytes': paths.canonical.write_bytes(b'changed source')
    if damage=='roles': view=JunyiPhaseView(view.roles,'outer_evaluation',('o',),view.roles.identity)
    if damage=='numeric_payload':
        path=args['gpu_receipt'].parent/'numeric.npz';path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError):
        worker.export_outer_numeric(paths,view,encoding,**args)
    assert not (args['output']/'COMPLETE.json').exists()


def test_numeric_window_coverage_refused(outer_case):
    paths,view,encoding,args=outer_case
    gpu=json.loads(args['gpu_receipt'].read_text())
    gpu['shards']=[]
    args['gpu_sha256']=write(args['gpu_receipt'],gpu)
    with pytest.raises(ValueError,match='numeric windows missing'):
        worker.export_outer_numeric(paths,view,encoding,**args)
    assert not (args['output']/'COMPLETE.json').exists()


def test_cli_import_is_torch_free():
    import subprocess,sys
    subprocess.run([sys.executable,'-B','-c','import scripts.akt.outer_numeric_cpu_export; import sys; assert "torch" not in sys.modules'],
        capture_output=True,text=True,check=True)


def test_posix_cloud_metadata_paths_relocate_on_windows_without_rewriting_pins(outer_case):
    paths,view,encoding,args=outer_case
    cache=json.loads(args['cache_receipt'].read_text());gpu=json.loads(args['gpu_receipt'].read_text())
    old_window=cache['windows']['path'];old_admission=cache['windows']['admission_path']
    old_shard=gpu['shards'][0]['manifest_path']
    cloud='/__modal/volumes/test/outer-window'
    cache['windows']['path']=cloud
    cache['windows']['admission_path']=cloud+'/ADMISSION.json'
    gpu['shards'][0]['manifest_path']='/__modal/volumes/test/numeric/manifest.json'
    args['cache_sha256']=write(args['cache_receipt'],cache);args['gpu_sha256']=write(args['gpu_receipt'],gpu)
    args['path_map']={cloud+'/manifest.json':str(Path(old_window)/'manifest.json'),
        cloud+'/ADMISSION.json':old_admission,'/__modal/volumes/test/numeric/manifest.json':old_shard}
    receipt=worker.export_outer_numeric(paths,view,encoding,**args)
    assert receipt['targets']==6
