"""Actual AKT, bounded synthetic training và frozen online/offline parity."""

from copy import deepcopy
from dataclasses import replace

import numpy as np
import pytest
import torch

from knowledge_tracing.akt.checkpoint import save_checkpoint, save_recovery_checkpoint
from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.encoding import fit_vocabulary,encode_exercises
from knowledge_tracing.akt.model import AKTAdapter
from knowledge_tracing.akt.online import load_online_akt, simulator_model_identity
from knowledge_tracing.akt.provenance import sha256_file
from knowledge_tracing.akt.training import train_epoch
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.shared_kt import build_causal_sequence_inputs
from knowledge_tracing.simulator_bridge import (SimulatorBank,SimulatorItem,ItemQuery,OnlineSession,
                                               ReferenceSet,probe_references)


def fitted_fixture(tmp_path, *, context=3,target_block=2):
    bank=SimulatorBank('grade10-synthetic-fixture',tuple(SimulatorItem(item,'C',1000+i*100)
                                                       for i,item in enumerate(['A','B','C','R'])))
    learner=LearnerEvents('train',1,tuple(KTEvent('train',item,i,i+1,i%2,0,1)
                                        for i,item in enumerate(['A','B','C','A','B','C','A','B'])))
    encoding=fit_vocabulary([learner])
    config=AKTConfig(d_model=16,heads=2,d_ff=32,final_fc=16,dropout=.2,
                     context=context,target_block=target_block,batch_size=2)
    torch.manual_seed(42)
    model=AKTAdapter(config,encoding)
    optimizer=torch.optim.Adam(model.native.parameters(),lr=config.lr)
    stats=train_epoch(model,lambda:iter_windows(learner,encoding,context=context,target_block=target_block,training=True),
                       optimizer=optimizer,epoch=1,budget={'max_steps':2,'max_seconds':30})
    assert stats.complete and stats.valid_targets==8 and stats.optimizer_steps<=2
    identity={**simulator_model_identity(config,bank,encoding),
              'artifact_role':'synthetic_engineering_fixture','training_targets':8}
    checkpoint=tmp_path/'fixture.pt'
    save_checkpoint(checkpoint,model,optimizer,identity=identity,progress={'epoch':1,'complete':True})
    return bank,config,model,optimizer,checkpoint,identity


def load(fixture):
    bank,config,model,optimizer,path,identity=fixture
    return load_online_akt(path,config,bank,expected_sha256=sha256_file(path),expected_identity=identity)


@pytest.mark.parametrize('sequence',[
    ['A','B','C','A','B','C','A','B','C','A','B'],
    ['R','A','B','R','C','A','B','R','C','A','B'],
])
def test_online_matches_offline_with_global_blocks_oov_partial_and_future_invariance(tmp_path,sequence):
    fixture=fitted_fixture(tmp_path)
    bank,config,model,optimizer,path,identity=fixture
    backend=load(fixture)
    session=OnlineSession(backend,bank,learner_id='eval',max_events=len(sequence))
    rows=[dict(user_id='eval',exercise=item,time_done=i//2,source_row=i+1,correct=i%2)
          for i,item in enumerate(sequence)]
    inputs,_=build_causal_sequence_inputs(rows,item_key='exercise')
    inputs=replace(inputs,item_ids=encode_exercises(sequence,model.encoding))
    expected=model.predict(inputs)
    from knowledge_tracing.akt.prediction import iter_predictions
    model.checkpoint_id=sha256_file(path)
    exported=list(iter_predictions(model,[LearnerEvents('eval',2,tuple(KTEvent('eval',row['exercise'],
        row['time_done'],row['source_row'],row['correct'],0,2) for row in rows))]))
    before={name:p.detach().clone() for name,p in backend._adapter.native.named_parameters()}
    rng=torch.get_rng_state().clone()
    for index,row in enumerate(rows):
        query=ItemQuery(row['exercise'],row['time_done'],row['source_row'])
        ticket=session.predict(query)
        if np.isnan(expected[index]):
            assert ticket.score.probability is None and ticket.score.prediction_kind=='unseen_item'
        else:
            assert ticket.score.probability == pytest.approx(float(expected[index]),abs=1e-6,rel=0)
        # Hai outcome hiện tại đều không đổi ticket/probe trước update.
        assert session.probe(query)==ticket.score
        assert ticket.score.history_available == exported[index].history_available
        assert ticket.score.history_used == exported[index].history_used
        assert ticket.score.context_reset == exported[index].context_reset
        session.observe(ticket,row['correct'])
    assert torch.equal(rng,torch.get_rng_state())
    assert all(torch.equal(value,dict(backend._adapter.native.named_parameters())[name]) for name,value in before.items())
    assert backend._adapter.native.training


def test_loader_preserves_rng_and_rejects_domain_recipe_vocab_hash_and_nonselected_snapshot(tmp_path):
    fixture=fitted_fixture(tmp_path)
    bank,config,model,optimizer,path,identity=fixture
    rng=torch.get_rng_state().clone()
    backend=load(fixture)
    assert torch.equal(rng,torch.get_rng_state())
    with pytest.raises(ValueError,match='domain'):
        load_online_akt(path,config,replace(bank,environment_id='Junyi'),
                        expected_sha256=sha256_file(path),expected_identity=identity)
    with pytest.raises(ValueError,match='recipe'):
        load_online_akt(path,replace(config,context=2),bank,
                        expected_sha256=sha256_file(path),expected_identity=identity)
    with pytest.raises(ValueError,match='SHA-256'):
        load_online_akt(path,config,bank,expected_sha256='0'*64,expected_identity=identity)
    changed={**identity,'vocabulary_sha256':'other'}
    with pytest.raises(ValueError,match='identity'):
        load_online_akt(path,config,bank,expected_sha256=sha256_file(path),expected_identity=changed)
    recovery=tmp_path/'complete-recovery.pt'
    save_checkpoint(recovery,model,optimizer,identity=identity,
                    progress={'epoch':1,'complete':True,'role':'selection_recovery_v1'})
    with pytest.raises(ValueError,match='not a selected'):
        load_online_akt(recovery,config,bank,expected_sha256=sha256_file(recovery),expected_identity=identity)


def test_reference_probes_snapshot_reset_and_learner_isolation_with_frozen_native_akt(tmp_path):
    fixture=fitted_fixture(tmp_path)
    backend=load(fixture);bank=fixture[0]
    a=OnlineSession(backend,bank,learner_id='a',max_events=10)
    b=OnlineSession(backend,bank,learner_id='b',max_events=10)
    initial=b.probe(ItemQuery('B',1,2))
    a.observe(a.predict(ItemQuery('A',0,1)),1)
    assert b.probe(ItemQuery('B',1,2))==initial
    snapshot=deepcopy(a.snapshot())
    refs=(ReferenceSet('C',(('A',.5),('B',.5))),)
    result=probe_references(a,refs,timestamp=1,source_row=2)
    assert result['scores']['C']['supported_items']==2
    assert a.snapshot()==snapshot
    clone=OnlineSession(backend,bank,learner_id='a',max_events=10)
    clone.restore(snapshot)
    assert clone.probe(ItemQuery('C',1,2))==a.probe(ItemQuery('C',1,2))
    pending=a.predict(ItemQuery('B',1,2))
    a.reset()
    assert a.probe(ItemQuery('B',1,2))==initial
    with pytest.raises(ValueError,match='stale'):
        a.observe(pending,0)
    result=probe_references(a,(ReferenceSet('C',(('A',.5),('R',.5))),),timestamp=1,source_row=2)
    assert result['scores']['C']['score'] is None
    with torch.no_grad():
        next(backend._adapter.native.parameters()).add_(.01)
    with pytest.raises(ValueError,match='frozen'):
        a.probe(ItemQuery('A',1,2))


def test_checkpoint_without_simulator_identity_cannot_be_silently_assigned_to_simulator(tmp_path):
    fixture=fitted_fixture(tmp_path)
    bank,config,model,optimizer,path,identity=fixture
    legacy=tmp_path/'junyi-like.pt'
    legacy_identity={'protocol':'akt-nr-exercise-v1','canonical_manifest_sha256':'Junyi-fixture'}
    save_checkpoint(legacy,model,optimizer,identity=legacy_identity,progress={'epoch':1,'complete':True})
    with pytest.raises(ValueError,match='domain'):
        load_online_akt(legacy,config,bank,expected_sha256=sha256_file(legacy),expected_identity=legacy_identity)


def test_export_does_not_reanchor_prebuilt_windows_when_context_is_not_multiple_of_block(tmp_path):
    from knowledge_tracing.akt.prediction import iter_predictions
    fixture=fitted_fixture(tmp_path)
    bank,config,model,optimizer,path,identity=fixture
    model.checkpoint_id=sha256_file(path)
    sequence=['A','B','C','A','B','C','A','B','C','A','B']
    events=tuple(KTEvent('eval',item,i//2,i+1,i%2,0,2) for i,item in enumerate(sequence))
    rows=[dict(user_id='eval',exercise=e.exercise,time_done=e.time_done,source_row=e.source_row,correct=e.correct)
          for e in events]
    inputs,_=build_causal_sequence_inputs(rows,item_key='exercise',item_vocabulary=model.encoding.vocabulary)
    expected=model.predict(inputs)
    actual=np.asarray([record.prediction for record in iter_predictions(model,[LearnerEvents('eval',2,events)])])
    np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-6)


def test_default_100_100_geometry_keeps_legacy_window_predictions_and_online_boundary_parity(tmp_path):
    from knowledge_tracing.akt.types import WindowInputs
    from knowledge_tracing.akt.prediction import iter_predictions
    from knowledge_tracing.simulator_bridge import Observation
    fixture=fitted_fixture(tmp_path,context=100,target_block=100)
    bank,config,model,optimizer,path,identity=fixture
    events=tuple(KTEvent('eval','R' if i==37 else ['A','B','C'][i%3],i//2,i+1,i%2,0,2)
                 for i in range(205))
    learner=LearnerEvents('eval',2,events)
    for window in iter_windows(learner,model.encoding,context=100,target_block=100,training=False):
        if isinstance(window,WindowInputs):
            legacy=model.predict(window.inputs)
            direct=model.predict_window(window)
            np.testing.assert_allclose(legacy[window.target_mask],direct[window.target_mask],atol=1e-6,rtol=0)
    model.checkpoint_id=sha256_file(path)
    exported=list(iter_predictions(model,[learner]))
    backend=load(fixture)
    for rank in (0,38,99,100,137,199,200,204):
        history=tuple(Observation(ItemQuery(event.exercise,event.time_done,event.source_row),event.correct)
                      for event in events[:rank])
        event=events[rank]
        score=backend.predict_next(history,ItemQuery(event.exercise,event.time_done,event.source_row),learner_id='eval')
        assert score.probability == pytest.approx(exported[rank].prediction,abs=1e-6,rel=0)
        assert score.history_used == exported[rank].history_used


def test_original_akt_has_no_elapsed_time_feature_despite_timestamped_api(tmp_path):
    fixture=fitted_fixture(tmp_path)
    backend=load(fixture)
    session=OnlineSession(backend,fixture[0],learner_id='eval',max_events=10)
    session.observe(session.predict(ItemQuery('A',0,1)),1)
    immediate=session.probe(ItemQuery('B',1,2))
    delayed=session.probe(ItemQuery('B',14*86400,2))
    assert immediate == delayed
    # Đây là giới hạn architecture nguồn; không gọi delayed p là retained latent mastery.


def test_batched_counterfactual_queries_match_sequential_without_cross_candidate_history(tmp_path):
    fixture=fitted_fixture(tmp_path)
    backend=load(fixture)
    session=OnlineSession(backend,fixture[0],learner_id='eval',max_events=10)
    for i,item in enumerate(['R','A','B']):
        session.observe(session.predict(ItemQuery(item,i,i+1)),i%2)
    before=session.snapshot()
    queries=tuple(ItemQuery(item,3,4) for item in ['A','R','B','C','A'])
    shapes=[]
    hook=backend._adapter.native.register_forward_hook(lambda module,args,result: shapes.append(tuple(args[0].shape)))
    try:
        sequential=tuple(session.probe(query) for query in queries)
        sequential_calls=len(shapes);shapes.clear()
        batched=session.probe_many(queries)
        batch_calls=len(shapes)
        assert sequential_calls==4 and batch_calls==2
        assert max(shape[0] for shape in shapes)<=fixture[1].batch_size==2
        for expected,actual in zip(sequential,batched):
            assert replace(actual,probability=expected.probability)==expected
            if expected.probability is not None:
                assert actual.probability==pytest.approx(expected.probability,abs=1e-6,rel=0)
        reversed_scores=session.probe_many(tuple(reversed(queries)))
        for first,second in zip(batched,reversed(reversed_scores)):
            assert first.prediction_kind==second.prediction_kind
            if first.probability is not None:
                assert first.probability==pytest.approx(second.probability,abs=1e-6,rel=0)
        assert session.snapshot()==before
    finally:
        hook.remove()


def test_native_batched_windows_keep_padding_and_per_window_shapes_separate(tmp_path):
    fixture=fitted_fixture(tmp_path)
    model=fixture[2]
    windows=[]
    for n in (1,5,8):
        learner=LearnerEvents('eval',2,tuple(KTEvent('eval',['A','B','C'][i%3],i,i+1,i%2,0,2)
                                             for i in range(n)))
        windows.append(list(iter_windows(learner,model.encoding,context=3,target_block=2,training=False))[-1])
    expected=[model.predict_window(window) for window in windows]
    actual=model.predict_windows(windows)
    assert [len(values) for values in actual]==[len(window.inputs.item_ids) for window in windows]
    for left,right in zip(expected,actual):
        np.testing.assert_allclose(left,right,atol=1e-6,rtol=0)
