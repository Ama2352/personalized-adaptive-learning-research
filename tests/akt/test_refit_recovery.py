"""Khôi phục refit cùng vocabulary, epoch budget và actual AKT dropout."""

from dataclasses import replace

import pytest
import torch

from knowledge_tracing.akt import training
from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.types import KTEvent, LearnerEvents


def inputs(output):
    learners = [LearnerEvents(user, fold, tuple(KTEvent(user, exercise, i, i, i % 2, 0, fold)
                for i in range(1, 5))) for user, fold, exercise in [('a', 1, 'A'), ('b', 2, 'B')]]
    config = AKTConfig(output_dir=output, d_model=16, heads=2, d_ff=32, final_fc=16,
                       dropout=.2, max_epochs=3, batch_size=2)
    kwargs = dict(outer_train_users=('a', 'b'), train_learners_factory=lambda: iter(learners),
                  selected_epochs=3, identity={'run': 'synthetic'}, budget={'max_steps': 10}, save_recovery=True)
    return config, kwargs


def test_refit_recovery_matches_uninterrupted_weights_adam_rng(tmp_path, monkeypatch):
    config, kwargs = inputs(tmp_path / 'continuous')
    expected = training.refit_outer_train(config, **kwargs)
    config = replace(config, output_dir=tmp_path / 'interrupted')
    original_save = training.save_checkpoint

    def interrupt(path, *args, **save_kwargs):
        original_save(path, *args, **save_kwargs)
        if path.name == 'refit-recovery-epoch-1.pt':
            raise InterruptedError('synthetic interruption')

    monkeypatch.setattr(training, 'save_checkpoint', interrupt)
    with pytest.raises(InterruptedError):
        training.refit_outer_train(config, **kwargs)
    monkeypatch.setattr(training, 'save_checkpoint', original_save)
    actual = training.refit_outer_train(config, **kwargs,
        resume_checkpoint=config.output_dir / 'refit-recovery-epoch-1.pt')
    assert actual.completed_epochs == 3
    assert actual.encoding == expected.encoding
    assert [r['loss_sum'] for r in actual.training_history] == [r['loss_sum'] for r in expected.training_history]
    assert all(torch.equal(p, q) for p, q in zip(actual.native.parameters(), expected.native.parameters()))
    before = torch.load(tmp_path / 'continuous/refit-recovery-epoch-3.pt', weights_only=True)
    after = torch.load(config.output_dir / 'refit-recovery-epoch-3.pt', weights_only=True)
    assert torch.equal(before['torch_rng'], after['torch_rng'])
    for key, state in before['optimizer_state_dict']['state'].items():
        for field, value in state.items():
            torch.testing.assert_close(value, after['optimizer_state_dict']['state'][key][field], rtol=0, atol=0)
    again = training.refit_outer_train(config, **kwargs,
        resume_checkpoint=config.output_dir / 'refit-recovery-epoch-3.pt')
    assert len(again.training_history) == 3


def test_refit_recovery_rejects_changed_epoch_budget(tmp_path):
    config, kwargs = inputs(tmp_path)
    training.refit_outer_train(config, **kwargs)
    with pytest.raises(ValueError, match='identity'):
        training.refit_outer_train(config, **{**kwargs, 'selected_epochs': 2},
            resume_checkpoint=tmp_path / 'refit-recovery-epoch-1.pt')
