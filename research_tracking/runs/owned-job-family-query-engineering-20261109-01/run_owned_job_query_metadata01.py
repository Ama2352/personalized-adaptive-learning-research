"""ROOT probe6query,whole10/owned7/worker5, chỉ metadata ownJob."""
import time
START = time.monotonic()
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP / 'owned-job-query-metadata01-owned'
CHILD = PREP / 'owned-job-query-metadata01'
WORKER = PREP / 'check_owned_job_query_metadata01.py'
sys.path.insert(0, str(ROOT / 'scripts/research'))
from windows_owned_worker import entry, safe, run_owned
entry()
assert len(sys.argv) == 2 and not safe(OUT).exists() and not safe(CHILD).exists()
assert hashlib.sha256(WORKER.read_bytes()).hexdigest() == sys.argv[1]
assert hashlib.sha256((ROOT / 'scripts/research/windows_owned_worker.py').read_bytes()).hexdigest() == '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
source_paths = [WORKER, Path(__file__).resolve(), ROOT / 'scripts/research/windows_owned_worker.py']
source_before = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
import psutil
free = int(psutil.virtual_memory().available)
if free < 1280 * 1024**2:
    OUT.mkdir()
    (OUT / 'final.json').write_text(json.dumps(dict(status='NO_GO_RAM_BEFORE_CHILD', available_bytes=free,
        admission_bytes=1280*1024**2, model_world_calls=0, owned_launch_started=False)), encoding='utf-8')
    raise SystemExit(1)
receipt = run_owned(WORKER, [sys.argv[1]], OUT, expected_worker_sha256=sys.argv[1],
    approval_reference='ROOT_METADATA_JOB_QUERY6_NO_SCIENTIFIC_MODULES',
    max_seconds=min(7., 10. - (time.monotonic() - START) - 2.), cleanup_reserve_seconds=2, max_output_bytes=16384)
if not OUT.exists():
    OUT.mkdir()
error = None
child = None
try:
    assert receipt['accepted'] and receipt['returncode'] == 0 and receipt['cleanup_accepted']
    assert receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed']
    child = json.loads((CHILD / 'result.json').read_bytes())
    assert child['status'] == 'ACCEPTED_JOB_QUERY_METADATA_CHILD' and child['handle_closed']
    assert child['scientific_modules_absent'] and len(child['samples']) == 6
except BaseException as caught:
    error = dict(type=type(caught).__name__, message=str(caught))
source_after = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
accepted = error is None and source_before == source_after and time.monotonic() - START < 10
result = dict(status='ACCEPTED_JOB_QUERY_METADATA_NOT_NATIVE' if accepted else 'REJECTED_RETAIN',
    error=error, child=child, receipt=receipt, admission_available_bytes=free,
    elapsed_seconds=time.monotonic()-START, cap_seconds=10, worker_sha256=sys.argv[1],
    source_before=source_before, source_after=source_after, automatic_retry=False)
with (OUT / 'final.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(dict(status=result['status'], seconds=time.monotonic()-START)))
raise SystemExit(0 if accepted and time.monotonic()-START < 10 else 1)
