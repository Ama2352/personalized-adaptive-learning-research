"""Known-answer fixtures for predefined counts/prefix semantics, no real/model data."""
import copy
import pytest

from analyze_closed_loop_descriptive import PHASES, VARIANTS, summarize


def row(variant, step):
    return {'seed': 1, 'profile': 'PG', 'variant': variant, 'step': step,
        'mastered_decisions': {'a': True, 'b': False}, 'ready_set': ['a', 'b'],
        'eligible_candidates': ['a', 'b'], 'balanced_candidates': ['a'],
        'served_tuple': {'concept': 'a', 'question': 'a-q', 'difficulty': 1.0},
        'query': {'concept': 'a', 'question': 'a-q', 'difficulty': 1.0,
                  'timestamp_iso': 't' + str(step), 'timestamp_ns': step},
        'correct': 1, 'prediction': 0.5, 'phases': PHASES[:],
        'select_timestamp_argument': None, 'is_served_in_simulator': True,
        'full_mastery_score_vector_available': False,
        'mastery_ready_capture_phase': 'during_selection_before_bookkeeping',
        'prediction_capture_phase': 'after_selection_bookkeeping_before_environment_interact',
        'state_before_selection_sha256': 'a' * 64, 'state_after_selection_sha256': 'b' * 64,
        'state_after_update_sha256': 'c' * 64, 'legacy_row_sha256': 'd' * 64, 'outcome_sha256': 'e' * 64,
        'mastery_calls': [{'concept': 'a', 'mastered': True}, {'concept': 'b', 'mastered': False}],
        'mastery_score_calls': [{'concept': 'a', 'score': 0.5}]}


def population(steps=4):
    return [row(variant, step) for variant in VARIANTS for step in range(steps)]


def analyze(rows, steps=4, ledger=None):
    return summarize(rows, seeds=(1,), profiles=('PG',), steps=steps, node_count=2, native_ledger=ledger)


def serve(value, cid):
    value['served_tuple'] = {'concept': cid, 'question': cid + '-q', 'difficulty': 1.0}
    value['query'].update(value['served_tuple'])
    value['balanced_candidates'] = [cid]


def test_pertrajectory_counts_order_only_set_change_histograms_and_negative():
    rows = population(3)
    rows[0]['eligible_candidates'] = ['b', 'a']
    rows[1]['ready_set'] = ['b']
    rows[1]['eligible_candidates'] = ['a']
    rows[2]['state_after_selection_sha256'] = rows[2]['state_before_selection_sha256']
    result, flags, prefixes = analyze(rows, 3)
    first = result['trajectories'][0]
    assert first['R_to_C_setdiff'] == 1 and first['R_to_C_order_onlydiff'] == 1
    assert first['C_to_B_setdiff'] == 2 and first['selected_outside_R'] == 1
    assert first['selected_M_true'] == 3 and first['selection_state_hash_changed'] == 2
    assert first['size_histograms'] == {'R': {'1': 1, '2': 2}, 'C': {'1': 1, '2': 2}, 'B': {'1': 3}}
    assert len(flags) == 9 and len(prefixes) == 6 and result['trajectory_count'] == 3
    assert result['trajectories'][2]['R_to_C_setdiff'] == 0


def test_label_only_break_is_sticky_and_first_action_difference_is_separate():
    rows = population()
    full = [v for v in rows if v['variant'] == 'graph_package']
    full[0]['correct'] = 0
    serve(full[1], 'b')
    result, _, flags = analyze(rows)
    group, negative = result['common_prefix']
    assert group['common_before_events'] == 1 and group['common_after_events'] == 0
    assert group['first_prefix_break'] == {'step': 0, 'reasons': ['label'], 'label_only': True}
    assert group['first_full_served_tuple_diff']['step'] == 1
    assert group['first_full_served_tuple_diff']['common_before'] is False
    assert [v['common_before'] for v in flags[:4]] == [1, 0, 0, 0]
    assert [v['M_setdiff'] for v in flags[:4]] == [0, '', '', '']
    assert negative['common_before_events'] == negative['common_after_events'] == 4
    assert negative['first_prefix_break'] is None and negative['first_full_served_tuple_diff'] is None


def test_break_snapshot_counts_before_current_event_then_never_reopens():
    rows = population()
    full = [v for v in rows if v['variant'] == 'graph_package']
    serve(full[1], 'b')
    full[1]['mastered_decisions']['a'] = False
    full[1]['mastery_calls'][0]['mastered'] = False
    result, _, flags = analyze(rows)
    group = result['common_prefix'][0]
    assert group['common_before_events'] == 2 and group['common_after_events'] == 1
    assert group['M_setdiff_on_common_before'] == 1 and group['served_tuple_diff_on_common_before'] == 1
    assert group['first_full_served_tuple_diff']['common_before'] is True
    assert [v['common_before'] for v in flags[:4]] == [1, 1, 0, 0]


def test_timestamp_only_break_does_not_become_action_difference():
    rows = population(2)
    target = next(v for v in rows if v['variant'] == 'graph_package' and v['step'] == 0)
    target['query']['timestamp_iso'] = 'other'
    target['query']['timestamp_ns'] = 99
    result, _, _ = analyze(rows, 2)
    group = result['common_prefix'][0]
    assert group['first_prefix_break']['reasons'] == ['timestamp']
    assert group['first_prefix_break']['label_only'] is False
    assert group['first_full_served_tuple_diff'] is None


@pytest.mark.parametrize('mode', ['missing', 'duplicate', 'selected_outside_B', 'B_outside_C', 'M_not_boolean', 'wrong_phase'])
def test_fail_closed_population_and_semantic_guards(mode):
    rows = population(2)
    if mode == 'missing': rows.pop()
    elif mode == 'duplicate': rows.append(copy.deepcopy(rows[0]))
    elif mode == 'selected_outside_B': rows[0]['balanced_candidates'] = ['b']
    elif mode == 'B_outside_C': rows[0]['eligible_candidates'] = ['b']
    elif mode == 'M_not_boolean': rows[0]['mastered_decisions']['a'] = 1
    else: rows[0]['phases'] = list(reversed(PHASES))
    with pytest.raises(ValueError): analyze(rows, 2)


def test_native_call_ledger_known_answer_and_missing_update_mastery_rejected():
    rows = population(2)
    ledger = {k: 6 for k in ('select', 'ready_set', 'predict', 'interact', 'update')}
    ledger.update(is_mastered=18, mastery_score=6)
    result, _, _ = analyze(rows, 2, ledger)
    assert result['native_call_ledger_verified'] == ledger
    ledger['is_mastered'] = 12
    with pytest.raises(ValueError, match='mastery call ledger'): analyze(rows, 2, ledger)


def test_bounded_check_interrupts_before_analysis():
    def stop(): raise TimeoutError('fixture deadline')
    with pytest.raises(TimeoutError):
        summarize(population(1), seeds=(1,), profiles=('PG',), steps=1, node_count=2, check=stop)
