import random

import numpy as np
import pytest
import torch

from knowledge_tracing.akt.checkpoint import load_checkpoint, restore_checkpoint, save_checkpoint
import knowledge_tracing.akt.checkpoint as checkpoint_module
from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.model import AKTAdapter
from knowledge_tracing.akt.types import KTEvent, LearnerEvents


def adapter():
    learner = LearnerEvents('u', 0, (KTEvent('u', 'A', 1, 1, 1, 0, 0),))
    enc = fit_vocabulary([learner])
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0.0)
    return AKTAdapter(cfg, enc)


def test_checkpoint_roundtrip_restores_state_and_rejects_mismatch(tmp_path):
    model = adapter()
    opt = torch.optim.Adam(model.native.parameters(), lr=0.001)
    path = tmp_path / 'checkpoint.pt'
    identity = {'source': 'pinned', 'vocab': 'v1', 'split': 's1', 'config': 'c1'}
    save_checkpoint(path, model, opt, identity=identity, progress={'epoch': 2, 'complete': True})
    payload = load_checkpoint(path, expected_identity=identity, device='cpu')
    assert payload['progress']['epoch'] == 2
    clone = adapter()
    clone.native.load_state_dict(payload['model_state_dict'])
    for left, right in zip(model.native.parameters(), clone.native.parameters()):
        assert torch.equal(left, right)
    for key in identity:
        with pytest.raises(ValueError, match='identity'):
            load_checkpoint(path, expected_identity={**identity, key: 'changed'}, device='cpu')
    with pytest.raises(FileExistsError):
        save_checkpoint(path, model, opt, identity=identity, progress={'epoch': 3, 'complete': True})


@pytest.mark.parametrize('optimizer_class', [torch.optim.Adam, torch.optim.AdamW])
@pytest.mark.parametrize('capturable,fused,expected_calls', [
    (False, False, 1), (True, False, 0), (False, True, 0),
])
def test_adam_resume_step_device_policy(monkeypatch, optimizer_class, capturable, fused, expected_calls):
    parameter = torch.nn.Parameter(torch.ones(1))
    optimizer = optimizer_class([parameter], capturable=capturable, fused=fused)
    step = torch.tensor(3.)
    momentum = torch.tensor([.25])
    optimizer.state[parameter] = {'step': step, 'exp_avg': momentum}
    original_cpu = torch.Tensor.cpu
    calls = []

    def record_cpu(tensor, *args, **kwargs):
        calls.append(tensor)
        return original_cpu(tensor, *args, **kwargs)

    monkeypatch.setattr(torch.Tensor, 'cpu', record_cpu)
    checkpoint_module._restore_adam_step_devices(optimizer)
    assert len(calls) == expected_calls
    assert all(value is step for value in calls)
    assert optimizer.state[parameter]['step'].item() == 3
    assert optimizer.state[parameter]['exp_avg'] is momentum


def test_checkpoint_rejects_incomplete_epoch(tmp_path):
    model = adapter()
    optimizer = torch.optim.Adam(model.native.parameters(), lr=0.001)
    with pytest.raises(ValueError, match='complete'):
        save_checkpoint(tmp_path / 'partial.pt', model, optimizer, identity={},
                        progress={'epoch': 1, 'complete': False})


def test_checkpoint_rejects_protected_output_before_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(checkpoint_module, 'PROJECT_ROOT', tmp_path)
    model = adapter()
    optimizer = torch.optim.Adam(model.native.parameters(), lr=0.001)
    path = tmp_path / 'artifacts/bkt_baseline/forbidden.pt'
    with pytest.raises(ValueError, match='protected'):
        save_checkpoint(path, model, optimizer, identity={}, progress={'epoch': 1, 'complete': True})
    assert not path.parent.exists()


def test_save_load_resume_reproduces_next_optimizer_step(tmp_path):
    torch.manual_seed(918)
    model = adapter()
    optimizer = torch.optim.Adam(model.native.parameters(), lr=0.001)
    path = tmp_path / 'resume.pt'
    identity = {'source': 'pinned', 'split': 's1'}
    save_checkpoint(path, model, optimizer, identity=identity,
                    progress={'epoch': 1, 'complete': True, 'sampler_seed': 919})

    expected_draws = (torch.rand(4), random.random(), np.random.random())
    expected_loss = sum(parameter.square().sum() for parameter in model.native.parameters())
    expected_loss.backward()
    optimizer.step()
    expected_parameters = [parameter.detach().clone() for parameter in model.native.parameters()]
    torch.rand(7)
    random.random()
    np.random.random()

    resumed = adapter()
    resumed_optimizer = torch.optim.Adam(resumed.native.parameters(), lr=0.001)
    payload = load_checkpoint(path, expected_identity=identity, device='cpu')
    restore_checkpoint(resumed, resumed_optimizer, payload)
    actual_draws = (torch.rand(4), random.random(), np.random.random())
    actual_loss = sum(parameter.square().sum() for parameter in resumed.native.parameters())
    actual_loss.backward()
    resumed_optimizer.step()

    assert torch.equal(actual_draws[0], expected_draws[0])
    assert actual_draws[1:] == expected_draws[1:]
    assert all(torch.equal(actual, expected)
               for actual, expected in zip(resumed.native.parameters(), expected_parameters))


def test_cuda_rng_restore_returns_remapped_state_to_cpu(tmp_path, monkeypatch):
    """Mô phỏng map_location=cuda; không giả là actual CUDA execution."""
    model = adapter()
    optimizer = torch.optim.Adam(model.native.parameters(), lr=.001)
    path = tmp_path / 'rng.pt'
    save_checkpoint(path, model, optimizer, identity={}, progress={'epoch': 1, 'complete': True})
    payload = load_checkpoint(path, expected_identity={}, device='cpu')
    state = torch.arange(16, dtype=torch.uint8)
    calls = []
    class RemappedState:
        def cpu(self):
            calls.append('cpu')
            return state
    payload['cuda_rng'] = [RemappedState()]
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: True)
    def restore(states):
        assert len(states) == 1 and isinstance(states[0], torch.Tensor)
        assert states[0].device.type == 'cpu' and states[0].dtype == torch.uint8
        assert torch.equal(states[0], state)
        calls.append('restore')
    monkeypatch.setattr(torch.cuda, 'set_rng_state_all', restore)
    restore_checkpoint(model, optimizer, payload)
    assert calls == ['cpu', 'restore']
