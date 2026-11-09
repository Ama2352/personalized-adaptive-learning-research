"""Watchdog cho một phép tính thăm dò từ bằng chứng đã đóng."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP / 'rq2-fresh-block-uncertainty01-outer'
SOURCE = PREP / 'analyze_rq2_fresh_block_uncertainty01.py'
PLAN = PREP / 'RQ2_FRESH_BLOCK_UNCERTAINTY_SPEC01.md'
SOURCE_SHA = '21dce940bf8c3ddd9114eccde5952c5bbcaea86f90b88e462f8fa89d39463938'
PLAN_SHA = '83f6cfde91ecbd12053de14da1f16295846aded1f798d0592b4cd61aa4b67da8'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


started = time.perf_counter()
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
assert sha(SOURCE) == SOURCE_SHA and sha(PLAN) == PLAN_SHA
assert (PREP / 'ROOT_RQ2_EXPLORATORY_UNCERTAINTY_REVIEW01.md').is_file()
OUT.mkdir()
command = [sys.executable, '-B', str(SOURCE), '--expected-source-sha', SOURCE_SHA,
           '--expected-plan-sha', PLAN_SHA]
write('allocation.json', dict(command=command, whole_cap_seconds=10,
    child_timeout_seconds=9, no_new_worlds_models=True))
error = None
returncode = None
stdout = stderr = b''
try:
    result = subprocess.run(command, cwd=ROOT, capture_output=True,
                            timeout=max(.1, 9 - (time.perf_counter() - started)))
    returncode, stdout, stderr = result.returncode, result.stdout, result.stderr
except subprocess.TimeoutExpired as caught:
    error = 'WATCHDOG_TIMEOUT_NO_AUTOMATIC_RETRY'
    stdout, stderr = caught.stdout or b'', caught.stderr or b''
for name, content in [('stdout.log', stdout), ('stderr.log', stderr)]:
    assert len(content) <= 65536
    with (OUT / name).open('xb') as stream:
        stream.write(content)
child = PREP / 'rq2-fresh-block-uncertainty01/result.json'
receipt = json.loads(child.read_bytes()) if child.exists() else None
accepted = (returncode == 0 and error is None and receipt is not None
    and receipt['status'] == 'ACCEPTED_CACHED_EXPLORATORY_STATISTICS_ONLY'
    and receipt['source_before'] == receipt['source_after']
    and receipt['new_world_model_response_calls'] == 0
    and sha(SOURCE) == SOURCE_SHA and sha(PLAN) == PLAN_SHA
    and time.perf_counter() - started < 10)
write('result.json', dict(accepted=accepted, returncode=returncode, error=error,
    elapsed_seconds=time.perf_counter() - started, child_receipt=receipt,
    stdout_sha256=sha(OUT / 'stdout.log'), stderr_sha256=sha(OUT / 'stderr.log')))
assert time.perf_counter() - started < 10
print(json.dumps(dict(accepted=accepted, returncode=returncode, error=error)))
raise SystemExit(0 if accepted else 1)
