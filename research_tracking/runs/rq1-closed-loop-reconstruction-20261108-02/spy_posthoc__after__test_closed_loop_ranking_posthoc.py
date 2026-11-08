"""Pure known answers for local key replay; no actual scores/model data."""
import pytest
from analyze_closed_loop_ranking_posthoc import analyze, replay_key
from test_closed_loop_descriptive import row, serve
from collections import Counter


CHAPTERS = {'a': 'Chapter A', 'b': 'Chapter B'}


def population():
    rows = []
    for variant in ('graph_free', 'graph_package', 'empty_graph_package'):
        for step in range(2):
            value = row(variant, step)
            value['balanced_candidates'] = ['a', 'b']
            value['mastery_score_calls'] = [{'concept': 'a', 'score': 0.1}, {'concept': 'b', 'score': 0.9}]
            rows.append(value)
    return rows


def run(rows):
    return analyze(rows, CHAPTERS, seeds=(1,), profiles=('PG',), steps=2)


def test_same_B_and_ties_logged_score_ranking_explains_concept_and_keeps_negative():
    rows = population()
    value = rows[2]
    serve(value, 'b');value['balanced_candidates'] = ['a', 'b']
    value['mastery_score_calls'] = [{'concept': 'a', 'score': 0.8}, {'concept': 'b', 'score': 0.1}]
    result = run(rows)
    assert result['rank_replays_validated'] == 6 and not result['unsupported']
    positive, negative = result['comparisons']
    first = positive['first_prefix_break']
    assert first['classification'] == 'SAME_B_TIES_NATIVE_B_SCORE_RANKING_EXPLAINS_CONCEPT_CHOICE'
    assert first['same_non_score_keys'] and first['tie_context_equal']
    assert negative['negative_case'] and negative['common_before_events'] == 2
    assert positive['rank_replayed_events_both_sides_all_steps'] == 4


def test_membership_difference_has_separate_non_score_only_classification():
    rows = population();value = rows[2];serve(value, 'b')
    value['ready_set'] = value['eligible_candidates'] = value['balanced_candidates'] = ['b']
    value['mastery_score_calls'] = [{'concept': 'b', 'score': 0.9}]
    result = run(rows)
    assert result['comparisons'][0]['first_prefix_break']['classification'] == 'B_MEMBERSHIP_DIFF_SCORE_ONLY_EXPLANATION_NOT_CLAIMED'


def test_missing_capture_stops_claim_without_filling_or_dropping_comparison():
    rows = population();value = rows[2];serve(value, 'b');value['balanced_candidates'] = ['a', 'b']
    value['mastery_score_calls'] = [{'concept': 'b', 'score': 0.1}]
    result = run(rows)
    assert len(result['unsupported']) == 1 and result['comparison_count'] == 2
    assert result['comparisons'][0]['first_prefix_break']['classification'] == 'UNSUPPORTED_CAPTURE_OR_TIE_CONTEXT_NO_FILL'


def test_question_only_break_not_explained_by_concept_ranking():
    rows = population();rows[2]['served_tuple']['question'] = 'different-item'
    rows[2]['query']['question'] = 'different-item'
    first = run(rows)['comparisons'][0]['first_prefix_break']
    assert first['classification'] == 'ITEM_ONLY_DIFF_NOT_EXPLAINED_BY_CONCEPT_RANK'


def test_exact_tie_key_uses_chapter_then_visits_then_lexical_not_B_order_or_current_P():
    value = population()[0]
    value['balanced_candidates'] = ['b', 'a']
    value['mastery_score_calls'] = [{'concept': 'b', 'score': 0.5}, {'concept': 'a', 'score': 0.5}]
    visits = Counter(a=1, b=1)
    assert replay_key(value, visits, None, CHAPTERS)['chosen_concept'] == 'a'
    value['prediction'] = 0.99
    assert replay_key(value, visits, None, CHAPTERS)['chosen_concept'] == 'a'
    serve(value, 'b');value['balanced_candidates'] = ['b', 'a']
    assert replay_key(value, visits, 'Chapter B', CHAPTERS)['chosen_concept'] == 'b'
    assert replay_key(value, Counter(a=2, b=1), None, CHAPTERS)['chosen_concept'] == 'b'
    value['mastery_score_calls'].reverse()
    with pytest.raises(ValueError, match='cover B'): replay_key(value, visits, None, CHAPTERS)
