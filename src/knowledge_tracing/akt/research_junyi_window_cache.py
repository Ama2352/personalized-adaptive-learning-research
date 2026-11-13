"""Cache window Junyi theo shard hữu hạn, không pickle hoặc full-corpus RAM.

Cache giữ nguyên kiểu record/geometry. Prediction window không chứa current
targets; UnseenTarget giữ event gốc để xuất OOV nhưng không được đưa vào model.
"""
from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import time
import uuid
import zipfile

import numpy as np

from ..shared_kt import CausalSequenceInputs
from .config import PROJECT_ROOT
from .filesystem import publish_new_file
from .research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from .types import KTEvent, TrainingWindow, UnseenTarget, WindowInputs

CACHE_BASE = PROJECT_ROOT/'artifacts/akt/window-cache'
KIND = 'JUNYI_ENCODED_WINDOW_CACHE_V1'
_INPUT_FIELDS = ('item_ids', 'timestamps', 'prior_responses', 'source_rows')
_WINDOW_FIELDS = ('target_mask', 'global_ranks', 'history_available', 'history_used', 'context_reset')
_FIELDS = (*_INPUT_FIELDS, *_WINDOW_FIELDS, 'targets')
_DTYPES = {name: np.dtype('int64') for name in _FIELDS}
_DTYPES.update(prior_responses=np.dtype('int8'), targets=np.dtype('int8'),
               target_mask=np.dtype('bool'), context_reset=np.dtype('bool'))


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def _write_json(path, value):
    temporary = path.with_name('.publish-'+uuid.uuid4().hex+'.tmp')
    with temporary.open('xb') as stream:
        stream.write(_json_bytes(value)); stream.flush(); os.fsync(stream.fileno())
    publish_new_file(temporary, path)


def _owned_root(path):
    absolute = Path(path).absolute()
    base = CACHE_BASE.absolute()
    _need(absolute != base and absolute.is_relative_to(base), 'Owned Junyi window-cache path required')
    current = absolute
    while current != current.parent:
        _need(not current.is_symlink() and not getattr(current, 'is_junction', lambda: False)(),
              'Cache path alias rejected')
        current = current.parent
    _need(absolute.resolve() == absolute, 'Physical cache path required')
    return absolute


def window_cache_key(view, encoding, source_data_sha256, *, expected_target_rows):
    _need(type(view) is JunyiPhaseView and type(encoding) is JunyiResearchEncoding,
          'Typed Junyi phase and encoding required')
    encoding.assert_for(view)
    _need(type(source_data_sha256) is str and len(source_data_sha256) == 64
          and all(c in '0123456789abcdef' for c in source_data_sha256), 'Source data SHA256 required')
    _need(type(expected_target_rows) is int and 0 < expected_target_rows < 2**63,
          'Expected source target count required')
    return _key_metadata(view, encoding, source_data_sha256, expected_target_rows)


def _key_metadata(view, encoding, source_data_sha256, expected_target_rows):
    return dict(kind=KIND, phase_view_identity=view.identity, encoding_identity=encoding.identity,
        source_data_sha256=source_data_sha256, phase_scope=view.scope,
        expected_target_rows=expected_target_rows, context=100, target_block=100, max_length=200)


def _encoding_guard(encoding, key):
    actual = hashlib.sha256(json.dumps(encoding._payload(), sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    _need(actual == encoding.identity == key['encoding_identity'], 'Window-cache encoding content changed')


def _parts(record, view, encoding, allowed_users):
    if type(record) is UnseenTarget:
        event = record.event
        _need(not view.optimization and type(event) is KTEvent and event.user_id in allowed_users
              and type(record.global_rank) is int and record.global_rank >= 0
              and type(event.correct) is int and event.correct in (0, 1)
              and type(event.suggested) is int and event.suggested in (0, 1)
              and type(event.fold) is int and event.fold in (0, 1, 2, 3)
              and type(event.source_row) is int and event.source_row > 0
              and type(event.time_done) is int and event.time_done >= 0
              and type(event.exercise) is str and event.exercise
              and event.exercise not in encoding.native.vocabulary.values, 'Invalid unseen target')
        return dict(kind='unseen', event=asdict(event), global_rank=record.global_rank), {}, (
            (record.global_rank, event.time_done, event.source_row),)
    training = type(record) is TrainingWindow
    _need(training == view.optimization and (training or type(record) is WindowInputs),
          'Cache record type differs from phase')
    window = record.window if training else record
    inputs = window.inputs
    size = len(inputs.item_ids)
    _need(1 <= size <= 200 and len(inputs.user_ids) == size and len(set(inputs.user_ids)) == 1
          and inputs.user_ids[0] in allowed_users and inputs.concept_ids is None
          and type(inputs.sequence_offsets) is np.ndarray and inputs.sequence_offsets.dtype.kind in 'iu'
          and np.array_equal(inputs.sequence_offsets, [0, size]), 'Native single-learner window required')
    arrays = {name: getattr(inputs, name) for name in _INPUT_FIELDS}
    arrays.update({name: getattr(window, name) for name in _WINDOW_FIELDS})
    for name, value in arrays.items():
        expected = 'b' if name in ('target_mask', 'context_reset') else 'iu'
        _need(type(value) is np.ndarray and value.shape == (size,) and value.dtype.kind in expected,
              'Numeric native window arrays must align')
        _need(value.dtype.kind != 'u' or int(value.max()) <= np.iinfo(np.int64).max,
              'Window integer value exceeds lossless int64 packing')
    _need(np.all((arrays['item_ids'] >= 0) & (arrays['item_ids'] < len(encoding.native.vocabulary.values)))
          and arrays['prior_responses'][0] == -1 and np.isin(arrays['prior_responses'][1:], (0, 1)).all(),
          'Invalid fitted item or causal prior response')
    mask = arrays['target_mask']
    _need(mask.any() and np.all(mask[np.flatnonzero(mask)[0]:])
          and np.all(arrays['source_rows'] > 0) and len(set(arrays['source_rows'].tolist())) == size
          and np.all(arrays['timestamps'] >= 0) and np.all(arrays['global_ranks'] >= 0)
          and np.all(np.diff(arrays['global_ranks']) == 1)
          and np.array_equal(arrays['history_used'], np.arange(size))
          and np.all(arrays['history_available'] >= arrays['history_used']), 'Native window geometry mismatch')
    chronology = tuple(zip(arrays['timestamps'].tolist(), arrays['source_rows'].tolist()))
    _need(all(left < right for left, right in zip(chronology, chronology[1:])), 'Window chronology mismatch')
    _need(type(window.window_id) is str and bool(window.window_id), 'Window identity required')
    if training:
        _need(type(record.targets) is np.ndarray and record.targets.shape == (size,)
              and record.targets.dtype.kind in 'iu' and np.isin(record.targets, (0, 1)).all(),
              'Training targets required')
        arrays['targets'] = record.targets
    metadata = dict(kind='training' if training else 'prediction', user_id=inputs.user_ids[0],
        window_id=window.window_id, dtypes={name: value.dtype.str for name, value in arrays.items()},
        offsets_dtype=inputs.sequence_offsets.dtype.str)
    targets = tuple((int(window.global_ranks[i]), *chronology[i]) for i in np.flatnonzero(mask))
    return metadata, arrays, targets


class _SequenceAudit:
    def __init__(self, view):
        self.positions = {user: index for index, user in enumerate(view.users)}
        self.position = -1
        self.next_rank = 0
        self.previous_time_row = None
        self.records = self.windows = self.unseen = self.targets = self.tokens = 0

    def add(self, metadata, arrays, targets):
        unseen = metadata['kind'] == 'unseen'
        user = metadata['event']['user_id'] if unseen else metadata['user_id']
        position = self.positions[user]
        if position != self.position:
            _need(position == self.position+1, 'Cache learner order/coverage mismatch')
            self.position = position; self.next_rank = 0; self.previous_time_row = None
        for rank, timestamp, source_row in targets:
            _need(rank == self.next_rank and (self.previous_time_row is None
                  or self.previous_time_row < (timestamp, source_row)), 'Target rank/chronology mismatch')
            self.next_rank += 1; self.previous_time_row = timestamp, source_row
        self.records += 1; self.unseen += int(unseen); self.windows += int(not unseen)
        self.targets += len(targets); self.tokens += len(arrays.get('item_ids', ()))

    def summary(self):
        _need(self.position == len(self.positions)-1, 'Incomplete source learner coverage')
        return dict(records=self.records, windows=self.windows, unseen_targets=self.unseen,
                    target_rows=self.targets, window_tokens=self.tokens, learners=self.position+1)


def _save_shard(path, records, *, compressed):
    offsets = [0]
    packed = {name: [] for name in _FIELDS}
    metadata = []
    for meta, arrays in records:
        size = len(arrays.get('item_ids', ()))
        offsets.append(offsets[-1]+size); metadata.append(meta)
        for name in _FIELDS:
            value = arrays.get(name, np.full(size, -1, dtype=np.int8))
            packed[name].append(np.asarray(value, dtype=_DTYPES[name]))
    values = {name: np.concatenate(parts) for name, parts in packed.items()}
    values.update(offsets=np.asarray(offsets, dtype=np.int64),
                  metadata=np.frombuffer(_json_bytes(metadata), dtype=np.uint8))
    writer = np.savez_compressed if compressed else np.savez
    with path.open('xb') as stream:
        writer(stream, **values); stream.flush(); os.fsync(stream.fileno())
    return dict(name=path.name, sha256=_sha(path), bytes=path.stat().st_size,
                records=len(records), tokens=offsets[-1])


def build_junyi_window_cache(cache_root, records, *, view, encoding, source_data_sha256,
                             expected_target_rows, shard_records=256, max_shard_tokens=51200, compressed=False):
    """Tiêu thụ stream một lần; lỗi giữ failure, không công bố COMPLETE."""
    key = window_cache_key(view, encoding, source_data_sha256, expected_target_rows=expected_target_rows)
    _need(type(shard_records) is int and 1 <= shard_records <= 1024
          and type(max_shard_tokens) is int and 200 <= max_shard_tokens <= 204800
          and type(compressed) is bool, 'Explicit bounded shard limits required')
    root = _owned_root(cache_root)
    root.mkdir(parents=True, exist_ok=False)
    _write_json(root/'BUILD_REQUEST.json', dict(key=key, shard_records=shard_records,
        max_shard_tokens=max_shard_tokens, compressed=compressed))
    audit = _SequenceAudit(view); pending = []; tokens = 0; shards = []
    try:
        for record in records:
            _encoding_guard(encoding, key)
            meta, arrays, targets = _parts(record, view, encoding, audit.positions)
            size = len(arrays.get('item_ids', ()))
            if pending and (len(pending) >= shard_records or tokens+size > max_shard_tokens):
                shards.append(_save_shard(root/f'shard-{len(shards):06d}.npz', pending, compressed=compressed))
                pending = []; tokens = 0
            audit.add(meta, arrays, targets)
            pending.append((meta, {name: value.copy() for name, value in arrays.items()})); tokens += size
        if pending:
            shards.append(_save_shard(root/f'shard-{len(shards):06d}.npz', pending, compressed=compressed))
        summary = audit.summary()
        _need(summary['target_rows'] == expected_target_rows, 'Truncated source target population')
        _need(key == window_cache_key(view, encoding, source_data_sha256, expected_target_rows=expected_target_rows),
              'Source phase/encoding changed during cache build')
        manifest = dict(status='COMPLETE', key=key, summary=summary, shards=shards,
            shard_records=shard_records, max_shard_tokens=max_shard_tokens, compressed=compressed)
        _write_json(root/'manifest.json', manifest)
        manifest_sha = _sha(root/'manifest.json')
        _write_json(root/'COMPLETE.json', dict(kind=KIND, manifest_sha256=manifest_sha))
        return dict(status='COMPLETE', manifest_sha256=manifest_sha, summary=summary,
                    cache_key_sha256=hashlib.sha256(_json_bytes(key)).hexdigest())
    except BaseException as error:
        _write_json(root/'failure.json', dict(type=type(error).__name__, error=str(error)))
        raise


def _load_shard(path, entry, manifest):
    _need(not path.is_symlink() and path.stat().st_size == entry['bytes'] <= 64*1024**2
          and _sha(path) == entry['sha256'], 'Window shard bytes/SHA mismatch')
    with zipfile.ZipFile(path) as archive:
        _need(sum(item.file_size for item in archive.infolist()) <= 32*1024**2, 'Window shard expansion limit')
    with np.load(path, allow_pickle=False) as saved:
        _need(set(saved.files) == set(_FIELDS) | {'offsets', 'metadata'}, 'Window shard fields mismatch')
        arrays = {name: saved[name] for name in saved.files}
    metadata = arrays.pop('metadata')
    _need(metadata.dtype == np.uint8 and metadata.ndim == 1 and metadata.size <= 2*1024**2,
          'Bounded JSON shard metadata required')
    records = json.loads(metadata.tobytes())
    offsets = arrays.pop('offsets')
    _need(type(records) is list and len(records) == entry['records'] <= manifest['shard_records']
          and offsets.dtype == np.int64 and offsets.shape == (len(records)+1,) and offsets[0] == 0
          and np.all(np.diff(offsets) >= 0) and offsets[-1] == entry['tokens'] <= manifest['max_shard_tokens'],
          'Window shard record/offset limits mismatch')
    _need(all(value.dtype == _DTYPES[name] and value.shape == (int(offsets[-1]),)
              for name, value in arrays.items()), 'Packed window array geometry mismatch')
    for index, meta in enumerate(records):
        begin, end = int(offsets[index]), int(offsets[index+1])
        if meta['kind'] == 'unseen':
            _need(begin == end, 'Unseen target cannot contain model arrays')
            yield UnseenTarget(KTEvent(**meta['event']), meta['global_rank'])
            continue
        _need(meta['kind'] in ('training', 'prediction') and 1 <= end-begin <= 200,
              'Known window metadata mismatch')
        names = set(_FIELDS) if meta['kind'] == 'training' else set(_FIELDS)-{'targets'}
        _need(set(meta['dtypes']) == names, 'Window label/array metadata mismatch')
        restored = {}
        for name in names:
            dtype = np.dtype(meta['dtypes'][name])
            _need(dtype.kind in ('b' if name in ('target_mask', 'context_reset') else 'iu')
                  and dtype.itemsize <= 8, 'Object/noninteger cache dtype rejected')
            restored[name] = arrays[name][begin:end].astype(dtype, copy=True)
        if meta['kind'] == 'prediction':
            _need(np.all(arrays['targets'][begin:end] == -1), 'Prediction cache cannot contain loss labels')
        offset_dtype = np.dtype(meta['offsets_dtype'])
        _need(offset_dtype.kind in 'iu' and offset_dtype.itemsize <= 8, 'Invalid sequence offset dtype')
        inputs = CausalSequenceInputs(*(restored[name] for name in _INPUT_FIELDS),
            np.asarray([0, end-begin], dtype=offset_dtype), (meta['user_id'],)*(end-begin), None)
        window = WindowInputs(inputs, *(restored[name] for name in _WINDOW_FIELDS), meta['window_id'])
        yield TrainingWindow(window, restored['targets']) if meta['kind'] == 'training' else window


def iter_junyi_window_cache(cache_root, *, view, encoding, source_data_sha256,
                            expected_target_rows, expected_manifest_sha256):
    """Factory dùng lại qua lambda; chỉ giữ một shard trong RAM mỗi lần đọc."""
    key = window_cache_key(view, encoding, source_data_sha256, expected_target_rows=expected_target_rows)
    root = _owned_root(cache_root)
    complete = json.loads((root/'COMPLETE.json').read_text())
    _need(complete == dict(kind=KIND, manifest_sha256=expected_manifest_sha256)
          and _sha(root/'manifest.json') == expected_manifest_sha256, 'Incomplete or changed window-cache manifest')
    manifest = json.loads((root/'manifest.json').read_text())
    _need(manifest['status'] == 'COMPLETE' and manifest['key'] == key
          and type(manifest['shard_records']) is int and 1 <= manifest['shard_records'] <= 1024
          and type(manifest['max_shard_tokens']) is int and 200 <= manifest['max_shard_tokens'] <= 204800,
          'Foreign phase/encoding/source or unbounded cache')
    audit = _SequenceAudit(view)
    for index, entry in enumerate(manifest['shards']):
        _need(entry['name'] == f'shard-{index:06d}.npz', 'Noncanonical shard path')
        for record in _load_shard(root/entry['name'], entry, manifest):
            _encoding_guard(encoding, key)
            meta, arrays, targets = _parts(record, view, encoding, audit.positions)
            audit.add(meta, arrays, targets)
            yield record
    summary = audit.summary()
    _need(summary == manifest['summary'] and summary['target_rows'] == expected_target_rows
          and key == window_cache_key(view, encoding, source_data_sha256, expected_target_rows=expected_target_rows),
          'Truncated cache or changed phase/encoding')


def _session_header(view, encoding):
    phase_headers = []
    for phase in (view, encoding.fit_view):
        roles = phase.roles
        phase_headers.append((id(phase), id(roles), id(phase.users), phase.scope,
            phase.identity, phase.expected_roles_identity, type(roles.outer_fold), roles.outer_fold,
            type(roles.seed), roles.seed,
            roles.algorithm, roles.rounding,
            *(id(getattr(roles, name)) for name in ('train_users', 'selection_users',
                                                  'calibration_users', 'outer_validation_users'))))
    native = encoding.native
    return (tuple(phase_headers), id(encoding), id(native), id(native.vocabulary),
            id(native.vocabulary.values), id(native.train_support_students), encoding.identity)


@dataclass(frozen=True)
class JunyiWindowCacheSession:
    """Opt-in: strict admission đầy đủ một lần, rồi kiểm SHA mỗi epoch.

Mặc định duyệt đủ strict stream. Handoff CPU có external SHA phải khớp nguồn
validator, key, manifest và từng shard byte trước khi tái dùng kết quả kiểm.
Hot iterator giữ nguyên record, kiểm key/encoding và SHA/bytes từng shard.
"""
    cache_root: Path
    view: JunyiPhaseView
    encoding: JunyiResearchEncoding
    source_data_sha256: str
    expected_target_rows: int
    expected_manifest_sha256: str
    prefetch: bool = False
    admission_receipt: Path | None = None
    expected_admission_sha256: str | None = None
    strict_records_verified: int = field(init=False)
    strict_seconds: float = field(init=False)
    _root: Path = field(init=False, repr=False)
    _key_bytes: bytes = field(init=False, repr=False)
    _header: tuple = field(init=False, repr=False)
    _roots: tuple = field(init=False, repr=False)
    _shards: tuple = field(init=False, repr=False)
    _limits: tuple = field(init=False, repr=False)
    _summary: tuple = field(init=False, repr=False)

    def __post_init__(self):
        _need(type(self.prefetch) is bool, 'Boolean shard prefetch control required')
        started = time.monotonic()
        root = _owned_root(self.cache_root)
        self._check_control_files(root)
        key = window_cache_key(self.view, self.encoding, self.source_data_sha256,
                               expected_target_rows=self.expected_target_rows)
        _need((self.admission_receipt is None)==(self.expected_admission_sha256 is None),
              'CPU admission receipt and external SHA required together')
        if self.admission_receipt is None:
            verified = 0
            for _ in iter_junyi_window_cache(root, view=self.view, encoding=self.encoding,
                    source_data_sha256=self.source_data_sha256, expected_target_rows=self.expected_target_rows,
                    expected_manifest_sha256=self.expected_manifest_sha256):
                verified += 1
        else:
            verified = _verify_cpu_admission(self, root, key)
        self._check_control_files(root)
        manifest = json.loads((root/'manifest.json').read_text())
        _need(manifest['summary']['records'] == verified and manifest['key'] == key,
              'Window-cache admission population/key changed')
        roots = [self.view, self.encoding, self.encoding.native, self.encoding.native.vocabulary,
                 self.encoding.native.vocabulary.values, self.encoding.native.train_support_students]
        for phase in (self.view, self.encoding.fit_view):
            roots.extend((phase, phase.roles, phase.users,
                *(getattr(phase.roles, name) for name in ('train_users', 'selection_users',
                    'calibration_users', 'outer_validation_users'))))
        object.__setattr__(self, '_roots', tuple(roots))
        object.__setattr__(self, '_root', root)
        object.__setattr__(self, '_key_bytes', _json_bytes(key))
        object.__setattr__(self, '_header', _session_header(self.view, self.encoding))
        object.__setattr__(self, '_shards', tuple(tuple(entry[name] for name in
            ('name', 'sha256', 'bytes', 'records', 'tokens')) for entry in manifest['shards']))
        object.__setattr__(self, '_limits', (manifest['shard_records'], manifest['max_shard_tokens']))
        object.__setattr__(self, '_summary', tuple(sorted(manifest['summary'].items())))
        object.__setattr__(self, 'strict_records_verified', verified)
        object.__setattr__(self, 'strict_seconds', time.monotonic()-started)

    def _check_control_files(self, root):
        _need(all(not (root/name).is_symlink() and not getattr(root/name, 'is_junction', lambda: False)()
                  for name in ('manifest.json', 'COMPLETE.json')), 'Cache control-file alias rejected')
        _need(_sha(root/'manifest.json') == self.expected_manifest_sha256
              and json.loads((root/'COMPLETE.json').read_text()) == dict(kind=KIND,
                  manifest_sha256=self.expected_manifest_sha256), 'Cache control files changed')

    def assert_boundary(self):
        _need(_owned_root(self.cache_root) == self._root
              and _session_header(self.view, self.encoding) == self._header,
              'Window-cache session phase/encoding header changed')
        self._check_control_files(self._root)
        # Roles/groups đã strict-admit và tuple frozen còn nguyên tham chiếu.
        # Chỉ phần support mutable cần content hash ở mỗi epoch boundary.
        key = _key_metadata(self.view, self.encoding, self.source_data_sha256, self.expected_target_rows)
        _encoding_guard(self.encoding, key)
        _need(_json_bytes(key) == self._key_bytes, 'Window-cache session key changed')

    def iter_windows(self):
        """Factory cho epoch, không chạy lại strict geometry audit từng record."""
        self.assert_boundary()
        records = tokens = targets = 0
        limits = dict(shard_records=self._limits[0], max_shard_tokens=self._limits[1])
        def read(pin):
            entry = dict(zip(('name', 'sha256', 'bytes', 'records', 'tokens'), pin))
            return _load_shard(self._root/entry['name'], entry, limits)

        def shards():
            if not self.prefetch:
                for pin in self._shards:
                    yield read(pin)
                return
            # Chỉ một shard tương lai. Reader không dùng RNG của model/sampler.
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1,thread_name_prefix='akt-shard') as executor:
                pending=None
                for index,pin in enumerate(self._shards):
                    current=list(read(pin)) if pending is None else pending.result()
                    pending=None
                    if index+1<len(self._shards):
                        pending=executor.submit(lambda next_pin: list(read(next_pin)),self._shards[index+1])
                    yield current

        for shard in shards():
            for record in shard:
                records += 1
                if type(record) is UnseenTarget:
                    targets += 1
                else:
                    window = record.window if type(record) is TrainingWindow else record
                    tokens += len(window.inputs.item_ids)
                    targets += int(window.target_mask.sum())
                yield record
        summary = dict(self._summary)
        _need(records == summary['records'] and tokens == summary['window_tokens']
              and targets == summary['target_rows'] == self.expected_target_rows,
              'Admitted window-cache replay population changed')
        self.assert_boundary()



def _admission_sources():
    names=('research_junyi_window_cache.py','research_junyi_data.py','windows.py','types.py','encoding.py',
           'config.py','../shared_kt.py')
    return {name:hashlib.sha256((Path(__file__).parent/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
            for name in names}


def write_cpu_admission(session, path):
    """Ghi sau full strict CPU pass, giữ pin từng byte để GPU chỉ kiểm SHA."""
    _need(type(session) is JunyiWindowCacheSession and session.admission_receipt is None,
          'Fresh full strict session required to produce CPU admission')
    session.assert_boundary()
    manifest=json.loads((session._root/'manifest.json').read_text())
    for pin in manifest['shards']:
        shard=session._root/pin['name']
        _need(shard.stat().st_size==pin['bytes'] and _sha(shard)==pin['sha256'],
              'Shard changed after strict CPU admission')
    payload=dict(kind='JUNYI_CPU_WINDOW_ADMISSION_V1',key=json.loads(session._key_bytes),
        manifest_sha256=session.expected_manifest_sha256,summary=dict(session._summary),
        shards=manifest['shards'],validator_sources=_admission_sources(),
        strict_records_verified=session.strict_records_verified)
    with Path(path).open('x',encoding='utf-8') as stream:
        json.dump(payload,stream,sort_keys=True,indent=2)
        stream.write('\n')


def _verify_cpu_admission(session, root, key):
    path=Path(session.admission_receipt)
    _need(not path.is_symlink() and not getattr(path,'is_junction',lambda:False)()
          and path.stat().st_size<=4*1024**2, 'Bounded regular CPU admission required')
    raw=path.read_bytes()
    _need(hashlib.sha256(raw).hexdigest()==session.expected_admission_sha256,
          'CPU admission external SHA mismatch')
    value=json.loads(raw)
    _need(set(value)=={'kind','key','manifest_sha256','summary','shards','validator_sources','strict_records_verified'}
          and value['kind']=='JUNYI_CPU_WINDOW_ADMISSION_V1', 'CPU admission schema mismatch')
    manifest=json.loads((root/'manifest.json').read_text())
    _need(value['key']==key and value['manifest_sha256']==session.expected_manifest_sha256
          and value['summary']==manifest['summary'] and value['shards']==manifest['shards']
          and value['validator_sources']==_admission_sources(), 'CPU admission data/source binding mismatch')
    _need(type(value['strict_records_verified']) is int
          and value['strict_records_verified']==manifest['summary']['records'], 'CPU admission count mismatch')
    for pin in value['shards']:
        _need(type(pin['name']) is str and Path(pin['name']).name==pin['name']
              and ':' not in pin['name'] and '\\' not in pin['name'], 'CPU admission shard path invalid')
        shard=root/pin['name']
        _need(not shard.is_symlink() and not getattr(shard,'is_junction',lambda:False)()
              and shard.stat().st_size==pin['bytes'] and _sha(shard)==pin['sha256'],
              'CPU admission shard bytes changed')
    return value['strict_records_verified']
