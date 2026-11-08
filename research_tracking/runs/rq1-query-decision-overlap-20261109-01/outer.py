"""ROOT outer: cached join tối đa10s, owned8s có cleanup2s; không NN."""
import time
START = time.perf_counter()
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
PLAN = P/'rq1_query_overlap_plan01.json'
WORKER = P/'check_rq1_overlap01.py'
OUT = P/'rq1-query-overlap01-owned'
CHILD = P/'rq1-query-overlap01'
assert not OUT.exists() and not CHILD.exists()
assert hashlib.sha256(PLAN.read_bytes()).hexdigest() == sys.argv[1]
plan = json.loads(PLAN.read_bytes())
for name, expected in plan['sources_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected
sys.path.insert(0, str(ROOT/'scripts/research'))
from windows_owned_worker import entry, run_owned
entry()
receipt = run_owned(WORKER, [sys.argv[1]], OUT,
    expected_worker_sha256=plan['sources_sha256'][WORKER.relative_to(ROOT).as_posix()],
    approval_reference='ROOT_CACHED_RQ1_QUERY_DECISION_OVERLAP_NO_NEW_MODEL_OR_WORLD',
    max_seconds=min(8., 10.-(time.perf_counter()-START)), cleanup_reserve_seconds=2,
    max_output_bytes=16384)
with (OUT/'receipt.json').open('x', encoding='utf-8') as stream:
    json.dump(receipt, stream, ensure_ascii=False, indent=2); stream.write('\n')
child = json.loads((CHILD/'validation.json').read_bytes())
accepted = receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup'] == 0
accepted = accepted and receipt['returncode'] == 0 and receipt['popen_handle_closed']
accepted = accepted and child['status'] == 'ACCEPTED_CACHED_OVERLAP_NOT_CAUSAL' and child['scientific_modules_loaded'] == []
accepted = accepted and time.perf_counter()-START < 10
final = dict(status='ACCEPTED_CACHED_JOIN_NOT_NEW_RESEARCH_SAMPLE' if accepted else 'REJECTED_KEEP_ALL',
             seconds=time.perf_counter()-START, cap_seconds=10, worker_cap_seconds=6, pairs=child['pairs'],
             fixture_tests=child['tests'], model_calls=0, plan_sha256=sys.argv[1])
with (OUT/'final.json').open('x', encoding='utf-8') as stream:
    json.dump(final, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(final)); raise SystemExit(0 if accepted else 1)
