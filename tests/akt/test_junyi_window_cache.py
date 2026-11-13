"""Roundtrip cache native windows, ranh giới phase và lỗi toàn vẹn."""
import json

import numpy as np
import pytest

from knowledge_tracing.shared_kt import StableVocabulary
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles, make_junyi_research_roles
from knowledge_tracing.akt.types import KTEvent, LearnerEvents, TrainingWindow, UnseenTarget
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.akt import research_junyi_window_cache as cache

SOURCE = 'a'*64


@pytest.mark.parametrize('scope',['train','selection'])
def test_prefetch_preserves_order_bytes_and_counts(case,scope):
    root,train,selection,encoding=case
    view=train if scope=='train' else selection
    items=['A','B']*205
    if scope=='selection':items[102]='OOV'
    source=records(view,encoding,items,[i%2 for i in range(len(items))])
    receipt=build(case,view,source,shard_records=1)
    kwargs=dict(view=view,encoding=encoding,source_data_sha256=SOURCE,
        expected_target_rows=receipt['summary']['target_rows'],expected_manifest_sha256=receipt['manifest_sha256'])
    sequential=cache.JunyiWindowCacheSession(root,**kwargs)
    prefetched=cache.JunyiWindowCacheSession(root,**kwargs,prefetch=True)
    for _ in range(2):
        first=list(sequential.iter_windows());second=list(prefetched.iter_windows())
        assert len(first)==len(second)==len(source)
        for left,right in zip(first,second):assert_record_equal(left,right)


def test_prefetch_propagates_background_read_error(case,monkeypatch):
    root,train,_,encoding=case
    source=records(train,encoding,['A']*305,[1]*305)
    receipt=build(case,train,source,shard_records=1)
    session=cache.JunyiWindowCacheSession(root,view=train,encoding=encoding,source_data_sha256=SOURCE,
        expected_target_rows=305,expected_manifest_sha256=receipt['manifest_sha256'],prefetch=True)
    original=cache._load_shard
    def fail(path,entry,manifest):
        if entry['name']=='shard-000001.npz':raise OSError('unit background read failure')
        yield from original(path,entry,manifest)
    monkeypatch.setattr(cache,'_load_shard',fail)
    with pytest.raises(OSError,match='background read failure'):list(session.iter_windows())


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, 'CACHE_BASE', tmp_path/'owned')
    roles = make_junyi_research_roles([(str(i), i % 5, 'development') for i in range(40)])
    train = JunyiPhaseView(roles, 'select_train80', roles.train_users[:1], roles.identity)
    selection = JunyiPhaseView(roles, 'raw_selection10', roles.selection_users[:1], roles.identity)
    native = ExerciseEncoding(StableVocabulary(('A', 'B', 'C')), dict(A=1, B=1, C=1))
    encoding = JunyiResearchEncoding(native, train)
    return tmp_path/'owned/cache01', train, selection, encoding


def records(view, encoding, items, responses):
    user = view.users[0]
    learner = LearnerEvents(user, 0, tuple(KTEvent(user, item, 100+i, i+1, correct, i % 2, 0)
        for i, (item, correct) in enumerate(zip(items, responses))))
    return list(iter_windows(learner, encoding.native, training=view.optimization))


def build(case, view, source, **kwargs):
    root, _, _, encoding = case
    expected = kwargs.pop('expected_target_rows', sum(1 if isinstance(row, UnseenTarget) else
        int((row.window if isinstance(row, TrainingWindow) else row).target_mask.sum()) for row in source))
    receipt = cache.build_junyi_window_cache(root, iter(source), view=view, encoding=encoding,
        source_data_sha256=SOURCE, expected_target_rows=max(1, expected), **kwargs)
    return receipt


def read(case, view, receipt, **kwargs):
    root, _, _, encoding = case
    return cache.iter_junyi_window_cache(root, view=view, encoding=encoding,
        source_data_sha256=SOURCE, expected_target_rows=receipt['summary']['target_rows'],
        expected_manifest_sha256=receipt['manifest_sha256'], **kwargs)


def assert_record_equal(left, right):
    assert type(left) is type(right)
    if isinstance(left, UnseenTarget):
        assert left == right
        return
    if isinstance(left, TrainingWindow):
        np.testing.assert_array_equal(left.targets, right.targets)
        assert left.targets.dtype == right.targets.dtype
        left, right = left.window, right.window
    assert left.window_id == right.window_id
    assert left.inputs.user_ids == right.inputs.user_ids
    assert left.inputs.concept_ids is right.inputs.concept_ids is None
    for name in (*cache._INPUT_FIELDS, 'sequence_offsets'):
        expected, actual = getattr(left.inputs, name), getattr(right.inputs, name)
        np.testing.assert_array_equal(expected, actual)
        assert expected.dtype == actual.dtype
    for name in cache._WINDOW_FIELDS:
        expected, actual = getattr(left, name), getattr(right, name)
        np.testing.assert_array_equal(expected, actual)
        assert expected.dtype == actual.dtype


@pytest.mark.parametrize('compressed', [False, True])
def test_training_exact_roundtrip_shards_reusable_factory(case, compressed):
    root, train, _, encoding = case
    source = records(train, encoding, ['A', 'B', 'C']*100, [0, 1, 1]*100)
    receipt = build(case, train, source, shard_records=1, compressed=compressed)
    assert receipt['summary']['target_rows'] == 300
    assert len(list(root.glob('shard-*.npz'))) == 3
    for _ in range(2):
        restored = list(read(case, train, receipt))
        assert len(source) == len(restored)
        for left, right in zip(source, restored):
            assert_record_equal(left, right)


def test_prediction_roundtrip_oov_geometry_and_no_model_target_labels(case):
    root, _, selection, encoding = case
    source = records(selection, encoding, ['A', 'OOV', 'C', 'B', 'C'], [1, 0, 0, 1, 1])
    receipt = build(case, selection, source, shard_records=2)
    restored = list(read(case, selection, receipt))
    for left, right in zip(source, restored):
        assert_record_equal(left, right)
    assert restored[2].context_reset.all()
    assert restored[2].global_ranks[0] == 2
    for shard in root.glob('*.npz'):
        with np.load(shard, allow_pickle=False) as saved:
            assert np.all(saved['targets'] == -1)
            assert all(saved[name].dtype.kind != 'O' for name in saved.files)


def test_foreign_source_and_manifest_pin_rejected(case):
    root, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A'], [1]))
    with pytest.raises(ValueError, match='Foreign'):
        list(cache.iter_junyi_window_cache(root, view=train, encoding=encoding,
            source_data_sha256='b'*64, expected_target_rows=1, expected_manifest_sha256=receipt['manifest_sha256']))
    with pytest.raises(ValueError, match='manifest'):
        list(cache.iter_junyi_window_cache(root, view=train, encoding=encoding,
            source_data_sha256=SOURCE, expected_target_rows=1, expected_manifest_sha256='0'*64))


def test_train80_and_refit90_keys_distinct_and_wrong_encoding_fails(case):
    root, train, selection, encoding = case
    refit = JunyiPhaseView(train.roles, 'refit_union90', (*train.users, *selection.users), train.roles.identity)
    encoding90 = JunyiResearchEncoding(encoding.native, refit)
    assert cache.window_cache_key(train, encoding, SOURCE, expected_target_rows=1) != cache.window_cache_key(
        refit, encoding90, SOURCE, expected_target_rows=1)
    with pytest.raises(ValueError, match='phase'):
        cache.window_cache_key(refit, encoding, SOURCE, expected_target_rows=1)
    receipt = build(case, train, records(train, encoding, ['A'], [1]))
    with pytest.raises(ValueError, match='Foreign'):
        list(cache.iter_junyi_window_cache(root, view=refit, encoding=encoding90,
            source_data_sha256=SOURCE, expected_target_rows=1, expected_manifest_sha256=receipt['manifest_sha256']))


@pytest.mark.parametrize('damage', ['flip', 'truncate', 'missing'])
def test_changed_or_missing_shard_rejected(case, damage):
    root, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A', 'B'], [1, 0]))
    shard = next(root.glob('shard-*.npz'))
    raw = bytearray(shard.read_bytes())
    if damage == 'flip':
        raw[-1] ^= 1; shard.write_bytes(raw)
    elif damage == 'truncate':
        shard.write_bytes(raw[:-20])
    else:
        shard.rename(root/'preserved-original.npz')
    with pytest.raises((ValueError, FileNotFoundError)):
        list(read(case, train, receipt))


def test_source_failure_preserves_failure_without_complete_marker(case):
    root, train, _, encoding = case
    source = records(train, encoding, ['A']*500, [1]*500)
    def interrupted():
        for index, record in enumerate(source):
            if index == 3:
                assert (root/'shard-000000.npz').exists()
                raise RuntimeError('controlled source interruption')
            yield record
    with pytest.raises(RuntimeError, match='controlled'):
        cache.build_junyi_window_cache(root, interrupted(), view=train, encoding=encoding,
            source_data_sha256=SOURCE, expected_target_rows=500, shard_records=1)
    assert (root/'failure.json').exists()
    assert not (root/'COMPLETE.json').exists()
    with pytest.raises(FileNotFoundError):
        list(cache.iter_junyi_window_cache(root, view=train, encoding=encoding,
            source_data_sha256=SOURCE, expected_target_rows=500, expected_manifest_sha256='0'*64))


@pytest.mark.parametrize('mode', ['empty', 'missing_first', 'duplicate'])
def test_incomplete_or_duplicate_target_stream_rejected(case, mode):
    _, train, _, encoding = case
    source = records(train, encoding, ['A']*210, [1]*210)
    altered = {'empty': [], 'missing_first': source[1:], 'duplicate': [source[0], source[0]]}[mode]
    with pytest.raises(ValueError, match='coverage|rank'):
        build(case, train, altered, shard_records=1)


def test_target_type_must_match_prediction_phase(case):
    _, train, selection, encoding = case
    with pytest.raises(ValueError, match='record type'):
        build(case, selection, records(train, encoding, ['A'], [1]))


def test_path_guard_and_existing_cache_are_exclusive(case):
    root, train, _, encoding = case
    with pytest.raises(ValueError, match='Owned'):
        cache.build_junyi_window_cache(root.parent.parent/'outside', [], view=train, encoding=encoding,
            source_data_sha256=SOURCE, expected_target_rows=1)
    source = records(train, encoding, ['A'], [1])
    build(case, train, source)
    with pytest.raises(FileExistsError):
        build(case, train, source)


def test_shard_token_cap_is_respected(case):
    root, train, _, encoding = case
    source = records(train, encoding, ['A']*500, [1]*500)
    receipt = build(case, train, source, shard_records=10, max_shard_tokens=200)
    manifest = json.loads((root/'manifest.json').read_text())
    assert all(shard['tokens'] <= 200 for shard in manifest['shards'])
    assert receipt['summary']['target_rows'] == 500
    assert len(list(read(case, train, receipt))) == len(source)


def test_encoding_content_drift_rejected_before_read(case):
    _, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A'], [1]))
    encoding.native.train_support_students['A'] = 2
    with pytest.raises(ValueError, match='changed'):
        list(read(case, train, receipt))


def test_encoding_drift_after_first_yield_rejected(case):
    _, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A']*210, [1]*210))
    iterator = read(case, train, receipt)
    next(iterator)
    encoding.native.train_support_students['A'] = 2
    with pytest.raises(ValueError, match='changed'):
        next(iterator)


def test_all_unseen_prediction_shard_preserves_events_without_model_arrays(case):
    root, _, selection, encoding = case
    source = records(selection, encoding, ['OOV']*4, [0, 1, 0, 1])
    receipt = build(case, selection, source)
    assert list(read(case, selection, receipt)) == source
    with np.load(next(root.glob('*.npz')), allow_pickle=False) as saved:
        assert all(saved[name].size == 0 for name in cache._FIELDS)


def test_integer_pack_does_not_silently_overflow(case):
    _, train, _, encoding = case
    source = records(train, encoding, ['A'], [1])
    source[0].window.inputs.timestamps[:] = 100
    oversized = np.asarray([2**63+5], dtype=np.uint64)
    object.__setattr__(source[0].window.inputs, 'timestamps', oversized)
    with pytest.raises(ValueError, match='int64 packing'):
        build(case, train, source)


def test_silent_final_learner_truncation_rejected_by_expected_source_count(case):
    root, train, _, encoding = case
    source = records(train, encoding, ['A']*210, [1]*210)
    with pytest.raises(ValueError, match='Truncated source'):
        build(case, train, source[:1], expected_target_rows=210)
    assert not (root/'COMPLETE.json').exists()


def session(case, view, receipt):
    return cache.JunyiWindowCacheSession(case[0], view, case[3], SOURCE,
        receipt['summary']['target_rows'], receipt['manifest_sha256'])


def test_session_strict_admission_once_then_hot_exact_roundtrip(case, monkeypatch):
    _, train, _, encoding = case
    source = records(train, encoding, ['A']*210, [1]*210)
    receipt = build(case, train, source)
    original = cache._parts
    calls = []
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(cache, '_parts', counted)
    admitted = session(case, train, receipt)
    assert admitted.strict_records_verified == len(source)
    assert admitted.strict_seconds >= 0
    assert len(calls) == len(source)
    for _ in range(3):
        restored = list(admitted.iter_windows())
        for left, right in zip(source, restored):
            assert_record_equal(left, right)
    assert len(calls) == len(source)


def test_session_checks_corrupted_shard_after_admission(case):
    root, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A'], [1]))
    admitted = session(case, train, receipt)
    shard = next(root.glob('shard-*.npz'))
    raw = bytearray(shard.read_bytes()); raw[-1] ^= 1; shard.write_bytes(raw)
    with pytest.raises(ValueError, match='SHA'):
        list(admitted.iter_windows())


def test_session_cannot_admit_incomplete_cache(case):
    root, train, _, encoding = case
    source = records(train, encoding, ['A'], [1])
    build(case, train, source)
    (root/'COMPLETE.json').rename(root/'preserved-COMPLETE.json')
    with pytest.raises(FileNotFoundError):
        cache.JunyiWindowCacheSession(root, train, encoding, SOURCE, 1,
            hashlib_sha(root/'manifest.json'))


def hashlib_sha(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_session_checks_role_tuple_replacement(case):
    _, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A'], [1]))
    admitted = session(case, train, receipt)
    object.__setattr__(train, 'users', ('foreign',))
    with pytest.raises(ValueError, match='header'):
        list(admitted.iter_windows())


def test_session_checks_encoding_drift_at_epoch_boundary(case):
    _, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A'], [1]))
    admitted = session(case, train, receipt)
    encoding.native.train_support_students['A'] = 7
    with pytest.raises(ValueError, match='changed'):
        list(admitted.iter_windows())


def test_session_checks_control_file_alias(case, monkeypatch):
    from pathlib import Path
    root, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A'], [1]))
    admitted = session(case, train, receipt)
    original = Path.is_symlink
    monkeypatch.setattr(Path, 'is_symlink', lambda path: path == root/'manifest.json' or original(path))
    with pytest.raises(ValueError, match='alias'):
        list(admitted.iter_windows())


def test_session_checks_control_file_hash(case):
    root, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A'], [1]))
    admitted = session(case, train, receipt)
    with (root/'manifest.json').open('a') as stream:
        stream.write(' ')
    with pytest.raises(ValueError, match='control files changed'):
        list(admitted.iter_windows())


def test_session_prediction_unseen_roundtrip(case):
    _, _, selection, encoding = case
    source = records(selection, encoding, ['A', 'OOV', 'C'], [1, 0, 1])
    receipt = build(case, selection, source)
    admitted = session(case, selection, receipt)
    restored = list(admitted.iter_windows())
    assert len(source) == len(restored)
    for left, right in zip(source, restored):
        assert_record_equal(left, right)


def test_session_hot_epochs_do_not_rehash_full_roles(case, monkeypatch):
    _, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A']*210, [1]*210))
    original = JunyiResearchRoles.identity.fget
    calls = []
    def counted(roles):
        calls.append(1)
        return original(roles)
    monkeypatch.setattr(JunyiResearchRoles, 'identity', property(counted))
    admitted = session(case, train, receipt)
    count_at_admission = len(calls)
    assert count_at_admission > 0
    for _ in range(3):
        assert len(list(admitted.iter_windows())) == 3
    assert len(calls) == count_at_admission


def test_session_other_role_group_mutation_rejected(case):
    _, train, _, encoding = case
    receipt = build(case, train, records(train, encoding, ['A'], [1]))
    admitted = session(case, train, receipt)
    object.__setattr__(train.roles, 'calibration_users', (*train.roles.calibration_users, 'foreign'))
    with pytest.raises(ValueError, match='header'):
        list(admitted.iter_windows())
