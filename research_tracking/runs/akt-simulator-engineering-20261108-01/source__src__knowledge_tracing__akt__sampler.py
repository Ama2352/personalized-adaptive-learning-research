"""Cursor phục hồi shuffle bằng deterministic replay và kiểm prefix digest."""

import hashlib
import json
import random

from .types import TrainingWindow


def iter_shuffled_windows(factory, *, seed, buffer_size=1024):
    if type(buffer_size) is not int or buffer_size < 1:
        raise ValueError('invalid shuffle buffer size')
    rng = random.Random(seed)
    buffer = []
    for window in factory():
        if not isinstance(window, TrainingWindow):
            raise ValueError('training contains an unseen target')
        if len(buffer) < buffer_size:
            buffer.append(window)
            continue
        index = rng.randrange(len(buffer))
        yield buffer[index]
        buffer[index] = window
    rng.shuffle(buffer)
    yield from buffer


def _window_digest(entry):
    window = entry.window
    inputs = window.inputs
    payload = {'users': inputs.user_ids, 'items': inputs.item_ids.tolist(),
               'times': inputs.timestamps.tolist(), 'rows': inputs.source_rows.tolist(),
               'prior': inputs.prior_responses.tolist(), 'targets': entry.targets.tolist(),
               'target_mask': window.target_mask.tolist(), 'window_id': window.window_id}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).digest()


class ReplayableWindowCursor:
    """Rebuild cùng stream rồi bỏ prefix đã commit, không thực hiện optimizer update.

    Replay tốn O(prefix) đọc và hash, bộ nhớ bounded theo shuffle buffer.
    Factory phải thuần xác định và không dùng global training RNG.
    Snapshot chỉ dùng ở batch boundary với toàn bộ yielded windows đã commit.
    Stream identity phải gắn dataset/vocabulary/window config immutable.
    """

    def __init__(self, factory, *, seed, stream_identity, buffer_size=1024, state=None):
        if not isinstance(stream_identity, str) or not stream_identity or type(seed) is not int:
            raise ValueError('invalid sampler identity')
        self.seed = seed
        self.stream_identity = stream_identity
        self.buffer_size = buffer_size
        self.consumed = 0
        self.digest = hashlib.sha256(b'akt-window-prefix-v1').digest()
        self.iterator = iter(iter_shuffled_windows(factory, seed=seed, buffer_size=buffer_size))
        self.pending = None
        if state is not None:
            if (state.get('schema_version') != 1 or state.get('seed') != seed
                    or state.get('stream_identity') != stream_identity or state.get('buffer_size') != buffer_size
                    or type(state.get('consumed_windows')) is not int or state['consumed_windows'] < 0):
                raise ValueError('sampler state identity mismatch')
            try:
                for _ in range(state['consumed_windows']):
                    next(self)
            except StopIteration as error:
                raise ValueError('sampler prefix exceeds stream') from error
            if state.get('prefix_sha256') != self.digest.hex():
                raise ValueError('sampler prefix content mismatch')

    def __iter__(self):
        return self

    def __next__(self):
        entry = self.peek()
        self.pending = None
        self.digest = hashlib.sha256(self.digest + _window_digest(entry)).digest()
        self.consumed += 1
        return entry

    def peek(self):
        """Nhìn window tiếp theo mà không commit cursor hoặc prefix digest."""
        if self.pending is None:
            self.pending = next(self.iterator)
        return self.pending

    def state_dict(self):
        return {'schema_version': 1, 'seed': self.seed, 'stream_identity': self.stream_identity,
                'buffer_size': self.buffer_size, 'consumed_windows': self.consumed,
                'prefix_sha256': self.digest.hex()}
