from dataclasses import replace

import pytest

from knowledge_tracing.diagnostics import DecisionTrace, compare_decision_traces


def trace():
    return DecisionTrace('event1', 'learner1', 1, .6, {'A': .7, 'B': .2}, frozenset({'A'}), 'A')


def test_better_prediction_can_leave_all_decisions_unchanged():
    a = trace()
    result = compare_decision_traces([a], [replace(a, probability=.9)], threshold=.8)
    assert result['candidate_minus_reference_log_loss'] < 0
    assert result['candidate_minus_reference_brier'] < 0
    assert result['changed_probability_rows'] == 1
    assert result['mastery_crossings'] == result['changed_actions'] == 0


def test_trace_detects_mastery_ready_and_action_changes():
    a = trace()
    b = replace(a, mastery={'A': .9, 'B': .2}, ready=frozenset({'B'}), action='B')
    result = compare_decision_traces([a], [b], threshold=.8)
    assert result['concept_decisions'] == 2
    assert result['mastery_crossings'] == result['changed_ready_sets'] == result['changed_actions'] == 1
    assert result['mean_ready_jaccard'] == 0


def test_unsupported_prediction_is_excluded_but_decisions_still_counted():
    a = trace()
    result = compare_decision_traces([a], [replace(a, probability=None)], threshold=.8)
    assert result['paired_events'] == result['unsupported_probability_pairs'] == 1
    assert result['candidate_minus_reference_log_loss'] is None
    assert result['concept_decisions'] == 2


@pytest.mark.parametrize('change', [dict(event_id='other'), dict(correct=0),
                                   dict(probability=float('nan')), dict(action='C')])
def test_invalid_or_unmatched_trace_is_rejected(change):
    a = trace()
    with pytest.raises(ValueError):
        compare_decision_traces([a], [replace(a, **change)], threshold=.8)


def test_duplicates_and_missing_pairs_are_rejected():
    a = trace()
    for left, right in (([a,a],[a,a]), ([a],[])):
        with pytest.raises(ValueError):
            compare_decision_traces(left, right, threshold=.8)


def test_equal_empty_ready_sets_and_zero_one_probabilities_are_valid():
    a = replace(trace(), ready=frozenset(), action=None, probability=0.)
    b = replace(a, probability=1.)
    result = compare_decision_traces([a], [b], threshold=.8)
    assert result['mean_ready_jaccard'] == 1
    assert result['candidate_minus_reference_log_loss'] < 0
