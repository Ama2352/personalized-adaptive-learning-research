"""Manufactured tmp artifacts only; không thực hiện solver/NN/teacher.

Các metadata counters dưới đây là fixture, không chứng nhận actual fits. Default
suite không phụ thuộc artifacts/binary/untracked outputs của máy phát triển.
"""
from dataclasses import FrozenInstanceError, replace
import builtins
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from knowledge_tracing import edge_confidence_artifact as reader
from knowledge_tracing.shared_kt import PrerequisiteGraph
from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem, identity_hash

H = 'a' * 64


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture(autouse=True)
def no_solver_or_neural_import(monkeypatch):
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split('.')[0] in {'torch', 'sklearn', 'scipy', 'pandas', 'joblib'}:
            raise AssertionError('data-only loader must not import model/solver: ' + name)
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.setattr(reader, 'ROOT', tmp_path)
    operation = 'artifacts/akt/method24-fixture'
    output = operation + '/method24-native01'
    (tmp_path / output).mkdir(parents=True)
    bank = SimulatorBank('manufactured-no-generated-corpus', tuple(
        SimulatorItem(f'c{i:02d}-{d}', f'c{i:02d}', d) for i in range(28) for d in (1050, 1200, 1350)))
    nodes = tuple(f'c{i:02d}' for i in range(28))
    learned_edges = [(p, c) for p in nodes for c in nodes if p < c][:31]
    declared = PrerequisiteGraph.from_edges(nodes, [('c27', 'c25'), ('c27', 'c26')])
    learners = [f'u{i:02d}' for i in range(48)]
    sources = {p: H for p in (
        operation + '/method24_worker01.py', operation + '/run_method24_native01.py',
        'scripts/research/windows_owned_worker.py', 'src/knowledge_tracing/__init__.py',
        'src/knowledge_tracing/akt/__init__.py', 'src/knowledge_tracing/akt/resources.py',
        'src/knowledge_tracing/edge_confidence.py', 'src/knowledge_tracing/simulator_bridge.py',
        'src/knowledge_tracing/simulator_corpus_reader.py', 'src/knowledge_tracing/simulator_data.py',
        'src/knowledge_tracing/simulator_research_data.py')}
    public = {n: H for n in reader.PUBLIC}
    recipe = dict(method_id='train-lagged-edge-confidence-v1', seed=42, folds=3, laplace_alpha=1.,
        support_scale=5., C=1., tol=1e-6, max_iter=200, clip=1e-6, bootstrap_replicates=200, min_eligible_learners=20)
    counts = dict(train_learners=48, train_events=10080, concepts=28, edges=756, fit_slots=2352,
        oof_rows=272160, baseline_oof_rows=10080, dag_budget=31, source_files=11)
    caps = dict(outer_seconds=120, active_seconds=110, cleanup_seconds=3, outer_finalization_seconds=7,
        export_reserve_seconds=8, max_rss_bytes=536870912, min_available_ram_bytes=1073741824,
        poll_seconds=.1, max_total_output_bytes=134217728, max_oof_file_bytes=100663296, max_stdout_stderr_bytes=65536)
    config = dict(schema_version=1, purpose=reader.PURPOSE,
        corpus=dict(id='manufactured-not-corpus', corpus_sha256=H, done_sha256=H, plan_sha256=H,
            train_provenance_sha256=H, train_observable_sha256=H,
            prior_inventory_relative='artifacts/akt/manufactured-inventory-not-opened.json', prior_inventory_sha256=H),
        recipe=recipe, counts=counts, caps=caps, scope_vi='PURE_METADATA_FIXTURE_NOT_EXECUTION')
    package = dict(distribution='numpy', version='fixture-version-not-installed', required=True,
        metadata_relative='.venv/Lib/site-packages/numpy-fixture.dist-info/METADATA', metadata_sha256=H,
        record_relative='.venv/Lib/site-packages/numpy-fixture.dist-info/RECORD', record_sha256=H,
        module_relative='.venv/Lib/site-packages/numpy/__init__.py', module_sha256=H)
    profile = dict(schema_version=1, scope='MANUFACTURED_NO_RUNTIME_ATTESTATION',
        lock_relative='requirements-akt.lock.txt', lock_sha256=H,
        protocol_relative='docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md', protocol_sha256=H,
        entry_sha256=H, cfg_sha256=H, method_source_sha256=H,
        extra_sources={'.venv/Lib/site-packages/sklearn/linear_model/_logistic.py': H},
        packages={'numpy': package}, limits_vi='Metadata only; these files do not exist in fixture')
    runtime_files = reader._runtime_files(profile)
    actor = dict(pid=1234, created_filetime_100ns='1', create_time=1., image='MANUFACTURED_NOT_EXECUTABLE')
    parent = dict(actor, pid=1233)
    owner = dict(status='OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE', worker=actor, parent_owner=parent,
        os_parent_pid=1233, nonce='fixture', ready_sha256=H, job_name='FAKE_NO_JOB_CREATED', preGO_forbidden_imports=[])
    owned = dict(status='ACCEPTED_OWNED_PROCESS_LAUNCH_NOT_SCIENTIFIC_ACCEPTANCE', GO_released=True,
        command=['NOT_EXECUTED'], parent=parent, approval_reference='MANUFACTURED_NO_AUTHORITY',
        job_name=owner['job_name'], helper_sha256=H, worker_sha256=H, actual_worker=actor, popen=actor,
        preGO_owned_tokens=[actor], actual_worker_in_job_before_GO=True, worker_returncode_before_cleanup=0,
        active_process_samples=[1], job_active_before_cleanup=0, job_active_after_cleanup=0,
        popen_handle_closed=True, cleanup_errors=[], cleanup_accepted=True, observed_owned_tokens=[actor],
        output_sha256={'stdout.log': H, 'stderr.log': H}, accepted=True, errors=[], elapsed_seconds=1.,
        max_seconds=110., cleanup_reserve_seconds=3., returncode=0, automatic_retry=False,
        elapsed_scope='MANUFACTURED_NO_PROCESS')
    resources = dict(samples=1, observed_peak_rss_bytes=1024, observed_minimum_available_ram_bytes=2**31,
                     guard_scope='MANUFACTURED_NOT_MEASURED')
    origin = dict(origin=package['module_relative'], sha256=H, version=package['version'])
    runtime = dict(environment_threads=dict(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'),
        native_windows_metadata=dict(phase='NATIVE_WINDOWS_METADATA_BOOTSTRAP_ONLY', phase_closed=True,
            helper_calls=1, blocked_bootstrap_attempts=0, outside_phase_popen_attempts=0),
        origins_after={'numpy': origin}, origins_before={'numpy': origin}, prefix='NOT_ACTUAL_PREFIX',
        process_counts=dict(fit_phase_popen_attempts=0, metadata_bootstrap_helpers=1,
            outside_metadata_phase_popen_attempts=0, overall_permitted_worker_child_popen_events=1),
        profile_sha256=None, scope='MANUFACTURED_NO_IMPORT', sys_executable='NOT_EXECUTED', threadpools=[{'num_threads': 1}])
    records = [dict(parent_id=p, child_id=c, full_child_targets=360, eligible_targets=20, excluded_targets=340,
        eligible_learners=20, eligible_class_counts=[10, 10], unary_evaluation_labels=False,
        fold_population=[[0, 120, 7, 7], [1, 120, 7, 7], [2, 120, 6, 6]], supported=True, reason=None,
        learner_deltas=[[u, .1] for u in learners[:20]], point_delta=.1, bootstrap_seed=42,
        bootstrap_positive=200, bootstrap_replicates=200, confidence=1.) for p in nodes for c in nodes if p != c]
    value = SimpleNamespace(root=tmp_path, operation=operation, output=output, bank=bank, declared=declared,
        nodes=nodes, learned_edges=learned_edges, learners=learners, sources=sources, public=public,
        config=config, profile=profile, runtime=runtime, owned=owned, owner=owner, resources=resources,
        records=records, overrides={}, raw_edges=None, mode='declared')
    value.limits = reader.Method24ReadLimits(128*1024, 2*1024**2, 32*1024, 2*1024**2, 6*1024**2, 28, 756, 20.)
    def put(relative, raw):
        path = tmp_path / relative
        path.write_bytes(raw)
        return sha(raw)
    def seal():
        """Chỉ ghi lại tmp fixture trước read; không động vào source/artifact thật."""
        metadata_shas = {}
        metadata_shas['config_sha256'] = put(operation + '/method24_config01.json', encode(config))
        metadata_shas['runtime_profile_sha256'] = put(operation + '/method24_runtime_profile01.json', encode(profile))
        request = dict(schema_version=1, purpose=reader.PURPOSE, approval_reference=owned['approval_reference'],
            config_sha256=metadata_shas['config_sha256'], runtime_profile_sha256=metadata_shas['runtime_profile_sha256'],
            source_count=11, source_sha256=sources, public_sha256=public, output_relative=output)
        request.update(value.overrides.get('request', {}))
        metadata_shas['request_sha256'] = put(operation + '/method24_request01.json', encode(request))
        request_sha = metadata_shas['request_sha256']
        runtime['profile_sha256'] = metadata_shas['runtime_profile_sha256']
        artifact_map = {}
        def item(name, raw):
            artifact_map[name] = dict(sha256=put(output + '/' + name, raw), bytes=len(raw))
        item('recipe.json', encode(recipe))
        item('folds.json', encode(dict(prepared_sha256=H, learner_ids=learners,
            folds=[[u, i % 3] for i, u in enumerate(learners)])))
        for name in ('fit-ledger.jsonl', 'baseline-oof.csv', 'edge-oof.csv', 'learner-deltas.csv'):
            item(name, b'FIXTURE_ONLY_NO_FITS_OR_OOF_POPULATION\n')
        item('edges.jsonl', value.raw_edges if value.raw_edges is not None else b''.join(encode(r) for r in records))
        graph = dict(status='SUPPORTED_DAG' if len(value.learned_edges) == 31 else 'UNSUPPORTED_EDGE_BUDGET',
            edge_confidence_sha256=H, nodes=list(nodes), requested_edges=31, edges=value.learned_edges,
            rejected_cycles=[], considered_positive_supported=sum(r['supported'] and r['point_delta'] > 0 for r in records))
        graph.update(value.overrides.get('graph', {}))
        graph['content_sha256'] = identity_hash(graph)
        item('graph.json', encode(graph))
        inventory = dict(oracle_files_opened=False, public_after=public, public_before=public,
            public_schema_audit_roles=['train', 'selection', 'calibration'], runtime_after=runtime_files,
            runtime_before=runtime_files, sources_after=sources, sources_before=sources, train_only_optimization=True)
        inventory.update(value.overrides.get('inventory', {}))
        item('input-source-inventory.json', encode(inventory)); item('runtime.json', encode(runtime))
        item('resources.json', encode(resources))
        item('reservation.json', encode(dict(automatic_retry=False, fit_slots=2352, neural_optimizer_steps=0,
            oof_rows=272160, owner=owner, request_sha256=request_sha, solver_calls=None,
            status='RESERVED_NOT_ACTUAL_FIT_COUNTS', teacher_calls=0)))
        worker = dict(actual_solver_calls=2352, config_sha256=metadata_shas['config_sha256'],
            data_sha256={n: artifact_map[n] for n in reader.DATA}, edge_summaries=756,
            graph_edges=len(value.learned_edges), graph_status=graph['status'], modal_spend_usd=0,
            neural_optimizer_steps=0, oof_rows=272160, outer_acceptance_required=True, owner=owner,
            prepared_sha256=H, processed_fit_slots=2352, request_sha256=request_sha, resources=resources,
            result_sha256=H, status='COMPLETE_CONDITIONAL_SURROGATE_PENDING_OUTER_ACCEPTANCE',
            supported_edges=sum(r['supported'] for r in records), teacher_calls=0)
        worker.update(value.overrides.get('worker', {})); item('worker_result.json', encode(worker))
        done = dict(schema_version=1, status='COMPLETE_METHOD24_PENDING_OUTER_ACCEPTANCE', request_sha256=request_sha,
                    files_sha256={n: v['sha256'] for n, v in artifact_map.items()})
        done.update(value.overrides.get('done', {})); item('DONE.json', encode(done))
        outer = dict(status='ACCEPTED_CONDITIONAL_TRAIN_SURROGATE_NOT_EDGE_TRUTH', error=None,
            elapsed_before_receipt_seconds=1., request_sha256=request_sha, reserved_solver_calls=2352,
            actual_solver_calls=2352, artifacts=artifact_map, owned_cleanup_accepted=True, automatic_retry=False,
            graph_status=graph['status'], terminal_RC0_and_no_postbudget_failure_required=True,
            teacher_calls=0, neural_optimizer_steps=0, modal_spend_usd=0)
        outer.update(value.overrides.get('outer', {}))
        metadata_shas['outer_run_sha256'] = put(operation + '/method24_run01.json', encode(outer))
        terminal = dict(kind='ROOT_OBSERVATION_OF_TOOL_TERMINAL_NOT_WORKER_GENERATED', tool_session_id=1,
            observed_exit_code=0, stdout_json=dict(status=outer['status'], elapsed_seconds=2., error=None,
                run_sha256=metadata_shas['outer_run_sha256']), scope_vi='MANUFACTURED_NO_TOOL_RUN')
        terminal['stdout_json'].update(value.overrides.get('terminal_stdout', {}))
        terminal.update(value.overrides.get('terminal', {}))
        metadata_shas['terminal_sha256'] = put(operation + '/method24_terminal_observation01.json', encode(terminal))
        metadata_shas['owned_receipt_sha256'] = put(operation + '/method24_owned_receipt01.json', encode(owned))
        value.ref = reader.Method24ArtifactRef(operation, output, **metadata_shas, done_sha256=artifact_map['DONE.json']['sha256'])
        value.expected = reader.Method24TrainingBinding('manufactured-not-corpus', H, H, H, H, H,
            identity_hash(bank.identity), H, metadata_shas['config_sha256'], metadata_shas['runtime_profile_sha256'],
            tuple(sorted(public.items())), tuple(sorted(sources.items())), tuple(sorted(runtime_files.items())))
    value.seal = seal
    def load():
        return reader.load_method24_scores(value.ref, expected_training=value.expected, bank=bank,
            declared_graph=value.declared, graph_binding=value.mode, limits=value.limits)
    value.load = load
    seal()
    return value


def test_complete_declared_scores_are_immutable_data_not_confidence_tensor(case):
    result = case.load()
    assert len(result.edge_scores) == 2 and all(r.score == 1. for r in result.edge_scores)
    assert result.score_semantics == reader.SEMANTICS and result.fit_scope == 'train80'
    assert result.training == case.expected and result.identity == case.load().identity
    assert result.actual_solver_calls == result.processed_fit_slots == 2352  # Declared fixture counters only.
    assert not hasattr(result, 'to_edge_confidence') and not hasattr(result, 'estimated_probability')
    with pytest.raises(FrozenInstanceError):
        result.fit_scope = 'refit90'


def test_supported_zero_remains_distinct_from_unsupported_null(case):
    first, second = [next(r for r in case.records if (r['parent_id'], r['child_id']) == pair)
                     for pair in case.declared.edges]
    first.update(confidence=0., bootstrap_positive=0, point_delta=-.1,
                 learner_deltas=[[u, -.1] for u in case.learners[:20]])
    second.update(supported=False, reason='FOLD_FIT_OR_PREDICTION_UNSUPPORTED', confidence=None,
                  bootstrap_positive=None, point_delta=None, learner_deltas=[])
    case.seal(); result = case.load()
    a, b = result.edge_scores
    assert a.supported and a.score == 0. and a.reason is None
    assert not b.supported and b.score is None and b.reason == 'FOLD_FIT_OR_PREDICTION_UNSUPPORTED'


def test_learned_binding_requires_exact31_edge_dag(case):
    case.mode = 'method24_learned'
    case.declared = PrerequisiteGraph.from_edges(case.nodes, case.learned_edges)
    result = case.load()
    assert len(result.edge_scores) == 31 and result.declared_edges == case.declared.edges


def test_learned_binding_rejects_different_declared_graph(case):
    case.mode = 'method24_learned'
    with pytest.raises(ValueError, match='exact accepted31'):
        case.load()


def test_expert_scores_allow_unsupported_learned_budget_but_learned_binding_rejects(case):
    case.learned_edges = case.learned_edges[:30]
    positive = {tuple(pair) for pair in case.learned_edges}
    for row in case.records:
        if (row['parent_id'], row['child_id']) not in positive:
            row.update(point_delta=-.1, confidence=0., bootstrap_positive=0,
                       learner_deltas=[[u, -.1] for u in case.learners[:20]])
    case.seal()
    assert all(r.score == 0. for r in case.load().edge_scores)
    case.mode = 'method24_learned'
    case.declared = PrerequisiteGraph.from_edges(case.nodes, case.learned_edges)
    with pytest.raises(ValueError, match='exact accepted31'):
        case.load()


@pytest.mark.parametrize('problem', ['pending_outer', 'terminal_rc', 'cleanup', 'unknown_counts',
    'wrong_owner', 'source_drift', 'runtime_drift', 'oracle', 'late_elapsed', 'teacher', 'thread_count', 'extra_schema'])
def test_rejects_semantically_invalid_even_externally_pinned_envelope(case, problem):
    if problem == 'pending_outer': case.overrides['outer'] = dict(status='PENDING')
    elif problem == 'terminal_rc': case.overrides['terminal'] = dict(observed_exit_code=1)
    elif problem == 'cleanup': case.owned['cleanup_accepted'] = False
    elif problem == 'unknown_counts': case.overrides['outer'] = dict(actual_solver_calls=None)
    elif problem == 'wrong_owner': case.owned['actual_worker'] = dict(pid=999)
    elif problem == 'source_drift': case.overrides['inventory'] = dict(sources_after={})
    elif problem == 'runtime_drift': case.overrides['inventory'] = dict(runtime_after={})
    elif problem == 'oracle': case.overrides['inventory'] = dict(oracle_files_opened=True)
    elif problem == 'late_elapsed': case.overrides['terminal_stdout'] = dict(elapsed_seconds=121.)
    elif problem == 'teacher': case.overrides['worker'] = dict(teacher_calls=1)
    elif problem == 'thread_count': case.runtime['threadpools'] = [{'num_threads': 2}]
    else: case.overrides['worker'] = dict(unknown_extra=True)
    case.seal()
    with pytest.raises(ValueError): case.load()


@pytest.mark.parametrize('problem', ['duplicate', 'missing', 'supported_null', 'unsupported_zero',
    'bool_score', 'score_fraction', 'foreign_learner', 'point_mismatch', 'fold_counts', 'self_loop'])
def test_rejects_invalid_edge_summaries_without_reestimating(case, problem):
    row = next(r for r in case.records if (r['parent_id'], r['child_id']) == case.declared.edges[0])
    if problem == 'duplicate': case.records.append(copy.deepcopy(row))
    elif problem == 'missing': case.records.remove(row)
    elif problem == 'supported_null': row['confidence'] = None
    elif problem == 'unsupported_zero': row.update(supported=False, reason='unsupported', confidence=0.)
    elif problem == 'bool_score': row['confidence'] = True
    elif problem == 'score_fraction': row['confidence'] = .99
    elif problem == 'foreign_learner': row['learner_deltas'][0][0] = 'calibration-learner'
    elif problem == 'point_mismatch': row['point_delta'] = .2
    elif problem == 'fold_counts': row['fold_population'][0][2] += 1
    else: row['parent_id'] = row['child_id']
    case.seal()
    with pytest.raises(ValueError): case.load()


@pytest.mark.parametrize('raw', [b'{"parent_id":"a","parent_id":"b"}\n',
                              b'{"confidence":NaN}\n', b'{"confidence":1e999}\n'])
def test_duplicate_or_nonfinite_json_rejected(case, raw):
    case.raw_edges = raw; case.seal()
    with pytest.raises(ValueError): case.load()


def test_rejects_payload_byte_tamper_before_any_summary_parse(case):
    path = case.root / case.output / 'edge-oof.csv'
    path.write_bytes(path.read_bytes() + b'TAMPER')
    with pytest.raises(ValueError, match='byte cap|SHA'):
        case.load()


@pytest.mark.parametrize('marker', ['method24_outer_failure01.log', 'method24_postbudget_failure01.json'])
def test_outer_failure_marker_overrides_complete(case, marker):
    (case.root / case.operation / marker).write_text('FAILED')
    with pytest.raises(ValueError, match='failure|postbudget'):
        case.load()


def test_late_failure_after_posthash_still_rejected(case, monkeypatch):
    original = reader._Reader.finish
    def finish(self):
        original(self)
        (case.root / case.operation / 'method24_postbudget_failure01.json').write_text('late')
    monkeypatch.setattr(reader._Reader, 'finish', finish)
    with pytest.raises(ValueError, match='late outer failure'):
        case.load()


@pytest.mark.parametrize('path', ['dataset/no.csv', 'artifacts/akt/../oracle/no.json',
                                 'artifacts/akt//bad', 'C:/private/file'])
def test_bad_artifact_path_rejected_before_open(case, monkeypatch, path):
    case.ref = replace(case.ref, output_directory=path)
    monkeypatch.setattr(Path, 'open', lambda *a, **kw: pytest.fail('bad path reached open'))
    with pytest.raises(ValueError): case.load()


@pytest.mark.parametrize('alias', ['symlink', 'junction'])
def test_ancestor_alias_rejected_without_creating_links(case, monkeypatch, alias):
    parent = case.root / 'artifacts/akt'
    attribute = 'is_symlink' if alias == 'symlink' else 'is_junction'
    original = getattr(Path, attribute, lambda self: False)
    monkeypatch.setattr(Path, attribute, lambda self: self == parent or original(self), raising=False)
    with pytest.raises(ValueError, match='symlink|junction'):
        case.load()


@pytest.mark.parametrize('bound', ['metadata', 'edge_line', 'output', 'read', 'time'])
def test_explicit_resource_caps_cannot_be_bypassed(case, monkeypatch, bound):
    if bound == 'metadata': case.limits = replace(case.limits, max_metadata_bytes=10)
    elif bound == 'edge_line': case.limits = replace(case.limits, max_line_bytes=10)
    elif bound == 'output': case.limits = replace(case.limits, max_output_bytes=1, max_edge_file_bytes=1, max_line_bytes=1)
    elif bound == 'read':
        total = sum(p.stat().st_size for p in (case.root / case.output).iterdir())
        edge = (case.root / case.output / 'edges.jsonl').stat().st_size
        case.limits = replace(case.limits, max_output_bytes=total, max_edge_file_bytes=edge, max_read_bytes=total)
    else:
        clock = iter([0., 100.])
        monkeypatch.setattr(reader, 'time', SimpleNamespace(
            monotonic=lambda: next(clock, 100.), time=lambda: 0.))
    with pytest.raises(ValueError): case.load()


@pytest.mark.parametrize('problem', ['cycle', 'duplicate_graph_pair', 'node_population', 'budget'])
def test_learned_graph_checks_actual_structure_not_only_status(case, problem):
    case.mode = 'method24_learned'
    case.declared = PrerequisiteGraph.from_edges(case.nodes, case.learned_edges)
    if problem == 'cycle': case.learned_edges[-1] = [case.learned_edges[0][1], case.learned_edges[0][0]]
    elif problem == 'duplicate_graph_pair': case.learned_edges[-1] = case.learned_edges[0]
    elif problem == 'node_population': case.overrides['graph'] = dict(nodes=list(case.nodes[:-1]))
    else: case.overrides['graph'] = dict(requested_edges=30)
    case.seal()
    with pytest.raises(ValueError): case.load()


def test_wrong_external_train_or_bank_binding_rejected(case):
    case.expected = replace(case.expected, train_provenance_sha256='b' * 64)
    with pytest.raises(ValueError, match='lineage'): case.load()
    case.seal()
    case.expected = replace(case.expected, domain_sha256='b' * 64)
    with pytest.raises(ValueError, match='bank/domain'): case.load()


def test_only_fixed_artifact_files_opened_not_corpus_or_sources_or_runtime(case, monkeypatch):
    opened = []
    original = Path.open
    def checked(path, *args, **kwargs):
        relative = path.relative_to(case.root).as_posix()
        assert relative.startswith(case.operation + '/')
        assert '/oracle/' not in relative and not relative.startswith(('dataset/', '.venv/', 'src/'))
        opened.append(relative)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', checked)
    result = case.load()
    assert result.edge_scores and opened
    assert not any(name.endswith(('train.jsonl', 'selection.jsonl', 'calibration.jsonl', 'METADATA', 'RECORD')) for name in opened)
