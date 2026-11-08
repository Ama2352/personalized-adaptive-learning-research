"""ROOT: hậu kiểm cached trace đã được nhận, Job ownership/cap10s."""
import time
START = time.perf_counter()
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
WORKER = P/'analyze_prediction_mastery_trace01.py'
SHA = '52370bcc27a0b7ca072d2182b7e2e0f519d21e2113aa7057378eeb76199ade27'
PLAN = '08fd73997c425ca38bd3d70681434b0c5aa68774b1bc5655d4023da3533abf91'
OUTER = '81cf9dd9df724338d6c8d57e01be16b5d2120d27b9730c186b5eb539803e4594'
OUT = P/'mastery-analysis-owned01'
RESULTS = P/'prediction-mastery-analysis-attempt01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists() and not RESULTS.exists()
assert sha(WORKER) == SHA and sha(P/'prediction_mastery_analysis_plan01.json') == PLAN
pure = json.loads((P/'mastery-analysis-pure01/result.json').read_bytes())
assert pure['status'] == 'ACCEPTED_8_BOOLEAN_ANALYSIS_FIXTURES_NOT_SCIENCE'
assert pure['source_before']['analyze_prediction_mastery_trace01.py'] == SHA
sys.path.insert(0, str(ROOT/'scripts/research'))
from windows_owned_worker import run_owned, entry
entry()
receipt = run_owned(WORKER, ['--outer-sha256',OUTER,'--source-sha256',SHA,'--plan-sha256',PLAN,
        '--output-name','prediction-mastery-analysis-attempt01'], OUT,
        expected_worker_sha256=SHA, approval_reference='ROOT_8PURE_ACCEPTED_ALL2160_TRACE_ADMISSION_CACHE_ANALYSIS_ONLY_20261109',
        max_seconds=10-(time.perf_counter()-START)-2, cleanup_reserve_seconds=2, max_output_bytes=32768)
with (OUT/'receipt.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
accepted = receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed']
error = None
inventory = {}
try:
    assert accepted and receipt['worker_returncode_before_cleanup']==0
    assert {p.name for p in RESULTS.iterdir()} == {'summary.json','event_flags.json','validation.json','result.json'}
    result = json.loads((RESULTS/'result.json').read_bytes())
    assert result['status'] == 'INNER_CACHED_MASTERY_ANALYSIS_PENDING_ROOT_OWNED_ACCEPTANCE'
    assert all(sha(RESULTS/n)==h for n,h in result['outputs_sha256'].items())
    valid = json.loads((RESULTS/'validation.json').read_bytes())
    assert valid['paired_events']==1080 and valid['paired_concept_snapshots']==30240 and valid['all18CRC'] and valid['no_rows_dropped']
    assert valid['source_sha256']==SHA and valid['outer_sha256']==OUTER and valid['plan_sha256']==PLAN
    assert sha(WORKER)==SHA and sha(P/'prediction_mastery_analysis_plan01.json')==PLAN
    inventory = {p.name:sha(p) for p in RESULTS.iterdir()}
    assert time.perf_counter()-START < 10
except BaseException as exc:
    accepted=False;error=dict(type=type(exc).__name__,message=str(exc))
final = dict(status='ACCEPTED_CACHED_NATIVE_MASTERY_DIAGNOSTIC_NOT_CALIBRATION' if accepted else 'REJECTED_KEEP_ALL',
             seconds=time.perf_counter()-START,cap_seconds=10,error=error,outputs_sha256=inventory,source_sha256=SHA,
             accepted_trace_outer_sha256=OUTER,native_calls=0,new_independent_N=0)
with (OUT/'final.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(final,f,ensure_ascii=False,indent=2);f.write('\n')
if time.perf_counter()-START >= 10:
    (OUT/'postwrite-rejection.json').write_text('{"status":"REJECTED_POSTWRITE"}',encoding='utf-8');accepted=False
print(json.dumps(final,ensure_ascii=False))
raise SystemExit(0 if accepted else 1)
