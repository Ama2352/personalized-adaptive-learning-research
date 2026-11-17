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

OLD_SOURCE = 'd22f6d2e3d6bb4a6c2d7f72da748e55c5c647ce8b41a7ab46b25c82290a4c96c'
NEW_SOURCE = '7c72414eedf9507d514430aed4734f0a192ab14914a4984b17fdfcbfebd39123'
GUARD_PATH = 'src/knowledge_tracing/akt/research_junyi_window_cache.py'
OLD_GUARD = '8e3331894fa490c16586b3157f725d26f42c77c185cae985dce8ee1d305e2687'
NEW_GUARD = '3168539b7d70ee93c1772f2a5cd7c593eebb46a9169223aff5baeca7224ad419'


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(value):
    _need(type(value) is str and len(value) == 64
          and all(character in '0123456789abcdef' for character in value),
          'explicit SHA256 pin required')


def _identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def runtime_source_files():
    """Đọc cùng danh sách nguồn với inference_source_identity, không importTorch."""
    from knowledge_tracing.akt.config import PROJECT_ROOT
    paths = tuple(sorted((PROJECT_ROOT/'src/knowledge_tracing/akt').glob('*.py')))
    paths += tuple(PROJECT_ROOT/name for name in (
        'src/knowledge_tracing/response_calibration.py', 'src/knowledge_tracing/simulator_bridge.py',
        'src/knowledge_tracing/shared_kt.py', 'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
        'artifacts/akt/dependencies/upstream/akt.py'))
    return {path.relative_to(PROJECT_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def _guard_release_maps(old_files, new_files):
    _need(type(old_files) is dict and type(new_files) is dict
          and len(old_files) == len(new_files) == 77 and set(old_files) == set(new_files),
          'full77 source maps required')
    _need(_identity(old_files) == OLD_SOURCE and _identity(new_files) == NEW_SOURCE,
          'only exact approved guard source release is accepted')
    _need([name for name in old_files if old_files[name] != new_files[name]] == [GUARD_PATH]
          and old_files[GUARD_PATH] == OLD_GUARD and new_files[GUARD_PATH] == NEW_GUARD,
          'only exact guard file delta permitted')
    from knowledge_tracing.akt.config import PROJECT_ROOT
    patched = (PROJECT_ROOT/GUARD_PATH).read_bytes()
    old = b'and type(event.fold) is int and event.fold in (0, 1, 2, 3)'
    new = b'and type(event.fold) is int and event.fold in view.allowed_folds'
    _need(hashlib.sha256(patched).hexdigest() == NEW_GUARD and patched.count(new) == 1
          and hashlib.sha256(patched.replace(new, old, 1)).hexdigest() == OLD_GUARD,
          'exact one-line guard patch proof required')


def build_compatibility_receipt(old_files, new_files, *, checkpoint_sha256=None,
                                calibration_identity=None):
    """Khóa release và variant; thiếu pin chỉ trả draft, không cấp admission."""
    _guard_release_maps(old_files, new_files)
    complete = checkpoint_sha256 is not None and calibration_identity is not None
    for value in (checkpoint_sha256, calibration_identity):
        if value is not None:
            _sha(value)
    return dict(kind='OUTER_EXACT_GUARD_SOURCE_COMPATIBILITY_V1',
        status='COMPLETE_VARIANT_PINS' if complete else 'DRAFT_MISSING_VARIANT_PINS',
        old_files=dict(old_files), new_files=dict(new_files),
        checkpoint_sha256=checkpoint_sha256, calibration_identity=calibration_identity)


def validate_compatibility(receipt, *, checkpoint_sha256, calibration_identity,
                            calibrated_source, current_source):
    _need(type(receipt) is dict and set(receipt) == {
        'kind', 'status', 'old_files', 'new_files', 'checkpoint_sha256', 'calibration_identity'}
        and receipt['kind'] == 'OUTER_EXACT_GUARD_SOURCE_COMPATIBILITY_V1'
        and receipt['status'] == 'COMPLETE_VARIANT_PINS', 'complete compatibility receipt required')
    _need(calibrated_source == OLD_SOURCE and current_source == NEW_SOURCE,
          'unapproved source transition')
    _guard_release_maps(receipt['old_files'], receipt['new_files'])
    _need(receipt['checkpoint_sha256'] == checkpoint_sha256
          and receipt['calibration_identity'] == calibration_identity,
          'compatibility checkpoint/calibrator mismatch')
    _need(runtime_source_files() == receipt['new_files'], 'actual runtime source files differ')
    return dict(calibration_source_sha256=OLD_SOURCE, inference_source_sha256=NEW_SOURCE,
                compatibility_receipt_sha256=_identity(receipt))


def admit_outer(predictor, *, view, expected_source_sha256, outer_data_sha256,
                calibration_data_sha256, calibration, compatibility=None):
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
    compatibility_provenance = None
    _need(compatibility is None or calibration is not None, 'compatibility requires fitted calibration')
    if calibration is not None:
        _need(type(calibration) is TemperatureCalibration
              and calibration.status == 'fitted_response_temperature', 'fitted calibrator required')
        fitted = asdict(calibration.binding)
        current = asdict(binding)
        _need(fitted.pop('domain_sha256') == calibration_data_sha256,
              'calibrator binding domain mismatch')
        current.pop('domain_sha256')
        if compatibility is not None:
            compatibility_provenance = validate_compatibility(compatibility,
                checkpoint_sha256=binding.checkpoint_sha256, calibration_identity=calibration.identity,
                calibrated_source=fitted.pop('model_source_sha256'),
                current_source=current.pop('model_source_sha256'))
        _need(fitted == current, 'calibrator binding differs from outer frozen model')
    return dict(phase='outer_evaluation', phase_identity=view.identity,
                roles_identity=view.roles.identity, encoding_identity=predictor.encoding.identity,
                raw_binding=asdict(binding),
                calibration_identity=None if calibration is None else calibration.identity,
                calibration_data_sha256=calibration_data_sha256,
                outer_data_sha256=outer_data_sha256,
                source_compatibility=compatibility_provenance)


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
        max_learner_events, receipt, calibration=None, batch_size=128, compatibility=None):
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
        calibration=calibration, compatibility=compatibility)
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
