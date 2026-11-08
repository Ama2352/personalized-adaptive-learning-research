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
           'OMP_NUM_THREADS': '2', 'MKL_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2'}
    temporary = ROOT / 'artifacts/akt/local-tests' / f'gate2-{run_id}-{uuid.uuid4().hex}'
    temporary.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-B', '-m', 'pytest', 'tests/akt', 'tests/shared_kt', '-q',
               '-p', 'no:cacheprovider', '--basetemp', str(temporary), '--junitxml', str(junit)]
    started = time.perf_counter()
    with log.open('xb') as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                timeout=timeout_seconds)
    if result.returncode:
        raise RuntimeError(f'Gate2 tests failed, inspect {log}')
    counts = test_result(junit)
    if (before != gate2_build_hashes()
            or lock_before != sha256_file(selected_lock_file(lock_path))):
        raise ValueError('source or lock changed during Gate2 execution')
    if source != verify_upstream(ROOT / 'artifacts/akt/dependencies/upstream', SOURCE_COMMIT):
        raise ValueError('upstream source changed during Gate2 execution')
    elapsed = time.perf_counter() - started
    payload = {'schema_version': 1, 'status': 'PASS', 'source_commit': SOURCE_COMMIT,
               'source': source, 'suite': 'tests/akt tests/shared_kt', 'test_result': counts,
               'lock_file': str(lock_path), 'lock_sha256': lock_before, 'build_hashes': before,
               'test_log_sha256': sha256_file(log), 'junit_sha256': sha256_file(junit),
               'command': command, 'python': sys.executable,
               'elapsed_seconds': elapsed, 'timeout_seconds': timeout_seconds,
               'scope': 'CPU synthetic/software gate only, no CUDA or full-training acceptance'}
    try:
        validate_gate2_elapsed_budget(elapsed, timeout_seconds)
    except ValueError as exc:
        # Exit 0/JUnit PASS không đủ: Windows wait và monotonic elapsed có thể
        # tính thời gian suspend khác nhau. Giữ rejection độc quyền trước pointer.
        payload.update(status='REJECTED_RESOURCE_BOUND', resource_error=str(exc),
                       observed_elapsed_seconds=repr(elapsed), allowed_seconds=timeout_seconds)
        if type(elapsed) not in (int, float) or (type(elapsed) is float and not math.isfinite(elapsed)):
            # Chuỗi repr giữ NaN/Infinity mà không tạo JSON numeric phi chuẩn.
            payload['elapsed_seconds'] = repr(elapsed)
        payload['observed_elapsed_seconds'] = payload['elapsed_seconds']
        with report.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        raise TimeoutError(f'Gate2 elapsed resource bound rejected; inspect {report}') from exc
    with report.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    pointer_payload = {'schema_version': 1, 'evidence_file': report.name,
                       'evidence_sha256': sha256_file(report), 'test_log_file': log.name,
                       'test_log_sha256': sha256_file(log)}
    if publish_current:
        pointer = directory / 'gate2-current.json'
        if pointer.exists():
            with (directory / f'gate2-pointer-before-{run_id}.json').open('xb') as stream:
                stream.write(pointer.read_bytes())
        temp = directory / f'gate2-current-{uuid.uuid4().hex}.tmp'
        with temp.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(pointer_payload, stream, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(pointer)
        require_gate2_evidence(AKTConfig(), project_root=ROOT, lock_file=lock_path)
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
