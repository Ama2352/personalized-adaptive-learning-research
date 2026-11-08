"""Không phát hành Gate2 từ zero tests hoặc suite có skip/failure."""

from pathlib import Path
import hashlib
import json
import runpy
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('seconds', [0, -1, 601, True, 4.2, '420'])
def test_gate2_timeout_rejects_unbounded_or_invalid_values(seconds):
    validate = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))['validate_timeout']
    with pytest.raises(ValueError, match='timeout'):
        validate(seconds)


def test_gate2_timeout_is_explicit_bounded_and_default_unchanged():
    import inspect
    module = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))
    assert module['validate_timeout'](420) == 420
    assert module['validate_timeout'](600) == 600
    assert inspect.signature(module['refresh']).parameters['timeout_seconds'].default == 300


@pytest.mark.parametrize('attribute', ['tests="0"', 'tests="2" failures="1"', 'tests="2" skipped="1"', 'tests="2" errors="1"'])
def test_gate2_refresh_rejects_incomplete_suite(tmp_path, attribute):
    parse = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))['test_result']
    path = tmp_path / 'junit.xml'
    path.write_text(f'<testsuites><testsuite {attribute}/></testsuites>', encoding='utf-8')
    with pytest.raises(ValueError, match='without failures'):
        parse(path)


def test_gate2_refresh_accepts_complete_suite(tmp_path):
    parse = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))['test_result']
    path = tmp_path / 'junit.xml'
    path.write_text('<testsuites><testsuite tests="3" failures="0" skipped="0" errors="0"/></testsuites>', encoding='utf-8')
    assert parse(path) == {'passed': 3, 'failed': 0, 'errors': 0, 'skipped': 0}


def _publisher(tmp_path, monkeypatch, *, elapsed):
    """Fake child only: no pytest subprocess, Torch, optimizer or Gate publication."""
    module = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))
    namespace = module['refresh'].__globals__
    root = tmp_path / 'project'
    directory = root / 'artifacts/akt/preflight'
    directory.mkdir(parents=True)
    (root / 'requirements-akt.lock.txt').write_text('synthetic lock', encoding='utf-8')
    pointer = directory / 'gate2-current.json'
    pointer.write_bytes(b'original pointer must remain intact\n')
    observed = {}

    def child(command, **kwargs):
        observed.update(kwargs)
        Path(command[command.index('--junitxml') + 1]).write_text(
            '<testsuites><testsuite tests="3" failures="0" errors="0" skipped="0"/></testsuites>',
            encoding='utf-8')
        kwargs['stdout'].write(b'3 passed, synthetic child receipt\n')
        return SimpleNamespace(returncode=0)

    clock = iter((100.0, 100.0 + elapsed))
    monkeypatch.setitem(namespace, 'ROOT', root)
    monkeypatch.setitem(namespace, 'sys', SimpleNamespace(prefix=str(root / '.venv'), executable='fixture-python'))
    monkeypatch.setitem(namespace, 'time', SimpleNamespace(perf_counter=lambda: next(clock)))
    monkeypatch.setitem(namespace, 'subprocess', SimpleNamespace(run=child, STDOUT=-2))
    monkeypatch.setitem(namespace, 'verify_upstream', lambda *args: {'commit': 'synthetic source'})
    monkeypatch.setitem(namespace, 'gate2_build_hashes', lambda: {'fixture.py': 'source hash'})
    monkeypatch.setitem(namespace, 'require_gate2_evidence', lambda *args: {'status': 'PASS'})
    # Track/revert keys changed by the real function; never alter Git config on disk.
    monkeypatch.setenv('GIT_CONFIG_COUNT', '0')
    monkeypatch.setenv('GIT_CONFIG_KEY_0', 'fixture.previous')
    monkeypatch.setenv('GIT_CONFIG_VALUE_0', 'fixture')
    return module['refresh'], directory, pointer, observed


def test_gate2_exit_zero_clock_overrun_rejected_without_pointer_change(tmp_path, monkeypatch):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=1084.0)
    original = pointer.read_bytes()
    with pytest.raises(TimeoutError, match='elapsed'):
        refresh('synthetic-overrun', publish_current=True, timeout_seconds=540)
    assert pointer.read_bytes() == original
    report = directory / 'gate2-evidence-synthetic-overrun.json'
    rejected = json.loads(report.read_text())
    assert rejected['status'] == 'REJECTED_RESOURCE_BOUND'
    assert rejected['elapsed_seconds'] == 1084.0 and rejected['timeout_seconds'] == 540
    assert rejected['test_result']['passed'] == 3
    assert rejected['build_hashes'] == {'fixture.py': 'source hash'}
    assert rejected['test_log_sha256'] == hashlib.sha256(
        (directory / 'gate2-tests-synthetic-overrun.log').read_bytes()).hexdigest()
    assert not (directory / 'gate2-pointer-before-synthetic-overrun.json').exists()
    assert not list(directory.glob('gate2-current-*.tmp'))
    with pytest.raises(FileExistsError):
        refresh('synthetic-overrun', publish_current=True, timeout_seconds=540)


def test_gate2_inbudget_publisher_retains_counts_and_bounds_child_threads(tmp_path, monkeypatch):
    import time
    real_counter = time.perf_counter
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=1.0)
    result = refresh('synthetic-valid', publish_current=True, timeout_seconds=30)
    assert result['published_current'] is True
    report = json.loads((directory / 'gate2-evidence-synthetic-valid.json').read_text())
    assert report['status'] == 'PASS' and report['elapsed_seconds'] == 1.0
    assert report['timeout_seconds'] == 30 and report['test_result']['passed'] == 3
    assert json.loads(pointer.read_text())['evidence_file'] == 'gate2-evidence-synthetic-valid.json'
    assert observed['timeout'] == 30
    assert {name: observed['env'][name] for name in
            ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'CUDA_VISIBLE_DEVICES')} == {
                'OMP_NUM_THREADS': '2', 'MKL_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2',
                'CUDA_VISIBLE_DEVICES': ''}
    assert time.perf_counter is real_counter  # Only the loaded script's clock was replaced.


@pytest.mark.parametrize('elapsed', [-1.0, float('nan'), float('inf')])
def test_gate2_publisher_rejects_invalid_elapsed_and_preserves_strict_json(tmp_path, monkeypatch, elapsed):
    refresh, directory, pointer, _ = _publisher(tmp_path, monkeypatch, elapsed=elapsed)
    original = pointer.read_bytes()
    with pytest.raises(TimeoutError, match='elapsed'):
        refresh('synthetic-bad-clock', publish_current=True, timeout_seconds=30)
    raw = (directory / 'gate2-evidence-synthetic-bad-clock.json').read_text()
    def reject_numeric_constant(value):
        raise AssertionError(f'nonstandard JSON constant: {value}')
    rejected = json.loads(raw, parse_constant=reject_numeric_constant)
    assert rejected['status'] == 'REJECTED_RESOURCE_BOUND'
    assert rejected['timeout_seconds'] == 30 and rejected['test_result']['passed'] == 3
    assert pointer.read_bytes() == original


def _reader_report(tmp_path, **resource):
    from knowledge_tracing.akt.authorization import require_gate2_evidence
    from knowledge_tracing.akt.config import AKTConfig
    config = AKTConfig()
    lock = tmp_path / 'lock'
    lock.write_bytes(b'synthetic lock')
    log = tmp_path / 'gate2-tests-synthetic.log'
    log.write_bytes(b'1 passed synthetic receipt\n')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = tmp_path / 'gate2-evidence-synthetic.json'
    payload = {'schema_version': 1, 'status': 'PASS', 'source_commit': config.source_commit,
               'suite': 'tests/akt tests/shared_kt',
               'test_result': {'passed': 1, 'failed': 0, 'errors': 0, 'skipped': 0},
               'lock_sha256': sha(lock), 'build_hashes': {'fixture.py': 'current hash'},
               'test_log_sha256': sha(log), **resource}
    report.write_text(json.dumps(payload), encoding='utf-8')
    pointer = tmp_path / 'gate2-current.json'
    pointer.write_text(json.dumps({'schema_version': 1, 'evidence_file': report.name,
        'evidence_sha256': sha(report), 'test_log_file': log.name, 'test_log_sha256': sha(log)}), encoding='utf-8')
    return lambda: require_gate2_evidence(config, gate2_report=pointer, lock_file=lock,
                                         build_hashes_fn=lambda: payload['build_hashes'])


@pytest.mark.parametrize('resource', [
    {}, {'elapsed_seconds': 1.0}, {'timeout_seconds': 30},
    {'elapsed_seconds': 31.0, 'timeout_seconds': 30},
    *({'elapsed_seconds': value, 'timeout_seconds': 30}
      for value in (True, False, None, '1.0', [], {}, -1.0, float('nan'), float('inf'), -float('inf'), 10**400)),
    *({'elapsed_seconds': 1.0, 'timeout_seconds': value}
      for value in (True, False, None, '30', 30.0, 0, 601, float('nan'), float('inf'))),
])
def test_gate2_reader_rejects_resource_bypass_even_after_rehash(tmp_path, resource):
    with pytest.raises(ValueError, match='elapsed|timeout|resource'):
        _reader_report(tmp_path, **resource)()


@pytest.mark.parametrize('elapsed,timeout', [(1.0, 30), (30.0, 30), (0, 1), (600.0, 600)])
def test_gate2_reader_accepts_finite_elapsed_within_declared_budget(tmp_path, elapsed, timeout):
    assert _reader_report(tmp_path, elapsed_seconds=elapsed, timeout_seconds=timeout)()['status'] == 'PASS'
