"""Arithmetic/join negatives trên tiny fixtures; không model/simulator run."""

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('rq1_transition_analysis', ROOT / 'scripts/research/analyze_rq1_transitions.py')
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def fixed_rows():
    rows = []
    for event in range(4):
        left = {'variant': 'graph_free', 'learner_id': '7-PG', 'event_id': str(event),
                'correct': 0, 'probability': .5, 'mastery': {'A': .9, 'B': .1},
                'mastered': [], 'ready': ['A', 'B'], 'action': 'A'}
        right = {**deepcopy(left), 'variant': 'graph_package'}
        if event in (0, 2):
            right['probability'] = .6
        if event == 1:
            right['mastered'] = ['A', 'B']
            left['ready'] = ['A']
            right['action'] = 'B'
        if event == 2:
            right['action'] = 'B'
        rows.extend((left, right))
    return rows


def events(rows=None):
    return analysis.paired_flags(rows or fixed_rows(), candidates=('graph_package',))[1]


def test_join_uses_cluster_event_identity_not_physical_trace_order():
    assert events() == events(list(reversed(fixed_rows())))


def test_mastery_event_and_concept_units_are_separate_and_use_explicit_decisions():
    summary = analysis.group_summary(events())
    assert summary['event_pairs'] == 4
    assert summary['changed_probability_events'] == 2
    assert summary['changed_mastery_events_any_concept'] == 1
    assert summary['mastery_concept_crossings'] == 2
    assert summary['concept_decision_pairs'] == 8
    # Same .9/.1 scores, explicit native decisions differ; không tự threshold scores.
    assert summary['joint_patterns_PMRA']['0111'] == 1
    # Action có thể đổi khi ready không đổi: không ép stages vào nested funnel.
    assert summary['joint_patterns_PMRA']['1001'] == 1


def test_conditional_counts_have_explicit_event_denominator():
    table = analysis.conditional_table(events(), 'p_changed', 'a_changed')
    row = next(r for r in table if r['first_changed'] and r['second_changed'])
    assert row['count'] == 1 and row['conditional_denominator'] == 2
    assert row['conditional_fraction'] == .5
    assert row['eligible_event_pairs'] == 4 and row['unknown_pairs_excluded'] == 0
    assert sum(r['count'] for r in table) == 4


def test_unknown_prediction_is_not_false_and_does_not_remove_observed_mastery_ready():
    rows = fixed_rows()
    rows[1]['probability'] = None
    paired = events(rows)
    assert paired[0]['p_changed'] is None
    p_table = analysis.conditional_table(paired, 'p_changed', 'a_changed')
    assert p_table[0]['eligible_event_pairs'] == 3 and p_table[0]['unknown_pairs_excluded'] == 1
    assert analysis.conditional_table(paired, 'm_changed', 'r_changed')[0]['eligible_event_pairs'] == 4


def test_identity_negative_control_has_zero_changes_and_undefined_empty_condition():
    rows = fixed_rows()
    for i in range(0, len(rows), 2):
        rows[i + 1] = {**deepcopy(rows[i]), 'variant': 'graph_package'}
    summary = analysis.group_summary(events(rows))
    assert summary['joint_patterns_PMRA']['0000'] == 4
    assert summary['mastery_concept_crossings'] == 0
    conditional = analysis.conditional_table(events(rows), 'p_changed', 'a_changed')
    assert all(r['conditional_fraction'] is None for r in conditional if r['first_changed'])


@pytest.mark.parametrize('case', ['duplicate', 'missing_pair', 'label', 'concept', 'missing_mastered',
                                 'oracle_extra', 'noncanonical_event', 'outside_action', 'duplicate_ready'])
def test_invalid_fixed_trace_contracts(case):
    rows = fixed_rows()
    if case == 'duplicate':
        rows.append(deepcopy(rows[0]))
    elif case == 'missing_pair':
        rows.pop()
    elif case == 'label':
        rows[1]['correct'] = 1
    elif case == 'concept':
        rows[1]['mastery']['C'] = .5
    elif case == 'missing_mastered':
        rows[1]['mastered'] = None
    elif case == 'oracle_extra':
        rows[1]['theta_true'] = 1400
    elif case == 'noncanonical_event':
        rows[1]['event_id'] = '00'
    elif case == 'outside_action':
        rows[1]['action'] = 'C'
    else:
        rows[1]['ready'] = ['A', 'A']
    with pytest.raises(ValueError):
        events(rows)


@pytest.mark.parametrize('value', [-.1, 1.1, float('nan'), float('inf'), True])
def test_invalid_probability_rejected(value):
    rows = fixed_rows()
    rows[1]['probability'] = value
    with pytest.raises(ValueError):
        events(rows)


def closed_fixture():
    rows, outcomes = [], []
    for variant in analysis.VARIANTS:
        actions = []
        for step in range(2):
            concept = 'B' if variant == 'graph_package' and step == 1 else 'A'
            actions.append(concept)
            rows.append({'seed': 7, 'profile': 'PG', 'variant': variant, 'step': step,
                         'concept': concept, 'question': concept + '_1', 'prediction': .5,
                         'timestamp': f't{step}', 'y': 0, 'theta_before': 1200, 'p_true': .8})
        outcomes.append({'seed': 7, 'profile': 'PG', 'variant': variant, 'actions': actions})
    return rows, outcomes, {'seeds': [7], 'steps_per_profile': 2}


def test_closed_loop_only_audits_served_action_identity_and_ignores_oracle():
    rows, outcomes, manifest = closed_fixture()
    result = analysis.analyze_closed(rows, outcomes, manifest)
    assert not result['full_transition_chain_available'] and not result['prediction_contrasts_computed']
    full = result['cluster_rows'][0]
    assert full['actual_concept_action_disagreements'] == 1
    assert full['first_concept_action_divergence_step'] == 1
    assert full['question_identity_disagreements'] == 1
    for r in rows:
        r['theta_before'] = -10000
        r['p_true'] = 999
    assert analysis.analyze_closed(list(reversed(rows)), outcomes, manifest) == result


@pytest.mark.parametrize('case', ['duplicate_step', 'missing_step', 'clock', 'action_aggregate', 'missing_outcome'])
def test_closed_loop_identity_and_source_reconciliation_guards(case):
    rows, outcomes, manifest = closed_fixture()
    if case == 'duplicate_step':
        rows.append(deepcopy(rows[0]))
    elif case == 'missing_step':
        rows.pop()
    elif case == 'clock':
        rows[3]['timestamp'] = 'different'
    elif case == 'action_aggregate':
        outcomes[1]['actions'][0] = 'other'
    else:
        outcomes.pop()
    with pytest.raises(ValueError):
        analysis.analyze_closed(rows, outcomes, manifest)
