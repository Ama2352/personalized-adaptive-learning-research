"""Khôi phục selection sau validation, kiểm bằng actual AKT CPU và dropout."""

from dataclasses import replace

import pytest
import torch

from knowledge_tracing.akt import training
from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.splits import InnerSplit
from knowledge_tracing.akt.types import KTEvent, LearnerEvents


def selection_inputs(output):
    train = LearnerEvents('train', 1, tuple(
        KTEvent('train', 'A', index, index, index % 2, 0, 1) for index in range(4)))
    val = LearnerEvents('val', 2, tuple(
        KTEvent('val', 'A', index, index + 10, index % 2, 0, 2) for index in range(4)))
    config = AKTConfig(output_dir=output, d_model=16, heads=2, d_ff=32,
                       final_fc=16, dropout=0.2, max_epochs=5, patience=2,
                       min_delta=1.0, batch_size=2)
    kwargs = dict(inner_split=InnerSplit(('train',), ('val',), 0, 'synthetic-split'),
                  train_learners_factory=lambda: iter([train]),
                  val_learners_factory=lambda: iter([val]), identity={'run': 'synthetic'},
                  budget={'max_steps': 10}, save_recovery=True)
    return config, kwargs


def test_epoch_recovery_preserves_weights_losses_and_stale_epochs(tmp_path, monkeypatch):
    config, kwargs = selection_inputs(tmp_path / 'continuous')
    expected = training.select_checkpoint(config, **kwargs)
    config = replace(config, output_dir=tmp_path / 'interrupted')
    original_save = training.save_checkpoint

    def interrupt_after_snapshot(path, *args, **save_kwargs):
        original_save(path, *args, **save_kwargs)
        if path.name == 'inner-recovery-epoch-2.pt':
            raise InterruptedError('synthetic interruption after validation')

    monkeypatch.setattr(training, 'save_checkpoint', interrupt_after_snapshot)
    with pytest.raises(InterruptedError):
        training.select_checkpoint(config, **kwargs)
    monkeypatch.setattr(training, 'save_checkpoint', original_save)
    actual = training.select_checkpoint(
        config, **kwargs, resume_checkpoint=config.output_dir / 'inner-recovery-epoch-2.pt')
    assert expected.selected_epoch == actual.selected_epoch == 1
    assert len(expected.history) == len(actual.history) == 3
    assert [row['validation_loss'] for row in expected.history] == [row['validation_loss'] for row in actual.history]
    for directory in (tmp_path / 'continuous', config.output_dir):
        assert not (directory / 'inner-recovery-epoch-4.pt').exists()
    before = torch.load(tmp_path / 'continuous/inner-recovery-epoch-3.pt', weights_only=True)
    after = torch.load(config.output_dir / 'inner-recovery-epoch-3.pt', weights_only=True)
    for key, value in before['model_state_dict'].items():
        assert torch.equal(value, after['model_state_dict'][key])
    for key, state in before['optimizer_state_dict']['state'].items():
        for field, value in state.items():
            torch.testing.assert_close(value, after['optimizer_state_dict']['state'][key][field], rtol=0, atol=0)
    assert torch.equal(before['torch_rng'], after['torch_rng'])
    # Resume một selection đã dừng không thực hiện thêm optimizer step.
    again = training.select_checkpoint(
        config, **kwargs, resume_checkpoint=config.output_dir / 'inner-recovery-epoch-3.pt')
    assert again.selected_epoch == 1 and len(again.history) == 3


def test_recovery_rejects_config_drift_and_changed_best_checkpoint(tmp_path):
    config, kwargs = selection_inputs(tmp_path)
    result = training.select_checkpoint(config, **kwargs)
    recovery = tmp_path / 'inner-recovery-epoch-2.pt'
    with pytest.raises(ValueError, match='identity'):
        training.select_checkpoint(replace(config, lr=config.lr * 2), **kwargs, resume_checkpoint=recovery)
    result.checkpoint.write_bytes(b'corrupted synthetic checkpoint')
    with pytest.raises(ValueError, match='best checkpoint mismatch'):
        training.select_checkpoint(config, **kwargs, resume_checkpoint=recovery)


def test_default_selection_keeps_existing_artifact_contract(tmp_path):
    config, kwargs = selection_inputs(tmp_path)
    kwargs['save_recovery'] = False
    result = training.select_checkpoint(config, **kwargs)
    assert result.checkpoint.name == 'inner-best-epoch-1.pt'
    assert not list(tmp_path.glob('inner-recovery-*.pt'))
