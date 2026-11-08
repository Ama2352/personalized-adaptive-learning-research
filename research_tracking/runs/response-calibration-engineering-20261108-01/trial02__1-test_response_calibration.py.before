"""Kiểm scalar/reference V1 bằng observed responses tổng hợp; không train NN."""
from dataclasses import replace
import json
import math

import pytest

from knowledge_tracing.response_calibration import (CalibrationPartition, CalibrationTarget,
    PredictionBinding, TemperatureCalibration, TAU_REF, calibrate_probability, fit_temperature,
    reference_bank_v1, reference_identity, score_reference_bank)
from knowledge_tracing.simulator_bridge import (SimulatorItem, SimulatorBank, OnlineSession,
    OnlineScore, identity_hash)

H = 'a' * 64


def fixture():
    bank = SimulatorBank('synthetic-observed-response-validation', tuple(
        SimulatorItem(f'C{c}-d{d}', f'C{c}', d) for c in range(28) for d in (1050, 1200, 1350)))
    refs = reference_bank_v1(bank)
    binding = PredictionBinding('frozen-model-sha', H, H, H, bank.identity['item_bank_sha256'],
                                reference_identity(refs), H, identity_hash(bank.identity))
    partition = CalibrationPartition(H, ('cal-a', 'cal-b'), ('fit', 'selection', 'final'),
        (('cal-a', 'family-cal-a'), ('cal-b', 'family-cal-b'), ('fit', 'family-fit'),
         ('selection', 'family-selection'), ('final', 'family-final')))
    # Tần suất response quan sát0.6, trong khi raw p=0.9.
    rows = tuple(CalibrationTarget('cal-a' if i < 10 else 'cal-b', str(i), 'known-item', H,
        1 if i % 10 < 6 else 0, .9, 'supported') for i in range(20))
    return bank, binding, partition, rows


def fit(rows=None, *, max_evaluations=200):
    bank, binding, partition, default = fixture()
    rows = default if rows is None else rows
    keys = tuple((r.learner_id, r.event_id, r.item_id, r.history_sha256) for r in rows)
    return fit_temperature(rows, binding=binding, partition=partition, expected_target_keys=keys,
                           max_evaluations=max_evaluations), binding, bank


def test_interior_optimum_matches_analytic_bernoulli_control():
    result, binding, _ = fit()
    # Bernoulli maximum-likelihood p equals6/10; not a copy of numerical solver.
    expected_t = math.log(9) / math.log(.6 / .4)
    assert result.temperature == pytest.approx(expected_t, rel=1e-6)
    assert calibrate_probability(.9, calibration=result, binding=binding) == pytest.approx(.6, abs=1e-8)
    assert result.calibrated_log_loss == pytest.approx(-.6*math.log(.6)-.4*math.log(.4), abs=1e-12)
    assert result.objective_evaluations <= 200
    assert result.total_targets == result.supported_targets == 20
    assert result.class_counts == (8, 12)


@pytest.mark.parametrize('probability,expected', [(1., 20.), (0., 20.)])
def test_clip_and_finite_boundary_fit(probability, expected):
    _, _, _, rows = fixture()
    rows = tuple(replace(r, probability=probability, correct=i % 2) for i, r in enumerate(rows))
    result, binding, _ = fit(rows)
    assert result.temperature == expected
    for p in (0., 1.): assert 0 < calibrate_probability(p, calibration=result, binding=binding) < 1


def test_low_temperature_boundary_and_no_favorable_loss_requirement():
    _, _, _, rows = fixture()
    rows = tuple(replace(r, correct=i % 2, probability=.9 if i % 2 else .1) for i, r in enumerate(rows))
    result, _, _ = fit(rows)
    assert result.temperature == .05


@pytest.mark.parametrize('limit', [4, 5, 16, 200])
def test_explicit_objective_budget_includes_raw_and_endpoints(limit):
    result, _, _ = fit(max_evaluations=limit)
    assert 3 <= result.objective_evaluations <= limit
    assert .05 <= result.temperature <= 20


@pytest.mark.parametrize('bad', [0, 3, 201, True])
def test_invalid_objective_budget(bad):
    with pytest.raises(ValueError, match='budget'): fit(max_evaluations=bad)


def test_unsupported_predictions_keep_full_denominator():
    _, _, _, rows = fixture()
    rows = (replace(rows[0], probability=None, support_reason='unseen_item'), *rows[1:])
    result, _, _ = fit(rows)
    assert result.total_targets == 20 and result.supported_targets == 19
    assert result.unsupported_counts == (('unseen_item', 1),)


@pytest.mark.parametrize('kind', ['missing_all', 'one_class'])
def test_no_calibrated_evaluation_when_support_insufficient(kind):
    _, _, _, rows = fixture()
    rows = tuple(replace(r, probability=None, support_reason='unsupported_history') if kind == 'missing_all'
                 else replace(r, correct=1) for r in rows)
    result, binding, _ = fit(rows)
    assert result.temperature is None and result.objective_evaluations == 0
    assert result.status == ('unsupported_no_predictions' if kind == 'missing_all' else 'unsupported_two_class_labels_required')
    with pytest.raises(ValueError, match='unsupported'): calibrate_probability(.5, calibration=result, binding=binding)
    assert TemperatureCalibration.from_payload(json.loads(json.dumps(result.to_payload())), binding=binding) == result


@pytest.mark.parametrize('p', [math.nan, math.inf, -.1, 1.1, True])
def test_nonfinite_and_invalid_probabilities_are_errors_not_missing_support(p):
    with pytest.raises(ValueError, match='finite probability'): CalibrationTarget('a', 'event', 'item', H, 0, p, 'supported')


@pytest.mark.parametrize('role', ['train', 'selection', 'final'])
def test_labels_from_other_roles_rejected(role):
    with pytest.raises(ValueError, match='calibration labels'): CalibrationTarget('a', 'event', 'item', H, 0, .5, 'supported', role)


def test_seed_families_and_learners_both_disjoint():
    with pytest.raises(ValueError, match='learner separation'): CalibrationPartition(H, ('a',), ('a',), None)
    with pytest.raises(ValueError, match='seed-family leakage'):
        CalibrationPartition(H, ('a',), ('b',), (('a', 'same'), ('b', 'same')))
    with pytest.raises(ValueError, match='complete seed-family'):
        CalibrationPartition(H, ('a',), ('b',), (('a', 'family'),))


def test_expected_target_join_detects_missing_extra_query_history_and_wrong_learner():
    _, binding, partition, rows = fixture()
    keys = tuple((r.learner_id, r.event_id, r.item_id, r.history_sha256) for r in rows)
    for changed in (rows[:-1], (*rows, rows[0]), (replace(rows[0], item_id='other'), *rows[1:]),
                    (replace(rows[0], history_sha256='b'*64), *rows[1:]),
                    (replace(rows[0], learner_id='final'), *rows[1:])):
        with pytest.raises(ValueError, match='population'):
            fit_temperature(changed, binding=binding, partition=partition, expected_target_keys=keys)


@pytest.mark.parametrize('field', list(PredictionBinding.__dataclass_fields__))
def test_every_binding_field_is_checked(field):
    result, binding, _ = fit()
    changed = replace(binding, **{field: 'other' if field == 'model_id' else 'b'*64})
    with pytest.raises(ValueError, match='binding mismatch'): calibrate_probability(.5, calibration=result, binding=changed)


def test_json_roundtrip_source_drift_and_extra_fields():
    result, binding, _ = fit()
    payload = json.loads(json.dumps(result.to_payload()))
    assert TemperatureCalibration.from_payload(payload, binding=binding) == result
    with pytest.raises(ValueError, match='schema'): TemperatureCalibration.from_payload({**payload, 'theta': 1250}, binding=binding)
    with pytest.raises(ValueError, match='source drift'):
        TemperatureCalibration.from_payload({**payload, 'implementation_sha256': 'b'*64}, binding=binding)


def session_for(bank, binding, *, missing=False):
    class Backend:
        domain = bank.identity
        model_id = binding.model_id
        def predict_next(self, history, query, *, learner_id):
            if missing and query.item_id == 'C0-d1050':
                return OnlineScore(None, 'unseen_item', len(history), 0, False, len(history))
            return OnlineScore(.9, 'fitted', len(history), len(history), False, len(history))
    return OnlineSession(Backend(), bank, learner_id='probe-learner', max_events=30)


def test_reference_actual_ids_full_bank_equal_weights_and_threshold():
    result, binding, bank = fit()
    session = session_for(bank, binding)
    before = session.snapshot()
    score = score_reference_bank(session, calibration=result, binding=binding, timestamp=0, source_row=1)
    assert session.snapshot() == before
    assert score['supported_concepts'] == score['total_concepts'] == 28
    assert len(score['item_calibrated_probabilities']) == 84
    assert score['history_sha256'] == score['reference_history_sha256'] == session.history_sha256
    assert score['bank_identity'] == bank.identity
    assert TAU_REF == pytest.approx(.5637150147511514, abs=1e-15)
    assert all(r['score'] == pytest.approx(.6) and r['reference_criterion'] for r in score['concepts'].values())
    assert all('mastery_probability' not in r for r in score['concepts'].values())


def test_missing_reference_null_concept_no_renormalization():
    result, binding, bank = fit()
    session = session_for(bank, binding, missing=True)
    score = score_reference_bank(session, calibration=result, binding=binding, timestamp=0, source_row=1)
    assert score['supported_concepts'] == 27
    c = score['concepts']['C0']
    assert c['score'] is None and c['reference_criterion'] is None and c['supported_items'] == 2
    assert c['missing_items'] == ('C0-d1050',)
    assert score['item_calibrated_probabilities']['C0-d1050'] is None


def test_reference_bank_requires_actual_three_items_no_synthetic1250():
    _, _, bank = fit()
    with pytest.raises(ValueError, match='28concepts'): reference_bank_v1(replace(bank, items=bank.items[:-1]))
    first = replace(bank.items[0], difficulty=1250)
    with pytest.raises(ValueError, match='28concepts'): reference_bank_v1(replace(bank, items=(first, *bank.items[1:])))


def test_probe_model_identity_rejected_before_predictions():
    result, binding, bank = fit()
    session = session_for(bank, binding)
    session.backend.model_id = 'changed'
    with pytest.raises(ValueError, match='binding mismatch'):
        score_reference_bank(session, calibration=result, binding=binding, timestamp=0, source_row=1)


def test_calibration_probe_controller_served_prediction_observe_integration():
    from knowledge_tracing.reference_controller import ControllerState, select_from_reference_snapshot
    from knowledge_tracing.simulator_bridge import ItemQuery
    result, binding, bank = fit()
    session = session_for(bank, binding)
    before = session.snapshot()
    refs = score_reference_bank(session, calibration=result, binding=binding, timestamp=0, source_row=1)
    concepts = {item.concept_id for item in bank.items}
    args = dict(bank=bank, parents={c: () for c in concepts}, chapters={c: 'chapter' for c in concepts})
    decision = select_from_reference_snapshot(**args, state=ControllerState(),
        history_sha256=session.history_sha256, reference_snapshot=refs)
    assert session.snapshot() == before
    assert decision.trace['served_probability'] is None
    assert decision.item_id in bank.item_ids
    # Reference snapshot không thay thế served-item ticket; raw served p có phase riêng.
    ticket = session.predict(ItemQuery(decision.item_id, 0, 1))
    assert ticket.query.item_id == decision.item_id and ticket.score.probability == .9
    assert calibrate_probability(ticket.score.probability, calibration=result, binding=binding) == pytest.approx(.6)
    assert session.snapshot() == before
    session.observe(ticket, 1)
    assert len(session.history) == 1 and session.history_sha256 != refs['history_sha256']
    assert dict(decision.next_state.item_counts)[decision.item_id] == 1
    with pytest.raises(ValueError, match='stale reference'):
        select_from_reference_snapshot(**args, state=decision.next_state,
            history_sha256=session.history_sha256, reference_snapshot=refs)
