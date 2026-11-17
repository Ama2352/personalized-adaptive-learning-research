"""Ghi nhận ranh giới outer hiện hành, không thay nguồn KT đang frozen."""
import pytest
import numpy as np
from types import SimpleNamespace

from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.akt.research_junyi_window_cache import _parts
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


@pytest.mark.xfail(strict=True, raises=ValueError,
                   reason='Frozen cache OOV guard accepts folds0–3 only; outer fold4 requires release')
def test_frozen_cache_should_accept_valid_outer_oov_record():
    view, encoding = fixture_assets()
    encoding.assert_for(view)
    assert view.allowed_folds == (4,)
    record = UnseenTarget(KTEvent('outer', 'unknown', 11, 2, 0, 0, 4), 1)
    metadata, arrays, targets = _parts(record, view, encoding, {'outer'})
    assert metadata['kind'] == 'unseen'


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
