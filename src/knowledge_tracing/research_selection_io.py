"""Primitive đọc artifact cho selector, không cấp quyền thực thi.

Chỉ mở exact FileRef caller đã review. Không import model, deserialize checkpoint,
mở corpus ngầm hoặc chọn winner. Caller vẫn phải normalize/admit metadata và
rows, kiểm input cuối bằng verify_unchanged trước khi đóng bất kỳ kết quả nào.
Các clocks/counts cooperative không thay owned hard deadline hoặc OS RAM quota.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import csv
import functools
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import stat
import time
from types import MappingProxyType

from knowledge_tracing.research_admission import ModelNeutralKey
from knowledge_tracing.research_selection import REQUIRED_CANDIDATE_IDS

_now = time.perf_counter
KEY_FIELDS = tuple(ModelNeutralKey.__dataclass_fields__)
PHASE_FIELDS = ('phase_scope', 'phase_sha256', 'encoding_sha256')
GEOMETRY_FIELDS = ('window_id', 'history_available', 'history_used', 'context_reset')


def need(ok, message):
    if not ok:
        raise ValueError(message)


@dataclass(frozen=True)
class FileRef:
    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self):
        need(type(self.path) is str and self.path and '\\' not in self.path
             and not any(ord(c) < 32 for c in self.path), 'Normalized relative file path')
        path = PurePosixPath(self.path)
        need(path.parts and not path.is_absolute() and path.as_posix() == self.path
             and all(part not in ('.', '..') and ':' not in part for part in path.parts), 'No path traversal/alias')
        need(type(self.sha256) is str and len(self.sha256) == 64
             and all(c in '0123456789abcdef' for c in self.sha256), 'Lowercase SHA256')
        need(type(self.size_bytes) is int and 0 <= self.size_bytes <= 2**40, 'Exact nonnegative byte size')


@dataclass(frozen=True)
class FileReadLimits:
    max_file_bytes: int
    max_total_read_bytes: int
    max_files: int
    max_open_files: int
    max_json_bytes: int
    max_csv_bytes: int
    max_csv_buffer_bytes: int
    max_csv_rows: int
    max_index_entries: int
    max_line_bytes: int
    max_fields: int
    max_field_bytes: int
    max_seconds: float

    def __post_init__(self):
        for name, value in self.__dict__.items():
            if name != 'max_seconds':
                need(type(value) is int and 0 < value <= 2**40, 'Explicit positive file/count limits')
        need(self.max_json_bytes <= self.max_file_bytes <= self.max_total_read_bytes
             and self.max_csv_bytes <= self.max_file_bytes
             and self.max_line_bytes <= self.max_csv_buffer_bytes <= self.max_csv_bytes
             and self.max_csv_rows <= self.max_index_entries, 'Consistent file/buffer/index limits')
        need(type(self.max_seconds) in (int, float) and math.isfinite(self.max_seconds)
             and 0 < self.max_seconds <= 120, 'Finite cooperative time limit')


def csv_fields(candidate_id, kind):
    need(candidate_id in REQUIRED_CANDIDATE_IDS and kind in ('predictions', 'targets'), 'Actual producer/CSV kind')
    if kind == 'targets':
        return (*KEY_FIELDS, *PHASE_FIELDS, 'correct') if candidate_id.startswith('A') else (*KEY_FIELDS, 'correct')
    if candidate_id.startswith('A'):
        return (*KEY_FIELDS, *PHASE_FIELDS, *GEOMETRY_FIELDS, 'probability', 'support_reason')
    return (*KEY_FIELDS, 'probability', 'support_reason', 'input_support_reason', *PHASE_FIELDS)


def _integer(text):
    need(text.isascii() and text.isdecimal() and (len(text) == 1 or text[0] != '0'), 'Canonical unsigned decimal key')
    return int(text)


def _key(row):
    return ModelNeutralKey(row['learner_id'], row['item_id'], _integer(row['timestamp']),
        _integer(row['source_row']), _integer(row['global_rank']), row['history_hash_scheme'],
        row['history_sha256'], row['origin_role'])


def _fail_closed(method):
    @functools.wraps(method)
    def wrapped(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except BaseException:
            self.failed = True
            raise
    return wrapped


class CsvRowIndex:
    """Chỉ keys/offset/length/rowSHA, không giữ body CSV hoặc chín row tables."""
    def __init__(self, reader, ref, candidate_id, kind, header, entries):
        self._reader, self.ref = reader, ref
        self.candidate_id, self.kind, self.header = candidate_id, kind, header
        self._entries = MappingProxyType(dict(entries))
        self.keys = tuple(sorted(self._entries))

    def row(self, key):
        return self._reader._indexed_row(self, key)

    def rows(self):
        for key in self.keys:
            yield self.row(key)

    def open_rows(self):
        """Giữ một handle đã xác minh trong context, tính vào max_open_files."""
        return self._reader.open_index_rows(self)


class _IndexedRowCursor:
    def __init__(self, reader, index, stream):
        self.reader, self.index, self.stream = reader, index, stream
        self.closed = False

    def row(self, key):
        return self.reader._cursor_row(self, key)


class BoundedArtifactReader:
    def __init__(self, root, limits):
        need(type(limits) is FileReadLimits, 'Typed limits')
        limits.__post_init__()
        self.root = Path(root).absolute()
        need(self.root.is_dir() and self.root.resolve() == self.root, 'Physical caller root')
        self.limits, self.started = limits, _now()
        self.failed = self.closed = False
        self.bytes_read = self.open_files = self.index_entries = 0
        self._refs, self._stamps, self._identities = {}, {}, {}

    def _guard(self):
        elapsed = _now() - self.started
        need(not self.failed and not self.closed and math.isfinite(elapsed)
             and 0 <= elapsed <= self.limits.max_seconds, 'Failed/closed/deadline reader')
        return elapsed

    def _path(self, ref):
        need(type(ref) is FileRef, 'Exact FileRef')
        ref.__post_init__()
        parts = PurePosixPath(ref.path).parts
        protected = (('dataset',), ('artifacts', 'bkt_baseline'), ('venv',), ('.wsl',))
        lowered = tuple(part.lower() for part in parts)
        need(not any(lowered[:len(prefix)] == prefix for prefix in protected), 'Protected input forbidden')
        cursor = self.root
        for part in ('', *parts):
            cursor = cursor / part
            need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'Ancestor alias forbidden')
        need(cursor.resolve() == cursor and cursor.is_file(), 'Physical regular file')
        return cursor

    @staticmethod
    def _stamp(value):
        return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)

    @contextmanager
    def _opened(self, ref, cap):
        self._guard()
        need(type(ref) is FileRef, 'Exact FileRef')
        need(ref.size_bytes <= min(cap, self.limits.max_file_bytes), 'File size cap before open')
        path = self._path(ref)
        old = self._refs.get(ref.path)
        need(old is None or old == ref, 'Same path cannot change declared bytes/pin')
        need(old is not None or len(self._refs) < self.limits.max_files, 'Unique file cap')
        before = path.stat()
        need(stat.S_ISREG(before.st_mode) and before.st_size == ref.size_bytes, 'Declared regular file size')
        token = self._stamp(before)
        need(ref.path not in self._stamps or token == self._stamps[ref.path], 'Input stat changed since verification')
        physical_id = (before.st_dev, before.st_ino)
        need(physical_id not in self._identities or self._identities[physical_id] == ref.path, 'Duplicate physical file alias')
        need(self.open_files < self.limits.max_open_files, 'Open handle cap')
        self._refs[ref.path] = ref
        self._identities[physical_id] = ref.path
        self.open_files += 1
        try:
            with path.open('rb') as stream:
                import os
                opened_token = self._stamp(os.fstat(stream.fileno()))
                # Path và handle có thể trả ctime khác nhau. Giữ kiểm ctime
                # trong từng API, identity/size/mtime vẫn phải khớp giữa hai API.
                need(opened_token[:4] == token[:4], 'Opened exact file identity')
                yield stream, token
                need(self._stamp(os.fstat(stream.fileno())) == opened_token
                     and self._stamp(path.stat()) == token, 'Input changed during read')
                self._path(ref)
                self._guard()
        finally:
            self.open_files -= 1

    def _charge(self, amount):
        self.bytes_read += amount
        need(self.bytes_read <= self.limits.max_total_read_bytes, 'Cumulative read byte cap')
        self._guard()

    def _reserve_read(self, amount):
        self._guard()
        need(self.bytes_read + amount <= self.limits.max_total_read_bytes, 'Read byte cap before IO')

    def _commit(self, ref, stamp, count, digest):
        need(count == ref.size_bytes and digest == ref.sha256, 'Actual SHA/size mismatch')
        self._stamps[ref.path] = stamp

    @_fail_closed
    def verify_file(self, ref):
        digest, size = hashlib.sha256(), 0
        with self._opened(ref, self.limits.max_file_bytes) as (stream, stamp):
            self._reserve_read(ref.size_bytes)
            while size < ref.size_bytes:
                chunk = stream.read(min(65536, self.limits.max_csv_buffer_bytes, ref.size_bytes - size))
                need(chunk, 'Unexpected EOF')
                self._charge(len(chunk)); digest.update(chunk); size += len(chunk)
        self._commit(ref, stamp, size, digest.hexdigest())
        return ref

    @_fail_closed
    def read_json(self, ref):
        with self._opened(ref, self.limits.max_json_bytes) as (stream, stamp):
            self._reserve_read(ref.size_bytes)
            data = stream.read(ref.size_bytes)
            self._charge(len(data))
            need(len(data) <= self.limits.max_json_bytes, 'JSON byte cap')
        self._commit(ref, stamp, len(data), hashlib.sha256(data).hexdigest())
        def unique(pairs):
            value = {}
            for key, item in pairs:
                need(key not in value, 'Duplicate JSON key')
                value[key] = item
            return value
        def finite_float(text):
            value = float(text)
            need(math.isfinite(value), 'Nonfinite JSON float')
            return value
        def bad_constant(text):
            raise ValueError('Nonfinite JSON constant ' + text)
        value = json.loads(data.decode('utf-8'), object_pairs_hook=unique,
                           parse_float=finite_float, parse_constant=bad_constant)
        need(type(value) is dict, 'JSON metadata object required')
        self._guard()
        return value

    def _csv_line(self, raw):
        need(raw.endswith(b'\n') and len(raw) <= self.limits.max_line_bytes
             and len(raw) <= self.limits.max_csv_buffer_bytes, 'Complete bounded physical CSV line')
        values = list(csv.reader(io.StringIO(raw.decode('utf-8'), newline=''), strict=True))
        need(len(values) == 1 and 0 < len(values[0]) <= self.limits.max_fields, 'Single CSV row/field cap')
        row = values[0]
        need(all(len(value.encode('utf-8')) <= self.limits.max_field_bytes
                 and not any(ord(c) < 32 for c in value) for value in row), 'No multiline/control/oversized CSV field')
        return row

    @_fail_closed
    def index_csv(self, ref, *, candidate_id, kind):
        expected = csv_fields(candidate_id, kind)
        need(len(expected) <= self.limits.max_fields, 'Header field cap')
        digest, size, entries = hashlib.sha256(), 0, {}
        with self._opened(ref, self.limits.max_csv_bytes) as (stream, stamp):
            self._reserve_read(ref.size_bytes)
            first = stream.readline(min(self.limits.max_line_bytes + 1, ref.size_bytes))
            self._charge(len(first)); digest.update(first); size += len(first)
            header = tuple(self._csv_line(first))
            need(len(header) == len(set(header)) and set(header) == set(expected), 'Exact producer CSV header')
            while size < ref.size_bytes:
                offset = stream.tell()
                raw = stream.readline(min(self.limits.max_line_bytes + 1, ref.size_bytes - size))
                need(raw, 'Unexpected CSV EOF')
                self._charge(len(raw)); digest.update(raw); size += len(raw)
                need(len(entries) < self.limits.max_csv_rows
                     and self.index_entries < self.limits.max_index_entries, 'CSV row/index entry cap')
                values = self._csv_line(raw)
                need(len(values) == len(header), 'CSV field count')
                row = dict(zip(header, values))
                key = _key(row)
                need(key not in entries, 'Duplicate canonical target K')
                entries[key] = (offset, len(raw), hashlib.sha256(raw).hexdigest())
                self.index_entries += 1
        need(entries, 'Nonempty full CSV population')
        self._commit(ref, stamp, size, digest.hexdigest())
        return CsvRowIndex(self, ref, candidate_id, kind, header, entries)

    @_fail_closed
    def _indexed_row(self, index, key):
        with self.open_index_rows(index) as cursor:
            return cursor.row(key)

    @contextmanager
    def open_index_rows(self, index):
        try:
            need(type(index) is CsvRowIndex and index._reader is self, 'Index owned by this reader')
            with self._opened(index.ref, self.limits.max_csv_bytes) as (stream, _):
                cursor = _IndexedRowCursor(self, index, stream)
                try:
                    yield cursor
                finally:
                    cursor.closed = True
        except BaseException:
            self.failed = True
            raise

    @_fail_closed
    def _cursor_row(self, cursor, key):
        need(type(cursor) is _IndexedRowCursor and cursor.reader is self and not cursor.closed,
             'Active owned row cursor required')
        index, stream = cursor.index, cursor.stream
        need(type(index) is CsvRowIndex and index._reader is self and type(key) is ModelNeutralKey,
             'Index/key owned by this reader')
        need(key in index._entries, 'Unknown target key')
        offset, length, digest = index._entries[key]
        self._reserve_read(length)
        stream.seek(offset)
        raw = stream.read(length)
        self._charge(len(raw))
        need(len(raw) == length and hashlib.sha256(raw).hexdigest() == digest, 'Indexed row bytes changed')
        values = self._csv_line(raw)
        need(len(values) == len(index.header), 'Indexed row field count')
        row = dict(zip(index.header, values))
        need(_key(row) == key, 'Indexed row identity changed')
        return row  # Strings unchanged, including null ''. Normalization belongs to producer adapters.

    @_fail_closed
    def verify_unchanged(self):
        need(self._refs and set(self._refs) == set(self._stamps), 'Every opened file must have complete SHA verification')
        for ref in tuple(self._refs.values()):
            self.verify_file(ref)
        need(self.open_files == 0, 'No outstanding file handles')
        return dict(files=len(self._refs), bytes_read=self.bytes_read, index_entries=self.index_entries,
                    elapsed_seconds=self._guard(), source_and_input_hashes_rechecked=True,
                    external_freeze_authority=False)

    def close(self):
        self.closed = True  # Each operation already closes its own handle in finally.

    def __enter__(self):
        self._guard()
        return self

    def __exit__(self, *unused):
        self.close()
