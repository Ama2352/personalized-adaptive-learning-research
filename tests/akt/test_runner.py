import json
import subprocess
import hashlib
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest
import torch

from knowledge_tracing.akt.config import AKTConfig, PROJECT_ROOT, load_config, validate_config
import knowledge_tracing.akt.config as config_module
import knowledge_tracing.akt.runner as runner
import knowledge_tracing.akt.training as training
import knowledge_tracing.akt.watchdog as watchdog
from knowledge_tracing.akt.types import KTEvent, LearnerEvents


def config_hash(config):
    return hashlib.sha256(json.dumps(asdict(config), sort_keys=True, default=str).encode()).hexdigest()


@pytest.fixture
def synthetic_authorization_inputs(monkeypatch):
    # Test authorization so sánh identity, không phụ thuộc Gate1/data của máy.
    monkeypatch.setattr(runner, 'preflight', lambda _: {'source': {'commit': runner.SOURCE_COMMIT}})
    monkeypatch.setattr(runner, '_identity', lambda config, result: {
        'config_sha256': config_hash(config), 'source': result['source'],
        'assignments_sha256': 'synthetic-assignments'})


def test_no_phase_runs_by_default_without_requesting_any_learners(tmp_path, monkeypatch):
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'),
                     run_id='smoke-test', output_dir=PROJECT_ROOT / 'experiments/akt/results/smoke-test')
    def forbidden(*args, **kwargs):
        raise AssertionError('real learner source must not be requested')
    monkeypatch.setattr(runner, 'read_development_assignments', forbidden)
    monkeypatch.setattr(runner, 'iter_development_learners', forbidden)
    with pytest.raises(PermissionError, match='authorization'):
        runner.run_smoke(config)
    with pytest.raises(PermissionError, match='authorization'):
        runner.run_pilot(replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/pilot.json'),
                                 run_id='pilot-test', output_dir=PROJECT_ROOT / 'experiments/akt/results/pilot-test'))


def test_full_fold_refuses_without_future_authorization_and_no_cv_command():
    config = AKTConfig(phase='fold-readiness')
    with pytest.raises(PermissionError, match='full-fold'):
        runner.run_full_fold(config, authorization=None)
    with pytest.raises(SystemExit):
        runner.main(['cv'])


def test_json_writer_atomically_replaces_existing_json(tmp_path):
    path = tmp_path / 'progress.json'
    path.write_text('{"old":true}\n', encoding='utf-8')

    runner._write_json(path, {'new': True})

    assert json.loads(path.read_text(encoding='utf-8')) == {'new': True}
    assert list(tmp_path.glob('progress.json.*.tmp')) == []


def _mock_json_writer_os(monkeypatch, *, name, replace):
    # Chỉ thay os của runner; os.name toàn cục phải giữ host để pathlib/pytest hoạt động.
    monkeypatch.setattr(runner, 'os', SimpleNamespace(
        name=name, getpid=runner.os.getpid, fsync=runner.os.fsync, replace=replace))


@pytest.mark.parametrize('winerror', [5, 32, 33])
def test_json_writer_retries_a_transient_windows_replace_denial(tmp_path, monkeypatch, winerror):
    path = tmp_path / 'progress.json'
    path.write_text('{"old":true}\n', encoding='utf-8')
    real_replace = runner.os.replace
    attempts = []
    sleeps = []

    def replace_with_one_sharing_denial(source, target):
        attempts.append((Path(source), Path(target)))
        if len(attempts) == 1:
            error = PermissionError(13, 'access denied')
            error.winerror = winerror
            raise error
        return real_replace(source, target)

    _mock_json_writer_os(monkeypatch, name='nt', replace=replace_with_one_sharing_denial)
    monkeypatch.setattr(runner.time, 'sleep', sleeps.append)

    runner._write_json(path, {'new': True})

    assert len(attempts) == 2
    assert sleeps == [0.05]
    assert json.loads(path.read_text(encoding='utf-8')) == {'new': True}
    assert list(tmp_path.glob('progress.json.*.tmp')) == []


@pytest.mark.parametrize('winerror', [5, 32, 33])
def test_json_writer_propagates_persistent_denial_and_cleans_temp(tmp_path, monkeypatch, winerror):
    path = tmp_path / 'progress.json'
    path.write_text('{"old":true}\n', encoding='utf-8')
    attempts = []
    sleeps = []

    def always_denied(source, target):
        attempts.append((Path(source), Path(target)))
        error = PermissionError(13, 'access denied')
        error.winerror = winerror
        raise error

    _mock_json_writer_os(monkeypatch, name='nt', replace=always_denied)
    monkeypatch.setattr(runner.time, 'sleep', sleeps.append)

    with pytest.raises(PermissionError) as error:
        runner._write_json(path, {'new': True})

    assert error.value.winerror == winerror
    assert len(attempts) == 5
    assert sleeps == [0.05, 0.1, 0.2, 0.4]
    assert json.loads(path.read_text(encoding='utf-8')) == {'old': True}
    assert list(tmp_path.glob('progress.json.*.tmp')) == []


@pytest.mark.parametrize(('platform_name', 'winerror'), [
    ('posix', None), ('posix', 5), ('posix', 32), ('posix', 33),
    ('nt', None), ('nt', 87),
])
def test_json_writer_does_not_retry_non_transient_replace_denial(
        tmp_path, monkeypatch, platform_name, winerror):
    path = tmp_path / 'progress.json'
    path.write_text('{"old":true}\n', encoding='utf-8')
    attempts = []
    sleeps = []
    denial = PermissionError(13, 'access denied')
    if winerror is not None:
        denial.winerror = winerror

    def always_denied(source, target):
        attempts.append((Path(source), Path(target)))
        raise denial

    _mock_json_writer_os(monkeypatch, name=platform_name, replace=always_denied)
    monkeypatch.setattr(runner.time, 'sleep', sleeps.append)

    with pytest.raises(PermissionError) as error:
        runner._write_json(path, {'new': True})

    assert error.value is denial
    assert len(attempts) == 1
    assert sleeps == []
    assert json.loads(path.read_text(encoding='utf-8')) == {'old': True}
    assert list(tmp_path.glob('progress.json.*.tmp')) == []


@pytest.mark.parametrize('pilot_result', [
    {'status': 'complete', 'source_commit': runner.SOURCE_COMMIT,
     'summary': {'complete_epoch': True, 'validation_loss': 0.5,
                 'checkpoint_reload_state_exact': True}},
    {'status': 'complete', 'source_commit': runner.SOURCE_COMMIT,
     'summary': {'complete_epoch': True, 'validation_loss': 0.5,
                 'checkpoint_reload_state_exact': True,
                 'coverage': {'status': 'incomplete', 'expected_rows': 3, 'prediction_rows': 2}}},
])
def test_fold_readiness_rejects_pilot_without_complete_validation_checkpoint_and_export(
        tmp_path, pilot_result):
    path = tmp_path / 'pilot.json'
    path.write_text(json.dumps(pilot_result), encoding='utf-8')

    with pytest.raises(ValueError, match='pilot result lacks complete validation/checkpoint/export evidence'):
        runner.prepare_fold_readiness(AKTConfig(phase='fold-readiness'), pilot_result=path)


def test_fold_readiness_rejects_failed_pilot(tmp_path):
    path = tmp_path / 'pilot.json'
    path.write_text(json.dumps({'status': 'failed', 'source_commit': runner.SOURCE_COMMIT}),
                    encoding='utf-8')

    with pytest.raises(ValueError, match='pilot result is incomplete'):
        runner.prepare_fold_readiness(AKTConfig(phase='fold-readiness'), pilot_result=path)


def test_fold_readiness_accepts_only_complete_pilot_lifecycle(tmp_path):
    path = tmp_path / 'pilot.json'
    path.write_text(json.dumps({
        'status': 'complete', 'source_commit': runner.SOURCE_COMMIT,
        'summary': {'complete_epoch': True, 'validation_loss': 0.5,
                    'validation': {'predicted_rows': 3},
                    'checkpoint_reload_state_exact': True,
                    'checkpoint_sha256': 'synthetic-checkpoint-hash',
                    'coverage': {'status': 'complete', 'expected_rows': 3, 'prediction_rows': 3}},
    }), encoding='utf-8')

    result = runner.prepare_fold_readiness(AKTConfig(phase='fold-readiness'), pilot_result=path)

    assert result['status'] == 'pending-explicit-approval'


def test_private_fold_workflow_is_guarded_and_orders_selection_refit_export(tmp_path, monkeypatch):
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/fold0.json'),
                     project_root=tmp_path, phase='fold', run_id='fold-synthetic',
                     output_dir=tmp_path / 'experiments/akt/results/fold-synthetic', execution_enabled=True)
    config.output_dir.mkdir(parents=True)
    monkeypatch.setattr(config_module, 'PROJECT_ROOT', tmp_path)
    validate_config(config)
    assignments = pd.DataFrame({'user_id': ['train', 'val', 'outer'], 'fold': [1, 2, 0]})
    split = runner.make_inner_split(assignments, outer_fold=0, seed=config.seed)
    calls = []
    outer = lambda: iter([SimpleNamespace(user_id='outer', fold=0)])
    train = lambda: iter(())
    adapter = SimpleNamespace(run_identity={'id': 'refit'}, optimizer=object(), training_history=[])
    def selection(*args, **kwargs):
        calls.append('selection')
        return SimpleNamespace(selected_epoch=2)
    def refit(*args, **kwargs):
        calls.append(('refit', kwargs['selected_epochs'], kwargs['outer_train_users']))
        return adapter
    def save(path, *args, **kwargs):
        path.write_bytes(b'synthetic checkpoint')
        calls.append('save')
    def prediction(model, learners):
        assert [learner.user_id for learner in learners] == ['outer']
        calls.append('prediction')
        return iter(())
    def export(*args, **kwargs):
        assert [learner.user_id for learner in kwargs['expected_learners_factory']()] == ['outer']
        calls.append('export')
        return {'expected_rows': 1}
    monkeypatch.setattr(runner, 'select_checkpoint', selection)
    monkeypatch.setattr(runner, 'refit_outer_train', refit)
    monkeypatch.setattr(runner, 'save_checkpoint', save)
    monkeypatch.setattr(runner, 'iter_predictions', prediction)
    monkeypatch.setattr(runner, 'export_predictions', export)
    monkeypatch.setattr(runner, '_require_gate2_evidence', lambda config: {
        'status': 'PASS', 'report_sha256': 'gate-report', 'test_log_sha256': 'gate-log',
        'pointer_sha256': 'gate-pointer'})
    monkeypatch.setattr(runner, 'preflight', lambda config: {'status': 'ready'})
    monkeypatch.setattr(runner, '_identity', lambda config, preflight: {'run': 'synthetic'})
    monkeypatch.setattr(runner, 'read_development_assignments', lambda paths: assignments)
    authorization = {'full_fold': True, 'scope': 'development-fold', 'run_id': config.run_id,
                     'source_commit': config.source_commit, 'config_sha256': config_hash(config),
                     'approval_reference': 'synthetic-only', 'budget': {'max_steps': 1},
                     'identity': {'run': 'synthetic'}}
    kwargs = dict(inner_split=split, outer_train_users=('train', 'val'),
                  inner_train_factory=train, inner_val_factory=train, outer_train_factory=train,
                  outer_eval_factory=outer, identity={'run': 'synthetic'}, budget={'max_steps': 1})
    with pytest.raises(PermissionError):
        runner._orchestrate_full_fold(config, authorization=None, **kwargs)
    with pytest.raises(PermissionError, match='budget'):
        runner._orchestrate_full_fold(config, authorization={**authorization, 'budget': {'max_steps': 2}}, **kwargs)
    with pytest.raises(PermissionError, match='identity'):
        runner._orchestrate_full_fold(config, authorization={**authorization, 'identity': {'run': 'other'}}, **kwargs)
    with pytest.raises(ValueError, match='inner split'):
        runner._orchestrate_full_fold(config, authorization=authorization,
                                      **{**kwargs, 'inner_split': replace(split, split_hash='wrong')})
    result = runner._orchestrate_full_fold(config, authorization=authorization, **kwargs)
    assert calls == ['selection', ('refit', 2, ('train', 'val')), 'save', 'prediction', 'export']
    assert result['selected_epoch'] == 2 and result['coverage']['expected_rows'] == 1
    kwargs['outer_eval_factory'] = lambda: iter(())
    with pytest.raises(ValueError, match='incomplete'):
        runner._orchestrate_full_fold(config, authorization=authorization, **kwargs)


def test_smoke_and_pilot_cohorts_exclude_outer_users_deterministically():
    assignments = pd.DataFrame({
        'user_id': [f'u{i:02}' for i in range(50)],
        'partition': ['development'] * 50,
        'fold': [i % 5 for i in range(50)],
    })
    for phase in ('smoke', 'pilot'):
        selected = runner._select_inner_cohort(assignments, outer_fold=0, seed=42,
                                                phase=phase, max_train_users=12, max_val_users=5)
        again = runner._select_inner_cohort(assignments.sample(frac=1, random_state=4), outer_fold=0,
                                             seed=42, phase=phase, max_train_users=12,
                                             max_val_users=5)
        train, val, split = selected
        assert selected == again
        assert len(train) == 12 and len(val) == 4
        parent = runner.make_inner_split(assignments, outer_fold=0, seed=42)
        rank = lambda user: (hashlib.sha256(f'akt-{phase}-v1|42|0|{user}'.encode()).hexdigest(), user)
        assert train == tuple(sorted(parent.inner_train_users, key=rank)[:12])
        assert val == tuple(sorted(parent.inner_val_users, key=rank)[:5])
        assert not set(train) & set(val)
        assert all(int(user[1:]) % 5 != 0 for user in (*train, *val))
        assert split.outer_fold == 0


def test_config_cannot_expand_smoke_or_pilot_caps():
    smoke = load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json')
    with pytest.raises(ValueError, match='smoke cap'):
        validate_config(replace(smoke, max_steps=21))
    pilot = load_config(PROJECT_ROOT / 'experiments/akt/configs/pilot.json')
    with pytest.raises(ValueError, match='pilot cap'):
        validate_config(replace(pilot, max_total_targets=100001))


def test_configs_are_disabled_namespaced_and_gate_pass_is_not_authorization(monkeypatch, synthetic_authorization_inputs):
    configs = [load_config(PROJECT_ROOT / 'experiments/akt/configs' / name)
               for name in ('smoke.json', 'pilot.json', 'fold0.json')]
    assert all(config.execution_enabled is False for config in configs)
    assert len({config.run_id for config in configs}) == 3
    assert configs[0].output_dir.parent == configs[1].output_dir.parent == PROJECT_ROOT / 'experiments/akt/results'
    assert configs[2].output_dir.parent == PROJECT_ROOT / 'experiments/akt/readiness'
    monkeypatch.setattr(runner, '_require_gate2_evidence', lambda _: {
        'status': 'PASS', 'report_sha256': 'gate-report', 'test_log_sha256': 'gate-log',
        'pointer_sha256': 'gate-pointer'})
    gate = {'gate': 'PASS', 'status': 'PASS', 'source_commit': configs[0].source_commit}
    with pytest.raises(PermissionError, match='authorization'):
        runner._require_authorization(configs[0], gate)
    enabled = replace(configs[0], execution_enabled=True)
    approval = {
        'approved': True, 'scope': 'development-inner-only', 'phase': 'smoke',
        'run_id': enabled.run_id, 'source_commit': enabled.source_commit,
        'config_sha256': config_hash(enabled),
        'identity': runner._authorization_identity(enabled),
        'approval_reference': 'future-user-approval',
        'caps': {'max_train_users': 32, 'max_val_users': 16, 'max_targets_per_side': 4096,
                 'max_steps': 20, 'max_seconds': 120, 'max_wall_seconds': 300,
                 'max_rss_bytes': 2147483648, 'min_available_ram_bytes': 1073741824},
    }
    assert runner._require_authorization(enabled, approval) == approval
    with pytest.raises(PermissionError, match='authorization'):
        runner._require_authorization(replace(enabled, seed=43), approval)
    with pytest.raises(PermissionError, match='gate evidence'):
        runner._require_authorization(enabled, {**approval, 'status': 'PASS'})
    with pytest.raises(PermissionError, match='exceeds'):
        runner._require_authorization(enabled, {**approval, 'caps': {**approval['caps'], 'max_steps': 21}})
    for name, invalid in [('max_steps', 2.5), ('max_train_users', True), ('max_seconds', float('nan')),
                          ('max_wall_seconds', float('inf'))]:
        with pytest.raises(PermissionError):
            runner._require_authorization(enabled, {**approval, 'caps': {**approval['caps'], name: invalid}})


def test_smoke_authorization_binds_exact_data_identity_and_phase(monkeypatch):
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'),
                     execution_enabled=True)
    identity = {
        'source': {'commit': config.source_commit, 'akt_py_sha256': 'source-hash'},
        'canonical_manifest_sha256': 'canonical-hash',
        'assignments_sha256': 'assignments-hash',
        'split_manifest_sha256': 'split-hash',
    }
    monkeypatch.setattr(runner, '_authorization_identity', lambda candidate: identity, raising=False)
    caps = {'max_train_users': 32, 'max_val_users': 16, 'max_targets_per_side': 4096,
            'max_steps': 20, 'max_seconds': 120, 'max_wall_seconds': 300,
            'max_rss_bytes': 2147483648, 'min_available_ram_bytes': 1073741824}
    approval = {
        'approved': True, 'scope': 'development-inner-only', 'phase': 'smoke',
        'run_id': config.run_id, 'source_commit': config.source_commit,
        'config_sha256': config_hash(config), 'identity': identity,
        'approval_reference': 'synthetic-user-authorization', 'caps': caps,
    }
    assert runner._require_authorization(config, approval) == approval
    with pytest.raises(PermissionError, match='identity'):
        runner._require_authorization(config, {**approval, 'identity': {**identity, 'assignments_sha256': 'other'}})
    with pytest.raises(PermissionError, match='identity'):
        runner._require_authorization(config, {key: value for key, value in approval.items() if key != 'identity'})
    with pytest.raises(PermissionError, match='authorization'):
        runner._require_authorization(replace(config, run_id='different'), approval)
    with pytest.raises(PermissionError, match='authorization'):
        runner._require_authorization(config, {**approval, 'phase': 'pilot'})
    with pytest.raises(PermissionError, match='authorization'):
        runner._require_authorization(replace(config, phase='pilot'), approval)
    with pytest.raises(PermissionError, match='authorization'):
        runner._require_authorization(replace(config, phase='fold'), approval)


def test_checkpoint_reload_state_parity_is_exact():
    native = torch.nn.Linear(2, 1)
    adapter = SimpleNamespace(native=native)
    saved = {name: value.detach().clone() for name, value in native.state_dict().items()}
    payload = {'model_state_dict': saved}
    assert runner._checkpoint_state_matches(adapter, payload)
    payload['model_state_dict']['weight'][0, 0] += 0.01
    assert not runner._checkpoint_state_matches(adapter, payload)


def test_authorization_identity_includes_current_gate2_source_hashes(monkeypatch):
    config = AKTConfig()
    monkeypatch.setattr(runner, 'preflight', lambda candidate: {'source': 'pinned-runtime'})
    monkeypatch.setattr(runner, '_identity', lambda candidate, evidence: {'source': evidence['source']})
    monkeypatch.setattr(runner, '_gate2_build_hashes', lambda: {'runner.py': 'current-build-hash'})
    monkeypatch.setattr(runner, '_require_gate2_evidence', lambda candidate: {
        'report_sha256': 'immutable-report-hash', 'test_log_sha256': 'immutable-log-hash',
        'pointer_sha256': 'current-pointer-hash'})
    identity = runner._authorization_identity(config)
    assert identity['source'] == 'pinned-runtime'
    assert identity['build_hashes'] == {'runner.py': 'current-build-hash'}
    assert identity['gate2_report_sha256'] == 'immutable-report-hash'
    assert identity['gate2_test_log_sha256'] == 'immutable-log-hash'
    assert identity['gate2_pointer_sha256'] == 'current-pointer-hash'


def test_approved_lower_cohort_and_target_caps_reach_loader(monkeypatch, synthetic_authorization_inputs):
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'), execution_enabled=True)
    monkeypatch.setattr(runner, '_require_gate2_evidence', lambda _: {
        'status': 'PASS', 'report_sha256': 'gate-report', 'test_log_sha256': 'gate-log',
        'pointer_sha256': 'gate-pointer'})
    caps = {'max_train_users': 4, 'max_val_users': 2, 'max_targets_per_side': 20,
            'max_steps': 2, 'max_seconds': 10, 'max_wall_seconds': 30,
            'max_rss_bytes': config.max_rss_bytes, 'min_available_ram_bytes': config.min_available_ram_bytes}
    approval = {'approved': True, 'scope': 'development-inner-only', 'phase': 'smoke',
                'run_id': config.run_id, 'source_commit': config.source_commit,
                'config_sha256': config_hash(config),
                'identity': runner._authorization_identity(config),
                'approval_reference': 'synthetic-test', 'caps': caps}
    observed = []
    def fake_load(effective_config):
        observed.append(effective_config)
        raise RuntimeError('synthetic stop before data')
    monkeypatch.setattr(runner, '_load_phase_inputs', fake_load)
    monkeypatch.setattr(runner, '_check_resource_budget', lambda budget: 0)
    monkeypatch.setattr(runner, '_require_gate2_evidence', lambda config: {
        'status': 'PASS', 'report_sha256': 'gate-report', 'test_log_sha256': 'gate-log',
        'pointer_sha256': 'gate-pointer'})
    monkeypatch.setattr(runner, '_mark_manifest', lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match='synthetic stop'):
        runner.run_smoke(config, authorization=approval)
    assert observed[0].max_train_users == 4
    assert observed[0].max_val_users == 2
    assert observed[0].max_targets_per_side == 20


def test_gate2_evidence_rejects_code_drift_and_missing_log(tmp_path, monkeypatch):
    root = tmp_path / 'project'
    (root / 'src/knowledge_tracing/akt').mkdir(parents=True)
    (root / 'tests/akt').mkdir(parents=True)
    (root / 'src/knowledge_tracing/akt/model.py').write_text('model', encoding='utf-8')
    (root / 'tests/akt/test_model.py').write_text('test', encoding='utf-8')
    (root / 'src/knowledge_tracing/shared_kt.py').write_text('shared', encoding='utf-8')
    (root / 'src/knowledge_tracing/paired_bootstrap.py').write_text('bootstrap', encoding='utf-8')
    (root / 'src/knowledge_tracing/gam_kt').mkdir()
    (root / 'src/knowledge_tracing/gam_kt/evaluation.py').write_text('metrics', encoding='utf-8')
    pointer_path = tmp_path / 'gate2-current.json'
    report_path = tmp_path / 'gate2-20261105-test.json'
    log_path = tmp_path / 'gate2-tests-20261105-test.log'
    log_path.write_text('synthetic verification: 1 passed\n', encoding='utf-8')
    monkeypatch.setattr(runner, 'PROJECT_ROOT', root)
    monkeypatch.setattr(runner, 'GATE2_REPORT', pointer_path)
    monkeypatch.setattr(runner, 'LOCK_FILE', tmp_path / 'lock')
    runner.LOCK_FILE.write_text('locked', encoding='utf-8')
    config = AKTConfig()
    payload = {'schema_version': 1, 'status': 'PASS', 'source_commit': config.source_commit,
               'suite': 'tests/akt tests/shared_kt',
               'elapsed_seconds': 1.0, 'timeout_seconds': 30,
               'test_result': {'passed': 1, 'failed': 0, 'errors': 0, 'skipped': 0},
               'lock_sha256': runner.sha256_file(runner.LOCK_FILE),
               'build_hashes': runner._gate2_build_hashes(),
               'test_log_sha256': runner.sha256_file(log_path)}
    report_path.write_text(json.dumps(payload), encoding='utf-8')
    pointer_path.write_text(json.dumps({
        'schema_version': 1,
        'evidence_file': report_path.name,
        'evidence_sha256': runner.sha256_file(report_path),
        'test_log_file': log_path.name,
        'test_log_sha256': runner.sha256_file(log_path),
    }), encoding='utf-8')
    assert runner._require_gate2_evidence(config)['status'] == 'PASS'
    (root / 'src/knowledge_tracing/paired_bootstrap.py').write_text('changed', encoding='utf-8')
    with pytest.raises(ValueError, match='Gate 2'):
        runner._require_gate2_evidence(config)
    (root / 'src/knowledge_tracing/paired_bootstrap.py').write_text('bootstrap', encoding='utf-8')
    (root / 'src/knowledge_tracing/akt/model.py').write_text('changed', encoding='utf-8')
    with pytest.raises(ValueError, match='Gate 2'):
        runner._require_gate2_evidence(config)
    log_path.unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        runner._require_gate2_evidence(config)


def test_gate2_pointer_rejects_tampered_versioned_evidence(tmp_path, monkeypatch):
    pointer_path = tmp_path / 'gate2-current.json'
    report_path = tmp_path / 'gate2-20261105-test.json'
    log_path = tmp_path / 'gate2-tests-20261105-test.log'
    report_path.write_text('{"schema_version":1,"status":"PASS",'
                           '"suite":"tests/akt tests/shared_kt",'
                           '"test_result":{"passed":1,"failed":0,"errors":0,"skipped":0}}',
                           encoding='utf-8')
    log_path.write_text('1 passed\n', encoding='utf-8')
    pointer_path.write_text(json.dumps({
        'schema_version': 1,
        'evidence_file': report_path.name,
        'evidence_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(),
        'test_log_file': log_path.name,
        'test_log_sha256': hashlib.sha256(log_path.read_bytes()).hexdigest(),
    }), encoding='utf-8')
    monkeypatch.setattr(runner, 'GATE2_REPORT', pointer_path)

    report_path.write_text('{"status":"FAIL"}', encoding='utf-8')

    with pytest.raises(ValueError, match='Gate 2'):
        runner._require_gate2_evidence(AKTConfig())


def test_resource_floor_fails_before_data_loading(monkeypatch):
    monkeypatch.setattr(training, 'memory_snapshot', lambda: {
        'pid': 321, 'process_rss_bytes': 100, 'process_peak_rss_bytes': 100,
        'system_available_ram_bytes': 49, 'system_total_ram_bytes': 1000})
    with pytest.raises(MemoryError, match='available-RAM') as error:
        runner._check_resource_budget({'max_rss_bytes': 200, 'min_available_ram_bytes': 50,
                                       'phase': 'smoke', 'run_id': 'synthetic-run'})
    message = str(error.value)
    assert 'worker_rss_bytes=100' in message
    assert 'system_available_ram_bytes=49' in message
    assert 'max_rss_bytes=200' in message and 'min_available_ram_bytes=50' in message
    assert 'phase=smoke' in message and 'run_id=synthetic-run' in message and 'pid=' in message


def test_rss_ceiling_error_includes_worker_and_system_measurements(monkeypatch):
    monkeypatch.setattr(training, 'memory_snapshot', lambda: {
        'pid': 654, 'process_rss_bytes': 201, 'process_peak_rss_bytes': 225,
        'system_available_ram_bytes': 777, 'system_total_ram_bytes': 1000})
    with pytest.raises(MemoryError, match='RSS ceiling') as error:
        runner._check_resource_budget({'max_rss_bytes': 200, 'min_available_ram_bytes': 50,
                                       'phase': 'pilot', 'run_id': 'ceiling-test'})
    message = str(error.value)
    assert 'worker_rss_bytes=201' in message and 'worker_cap_value_bytes=225' in message
    assert 'worker_peak_rss_bytes=225' in message and 'system_available_ram_bytes=777' in message
    assert 'max_rss_bytes=200' in message and 'min_available_ram_bytes=50' in message
    assert 'phase=pilot' in message and 'run_id=ceiling-test' in message and 'pid=654' in message


def test_cli_watchdog_reports_timeout_without_completed_result(tmp_path, monkeypatch, capsys):
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'), execution_enabled=True)
    identity = {'source': {'commit': config.source_commit}, 'assignments_sha256': 'synthetic-data-hash'}
    monkeypatch.setattr(watchdog, 'require_authorization', lambda *args: approval)
    caps = {'max_train_users': 32, 'max_val_users': 16, 'max_targets_per_side': 4096,
            'max_steps': 20, 'max_seconds': 120, 'max_wall_seconds': 300,
            'max_rss_bytes': config.max_rss_bytes, 'min_available_ram_bytes': config.min_available_ram_bytes}
    approval = {'approved': True, 'scope': 'development-inner-only', 'phase': 'smoke',
                'run_id': config.run_id, 'source_commit': config.source_commit,
                'config_sha256': config_hash(config),
                'identity': identity,
                'approval_reference': 'synthetic-test', 'caps': caps}
    path = tmp_path / 'approval.json'
    path.write_text(json.dumps(approval), encoding='utf-8')
    monkeypatch.setattr(watchdog, 'load_config', lambda path: config)
    monkeypatch.setattr(watchdog, 'memory_snapshot', lambda: {
        'pid': 123, 'process_rss_bytes': 100, 'process_peak_rss_bytes': 100,
        'system_available_ram_bytes': 4 * 1024**3, 'system_total_ram_bytes': 8 * 1024**3})
    class TimedOutWorker:
        pid = 987
        def __init__(self):
            self.calls = 0
            self.killed = False
        def communicate(self, timeout=None):
            assert timeout in (None, 300)
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired(['worker'], timeout, output='partial stdout', stderr='partial stderr')
            return ('partial stdout', 'partial stderr')
        def kill(self):
            self.killed = True
        def poll(self):
            return None if not self.killed else -9
    worker = TimedOutWorker()
    def spawn(*args, **kwargs):
        assert kwargs['stdout'] == subprocess.PIPE and kwargs['stderr'] == subprocess.PIPE
        return worker
    monkeypatch.setattr(watchdog.subprocess, 'Popen', spawn)
    with pytest.raises(TimeoutError, match='watchdog'):
        watchdog.main(['smoke', '--config', 'unused.json', '--authorization', str(path)])
    assert worker.killed and worker.calls == 2
    output = capsys.readouterr()
    events = [json.loads(line) for line in output.err.splitlines() if line.startswith('{')]
    assert {event['event'] for event in events} == {
        'watchdog-before-worker-spawn', 'watchdog-after-worker-spawn', 'watchdog-timeout'}
    assert next(event for event in events if event['event'] == 'watchdog-after-worker-spawn')['worker_pid'] == 987
    assert 'partial stdout' in output.out
    assert 'partial stderr' in output.err


def test_failed_synthetic_run_manifest_keeps_audit_records(tmp_path, monkeypatch):
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'),
                     output_dir=tmp_path / 'run', execution_enabled=True)
    caps = {'max_train_users': 4, 'max_val_users': 2, 'max_targets_per_side': 20,
            'max_steps': 2, 'max_seconds': 10, 'max_wall_seconds': 30,
            'max_rss_bytes': config.max_rss_bytes, 'min_available_ram_bytes': config.min_available_ram_bytes}
    approved = {'caps': caps, 'approval_reference': 'synthetic-approval'}
    learner = LearnerEvents('synthetic', 1, (KTEvent('synthetic', 'A', 1, 1, 1, 0, 1),))
    monkeypatch.setattr(runner, 'validate_config', lambda config: None)
    monkeypatch.setattr(runner, '_require_authorization', lambda *args: approved)
    monkeypatch.setattr(runner, '_check_resource_budget', lambda budget: 0)
    monkeypatch.setattr(runner, '_require_gate2_evidence', lambda config: {'status': 'PASS', 'report_sha256': 'gate'})
    monkeypatch.setattr(runner, '_load_phase_inputs', lambda config: (
        {'runtime_report_sha256': 'runtime'}, object(), (learner,), (learner,)))
    def stop(*args, **kwargs):
        raise RuntimeError('synthetic failure')
    monkeypatch.setattr(runner, 'select_checkpoint', stop)
    with pytest.raises(RuntimeError, match='synthetic failure'):
        runner.run_smoke(config, authorization=approved, _invocation={'kind': 'cli', 'argv': ['synthetic']})
    manifest = json.loads((config.output_dir / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['status'] == 'incomplete'
    assert manifest['invocation']['argv'] == ['synthetic']
    assert manifest['retry_history'] == [] and manifest['attempt'] == 1
    assert manifest['gate_records']['gate2']['report_sha256'] == 'gate'
    assert manifest['approved_caps'] == caps and manifest['error_type'] == 'RuntimeError'


def test_config_rejects_unsafe_run_id_and_output_path():
    config = AKTConfig(phase='smoke', run_id='../overwrite', execution_enabled=True,
                       output_dir=PROJECT_ROOT / 'experiments/akt/results/unsafe')
    with pytest.raises(ValueError):
        validate_config(config)
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'), run_id='unsafe',
                     output_dir=PROJECT_ROOT / 'artifacts/bkt_baseline/unsafe')
    with pytest.raises(ValueError, match='protected'):
        validate_config(config)


def test_readiness_report_never_grants_execution_authorization(tmp_path):
    pilot_result = tmp_path / 'pilot.json'
    pilot_result.write_text(json.dumps({
        'status': 'complete', 'run_id': 'pilot-001',
        'source_commit': load_config(PROJECT_ROOT / 'experiments/akt/configs/fold0.json').source_commit,
        'summary': {
            'complete_epoch': True,
            'validation_loss': 0.5,
            'validation': {'predicted_rows': 3},
            'checkpoint_reload_state_exact': True,
            'checkpoint_sha256': 'synthetic-checkpoint-hash',
            'coverage': {'status': 'complete', 'expected_rows': 3, 'prediction_rows': 3},
        },
    }), encoding='utf-8')
    config = AKTConfig(phase='fold-readiness', run_id='fold0-readiness',
                       output_dir=PROJECT_ROOT / 'experiments/akt/readiness/fold0-readiness')
    result = runner.prepare_fold_readiness(config, pilot_result=pilot_result)
    assert result['authorization'] == {'full_fold': False, 'five_fold': False}
    assert result['status'] == 'pending-explicit-approval'


def test_cli_has_no_default_execution_phase_and_help_is_available():
    with pytest.raises(SystemExit) as error:
        runner.main([])
    assert error.value.code == 2
    with pytest.raises(SystemExit) as help_exit:
        runner.main(['--help'])
    assert help_exit.value.code == 0


def test_preflight_verifies_gate1_without_opening_dataset(tmp_path, monkeypatch):
    config = load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json')
    monkeypatch.setattr(runner, 'read_development_assignments',
                        lambda *args, **kwargs: pytest.fail('preflight must not open assignments'))
    lock = tmp_path/'lock.txt'
    lock.write_text('synthetic lock',encoding='utf-8')
    source = {'commit': config.source_commit}
    report = tmp_path/'runtime.json'
    # Fixture runtime isolated, không chứng nhận origins thực của Colab inherited venv.
    runtime_sys = runner.authorization_module.sys
    executable = runner.authorization_module.validate_runtime_interpreter(
        PROJECT_ROOT / '.venv', executable=runtime_sys.executable,
        prefix=runtime_sys.prefix, platform_id=runtime_sys.platform)
    report.write_text(json.dumps({'runtime_schema_version': 2,
        'platform_id': runtime_sys.platform, 'source': source,
        'lock_sha256': hashlib.sha256(lock.read_bytes()).hexdigest(),
        'python': str(executable), 'python_prefix': str((PROJECT_ROOT / '.venv').resolve()),
        'project_root': str(PROJECT_ROOT.resolve()), 'lock_file': str(lock.resolve()),
        'device': 'cpu', 'cuda_available': False,
        'torch_origin': str(PROJECT_ROOT / '.venv/fixture/torch/__init__.py'),
        'numpy_origin': str(PROJECT_ROOT / '.venv/fixture/numpy/__init__.py')}), encoding='utf-8')
    monkeypatch.setattr(runner, 'LOCK_FILE', lock)
    monkeypatch.setattr(runner, 'RUNTIME_REPORT', report)
    monkeypatch.setattr(runner, 'GATE2_REPORT', tmp_path/'missing-gate2.json')
    monkeypatch.setattr(runner.authorization_module, 'verify_upstream', lambda *args: source)
    monkeypatch.setattr(runner.authorization_module.sys, 'prefix', str(PROJECT_ROOT/'.venv'))
    result = runner.preflight(config)
    assert result['status'] == 'ready'
    assert result['source']['commit'] == config.source_commit
    assert result['lock_sha256'] == result['runtime']['lock_sha256']
