"""Snapshot loader thật và backbone CPU nhỏ; chưa từng train dữ liệu nghiên cứu."""
from dataclasses import asdict
import hashlib
import json
import sys
import zipfile

import psutil
import pytest


@pytest.mark.parametrize('variant',['A0','A1','A2','A3'])
def test_native_refit_export_to_calibration_and_consumer(tmp_path,monkeypatch,variant):
    required_mib=256 if 'torch' in sys.modules else 1024
    before_available=psutil.virtual_memory().available
    before_rss=psutil.Process().memory_info().rss
    if before_available<required_mib*1024**2:
        pytest.skip(f'Native toy cần {required_mib} MiB RAM trống tại bước hiện tại, là estimate engineering.')
    import torch
    from knowledge_tracing.akt import research_junyi_calibration as producer
    from knowledge_tracing.akt import research_graph_model as graph_native
    from knowledge_tracing.akt import research_junyi_graph_model as graph_model
    from knowledge_tracing.akt import prediction,data
    from knowledge_tracing.akt.checkpoint import save_checkpoint
    from knowledge_tracing.akt.config import AKTConfig,DataPaths
    from knowledge_tracing.akt.encoding import ExerciseEncoding
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition,JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_confidence_binding import JunyiConfidenceBinding
    from knowledge_tracing.akt.research_graph_condition import OperationalEdgeWeight
    from knowledge_tracing.akt.types import KTEvent,LearnerEvents
    from knowledge_tracing.shared_kt import StableVocabulary,PrerequisiteGraph
    from knowledge_tracing.response_calibration import PredictionBinding
    from knowledge_tracing.akt.evaluation import iter_calibrated_predictions
    monkeypatch.setattr(graph_native,'validate_config',lambda *a,**k:None)
    monkeypatch.setattr(graph_model,'validate_config',lambda *a,**k:None)
    monkeypatch.setattr(torch.cuda,'is_available',lambda:False)
    monkeypatch.setattr(prediction,'PROJECT_ROOT',tmp_path)
    torch.set_num_threads(1)
    roles=make_junyi_research_roles([(str(i),i%5,'development') for i in range(20)])
    train=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    refit=JunyiPhaseView(roles,'refit_union90',tuple(sorted((*roles.train_users,*roles.selection_users))),roles.identity)
    phase=JunyiPhaseView(roles,'calibration_predict',roles.calibration_users,roles.identity)
    native=ExerciseEncoding(StableVocabulary(('A','B')),dict(A=2,B=2))
    encoding=JunyiResearchEncoding(native,refit)
    origin=JunyiResearchEncoding(native,train)
    config=AKTConfig(phase='junyi-research',outer_fold=4,d_model=16,heads=2,d_ff=32,final_fc=16,batch_size=2)
    if variant=='A0':
        adapter=AKTAdapter(config,native)
        condition=None
    else:
        graph=PrerequisiteGraph.from_edges(('A','B'),(('A','B'),))
        confidence=JunyiConfidenceBinding(train.identity,origin.identity,'a'*64,'b'*64,'c'*64,
            (OperationalEdgeWeight('A','B',True,.75,None,.75),))
        condition=JunyiGraphCondition(encoding,graph,'a'*64,variant=variant,
            confidence=None if variant=='A1' else confidence,train80_origin=origin)
        adapter=graph_model.JunyiGraphAKTAdapter(config=config,encoding=encoding,condition=condition,
            phase=JunyiGraphPhaseSession(condition,refit),compact_context=True)
    export=tmp_path/'compact-export'
    export.mkdir()
    checkpoint=export/(variant+'_JUNYI_REFIT.pt')
    identity=dict(phase='junyi_refit90',variant=variant,encoding=encoding.identity,
                  condition=None if condition is None else condition.identity,purpose='synthetic_loader_fixture')
    history=[dict(epoch=1)]
    save_checkpoint(checkpoint,adapter,type('EmptyOptimizer',(),{'state_dict':lambda self:{}})(),
                    identity=identity,progress=dict(complete=True,role='junyi_refit90',epoch=1,history=history))
    checkpoint_sha=producer.sha256_file(checkpoint)
    payloads={
        'inputs/config.json':json.loads(json.dumps(asdict(config),default=str)),
        'inputs/roles.json':asdict(roles),'run-manifest.json':identity,
        'metadata.json':dict(identity=identity,checkpoint_sha256=checkpoint_sha),
        'COMPLETE.json':dict(status='JUNYI_REFIT90_COMPLETE',frozen_epochs=1,complete_epochs=1,checkpoint_sha256=checkpoint_sha)}
    inventory={}
    with zipfile.ZipFile(export/'SUPPORT.zip','x') as archive:
        for name,value in payloads.items():
            raw=json.dumps(value).encode()
            archive.writestr(name,raw)
            inventory[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        archive.writestr('INVENTORY.json',json.dumps(inventory))
    index=dict(model=variant+'_JUNYI_REFIT',phase='refit90',identity=identity,epochs=1,
        checkpoint_file=checkpoint.name,checkpoint_bytes=checkpoint.stat().st_size,
        checkpoint_sha256=checkpoint_sha,support_sha256=producer.sha256_file(export/'SUPPORT.zip'))
    (export/'MODEL_INDEX.json').write_text(json.dumps(index))
    binding=PredictionBinding('synthetic_'+variant,checkpoint_sha,encoding.identity,roles.identity,
        'a'*64,'b'*64,producer.inference_source_identity(),'c'*64)
    attached=producer.attach_refit_export(adapter,encoding,export,
        expected_index_sha256=producer.sha256_file(export/'MODEL_INDEX.json'),binding=binding,
        max_checkpoint_bytes=1024**2)
    assert attached.receipt['training_identity']==identity
    assert index['identity']==identity
    paths=DataPaths(tmp_path/'unused',tmp_path/'unused',tmp_path/'source.json',tmp_path/'roles.json')
    paths.canonical_manifest.write_text('{"fixture":"synthetic"}')
    paths.split_manifest.write_text(json.dumps(asdict(roles)))
    pins={name:producer.sha256_file(getattr(paths,name)) for name in ('canonical_manifest','split_manifest')}
    learners=tuple(LearnerEvents(user,int(user)%5,tuple(KTEvent(user,item,i+1,j*10+i+1,i%2,0,int(user)%5)
        for i,item in enumerate(('A','B','unknown','A')))) for j,user in enumerate(phase.users))
    monkeypatch.setattr(data,'iter_development_learners',lambda *a,**k:iter(learners))
    population=producer.prepare_calibration_population(paths,phase,source_pins=pins,max_targets=8,max_learner_events=4)
    calibration=producer.fit_refit_response_calibration(attached,paths,phase,population=population,
        expected_population_identity=population['identity'],source_pins=pins,max_targets=8,max_learner_events=4,
        prediction_batch_size=2,output=tmp_path/'experiments/akt/results/calibration')
    assert calibration.total_targets==8 and calibration.supported_targets==6
    assert calibration.status=='fitted_response_temperature'
    raw=list(prediction.iter_predictions(adapter,iter(learners)))
    assert len(tuple(iter_calibrated_predictions(raw,calibration=calibration,binding=binding)))==8
    (tmp_path/'native-resources.json').write_text(json.dumps(dict(
        variant=variant,available_before=before_available,rss_before=before_rss,
        rss_after=psutil.Process().memory_info().rss,available_after=psutil.virtual_memory().available,
        peak_working_set=psutil.Process().memory_info()._asdict().get('peak_wset'),
        checkpoint_bytes=checkpoint.stat().st_size,resource_guard_mib=required_mib,
        scope='synthetic tiny CPU model, no training, CUDA detection mocked false')))
