"""Collation callback: trainer thật, adapter giả; không constructor/optimizer."""
from types import SimpleNamespace

import pytest

from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.tensors import collate_windows
from knowledge_tracing.akt.training import train_epoch
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows


def fixture():
    learner=LearnerEvents('callback-engineering',1,tuple(
        KTEvent('callback-engineering','A',i+1,i+1,i%2,0,1) for i in range(3)))
    encoding=fit_vocabulary([learner])
    windows=tuple(iter_windows(learner,encoding,context=1,target_block=1,training=True))
    batches=[]
    def step(batch,optimizer):
        batches.append(batch)
        n=int((batch.loss_targets>=0).sum())
        return dict(stepped=True,valid_targets=n,loss_sum=.5*n)
    adapter=SimpleNamespace(native=SimpleNamespace(train=lambda:None),encoding=encoding,
        config=SimpleNamespace(seed=42,batch_size=2,device='cpu',max_grad_norm=1),step=step)
    return adapter,windows,batches


def test_callback_receives_original_entries_and_step_receives_same_batch_object():
    adapter,windows,batches=fixture();seen=[];made=[]
    def factory(entries):
        assert type(entries) is tuple
        assert all(any(e is w for w in windows) for e in entries)
        seen.extend(entries)
        batch=collate_windows([e.window for e in entries],n_items=1,device='cpu',targets=[e.targets for e in entries])
        made.append(batch)
        return batch
    result=train_epoch(adapter,lambda:iter(windows),optimizer=object(),epoch=1,budget={},batch_factory=factory)
    assert result.complete and result.valid_targets==3 and result.batches==2
    assert {id(e) for e in seen}=={id(e) for e in windows}
    assert len(made)==len(batches)==2 and all(a is b for a,b in zip(made,batches,strict=True))


def test_default_collation_keeps_original_population_without_callback():
    adapter,windows,batches=fixture()
    result=train_epoch(adapter,lambda:iter(windows),optimizer=object(),epoch=1,budget={})
    assert result.complete and result.valid_targets==3
    assert sum(int((b.loss_targets>=0).sum()) for b in batches)==3


@pytest.mark.parametrize('factory',[False,0,'callback'])
def test_noncallable_factory_rejected_before_native_training(factory):
    adapter,windows,batches=fixture()
    adapter.native.train=lambda:pytest.fail('native must not be entered')
    with pytest.raises(ValueError,match='callable'):
        train_epoch(adapter,lambda:iter(windows),optimizer=object(),epoch=1,budget={},batch_factory=factory)
    assert not batches


def test_recovery_and_custom_factory_rejected_before_state_load_or_forward():
    adapter,windows,batches=fixture()
    adapter.native.train=lambda:pytest.fail('native must not be entered')
    with pytest.raises(ValueError,match='no recovery contract'):
        train_epoch(adapter,lambda:iter(windows),optimizer=object(),epoch=1,budget={},recovery={},batch_factory=lambda _:None)
    assert not batches


def test_wrong_callback_result_rejected_before_step():
    adapter,windows,batches=fixture()
    with pytest.raises(ValueError,match='AKTBatch'):
        train_epoch(adapter,lambda:iter(windows),optimizer=object(),epoch=1,budget={},batch_factory=lambda _:None)
    assert not batches


def test_step_budget_stops_before_callback_for_unconsumed_batch():
    adapter,windows,batches=fixture()
    result=train_epoch(adapter,lambda:iter(windows),optimizer=object(),epoch=1,budget={'max_steps':0},
        batch_factory=lambda _:pytest.fail('no callback after step budget'))
    assert not result.complete and result.stop_reason=='step_budget' and not batches
