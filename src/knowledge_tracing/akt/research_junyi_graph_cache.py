"""Cache A1 bất biến theo window, build CPU và đọc SQLite read-only khi train.

Khóa chứa toàn input quá khứ và geometry; target labels không thuộc cache.
Manifest bên ngoài ghim SHA file. Không tự xây cache trong bước GPU.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import uuid
import zlib

import numpy as np

from .config import PROJECT_ROOT
from .filesystem import publish_new_file
from .cache_artifacts import JunyiCacheArtifactRoot
from .research_junyi_compact import (CompactA1Context, CompactConfidenceContext,
    build_compact_context, build_compact_confidence_context)

CACHE_ROOT = PROJECT_ROOT / 'artifacts/akt/graph-context-cache'
FORMAT = 'junyi-a1-graph-context-cache-v1'
SOURCE_FILES = (
    'research_junyi_graph_cache.py', 'research_junyi_compact.py',
    'research_junyi_graph.py', 'research_junyi_data.py', 'windows.py', 'types.py',
)


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _owned(path, artifact_root=None):
    if artifact_root is not None:
        _need(type(artifact_root) is JunyiCacheArtifactRoot, 'Typed cloud graph cache root required')
        return artifact_root.validate(path)
    path = Path(path).absolute()
    base = CACHE_ROOT.absolute()
    _need(path != base and path.is_relative_to(base), 'owned graph-context cache required')
    current = path
    while current != current.parent:
        _need(not current.is_symlink() and not getattr(current, 'is_junction', lambda: False)(),
              'graph cache alias rejected')
        current = current.parent
    _need(path.resolve() == path, 'physical graph cache path required')
    return path


def _binding(phase, dataset_sha256, window_manifest_sha256):
    for value in (dataset_sha256, window_manifest_sha256):
        _need(type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value),
              'external dataset/window SHA required')
    phase.assert_boundary()
    format_id = FORMAT if phase.condition.variant == 'A1' else 'junyi-confidence-graph-context-cache-v1'
    return dict(format=format_id, dataset_sha256=dataset_sha256,
                window_manifest_sha256=window_manifest_sha256,
                phase_sha256=phase.view.identity, encoding_sha256=phase._encoding_identity,
                condition_sha256=phase._condition_identity,
                sources={name: _sha(Path(__file__).parent / name) for name in SOURCE_FILES})


def window_key(window):
    digest = hashlib.sha256(json.dumps((window.window_id, window.inputs.user_ids),
                                       separators=(',', ':')).encode())
    for array in (window.inputs.item_ids, window.inputs.timestamps, window.inputs.prior_responses,
                  window.inputs.source_rows, window.inputs.sequence_offsets, window.target_mask,
                  window.global_ranks, window.history_available, window.history_used, window.context_reset):
        digest.update(str(array.dtype).encode())
        digest.update(json.dumps(array.shape).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def _decode(width, window_id, payload, phase):
    _need(type(width) is int and 1 <= width <= 200, 'bounded cached window required')
    decoder = zlib.decompressobj()
    weighted = phase.condition.variant in ('A2', 'A3')
    size = (31 if weighted else 15) * width
    raw = decoder.decompress(payload, size + 1)
    _need(len(raw) == size and decoder.eof and not decoder.unused_data,
          'graph cache payload size/stream mismatch')
    base = CompactA1Context((1, width), (window_id,), phase._condition_identity,
        phase._encoding_identity, phase.view.identity,
        raw[:4*width], raw[4*width:5*width], raw[5*width:6*width],
        raw[6*width:7*width], raw[7*width:15*width])
    return CompactConfidenceContext(base, phase.condition.variant, raw[15*width:]) if weighted else base


def build_graph_context_cache(path, records, phase, *, dataset_sha256, window_manifest_sha256,
                              expected_windows, expected_targets, max_seconds, max_rss_bytes, artifact_root=None):
    """Công bố file mới sau khi kiểm coverage; lỗi giữ file .partial có danh tính riêng."""
    import psutil
    from .types import TrainingWindow, WindowInputs
    path = _owned(path, artifact_root)
    _need(not path.exists(), 'graph cache already exists')
    _need(type(expected_windows) is int and expected_windows > 0
          and type(expected_targets) is int and expected_targets > 0
          and max_seconds > 0 and max_rss_bytes > 0, 'explicit graph cache bounds required')
    binding = _binding(phase, dataset_sha256, window_manifest_sha256)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.partial')
    started = time.monotonic()
    process = psutil.Process()
    peak_rss = process.memory_info().rss
    connection = sqlite3.connect(temporary)
    count = targets = 0
    pending = []
    try:
        connection.execute('PRAGMA cache_size=-2048')
        connection.execute('CREATE TABLE metadata (payload TEXT NOT NULL)')
        connection.execute('CREATE TABLE contexts (key TEXT PRIMARY KEY, window_id TEXT UNIQUE NOT NULL, '
                           'width INTEGER NOT NULL, payload BLOB NOT NULL, digest TEXT NOT NULL)')
        def flush():
            nonlocal count, targets, peak_rss
            if not pending:
                return
            peak_rss = max(peak_rss, process.memory_info().rss)
            _need(time.monotonic() - started <= max_seconds and peak_rss <= max_rss_bytes,
                  'graph cache build resource limit')
            weighted = phase.condition.variant in ('A2', 'A3')
            bulk = (build_compact_confidence_context if weighted else build_compact_context)(tuple(pending), phase)
            arrays = bulk.arrays()
            messages, active, target, valid = arrays[:4]
            base = bulk.base if weighted else bulk
            sources = np.frombuffer(base.source_rows, dtype='<i8').reshape(base.shape)
            rows = []
            for row, window in enumerate(pending):
                width = len(window.inputs.item_ids)
                context = CompactA1Context((1, width), (window.window_id,), base.condition_sha256,
                    base.encoding_sha256, base.phase_sha256, messages[row, :width].tobytes(),
                    active[row, :width].tobytes(), target[row, :width].tobytes(),
                    valid[row, :width].tobytes(), sources[row, :width].tobytes())
                raw = context.messages + context.applied + context.target_mask + context.valid_mask + context.source_rows
                if weighted:
                    features = arrays[4][row, :width].tobytes()
                    context = CompactConfidenceContext(context, phase.condition.variant, features)
                    raw += features
                rows.append((window_key(window), window.window_id, width, zlib.compress(raw, 1), context.identity))
                targets += int(window.target_mask.sum())
            connection.executemany('INSERT INTO contexts VALUES (?,?,?,?,?)', rows)
            count += len(pending)
            _need(count <= expected_windows and targets <= expected_targets, 'graph cache population exceeded')
            pending.clear()
        for record in records:
            window = record.window if type(record) is TrainingWindow else record
            _need(type(window) is WindowInputs, 'known typed cache window required')
            pending.append(window)
            if len(pending) == 128:
                flush()
        flush()
        _need(count == expected_windows and targets == expected_targets, 'graph cache coverage incomplete')
        _need(binding == _binding(phase, dataset_sha256, window_manifest_sha256), 'cache build binding changed')
        metadata = dict(binding=binding, windows=count, targets=targets, status='COMPLETE')
        connection.execute('INSERT INTO metadata VALUES (?)', (json.dumps(metadata, sort_keys=True),))
        connection.commit()
        _need(connection.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'invalid built SQLite cache')
    except BaseException:
        connection.close()
        raise
    connection.close()
    digest = _sha(temporary)
    publish_new_file(temporary, path)
    _need(_sha(path) == digest, 'published graph cache differs')
    return dict(status='COMPLETE', cache_sha256=digest, bytes=path.stat().st_size,
                windows=count, targets=targets, wall_seconds=time.monotonic()-started,
                peak_rss_bytes=peak_rss, binding=binding)


@dataclass(frozen=True)
class GraphContextCache:
    path: Path
    expected_sha256: str
    binding: str
    fingerprint: tuple
    windows: int
    targets: int

    @classmethod
    def open(cls, path, expected_sha256, phase, *, dataset_sha256, window_manifest_sha256, artifact_root=None):
        path = _owned(path, artifact_root)
        _need(path.is_file() and _sha(path) == expected_sha256, 'graph cache file SHA mismatch')
        connection = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)
        try:
            _need(connection.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'invalid SQLite cache')
            rows = connection.execute('SELECT payload FROM metadata').fetchall()
            _need(len(rows) == 1, 'single graph cache metadata required')
            metadata = json.loads(rows[0][0])
            expected = _binding(phase, dataset_sha256, window_manifest_sha256)
            _need(metadata['status'] == 'COMPLETE' and metadata['binding'] == expected,
                  'graph cache dataset/phase/encoding/graph/source mismatch')
            _need(connection.execute('SELECT count(*) FROM contexts').fetchone()[0] == metadata['windows'],
                  'graph cache row count mismatch')
        finally:
            connection.close()
        stat = path.stat()
        return cls(path, expected_sha256, json.dumps(expected, sort_keys=True),
                   (stat.st_size, stat.st_mtime_ns, stat.st_ino), metadata['windows'], metadata['targets'])

    @property
    def identity(self):
        return _digest((FORMAT, self.expected_sha256, self.binding))

    def assert_for(self, phase):
        phase._light_check()
        stat = self.path.stat()
        _need((stat.st_size, stat.st_mtime_ns, stat.st_ino) == self.fingerprint, 'graph cache file changed')
        binding = json.loads(self.binding)
        _need(binding['phase_sha256'] == phase.view.identity
              and binding['encoding_sha256'] == phase._encoding_identity
              and binding['condition_sha256'] == phase._condition_identity, 'graph cache phase/condition mismatch')

    def batch(self, windows, phase):
        self.assert_for(phase)
        _need(type(windows) is tuple and 1 <= len(windows) <= 128, 'bounded graph cache batch required')
        keys = tuple(window_key(window) for window in windows)
        _need(len(set(keys)) == len(keys), 'duplicate graph cache windows')
        connection = sqlite3.connect(self.path.as_uri() + '?mode=ro&immutable=1', uri=True)
        try:
            rows = connection.execute('SELECT key,window_id,width,payload,digest FROM contexts WHERE key IN ('
                + ','.join('?' for _ in keys) + ')', keys).fetchall()
        finally:
            connection.close()
        _need(len(rows) == len(keys), 'graph context cache miss; rebuild against matching inputs')
        indexed = {row[0]: row[1:] for row in rows}
        shape = (len(windows), max(len(window.inputs.item_ids) for window in windows))
        messages = np.zeros(shape, dtype='<f4')
        active = np.zeros(shape, dtype=np.bool_)
        target = np.zeros(shape, dtype=np.bool_)
        valid = np.zeros(shape, dtype=np.bool_)
        sources = np.full(shape, -1, dtype='<i8')
        weighted = phase.condition.variant in ('A2', 'A3')
        features = np.zeros((*shape, 4), dtype='<f4') if weighted else None
        for row, (key, window) in enumerate(zip(keys, windows)):
            window_id, width, payload, digest = indexed[key]
            _need(window_id == window.window_id and width == len(window.inputs.item_ids), 'cached window identity differs')
            context = _decode(width, window_id, payload, phase)
            _need(context.identity == digest, 'cached graph context digest mismatch')
            if weighted:
                features[row, :width] = np.frombuffer(context.features, dtype='<f4').reshape((width, 4))
                context = context.base
            # File đã được xác minh toàn vẹn, semantic đã kiểm lúc build; hash phát hiện bytes drift.
            messages[row, :width] = np.frombuffer(context.messages, dtype='<f4')
            active[row, :width] = np.frombuffer(context.applied, dtype=np.bool_)
            target[row, :width] = np.frombuffer(context.target_mask, dtype=np.bool_)
            valid[row, :width] = np.frombuffer(context.valid_mask, dtype=np.bool_)
            sources[row, :width] = np.frombuffer(context.source_rows, dtype='<i8')
        self.assert_for(phase)
        base = CompactA1Context(shape, tuple(window.window_id for window in windows), phase._condition_identity,
            phase._encoding_identity, phase.view.identity, messages.tobytes(), active.tobytes(),
            target.tobytes(), valid.tobytes(), sources.tobytes())
        return CompactConfidenceContext(base, phase.condition.variant, features.tobytes()) if weighted else base
