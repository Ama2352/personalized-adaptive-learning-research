import numpy as np
import pytest

from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.types import KTEvent, LearnerEvents, TrainingWindow, UnseenTarget
from knowledge_tracing.akt.windows import iter_windows


def sequence(n, *, oov_ranks=(), user='u'):
    return LearnerEvents(user, 0, tuple(
        KTEvent(user, 'X' if i in oov_ranks else 'A', 100+i, i+1, i % 2, 0, 0)
        for i in range(n)))


def encoding():
    return fit_vocabulary([sequence(1, user='train')])


def targets(records):
    result = {}
    for record in records:
        if isinstance(record, UnseenTarget):
            result[record.global_rank] = ('unseen', None, None)
        else:
            window = record.window if isinstance(record, TrainingWindow) else record
            for i, keep in enumerate(window.target_mask):
                if keep:
                    rank = int(window.global_ranks[i])
                    assert rank not in result
                    result[rank] = ('known', int(window.history_used[i]), bool(window.context_reset[i]))
    return result


@pytest.mark.parametrize('n', [1, 100, 101, 200, 201, 22067])
def test_target_partition_for_short_and_long_histories(n):
    rows = list(iter_windows(sequence(n), encoding(), training=True))
    scored = targets(rows)
    assert sorted(scored) == list(range(n))
    assert scored[0][1] == 0
    if n >= 101:
        assert scored[100][1] == 100
    if n >= 200:
        assert scored[199][1] == 199
    if n >= 201:
        assert scored[200][1] == 100
    for record in rows:
        if isinstance(record, TrainingWindow):
            assert len(record.window.inputs.item_ids) <= 200
            assert not hasattr(record.window.inputs, 'targets')
            assert record.window.inputs.prior_responses[0] == -1


def test_history_available_counts_nominal_window_history_not_global_rank():
    windows = list(iter_windows(sequence(201), encoding(), training=False))
    actual = {}
    for window in windows:
        for i, keep in enumerate(window.target_mask):
            if keep:
                actual[int(window.global_ranks[i])] = int(window.history_available[i])
    assert actual[100] == 100
    assert actual[199] == 199
    assert actual[200] == 100


def test_oov_barrier_keeps_global_anchors_and_expires():
    scored = targets(list(iter_windows(sequence(301, oov_ranks=(100,)), encoding(), training=True)))
    assert scored[100][0] == 'unseen'
    assert scored[101] == ('known', 0, True)
    assert scored[200] == ('known', 99, True)
    assert scored[300] == ('known', 100, False)
    assert len(scored) == 301


def test_consecutive_first_and_last_oov_are_counted_once():
    scored = targets(list(iter_windows(sequence(5, oov_ranks=(0, 1, 4)), encoding(), training=True)))
    assert [scored[i][0] for i in range(5)] == ['unseen', 'unseen', 'known', 'known', 'unseen']
    assert scored[2][1] == 0
    assert scored[3][1] == 1


def test_custom_window_lengths_and_empty_learner():
    rows = list(iter_windows(sequence(12), encoding(), context=3, target_block=4, training=False))
    assert max(len(r.inputs.item_ids) for r in rows) == 7
    assert len(targets(rows)) == 12
    assert list(iter_windows(sequence(0), encoding(), training=False)) == []
