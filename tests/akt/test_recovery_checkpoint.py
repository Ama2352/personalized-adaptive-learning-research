import random

import numpy as np
import pytest
import torch

from knowledge_tracing.akt.checkpoint import (
    load_checkpoint, load_recovery_checkpoint, restore_checkpoint,
    restore_recovery_checkpoint, save_checkpoint, save_recovery_checkpoint,
)
from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.model import AKTAdapter
from knowledge_tracing.akt.tensors import collate_windows
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows


def setup_model():
    learner = LearnerEvents('synthetic', 1, tuple(
        KTEvent('synthetic', 'A', i + 1, i + 1, i % 2, 0, 1) for i in range(4)))
    encoding = fit_vocabulary([learner])
    model = AKTAdapter(AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32), encoding)
    optimizer = torch.optim.Adam(model.native.parameters(), lr=0.001)
    entry = next(iter_windows(learner, encoding, training=True))
    batch = collate_windows([entry.window], n_items=1, device='cpu', targets=[entry.targets])
    return model, optimizer, batch


def state():
    return {'schema_version': 1, 'epoch': 1, 'optimizer_steps': 1,
            'sampler_state': {'next_window': 1, 'seed': 43, 'stream_hash': 'synthetic'},
            'trainer_state': {'valid_targets': 4, 'loss_sum': 2.0}}


def test_recovery_restores_next_real_akt_update_and_rng(tmp_path):
    torch.manual_seed(42)
    model, optimizer, batch = setup_model()
    model.native.train()
    model.step(batch, optimizer)
    path = tmp_path / 'recovery.pt'
    save_recovery_checkpoint(path, model, optimizer, identity={'run': 'test'}, resume_state=state())
    expected_draws = torch.rand(3), random.random(), np.random.random()
    expected_step = model.step(batch, optimizer)
    expected_weights = {name: value.detach().clone() for name, value in model.native.state_dict().items()}
    clone, clone_optimizer, clone_batch = setup_model()
    payload = load_recovery_checkpoint(path, expected_identity={'run': 'test'}, device='cpu')
    restored = restore_recovery_checkpoint(clone, clone_optimizer, payload)
    assert restored == state()
    assert torch.equal(torch.rand(3), expected_draws[0])
    assert (random.random(), np.random.random()) == expected_draws[1:]
    actual_step = clone.step(clone_batch, clone_optimizer)
    assert actual_step['loss_sum'] == expected_step['loss_sum']
    assert all(torch.equal(value, expected_weights[name])
               for name, value in clone.native.state_dict().items())
    with pytest.raises(ValueError, match='incomplete'):
        load_checkpoint(path, expected_identity={'run': 'test'}, device='cpu')
    with pytest.raises(ValueError, match='incomplete'):
        restore_checkpoint(clone, clone_optimizer, payload)
    with pytest.raises(ValueError, match='identity'):
        load_recovery_checkpoint(path, expected_identity={'run': 'other'}, device='cpu')
    with pytest.raises(FileExistsError):
        save_recovery_checkpoint(path, model, optimizer, identity={}, resume_state=state())


@pytest.mark.parametrize('change', [
    {'schema_version': 2}, {'epoch': 0}, {'optimizer_steps': True},
    {'sampler_state': {}}, {'trainer_state': None},
])
def test_invalid_recovery_state_writes_nothing(tmp_path, change):
    model, optimizer, _ = setup_model()
    path = tmp_path / 'bad.pt'
    with pytest.raises(ValueError):
        save_recovery_checkpoint(path, model, optimizer, identity={}, resume_state={**state(), **change})
    assert not path.exists()


def test_complete_epoch_is_not_loaded_as_recovery(tmp_path):
    model, optimizer, _ = setup_model()
    path = tmp_path / 'selected.pt'
    save_checkpoint(path, model, optimizer, identity={}, progress={'epoch': 1, 'complete': True})
    with pytest.raises(ValueError, match='not a training recovery'):
        load_recovery_checkpoint(path, expected_identity={}, device='cpu')
