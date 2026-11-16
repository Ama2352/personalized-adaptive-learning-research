"""Consumer temperature trên PredictionRecord tổng hợp, không nạp model/dataset."""
from dataclasses import asdict, replace
import math

import pytest

from knowledge_tracing.akt.evaluation import iter_calibrated_predictions, score_akt_shards
from knowledge_tracing.akt.prediction import _record_rows
from knowledge_tracing.akt.types import PredictionRecord
from knowledge_tracing.response_calibration import (
    CalibrationPartition, CalibrationTarget, PredictionBinding, fit_temperature,
    bind_probability_calibrator, calibrate_probability,
)


@pytest.fixture
def fitted():
    digest = 'a' * 64
    binding = PredictionBinding('synthetic-frozen-checkpoint', *([digest] * 7))
    partition = CalibrationPartition(digest, ('calibration',), ('train', 'selection', 'audit'), None)
    targets = tuple(CalibrationTarget('calibration', str(i), 'A', digest,
        int(i % 10 < 6), .9, 'supported') for i in range(20))
    keys = tuple((row.learner_id, row.event_id, row.item_id, row.history_sha256) for row in targets)
    calibration = fit_temperature(targets, binding=binding, partition=partition, expected_target_keys=keys)
    return calibration, binding


def records(binding):
    return (
        PredictionRecord(1, 'audit', 'A', 1, 1, 0, 4, .9, 'fitted', False,
            3, 0, 0, False, 'window1', binding.checkpoint_sha256),
        PredictionRecord(2, 'audit', 'unknown', 2, 0, 1, 4, None, 'unseen', False,
            0, 1, 0, True, 'window2', binding.checkpoint_sha256),
    )


def test_stream_preserves_metadata_nulls_and_analytic_temperature(fitted):
    calibration, binding = fitted
    raw = records(binding)
    result = tuple(iter_calibrated_predictions(iter(raw), calibration=calibration, binding=binding))
    assert len(result) == len(raw)
    assert result[0].prediction == pytest.approx(.6, abs=1e-8)
    assert result[1] is raw[1]
    assert replace(result[0], prediction=raw[0].prediction) == raw[0]
    assert raw[0].prediction == .9


def test_calibration_source_checked_once_before_consuming_stream(fitted, monkeypatch):
    import knowledge_tracing.response_calibration as shared
    calibration, binding = fitted
    calls = []
    original = shared.implementation_identity
    monkeypatch.setattr(shared, 'implementation_identity', lambda: (calls.append('source'), original())[1])

    def source():
        for row in records(binding):
            calls.append('row')
            yield row

    result = iter_calibrated_predictions(source(), calibration=calibration, binding=binding)
    assert calls == []
    next(result)
    assert calls == ['source', 'row']
    next(result)
    assert calls == ['source', 'row', 'row']
    with pytest.raises(StopIteration):
        next(result)


@pytest.mark.parametrize('probability', [0., 1., .1, .5, .9])
def test_same_clipped_scalar_arithmetic(fitted, probability):
    calibration, binding = fitted
    row = replace(records(binding)[0], prediction=probability)
    clipped = min(1 - 1e-6, max(1e-6, probability))
    expected = 1 / (1 + math.exp(-math.log(clipped / (1 - clipped)) / calibration.temperature))
    actual = next(iter_calibrated_predictions([row], calibration=calibration, binding=binding))
    assert actual.prediction == pytest.approx(expected, abs=1e-15)
    assert actual.prediction == calibrate_probability(probability, calibration=calibration, binding=binding)


@pytest.mark.parametrize('probability', [None, True, '0.5', float('nan'), float('inf'), -.1, 1.1])
def test_scalar_and_bound_transform_preserve_probability_exceptions(fitted, probability):
    calibration, binding = fitted
    transform = bind_probability_calibrator(calibration=calibration, binding=binding)
    with pytest.raises(ValueError, match=r'finite probability in \[0,1\] required'):
        calibrate_probability(probability, calibration=calibration, binding=binding)
    with pytest.raises(ValueError, match=r'finite probability in \[0,1\] required'):
        transform(probability)


def test_source_change_rejected_when_opening_each_new_stream(fitted, monkeypatch):
    import knowledge_tracing.response_calibration as shared
    calibration, binding = fitted
    pending = iter_calibrated_predictions(records(binding), calibration=calibration, binding=binding)
    monkeypatch.setattr(shared, 'implementation_identity', lambda: 'b' * 64)
    with pytest.raises(ValueError, match='implementation/source drift'):
        next(pending)
    with pytest.raises(ValueError, match='implementation/source drift'):
        calibrate_probability(.9, calibration=calibration, binding=binding)


def test_consumer_preserves_input_order(fitted):
    calibration, binding = fitted
    raw = tuple(reversed(records(binding)))
    result = tuple(iter_calibrated_predictions(raw, calibration=calibration, binding=binding))
    assert [row.source_row for row in result] == [row.source_row for row in raw]


@pytest.mark.parametrize('changes', [
    {'checkpoint_id': 'b' * 64},
    {'prediction': float('nan')},
    {'prediction': None},
    {'is_fallback': True},
    {'prediction_kind': 'unknown'},
])
def test_rejects_wrong_checkpoint_or_invalid_prediction(fitted, changes):
    calibration, binding = fitted
    row = replace(records(binding)[0], **changes)
    with pytest.raises(ValueError):
        tuple(iter_calibrated_predictions([row], calibration=calibration, binding=binding))


@pytest.mark.parametrize('change', ['binding', 'source', 'unsupported'])
def test_rejects_calibrator_before_reading_any_predictions(fitted, change):
    calibration, binding = fitted
    if change == 'binding':
        binding = replace(binding, vocabulary_sha256='b' * 64)
    elif change == 'source':
        calibration = replace(calibration, implementation_sha256='b' * 64)
    else:
        calibration = replace(calibration, status='unsupported_two_class_labels_required', temperature=None)

    def unread():
        pytest.fail('rejected calibrator must not consume prediction stream')
        yield

    with pytest.raises(ValueError):
        tuple(iter_calibrated_predictions(unread(), calibration=calibration, binding=binding))


def test_calibrated_records_use_existing_parquet_scoring_entrypoint(fitted, tmp_path):
    calibration, binding = fitted
    raw = records(binding)
    calibrated = list(iter_calibrated_predictions(raw, calibration=calibration, binding=binding))
    path = tmp_path / 'calibrated.parquet'
    _record_rows(path, calibrated)
    scored = score_akt_shards(str(path))
    assert scored['coverage']['expected_rows'] == 2
    assert scored['coverage']['fitted_rows'] == scored['coverage']['unseen_rows'] == 1
    assert scored['native']['metrics']['log_loss'] == pytest.approx(-math.log(.6), abs=1e-8)
    assert asdict(raw[1]) == asdict(calibrated[1])
