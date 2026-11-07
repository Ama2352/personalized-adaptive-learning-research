"""Context→recovery certificate negatives, chỉ JSON/hash, không Torch/model.

Fake .pt là bytes có nhãn, không unpickle. Không mock authorization/validator;
certificate fixture không là execution approval. Subprocess chỉ đi tới early
context rejection của lightweight watchdog với config trusted root thật.
"""

from copy import deepcopy
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from knowledge_tracing.akt.authorization import config_hash
from knowledge_tracing.akt.config import PROJECT_ROOT, RecoveryOptions, load_config
from knowledge_tracing.akt.context import load_worker_context
from knowledge_tracing.akt import recovery


def source_certificate(tmp_path, *, cuda=True):
    """Reuse publish/validate contract thật; fixture root không chạy worker."""
    root = tmp_path / 'p'
    dataset = root / 'artifacts/akt/synthetic/d'
    (dataset / 'c').mkdir(parents=True)
    for name, content in (
        ('c/a.parquet', b'SYNTHETIC_PLACEHOLDER_NOT_PARQUET_NO_READER'),
        ('a.parquet', b'SYNTHETIC_ASSIGNMENT_PLACEHOLDER_NO_READER'),
        ('cm.json', b'{}'), ('sm.json', b'{}'),
        ('SYNTHETIC_ONLY.json', b'{"synthetic_only":true,"real_data_authorized":false}'),
    ):
        (dataset / name).write_bytes(content)
    payload = {'schema_version': 1, 'scope': 'synthetic-development-only',
               'runtime_report': 'artifacts/akt/preflight/runtime.json',
               'lock_file': 'requirements-akt-linux.txt',
               'gate2_report': 'artifacts/akt/preflight/gate2-current.json',
               'dataset_root': 'artifacts/akt/synthetic/d',
               'canonical': 'artifacts/akt/synthetic/d/c',
               'assignments': 'artifacts/akt/synthetic/d/a.parquet',
               'canonical_manifest': 'artifacts/akt/synthetic/d/cm.json',
               'split_manifest': 'artifacts/akt/synthetic/d/sm.json',
               'input_hashes': {p.relative_to(root).as_posix(): recovery.digest_file(p)
                                for p in dataset.rglob('*') if p.is_file()}}
    if cuda:
        payload['cuda_limits'] = {'max_vram_bytes': 256 * 1024**2, 'visible_devices': 1}
    sidecar = root / 'artifacts/akt/context.json'
    sidecar.write_text(json.dumps(payload), encoding='utf-8')
    context = load_worker_context(sidecar, expected_sha256=recovery.digest_file(sidecar), project_root=root)
    template = load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json')
    old = replace(template, project_root=root, phase='cuda-smoke' if cuda else 'smoke',
                  device='cuda' if cuda else 'cpu', run_id='old',
                  output_dir=root / 'experiments/akt/results/old',
                  max_train_users=2, max_val_users=1, max_targets_per_side=8,
                  max_steps=2, max_seconds=30, max_wall_seconds=90, recovery=RecoveryOptions())
    context.validate_for(old)
    old.output_dir.mkdir(parents=True)
    for name, status in (('manifest.json', 'incomplete'), ('watchdog-resources.json', 'failed')):
        (old.output_dir / name).write_text(json.dumps({'run_id': 'old', 'status': status}), encoding='utf-8')
    checkpoint = old.output_dir / 'snapshot.pt'
    checkpoint.write_bytes(b'VALIDATOR_ONLY_SYNTHETIC_BYTES_NEVER_TORCH_LOAD')
    (old.output_dir / 'recovery-progress.json').write_text(json.dumps({
        'checkpoint': checkpoint.name,
        'files': [{'name': checkpoint.name, 'sha256': recovery.digest_file(checkpoint)}]}), encoding='utf-8')
    caps = {name: getattr(old, name) for name in ('max_train_users', 'max_val_users',
            'max_targets_per_side', 'max_steps', 'max_seconds', 'max_wall_seconds',
            'max_rss_bytes', 'min_available_ram_bytes')}
    identity = {**context.identity, 'config_sha256': config_hash(old),
                'build_hashes': {'validator-test-source': recovery.digest_file(Path(__file__))},
                'assignments_sha256': recovery.digest_file(context.data_paths.assignments),
                'source': {'commit': old.source_commit}}
    certificate_inputs = {'identity': identity, 'caps': caps,
                          'approval_reference': 'VALIDATOR_ONLY; not an execution approval'}
    recovery.publish_envelope(old, authorization=certificate_inputs, elapsed_seconds=6.5)
    envelope = old.output_dir / 'recovery-envelope.json'
    resumed = replace(old, run_id='new', output_dir=old.output_dir.with_name('new'),
                      recovery=RecoveryOptions(source_envelope=envelope,
                                               source_sha256=recovery.digest_file(envelope)))
    return old, resumed, certificate_inputs, context, payload


@pytest.mark.parametrize('cuda', [False, True])
def test_unchanged_context_certificate_accepts_new_attempt_without_mutating_source(tmp_path, cuda):
    old, resumed, inputs, context, _ = source_certificate(tmp_path, cuda=cuda)
    before = {p.name: recovery.digest_file(p) for p in old.output_dir.iterdir()}
    current = {**inputs['identity'], 'config_sha256': config_hash(resumed),
               'gate2_report_sha256': 'reissued-same-build-report',
               'gate2_pointer_sha256': 'reissued-same-build-pointer'}
    result = recovery.validate_source(resumed, current_identity=current, caps=inputs['caps'])
    assert result['attempt'] == 1 and result['cumulative_wall_seconds'] == 6.5
    assert result['input_identity']['worker_context_sha256'] == context.manifest_sha256
    assert result['input_identity']['worker_context_inputs_sha256'] == dict(context.input_hashes)
    if cuda:
        assert result['input_identity']['worker_context_cuda_limits'] == {
            'max_vram_bytes': 256 * 1024**2, 'visible_devices': 1}
    assert recovery.semantic_hash(old) == recovery.semantic_hash(resumed)
    assert before == {p.name: recovery.digest_file(p) for p in old.output_dir.iterdir()}
    assert not resumed.output_dir.exists()


@pytest.mark.parametrize('changed', ['worker_context_sha256', 'worker_context_inputs_sha256',
                                    'worker_context_cuda_limits', 'worker_context_scope'])
def test_recovery_keeps_each_context_field_in_stable_identity(tmp_path, changed):
    _, resumed, inputs, _, _ = source_certificate(tmp_path)
    current = deepcopy(inputs['identity'])
    if changed == 'worker_context_inputs_sha256':
        current[changed][next(iter(current[changed]))] = '0' * 64
    elif changed == 'worker_context_cuda_limits':
        current[changed]['max_vram_bytes'] = 128 * 1024**2
    elif changed == 'worker_context_scope':
        current[changed] = 'research-data-not-authorized'
    else:
        current[changed] = '0' * 64
    with pytest.raises(ValueError, match='semantic or input identity mismatch'):
        recovery.validate_source(resumed, current_identity=current, caps=inputs['caps'])


@pytest.mark.parametrize('changed', ['input_bytes', 'allocator_budget'])
def test_fresh_valid_rehashed_context_cannot_resume_old_context_checkpoint(tmp_path, changed):
    _, resumed, inputs, old_context, payload = source_certificate(tmp_path)
    if changed == 'input_bytes':
        canonical = old_context.data_paths.canonical / 'a.parquet'
        canonical.write_bytes(b'CHANGED_SYNTHETIC_BYTES_STILL_NO_READER')
        payload['input_hashes'][canonical.relative_to(old_context.project_root).as_posix()] = recovery.digest_file(canonical)
    else:
        payload['cuda_limits']['max_vram_bytes'] = 128 * 1024**2
    old_context.manifest_path.write_text(json.dumps(payload), encoding='utf-8')
    new_context = load_worker_context(old_context.manifest_path,
                                     expected_sha256=recovery.digest_file(old_context.manifest_path),
                                     project_root=old_context.project_root)
    new_context.validate_for(resumed)
    assert new_context.manifest_sha256 != old_context.manifest_sha256
    current = {**inputs['identity'], **new_context.identity}
    with pytest.raises(ValueError, match='semantic or input identity mismatch'):
        recovery.validate_source(resumed, current_identity=current, caps=inputs['caps'])


def test_cpu_context_checkpoint_cannot_cross_into_new_cuda_phase(tmp_path):
    _, resumed, inputs, _, _ = source_certificate(tmp_path, cuda=False)
    changed = replace(resumed, phase='cuda-smoke', device='cuda')
    assert recovery.semantic_hash(changed) != recovery.semantic_hash(resumed)
    with pytest.raises(ValueError, match='semantic or input identity mismatch'):
        recovery.validate_source(changed, current_identity=inputs['identity'], caps=inputs['caps'])


@pytest.mark.parametrize('case', ['missing_context', 'changed_context'])
def test_light_watchdog_context_rejection_precedes_runner_and_dataset_import(tmp_path, case):
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'),
                     phase='cuda-smoke', device='cuda', run_id='context-early-guard',
                     output_dir=PROJECT_ROOT / 'experiments/akt/results/context-early-guard')
    config_file = tmp_path / 'config.json'
    config_file.write_text(json.dumps(asdict(config), default=str), encoding='utf-8')
    argv = ['_execute', 'cuda-smoke', '--config', str(config_file)]
    if case == 'changed_context':
        sidecar = tmp_path / 'changed-context.json'
        sidecar.write_text('{}', encoding='utf-8')
        expected = recovery.digest_file(sidecar)
        sidecar.write_text('{"changed":true}', encoding='utf-8')
        argv += ['--context-file', str(sidecar), '--context-sha256', expected]
    # Import trap chỉ làm negative path fail nếu đi quá xa; không thay auth/validator.
    code = '''import builtins,json,sys
original=builtins.__import__;blocked=[]
def guarded(name,*args,**kwargs):
    if name.split('.')[0] in {'torch','duckdb'} or name in {'runner','knowledge_tracing.akt.runner'}:
        blocked.append(name);raise AssertionError('unexpected heavy import before context rejection: '+name)
    return original(name,*args,**kwargs)
builtins.__import__=guarded
from knowledge_tracing.akt.watchdog import main
try:main(json.loads(sys.argv[1]))
except ValueError as error:
    assert not blocked
    assert 'knowledge_tracing.akt.data' not in sys.modules
    assert 'knowledge_tracing.akt.runner' not in sys.modules and 'torch' not in sys.modules
    print(json.dumps({'status':'EXPECTED_EARLY_CONTEXT_REJECTION','error':str(error),'blocked_imports':blocked,'dataset_module_loaded':False,'runner_module_loaded':False,'torch_module_loaded':False}))
else:raise AssertionError('invalid context request unexpectedly accepted')
'''
    env = {**os.environ, 'PYTHONPATH': str(PROJECT_ROOT / 'src'),
           'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': ''}
    result = subprocess.run([sys.executable, '-B', '-c', code, json.dumps(argv)], cwd=PROJECT_ROOT,
                            env=env, capture_output=True, text=True, timeout=15)
    (tmp_path / 'child-stdout.json').write_text(result.stdout, encoding='utf-8')
    (tmp_path / 'child-stderr.log').write_text(result.stderr, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt['status'] == 'EXPECTED_EARLY_CONTEXT_REJECTION'
    if case == 'missing_context':
        assert 'requires a synthetic worker context' in receipt['error']
    elif tmp_path.resolve().is_relative_to((PROJECT_ROOT / 'artifacts/akt').resolve()):
        assert 'SHA-256 mismatch' in receipt['error']
