"""Cửa sổ nhân quả với global target anchors và rào cản OOV."""

from collections.abc import Iterator
import hashlib

import numpy as np

from knowledge_tracing.shared_kt import CausalSequenceInputs
from .encoding import ExerciseEncoding, encode_exercises
from .types import LearnerEvents, TrainingWindow, UnseenTarget, WindowInputs, WindowRecord, WindowSlice


def iter_window_slices(item_ids: np.ndarray, sequence_offsets: np.ndarray, *,
                       context: int = 100, target_block: int = 100) -> Iterator[WindowSlice]:
    ids = np.asarray(item_ids)
    offsets = np.asarray(sequence_offsets)
    if (ids.ndim != 1 or not np.issubdtype(ids.dtype, np.integer) or np.any(ids < -1)
            or offsets.ndim != 1 or not np.issubdtype(offsets.dtype, np.integer)
            or len(offsets) == 0 or offsets[0] != 0 or offsets[-1] != len(ids)
            or np.any(np.diff(offsets) <= 0) or context < 0 or target_block <= 0):
        raise ValueError('invalid sequence ids, offsets or window sizes')
    for begin, end in zip(offsets[:-1], offsets[1:]):
        begin, end = int(begin), int(end)
        n, last_oov = end - begin, -1
        for block in range(0, n, target_block):
            block_end = min(n, block + target_block)
            cursor = block
            while cursor < block_end:
                if ids[begin + cursor] == -1:
                    yield WindowSlice(begin + cursor, begin + cursor + 1, begin + cursor,
                                      np.asarray([cursor], dtype=np.int64), True)
                    last_oov = cursor
                    cursor += 1
                    continue
                run_end = cursor + 1
                while run_end < block_end and ids[begin + run_end] != -1:
                    run_end += 1
                base = max(0, block - context)
                start = max(base, last_oov + 1)
                yield WindowSlice(begin + start, begin + run_end, begin + cursor,
                                  np.arange(start, run_end, dtype=np.int64), False, start > base,
                                  np.arange(start, run_end, dtype=np.int64) - base)
                cursor = run_end


def slice_causal_inputs(inputs: CausalSequenceInputs, window_slice: WindowSlice) -> WindowInputs:
    if window_slice.unseen:
        raise ValueError('unseen target cannot be sent to model')
    start, stop = window_slice.start, window_slice.stop
    n = len(inputs.item_ids)
    arrays = (inputs.timestamps, inputs.prior_responses, inputs.source_rows, inputs.user_ids)
    if (not 0 <= start <= window_slice.target_start < stop <= n
            or any(len(value) != n for value in arrays)
            or len(window_slice.global_ranks) != stop - start
            or len(set(inputs.user_ids[start:stop])) != 1
            or np.any(inputs.item_ids[start:stop] < 0)):
        raise ValueError('invalid window or sequence inputs')
    prior = np.asarray(inputs.prior_responses[start:stop], dtype=np.int8).copy()
    prior[0] = -1
    sliced = CausalSequenceInputs(
        np.asarray(inputs.item_ids[start:stop], dtype=np.int64).copy(),
        np.asarray(inputs.timestamps[start:stop]).copy(), prior,
        np.asarray(inputs.source_rows[start:stop], dtype=np.int64).copy(),
        np.asarray([0, stop - start], dtype=np.int64), tuple(inputs.user_ids[start:stop]), None)
    ranks = window_slice.global_ranks.copy()
    available = window_slice.history_available
    if available is None or len(available) != stop - start:
        raise ValueError('window history accounting is missing')
    target_mask = np.arange(start, stop) >= window_slice.target_start
    identity = f'{sliced.user_ids[0]}\0{int(ranks[target_mask][0])}'
    return WindowInputs(sliced, target_mask, ranks, available.copy(), np.arange(stop-start, dtype=np.int64),
                        np.full(stop-start, window_slice.barrier_applied, dtype=bool),
                        hashlib.sha256(identity.encode('utf-8')).hexdigest())


def iter_windows(learner: LearnerEvents, encoding: ExerciseEncoding, *, context: int = 100,
                 target_block: int = 100, training: bool) -> Iterator[WindowRecord]:
    events = learner.events
    if not events:
        return
    if any(e.user_id != learner.user_id or e.fold != learner.fold or e.correct not in (0, 1) for e in events):
        raise ValueError('invalid learner event identity or response')
    ids = encode_exercises([e.exercise for e in events], encoding)
    labels = np.asarray([e.correct for e in events], dtype=np.int8)
    prior = np.full(len(events), -1, dtype=np.int8)
    prior[1:] = labels[:-1]
    inputs = CausalSequenceInputs(ids, np.asarray([e.time_done for e in events]), prior,
                                  np.asarray([e.source_row for e in events], dtype=np.int64),
                                  np.asarray([0, len(events)], dtype=np.int64),
                                  tuple(learner.user_id for _ in events), None)
    for geometry in iter_window_slices(ids, inputs.sequence_offsets, context=context, target_block=target_block):
        if geometry.unseen:
            yield UnseenTarget(events[geometry.start], int(geometry.global_ranks[0]))
        else:
            window = slice_causal_inputs(inputs, geometry)
            if training:
                yield TrainingWindow(window, labels[geometry.start:geometry.stop].copy())
            else:
                yield window
