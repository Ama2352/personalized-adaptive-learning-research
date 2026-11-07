"""Common-population order contrast: coverage, ties, learner weighting và no labels."""

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from knowledge_tracing.gam_kt.practice_order import compare_order_controls


BASE = [('A', 'X'), ('B', 'Y')]
CONTROL = [('B', 'X'), ('A', 'Y')]


def events(sequences):
    result = []
    for user, sequence in sequences.items():
        for timestamp, exercise in enumerate(sequence, 1):
            result.append({'user_id': user, 'exercise': exercise, 'time_done': timestamp,
                'source_row': len(result)+1, 'partition': 'development', 'fold': 1})
    return result


def compare(data, base=BASE, control=CONTROL):
    return compare_order_controls(data, base, control, allowed_users={row['user_id'] for row in data},
                                  outer_fold=0)


def test_fixed_denominator_keeps_missing_parents_and_reports_attrition():
    result = compare(events({'u': ['A', 'X'], 'v': ['B', 'X'], 'w': ['C']}))
    assert result['cohort_learners'] == 3 and result['eligible_learners'] == 2
    assert result['excluded_no_incoming_child'] == 1
    assert result['fixed_child_opportunities'] == 2
    assert result['changed_parent_child_opportunities'] == 2
    assert result['all_fixed_opportunities']['base']['observed_prior_fraction'] == .5
    assert result['all_fixed_opportunities']['base']['unobserved_parent_fraction'] == .5
    assert result['all_fixed_opportunities']['paired_control_minus_base']['observed_prior_fraction']['mean'] == 0
    assert result['common_coobserved_opportunities'] is None
    assert result['common_opportunity_retained_fraction'] == 0


def test_learner_is_unit_and_timestamp_ties_not_forced_into_before():
    data = events({'u': ['A', 'X', 'Y', 'B'], 'v': ['B', 'X']})
    data[1]['time_done'] = data[0]['time_done']  # chronology tie broken by source_row only
    result = compare(data)
    base = result['all_fixed_opportunities']['base']
    assert base['timestamp_tie_fraction'] == .25  # .5 for u, 0 for v; not 1/3 pooled-child rate
    assert base['observed_later_fraction'] == .25
    assert base['unobserved_parent_fraction'] == .5
    assert result['common_coobserved_child_opportunities'] == 2
    assert result['common_coobserved_opportunities']['learners'] == 1
    assert sum(base.values()) == 1


def test_identity_control_zero_contrast_including_missingness_and_labels_ignored():
    data = events({'u': ['A','X','B','Y'], 'v': ['C','X']})
    original = deepcopy(data)
    first = compare(data, control=BASE)
    for row in data:
        row['correct'] = object()  # Không cần đọc/serialize correctness.
    assert compare(data, control=BASE) == first
    for changes in first['all_fixed_opportunities']['paired_control_minus_base'].values():
        assert changes['mean'] == 0 and changes['unchanged_learners'] == 2
    assert [{key: value for key, value in row.items() if key != 'correct'} for row in data] == original


def test_swapping_base_and_control_changes_sign_on_same_population():
    data = events({'u':['A','X','B'], 'v':['A','Y']})
    forward = compare(data)
    reverse = compare(data, base=CONTROL, control=BASE)
    for key, value in forward['all_fixed_opportunities']['paired_control_minus_base'].items():
        assert value['mean'] == -reverse['all_fixed_opportunities']['paired_control_minus_base'][key]['mean']


def test_reject_unmatched_degree_outer_scope_and_over_cap():
    data = events({'u':['A','X','B']})
    with pytest.raises(ValueError, match='degree'):
        compare(data, control=[('A','Y')])
    data[0]['fold'] = 0
    with pytest.raises(ValueError, match='scope'):
        compare(data)
    with pytest.raises(ValueError, match='cap'):
        compare_order_controls(events({'u':['A','X']}), BASE, CONTROL,
                               allowed_users={'u'}, outer_fold=0, max_events=1)


@pytest.mark.parametrize('key,value', [('max_learners',257), ('max_learners',True),
    ('max_events_per_learner',301), ('max_seconds',181), ('uses_correct_labels',True), ('outer_fold',1),
    ('scope','outer-fold validation'), ('control_spec',{'seeds':[1,2,3]})])
def test_analysis_entrypoint_preserves_authorized_scope(key, value):
    path = Path(__file__).resolve().parents[2] / 'scripts/research/analyze_order_controls.py'
    spec = importlib.util.spec_from_file_location('order_analysis_fixture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = {'kind':'approved_cpu_junyi_order_pilot', 'outer_fold':0, 'matched_controls':True,
        'uses_correct_labels':False, 'scope':'inner-train learners only', 'max_learners':256,
        'max_events_per_learner':300, 'max_seconds':180, 'control_spec':{'seeds':[0,1,2]}}
    module.validate_scope(manifest)
    manifest[key] = value
    with pytest.raises(ValueError):
        module.validate_scope(manifest)
