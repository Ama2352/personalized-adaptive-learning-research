"""Producer bằng dữ liệu tổng hợp, predictor giả và reader Parquet nhỏ."""
from dataclasses import asdict,replace
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from knowledge_tracing.akt.config import AKTConfig,DataPaths
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
from knowledge_tracing.akt.types import KTEvent,LearnerEvents,PredictionRecord
from knowledge_tracing.akt import research_junyi_calibration as producer
from knowledge_tracing.akt.prediction import iter_predictions
from knowledge_tracing.akt.evaluation import iter_calibrated_predictions
from knowledge_tracing.response_calibration import PredictionBinding
from knowledge_tracing.shared_kt import StableVocabulary


@pytest.fixture
def case(tmp_path,monkeypatch):
    from knowledge_tracing.akt import data,prediction
    roles=make_junyi_research_roles([(str(i),i%5,'development') for i in range(20)])
    refit=JunyiPhaseView(roles,'refit_union90',tuple(sorted((*roles.train_users,*roles.selection_users))),roles.identity)
    phase=JunyiPhaseView(roles,'calibration_predict',roles.calibration_users,roles.identity)
    native=ExerciseEncoding(StableVocabulary(('A','B')),dict(A=2,B=2))
    encoding=JunyiResearchEncoding(native,refit)
    paths=DataPaths(tmp_path/'events.parquet',tmp_path/'assignments.parquet',
                    tmp_path/'canonical-manifest.json',tmp_path/'roles.json')
    paths.canonical_manifest.write_text('{"purpose":"synthetic_test"}')
    paths.split_manifest.write_text(json.dumps(asdict(roles)))
    pins={name:producer.sha256_file(getattr(paths,name)) for name in ('canonical_manifest','split_manifest')}
    learners=[]
    for j,user in enumerate(phase.users):
        fold=int(user)%5
        events=tuple(KTEvent(user,'unknown' if i==4 else ('A' if i%2==0 else 'B'),
            100+i,j*100+i+1,int(i<6),0,fold) for i in range(10))
        learners.append(LearnerEvents(user,fold,events))
    original=data.iter_development_learners
    def reader(_paths,*,user_ids,**options):
        return iter(row for row in learners if row.user_id in user_ids)
    monkeypatch.setattr(data,'iter_development_learners',reader)
    monkeypatch.setattr(prediction,'PROJECT_ROOT',tmp_path)
    config=AKTConfig(phase='junyi-research',outer_fold=4,batch_size=2,d_model=16,heads=2,d_ff=32,final_fc=16)
    class Predictor:
        def predict_window(self,window):
            return self.predict_windows([window])[0]
        def predict_windows(self,windows):
            return [np.full(len(window.inputs.item_ids),.9) for window in windows]
    adapter=Predictor()
    adapter.config=config
    adapter.encoding=native
    buffers={}
    adapter.native=SimpleNamespace(parameters=lambda:iter(()),named_parameters=lambda:iter(()),
                                   named_buffers=lambda:iter(buffers.items()))
    adapter.checkpoint_id='a'*64
    binding=PredictionBinding('synthetic-refit-predictor','a'*64,encoding.identity,roles.identity,
        'b'*64,'c'*64,producer.inference_source_identity(),'d'*64)
    receipt=dict(checkpoint_sha256=binding.checkpoint_sha256,
        inference_source_sha256=binding.model_source_sha256,training_identity=dict(purpose='synthetic_only'),
        native_state_seal=producer._native_seal(adapter.native),
        inference_config=json.loads(json.dumps(asdict(config),default=str)),graph_enabled=None)
    attached=producer.RefitCalibrationPredictor(adapter,encoding,binding,receipt)
    population=producer.prepare_calibration_population(paths,phase,source_pins=pins,max_targets=20,max_learner_events=10)
    return dict(roles=roles,phase=phase,encoding=encoding,paths=paths,pins=pins,learners=learners,
        adapter=adapter,binding=binding,attached=attached,population=population,original_reader=original,
        output=tmp_path/'experiments/akt/results/calibration',buffers=buffers)


def observations(case,records=None,**kwargs):
    if records is None:
        records=iter_predictions(case['adapter'],iter(case['learners']))
    return producer.iter_calibration_observations(records,iter(case['learners']),view=case['phase'],
        binding=case['binding'],population=case['population'],max_targets=20,max_learner_events=10,**kwargs)


def test_raw_export_preserves_explicit_graph_context_cache_on_phase_transition(case,monkeypatch):
    from knowledge_tracing.akt import research_junyi_graph
    cache=object()
    phase=object()
    seen=[]
    case['adapter'].condition=SimpleNamespace(identity=None)
    case['adapter'].set_phase=lambda value,**kwargs:seen.append((value,kwargs))
    monkeypatch.setattr(research_junyi_graph,'JunyiGraphPhaseSession',lambda *_:phase)
    producer.export_refit_calibration_predictions(case['attached'],case['paths'],case['phase'],
        population=case['population'],expected_population_identity=case['population']['identity'],
        source_pins=case['pins'],max_targets=20,max_learner_events=10,prediction_batch_size=2,
        output=case['output']/'cached-raw',context_cache=cache)
    assert seen==[(phase,dict(context_cache=cache))]


def test_raw_targets_keep_oov_and_warmup(case):
    rows=list(observations(case))
    assert len(rows)==20
    assert sum(target.probability is None for _,target,_ in rows)==2
    assert rows[0][0].history_available==rows[0][0].history_used==0
    assert rows[0][1].event_id==str(case['learners'][0].events[0].source_row)
    assert rows[5][0].context_reset and rows[5][0].history_used==0
    assert all(target.history_sha256==key[3] for _,target,key in rows)


def test_prefix_excludes_current_and_future_labels(case):
    learner=case['learners'][0]
    rows=list(producer._expected_rows(case['learners'],case['phase'],max_targets=20,max_learner_events=10))
    changed=replace(learner,events=tuple(replace(e,correct=1-e.correct) if i==3 else e for i,e in enumerate(learner.events)))
    after=list(producer._expected_rows([changed,*case['learners'][1:]],case['phase'],max_targets=20,max_learner_events=10))
    assert [key for _,key in rows[:4]]==[key for _,key in after[:4]]
    assert rows[4][1][3]!=after[4][1][3]
    future=replace(learner,events=tuple(replace(e,correct=1-e.correct) if i==8 else e for i,e in enumerate(learner.events)))
    future_rows=list(producer._expected_rows([future,*case['learners'][1:]],case['phase'],max_targets=20,max_learner_events=10))
    assert [key for _,key in rows[:9]]==[key for _,key in future_rows[:9]]


@pytest.mark.parametrize('oov_rank',[99,100,199])
def test_window_overlap_and_oov_barrier_keep_exact_population(case,oov_rank):
    for j,learner in enumerate(case['learners']):
        events=tuple(KTEvent(learner.user_id,'unknown' if i==oov_rank else 'A',
            100+i,j*1000+i+1,i%2,0,learner.fold) for i in range(205))
        case['learners'][j]=replace(learner,events=events)
    population=producer.prepare_calibration_population(case['paths'],case['phase'],source_pins=case['pins'],
        max_targets=410,max_learner_events=205)
    rows=list(producer.iter_calibration_observations(
        iter_predictions(case['adapter'],iter(case['learners'])),iter(case['learners']),
        view=case['phase'],binding=case['binding'],population=population,max_targets=410,max_learner_events=205))
    assert len(rows)==410 and len({key for _,_,key in rows})==410
    assert len({record.source_row for record,_,_ in rows})==410
    assert rows[oov_rank][1].probability is None
    after=rows[oov_rank+1][0]
    assert after.context_reset and after.history_used==0


@pytest.mark.parametrize('mode',['missing','extra','label','item','checkpoint','order'])
def test_prediction_mismatch_rejected(case,mode):
    records=list(iter_predictions(case['adapter'],iter(case['learners'])))
    if mode=='missing': records.pop()
    if mode=='extra': records.append(records[-1])
    if mode=='label': records[0]=replace(records[0],correct=1-records[0].correct)
    if mode=='item': records[0]=replace(records[0],exercise='B')
    if mode=='checkpoint': records[0]=replace(records[0],checkpoint_id='e'*64)
    if mode=='order': records[:2]=reversed(records[:2])
    with pytest.raises(ValueError):list(observations(case,records))


def test_population_prefix_or_role_change_rejected(case):
    for field in ('prefix_keys_sha256','roles_identity'):
        population=dict(case['population']);population[field]='0'*64
        population['identity']=producer._identity({k:v for k,v in population.items() if k!='identity'})
        original=case['population'];case['population']=population
        with pytest.raises(ValueError):list(observations(case))
        case['population']=original


def test_source_metadata_change_rejected(case):
    case['paths'].canonical_manifest.write_text('changed')
    with pytest.raises(ValueError,match='metadata changed'):
        producer.prepare_calibration_population(case['paths'],case['phase'],source_pins=case['pins'],
            max_targets=20,max_learner_events=10)


def test_target_and_learner_caps_rejected(case):
    with pytest.raises(ValueError,match='target memory cap'):
        producer.prepare_calibration_population(case['paths'],case['phase'],source_pins=case['pins'],
            max_targets=19,max_learner_events=10)
    with pytest.raises(ValueError,match='scope/size'):
        producer.prepare_calibration_population(case['paths'],case['phase'],source_pins=case['pins'],
            max_targets=20,max_learner_events=9)


@pytest.mark.parametrize('batch',[None,2])
def test_full_wiring_raw_export_fit_temperature_and_consumer(case,batch):
    calibration=producer.fit_refit_response_calibration(case['attached'],case['paths'],case['phase'],
        population=case['population'],expected_population_identity=case['population']['identity'],
        source_pins=case['pins'],max_targets=20,max_learner_events=10,
        prediction_batch_size=batch,output=case['output'])
    assert calibration.status=='fitted_response_temperature'
    assert calibration.total_targets==20 and calibration.supported_targets==18
    assert calibration.calibrated_log_loss<=calibration.raw_log_loss
    raw=list(iter_predictions(case['adapter'],iter(case['learners'])))
    calibrated=list(iter_calibrated_predictions(raw,calibration=calibration,binding=case['binding']))
    assert calibrated[0].prediction==pytest.approx(5/9,abs=1e-7)
    assert calibrated[4] is raw[4]
    manifest=json.loads((case['output']/'fit/manifest.json').read_text())
    assert manifest['raw_export']['prediction_rows']==20
    assert (case['output']/'fit/temperature.json').is_file()


@pytest.mark.parametrize('kind',['condition','buffer_add','buffer_update','buffer_replace'])
def test_graph_or_buffer_mutation_rejected_before_prediction(case,kind,monkeypatch):
    if kind.startswith('buffer_'):
        value=SimpleNamespace(_version=0,shape=(1,),dtype='float32',device='cpu')
        if kind!='buffer_add':
            case['buffers']['state']=value
            case['attached'].receipt['native_state_seal']=producer._native_seal(case['adapter'].native)
        if kind=='buffer_update':value._version+=1
        elif kind=='buffer_replace':
            case['buffers']['state']=SimpleNamespace(_version=0,shape=(1,),dtype='float32',device='cpu')
        else:case['buffers']['state']=value
    else:
        case['adapter'].condition=SimpleNamespace(identity='changed')
    monkeypatch.setattr(case['adapter'],'predict_window',lambda *_:pytest.fail('Must reject before prediction'))
    with pytest.raises(ValueError,match='condition changed|parameters/buffers changed'):
        producer.export_refit_calibration_predictions(case['attached'],case['paths'],case['phase'],
            population=case['population'],expected_population_identity=case['population']['identity'],
            source_pins=case['pins'],max_targets=20,max_learner_events=10,
            prediction_batch_size=2,output=case['output']/'raw')


def test_cpu_fit_after_releasing_predictor(case,monkeypatch):
    raw=case['output']/'raw'
    manifest=producer.export_refit_calibration_predictions(case['attached'],case['paths'],case['phase'],
        population=case['population'],expected_population_identity=case['population']['identity'],
        source_pins=case['pins'],max_targets=20,max_learner_events=10,prediction_batch_size=2,output=raw)
    pins={row['path']:producer.sha256_file(raw/row['path']) for row in manifest['shards']}
    binding=case['binding']
    case.pop('attached')
    case.pop('adapter')
    monkeypatch.setattr(producer,'iter_predictions',lambda *_:pytest.fail('CPU fit must not run inference'))
    calibration=producer.fit_response_temperature_from_raw_export(raw,case['paths'],case['phase'],binding=binding,
        population=case['population'],expected_population_identity=case['population']['identity'],
        expected_manifest_sha256=producer.sha256_file(raw/'manifest.json'),shard_sha256=pins,
        source_pins=case['pins'],max_targets=20,max_learner_events=10,output=case['output']/'cpu-fit')
    assert calibration.total_targets==20 and calibration.supported_targets==18


def test_cpu_fit_rejects_changed_parquet_shard(case):
    raw=case['output']/'raw'
    manifest=producer.export_refit_calibration_predictions(case['attached'],case['paths'],case['phase'],
        population=case['population'],expected_population_identity=case['population']['identity'],
        source_pins=case['pins'],max_targets=20,max_learner_events=10,prediction_batch_size=2,output=raw)
    pins={row['path']:producer.sha256_file(raw/row['path']) for row in manifest['shards']}
    with (raw/manifest['shards'][0]['path']).open('ab') as stream:stream.write(b'changed')
    with pytest.raises(ValueError,match='shard changed'):
        producer.fit_response_temperature_from_raw_export(raw,case['paths'],case['phase'],binding=case['binding'],
            population=case['population'],expected_population_identity=case['population']['identity'],
            expected_manifest_sha256=producer.sha256_file(raw/'manifest.json'),shard_sha256=pins,
            source_pins=case['pins'],max_targets=20,max_learner_events=10,output=case['output']/'cpu-fit')


def test_raw_export_rejects_existing_directory_before_prediction(case,monkeypatch):
    raw=case['output']/'raw'
    raw.mkdir(parents=True)
    monkeypatch.setattr(case['adapter'],'predict_window',lambda *_:pytest.fail('Must reject existing output'))
    with pytest.raises(ValueError,match='new raw calibration'):
        producer.export_refit_calibration_predictions(case['attached'],case['paths'],case['phase'],
            population=case['population'],expected_population_identity=case['population']['identity'],
            source_pins=case['pins'],max_targets=20,max_learner_events=10,prediction_batch_size=2,output=raw)


def test_materialization_guard_before_prediction(case,monkeypatch):
    import psutil
    monkeypatch.setattr(psutil,'virtual_memory',lambda:SimpleNamespace(available=1))
    with pytest.raises(MemoryError,match='materialization'):
        producer.fit_refit_response_calibration(case['attached'],case['paths'],case['phase'],
            population=case['population'],expected_population_identity=case['population']['identity'],
            source_pins=case['pins'],max_targets=20,max_learner_events=10,prediction_batch_size=2,output=case['output'])
    assert not case['output'].exists()


def test_synthetic_parquet_reader_through_normal_entrypoint(case,monkeypatch):
    import pandas as pd
    from knowledge_tracing.akt import data
    frame=pd.DataFrame([asdict(event) for learner in case['learners'] for event in learner.events])
    frame.to_parquet(case['paths'].canonical,index=False)
    pd.DataFrame([dict(user_id=str(i),fold=i%5,partition='development') for i in range(20)]).to_parquet(case['paths'].assignments,index=False)
    monkeypatch.setattr(data,'iter_development_learners',case['original_reader'])
    calibration=producer.fit_refit_response_calibration(case['attached'],case['paths'],case['phase'],
        population=case['population'],expected_population_identity=case['population']['identity'],
        source_pins=case['pins'],max_targets=20,max_learner_events=10,prediction_batch_size=2,output=case['output'])
    assert calibration.total_targets==20 and calibration.supported_targets==18
