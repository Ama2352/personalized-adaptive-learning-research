"""Kiểm controller mới: causal phase, readiness, escape, ties và missing support."""
from copy import deepcopy

import pytest

from knowledge_tracing.reference_controller import (ControllerState, TAU_REFERENCE,
    select_reference_activity, select_from_reference_snapshot)
from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem


def inputs():
    bank = SimulatorBank('synthetic-controller-contract', tuple(
        SimulatorItem(cid + str(i), cid, difficulty)
        for cid in ('A', 'B', 'C') for i, difficulty in enumerate((1050, 1200, 1350))))
    return dict(bank=bank, parents={'A': (), 'B': ('A',), 'C': ()},
                chapters={'A': 'one', 'B': 'one', 'C': 'two'},
                concept_scores={'A': .4, 'B': .1, 'C': .5},
                item_probabilities={item.item_id: {'A': .4, 'B': .1, 'C': .5}[item.concept_id]
                                    for item in bank.items},
                state=ControllerState(), history_sha256='a' * 64,
                reference_history_sha256='a' * 64, calibration_id='b' * 64,
                reference_bank_identity=bank.identity)


def set_score(values, cid, probabilities):
    values['concept_scores'][cid] = sum(probabilities) / 3
    values['item_probabilities'].update({cid + str(i): value for i, value in enumerate(probabilities)})


def test_graph_prevents_low_score_child_before_prerequisite():
    values = inputs()
    before = deepcopy(values)
    result = select_reference_activity(**values)
    assert result.concept_id == 'A'  # B thấp hơn nhưng chưa ready.
    assert result.trace['raw_ready'] == ['A', 'C']
    assert result.trace['served_probability'] is None
    assert result.trace['phase'] == 'preselect_reference'
    assert values == before
    assert dict(result.next_state.concept_counts)['A'] == 1
    assert dict(result.next_state.item_counts)['A0'] == 1


def test_six_exposures_unlock_without_mastery_and_balance_still_applies():
    values = inputs()
    values['state'] = ControllerState((('A', 6),), (('A0', 6),))
    result = select_reference_activity(**values)
    assert not result.trace['mastered']['A']
    assert result.trace['raw_ready'] == ['A', 'B', 'C']
    assert result.trace['balanced'] == ['B', 'C']
    assert result.concept_id == 'B'


def test_threshold_crossing_changes_ready_and_activity():
    values = inputs()
    first = select_reference_activity(**values)
    set_score(values, 'A', (.57, .57, .57))
    second = select_reference_activity(**values)
    assert first.concept_id == 'A' and second.concept_id == 'B'
    assert second.trace['raw_ready'] == ['B', 'C']


def test_probability_change_can_leave_action_identical():
    values = inputs()
    first = select_reference_activity(**values)
    set_score(values, 'A', (.41, .41, .41))
    second = select_reference_activity(**values)
    assert first.item_id == second.item_id
    assert first.trace['trace_sha256'] != second.trace['trace_sha256']


def test_spaced_review_can_leave_raw_ready():
    values = inputs()
    set_score(values, 'B', (.9, .9, .9))
    set_score(values, 'C', (.9, .9, .9))
    values['state'] = ControllerState((('A', 3),), (('A0', 3),), ('A', 'A', 'A'), 'one')
    result = select_reference_activity(**values)
    assert result.trace['raw_ready'] == ['A']
    assert result.trace['escape'] == 'spaced_review_outside_ready'
    assert result.concept_id == 'C'  # B phụ thuộc A chưa mastered/exposed6.
    assert result.concept_id not in result.trace['ready']


def test_all_mastered_review_and_chapter_tie():
    values = inputs()
    for cid in ('A', 'B', 'C'):
        set_score(values, cid, (.8, .8, .8))
    values['state'] = ControllerState(current_chapter='two')
    result = select_reference_activity(**values)
    assert result.trace['raw_ready'] == []
    assert result.trace['ready_reason'] == 'all_mastered_review'
    assert result.concept_id == 'C'


def test_item_targets_success_then_visits_then_id():
    values = inputs()
    set_score(values, 'A', (.1, .7, .7))
    set_score(values, 'C', (.55, .55, .55))
    values['state'] = ControllerState((('A', 1),), (('A1', 1),))
    result = select_reference_activity(**values)
    assert result.concept_id == 'A' and result.item_id == 'A2'


def test_symmetric_item_distances_do_not_override_visit_tie_with_float_noise():
    values = inputs()
    set_score(values, 'A', (.1, .6, .8))
    set_score(values, 'C', (.55, .55, .55))
    values['state'] = ControllerState((('A', 1),), (('A1', 1),))
    result = select_reference_activity(**values)
    assert result.trace['nearest_item_pool'] == ['A1', 'A2']
    assert result.item_id == 'A2'


@pytest.mark.parametrize('change', ['missing_item', 'missing_concept', 'null', 'nan', 'bool',
                                  'wrong_history', 'wrong_bank', 'inconsistent_mean', 'cycle',
                                  'bad_counts', 'unknown_state', 'duplicate_parent',
                                  'recent_without_counts', 'recent_wrong_chapter'])
def test_rejects_unsupported_or_misaligned_inputs(change):
    values = inputs()
    if change == 'missing_item': del values['item_probabilities']['A0']
    elif change == 'missing_concept': del values['concept_scores']['A']
    elif change == 'null': values['item_probabilities']['A0'] = None
    elif change == 'nan': values['concept_scores']['A'] = float('nan')
    elif change == 'bool': values['concept_scores']['A'] = True
    elif change == 'wrong_history': values['reference_history_sha256'] = 'c' * 64
    elif change == 'wrong_bank': values['reference_bank_identity'] = {}
    elif change == 'inconsistent_mean': values['concept_scores']['A'] = .2
    elif change == 'cycle': values['parents']['A'] = ('B',)
    elif change == 'bad_counts': values['state'] = ControllerState((('A', 1),))
    elif change == 'unknown_state': values['state'] = ControllerState(recent_concepts=('X',))
    elif change == 'duplicate_parent': values['parents']['B'] = ('A', 'A')
    elif change == 'recent_without_counts': values['state'] = ControllerState(recent_concepts=('A', 'A', 'A'), current_chapter='one')
    elif change == 'recent_wrong_chapter': values['state'] = ControllerState((('A', 1),), (('A0', 1),), ('A',), 'two')
    with pytest.raises(ValueError):
        select_reference_activity(**values)


def test_bookkeeping_is_consistent_over_repeated_selection():
    values = inputs()
    for _ in range(10):
        result = select_reference_activity(**values)
        values['state'] = result.next_state
    assert sum(dict(result.next_state.concept_counts).values()) == 10
    assert sum(dict(result.next_state.item_counts).values()) == 10
    assert len(result.next_state.recent_concepts) == 3


def test_snapshot_bridge_binds_current_history_and_requires_complete_support():
    bank = SimulatorBank('synthetic-complete-bank', tuple(
        SimulatorItem(f'C{cid:02}-{i}', f'C{cid:02}', difficulty)
        for cid in range(28) for i, difficulty in enumerate((1050, 1200, 1350))))
    concepts = sorted({item.concept_id for item in bank.items})
    snapshot = dict(recipe='response-temperature-reference-v1', tau_ref=TAU_REFERENCE,
        total_concepts=28, supported_concepts=28, history_sha256='a'*64,
        reference_history_sha256='a'*64, bank_identity=bank.identity,
        calibration_sha256='b'*64, concepts={cid: {'score': .4} for cid in concepts},
        item_calibrated_probabilities={item.item_id: .4 for item in bank.items})
    kwargs = dict(bank=bank, parents={cid: () for cid in concepts},
        chapters={cid: 'one' for cid in concepts}, state=ControllerState(),
        history_sha256='a'*64, reference_snapshot=snapshot)
    assert select_from_reference_snapshot(**kwargs).item_id == 'C00-0'
    for field, value in [('history_sha256', 'c'*64), ('supported_concepts', 27),
                         ('calibration_sha256', 'not-a-hash')]:
        original = snapshot[field]
        snapshot[field] = value
        with pytest.raises(ValueError):
            select_from_reference_snapshot(**kwargs)
        snapshot[field] = original
