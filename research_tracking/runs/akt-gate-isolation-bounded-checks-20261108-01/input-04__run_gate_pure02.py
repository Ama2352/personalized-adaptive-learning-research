"""ROOT: pure Gate tests, owned Job; không gọi full refresh/Gate publication."""
from pathlib import Path
import sys,time,json,hashlib,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import run_owned
start=time.perf_counter();wall=time.time()
worker=P/'check_gate_isolation02.py';attempt=P/'gate_isolation02-owned'
source=hashlib.sha256(worker.read_bytes()).hexdigest()
receipt=run_owned(worker,[],attempt,expected_worker_sha256=source,
    approval_reference='USER_LOCAL_ENGINEERING_GATE_PARTITION_PURE_TESTS_0NATIVE_PRIOR20_TOTAL60',
    max_seconds=37,cleanup_reserve_seconds=3,max_output_bytes=65536)
with (attempt/'outer_receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
result_path=P/'gate_isolation02/result.json';junit=P/'gate_isolation02/junit.xml'
result=json.loads(result_path.read_bytes()) if result_path.exists() else None
suite=ET.parse(junit).getroot() if junit.exists() else None
counts=None if suite is None else {k:sum(int(x.get(k,'0')) for x in suite.iter('testsuite')) for k in ('tests','errors','failures','skipped')}
elapsed=max(time.perf_counter()-start,time.time()-wall)
accepted=bool(receipt['accepted'] and result and result['pytest_exit_code']==0 and counts and counts['tests']>0
    and not any(counts[k] for k in ('errors','failures','skipped')) and elapsed+20<60)
final=dict(status='ACCEPTED_PURE_PARTITION_TESTS_NOT_FULL_GATE' if accepted else 'REJECTED_PURE_TEST_ATTEMPT',
    counts=counts,outer_elapsed_seconds=elapsed,prior_charge_seconds=20,cumulative_seconds=elapsed+20,cap_seconds=60,
    owned_accepted=receipt['accepted'],actual_full_gate=False,actual_model_calls=0)
with (attempt/'final.json').open('x',encoding='utf-8') as f:json.dump(final,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(final,ensure_ascii=False))
raise SystemExit(0 if accepted else 1)
