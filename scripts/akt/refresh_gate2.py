"""Chạy CPU synthetic suite và phát hành Gate2 gắn đúng source hiện tại."""

import argparse
import json
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

from knowledge_tracing.akt.authorization import gate2_build_hashes, require_gate2_evidence
from knowledge_tracing.akt.config import AKTConfig, SOURCE_COMMIT
from knowledge_tracing.akt.provenance import sha256_file, verify_upstream


def test_result(xml_path):
    suites = list(ET.parse(xml_path).getroot().iter('testsuite'))
    counts = {key: sum(int(suite.attrib.get(key, '0')) for suite in suites)
              for key in ('tests', 'failures', 'errors', 'skipped')}
    if counts['tests'] <= 0 or any(counts[key] for key in ('failures', 'errors', 'skipped')):
        raise ValueError('Gate2 requires a nonempty suite without failures/errors/skips')
    return {'passed': counts['tests'], 'failed': 0, 'errors': 0, 'skipped': 0}


def refresh(run_id, *, publish_current=False):
    if Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
        raise ValueError('use the project .venv interpreter')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', run_id):
        raise ValueError('invalid Gate2 run ID')
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
    lock_before = sha256_file(ROOT / 'requirements-akt.lock.txt')
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src') + os.pathsep + str(ROOT / 'third_party'),
           'CUDA_VISIBLE_DEVICES': '', 'PYTHONDONTWRITEBYTECODE': '1'}
    temporary = ROOT / 'artifacts/akt/local-tests' / f'gate2-{run_id}-{uuid.uuid4().hex}'
    temporary.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-B', '-m', 'pytest', 'tests/akt', 'tests/shared_kt', '-q',
               '-p', 'no:cacheprovider', '--basetemp', str(temporary), '--junitxml', str(junit)]
    started = time.perf_counter()
    with log.open('xb') as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=300)
    if result.returncode:
        raise RuntimeError(f'Gate2 tests failed, inspect {log}')
    counts = test_result(junit)
    if before != gate2_build_hashes() or lock_before != sha256_file(ROOT / 'requirements-akt.lock.txt'):
        raise ValueError('source or lock changed during Gate2 execution')
    if source != verify_upstream(ROOT / 'artifacts/akt/dependencies/upstream', SOURCE_COMMIT):
        raise ValueError('upstream source changed during Gate2 execution')
    payload = {'schema_version': 1, 'status': 'PASS', 'source_commit': SOURCE_COMMIT,
               'source': source, 'suite': 'tests/akt tests/shared_kt', 'test_result': counts,
               'lock_sha256': lock_before, 'build_hashes': before,
               'test_log_sha256': sha256_file(log), 'junit_sha256': sha256_file(junit),
               'command': command, 'python': sys.executable,
               'elapsed_seconds': time.perf_counter() - started,
               'scope': 'CPU synthetic/software gate only, no CUDA or full-training acceptance'}
    with report.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
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
        require_gate2_evidence(AKTConfig())
    return {'report': str(report.relative_to(ROOT)), 'test_result': counts,
            'published_current': publish_current, 'report_sha256': sha256_file(report)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--publish-current', action='store_true')
    args = parser.parse_args()
    print(json.dumps(refresh(args.run_id, publish_current=args.publish_current), ensure_ascii=False, indent=2))
