"""Đối chiếu compact A1 qua adapter, training step, mutation và resume thật CPU."""
from dataclasses import replace

import numpy as np
import pytest
import torch

from test_junyi_graph_model import (setup,adam,windows,_assert_tree_equal,
    test_native_graph_checkpoint_resume_matches_continuous as base_resume)
from knowledge_tracing.akt.research_junyi_compact import build_compact_context
from knowledge_tracing.akt.research_junyi_graph import JunyiGraphPhaseSession
from knowledge_tracing.akt.windows import iter_windows


@pytest.mark.parametrize('variant',['A2','A3'])
def test_weighted_compact_messages_and_gate_features_use_only_native_prefix(setup,variant):
    from knowledge_tracing.akt.research_junyi_confidence_binding import JunyiConfidenceBinding
    from knowledge_tracing.akt.research_graph_condition import OperationalEdgeWeight
    from knowledge_tracing.akt.research_junyi_compact import build_compact_confidence_context
    original=setup['condition']((('A','C'),('B','C')))
    binding=JunyiConfidenceBinding(setup['train'].identity,setup['encoding'].identity,'a'*64,'b'*64,'c'*64,
        (OperationalEdgeWeight('A','C',True,.25,None,.25),OperationalEdgeWeight('B','C',True,.75,None,.75)))
    condition=replace(original,variant=variant,confidence=binding)
    phase=JunyiGraphPhaseSession(condition,setup['train'])
    entries=windows(setup,setup['train'],items=('A','B','C','A','C'),labels=(1,0,1,0,1),training=True)
    context=build_compact_confidence_context(tuple(row.window for row in entries),phase)
    message,active,_,_,features=context.arrays()
    assert message[0,2]==-.25 and active[0,2]
    np.testing.assert_array_equal(features[0,2],np.asarray((2/3,.5,.0625,1.),dtype=np.float32))
    changed=windows(setup,setup['train'],items=('A','B','C','A','C'),labels=(1,0,1,1,0),training=True)
    alternate=build_compact_confidence_context(tuple(row.window for row in changed),phase)
    assert np.array_equal(message[:,:4],alternate.arrays()[0][:,:4])
    assert np.array_equal(features[:,:4],alternate.arrays()[4][:,:4])
    with pytest.raises(ValueError,match='geometry'):
        replace(context,features=b'').arrays()


@pytest.mark.parametrize('variant',['A2','A3'])
@pytest.mark.parametrize('enabled',[True,False])
def test_weighted_compact_checkpoint_resume_exact(setup,tmp_path,variant,enabled):
    factory=setup['adapter']
    patched=dict(setup,adapter=lambda **kwargs:factory(variant=variant,compact=True,**kwargs))
    base_resume(patched,tmp_path,enabled)


def case(setup,mode):
    edges=(('B','C'),) if mode=='unsupported' else (('A','C'),)
    old=setup['adapter'](edges=edges,enabled=mode!='off')
    new=setup['adapter'](edges=edges,enabled=mode!='off',compact=True)
    learners=[setup['student'](setup['train'].users[0],labels=(1,0,0,1,1,0)),
              setup['student'](setup['train'].users[1],items=('A','C','A'),labels=(0,1,1))]
    entries=tuple(entry for learner in learners for entry in iter_windows(learner,new.encoding,training=True))
    return old,new,entries


@pytest.mark.parametrize('alpha',[0.,.75])
@pytest.mark.parametrize('mode',['on','off','unsupported'])
def test_two_adapter_steps_match_reference(setup,alpha,mode):
    old,new,entries=case(setup,mode)
    with torch.no_grad():
        old.native.alpha.fill_(alpha)
    new.native.load_state_dict(old.native.state_dict(),strict=True)
    optimizers=[adam(adapter) for adapter in (old,new)]
    for _ in range(2):
        rng=torch.get_rng_state().clone()
        results=[]
        rng_after=[]
        for adapter,optimizer in zip((old,new),optimizers):
            torch.set_rng_state(rng)
            results.append(adapter.step(adapter.collate_training(entries),optimizer))
            rng_after.append(torch.get_rng_state().clone())
        assert results[0]['loss_sum']==results[1]['loss_sum']
        assert results[0]['valid_targets']==results[1]['valid_targets']
        assert torch.equal(*rng_after)
        _assert_tree_equal(old.native.state_dict(),new.native.state_dict())
        _assert_tree_equal(optimizers[0].state_dict(),optimizers[1].state_dict())
        for first,second in zip(old.native.parameters(),new.native.parameters()):
            assert (first.grad is None)==(second.grad is None)
            if first.grad is not None:
                assert torch.equal(first.grad,second.grad)
    phase=JunyiGraphPhaseSession(new.condition,setup['selection'])
    old.set_phase(JunyiGraphPhaseSession(old.condition,setup['selection']))
    new.set_phase(phase)
    samples=windows(setup,setup['selection'])
    for first,second in zip(old.predict_windows(samples),new.predict_windows(samples)):
        assert np.array_equal(first,second)


def test_compact_context_detects_batch_and_payload_changes(setup):
    _,adapter,entries=case(setup,'on')
    batch=adapter.collate_training(entries)
    context=adapter._ticket.evidence
    context.assert_for(batch,adapter.condition.identity)
    with pytest.raises(ValueError,match='condition'):
        context.assert_for(batch,'0'*64)
    with pytest.raises(ValueError,match='size'):
        replace(context,messages=b'').assert_for(batch,adapter.condition.identity)
    changed=replace(context,source_rows=b'\x00'*len(context.source_rows))
    with pytest.raises(ValueError,match='source rows'):
        changed.assert_for(batch,adapter.condition.identity)
    adapter.native.bind(batch,context,enabled=True)
    object.__setattr__(context,'messages',b'\x00'*len(context.messages))
    with pytest.raises(ValueError,match='evidence drift'):
        adapter.native(batch.q_data,batch.qa_data,batch.loss_targets)


def test_compact_keeps_future_boundary_and_encoding_checks(setup):
    adapter=setup['adapter'](compact=True)
    sample=windows(setup,setup['train'])[0]
    prior=sample.inputs.prior_responses.copy()
    prior[4:]=1-prior[4:]
    changed=replace(sample,inputs=replace(sample.inputs,prior_responses=prior))
    before=build_compact_context((sample,),adapter.phase).arrays()
    after=build_compact_context((changed,),adapter.phase).arrays()
    assert np.array_equal(before[0][0,:4],after[0][0,:4])
    adapter.encoding.train_support_students['A']=999
    with pytest.raises(ValueError,match='encoding content'):
        build_compact_context((sample,),adapter.phase)


def test_mid_batch_encoding_change_is_detected(setup,monkeypatch):
    from knowledge_tracing.akt import research_junyi_compact as compact
    adapter=setup['adapter'](compact=True)
    sample=windows(setup,setup['train'])[0]
    original=compact._validate_window
    def changed(window,phase):
        original(window,phase)
        adapter.encoding.train_support_students['A']=999
    monkeypatch.setattr(compact,'_validate_window',changed)
    with pytest.raises(ValueError,match='encoding content'):
        build_compact_context((sample,),adapter.phase)


def test_zero_message_keeps_active_target(setup):
    adapter=setup['adapter'](compact=True)
    sample=windows(setup,setup['train'],items=('A','A','C'),labels=(1,0,1))[0]
    messages,active,_,_=build_compact_context((sample,),adapter.phase).arrays()
    assert active[0,2] and messages[0,2]==0.


def test_context_backend_mutation_is_rejected(setup):
    adapter=setup['adapter'](compact=True)
    adapter._compact_context=False
    with pytest.raises(ValueError,match='context backend changed'):
        adapter.audit_context_boundary()


def test_selected_factory_enables_compact_a1(setup,monkeypatch):
    from knowledge_tracing.akt import research_junyi_graph_model as model
    from knowledge_tracing.akt.research_junyi_selection import _make_selected_adapter
    monkeypatch.setattr(model,'JunyiGraphAKTAdapter',lambda **kwargs:kwargs)
    condition=setup['condition']()
    kwargs=_make_selected_adapter(setup['config'],None,setup['encoding'],setup['train'],condition)
    assert kwargs['compact_context'] is True
    assert kwargs['phase'].condition is condition


@pytest.mark.parametrize('enabled',[True,False])
def test_compact_checkpoint_resume_matches_continuous(setup,tmp_path,enabled):
    original=setup['adapter']
    def compact_adapter(**kwargs):
        return original(compact=True,**kwargs)
    bound=dict(setup,adapter=compact_adapter)
    base_resume(bound,tmp_path,enabled)
