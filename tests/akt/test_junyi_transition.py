"""Fixture dict kiểm chuyển nguồn A1, không import Torch hoặc đọc artifact."""

from copy import deepcopy

import pytest

from knowledge_tracing.akt.research_junyi_transition import (
    CHECKS, CONFIG_FIELDS, PROFILE_FIELDS, identity_sha256, validate_source_transition,
)


def identities():
    source = dict(kind='junyi_a1_selected_v1', inputs='1'*64, encoding='2'*64,
                  prediction_implementation='batched_windows_v1_batch128',
                  config={name: 1 for name in CONFIG_FIELDS},
                  profile={name: False for name in PROFILE_FIELDS},
                  source_build_sha256='3'*64, candidate_id='A1_EXPERT',
                  batch_factory=dict(condition_sha256='4'*64, encoding_sha256='2'*64,
                                     phase_sha256='5'*64, graph_enabled=True),
                  comparison_reference_sha256='6'*64, validation_batch_size=128)
    source['config'].update(run_id='source', output_dir='/output/source',
                            max_seconds=1500, max_wall_seconds=1600)
    target = deepcopy(source)
    target['config'].update(run_id='target', output_dir='/output/target')
    target.update(source_build_sha256='7'*64, selection_cache_manifest_sha256='8'*64,
                  prefetch_train_windows=True)
    target['batch_factory'].update(context_backend='compact-a1-v1', graph_context_cache='9'*64)
    return source, target


def receipt(source, target):
    return dict(status='PASS_ACTUAL_CHECKPOINT_PARITY', checkpoint_sha256='a'*64,
                source_identity_sha256=identity_sha256(source), target_identity_sha256=identity_sha256(target),
                max_absolute_drift=0.0, checks={name: True for name in CHECKS})


def validate(source, target, evidence=None):
    validate_source_transition(source, target, receipt(source, target) if evidence is None else evidence,
                               checkpoint_sha256='a'*64)


def test_explicit_transition_accepts_exact_parity():
    source, target = identities()
    assert validate(source, target) is None
    target['config'].update(max_seconds=1200, max_wall_seconds=1300)
    validate(source, target)


@pytest.mark.parametrize('field', ['inputs', 'encoding', 'prediction_implementation', 'kind',
                                  'candidate_id', 'comparison_reference_sha256', 'validation_batch_size'])
def test_frozen_identity_rejected_even_with_rebound_receipt(field):
    source, target = identities()
    target[field] = 'b'*64
    with pytest.raises(ValueError):
        validate(source, target)


@pytest.mark.parametrize('field', sorted(CONFIG_FIELDS - {'run_id', 'output_dir', 'max_seconds', 'max_wall_seconds'}))
def test_every_frozen_config_field_rejected(field):
    source, target = identities()
    target['config'][field] = 2
    with pytest.raises(ValueError):
        validate(source, target)


@pytest.mark.parametrize('field', ['condition_sha256', 'encoding_sha256', 'phase_sha256', 'graph_enabled'])
def test_frozen_factory_rejected(field):
    source, target = identities()
    target['batch_factory'][field] = False if field == 'graph_enabled' else 'b'*64
    with pytest.raises(ValueError):
        validate(source, target)


@pytest.mark.parametrize('section', [None, 'config', 'batch_factory', 'profile'])
@pytest.mark.parametrize('mutation', ['unknown', 'missing'])
def test_closed_identity_schemas(section, mutation):
    source, target = identities()
    changed = target if section is None else target[section]
    if mutation == 'unknown':
        changed['unknown'] = 1
    else:
        del changed[next(iter(changed))]
    with pytest.raises(ValueError):
        validate(source, target)


@pytest.mark.parametrize('drift', [True, None, '0', 1e-12, float('nan'), float('inf'), -float('inf')])
def test_invalid_drift_rejected(drift):
    source, target = identities()
    evidence = receipt(source, target)
    evidence['max_absolute_drift'] = drift
    with pytest.raises(ValueError):
        validate(source, target, evidence)


@pytest.mark.parametrize('field', ['checkpoint_sha256', 'source_identity_sha256', 'target_identity_sha256', 'status'])
def test_receipt_binding_rejected(field):
    source, target = identities()
    evidence = receipt(source, target)
    evidence[field] = 'b'*64
    with pytest.raises(ValueError):
        validate(source, target, evidence)


@pytest.mark.parametrize('field', sorted(CHECKS))
@pytest.mark.parametrize('value', [False, 1, None])
def test_every_check_requires_true(field, value):
    source, target = identities()
    evidence = receipt(source, target)
    evidence['checks'][field] = value
    with pytest.raises(ValueError):
        validate(source, target, evidence)


def test_profile_and_nonfinite_config_rejected():
    source, target = identities()
    target['profile']['seed'] = 2
    with pytest.raises(ValueError):
        validate(source, target)
    source, target = identities()
    target['config']['max_seconds'] = float('nan')
    with pytest.raises(ValueError):
        validate(source, target)


def test_boolean_does_not_equal_numeric_frozen_value():
    source, target = identities()
    target['config']['seed'] = True
    with pytest.raises(ValueError):
        validate(source, target)


@pytest.mark.parametrize('section', [None, 'checks'])
@pytest.mark.parametrize('mutation', ['unknown', 'missing'])
def test_receipt_closed_schemas(section, mutation):
    source, target = identities()
    evidence = receipt(source, target)
    changed = evidence if section is None else evidence[section]
    if mutation == 'unknown':
        changed['unknown'] = True
    else:
        del changed[next(iter(changed))]
    with pytest.raises(ValueError):
        validate(source, target, evidence)


@pytest.mark.parametrize('field,value', [('max_seconds', 0), ('max_wall_seconds', -1),
                                        ('max_seconds', True), ('run_id', ''), ('output_dir', None)])
def test_invalid_mutable_config_rejected(field, value):
    source, target = identities()
    target['config'][field] = value
    with pytest.raises(ValueError):
        validate(source, target)


@pytest.mark.parametrize('field,value', [('context_backend', 'unknown'), ('graph_context_cache', 'bad')])
def test_invalid_factory_optimization_rejected(field, value):
    source, target = identities()
    target['batch_factory'][field] = value
    with pytest.raises(ValueError):
        validate(source, target)


def test_validation_preserves_input_dicts():
    source, target = identities()
    evidence = receipt(source, target)
    saved = deepcopy((source, target, evidence))
    validate(source, target, evidence)
    assert (source, target, evidence) == saved


@pytest.mark.parametrize('value', [False, True])
def test_optional_selection_prefetch_boolean_accepted(value):
    source, target = identities()
    target['prefetch_selection_windows'] = value
    validate(source, target)


@pytest.mark.parametrize('value', [None, 0, 1, 'true', [], {}])
def test_optional_selection_prefetch_requires_boolean(value):
    source, target = identities()
    target['prefetch_selection_windows'] = value
    with pytest.raises(ValueError):
        validate(source, target)
