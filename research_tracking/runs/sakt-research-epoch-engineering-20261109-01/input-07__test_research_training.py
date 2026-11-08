"""Tiny CPU numerical fixtures, không corpus thật/lifecycle research fit.

Compute inventory đề xuất cho ROOT:16SAKT constructors,11forwards,5backwards,
5SGD.step bodies,15SGD constructors; một wrapper raise SAU actual update. Không Adam,
checkpoint/teacher/GPU/OnlineSession. Đây là inventory từ source, chưa actual.
"""
from dataclasses import replace
from itertools import islice
import math
from types import SimpleNamespace

import pytest
import torch

from knowledge_tracing.sakt import SAKTConfig, SAKTCore
from knowledge_tracing.sakt import research_data as rd
from knowledge_tracing.sakt import research_training as rt
from .test_research_data import corpus, changed_role, freeze  # Handmade typed fixtures only.


def spec(*, batch_size=32, order='in_order'):
    return rt.SAKTResearchSpec(batch_size, 10., 42, order, 'cpu', 'float32', 'mean_bce_on_eligible_targets')


def budget(*, seen=32, processed=32, steps=32):
    return rt.SAKTResearchBudget(30., seen, processed, steps)


def view(corpus, scope='select_train80', **kwargs):
    return rd.prepare_sakt_research_view(corpus, scope=scope,
        recipe=rd.SAKTDataRecipe(2, 'left', 'query_only', 'sliding_last_context',
                                'window_relative_interaction_rank'), **kwargs)


def model(prepared, *, zero=True):
    with torch.random.fork_rng(devices=[]), torch.device('cpu'):
        torch.random.default_generator.manual_seed(13)
        value = SAKTCore(SAKTConfig(len(prepared.vocabulary.values), 3, 4, 1, 4, 0., 1e-5))
        value.to(device='cpu', dtype=torch.float32)
        if zero:
            with torch.no_grad():
                for parameter in value.parameters():
                    parameter.zero_()
    return value


def all_zero_labels(corpus):
    return changed_role(corpus, 'train', lambda trajectories: tuple(
        replace(t, observations=tuple(replace(o, correct=0) for o in t.observations)) for t in trajectories))


@pytest.mark.parametrize('change', [dict(batch_size=True), dict(max_grad_norm=float('nan')),
    dict(epoch_seed=-1), dict(device='cuda'), dict(precision='float64'), dict(objective='another_objective')])
def test_specs_and_budgets_have_no_implicit_invalid_profile(change):
    values = dict(batch_size=32, max_grad_norm=10., epoch_seed=42, order='in_order',
                  device='cpu', precision='float32', objective='mean_bce_on_eligible_targets')
    values.update(change)
    with pytest.raises(ValueError):
        rt.SAKTResearchSpec(**values)
    for bad in (dict(max_seconds=float('nan')), dict(max_seen_targets=True), dict(max_optimizer_steps=-1)):
        values = dict(max_seconds=30., max_seen_targets=32, max_processed_targets=32, max_optimizer_steps=32)
        values.update(bad)
        with pytest.raises(ValueError):
            rt.SAKTResearchBudget(**values)


def test_optimizer_foreign_missing_duplicate_and_wrong_geometry_rejected_before_forward(corpus):
    prepared = view(corpus)
    native = model(prepared)
    parameters = list(native.parameters())
    missing = torch.optim.SGD(parameters[:-1], lr=.2)
    duplicate = torch.optim.SGD(parameters, lr=.2)
    duplicate.param_groups[0]['params'].append(parameters[0])
    foreign = torch.optim.SGD(parameters, lr=.2)
    foreign.param_groups[0]['params'][-1] = torch.nn.Parameter(torch.zeros(1, device='cpu'))
    for optimizer in (missing, duplicate, foreign, None):
        with pytest.raises(ValueError, match='optimizer'):
            rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec(), budget=budget())
    with torch.inference_mode(), pytest.raises(ValueError, match='inference_mode'):
        rt.train_research_epoch(native, prepared, optimizer=torch.optim.SGD(native.parameters(), lr=.2),
            spec=spec(), budget=budget())
    native.config = replace(native.config, num_items=native.config.num_items+1)
    with pytest.raises(ValueError, match='binding mismatch'):
        rt.predict_research_sakt(native, prepared, spec=spec(), budget=budget(steps=0))


@pytest.mark.parametrize('scope', ['raw_selection10', 'calibration_predict'])
def test_prediction_roles_cannot_optimize(corpus, scope):
    train = view(corpus)
    if scope == 'raw_selection10':
        prepared = view(corpus, scope, encoding=train.encoding)
    else:
        selected = freeze(corpus)
        refit = view(corpus, 'refit_union90', selection_freeze=selected)
        prepared = view(corpus, scope, encoding=refit.encoding, selection_freeze=selected)
    native = model(prepared)
    optimizer = torch.optim.SGD(native.parameters(), lr=.2)
    with pytest.raises(ValueError, match='prediction-only'):
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec(), budget=budget())


def test_complete_epoch_matches_constant_logit_gradient_and_raw_prediction(corpus):
    prepared = view(all_zero_labels(corpus))
    native = model(prepared)
    optimizer = torch.optim.SGD(native.parameters(), lr=.2)
    before_rng = torch.random.get_rng_state().clone()
    def training_mode(module, inputs):
        assert module.training and torch.is_grad_enabled() and not torch.is_inference_mode_enabled()
    handle = native.register_forward_pre_hook(training_mode)
    with torch.no_grad():
        result = rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec(), budget=budget(steps=1))
        assert not torch.is_grad_enabled()
    handle.remove()
    assert torch.equal(before_rng, torch.random.get_rng_state())
    assert result['status'] == 'complete' and result['ledger']['complete']
    assert result['ledger']['expected_targets'] == result['ledger']['seen_targets'] == 32
    assert result['ledger']['optimized_targets'] == result['ledger']['processed_targets'] == 32
    assert result['ledger']['scored_targets'] == result['ledger']['unsupported_targets_seen'] == 0
    assert result['ledger']['optimizer_steps_started'] == result['ledger']['optimizer_steps_body_returned'] == 1
    assert result['mean_loss'] == pytest.approx(math.log(2), abs=1e-6)
    # All weights zero => logit0, y0 => bias gradient0.5, SGD0.2 => bias-0.1.
    assert native.prediction.bias.item() == pytest.approx(-.1, abs=1e-7)
    assert result['weights_changed'] and not result['fitted_research_model']
    predicted = rt.predict_research_sakt(native, prepared, spec=spec(), budget=budget(steps=0))
    assert predicted['status'] == 'complete' and predicted['ledger']['complete']
    assert predicted['ledger']['scored_targets'] == len(predicted['predictions']) == len(predicted['truth_sidecar']) == 32
    assert not predicted['weights_changed'] and predicted['model_state_before'] == predicted['model_state_after']
    for row in predicted['predictions']:
        assert row['probability'] == pytest.approx(1/(1+math.exp(.1)), abs=1e-7)
        assert 'correct' not in row and row['prediction_status'] == 'scored'
    assert all(target.correct == 0 for target in predicted['truth_sidecar'])


def test_seen_budget_stops_before_any_forward_without_full_denominator_claim(corpus):
    prepared = view(corpus)
    native = model(prepared)
    optimizer = torch.optim.SGD(native.parameters(), lr=.2)
    result = rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec(), budget=budget(seen=1))
    assert result['status'] == 'bounded' and not result['ledger']['complete']
    assert result['ledger']['seen_targets'] == 1 and result['ledger']['unseen_targets'] == 31
    assert result['ledger']['expected_eligible_targets'] is None
    assert result['ledger']['optimizer_steps_started'] == result['ledger']['processed_targets'] == 0
    assert not result['weights_changed']
    excluded = rd.prepare_sakt_research_view(corpus, scope='select_train80',
        recipe=rd.SAKTDataRecipe(0, 'left', 'unsupported', 'sliding_last_context',
                                'window_relative_interaction_rank'))
    with pytest.raises(rt.SAKTResearchExecutionError, match='no eligible') as caught:
        rt.train_research_epoch(native, excluded, optimizer=optimizer, spec=spec(), budget=budget())
    assert caught.value.result['ledger']['seen_targets'] == caught.value.result['ledger']['unsupported_targets_seen'] == 32
    assert caught.value.result['ledger']['expected_eligible_targets'] == 0
    assert caught.value.result['ledger']['optimizer_steps_started'] == 0


def test_step_budget_keeps_real_partial_update_and_unique_processed_targets(corpus):
    prepared = view(all_zero_labels(corpus))
    native = model(prepared)
    optimizer = torch.optim.SGD(native.parameters(), lr=.2)
    result = rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec(batch_size=16), budget=budget(steps=1))
    ledger = result['ledger']
    assert result['status'] == 'bounded' and result['stop_reason'] == 'max_optimizer_steps'
    assert ledger['seen_targets'] == ledger['expected_eligible_targets'] == 32
    assert ledger['optimized_targets'] == ledger['processed_targets'] == 16
    assert len(set(ledger['processed_source_rows'])) == 16
    assert ledger['unprocessed_seen_eligible_targets'] == 16 and not ledger['complete']
    assert ledger['optimizer_steps_started'] == ledger['optimizer_steps_body_returned'] == 1
    assert result['weights_changed'] and ledger['rollback'] is False


def test_truncated_generator_is_failure_not_complete_or_favorable_subset(corpus, monkeypatch):
    prepared = view(corpus)
    native = model(prepared)
    optimizer = torch.optim.SGD(native.parameters(), lr=.2)
    original = rt.iter_sakt_research_inputs

    def short(*args, **kwargs):
        stream = original(*args, **kwargs)
        try:
            yield from islice(stream, 3)
        finally:
            stream.close()

    monkeypatch.setattr(rt, 'iter_sakt_research_inputs', short)
    with pytest.raises(rt.SAKTResearchExecutionError, match='ended before full') as caught:
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec(), budget=budget())
    assert caught.value.result['status'] == 'failed'
    assert caught.value.result['ledger']['seen_targets'] == 3
    assert not caught.value.result['ledger']['complete'] and not caught.value.result['weights_changed']
    assert caught.value.result['ledger']['optimizer_steps_started'] == 0


def test_predictions_are_causal_peer_independent_and_restore_mixed_modes(corpus):
    prepared = view(corpus)
    native = model(prepared, zero=False)
    native.train()
    native.dropout.eval()
    modes = [module.training for module in native.modules()]
    before_rng = torch.random.get_rng_state().clone()
    def inference_mode(module, inputs):
        assert not module.training and torch.is_inference_mode_enabled() and not torch.is_grad_enabled()
    handle = native.register_forward_pre_hook(inference_mode)
    before = rt.predict_research_sakt(native, prepared, spec=spec(), budget=budget(steps=0))

    def perturb(trajectories):
        first = trajectories[0]
        observations = list(first.observations)
        for rank in (2, 3):
            observations[rank] = replace(observations[rank], correct=1-observations[rank].correct)
        return (replace(first, observations=tuple(observations)), *trajectories[1:])

    altered = view(changed_role(corpus, 'train', perturb))
    after = rt.predict_research_sakt(native, altered, spec=spec(), budget=budget(steps=0))
    handle.remove()
    assert [module.training for module in native.modules()] == modes
    assert torch.equal(before_rng, torch.random.get_rng_state())
    a, b = before['predictions'], after['predictions']
    assert [row['probability'] for row in a[:3]] == [row['probability'] for row in b[:3]]
    assert [row['history_sha256'] for row in a[:3]] == [row['history_sha256'] for row in b[:3]]
    assert abs(a[3]['probability']-b[3]['probability']) > 1e-7  # Positive response-dependence control.
    assert [row['probability'] for row in a[4:]] == [row['probability'] for row in b[4:]]
    assert before['truth_sidecar'][2].correct != after['truth_sidecar'][2].correct
    assert before['model_state_before'] == before['model_state_after'] == after['model_state_after']


def test_partial_prediction_and_all_unsupported_population_keep_distinct_null_reasons(corpus):
    train = view(corpus)
    prepared = view(corpus, 'raw_selection10', encoding=train.encoding)
    native = model(prepared)
    result = rt.predict_research_sakt(native, prepared, spec=spec(batch_size=1), budget=budget(processed=1, steps=0))
    assert result['status'] == 'bounded' and not result['ledger']['complete']
    assert result['ledger']['seen_targets'] == len(result['predictions']) == len(result['truth_sidecar']) == 5
    assert result['ledger']['eligible_targets_seen'] == 3 and result['ledger']['unsupported_targets_seen'] == 2
    assert result['ledger']['scored_targets'] == 1 and result['ledger']['optimized_targets'] == 0
    statuses = [row['prediction_status'] for row in result['predictions']]
    assert statuses.count('scored') == 1 and statuses.count('unsupported') == statuses.count('unprocessed') == 2
    altered = changed_role(corpus, 'selection', lambda trajectories: tuple(replace(t,
        observations=tuple(replace(o, query=replace(o.query, item_id=corpus.bank.item_ids[3]))
                           for o in t.observations)) for t in trajectories))
    unsupported = view(altered, 'raw_selection10', encoding=train.encoding)
    result = rt.predict_research_sakt(native, unsupported, spec=spec(), budget=budget(steps=0))
    assert result['status'] == 'complete' and result['ledger']['complete']
    assert result['ledger']['expected_eligible_targets'] == result['ledger']['scored_targets'] == 0
    assert len(result['predictions']) == 5 and all(row['probability'] is None for row in result['predictions'])
    assert all(row['prediction_status'] == 'unsupported' for row in result['predictions'])


def test_late_optimizer_completion_cannot_be_accepted_by_resetting_time(corpus, monkeypatch):
    prepared = view(all_zero_labels(corpus))
    native = model(prepared)
    optimizer = torch.optim.SGD(native.parameters(), lr=.2)
    clock = [0.]
    # Patch only module binding, never global time/perf_counter used by pytest/outer.
    monkeypatch.setattr(rt, 'time', SimpleNamespace(perf_counter=lambda: clock[0]))
    step = optimizer.step

    def late():
        result = step()
        clock[0] = 31.
        return result

    monkeypatch.setattr(optimizer, 'step', late)
    result = rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec(), budget=budget(steps=1))
    assert result['status'] == 'bounded' and not result['ledger']['complete']
    assert result['ledger']['optimized_targets'] == 32 and result['weights_changed']
    assert result['ledger']['optimizer_steps_body_returned'] == 1


def test_optimizer_identity_drift_after_step_fails_with_actual_returned_work(corpus, monkeypatch):
    prepared = view(all_zero_labels(corpus))
    native = model(prepared)
    optimizer = torch.optim.SGD(native.parameters(), lr=.2)
    step = optimizer.step

    def changed():
        result = step()
        optimizer.param_groups[0]['lr'] = .9
        return result

    monkeypatch.setattr(optimizer, 'step', changed)
    with pytest.raises(rt.SAKTResearchExecutionError, match='identity changed') as caught:
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec(), budget=budget(steps=1))
    result = caught.value.result
    assert result['status'] == 'failed' and not result['ledger']['complete']
    assert result['ledger']['optimizer_steps_started'] == result['ledger']['optimizer_steps_body_returned'] == 1
    assert result['ledger']['optimized_targets'] == 32 and result['weights_changed']


def test_optimizer_exception_after_update_retains_uncertain_batch_not_fake_rollback(corpus, monkeypatch):
    prepared = view(all_zero_labels(corpus))
    native = model(prepared)
    optimizer = torch.optim.SGD(native.parameters(), lr=.2)
    step = optimizer.step

    def failed():
        step()
        raise RuntimeError('synthetic step wrapper failed after mutation')

    monkeypatch.setattr(optimizer, 'step', failed)
    with pytest.raises(rt.SAKTResearchExecutionError, match='failed after mutation') as caught:
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec(), budget=budget(steps=1))
    result = caught.value.result
    assert result['status'] == 'failed' and not result['ledger']['complete'] and result['weights_changed']
    assert result['ledger']['optimizer_steps_started'] == 1 and result['ledger']['optimizer_steps_body_returned'] == 0
    assert result['ledger']['optimized_targets'] == result['ledger']['processed_targets'] == 0
    assert len(result['ledger']['possibly_updated_source_rows']) == 32 and result['ledger']['rollback'] is False


def test_seeded_order_reproducible_without_update_and_without_changing_global_rng(corpus):
    prepared = view(corpus)
    native = model(prepared)
    optimizer = torch.optim.SGD(native.parameters(), lr=.2)
    before = torch.random.get_rng_state().clone()
    first = rt.train_research_epoch(native, prepared, optimizer=optimizer,
        spec=spec(order='seeded_permutation'), budget=budget(steps=0))
    second = rt.train_research_epoch(native, prepared, optimizer=optimizer,
        spec=spec(order='seeded_permutation'), budget=budget(steps=0))
    assert first['status'] == second['status'] == 'bounded'
    order = first['ledger']['processing_order_source_rows']
    assert order == second['ledger']['processing_order_source_rows']
    assert sorted(order) == sorted(first['ledger']['seen_source_rows']) and order != first['ledger']['seen_source_rows']
    assert torch.equal(before, torch.random.get_rng_state())
    assert first['ledger']['optimizer_steps_started'] == second['ledger']['optimizer_steps_started'] == 0


def test_finite_extreme_logits_with_overflowing_sum_fail_before_backward_or_step(corpus, monkeypatch):
    prepared = view(all_zero_labels(corpus))
    native = model(prepared)
    with torch.no_grad():
        native.prediction.bias.fill_(3e38)  # Finite FP32 logits, but32 summed losses overflow.
    optimizer = torch.optim.SGD(native.parameters(), lr=.2)
    calls = dict(backward=0, step=0)

    def forbidden_backward(*args, **kwargs):
        calls['backward'] += 1
        pytest.fail('nonfinite objective must stop before backward')

    def forbidden_step(*args, **kwargs):
        calls['step'] += 1
        pytest.fail('nonfinite objective must stop before optimizer')

    monkeypatch.setattr(torch.Tensor, 'backward', forbidden_backward)
    monkeypatch.setattr(optimizer, 'step', forbidden_step)
    with pytest.raises(rt.SAKTResearchExecutionError, match='nonfinite batch or aggregated objective') as caught:
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec(), budget=budget(steps=1))
    result = caught.value.result
    assert calls == dict(backward=0, step=0)
    assert result['status'] == 'failed' and not result['ledger']['complete']
    assert result['ledger']['optimizer_steps_started'] == result['ledger']['optimized_targets'] == 0
    assert result['loss_sum'] == 0 and result['mean_loss'] is None and not result['weights_changed']


def test_same_count_foreign_iterator_key_fails_before_prediction(corpus, monkeypatch):
    prepared = view(corpus)
    native = model(prepared)
    original = rt.iter_sakt_research_inputs

    def altered(*args, **kwargs):
        for index, record in enumerate(original(*args, **kwargs)):
            if index == 0:
                record = replace(record, query=replace(record.query, source_row=999999999))
            yield record

    monkeypatch.setattr(rt, 'iter_sakt_research_inputs', altered)
    with pytest.raises(rt.SAKTResearchExecutionError, match='differs from observable population') as caught:
        rt.predict_research_sakt(native, prepared, spec=spec(), budget=budget(steps=0))
    assert caught.value.result['status'] == 'failed' and not caught.value.result['ledger']['complete']
    assert caught.value.result['ledger']['scored_targets'] == 0 and not caught.value.result['weights_changed']


def test_same_count_wrong_truth_key_rejected_after_prediction_not_false_complete(corpus, monkeypatch):
    train = view(corpus)
    prepared = view(corpus, 'raw_selection10', encoding=train.encoding)
    native = model(prepared)
    original = rt.sakt_research_scoring_targets

    def altered(prepared):
        rows = original(prepared)
        return (replace(rows[0], query=replace(rows[0].query, source_row=999999999)), *rows[1:])

    monkeypatch.setattr(rt, 'sakt_research_scoring_targets', altered)
    with pytest.raises(rt.SAKTResearchExecutionError, match='truth sidecar exact population keyset') as caught:
        rt.predict_research_sakt(native, prepared, spec=spec(), budget=budget(steps=0))
    result = caught.value.result
    assert result['status'] == 'failed' and not result['ledger']['complete']
    assert result['ledger']['scored_targets'] == 3 and not result['weights_changed']
    assert not result['truth_sidecar_complete']
