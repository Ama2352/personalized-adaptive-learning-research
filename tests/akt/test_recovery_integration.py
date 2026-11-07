"""Selection/refit fork và batch accounting trên actual AKT CPU, có dropout."""

from dataclasses import replace

import pytest
import torch

from knowledge_tracing.akt import training
from knowledge_tracing.akt.config import AKTConfig, RecoveryOptions
from knowledge_tracing.akt.splits import InnerSplit
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.recovery import digest_file


def inputs(output):
    train = LearnerEvents('train', 1, tuple(KTEvent('train', 'A', i, i, i % 2, 0, 1) for i in range(17)))
    val = LearnerEvents('val', 2, tuple(KTEvent('val', 'A' if i != 3 else 'OOV', i, i+100,
                                            i % 2, 0, 2) for i in range(9)))
    config = AKTConfig(output_dir=output, run_id=output.name, d_model=16, heads=2, d_ff=32,
        final_fc=16, dropout=.2, max_epochs=5, patience=2, min_delta=1.0,
        batch_size=2, context=2, target_block=2, recovery=RecoveryOptions(2))
    kwargs = dict(inner_split=InnerSplit(('train',), ('val',), 0, 'fixture-split'),
        train_learners_factory=lambda: iter([train]), val_learners_factory=lambda: iter([val]),
        identity={'data': 'fixture'}, budget={'max_steps': 5, 'max_seconds': 60}, save_recovery=True)
    return config, kwargs


def assert_payload_equal(expected, actual):
    for key, value in expected['model_state_dict'].items():
        assert torch.equal(value, actual['model_state_dict'][key]), key
    for key, fields in expected['optimizer_state_dict']['state'].items():
        for name, value in fields.items():
            assert torch.equal(value, actual['optimizer_state_dict']['state'][key][name])
    assert torch.equal(expected['torch_rng'], actual['torch_rng'])
    assert expected['python_rng'] == actual['python_rng']
    assert expected['numpy_rng'] == actual['numpy_rng']


@pytest.mark.parametrize('boundary', ['batch', 'before-validation', 'orphan-best', 'epoch', 'export'])
def test_fresh_attempt_matches_continuous_and_keeps_source_immutable(tmp_path, monkeypatch, boundary):
    config, kwargs = inputs(tmp_path / 'continuous')
    expected = training.select_checkpoint(config, **kwargs)
    interrupted = replace(config, output_dir=tmp_path / 'interrupted', run_id='interrupted')
    latest = []
    save = training.save_checkpoint
    evaluate = training.evaluate_inner
    validations = 0

    def callback(path, best):
        latest.append(path)
        if ((boundary == 'batch' and 'epoch-2-step-2-' in path.name)
                or (boundary == 'epoch' and path.name == 'inner-recovery-epoch-2.pt')):
            raise InterruptedError('synthetic interruption after committed checkpoint')

    def before_validation(*args, **options):
        nonlocal validations
        validations += 1
        if boundary == 'before-validation' and validations == 2:
            raise InterruptedError('synthetic validation boundary')
        return evaluate(*args, **options)

    def orphan(path, *args, **options):
        save(path, *args, **options)
        if boundary == 'orphan-best' and path.name.startswith('inner-best-epoch-1-'):
            raise InterruptedError('synthetic orphan best checkpoint')

    monkeypatch.setattr(training, 'save_checkpoint', orphan)
    monkeypatch.setattr(training, 'evaluate_inner', before_validation)
    if boundary == 'export':
        training.select_checkpoint(interrupted, **kwargs, checkpoint_callback=callback)
    else:
        with pytest.raises(InterruptedError):
            training.select_checkpoint(interrupted, **kwargs, checkpoint_callback=callback)
    monkeypatch.setattr(training, 'save_checkpoint', save)
    monkeypatch.setattr(training, 'evaluate_inner', evaluate)
    before = {path.name: digest_file(path) for path in interrupted.output_dir.iterdir()}
    fork = replace(config, run_id='resumed', output_dir=tmp_path / 'resumed')
    actual = training.select_checkpoint(fork, **kwargs, resume_checkpoint=latest[-1],
                                        checkpoint_callback=lambda path, best: None)
    assert actual.selected_epoch == expected.selected_epoch == 1
    assert len(actual.history) == len(expected.history) == 3
    assert [row['validation_loss'] for row in actual.history] == [row['validation_loss'] for row in expected.history]
    for old, new in zip(expected.history, actual.history):
        for field in ('valid_targets', 'optimizer_steps', 'windows_processed', 'processed_target_rows',
                      'collated_windows', 'loss_sum', 'target_tokens', 'valid_tokens', 'padding_tokens',
                      'sequence_length_counts', 'batch_shape_counts', 'parameter_update_steps'):
            assert new['training'][field] == old['training'][field], field
        assert new['training']['valid_targets'] == 17
        assert new['training']['optimizer_steps'] == 5
    assert_payload_equal(torch.load(config.output_dir / 'inner-recovery-epoch-3.pt', weights_only=True),
                         torch.load(fork.output_dir / 'inner-recovery-epoch-3.pt', weights_only=True))
    assert before == {path.name: digest_file(path) for path in interrupted.output_dir.iterdir()}


def test_refit_complete_epoch_can_fork_without_config_drift(tmp_path, monkeypatch):
    config, selection_kwargs = inputs(tmp_path / 'continuous')
    kwargs = dict(outer_train_users=('train',), train_learners_factory=selection_kwargs['train_learners_factory'],
                  selected_epochs=3, identity={'data': 'fixture'}, budget={'max_steps': 5}, save_recovery=True)
    expected = training.refit_outer_train(config, **kwargs)
    interrupted = replace(config, output_dir=tmp_path / 'old', run_id='old')
    save = training.save_checkpoint

    def stop(path, *args, **options):
        save(path, *args, **options)
        if path.name == 'refit-recovery-epoch-1.pt':
            raise InterruptedError('fixture')
    monkeypatch.setattr(training, 'save_checkpoint', stop)
    with pytest.raises(InterruptedError):
        training.refit_outer_train(interrupted, **kwargs)
    monkeypatch.setattr(training, 'save_checkpoint', save)
    fork = replace(config, output_dir=tmp_path / 'new', run_id='new')
    checkpoint = interrupted.output_dir / 'refit-recovery-epoch-1.pt'
    actual = training.refit_outer_train(fork, **kwargs, resume_checkpoint=checkpoint)
    assert all(torch.equal(p, q) for p, q in zip(actual.native.parameters(), expected.native.parameters()))
    with pytest.raises(ValueError, match='identity'):
        training.refit_outer_train(replace(fork, lr=.01), **kwargs, resume_checkpoint=checkpoint)


def test_refit_batch_fork_and_cumulative_step_target_caps(tmp_path):
    config, selection_kwargs = inputs(tmp_path / 'continuous')
    kwargs = dict(outer_train_users=('train',), train_learners_factory=selection_kwargs['train_learners_factory'],
                  selected_epochs=2, identity={'data': 'fixture'}, budget={'max_steps': 5}, save_recovery=True)
    expected = training.refit_outer_train(config, **kwargs)
    interrupted = replace(config, output_dir=tmp_path / 'old', run_id='old')
    checkpoints = []
    def stop(path, best):
        checkpoints.append(path)
        if 'refit-batch-epoch-2-step-2-' in path.name:
            raise InterruptedError('fixture batch interruption')
    with pytest.raises(InterruptedError):
        training.refit_outer_train(interrupted, **kwargs, checkpoint_callback=stop)
    fork = replace(config, output_dir=tmp_path / 'new', run_id='new')
    actual = training.refit_outer_train(fork, **kwargs, resume_checkpoint=checkpoints[-1])
    assert all(torch.equal(p, q) for p, q in zip(actual.native.parameters(), expected.native.parameters()))
    assert [row['loss_sum'] for row in actual.training_history] == [row['loss_sum'] for row in expected.training_history]

    # Không tăng caps để completion: bounded resume vẫn chỉ có cùng committed prefix.
    limited = replace(config, output_dir=tmp_path / 'limited', run_id='limited')
    capped = {**selection_kwargs, 'budget': {'max_steps': 2, 'max_targets': 8}}
    snapshots = []
    first = training.select_checkpoint(limited, **capped,
        checkpoint_callback=lambda path, best: snapshots.append(path))
    fork = replace(limited, output_dir=tmp_path / 'limited-fork', run_id='limited-fork')
    again = training.select_checkpoint(fork, **capped, resume_checkpoint=snapshots[-1])
    assert first.status == again.status == 'bounded'
    assert first.history[-1]['training']['optimizer_steps'] == again.history[-1]['training']['optimizer_steps'] == 2
    assert first.history[-1]['training']['valid_targets'] == again.history[-1]['training']['valid_targets'] <= 8
