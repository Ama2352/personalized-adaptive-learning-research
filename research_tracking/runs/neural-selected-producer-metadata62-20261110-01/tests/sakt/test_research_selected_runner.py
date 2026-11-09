"""SOURCE-ONLY pure metadata/joins, không fake live admission hoặc NN.

Normal import canonical SAKT modules, giữ nguyên class identity trong process.
Các SHA a/b/c và8/1/1 dưới đây chỉ là metadata fixtures. Không proof accepted,
corpus giả đã publication, mocked successful guard hoặc public fitted output.
ROOT review và cấp bounded pure allocation trước khi chạy file này.
"""
from dataclasses import asdict, replace
import hashlib
import json
from types import SimpleNamespace

import pytest


H = 'a'*64


@pytest.fixture(scope='module')
def modules():
    from knowledge_tracing.sakt import research_execution, research_runner
    assert research_runner.AuthorizedSAKTSelectedExecution is research_execution.AuthorizedSAKTSelectedExecution
    return research_execution, research_runner


def declared_spec(execution):
    from knowledge_tracing import research_admission as shared
    context = shared.MainSelectionContext('grade10_simulator', shared.PROTOCOL21, shared.RECIPE26,
        shared.ALLOCATION, H, 'b'*64, 'c'*64, 'd'*64, 'e'*64)
    sources = dict.fromkeys(execution.SOURCE_NAMES, H)
    sources.update({execution.RECIPE_PATH: execution.RECIPE_SHA256,
        'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md': context.protocol21_sha256,
        'docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md': context.recipe26_sha256,
        'docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json': context.allocation_sha256})
    budget = execution.SAKTSelectedBudget(8, 1, 1, 32, 4, 4, 50, 1600, 204,
        60., 120., 2**30, 2*2**30, 4*2**30, 2**18, 8*2**20, 8*2**20, 8*2**20, 512*2**20, 2)
    limits = execution.public_reader.CorpusReadLimits(2**20, 8*2**20, 2**16, 8, 4, 40, 10.)
    return execution.SAKTSelectedExecutionSpec('metadata-only', context, execution.SAKTSelectedRecipe(),
        'not-published', H, 'b'*64, json.dumps(asdict(limits)), tuple(sorted(sources.items())), budget)


def declared_evidence(execution):
    pin = execution.FilePin
    components = tuple(execution.SAKTComponentAcceptance(kind, pin('artifacts/akt/'+kind+'-outer.json', H),
        pin('artifacts/akt/'+kind+'-child.json', H), pin('artifacts/akt/'+kind+'-owned.json', H))
        for kind in ('epoch22', 'checkpoint33'))
    files = tuple(pin(name, H) for name in ('.venv/pyvenv.cfg', '.venv/Scripts/python.exe',
        '.venv/Lib/site-packages/torch/__init__.py', '.venv/Lib/site-packages/numpy/__init__.py'))
    return execution.SAKTSelectedEvidence(pin('artifacts/akt/runtime.json', H),
        pin('artifacts/akt/preflight/gate2-current.json', H), pin('requirements-akt.lock.txt', H), components, files)


@pytest.mark.parametrize('field,value', [('d_model', 4), ('head_dim', 200), ('context', 2),
    ('max_epochs', 2), ('dropout', 0.), ('batch_size', 32), ('seed', True), ('betas', [.9, .999])])
def test_recipe_is_adopted_not_a_toy_or_tuning_switch(modules, field, value):
    execution, _ = modules
    with pytest.raises(ValueError, match='exact adopted'):
        replace(execution.SAKTSelectedRecipe(), **{field: value})


@pytest.mark.parametrize('field,value', [('max_optimizer_steps', 49), ('max_optimized_targets', 1599),
                                      ('max_prediction_targets', 203)])
def test_reserve_all_declared_epochs_before_io(modules, field, value):
    execution, _ = modules
    spec = declared_spec(execution)
    with pytest.raises(ValueError, match='whole declared'):
        replace(spec, budget=replace(spec.budget, **{field: value}))


def test_registry_is_not_a_fixed_fitted_vocabulary(modules):
    execution, _ = modules
    spec = declared_spec(execution)
    assert spec.recipe.max_length == spec.recipe.context+1 == 101
    assert not hasattr(spec.recipe, 'num_items')
    assert execution.PHASES == ('select_train80', 'raw_selection10')
    assert spec.identity == replace(spec).identity


def test_sources_reject_protected_extra_path(modules):
    execution, _ = modules
    spec = declared_spec(execution)
    with pytest.raises(ValueError, match='source files'):
        replace(spec, expected_sources=tuple(sorted((*spec.expected_sources, ('dataset/secret.py', H)))))


def test_package_initializers_are_mandatory_source_bindings(modules):
    execution, _ = modules
    spec = declared_spec(execution)
    for name in ('src/knowledge_tracing/__init__.py', 'src/knowledge_tracing/akt/__init__.py',
                 'src/knowledge_tracing/sakt/__init__.py', 'src/knowledge_tracing/gam_kt/__init__.py'):
        assert name in execution.SOURCE_NAMES
        with pytest.raises(ValueError, match='all SAKT/shared method sources required'):
            replace(spec, expected_sources=tuple(row for row in spec.expected_sources if row[0] != name))


@pytest.mark.parametrize('kind', ['a0_scope', 'noauth_stage', 'extra_phase', 'schema_bool',
                                 'different_caps', 'caps_bool', 'extra_approved', 'wrong_spec'])
def test_real_entry_rejects_bad_closed_auth_before_reader_and_lazy_nn(modules, tmp_path, monkeypatch, kind):
    execution, runner = modules
    monkeypatch.setattr(execution, 'ROOT', tmp_path)
    spec = declared_spec(execution); evidence = declared_evidence(execution)
    auth = dict(schema_version=1, scope=execution.SCOPE, decision='AUTHORIZE_BOUNDED_SAKT_MAIN_SELECTED_ONLY',
        run_id=spec.run_id, spec_sha256=spec.identity, recipe_sha256=execution.RECIPE_SHA256,
        identity={}, caps=execution.canonical(asdict(spec.budget)), requested_phases=list(execution.PHASES),
        approval_reference='SYNTHETIC_INVALID_AUTH_NOT_A_GRANT')
    if kind == 'a0_scope': auth['scope'] = 'simulator-research-a0-selected-refit-calibration-v1'
    elif kind == 'noauth_stage': auth['decision'] = 'NO_EXECUTION_AUTHORITY'
    elif kind == 'extra_phase': auth['requested_phases'].append('refit_union90')
    elif kind == 'schema_bool': auth['schema_version'] = True
    elif kind == 'different_caps': auth['caps']['max_optimizer_steps'] += 1
    elif kind == 'caps_bool': auth['caps']['selection_learners'] = True
    elif kind == 'extra_approved': auth['approved'] = True
    else: auth['spec_sha256'] = '0'*64
    path = tmp_path/'artifacts/akt/invalid-auth.json'; path.parent.mkdir(parents=True)
    raw = json.dumps(auth, sort_keys=True).encode(); path.write_bytes(raw)
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError('No reader/model before rejected authorization')
    monkeypatch.setattr(runner, '_lazy', forbidden)
    monkeypatch.setattr(runner, 'read_public_research_corpus', forbidden)
    with pytest.raises(ValueError, match='closed SAKT authorization'):
        runner.run_sakt_selected_fit(spec, evidence, authorization_file='artifacts/akt/invalid-auth.json',
            expected_authorization_sha256=hashlib.sha256(raw).hexdigest())
    assert calls == [] and not spec.output.exists()


def prediction_fixture():
    from knowledge_tracing.simulator_bridge import ItemQuery
    targets, predictions = [], []
    for rank, probability in enumerate((.25, None)):
        query = ItemQuery('item'+str(rank), 100+rank, rank+1)
        target = SimpleNamespace(learner_id='learner', query=query, global_rank=rank, origin_role='selection',
            history_hash_scheme='observable-prefix-chain-v1', history_sha256=str(rank)*64,
            phase_sha256='c'*64, encoding_sha256='d'*64, correct=rank)
        targets.append(target)
        predictions.append(dict(learner_id=target.learner_id, source_row=query.source_row, global_rank=rank,
            item_id=query.item_id, timestamp=query.timestamp, origin_role=target.origin_role,
            history_hash_scheme=target.history_hash_scheme, history_sha256=target.history_sha256,
            phase_sha256=target.phase_sha256, encoding_sha256=target.encoding_sha256,
            probability=probability, support_reason='cold_query_only' if probability is not None else 'oov_item',
            prediction_status='scored' if probability is not None else 'unsupported'))
    return dict(status='complete', stop_reason='prediction_complete', truth_sidecar_complete=True,
        role='research_computation_only_no_selected_fit_attestation', resume_supported=False, fitted_research_model=False,
        binding=dict(phase_scope='raw_selection10', encoding_sha256='d'*64),
        ledger=dict(complete=True, input_population_complete=True, expected_targets=2),
        model_state_before=H, model_state_after=H, predictions=predictions, truth_sidecar=targets)


def test_raw_join_preserves_null_and_separates_input_reason(modules):
    _, runner = modules
    rows, reasons = runner.selection_rows(prediction_fixture())
    assert len(rows) == 2 and rows[0].support_reason == 'supported'
    assert reasons[rows[0].key] == 'cold_query_only'
    assert rows[1].probability is None and rows[1].support_reason == 'oov_item'
    population = runner.population(rows)
    assert population['scheme'] == 'model-neutral-selection-K-y-jsonl-v1'
    assert population['full_keys_sha256'] != population['full_keys_labels_sha256']


@pytest.mark.parametrize('kind', ['item', 'clock', 'history', 'phase', 'encoding', 'duplicate',
                                 'missing', 'unprocessed', 'nonfinite', 'label'])
def test_raw_join_rejects_mismatched_identity_or_invalid_prediction(modules, kind):
    _, runner = modules
    result = prediction_fixture(); row = result['predictions'][0]
    if kind == 'item': row['item_id'] = 'different'
    elif kind == 'clock': row['timestamp'] += 1
    elif kind == 'history': row['history_sha256'] = 'f'*64
    elif kind == 'phase': row['phase_sha256'] = 'f'*64
    elif kind == 'encoding': row['encoding_sha256'] = 'f'*64
    elif kind == 'duplicate': result['predictions'][1] = dict(row)
    elif kind == 'missing': result['predictions'].pop()
    elif kind == 'unprocessed': row['prediction_status'] = 'unprocessed'
    elif kind == 'nonfinite': row['probability'] = float('nan')
    else: result['truth_sidecar'][0].correct = True
    with pytest.raises(ValueError):
        runner.selection_rows(result)


def test_calibration_fields_cannot_enter_raw_selection_join(modules):
    _, runner = modules
    result = prediction_fixture()
    result['truth_sidecar'][0].origin_role = 'calibration'
    result['predictions'][0]['origin_role'] = 'calibration'
    with pytest.raises(ValueError, match='selection'):
        runner.selection_rows(result)


def test_execution_constructor_has_no_stage_or_bool_bypass(modules):
    execution, _ = modules
    with pytest.raises(ValueError, match='actual closed'):
        execution.AuthorizedSAKTSelectedExecution(None, None, None, None, {}, (0., 0.), object())
