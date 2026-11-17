"""Shard xác suất không nhãn và nối metadata CPU theo cửa sổ đã ghim.

Không import Torch. Caller phải tiêu thụ iterator tới cuối để nghiệm thu coverage.
Chỉ manifest hoàn chỉnh được xem là artifact đã công bố.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from .filesystem import publish_new_file
from .prediction_batch import iter_prepared_predictions_batched
from .research_junyi_graph_cache import window_key
from .types import KTEvent, UnseenTarget, WindowInputs


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _hash(value):
    return (type(value) is str and len(value) == 64
            and all(char in '0123456789abcdef' for char in value))


@dataclass(frozen=True)
class NumericBinding:
    variant: str
    checkpoint_id: str
    checkpoint_sha256: str
    phase_sha256: str
    encoding_sha256: str
    window_manifest_sha256: str
    source_sha256: str

    def validate(self):
        if (self.variant not in ('A0', 'A1', 'A2', 'A3')
                or type(self.checkpoint_id) is not str or not self.checkpoint_id
                or any(not _hash(value) for name, value in asdict(self).items()
                       if name.endswith('_sha256'))):
            raise ValueError('invalid numeric prediction binding')


@dataclass(frozen=True)
class NumericWindow:
    window_id: str
    key: str
    width: int
    targets: int

    @classmethod
    def from_window(cls, window):
        if not isinstance(window, WindowInputs):
            raise ValueError('numeric identity requires WindowInputs')
        return cls(window.window_id, window_key(window), len(window.target_mask),
                   int(np.count_nonzero(window.target_mask)))

    def validate(self):
        if (type(self.window_id) is not str or not self.window_id or not _hash(self.key)
                or type(self.width) is not int or not 1 <= self.width <= 200
                or type(self.targets) is not int or not 1 <= self.targets <= self.width):
            raise ValueError('invalid numeric window identity')


@dataclass(frozen=True)
class NumericShard:
    manifest_path: Path
    manifest_sha256: str


def _root(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError('explicit physical absolute artifact root required')
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part, 'is_junction', lambda: False)():
            raise ValueError('artifact aliases rejected')
    return path


def write_numeric_shard(root, name, identities, probabilities, *, binding, shard_index):
    """Ghi tối đa128 cửa sổ. Đầu vào GPU không có outcome hoặc learner metadata."""
    binding.validate()
    root = _root(root)
    if (type(name) is not str or not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in name)
            or type(shard_index) is not int or shard_index < 0):
        raise ValueError('invalid numeric shard name/index')
    identities, probabilities = tuple(identities), tuple(probabilities)
    if not 1 <= len(identities) <= 128 or len(identities) != len(probabilities):
        raise ValueError('numeric shard window count mismatch')
    arrays = {}
    for index, (identity, values) in enumerate(zip(identities, probabilities)):
        if not isinstance(identity, NumericWindow):
            raise ValueError('typed numeric window required')
        identity.validate()
        if (not isinstance(values, np.ndarray) or values.dtype != np.dtype('float64')
                or values.shape != (identity.width,) or not np.isfinite(values).all()
                or np.any(values < 0) or np.any(values > 1)):
            raise ValueError('finite float64 probability vector required')
        arrays[f'p{index}'] = values
    if len({identity.key for identity in identities}) != len(identities):
        raise ValueError('repeated numeric window')
    root.mkdir(parents=True, exist_ok=True)
    output, manifest = root / f'{name}.npz', root / f'{name}.json'
    if output.exists() or manifest.exists():
        raise FileExistsError('numeric artifact is immutable')
    temporary = root / f'{name}.partial'
    with temporary.open('xb') as stream:
        np.savez(stream, **arrays)
        stream.flush()
        os.fsync(stream.fileno())
    publish_new_file(temporary, output)
    payload = dict(kind='JUNYI_NUMERIC_PREDICTIONS_V1', binding=asdict(binding),
                   shard_index=shard_index, windows=[asdict(item) for item in identities],
                   payload=output.name, payload_sha256=_sha(output))
    temporary = root / f'{name}.manifest.partial'
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    publish_new_file(temporary, manifest)
    return NumericShard(manifest, _sha(manifest))


def _read_shards(shards, binding):
    binding.validate()
    for expected_index, artifact in enumerate(shards):
        if not isinstance(artifact, NumericShard) or not _hash(artifact.manifest_sha256):
            raise ValueError('typed pinned numeric shard required')
        path = Path(artifact.manifest_path)
        _root(path.parent)
        if _sha(path) != artifact.manifest_sha256:
            raise ValueError('numeric manifest integrity mismatch')
        manifest = json.loads(path.read_text(encoding='utf-8'))
        if (manifest['kind'] != 'JUNYI_NUMERIC_PREDICTIONS_V1'
                or manifest['binding'] != asdict(binding)
                or manifest['shard_index'] != expected_index
                or manifest['payload'] != path.with_suffix('.npz').name):
            raise ValueError('numeric binding/order mismatch')
        payload = path.with_suffix('.npz')
        if _sha(payload) != manifest['payload_sha256']:
            raise ValueError('numeric payload integrity mismatch')
        identities = tuple(NumericWindow(**item) for item in manifest['windows'])
        if not 1 <= len(identities) <= 128:
            raise ValueError('bounded numeric shard required')
        with np.load(payload, allow_pickle=False) as data:
            if set(data.files) != {f'p{i}' for i in range(len(identities))}:
                raise ValueError('numeric payload keys mismatch')
            for index, identity in enumerate(identities):
                identity.validate()
                values = data[f'p{index}']
                if (values.dtype != np.dtype('float64') or values.shape != (identity.width,)
                        or not np.isfinite(values).all() or np.any(values < 0) or np.any(values > 1)):
                    raise ValueError('invalid numeric payload probabilities')
                yield identity, values


def iter_numeric_prediction_records(adapter, prepared, shards, *, binding,
                                    expected_records, expected_windows, expected_targets):
    """Nối CPU qua iterator chuẩn, giữ OOV, warm-up và thứ tự; không gọi model.

Adapter chỉ cung cấp config/encoding/checkpoint. Đây là replay artifact tường minh,
không phải RefitCalibrationPredictor và không thay thế native inference admission.
"""
    if any(type(value) is not int or value < 0
           for value in (expected_records, expected_windows, expected_targets)):
        raise ValueError('exact nonnegative coverage counts required')
    if getattr(adapter, 'checkpoint_id', None) != binding.checkpoint_id:
        raise ValueError('CPU adapter checkpoint mismatch')
    source = iter(_read_shards(shards, binding))
    windows_seen = targets_seen = records_seen = 0

    def predict(windows):
        nonlocal windows_seen, targets_seen
        result = []
        for window in windows:
            item = next(source, None)
            if item is None or item[0] != NumericWindow.from_window(window):
                raise ValueError('numeric windows missing, reordered or changed')
            windows_seen += 1
            targets_seen += item[0].targets
            result.append(item[1])
        return result

    replay = SimpleNamespace(config=adapter.config, encoding=adapter.encoding,
                             checkpoint_id=binding.checkpoint_id, predict_windows=predict)

    def checked_sidecar():
        for item in prepared:
            if isinstance(item, UnseenTarget):
                yield item
                continue
            window, targets = item
            indices = tuple(int(index) for index in np.flatnonzero(window.target_mask))
            targets = tuple(targets)
            if tuple(index for index, _ in targets) != indices:
                raise ValueError('CPU target sidecar indices mismatch')
            for index, event in targets:
                if (not isinstance(event, KTEvent)
                        or event.source_row != int(window.inputs.source_rows[index])
                        or event.user_id != window.inputs.user_ids[index]
                        or event.time_done != int(window.inputs.timestamps[index])
                        or event.correct not in (0, 1) or event.suggested not in (0, 1)):
                    raise ValueError('CPU target sidecar event mismatch')
            yield window, targets

    try:
        for record in iter_prepared_predictions_batched(replay, checked_sidecar()):
            records_seen += 1
            yield record
        if next(source, None) is not None:
            raise ValueError('unused numeric windows')
        if (records_seen, windows_seen, targets_seen) != (expected_records, expected_windows, expected_targets):
            raise ValueError('numeric prediction coverage mismatch')
    finally:
        source.close()
