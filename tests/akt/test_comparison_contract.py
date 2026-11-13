"""Bắt mismatch protocol và rò rỉ nguồn graph trước khi chi GPU."""
from copy import deepcopy

import pytest

from knowledge_tracing.akt.comparison_contract import TRAINING_FIELDS, require_matched_candidate


@pytest.fixture
def reference():
    result = dict(data_pins={'roles': 'a'*64, 'encoding': 'b'*64}, roles_identity='r',
        encoding_identity='e', train_view_identity='t', train_targets=100,
        selection_targets=20, prediction_implementation='legacy_single_window_v1',
        initial_backbone_sha256='c'*64, numeric_profile={'dtype': 'float32'},
        training_config={key: index for index, key in enumerate(TRAINING_FIELDS)},
        selection_population_sha256='d'*64)
    return result


def candidate(reference, name='A1_EXPERT'):
    result = deepcopy(reference)
    result.update(candidate_id=name, observed_selection_population_sha256='d'*64,
        graph_provenance=dict(train_view_identity='t', encoding_identity='e',
            history_scope='effective_native_window_prefix', artifact_sha256='f'*64,
            uses_oracle_labels=False, confidence_fit_view_identity='t',
            confidence_artifact_sha256='1'*64))
    return result


@pytest.mark.parametrize('name', ['A0','A1_EXPERT','A1_LEARNED','A2_EXPERT','A2_LEARNED','A3_EXPERT','A3_LEARNED'])
def test_equal_contract_and_observed_population(reference, name):
    require_matched_candidate(reference, candidate(reference, name), observed=True)


@pytest.mark.parametrize('field', TRAINING_FIELDS)
def test_changed_training_budget_or_architecture_rejected(reference, field):
    value = candidate(reference)
    value['training_config'][field] = 'changed'
    with pytest.raises(ValueError, match='Training mismatch'):
        require_matched_candidate(reference, value)


@pytest.mark.parametrize('field', ['data_pins','roles_identity','encoding_identity',
    'train_view_identity','train_targets','selection_targets','initial_backbone_sha256',
    'numeric_profile','prediction_implementation'])
def test_changed_population_and_execution_recipe_rejected(reference, field):
    value = candidate(reference)
    value[field] = 'changed'
    with pytest.raises(ValueError, match='Comparison mismatch'):
        require_matched_candidate(reference, value)


@pytest.mark.parametrize('field,value', [
    ('train_view_identity','selection'), ('encoding_identity','different'),
    ('history_scope','full_learner_history'), ('uses_oracle_labels',True),
    ('artifact_sha256',None), ('artifact_sha256','unpinned'),
    ('confidence_fit_view_identity','calibration'),
    ('confidence_artifact_sha256',None), ('confidence_artifact_sha256','unpinned')])
def test_leaked_graph_or_confidence_rejected(reference, field, value):
    condition = candidate(reference, 'A3_EXPERT')
    condition['graph_provenance'][field] = value
    with pytest.raises(ValueError):
        require_matched_candidate(reference, condition)


def test_equal_counts_do_not_replace_observed_target_identity(reference):
    condition = candidate(reference)
    condition['observed_selection_population_sha256'] = 'other_rows_same_count'
    require_matched_candidate(reference, condition)
    with pytest.raises(ValueError, match='target population'):
        require_matched_candidate(reference, condition, observed=True)
