"""Hồi quy guardfold outer, giữ mọi role/rank/OOV contract."""
import pytest
import numpy as np
from types import SimpleNamespace
import hashlib

from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.akt.research_junyi_window_cache import _parts
from knowledge_tracing.akt import research_junyi_window_cache as cache
from knowledge_tracing.akt.types import KTEvent, LearnerEvents, UnseenTarget
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.akt.prediction_batch import iter_predictions_batched
from knowledge_tracing.shared_kt import StableVocabulary


def fixture_assets():
    roles = JunyiResearchRoles(('train',), ('selection',), ('calibration',), ('outer',))
    fit = JunyiPhaseView(roles, 'refit_union90', ('train', 'selection'), roles.identity)
    outer = JunyiPhaseView(roles, 'outer_evaluation', ('outer',), roles.identity)
    native = ExerciseEncoding(StableVocabulary(('known',)), {'known': 1})
    return outer, JunyiResearchEncoding(native, fit)


def test_native_outer_windows_keep_known_and_oov_targets():
    view, encoding = fixture_assets()
    learner = LearnerEvents('outer', 4, (
        KTEvent('outer', 'known', 10, 1, 1, 0, 4),
        KTEvent('outer', 'unknown', 11, 2, 0, 0, 4),
    ))
    records = list(iter_windows(learner, encoding.native, training=False))
    assert len(records) == 2
    metadata, arrays, targets = _parts(records[0], view, encoding, {'outer'})
    assert metadata['kind'] == 'prediction'
    assert targets == ((0, 10, 1),)
    assert len(arrays['item_ids']) == 1
    assert isinstance(records[1], UnseenTarget)
    assert records[1].event.fold == 4
    assert records[1].global_rank == 1


def test_cache_accepts_valid_outer_oov_record():
    view, encoding = fixture_assets()
    encoding.assert_for(view)
    assert view.allowed_folds == (4,)
    record = UnseenTarget(KTEvent('outer', 'unknown', 11, 2, 0, 0, 4), 1)
    metadata, arrays, targets = _parts(record, view, encoding, {'outer'})
    assert metadata['kind'] == 'unseen'


@pytest.mark.parametrize('scope,user,fold', [
    ('outer_evaluation', 'outer', 0),
    ('outer_evaluation', 'outer', 3),
    ('calibration_predict', 'calibration', 4),
    ('outer_evaluation', 'foreign', 4),
])
def test_oov_guard_rejects_foreign_fold_or_learner(scope, user, fold):
    outer, encoding = fixture_assets()
    view = outer if scope == 'outer_evaluation' else JunyiPhaseView(
        outer.roles, scope, ('calibration',), outer.roles.identity)
    record = UnseenTarget(KTEvent(user, 'unknown', 11, 2, 0, 0, fold), 1)
    with pytest.raises(ValueError, match='Invalid unseen target'):
        _parts(record, view, encoding, set(view.users))


def test_calibration_fold_oov_still_accepted():
    outer, encoding = fixture_assets()
    view = JunyiPhaseView(outer.roles, 'calibration_predict', ('calibration',), outer.roles.identity)
    record = UnseenTarget(KTEvent('calibration', 'unknown', 11, 2, 0, 0, 3), 1)
    metadata, arrays, targets = _parts(record, view, encoding, {'calibration'})
    assert metadata['kind'] == 'unseen'
    assert arrays == {}
    assert targets == ((1, 11, 2),)


def test_uncached_native_outer_preserves_oov_null_without_model_call():
    _, encoding = fixture_assets()
    calls = []

    def predict_windows(windows):
        calls.extend(windows)
        return [np.full(len(window.target_mask), 0.6) for window in windows]

    adapter = SimpleNamespace(
        encoding=encoding.native, checkpoint_id='a' * 64,
        config=SimpleNamespace(batch_size=128, context=100, target_block=100),
        predict_windows=predict_windows,
    )
    learner = LearnerEvents('outer', 4, (
        KTEvent('outer', 'known', 10, 1, 1, 0, 4),
        KTEvent('outer', 'unknown', 11, 2, 0, 0, 4),
        KTEvent('outer', 'known', 12, 3, 1, 0, 4),
    ))
    result = list(iter_predictions_batched(adapter, [learner], batch_size=128))
    assert [record.source_row for record in result] == [1, 2, 3]
    assert [record.fold for record in result] == [4, 4, 4]
    assert [record.prediction for record in result] == [0.6, None, 0.6]
    assert result[1].prediction_kind == 'unseen'
    assert len(calls) == 2
    assert all(window.inputs.item_ids.tolist() == [0] for window in calls)


def test_outer_oov_full_cache_roundtrip_and_cpu_admission(tmp_path, monkeypatch):
    view, encoding = fixture_assets()
    monkeypatch.setattr(cache, 'CACHE_BASE', tmp_path/'owned')
    root = tmp_path/'owned/cache01'
    learner = LearnerEvents('outer', 4, (
        KTEvent('outer', 'known', 10, 1, 1, 0, 4),
        KTEvent('outer', 'unknown', 11, 2, 0, 0, 4),
        KTEvent('outer', 'known', 12, 3, 1, 0, 4),
    ))
    records = list(iter_windows(learner, encoding.native, training=False))
    built = cache.build_junyi_window_cache(root, iter(records), view=view,
        encoding=encoding, source_data_sha256='a'*64, expected_target_rows=3)
    kwargs = dict(view=view, encoding=encoding, source_data_sha256='a'*64,
        expected_target_rows=3, expected_manifest_sha256=built['manifest_sha256'])
    strict = cache.JunyiWindowCacheSession(root, **kwargs)
    admission = root/'CPU_ADMISSION.json'
    cache.write_cpu_admission(strict, admission)
    admitted = cache.JunyiWindowCacheSession(root, **kwargs,
        admission_receipt=admission,
        expected_admission_sha256=hashlib.sha256(admission.read_bytes()).hexdigest())
    restored = list(admitted.iter_windows())
    assert built['summary']['unseen_targets'] == 1
    assert built['summary']['target_rows'] == 3
    assert restored[1] == records[1]
    assert restored[1].event.fold == 4
    assert restored[0].global_ranks.tolist() == [0]
    assert restored[2].global_ranks.tolist() == [2]
    assert restored[2].history_used.tolist() == records[2].history_used.tolist()
    assert restored[2].context_reset.tolist() == records[2].context_reset.tolist()
