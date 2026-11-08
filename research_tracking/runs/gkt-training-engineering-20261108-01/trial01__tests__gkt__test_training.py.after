"""Toy GKT train-batch, cumulative ledger<=8 actual Adam updates; không corpus."""
import copy
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import time

import pytest
import torch

from knowledge_tracing.gkt import GKTBinding, GKTKernelConfig
from knowledge_tracing.gkt.recurrent import GKTStaticRecurrentCandidate, RECIPE_ID, GRU_VARIANT
from knowledge_tracing.gkt import training as tr


@pytest.fixture(scope='module', autouse=True)
def bounded_cpu_and_update_ledger(tmp_path_factory):
    ledger = Path(os.environ.get('GKT_TRAINING_UPDATE_LEDGER', tmp_path_factory.getbasetemp() / 'updates.jsonl'))
    original = torch.optim.Adam.step
    threads = torch.get_num_threads()
    torch.set_num_threads(2)
    def counted(optimizer, *args, **kwargs):
        rows = ledger.read_text().splitlines() if ledger.exists() else []
        assert len(rows) < 8, 'cumulative actual optimizer cap exhausted BEFORE update'
        with ledger.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'update': len(rows) + 1, 'monotonic': time.perf_counter()}) + '\n')
        return original(optimizer, *args, **kwargs)
    torch.optim.Adam.step = counted
    try:
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(42)
            yield
    finally:
        torch.optim.Adam.step = original
        torch.set_num_threads(threads)


def model():
    c = GKTKernelConfig(3, 2, 2, 2, 'static', 'concept', True, True)
    binding = GKTBinding('toy-gkt-train-not-Junyi-not-Grade10', 'a' * 64, ('A', 'B', 'C'), 'concept')
    adjacency = torch.tensor([[0., .4, 0.], [.2, 0., .7], [0., .3, 0.]], dtype=torch.float64, device='cpu')
    return GKTStaticRecurrentCandidate(c, binding, adjacency, recipe_id=RECIPE_ID, mlp_hidden_dim=3,
        normalization='none', dropout=0, initial_state_policy='zeros', gru_variant=GRU_VARIANT)


def settings(**changes):
    values = dict(optimizer='adam', lr=.01, betas=(.8, .9), eps=1e-7, weight_decay=0.,
                  max_grad_norm=.5, objective='mean_bce_on_explicit_loss_mask', precision='float64')
    values.update(changes)
    return tr.GKTTrainingSettings(**values)


def optimizer(m, s=None):
    s = settings() if s is None else s
    return torch.optim.Adam(m.parameters(), lr=s.lr, betas=s.betas, eps=s.eps, weight_decay=s.weight_decay,
                            foreach=False, fused=False)


def batch(m, **changes):
    ids = torch.tensor([[0, 1, 2, 0], [2, 0, 1, 2]], device='cpu')
    values = dict(query_ids=ids, responses=torch.tensor([[0, 1, 1, 0], [1, 0, 1, 0]], device='cpu'),
        event_valid_mask=torch.ones_like(ids, dtype=torch.bool),
        loss_mask=torch.tensor([[False, True, True, True], [True, False, True, True]], device='cpu'),
        initial_state=m.initial_state(2, binding=m.binding, graph_sha256=m.graph_sha256),
        learner_ids=('toy-one', 'toy-two'), source_rows=torch.arange(1, 9, device='cpu').reshape(2, 4),
        global_ranks=torch.tensor([[0, 1, 2, 3], [0, 1, 2, 3]], device='cpu'),
        binding=m.binding, graph_sha256=m.graph_sha256, recipe_sha256=m.recipe_sha256,
        initial_state_model_sha256=tr.model_digest(m), role=tr.TRAIN_ROLE,
        synthetic_only=True, source_sha256=tr.source_identity())
    values.update(changes)
    return tr.bind_train_batch(**values)


def budget(**changes):
    values = dict(max_steps=8, max_targets=192, max_seconds=60., steps_used=0,
                  targets_used=0, started_at=time.perf_counter())
    values.update(changes)
    return tr.GKTStepBudget(**values)


def fields(b, **changes):
    values = dict(b.__dict__); values.pop('content_sha256'); values.update(changes)
    return tr.bind_train_batch(**values)


@pytest.fixture(scope='module')
def happy():
    m = model(); reference = copy.deepcopy(m); s = settings(); opt = optimizer(m, s); b = batch(m)
    # Independent objective and first-step Adam scalar formula; no reference optimizer.step.
    ref = reference.sequence(b.query_ids, b.responses, b.event_valid_mask,
        initial_state=b.initial_state, binding=b.binding, graph_sha256=b.graph_sha256)
    z = ref.logits[b.loss_mask]; y = b.responses[b.loss_mask].to(z.dtype)
    losses = torch.logaddexp(torch.zeros_like(z), z) - y * z
    expected_loss = float(losses.detach().sum())
    losses.mean().backward()
    norms = [p.grad.square().sum() for p in reference.parameters() if p.grad is not None]
    norm = torch.stack(norms).sum().sqrt()
    coefficient = min(1., s.max_grad_norm / (float(norm) + 1e-6))
    with torch.no_grad():
        for p in reference.parameters():
            if p.grad is not None:
                p.grad.mul_(coefficient)
                p.add_(-s.lr * p.grad / (p.grad.abs() + s.eps))
    m.eval(); m.self_mlp[0].train(True)
    flags = tuple(x.training for x in m.modules()); rng = torch.random.get_rng_state().clone()
    old_device = torch.get_default_device()
    try:
        torch.set_default_device('meta')
        result = tr.train_gkt_batch(m, opt, b, settings=s, budget=budget())
    finally:
        torch.set_default_device(old_device)
    return m, opt, b, result, reference, expected_loss, flags, rng


def test_one_step_matches_independent_loss_and_first_adam_equation(happy):
    m, _, b, r, reference, expected, _, _ = happy
    assert r.status == 'complete' and r.complete_train_step and r.optimizer_steps == 1
    assert r.selected_targets == 6 and r.observed_events == 8 and r.cumulative_targets == 6
    assert r.selected_source_rows == tuple(b.source_rows[b.loss_mask].tolist())
    assert r.loss_sum == pytest.approx(expected, abs=1e-12)
    assert r.mean_loss == pytest.approx(expected / 6, abs=1e-12)
    assert r.role == tr.WEIGHT_ROLE and r.model_sha256_before != r.model_sha256_after
    assert math.isfinite(r.grad_norm) and r.grad_norm > 0
    for actual, expected in zip(m.parameters(), reference.parameters()):
        torch.testing.assert_close(actual, expected, rtol=1e-12, atol=1e-12)
        if actual.grad is not None:
            assert torch.isfinite(actual.grad).all()
    assert all(x.device.type == 'cpu' for x in m.parameters())


def test_caller_flags_rng_inputs_and_preupdate_state_identity(happy):
    m, _, b, r, _, _, flags, rng = happy
    assert tuple(x.training for x in m.modules()) == flags
    assert torch.equal(torch.random.get_rng_state(), rng)
    assert tr._batch_digest(b) == b.content_sha256
    assert r.state_computed_with_model_sha256 == r.model_sha256_before
    assert r.final_state.values.grad_fn is None and not r.final_state.values.requires_grad
    assert r.final_state.values.data_ptr() != b.initial_state.values.data_ptr()
    assert b.initial_state.history_counts.tolist() == [0, 0]
    assert r.final_state.history_counts.tolist() == [4, 4]
    assert not hasattr(r, 'completed_epoch') and not hasattr(r, 'resume_supported')


def test_stale_initial_and_postupdate_diagnostic_state_rejected_before_forward(happy, monkeypatch):
    m, opt, b, r, *_ = happy
    monkeypatch.setattr(m, 'sequence', lambda *a, **k: pytest.fail('stale state must fail BEFORE forward'))
    with pytest.raises(ValueError, match='parameter-version'):
        tr.train_gkt_batch(m, opt, b, settings=settings(), budget=budget())
    diagnostic = fields(b, initial_state=r.final_state)
    with pytest.raises(ValueError, match='parameter-version'):
        tr.train_gkt_batch(m, opt, diagnostic, settings=settings(), budget=budget())


def test_padding_matches_equivalent_compacted_events_and_updates():
    m = model(); compact = copy.deepcopy(m); b = batch(m)
    mask = torch.tensor([[True, False, True, True], [True, True, False, True]], device='cpu')
    ids = b.query_ids.clone(); answers = b.responses.clone(); rows = b.source_rows.clone()
    ranks = torch.tensor([[0, -1, 1, 2], [0, 1, -1, 2]], device='cpu')
    ids[~mask] = 999; answers[~mask] = -9; rows[~mask] = -1
    padded = fields(b, query_ids=ids, responses=answers, source_rows=rows,
                    global_ranks=ranks, event_valid_mask=mask, loss_mask=mask)
    packed = fields(batch(compact), query_ids=ids[mask].reshape(2, 3), responses=answers[mask].reshape(2, 3),
        source_rows=rows[mask].reshape(2, 3), global_ranks=ranks[mask].reshape(2, 3),
        event_valid_mask=torch.ones((2, 3), dtype=torch.bool, device='cpu'),
        loss_mask=torch.ones((2, 3), dtype=torch.bool, device='cpu'))
    left = tr.train_gkt_batch(m, optimizer(m), padded, settings=settings(), budget=budget())
    right = tr.train_gkt_batch(compact, optimizer(compact), packed, settings=settings(), budget=budget())
    assert left.selected_source_rows == right.selected_source_rows and left.selected_targets == right.selected_targets == 6
    assert left.loss_sum == pytest.approx(right.loss_sum, abs=1e-12)
    for a, b in zip(m.parameters(), compact.parameters()):
        torch.testing.assert_close(a, b, rtol=1e-12, atol=1e-12)


def test_post_update_deadline_consumes_step_and_is_not_complete(monkeypatch):
    m = model(); opt = optimizer(m); b = batch(m); bound = budget(started_at=0., max_seconds=1.)
    times = iter([0., 0., 2., 2.])
    monkeypatch.setattr(tr, '_elapsed', lambda unused_budget: next(times))
    r = tr.train_gkt_batch(m, opt, b, settings=settings(), budget=bound)
    assert r.status == 'bounded' and r.stop_reason == 'max_seconds_after_update'
    assert r.optimizer_steps == r.cumulative_steps == 1 and r.cumulative_targets == 6
    assert not r.complete_train_step and r.model_sha256_before != r.model_sha256_after


@pytest.mark.parametrize('reason,changes', [
    ('max_steps', {'max_steps': 1, 'steps_used': 1}),
    ('max_targets', {'max_targets': 5}),
    ('max_seconds', {'started_at': 0., 'max_seconds': 1.}),
])
def test_exhausted_budget_never_calls_forward_or_step(monkeypatch, reason, changes):
    m = model(); opt = optimizer(m); b = batch(m)
    monkeypatch.setattr(m, 'sequence', lambda *a, **k: pytest.fail('budget before forward'))
    monkeypatch.setattr(opt, 'step', lambda: pytest.fail('budget before step'))
    r = tr.train_gkt_batch(m, opt, b, settings=settings(), budget=budget(**changes))
    assert r.status == 'bounded' and r.stop_reason == reason and r.optimizer_steps == 0
    assert r.model_sha256_before == r.model_sha256_after and r.final_state is None


@pytest.mark.parametrize('case', ['role', 'synthetic', 'domain', 'vocab', 'graph', 'recipe', 'source',
    'mutated_tensor', 'unknown', 'nonbinary', 'loss_subset', 'empty_loss', 'duplicate_rows',
    'ranks', 'state_grad', 'state_model', 'optimizer_lr', 'optimizer_missing', 'optimizer_duplicate',
    'precision', 'oversize'])
def test_invalid_contracts_fail_before_forward(case, monkeypatch):
    m = model(); opt = optimizer(m); b = batch(m); s = settings()
    if case == 'role': b = fields(b, role='validation')
    elif case == 'synthetic': b = fields(b, synthetic_only=False)
    elif case == 'domain': b = fields(b, binding=replace(b.binding, domain='Grade10'))
    elif case == 'vocab': b = fields(b, binding=replace(b.binding, vocabulary_sha256='b' * 64))
    elif case == 'graph': b = fields(b, graph_sha256='b' * 64)
    elif case == 'recipe': b = fields(b, recipe_sha256='b' * 64)
    elif case == 'source': b = fields(b, source_sha256={})
    elif case == 'mutated_tensor': b.responses[0, 0] = 1
    elif case == 'unknown':
        x = b.query_ids.clone(); x[0, 0] = 999; b = fields(b, query_ids=x)
    elif case == 'nonbinary':
        x = b.responses.clone(); x[0, 0] = 2; b = fields(b, responses=x)
    elif case == 'loss_subset':
        x = b.event_valid_mask.clone(); x[0, 1] = False; b = fields(b, event_valid_mask=x)
    elif case == 'empty_loss': b = fields(b, loss_mask=torch.zeros_like(b.loss_mask))
    elif case == 'duplicate_rows':
        x = b.source_rows.clone(); x[0, 1] = x[0, 0]; b = fields(b, source_rows=x)
    elif case == 'ranks': b = fields(b, global_ranks=b.global_ranks.flip(1))
    elif case == 'state_grad':
        state = replace(b.initial_state, values=b.initial_state.values.clone().requires_grad_())
        b = fields(b, initial_state=state)
    elif case == 'state_model': b = fields(b, initial_state_model_sha256='b' * 64)
    elif case == 'optimizer_lr': opt.param_groups[0]['lr'] *= 2
    elif case == 'optimizer_missing': opt.param_groups[0]['params'] = opt.param_groups[0]['params'][:-1]
    elif case == 'optimizer_duplicate': opt.param_groups[0]['params'][-1] = opt.param_groups[0]['params'][0]
    elif case == 'precision': s = settings(precision='float32')
    elif case == 'oversize': m.mlp_hidden_dim = 9
    monkeypatch.setattr(m, 'sequence', lambda *a, **k: pytest.fail('guard before forward'))
    monkeypatch.setattr(opt, 'step', lambda: pytest.fail('guard before step'))
    with pytest.raises(ValueError): tr.train_gkt_batch(m, opt, b, settings=s, budget=budget())


def test_source_drift_before_forward(monkeypatch):
    m = model(); b = batch(m); opt = optimizer(m)
    monkeypatch.setattr(tr, 'source_identity', lambda: {})
    monkeypatch.setattr(m, 'sequence', lambda *a, **k: pytest.fail('source guard before forward'))
    with pytest.raises(ValueError, match='source'):
        tr.train_gkt_batch(m, opt, b, settings=settings(), budget=budget())


def test_current_response_changes_do_not_change_current_scores_without_updates():
    m = model(); b = batch(m)
    def forward(answers):
        return m.sequence(b.query_ids, answers, b.event_valid_mask, initial_state=b.initial_state,
                          binding=b.binding, graph_sha256=b.graph_sha256).logits
    baseline = forward(b.responses)
    changed = b.responses.clone(); changed[:, 2:] = 1 - changed[:, 2:]
    assert torch.equal(forward(changed)[:, :3], baseline[:, :3])


@pytest.mark.parametrize('changes', [{'lr': True}, {'eps': float('nan')}, {'betas': (.9, 1.)},
    {'weight_decay': -1.}, {'objective': 'implicit'}, {'precision': 'cuda'}, {'max_grad_norm': 0.}])
def test_explicit_settings_invalid(changes):
    with pytest.raises(ValueError): settings(**changes)


@pytest.mark.parametrize('changes', [{'max_steps': 9}, {'steps_used': True}, {'max_targets': 193},
    {'max_seconds': 61.}, {'started_at': float('inf')}, {'steps_used': 9}, {'targets_used': -1}])
def test_explicit_budget_invalid(changes):
    with pytest.raises(ValueError): budget(**changes)
