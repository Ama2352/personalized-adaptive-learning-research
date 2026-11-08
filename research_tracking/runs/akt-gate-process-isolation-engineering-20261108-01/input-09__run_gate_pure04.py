"""ROOT: một allocation phần mềm mới 240s; giữ nguyên hai lượt rejected cũ."""
from pathlib import Path
import hashlib,json,sys,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import run_owned
worker=P/'check_gate_pure04.py';out=P/'gate_pure04-owned'
names=('scripts/akt/refresh_gate2.py','tests/akt/test_gate2_refresh.py',
       'src/knowledge_tracing/akt/authorization.py','src/knowledge_tracing/akt/config.py',
       'src/knowledge_tracing/akt/provenance.py','src/knowledge_tracing/akt/__init__.py',
       'src/knowledge_tracing/__init__.py','scripts/research/windows_owned_worker.py')
expected={name:hashlib.sha256((R/name).read_bytes()).hexdigest() for name in names}
start=time.perf_counter();wall=time.time()
receipt=run_owned(worker,[],out,expected_worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),
                  approval_reference='USER_LOCAL_ENGINEERING_76PURE_GATE_NEW240S_NO_NATIVE',
                  max_seconds=237,cleanup_reserve_seconds=5,max_output_bytes=16384)
with (out/'receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
rp=P/'gate_pure04/result.json';jp=P/'gate_pure04/junit.xml'
result=json.loads(rp.read_bytes()) if rp.exists() else None
suites=ET.parse(jp).getroot() if jp.exists() else None
counts=None if suites is None else {key:sum(int(s.get(key,'0')) for s in suites.iter('testsuite')) for key in ('tests','failures','errors','skipped')}
elapsed=max(time.perf_counter()-start,time.time()-wall)
accepted=bool(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0
              and receipt['popen_handle_closed'] and result and result['pytest_exit_code']==0 and counts
              and counts==dict(tests=76,failures=0,errors=0,skipped=0) and elapsed<240
              and result['source_unchanged'] is True and result['source_before']==result['source_after']==expected
              and result['environment_restored'] is True and result['actual_subprocess_attempts']==[]
              and result['heavy_modules_loaded']==result['protected_data_attempts']==[]
              and len(result['collected_nodeids'])==len(set(result['collected_nodeids']))==76
              and result['report_count']==228
              and all(hashlib.sha256((R/name).read_bytes()).hexdigest()==digest for name,digest in expected.items()))
final=dict(status='ACCEPTED_76PURE_NOT_FULL_GATE' if accepted else 'REJECTED_PURE_GATE_ATTEMPT',counts=counts,
           elapsed_seconds=elapsed,cap_seconds=240,prior_rejected_seconds=54.055553913116455,
           actual_full_gate=False,actual_model_calls=0)
with (out/'final.json').open('x',encoding='utf-8') as f:json.dump(final,f,ensure_ascii=False,indent=2);f.write('\n')
if max(time.perf_counter()-start,time.time()-wall)>=240:
    with (out/'postwrite_rejection.json').open('x',encoding='utf-8') as f:json.dump({'status':'REJECTED_POSTWRITE_BUDGET'},f)
    accepted=False
print(json.dumps(final,ensure_ascii=False));raise SystemExit(0 if accepted else 1)
