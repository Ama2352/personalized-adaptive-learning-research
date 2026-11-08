"""Synthetic CPU trainer contracts; shared per-invocation optimizer budget≤32."""

from dataclasses import replace
import json
import os
from pathlib import Path

import numpy as np
import pytest
import torch

from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.sakt.config import SAKTConfig
from knowledge_tracing.sakt.model import SAKTCore
from knowledge_tracing.sakt import training
from knowledge_tracing.sakt.training import (SAKTTrainingConfig, collate_target_batch, evaluate_sakt,
    masked_bce, population_ledger, state_digest, train_synthetic_sakt)
from knowledge_tracing.sakt.training_data import SAKTDataRecipe, prepare_sakt_training_data
from knowledge_tracing.sakt.training_checkpoint import save_engineering_weights


@pytest.fixture(autouse=True)
def cpu_budget(monkeypatch, tmp_path_factory):
    ledger = Path(os.environ.get('SAKT_TRAINING_UPDATE_LEDGER', tmp_path_factory.getbasetemp() / 'optimizer_updates.jsonl'))
    ledger.parent.mkdir(parents=True, exist_ok=True)
    original = torch.optim.Adam.step
    def counted(optimizer, *args, **kwargs):
        previous = ledger.read_text(encoding='utf-8').splitlines() if ledger.exists() else []
        assert len(previous) < 32, 'global synthetic optimizer budget exhausted BEFORE next update'
        with ledger.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'step': len(previous) + 1, 'test': os.environ.get('PYTEST_CURRENT_TEST'),
                                     'module': __name__, 'device': 'cpu'}) + '\n')
        return original(optimizer, *args, **kwargs)
    monkeypatch.setattr(torch.optim.Adam, 'step', counted)
    threads = torch.get_num_threads(); torch.set_num_threads(1)
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(42)
        yield
    torch.set_num_threads(threads)


def learner(user, items, labels, start):
    return LearnerEvents(user, 1, tuple(KTEvent(user, item, i + 10, start + i, int(label), 0, 1)
                                      for i, (item, label) in enumerate(zip(items, labels))))


def recipe(**changes):
    values = dict(context=2, padding_side='right', first_target_policy='query_only',
                  window_policy='sliding_last_context', position_policy='window_relative_interaction_rank')
    values.update(changes); return SAKTDataRecipe(**values)


def data(**changes):
    return prepare_sakt_training_data((learner('train', 'ABAB', [0, 1, 0, 1], 1),),
        (learner('validation', 'ACBA', [1, 0, 1, 0], 101),),
        domain='synthetic-unit-test-not-Junyi-or-Grade10', recipe=recipe(**changes), synthetic_only=True)


def model_config(d=None, **changes):
    d = data() if d is None else d
    values = dict(num_items=len(d.vocabulary.values), max_length=d.recipe.context + 1,
                  d_model=8, num_heads=2, head_dim=4, dropout=0., layer_norm_eps=1e-5)
    values.update(changes); return SAKTConfig(**values)


def train_config(**changes):
    values = dict(optimizer='adam', lr=.01, betas=(.9, .999), eps=1e-8, weight_decay=0.,
        max_grad_norm=1., epochs=1, batch_size=4, shuffle_seed=42,
        objective='mean_bce_on_eligible_targets', max_steps=4, max_targets=64, max_seconds=30.,
        device='cpu', precision='float32')
    values.update(changes); return SAKTTrainingConfig(**values)


@pytest.mark.parametrize('cold', ['query_only', 'unsupported'])
def test_train_only_vocabulary_oov_barrier_and_loss_population(cold):
    d = data(first_target_policy=cold)
    assert d.vocabulary.values == ('A', 'B') and 'C' not in d.train_support_students
    records = d.validation
    assert records[1].reason == 'oov_item' and records[1].inputs is None
    assert records[2].history_used == 0 and records[2].context_reset
    assert records[2].reason == ('cold_query_only' if cold == 'query_only' else 'cold_unsupported')
    assert records[3].history_used == 1
    ledger = population_ledger(records)
    assert ledger['expected_targets'] == ledger['eligible_targets'] + ledger['oov_targets'] + ledger['cold_excluded_targets']
    assert len({x.source_row for x in records}) == len(records)
    d.assert_integrity()


@pytest.mark.parametrize('side', ['left', 'right'])
def test_terminal_mask_context_never_in_loss_and_prior_shift_once(side):
    d = data(padding_side=side)
    records = list(d.train)
    batch, labels, mask = collate_target_batch(records, model_config=model_config(d), recipe=d.recipe)
    assert int(mask.sum()) == len(records)
    for row, record in enumerate(records):
        pos = len(record.inputs.item_ids) - 1 if side == 'right' else batch.item_ids.shape[1] - 1
        assert mask[row, pos] and int(labels[row, pos]) == record.target
        assert int(mask[row].sum()) == 1
    assert records[2].inputs.prior_responses.tolist() == [-1, 0, 1]
    assert records[3].inputs.item_ids.tolist() == [1, 0, 1]
    assert records[3].inputs.prior_responses.tolist() == [-1, 1, 0]
    assert all(len(x.inputs.item_ids) <= d.recipe.context + 1 for x in records)


def test_masked_bce_known_answer_ignores_invalid_context_values():
    logits = torch.tensor([[float('nan'), 0., 9.]])
    labels = torch.tensor([[-1., 1., -1.]])
    total, n = masked_bce(logits, labels, torch.tensor([[False, True, False]]))
    assert n == 1 and float(total) == pytest.approx(np.log(2), abs=1e-7)
    with pytest.raises(ValueError): masked_bce(logits, labels, torch.ones_like(labels, dtype=torch.bool))


def test_training_has_finite_updates_unique_targets_reproducible_and_preserves_caller_rng():
    d = data(); cfg, tc = model_config(d), train_config()
    rng = torch.get_rng_state().clone()
    with torch.random.fork_rng(devices=[]), torch.device('cpu'):
        torch.random.default_generator.manual_seed(tc.shuffle_seed); initial = state_digest(SAKTCore(cfg))
    first = train_synthetic_sakt(d, model_config=cfg, training_config=tc)
    second = train_synthetic_sakt(d, model_config=cfg, training_config=tc)
    assert first.status == 'complete' and first.optimizer_steps == 1
    assert first.model_state_sha256 != initial and first.model_state_sha256 == second.model_state_sha256
    assert torch.equal(rng, torch.get_rng_state())
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in first.model.parameters())
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in first.model.parameters())
    ledger = first.history[0]['population']
    assert ledger['optimized_targets'] == 4 and len(set(ledger['optimized_source_rows'])) == 4
    assert ledger['unprocessed_eligible_targets'] == 0
    assert first.role == 'synthetic_trained_engineering_only'


def test_budget_incomplete_retains_unprocessed_targets_and_cannot_save(tmp_path):
    d = prepare_sakt_training_data((learner('train', 'ABABAB', [0, 1, 0, 1, 0, 1], 1),),
        (learner('validation', 'AB', [1, 0], 101),), domain='synthetic-budget', recipe=recipe(), synthetic_only=True)
    result = train_synthetic_sakt(d, model_config=model_config(d), training_config=train_config(max_steps=1))
    assert result.status == 'bounded' and result.optimizer_steps == 1 and result.completed_epochs == 0
    assert result.history[0]['population']['unprocessed_eligible_targets'] == 2
    with pytest.raises(ValueError, match='completed'): save_engineering_weights(tmp_path / 'incomplete.pt', result)
    zero = train_synthetic_sakt(d, model_config=model_config(d), training_config=train_config(max_targets=3))
    assert zero.optimizer_steps == 0 and zero.status == 'bounded'
    assert zero.role == 'synthetic_untrained_engineering_attempt'


def test_evaluation_no_update_no_loss_for_oov_and_restores_mode():
    d = data(); result = train_synthetic_sakt(d, model_config=model_config(d), training_config=train_config())
    result.model.train(); before = state_digest(result.model)
    evaluated = evaluate_sakt(result.model, d, batch_size=2)
    assert result.model.training and state_digest(result.model) == before
    assert evaluated['eligible_targets'] == 3 and evaluated['predictions'][1]['probability'] is None
    assert evaluated['role'] == 'synthetic_evaluation_no_fit_attestation'


def test_current_target_label_does_not_enter_its_forward_inputs():
    left = data()
    changed = prepare_sakt_training_data((learner('train', 'ABAB', [0, 1, 1, 1], 1),),
        (learner('validation', 'ACBA', [1, 0, 1, 0], 101),), domain=left.domain, recipe=left.recipe, synthetic_only=True)
    for field in ['item_ids', 'prior_responses']:
        np.testing.assert_array_equal(getattr(left.train[2].inputs, field), getattr(changed.train[2].inputs, field))
    cfg = model_config(left)
    with torch.device('cpu'): core = SAKTCore(cfg).eval()
    a, _, mask_a = collate_target_batch([left.train[2]], model_config=cfg, recipe=left.recipe)
    b, _, mask_b = collate_target_batch([changed.train[2]], model_config=cfg, recipe=left.recipe)
    torch.testing.assert_close(core(a).logits[mask_a], core(b).logits[mask_b])
    assert left.train[3].inputs.prior_responses[-1] != changed.train[3].inputs.prior_responses[-1]


def test_validation_deadline_checks_after_forward_without_new_optimizer(monkeypatch):
    d = data(); core = SAKTCore(model_config(d)).eval(); clock = [0.]
    original = core.forward
    def delayed(batch):
        value = original(batch); clock[0] = 2.; return value
    monkeypatch.setattr(core, 'forward', delayed)
    monkeypatch.setattr(training.time, 'perf_counter', lambda: clock[0])
    with pytest.raises(TimeoutError, match='deadline'):
        evaluate_sakt(core, d, batch_size=2, deadline=1.)


def test_validation_timeout_marks_training_incomplete_and_checkpoint_rejects(monkeypatch, tmp_path):
    d = data()
    def timeout(*args, **kwargs): raise TimeoutError('injected validation deadline')
    monkeypatch.setattr(training, 'evaluate_sakt', timeout)
    result = train_synthetic_sakt(d, model_config=model_config(d), training_config=train_config())
    assert result.status == 'bounded' and result.stop_reason == 'max_seconds_validation'
    assert result.completed_epochs == 0 and result.history[0]['training_complete']
    with pytest.raises(ValueError): save_engineering_weights(tmp_path / 'deadline.pt', result)


def test_post_optimizer_deadline_does_not_claim_complete(monkeypatch, tmp_path):
    d = data(); clock = [0.]; original = torch.optim.Adam.step
    def delayed(optimizer, *args, **kwargs):
        value = original(optimizer, *args, **kwargs); clock[0] = 2.; return value
    monkeypatch.setattr(torch.optim.Adam, 'step', delayed)
    monkeypatch.setattr(training.time, 'perf_counter', lambda: clock[0])
    result = train_synthetic_sakt(d, model_config=model_config(d), training_config=train_config(max_seconds=1.))
    assert result.status == 'bounded' and result.stop_reason == 'max_seconds_after_optimizer'
    with pytest.raises(ValueError): save_engineering_weights(tmp_path / 'post-step.pt', result)


def test_final_stage_deadline_cannot_be_checkpointed(monkeypatch, tmp_path):
    d = data(); clock = [0.]; original = training.source_identity; calls = [0]
    def source():
        calls[0] += 1
        if calls[0] == 2: clock[0] = 2.
        return original()
    monkeypatch.setattr(training, 'source_identity', source)
    monkeypatch.setattr(training.time, 'perf_counter', lambda: clock[0])
    result = train_synthetic_sakt(d, model_config=model_config(d), training_config=train_config(max_seconds=1.))
    assert result.status == 'bounded' and result.stop_reason == 'max_seconds_final_stage'
    with pytest.raises(ValueError): save_engineering_weights(tmp_path / 'final-stage.pt', result)


@pytest.mark.parametrize('change', [dict(d_model=65), dict(num_heads=9), dict(head_dim=65), dict(max_length=258)])
def test_huge_geometry_rejected_before_constructor(monkeypatch, change):
    d = data()
    monkeypatch.setattr(training, 'SAKTCore', lambda *a, **k: pytest.fail('no model allocation allowed'))
    with pytest.raises(ValueError, match='geometry'):
        train_synthetic_sakt(d, model_config=model_config(d, **change), training_config=train_config())


def test_explicit_cpu_construction_even_with_meta_default_and_no_cuda_seeding(monkeypatch):
    d = data(); cfg = model_config(d)
    monkeypatch.setattr(torch.cuda, 'manual_seed_all', lambda *a, **k: pytest.fail('no CUDA RNG mutation'))
    with torch.device('meta'):
        result = train_synthetic_sakt(d, model_config=cfg, training_config=train_config())
    assert all(p.device.type == 'cpu' and p.dtype == torch.float32 for p in result.model.parameters())


@pytest.mark.parametrize('kind', ['learner_overlap', 'row_overlap', 'chronology'])
def test_population_invalidity_rejected_before_train(kind):
    train = learner('train', 'AB', [0, 1], 1)
    val = learner('validation', 'AB', [1, 0], 101)
    if kind == 'learner_overlap': val = learner('train', 'AB', [1, 0], 101)
    if kind == 'row_overlap': val = learner('validation', 'AB', [1, 0], 1)
    if kind == 'chronology': train = replace(train, events=tuple(reversed(train.events)))
    with pytest.raises(ValueError):
        prepare_sakt_training_data((train,), (val,), domain='synthetic-negative', recipe=recipe(), synthetic_only=True)


def test_prepared_data_mutation_detected_and_context_zero_policy():
    d = data()
    with pytest.raises(ValueError): replace(d, domain='other').assert_integrity()
    with pytest.raises(ValueError): data(context=0, first_target_policy='unsupported')
    zero = data(context=0, first_target_policy='query_only')
    assert all(x.history_used == 0 for x in zero.train)


@pytest.mark.parametrize('change', [dict(epochs=33), dict(batch_size=33), dict(device='cuda'),
                                    dict(max_steps=33), dict(precision='float64'), dict(lr=float('nan'))])
def test_explicit_optimizer_and_engineering_budget_validation(change):
    with pytest.raises(ValueError): train_config(**change)
