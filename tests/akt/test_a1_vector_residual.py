"""Đối chiếu A1 vector hóa với công thức scalar cũ trên native AKT CPU.

Giữ nguyên ngưỡng, RNG/dropout, loss và Adam. Alpha gradient có thể đổi cây
cộng FP32, nên nghiệm thu số học có tolerance thay vì claim bitwise trajectory.
"""
import pytest
import torch
from torch.nn import functional as F

from test_junyi_graph_model import setup
from knowledge_tracing.akt.tensors import collate_windows
from knowledge_tracing.akt.windows import iter_windows


def legacy_forward(native, batch, evidence, *, enabled):
    """Công thức A1 scalar trước tối ưu, giữ thứ tự ghi và nhân gate=1."""
    active = []
    if enabled:
        for row, items in enumerate(evidence):
            for local, item in enumerate(items):
                if item is None:
                    continue
                observed = tuple(parent for parent in item.audit.parents if parent.support > 0)
                mass = sum(parent.confidence for parent in observed)
                if mass > 0:
                    message = sum(parent.confidence * (parent.mean_observed_correctness - .5)
                                  for parent in observed) / max(1., mass)
                    active.append((row, local, message))
    if not active:
        return native.backbone(batch.q_data, batch.qa_data, batch.loss_targets)
    question = native.backbone.q_embed(batch.q_data)
    responses = (batch.qa_data - batch.q_data) // native.backbone.n_question
    answer = native.backbone.qa_embed(responses) + question
    hidden = native.backbone.model(question, answer)
    base_logits = native.backbone.out(torch.cat([hidden, question], dim=-1)).reshape(batch.q_data.shape)
    base_probabilities = torch.sigmoid(base_logits)
    residual = torch.zeros_like(base_logits)
    applied = torch.zeros_like(batch.q_data, dtype=torch.bool)
    for row, local, message in active:
        residual[row, local] = native.alpha * base_logits.new_ones(()) * message
        applied[row, local] = True
    logits = base_logits + residual
    probabilities = torch.where(applied, torch.sigmoid(logits), base_probabilities)
    labels = batch.loss_targets.reshape(-1)
    mask = labels > -.9
    loss = F.binary_cross_entropy_with_logits(logits.reshape(-1)[mask], labels[mask].float(),
                                             reduction='none').sum()
    return loss, probabilities.reshape(-1), mask.sum()


def make_case(setup, *, unsupported=False):
    adapter = setup['adapter'](edges=(('B', 'C'),) if unsupported else (('A', 'C'),))
    learners = [setup['student'](setup['train'].users[0], labels=(1, 0, 0, 1, 1, 0)),
                setup['student'](setup['train'].users[1], items=('A', 'C', 'A'), labels=(0, 1, 1))]
    entries = tuple(entry for learner in learners
                    for entry in iter_windows(learner, adapter.encoding, training=True))
    windows = tuple(entry.window for entry in entries)
    batch = collate_windows(windows, n_items=3, device='cpu', targets=[entry.targets for entry in entries])
    evidence = tuple(adapter.phase.prefix_evidence(window) for window in windows)
    assert batch.q_data.shape == (2, 6)
    assert not batch.valid_mask[1, 3:].any()
    return adapter, batch, evidence


@pytest.mark.parametrize('alpha', [0., .75])
@pytest.mark.parametrize('mode', ['enabled', 'off', 'unsupported'])
def test_a1_vector_matches_scalar_loss_gradients_and_two_adam_steps(setup, alpha, mode):
    adapter, batch, evidence = make_case(setup, unsupported=mode == 'unsupported')
    reference = setup['adapter'](edges=(('B', 'C'),) if mode == 'unsupported' else (('A', 'C'),)).native
    current = adapter.native
    with torch.no_grad():
        current.alpha.fill_(alpha)
    reference.load_state_dict(current.state_dict(), strict=True)
    current.train()
    reference.train()
    optimizer_current = torch.optim.Adam(current.parameters(), lr=1e-4, foreach=False, fused=False)
    optimizer_reference = torch.optim.Adam(reference.parameters(), lr=1e-4, foreach=False, fused=False)
    enabled = mode != 'off'
    drift = dict(loss=0., probability=0., gradient=0., parameter=0.)
    for step in range(2):
        optimizer_current.zero_grad(set_to_none=True)
        optimizer_reference.zero_grad(set_to_none=True)
        rng = torch.get_rng_state().clone()
        expected = legacy_forward(reference, batch, evidence, enabled=enabled)
        (expected[0] / expected[2]).backward()
        torch.set_rng_state(rng)
        current.bind(batch, evidence, enabled=enabled)
        actual = current(batch.q_data, batch.qa_data, batch.loss_targets)
        (actual[0] / actual[2]).backward()
        assert actual[2].item() == expected[2].item() == 9
        torch.testing.assert_close(actual[0], expected[0], atol=1e-6, rtol=1e-6)
        torch.testing.assert_close(actual[1], expected[1], atol=1e-7, rtol=1e-6)
        drift['loss'] = max(drift['loss'], abs(actual[0].item() - expected[0].item()))
        drift['probability'] = max(drift['probability'], float((actual[1]-expected[1]).abs().max()))
        for (name, parameter), (other_name, other) in zip(current.named_parameters(), reference.named_parameters()):
            assert name == other_name
            assert (parameter.grad is None) == (other.grad is None), name
            if parameter.grad is not None:
                torch.testing.assert_close(parameter.grad, other.grad, atol=1e-7, rtol=1e-5, msg=name)
                drift['gradient'] = max(drift['gradient'], float((parameter.grad-other.grad).abs().max()))
        if mode == 'enabled' and step == 0:
            assert current.alpha.grad is not None and current.alpha.grad.abs().item() > 0
        elif mode != 'enabled':
            assert current.alpha.grad is None
        optimizer_current.step()
        optimizer_reference.step()
        for (name, parameter), (_, other) in zip(current.named_parameters(), reference.named_parameters()):
            torch.testing.assert_close(parameter, other, atol=2e-7, rtol=2e-5, msg=name)
            drift['parameter'] = max(drift['parameter'], float((parameter-other).abs().max()))
    print(dict(alpha=alpha, mode=mode, max_absolute_drift=drift))


@pytest.mark.parametrize('when', ['before_bind', 'after_bind'])
def test_bulk_mask_snapshot_keeps_context_and_mutation_checks(setup, when):
    adapter, batch, evidence = make_case(setup)
    if when == 'before_bind':
        batch.target_mask[0, 1] = False
        with pytest.raises(ValueError, match='context outside target mask'):
            adapter.native.bind(batch, evidence, enabled=True)
    else:
        adapter.native.bind(batch, evidence, enabled=True)
        batch.target_mask[0, 1] = False
        with pytest.raises(ValueError, match='batch changed after binding'):
            adapter.native(batch.q_data, batch.qa_data, batch.loss_targets)
