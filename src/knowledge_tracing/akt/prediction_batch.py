"""Dự đoán AKT theo batch cửa sổ, giữ hợp đồng target của iterator lịch sử.

API opt-in dùng cho producer Junyi mới. Không import Torch hoặc thay đường
iter_predictions hiện có. PredictionRecord được nối với outcome sau inference.
"""
from collections.abc import Iterable, Iterator
import hashlib
import json
import math

import numpy as np

from .types import LearnerEvents, PredictionRecord, UnseenTarget
from .windows import iter_windows


def _checkpoint_identity(adapter):
    pinned = getattr(adapter, 'checkpoint_id', None)
    if isinstance(pinned, str) and pinned:
        return pinned
    identity = getattr(adapter, 'run_identity', None)
    if not isinstance(identity, dict) or not identity:
        raise ValueError('adapter has no checkpoint identity')
    payload = json.dumps(identity, sort_keys=True, separators=(',', ':'), default=str).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def _validate_learner(learner, previous_user):
    if (not learner.user_id or not learner.events or learner.user_id == previous_user
            or any(event.user_id != learner.user_id or event.fold != learner.fold
                   or event.correct not in (0, 1) or event.suggested not in (0, 1)
                   for event in learner.events)):
        raise ValueError('invalid or repeated prediction learner')
    if previous_user is not None and learner.user_id < previous_user:
        raise ValueError('prediction learners must be sorted by user_id')
    rows = [event.source_row for event in learner.events]
    if any(row <= 0 for row in rows) or len(rows) != len(set(rows)):
        raise ValueError('source_row must be positive and unique per learner')
    if any((left.time_done, left.source_row) > (right.time_done, right.source_row)
           for left, right in zip(learner.events, learner.events[1:])):
        raise ValueError('learner events are not in canonical chronological order')


def iter_predictions_batched(adapter, learners: Iterable[LearnerEvents], *,
                             batch_size: int | None = None, prefetch: bool = False) -> Iterator[PredictionRecord]:
    """Giữ thứ tự record/OOV; chỉ cửa sổ nhân quả đi vào predict_windows.

Batch tối đa128 cửa sổ, có thể chứa nhiều learner. Gặp OOV thì xuất batch đang
chờ trước, sau đó phát record null. Caller phải tiêu thụ iterator tới cuối.
Metadata/target coverage giữ cùng iterator lịch sử. Sai khác số học khi dùng
batch CUDA cần được đo riêng trên runtime thật trước producer chính.
"""
    yield from iter_prepared_predictions_batched(adapter,prepare_prediction_windows(adapter,learners),
                                                 batch_size=batch_size,prefetch=prefetch)


def prepare_prediction_windows(adapter, learners):
    previous_user = None
    for learner in learners:
        _validate_learner(learner, previous_user)
        events_by_row = {event.source_row: event for event in learner.events}
        for window in iter_windows(learner, adapter.encoding, context=adapter.config.context,
                                   target_block=adapter.config.target_block, training=False):
            if isinstance(window, UnseenTarget):
                yield window
            else:
                targets = tuple((int(index), events_by_row.get(int(window.inputs.source_rows[index])))
                                for index in np.flatnonzero(window.target_mask))
                yield window, targets
        previous_user = learner.user_id


def _prefetch_prepared(prepared,size):
    """Một chunk tương lai, giữ nguyên record/OOV và đóng reader khi lỗi."""
    from concurrent.futures import ThreadPoolExecutor
    from itertools import islice
    source=iter(prepared)
    try:
        with ThreadPoolExecutor(max_workers=1,thread_name_prefix='akt-selection') as executor:
            def take():
                return tuple(islice(source,size))
            future=executor.submit(take)
            try:
                while True:
                    chunk=future.result()
                    if not chunk:
                        break
                    future=executor.submit(take)
                    yield from chunk
            finally:
                future.cancel()
    finally:
        close=getattr(source,'close',None)
        if close is not None:
            close()


def iter_prepared_predictions_batched(adapter, prepared, *, batch_size=None, prefetch=False):
    """Chấm cùng batch từ input/metadata đã chuẩn bị; model chỉ nhận WindowInputs."""
    configured = adapter.config.batch_size
    requested = configured if batch_size is None else batch_size
    if (type(configured) is not int or not 1 <= configured <= 128
            or type(requested) is not int or not 1 <= requested <= configured or type(prefetch) is not bool):
        raise ValueError('prediction batch must be an integer within configured1..128')
    checkpoint_id = _checkpoint_identity(adapter)
    support = adapter.encoding.train_support_students
    pending = []

    def flush():
        if not pending:
            return
        windows = tuple(window for window, _ in pending)
        probabilities = adapter.predict_windows(windows)
        if len(probabilities) != len(pending):
            raise ValueError('adapter batch output count does not align with windows')
        for (window, targets), values in zip(pending, probabilities):
            values = np.asarray(values, dtype=np.float64)
            if values.shape != window.target_mask.shape:
                raise ValueError('adapter prediction shape does not align with window')
            for index, event in targets:
                value = float(values[index])
                if event is None or not math.isfinite(value) or not 0.0 <= value <= 1.0:
                    raise ValueError('known target has missing identity or invalid probability')
                item_support = support.get(event.exercise, 0)
                if item_support <= 0:
                    raise ValueError('known prediction has no train support')
                yield PredictionRecord(
                    event.source_row, event.user_id, event.exercise, event.time_done,
                    event.correct, event.suggested, event.fold, value, 'fitted', False,
                    int(item_support), int(window.history_available[index]), int(window.history_used[index]),
                    bool(window.context_reset[index]), window.window_id, checkpoint_id)
        pending.clear()

    source=_prefetch_prepared(prepared,requested) if prefetch else prepared
    try:
        for record in source:
            if isinstance(record, UnseenTarget):
                yield from flush()
                window = record
                event = window.event
                block_start = (window.global_rank // adapter.config.target_block) * adapter.config.target_block
                base = max(0, block_start-adapter.config.context)
                yield PredictionRecord(
                    event.source_row, event.user_id, event.exercise, event.time_done,
                    event.correct, event.suggested, event.fold, None, 'unseen', False, 0,
                    window.global_rank-base, 0, True,
                    hashlib.sha256(f'{event.user_id}\0{window.global_rank}\0unseen'.encode()).hexdigest(),
                    checkpoint_id)
                continue
            window, targets = record
            pending.append((window, targets))
            if len(pending) == requested:
                yield from flush()
        yield from flush()
    finally:
        if prefetch:
            source.close()
