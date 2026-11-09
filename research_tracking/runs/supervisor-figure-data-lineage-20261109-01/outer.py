"""Outer30s cho metadata figure, giữ stdout/stderr nguyên byte."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

start = time.perf_counter()
ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
helper = PREP / 'verify_figure_data_lineage01.py'
pin = 'cdd2005c4474c67eeb9df3b8e28d8f8f1f51c569274c29a2cc2ba9e40de7ad78'
assert hashlib.sha256(helper.read_bytes()).hexdigest() == pin
output = PREP / 'figure-data-lineage-outer01'
assert not output.exists()
output.mkdir()
command = [sys.executable, '-B', str(helper), '--lineage-sha256',
    'bf2128507f850d6d33177814af148fc63132e6594187c875d99da8f80eb5a775',
    '--helper-sha256', pin, '--review-reference', 'ROOT_REVIEWED_FIGURE_LINEAGE_METADATA_ONLY']
timeout = False
try:
    process = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=25)
    stdout, stderr, returncode = process.stdout, process.stderr, process.returncode
except subprocess.TimeoutExpired as error:
    stdout, stderr, returncode = error.stdout or b'', error.stderr or b'', None
    timeout = True
(output / 'stdout.log').write_bytes(stdout)
(output / 'stderr.log').write_bytes(stderr)
result_path = PREP / 'figure-data-lineage-verification01/result.json'
actual = json.loads(result_path.read_bytes()) if result_path.is_file() else None
elapsed = time.perf_counter()-start
accepted = (returncode == 0 and not timeout and elapsed < 30 and actual is not None
    and actual['accepted'] is True and actual['builder_execution'] is False
    and actual['end_to_end_rebuild'] == 'UNKNOWN_NOT_PERFORMED'
    and actual['source_before'] == actual['source_after']
    and not (result_path.parent / 'postwrite_rejection.json').exists())
receipt = dict(status='ACCEPTED_FIGURE_LINEAGE_METADATA_ONLY' if accepted else 'REJECTED_KEEP_ALL',
    accepted=accepted, timed_out=timeout, returncode=returncode, elapsed_seconds=elapsed,
    whole_cap_seconds=30, command=command, helper_sha256=pin,
    result_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest() if actual is not None else None,
    scope_vi='Outer timeout của một child stdlib. Không hardOS/RSS quota hoặc builder/render acceptance.')
(output / 'final.json').write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
print(json.dumps(receipt, ensure_ascii=False))
raise SystemExit(0 if accepted else 1)
