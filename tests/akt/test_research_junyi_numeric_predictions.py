"""Parity tổng hợp của shard GPU không nhãn và nối CPU, không nạp Torch."""
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.prediction_batch import prepare_prediction_windows, iter_predictions_batched
from knowledge_tracing.akt.research_junyi_numeric_predictions import (
    NumericBinding, NumericWindow, iter_numeric_prediction_records, write_numeric_shard,
)
from knowledge_tracing.akt.types import KTEvent, LearnerEvents, UnseenTarget
from knowledge_tracing.shared_kt import StableVocabulary


class Adapter:
    config = SimpleNamespace(context=100, target_block=100, batch_size=128)
    encoding = ExerciseEncoding(StableVocabulary(('A', 'B')), {'A': 10, 'B': 5})
    checkpoint_id = 'checkpoint'

    def predict_windows(self, windows):
        return [np.asarray([.2 + .01 * int(value) for value in window.inputs.prior_responses],
                           dtype=np.float64) for window in windows]


def fixture(tmp_path, items, variant='A0'):
    learner = LearnerEvents('u', 0, tuple(KTEvent('u', item, i // 2, i + 1, i % 2, 0, 0)
                                        for i, item in enumerate(items)))
    adapter = Adapter()
    prepared = list(prepare_prediction_windows(adapter, [learner]))
    windows = [item[0] for item in prepared if not isinstance(item, UnseenTarget)]
    binding = NumericBinding(variant, 'checkpoint', *(['a' * 64] * 5))
    shards = []
    for index, start in enumerate(range(0, len(windows), 2)):
        batch = windows[start:start + 2]
        shards.append(write_numeric_shard(tmp_path, f'shard-{index}',
                      [NumericWindow.from_window(w) for w in batch], adapter.predict_windows(batch),
                      binding=binding, shard_index=index))
    kwargs = dict(binding=binding, expected_records=len(items), expected_windows=len(windows),
                  expected_targets=sum(item != 'X' for item in items))
    return adapter, learner, prepared, shards, kwargs


@pytest.mark.parametrize('variant', ['A0', 'A1', 'A2', 'A3'])
@pytest.mark.parametrize('items', [['A'], ['X'] * 3, ['A', 'X', 'B'],
                                  ['A', 'B'] * 151 + ['X'] + ['A'] * 110])
def test_parity_all_fields_and_coverage(tmp_path, items, variant):
    adapter, learner, prepared, shards, kwargs = fixture(tmp_path, items, variant)
    expected = list(iter_predictions_batched(adapter, [learner]))
    adapter.predict_windows = lambda _: pytest.fail('CPU join called model')
    assert list(iter_numeric_prediction_records(adapter, prepared, shards, **kwargs)) == expected


@pytest.mark.parametrize('field', ['variant', 'checkpoint_sha256', 'phase_sha256',
                                  'encoding_sha256', 'window_manifest_sha256', 'source_sha256'])
def test_binding_rejected(tmp_path, field):
    adapter, _, prepared, shards, kwargs = fixture(tmp_path, ['A'])
    kwargs['binding'] = replace(kwargs['binding'], **{field: 'A1' if field == 'variant' else 'b' * 64})
    with pytest.raises(ValueError, match='binding'):
        list(iter_numeric_prediction_records(adapter, prepared, shards, **kwargs))


@pytest.mark.parametrize('mode', ['missing', 'extra', 'reorder', 'window', 'checkpoint', 'coverage'])
def test_alignment_failures(tmp_path, mode):
    adapter, _, prepared, shards, kwargs = fixture(tmp_path, ['A'] * 501)
    if mode == 'missing':
        shards = shards[:-1]
    elif mode == 'extra':
        prepared = prepared[:-1]
    elif mode == 'reorder':
        shards = shards[::-1]
    elif mode == 'window':
        window, targets = prepared[0]
        prepared[0] = replace(window, window_id='changed'), targets
    elif mode == 'checkpoint':
        adapter.checkpoint_id = 'other'
    else:
        kwargs['expected_records'] += 1
    with pytest.raises(ValueError):
        list(iter_numeric_prediction_records(adapter, prepared, shards, **kwargs))


@pytest.mark.parametrize('mode', ['float32', 'nan', 'shape', 'range'])
def test_writer_rejects_invalid_probabilities(tmp_path, mode):
    adapter, _, prepared, _, kwargs = fixture(tmp_path, ['A'])
    window = prepared[0][0]
    values = {'float32': np.array([.2], dtype=np.float32), 'nan': np.array([np.nan]),
              'shape': np.array([.2, .3]), 'range': np.array([1.1])}[mode]
    with pytest.raises(ValueError, match='float64'):
        write_numeric_shard(tmp_path, 'bad', [NumericWindow.from_window(window)], [values],
                            binding=kwargs['binding'], shard_index=0)


@pytest.mark.parametrize('file', ['json', 'npz'])
def test_integrity_and_immutability(tmp_path, file):
    adapter, _, prepared, shards, kwargs = fixture(tmp_path, ['A'])
    with pytest.raises(FileExistsError):
        write_numeric_shard(tmp_path, 'shard-0', [NumericWindow.from_window(prepared[0][0])],
                            [np.array([.2])], binding=kwargs['binding'], shard_index=0)
    path = tmp_path / f'shard-0.{file}'
    path.write_bytes(path.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='integrity'):
        list(iter_numeric_prediction_records(adapter, prepared, shards, **kwargs))


def test_manifest_has_no_labels_or_learner_metadata(tmp_path):
    import json
    _, _, _, shards, _ = fixture(tmp_path, ['A'])
    manifest = json.loads(shards[0].manifest_path.read_text())
    assert set(manifest['windows'][0]) == {'window_id', 'key', 'width', 'targets'}
    assert 'correct' not in str(manifest) and 'user_id' not in str(manifest)


@pytest.mark.parametrize('field', ['source_row', 'user_id', 'time_done', 'correct', 'indices'])
def test_sidecar_event_alignment(tmp_path, field):
    adapter, _, prepared, shards, kwargs = fixture(tmp_path, ['A'])
    window, targets = prepared[0]
    index, event = targets[0]
    changes = dict(source_row=999, user_id='other', time_done=99, correct=4)
    targets = ((index + 1, event),) if field == 'indices' else ((index, replace(event, **{field: changes[field]})),)
    with pytest.raises(ValueError, match='sidecar'):
        list(iter_numeric_prediction_records(adapter, [(window, targets)], shards, **kwargs))


def test_no_torch_import_in_fresh_interpreter():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, '-B', '-c',
        'import sys; import knowledge_tracing.akt.research_junyi_numeric_predictions; '
        'assert "torch" not in sys.modules'], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
