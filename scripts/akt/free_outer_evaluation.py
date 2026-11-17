"""Hợp đồng outer native trên CPU/local hoặc Colab, ngoài nguồn KT frozen.

Không tạo container, nạp weights, fit temperature hoặc ghi predictions lớn.
Caller attach predictor bằng API hiện có, kiểm nguồn dữ liệu và cấp output sink
Drive riêng. Native iterator này chưa là pipeline numeric CPU/H100 tách biệt.
Receipt chỉ COMPLETE sau khi tiêu thụ hết; sink phải giữ staging đến thời điểm đó.
"""
from dataclasses import asdict
import hashlib
from itertools import zip_longest
import json

from knowledge_tracing.akt.evaluation import iter_calibrated_predictions
from knowledge_tracing.akt.prediction_batch import iter_predictions_batched
from knowledge_tracing.akt.research_junyi_calibration import (
    RefitCalibrationPredictor, inference_source_identity,
)
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView
from knowledge_tracing.akt.types import LearnerEvents
from knowledge_tracing.response_calibration import PredictionBinding, TemperatureCalibration


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(value):
    _need(type(value) is str and len(value) == 64
          and all(character in '0123456789abcdef' for character in value),
          'explicit SHA256 pin required')


def admit_outer(predictor, *, view, expected_source_sha256, outer_data_sha256,
                calibration_data_sha256, calibration):
    """Tách source outer với domain đã fit, giữ nguyên calibrator binding."""
    _need(type(view) is JunyiPhaseView and view.scope == 'outer_evaluation'
          and view.full_role_coverage and view.allowed_folds == (4,),
          'full outer role required')
    _need(type(predictor) is RefitCalibrationPredictor, 'attached refit predictor required')
    for value in (expected_source_sha256, outer_data_sha256, calibration_data_sha256):
        _sha(value)
    _need(outer_data_sha256 != calibration_data_sha256, 'separate outer/calibration source pins required')
    predictor.assert_boundary()
    predictor.encoding.assert_for(view)
    binding = predictor.binding
    _need(type(binding) is PredictionBinding
          and binding.model_source_sha256 == expected_source_sha256 == inference_source_identity()
          and binding.domain_sha256 == outer_data_sha256
          and binding.vocabulary_sha256 == predictor.encoding.identity
          and binding.split_sha256 == view.roles.identity,
          'outer predictor source/domain binding mismatch')
    phase = getattr(predictor.adapter, 'phase', None)
    if hasattr(predictor.adapter, 'set_phase'):
        _need(phase is not None and phase.view.identity == view.identity,
              'graph adapter must already use admitted outer phase')
        phase.assert_boundary()
    if calibration is not None:
        _need(type(calibration) is TemperatureCalibration
              and calibration.status == 'fitted_response_temperature', 'fitted calibrator required')
        fitted = asdict(calibration.binding)
        current = asdict(binding)
        _need(fitted.pop('domain_sha256') == calibration_data_sha256,
              'calibrator binding domain mismatch')
        current.pop('domain_sha256')
        _need(fitted == current, 'calibrator binding differs from outer frozen model')
    return dict(phase='outer_evaluation', phase_identity=view.identity,
                roles_identity=view.roles.identity, encoding_identity=predictor.encoding.identity,
                raw_binding=asdict(binding),
                calibration_identity=None if calibration is None else calibration.identity,
                calibration_data_sha256=calibration_data_sha256,
                outer_data_sha256=outer_data_sha256)


def _checked_learners(factory, view, max_learner_events):
    expected = iter(sorted(view.users))
    sentinel = object()
    for learner, user in zip_longest(factory(), expected, fillvalue=sentinel):
        _need(type(learner) is LearnerEvents and user is not sentinel
              and learner.user_id == user and learner.fold == 4,
              'outer learner coverage/order mismatch')
        events = learner.events
        _need(0 < len(events) <= max_learner_events, 'outer learner event cap exceeded')
        _need(all(event.user_id == user and event.fold == 4 for event in events),
              'foreign event in outer learner')
        _need(all((left.time_done, left.source_row) < (right.time_done, right.source_row)
                  for left, right in zip(events, events[1:])), 'outer chronology mismatch')
        yield learner


def _key(row):
    return (row.user_id, row.exercise, row.time_done, row.source_row,
            row.correct, row.suggested, row.fold)


def iter_outer_predictions(predictor, learners_factory, *, view, expected_source_sha256,
        outer_data_sha256, calibration_data_sha256, expected_targets,
        max_learner_events, receipt, calibration=None, batch_size=128):
    """Ép đủ role/key/OOV. Hai lượt factory đều phải đọc cùng nguồn đã ghim.

Đây là wrapper stream native phục vụ nối CPU và kiểm đối chiếu. Không gọi trực
tiếp toàn bộ wrapper trong GPU thuê khi chưa chuẩn bị/caching CPU riêng.
Không trả metric hoặc chọn model. Consumer phải tiêu thụ hết trước publish.
"""
    _need(type(receipt) is dict and not receipt, 'new empty receipt required')
    _need(type(expected_targets) is int and expected_targets > 0
          and type(max_learner_events) is int and max_learner_events > 0,
          'positive exact target count and learner cap required')
    admission = admit_outer(predictor, view=view, expected_source_sha256=expected_source_sha256,
        outer_data_sha256=outer_data_sha256, calibration_data_sha256=calibration_data_sha256,
        calibration=calibration)
    receipt.update(status='RUNNING', admission=admission)
    factory = lambda: _checked_learners(learners_factory, view, max_learner_events)
    raw = iter_predictions_batched(predictor.adapter, factory(), batch_size=batch_size)
    expected = (event for learner in factory() for event in learner.events)
    digest = hashlib.sha256()
    counts = dict(targets=0, fitted_targets=0, oov_targets=0)
    sentinel = object()

    def checked():
        for record, event in zip_longest(raw, expected, fillvalue=sentinel):
            _need(record is not sentinel and event is not sentinel and _key(record) == _key(event),
                  'outer row identity/coverage mismatch')
            counts['targets'] += 1
            _need(counts['targets'] <= expected_targets, 'outer target count exceeds declared population')
            supported = event.exercise in predictor.encoding.native.train_support_students
            _need((supported and record.prediction is not None and record.prediction_kind == 'fitted')
                  or (not supported and record.prediction is None
                      and record.prediction_kind == 'unseen' and record.train_support_students == 0),
                  'outer fitted/OOV contract mismatch')
            counts['fitted_targets' if supported else 'oov_targets'] += 1
            digest.update(json.dumps(_key(record), separators=(',', ':')).encode() + b'\n')
            yield record
        _need(counts['targets'] == expected_targets, 'outer target count differs from declared population')
        predictor.assert_boundary()

    stream = checked()
    if calibration is not None:
        stream = iter_calibrated_predictions(stream, calibration=calibration, binding=calibration.binding)
    try:
        yield from stream
        receipt.update(status='COMPLETE', learners=len(view.users), **counts,
                       target_keys_sha256=digest.hexdigest())
    except BaseException:
        receipt.update(status='INCOMPLETE', **counts)
        raise
    finally:
        raw.close()
        expected.close()
