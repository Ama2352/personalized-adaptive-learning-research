"""Mocked selected-only orchestration; no actual guard/Gate/NN/corpus certificate."""
from contextlib import nullcontext
from dataclasses import replace
from types import SimpleNamespace as N
import random
import pytest

from knowledge_tracing.akt import research_selected_runner as runner
from knowledge_tracing.akt.research_main_stage import prepare_main_selected_stage
from test_research_main_execution import make_case,H


def test_public_entry_rejects_noauth_stage_boolean_callable_before_lazy_model(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch)
    monkeypatch.setattr(runner,'require_main_selected_authorization',lambda *a,**k:pytest.fail('no actual spec; no guard/model'))
    monkeypatch.setattr(runner,'_tools',lambda:pytest.fail('no actual authorization; no lazy Torch'))
    for value in (True,lambda:True,prepare_main_selected_stage(c.spec.stage)):
        with pytest.raises(ValueError):runner.run_main_selected_candidate(value,c.evidence,authorization_file='missing',expected_authorization_sha256=H)


def test_epoch_reuses_native_api_and_final_progress_does_not_double_charge():
    events=[];seen={}
    run=N(stage=N(phase_inputs=lambda:('select_train80',(('train',H),))),
        budget=N(train_targets=2,max_optimizer_steps=3,max_optimized_targets=6,max_training_seconds=10.,max_wall_seconds=20.,
            max_rss_bytes=1024**3,min_available_ram_bytes=1024**3),
        config=N(context=100,target_block=100),reserved_steps=1,returned_steps=1,completed_steps=1,
        reserved_targets=2,returned_targets=2,completed_targets=2,batch_targets=None,
        training_started=None,training_spent=0.,guard=lambda:None,boundary=lambda:None,
        clocks=lambda:dict(training_seconds=0.,wall_seconds=0.),event=lambda kind,**k:events.append(kind))
    run.optimizer_event=lambda e:runner._Run.optimizer_event(run,e)
    adapter=N(set_context_index=lambda index:seen.setdefault('index',index),audit_context_boundary=lambda:None)
    class Tracker:
        pending=None
        def begin_epoch(self,e):seen['epoch']=e
        def collate(self,entries):
            adapter._ticket=N(context=((object(),object()),));self.pending={'placeholder':True};return 'LABELLED_BATCH_ONLY_FOR_NATIVE_TRAINER'
        def progress(self,event):self.pending=None
        def finish_epoch(self,stats):return 'MOCK_RECEIPT_NOT_EPOCH_ATTESTATION'
    tracker=Tracker();tracker.adapter=adapter
    def native_epoch(actual,factory,**kw):
        seen['budget']=kw['budget'];assert kw['recovery'] is None and actual is adapter
        assert kw['batch_factory'](tuple(factory()))=='LABELLED_BATCH_ONLY_FOR_NATIVE_TRAINER'
        run.optimizer_event(dict(kind='optimizer_started',started=2,body_returned=1))
        assert events[-1]=='tracker_optimizer_started'  # Durable sink precedes mocked body.
        run.optimizer_event(dict(kind='optimizer_body_returned',started=2,body_returned=2))
        kw['progress_callback']({'complete_epoch':False});kw['progress_callback']({'complete_epoch':True})
        return N(complete=True,valid_targets=2)
    data=N(iter_research_windows=lambda phase,encoding,**kw: iter(('TRAIN_ONLY_ENTRY',)))
    stats,receipt=runner._epoch(run,N(train_epoch=native_epoch,torch=N(device=lambda _:nullcontext())),data,adapter,object(),tracker,N(scope='select_train80'),object(),'TRAIN_INDEX',2)
    assert seen['index']=='TRAIN_INDEX' and seen['budget']['max_steps']==2 and seen['budget']['max_targets']==4
    assert (run.reserved_steps,run.returned_steps,run.completed_steps)==(2,2,2)
    assert (run.reserved_targets,run.returned_targets,run.completed_targets)==(4,4,4)
    assert events.count('step_committed')==1 and receipt=='MOCK_RECEIPT_NOT_EPOCH_ATTESTATION'


def test_raw_prediction_joins_labels_after_all_queries_and_keeps_oov(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch);calls=[]
    run=N(stage=prepare_main_selected_stage(c.spec.stage).begin_selected_fit(),config=c.spec.research.native_config,
        guard=lambda:None,boundary=lambda:None)
    phase=N(scope='raw_selection10',assert_integrity=lambda:None)
    encoding=N(assert_integrity=lambda:None)
    class Unknown:
        learner_id='learner';query=N(source_row=2);global_rank=2
    window=N(inputs=N(item_ids=(0,1),user_ids=('learner','learner'),source_rows=(0,1)),target_mask=(True,True),
        global_ranks=(0,1),window_id='manufactured',history_available=(0,1),history_used=(0,1),context_reset=(False,False))
    def predict(windows):
        calls.append('predict');assert all(not hasattr(w,'targets') for w in windows);return [(.5,.25)]
    adapter=N(set_context_index=lambda index:calls.append('selection_index'),audit_context_boundary=lambda:None,predict_windows=predict)
    def truth(p,e):
        assert calls.count('predict')==1;calls.append('truth_after_prediction')
        return [N(learner_id='learner',query=N(source_row=i,item_id='item'+str(i),timestamp=i),global_rank=i,
            history_sha256=H,history_hash_scheme='observable-prefix-chain-v1',origin_role='selection',phase_scope='raw_selection10',
            phase_sha256=H,encoding_sha256=H,trained_item=i<2,correct=i%2) for i in range(3)]
    data=N(ResearchUnseenTarget=Unknown,iter_research_windows=lambda *a,**k:iter((window,Unknown())),research_scoring_targets=truth)
    tools=N(np=N(flatnonzero=lambda mask:[i for i,v in enumerate(mask) if v],float32=lambda p:p),
        pd=N(DataFrame=lambda value:value),_metrics=lambda frame:{'manufactured_only':True})
    monkeypatch.setattr(runner.primitive,'_state_hash',lambda adapter:H)
    monkeypatch.setattr(runner.primitive,'_population',lambda *a:H)
    monkeypatch.setattr(runner.primitive,'_native_bce',lambda *a:1.)
    summary,rows,labels=runner._predict(run,tools,data,adapter,phase,encoding,'SELECTION_INDEX')
    assert (summary['full_targets'],summary['supported_targets'],summary['unsupported_targets'])==(3,2,1)
    assert [r['probability'] for r in rows]==[.5,.25,None] and rows[-1]['support_reason']=='oov_item'
    assert calls.index('predict')<calls.index('truth_after_prediction') and [r['correct'] for r in labels]==[0,1,0]
    with pytest.raises(ValueError,match='raw selection10'):
        runner._predict(run,tools,data,adapter,N(scope='calibration_predict'),encoding,'FORBIDDEN')


def test_checkpoint_delegation_and_prewrite_quota_no_fake_state(tmp_path):
    calls=[]
    run=N(output=tmp_path,output_bytes=0,spec=N(max_output_bytes=100),boundary=lambda:calls.append('boundary'))
    limits=N(max_checkpoint_bytes=20,max_metadata_bytes=10)
    adapter=N(index='TRAIN_INDEX')
    def save(directory,**kwargs):
        assert kwargs['adapter'].index=='TRAIN_INDEX' and kwargs['epoch_receipt']=='EXACT_RECEIPT'
        calls.append('existing_checkpoint_api')
        directory.mkdir(parents=True)  # Empty fixture directory only; no checkpoint/state certificate.
        return N(directory=directory)
    tools=N(cp=N(save_graph_epoch_state=save))
    runner._save(run,tools,adapter,object(),object(),'EXACT_RECEIPT',object(),{'id':'same'},1,limits)
    assert calls==['boundary','existing_checkpoint_api','boundary']
    run.output_bytes=90
    with pytest.raises(ValueError,match='quota'):
        runner._save(run,tools,adapter,object(),object(),'EXACT_RECEIPT',object(),{},2,limits)
    assert calls.count('existing_checkpoint_api')==1


def test_fresh_container_limit_and_counters_never_reset_on_reload():
    calls=[];before=random.getstate()
    run=N(config=N(seed=42,lr=1e-4,betas=(.9,.999),eps=1e-8,weight_decay=0.),constructors=0,optimizer_constructors=0,
        reserved_steps=7,returned_steps=7,completed_steps=7,boundary=lambda:None)
    tools=N(np=N(random=N(seed=lambda seed:calls.append('numpy_seed'))),
        torch=N(random=N(default_generator=N(manual_seed=lambda seed:calls.append('torch_seed'))),
            device=lambda device:nullcontext(),optim=N(Adam=lambda *a,**k:object())),
        graph_adapter=lambda **k:N(native=N(parameters=lambda:())))
    try:
        first,_=runner._construct(run,tools,object(),object(),object())
        second,_=runner._construct(run,tools,object(),object(),object())
        assert first is not second and (run.constructors,run.optimizer_constructors)==(2,2)
        assert (run.reserved_steps,run.returned_steps,run.completed_steps)==(7,7,7)
        with pytest.raises(ValueError):runner._construct(run,tools,object(),object(),object())
    finally:random.setstate(before)


def test_terminal_reasons_come_from_rows_not_assumed_oov_rescue():
    run=N()
    summary={'unsupported_targets':2}
    rows=[{'probability':None,'support_reason':'unseen_history'}]
    with pytest.raises(ValueError,match='coverage'):
        runner._claim(run,summary,rows,None,1,1,H,H,None,None,None)
