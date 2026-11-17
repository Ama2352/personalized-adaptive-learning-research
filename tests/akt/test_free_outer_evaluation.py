"""Hợp đồng outer ở ngoài nguồn KT frozen, chỉ dữ liệu tổng hợp."""
from dataclasses import replace
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_calibration import RefitCalibrationPredictor, inference_source_identity
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.response_calibration import PredictionBinding, TemperatureCalibration, implementation_identity
from knowledge_tracing.shared_kt import StableVocabulary

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/akt/free_outer_evaluation.py'


@pytest.fixture
def wrapper():
    spec = importlib.util.spec_from_file_location('free_outer_evaluation', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def case(monkeypatch):
    roles = JunyiResearchRoles(('t',), ('s',), ('c',), ('o',))
    fit = JunyiPhaseView(roles, 'refit_union90', ('s', 't'), roles.identity)
    view = JunyiPhaseView(roles, 'outer_evaluation', ('o',), roles.identity)
    encoding = JunyiResearchEncoding(ExerciseEncoding(StableVocabulary(('known',)), {'known': 1}), fit)
    binding = PredictionBinding('A0', 'a'*64, encoding.identity, roles.identity,
                                'b'*64, 'c'*64, inference_source_identity(), 'd'*64)
    adapter = SimpleNamespace(encoding=encoding.native,
        config=SimpleNamespace(context=100, target_block=100, batch_size=128),
        checkpoint_id=binding.checkpoint_sha256,
        predict_windows=lambda windows: [np.full(len(window.target_mask), .6) for window in windows])
    predictor = RefitCalibrationPredictor(adapter, encoding, binding, {})
    monkeypatch.setattr(RefitCalibrationPredictor, 'assert_boundary', lambda self: None)
    learner = LearnerEvents('o', 4, (KTEvent('o', 'known', 10, 1, 1, 0, 4),
                                  KTEvent('o', 'new', 11, 2, 0, 0, 4)))
    calibration = TemperatureCalibration(replace(binding, domain_sha256='e'*64), 'f'*64,
        '1'*64, implementation_identity(), 'fitted_response_temperature', 2., 5,
        2, 2, (1, 1), (), .5, .4)
    kwargs = dict(view=view, expected_source_sha256=binding.model_source_sha256,
                  outer_data_sha256='d'*64, calibration_data_sha256='e'*64,
                  expected_targets=2, max_learner_events=3)
    return predictor, learner, calibration, kwargs


def test_full_native_outer_oov_and_completed_receipt(wrapper, case):
    predictor, learner, calibration, kwargs = case
    receipt = {}
    rows = list(wrapper.iter_outer_predictions(predictor, lambda: iter((learner,)),
        calibration=calibration, receipt=receipt, **kwargs))
    assert [r.source_row for r in rows] == [1, 2]
    assert rows[0].prediction == pytest.approx(.5505102572168219)
    assert rows[1].prediction is None and rows[1].prediction_kind == 'unseen'
    assert calibration.binding.domain_sha256 == 'e'*64
    assert predictor.binding.domain_sha256 == 'd'*64
    assert receipt['status'] == 'COMPLETE'
    assert receipt['targets'] == 2 and receipt['oov_targets'] == 1
    assert receipt['learners'] == 1


@pytest.mark.parametrize('field', ['checkpoint_sha256', 'model_source_sha256', 'vocabulary_sha256'])
def test_mismatched_calibrator_refused_before_prediction(wrapper, case, field):
    predictor, learner, calibration, kwargs = case
    calibration = replace(calibration, binding=replace(calibration.binding, **{field:'2'*64}))
    with pytest.raises(ValueError, match='calibrator binding'):
        list(wrapper.iter_outer_predictions(predictor, lambda: iter((learner,)),
             calibration=calibration, receipt={}, **kwargs))


def test_partial_outer_role_refused(wrapper, case):
    predictor, learner, calibration, kwargs = case
    roles = replace(kwargs['view'].roles, outer_validation_users=('o', 'o2'))
    kwargs['view'] = JunyiPhaseView(roles, 'outer_evaluation', ('o',), roles.identity)
    with pytest.raises(ValueError, match='full outer'):
        list(wrapper.iter_outer_predictions(predictor, lambda: iter((learner,)),
             calibration=None, receipt={}, **kwargs))


def test_target_count_mismatch_never_publishes_complete(wrapper, case):
    predictor, learner, _, kwargs = case
    kwargs['expected_targets'] = 3
    receipt = {}
    with pytest.raises(ValueError, match='target count'):
        list(wrapper.iter_outer_predictions(predictor, lambda: iter((learner,)),
             calibration=None, receipt=receipt, **kwargs))
    assert receipt['status'] != 'COMPLETE'


def test_factory_key_drift_refused(wrapper, case):
    predictor, learner, _, kwargs = case
    variants = iter((learner, replace(learner, events=(replace(learner.events[0], source_row=3), learner.events[1]))))
    with pytest.raises(ValueError, match='row identity|chronology'):
        list(wrapper.iter_outer_predictions(predictor, lambda: iter((next(variants),)),
             calibration=None, receipt={}, **kwargs))


def test_source_pin_drift_refused(wrapper, case):
    predictor, learner, _, kwargs = case
    kwargs['expected_source_sha256'] = '9'*64
    with pytest.raises(ValueError, match='source/domain'):
        list(wrapper.iter_outer_predictions(predictor, lambda: iter((learner,)),
             calibration=None, receipt={}, **kwargs))


def test_graph_phase_must_be_outer_before_native_prediction(wrapper, case):
    predictor, learner, _, kwargs = case
    predictor.adapter.set_phase = lambda phase: None
    with pytest.raises(ValueError, match='graph adapter'):
        list(wrapper.iter_outer_predictions(predictor, lambda: iter((learner,)),
             calibration=None, receipt={}, **kwargs))


def test_partial_consumption_keeps_receipt_incomplete(wrapper, case):
    predictor, learner, _, kwargs = case
    receipt = {}
    stream = wrapper.iter_outer_predictions(predictor, lambda: iter((learner,)),
         calibration=None, receipt=receipt, **kwargs)
    next(stream)
    assert receipt['status'] == 'RUNNING'
    stream.close()
    assert receipt['status'] == 'INCOMPLETE'


def test_same_calibration_and_outer_domain_refused(wrapper, case):
    predictor, learner, _, kwargs = case
    kwargs['calibration_data_sha256'] = kwargs['outer_data_sha256']
    with pytest.raises(ValueError, match='separate outer/calibration'):
        list(wrapper.iter_outer_predictions(predictor, lambda: iter((learner,)),
             calibration=None, receipt={}, **kwargs))
