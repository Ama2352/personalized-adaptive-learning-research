from dataclasses import replace

import pytest
import torch

import knowledge_tracing.akt.resumable as module
from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.model import AKTAdapter
from knowledge_tracing.akt.resumable import train_resumable_epoch
from knowledge_tracing.akt.training import train_epoch
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows


def setup():
    learner = LearnerEvents('u', 1, tuple(KTEvent('u','A',i+1,i+1,i%2,0,1) for i in range(17)))
    encoding = fit_vocabulary([learner])
    config = replace(AKTConfig(), d_model=32, heads=4, d_ff=64, final_fc=32,
                     batch_size=2, context=2, target_block=2)
    torch.manual_seed(42)
    adapter = AKTAdapter(config, encoding)
    optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr)
    factory = lambda: iter_windows(learner, encoding, context=2, target_block=2, training=True)
    return adapter, optimizer, factory


def test_full_and_interrupted_resume_match_original_training(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'PROJECT_ROOT', tmp_path)
    original, opt, factory = setup()
    expected = train_epoch(original, factory, optimizer=opt, epoch=1, budget={})
    model, optimizer, factory = setup()
    args = dict(epoch=1, stream_identity='synthetic-vocab-A-H2-T2', identity={'run':'fixture'},
                checkpoint_dir=tmp_path/'experiments/akt/results/run', max_steps=20, max_seconds=60)
    checkpoints = []
    def interrupt(path, state):
        checkpoints.append(path)
        if state['optimizer_steps'] == 2:
            raise InterruptedError('synthetic interruption')
    with pytest.raises(InterruptedError):
        train_resumable_epoch(model, optimizer, factory, **args, checkpoint_callback=interrupt)
    clone, clone_optimizer, factory = setup()
    actual = train_resumable_epoch(clone, clone_optimizer, factory, **args,
                                    resume_checkpoint=checkpoints[-1])
    assert actual['complete']
    assert actual['valid_targets'] == expected.valid_targets == 17
    assert actual['optimizer_steps'] == expected.optimizer_steps == 5
    assert actual['loss_sum'] == expected.loss_sum
    assert actual['sampler_state']['consumed_windows'] == 9
    assert all(torch.equal(p, q) for p, q in zip(original.native.parameters(), clone.native.parameters()))


def test_resume_caps_do_not_reset_and_stream_change_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'PROJECT_ROOT', tmp_path)
    model, optimizer, factory = setup()
    args = dict(epoch=1, stream_identity='fixed', identity={},
                checkpoint_dir=tmp_path/'experiments/akt/results/run', max_steps=1, max_seconds=60)
    result = train_resumable_epoch(model, optimizer, factory, **args)
    assert not result['complete']
    path = args['checkpoint_dir']/'recovery-epoch-1-step-1.pt'
    clone, opt, factory = setup()
    result = train_resumable_epoch(clone, opt, factory, **args, resume_checkpoint=path)
    assert result['optimizer_steps'] == 1 and result['stop_reason'] == 'step_budget'
    with pytest.raises(ValueError, match='identity'):
        train_resumable_epoch(clone, opt, factory, **{**args,'stream_identity':'changed'}, resume_checkpoint=path)


def test_target_cap_preserves_only_committed_prefix_and_is_cumulative(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'PROJECT_ROOT', tmp_path)
    model, optimizer, factory = setup()
    args = dict(epoch=1, stream_identity='fixed', identity={},
                checkpoint_dir=tmp_path/'experiments/akt/results/run', max_steps=20, max_seconds=60,
                max_targets=6, checkpoint_every_steps=10)
    result = train_resumable_epoch(model, optimizer, factory, **args)
    assert result['stop_reason'] == 'target_budget'
    assert result['valid_targets'] <= 6
    path = args['checkpoint_dir'] / f"recovery-epoch-1-step-{result['optimizer_steps']}.pt"
    payload = torch.load(path, weights_only=True)
    assert result['sampler_state'] == payload['resume_state']['sampler_state']
    clone, opt, factory = setup()
    capped = train_resumable_epoch(clone, opt, factory, **args, resume_checkpoint=path)
    assert capped['optimizer_steps'] == result['optimizer_steps']
    assert capped['valid_targets'] == result['valid_targets']
    resumed = train_resumable_epoch(clone, opt, factory, **{**args, 'max_targets': 30}, resume_checkpoint=path)
    original, original_opt, factory = setup()
    expected = train_epoch(original, factory, optimizer=original_opt, epoch=1, budget={})
    assert resumed['complete'] and resumed['loss_sum'] == expected.loss_sum
    assert all(torch.equal(p, q) for p, q in zip(original.native.parameters(), clone.native.parameters()))


def test_checkpoint_cadence_flushes_last_step_on_bounded_stop(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'PROJECT_ROOT', tmp_path)
    model, optimizer, factory = setup()
    checkpoints = []
    result = train_resumable_epoch(
        model, optimizer, factory, epoch=1, stream_identity='fixed', identity={},
        checkpoint_dir=tmp_path/'experiments/akt/results/run', max_steps=3, max_seconds=60,
        checkpoint_every_steps=2, checkpoint_callback=lambda path, state: checkpoints.append(state['optimizer_steps']))
    assert result['stop_reason'] == 'step_budget'
    assert checkpoints == [2, 3]


def test_epoch_finishes_when_step_cap_equals_exact_required_updates(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'PROJECT_ROOT', tmp_path)
    model, optimizer, factory = setup()
    args = dict(epoch=1, stream_identity='fixed', identity={},
                checkpoint_dir=tmp_path/'experiments/akt/results/run',max_steps=5,max_seconds=60)
    result = train_resumable_epoch(model, optimizer, factory, **args)
    assert result['complete'] and result['stop_reason'] == 'epoch_complete'
    assert result['optimizer_steps'] == 5 and result['valid_targets'] == 17
    clone, opt, factory = setup()
    resumed = train_resumable_epoch(clone,opt,factory,**args,
                                   resume_checkpoint=args['checkpoint_dir']/'recovery-epoch-1-step-5.pt')
    assert resumed['complete'] and resumed['optimizer_steps'] == 5
    assert all(torch.equal(p,q) for p,q in zip(model.native.parameters(),clone.native.parameters()))
