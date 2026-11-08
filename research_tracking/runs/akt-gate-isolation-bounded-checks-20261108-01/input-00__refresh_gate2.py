"""Chạy CPU synthetic suite và phát hành Gate2 gắn đúng source hiện tại."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from knowledge_tracing.akt.authorization import (
    gate2_build_hashes, require_gate2_evidence, validate_gate2_elapsed_budget,
)
from knowledge_tracing.akt.config import AKTConfig, SOURCE_COMMIT
from knowledge_tracing.akt.provenance import sha256_file, verify_upstream


STRICT_STDLIB = ('tests/shared_kt/test_development_corpus_worker.py',)
NO_TORCH = (
    'tests/akt/test_research_execution.py',
    'tests/akt/test_research_lifecycle.py',
    'tests/akt/test_research_runner.py',
    'tests/akt/test_research_simulator_data.py',
    'tests/shared_kt/test_simulator_corpus_publisher.py',
    'tests/shared_kt/test_simulator_corpus_reader.py',
)
ChildTimeout = subprocess.TimeoutExpired


def test_partition(root):
    """Ba fresh processes; inventory đủ mọi test module, không -k/deselect."""
    modules = sorted({p.relative_to(root).as_posix()
                      for base in (root / 'tests/akt', root / 'tests/shared_kt')
                      for p in base.rglob('*.py')
                      if p.name.startswith('test_') or p.name.endswith('_test.py')})
    required = (*STRICT_STDLIB, *NO_TORCH)
    if not modules or len(required) != len(set(required)) or not set(required) <= set(modules):
        raise ValueError('Gate2 isolation requires every explicit pure test module')
    groups = [('stdlib', list(STRICT_STDLIB)), ('no-torch', list(NO_TORCH)),
              ('remaining', [p for p in modules if p not in required])]
    flat = [p for _, paths in groups for p in paths]
    if (any(not paths for _, paths in groups) or len(flat) != len(set(flat))
            or sorted(flat) != modules):
        raise ValueError('Gate2 test partition must cover all modules exactly once without empty groups')
    for relative in modules:
        path = root / relative
        if path.is_symlink() or path.is_junction() or not path.is_file():
            raise ValueError('Gate2 requires physical test modules')
    return groups


def remaining_seconds(started, timeout_seconds):
    elapsed = time.perf_counter() - started
    try:
        validate_gate2_elapsed_budget(elapsed, timeout_seconds)
    except ValueError as exc:
        raise TimeoutError('Gate2 elapsed resource bound rejected') from exc
    remaining = timeout_seconds - elapsed
    if remaining <= 0:
        raise TimeoutError('Gate2 elapsed budget exhausted before next stage')
    return remaining


def resource_rejection(report, payload, started, timeout_seconds, error, *, own_report_sha=None):
    """Chỉ ghi/reclassify report mới của invocation này; không sửa hồ sơ cũ."""
    elapsed = time.perf_counter() - started
    payload.update(status='REJECTED_RESOURCE_BOUND', resource_error=str(error),
                   elapsed_seconds=elapsed, observed_elapsed_seconds=elapsed,
                   allowed_seconds=timeout_seconds)
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed):
        payload['elapsed_seconds'] = payload['observed_elapsed_seconds'] = repr(elapsed)
    raw = (json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    if own_report_sha is None:
        with report.open('xb') as stream:
            stream.write(raw)
    else:
        # The report was created exclusively by this still-running invocation.
        with report.open('r+b') as stream:
            if sha256_file(report) != own_report_sha:
                raise ValueError('fresh Gate2 report changed before resource rejection')
            stream.seek(0); stream.write(raw); stream.truncate(); stream.flush(); os.fsync(stream.fileno())
    raise TimeoutError(f'Gate2 elapsed resource bound rejected; inspect {report}') from error


def combine_junit(groups, output):
    """Giữ nguyên suites/cases từ từng process; không cộng historical counts."""
    aggregate = ET.Element('testsuites')
    seen = set()
    for group in groups:
        tree = ET.parse(group['junit_path']).getroot()
        cases = list(tree.iter('testcase'))
        if len(cases) != group['test_result']['passed']:
            raise ValueError('Gate2 JUnit cases do not match actual shard count')
        for case in cases:
            key = (case.get('classname'), case.get('name'))
            if not all(type(v) is str and v for v in key) or key in seen:
                raise ValueError('Gate2 duplicate or invalid testcase identity across groups')
            seen.add(key)
        if tree.tag == 'testsuite':
            aggregate.append(tree)
        else:
            aggregate.extend(list(tree))
    with output.open('xb') as stream:
        ET.ElementTree(aggregate).write(stream, encoding='utf-8', xml_declaration=True)
    result = test_result(output)
    if result['passed'] != sum(g['test_result']['passed'] for g in groups):
        raise ValueError('Gate2 aggregate counts do not match all process groups')
    return result


def test_result(xml_path):
    suites = list(ET.parse(xml_path).getroot().iter('testsuite'))
    counts = {key: sum(int(suite.attrib.get(key, '0')) for suite in suites)
              for key in ('tests', 'failures', 'errors', 'skipped')}
    if counts['tests'] <= 0 or any(counts[key] for key in ('failures', 'errors', 'skipped')):
        raise ValueError('Gate2 requires a nonempty suite without failures/errors/skips')
    return {'passed': counts['tests'], 'failed': 0, 'errors': 0, 'skipped': 0}


def validate_timeout(seconds):
    """Ngân sách riêng cho CPU software suite, không thay cap training/pilot."""
    if type(seconds) is not int or not 1 <= seconds <= 600:
        raise ValueError('Gate2 CPU test timeout must be an integer from 1 to 600 seconds')
    return seconds


def selected_lock_file(lock_file=None):
    """Lock có sẵn trong project; default Windows fixture giữ nguyên."""
    root = ROOT.resolve()
    if lock_file is None:
        candidate = root / 'requirements-akt.lock.txt'
    elif isinstance(lock_file, (str, Path)):
        candidate = Path(lock_file)
        if not candidate.is_absolute():
            candidate = root / candidate
    else:
        raise ValueError('Gate2 lock path must be a string or Path')
    resolved = candidate.resolve()
    protected = (root / 'dataset', root / 'artifacts/bkt_baseline', root / 'venv',
                 root / '.wsl', root / 'artifacts/akt/private')
    allowed = ((resolved.is_relative_to(root / 'artifacts/akt') and resolved != root / 'artifacts/akt')
               or (resolved.parent == root and resolved.name.startswith('requirements-akt')
                   and resolved.name.endswith('.txt')))
    if (not resolved.is_relative_to(root) or not allowed
            or any(resolved.is_relative_to(path) for path in protected)
            or candidate.is_symlink() or candidate.is_junction() or not resolved.is_file()):
        raise ValueError('Gate2 lock must be an existing allowed project file')
    return resolved


def refresh(run_id, *, publish_current=False, timeout_seconds=300, lock_file=None):
    validate_timeout(timeout_seconds)
    started = time.perf_counter()
    if Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
        raise ValueError('use the project .venv interpreter')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', run_id):
        raise ValueError('invalid Gate2 run ID')
    lock_path = selected_lock_file(lock_file)
    directory = ROOT / 'artifacts/akt/preflight'
    directory.mkdir(parents=True, exist_ok=True)
    report = directory / f'gate2-evidence-{run_id}.json'
    log = directory / f'gate2-tests-{run_id}.log'
    junit = directory / f'gate2-tests-{run_id}.xml'
    if any(path.exists() for path in (report, log, junit)):
        raise FileExistsError('Gate2 run ID already exists')
    partition = test_partition(ROOT)
    module_hashes = {p: sha256_file(ROOT / p) for _, paths in partition for p in paths}
    group_paths = [(directory / f'gate2-tests-{run_id}-{name}.log',
                    directory / f'gate2-tests-{run_id}-{name}.xml') for name, _ in partition]
    if any(p.exists() for paths in group_paths for p in paths):
        raise FileExistsError('Gate2 group artifact already exists')
    # Per-process exact safe.directory, không sửa Git global configuration.
    count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
    os.environ[f'GIT_CONFIG_KEY_{count}'] = 'safe.directory'
    os.environ[f'GIT_CONFIG_VALUE_{count}'] = (ROOT / 'artifacts/akt/dependencies/upstream').as_posix()
    os.environ['GIT_CONFIG_COUNT'] = str(count + 1)
    source = verify_upstream(ROOT / 'artifacts/akt/dependencies/upstream', SOURCE_COMMIT)
    before = gate2_build_hashes()
    lock_before = sha256_file(lock_path)
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src') + os.pathsep + str(ROOT / 'third_party'),
           'CUDA_VISIBLE_DEVICES': '', 'PYTHONDONTWRITEBYTECODE': '1',
           'OMP_NUM_THREADS': '2', 'MKL_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2',
           'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTEST_ADDOPTS': '', 'PYTEST_PLUGINS': ''}
    temporary = ROOT / 'artifacts/akt/local-tests' / f'gate2-{run_id}-{uuid.uuid4().hex}'
    temporary.parent.mkdir(parents=True, exist_ok=True)
    commands, groups = [], []
    counts = {'passed': 0, 'failed': 0, 'errors': 0, 'skipped': 0}
    payload = {'schema_version': 1, 'status': 'PASS', 'source_commit': SOURCE_COMMIT,
               'source': source, 'suite': 'tests/akt tests/shared_kt', 'test_result': counts,
               'lock_file': str(lock_path), 'lock_sha256': lock_before, 'build_hashes': before,
               'command': commands, 'python': sys.executable, 'timeout_seconds': timeout_seconds,
               'process_isolation_schema_version': 1, 'test_module_sha256': module_hashes,
               'process_groups': groups,
               'scope': 'CPU synthetic/software gate only, no CUDA or full-training acceptance'}
    try:
        with log.open('xb') as combined:
            for (name, modules), (group_log, group_xml) in zip(partition, group_paths):
                allowance = remaining_seconds(started, timeout_seconds)
                command = [sys.executable, '-B', '-m', 'pytest', *modules, '-q', '-o', 'addopts=',
                           '-p', 'no:cacheprovider', '--basetemp', str(temporary / name),
                           '--junitxml', str(group_xml)]
                commands.append(command)
                group = {'name': name, 'modules': modules, 'command': command,
                         'junit_path': str(group_xml), 'log_path': str(group_log),
                         'timeout_seconds_remaining': allowance}
                groups.append(group)
                try:
                    with group_log.open('xb') as stream:
                        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                                stderr=subprocess.STDOUT, timeout=allowance)
                    group['returncode'] = result.returncode
                    if result.returncode:
                        raise RuntimeError(f'Gate2 group {name} failed, inspect {group_log}')
                    group['test_result'] = test_result(group_xml)
                    group['junit_sha256'] = sha256_file(group_xml)
                    counts['passed'] += group['test_result']['passed']
                finally:
                    if group_log.exists():
                        group['log_sha256'] = sha256_file(group_log)
                        combined.write(('\n=== Gate2 process group ' + name + ' ===\n').encode())
                        with group_log.open('rb') as original:
                            while block := original.read(65536):
                                combined.write(block)
                        combined.flush()
                remaining_seconds(started, timeout_seconds)
        if test_partition(ROOT) != partition or any(sha256_file(ROOT / p) != d for p, d in module_hashes.items()):
            raise ValueError('test module inventory changed during Gate2 execution')
        counts = combine_junit(groups, junit)
        payload['test_result'] = counts
        if (before != gate2_build_hashes()
                or lock_before != sha256_file(selected_lock_file(lock_path))):
            raise ValueError('source or lock changed during Gate2 execution')
        if source != verify_upstream(ROOT / 'artifacts/akt/dependencies/upstream', SOURCE_COMMIT):
            raise ValueError('upstream source changed during Gate2 execution')
        remaining_seconds(started, timeout_seconds)
    except (TimeoutError, ChildTimeout) as exc:
        if log.exists():
            payload['test_log_sha256'] = sha256_file(log)
        resource_rejection(report, payload, started, timeout_seconds, exc)
    own_report_sha = None
    pointer = directory / 'gate2-current.json'
    old_pointer = None
    pointer_published = False
    try:
        remaining_seconds(started, timeout_seconds)
        payload.update(elapsed_seconds=timeout_seconds-remaining_seconds(started, timeout_seconds),
                       test_log_sha256=sha256_file(log), junit_sha256=sha256_file(junit))
        validate_gate2_elapsed_budget(payload['elapsed_seconds'], timeout_seconds)
        with report.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        own_report_sha = sha256_file(report)
        if publish_current:
            old_pointer = pointer.read_bytes() if pointer.exists() else None
            if old_pointer is not None:
                with (directory / f'gate2-pointer-before-{run_id}.json').open('xb') as stream:
                    stream.write(old_pointer)
            pointer_payload = {'schema_version': 1, 'evidence_file': report.name,
                               'evidence_sha256': own_report_sha, 'test_log_file': log.name,
                               'test_log_sha256': sha256_file(log)}
            temp = directory / f'gate2-current-{uuid.uuid4().hex}.tmp'
            with temp.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump(pointer_payload, stream, sort_keys=True)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
            # Actual reader, source and selected lock validated before publication.
            require_gate2_evidence(AKTConfig(), project_root=ROOT, gate2_report=temp, lock_file=lock_path)
            remaining_seconds(started, timeout_seconds)
            temp.replace(pointer)
            pointer_published = True
        # Includes all subprocess waits, merged receipts, validation and publication.
        remaining_seconds(started, timeout_seconds)
    except (TimeoutError, ChildTimeout) as exc:
        if pointer_published:
            if old_pointer is None:
                pointer.unlink()
            else:
                rollback = directory / f'gate2-rollback-{uuid.uuid4().hex}.tmp'
                with rollback.open('xb') as stream:
                    stream.write(old_pointer); stream.flush(); os.fsync(stream.fileno())
                rollback.replace(pointer)
            payload['late_pointer_rollback'] = True
        resource_rejection(report, payload, started, timeout_seconds, exc, own_report_sha=own_report_sha)
    return {'report': str(report.relative_to(ROOT)), 'test_result': counts,
            'published_current': publish_current, 'report_sha256': sha256_file(report)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--publish-current', action='store_true')
    parser.add_argument('--timeout-seconds', type=int, default=300,
                        help='CPU software suite only, explicit maximum 600 seconds; default 300')
    parser.add_argument('--lock-file', type=Path,
                        help='existing project AKT lock; default requirements-akt.lock.txt remains unchanged')
    args = parser.parse_args()
    print(json.dumps(refresh(args.run_id, publish_current=args.publish_current,
                             timeout_seconds=args.timeout_seconds, lock_file=args.lock_file),
                     ensure_ascii=False, indent=2))
