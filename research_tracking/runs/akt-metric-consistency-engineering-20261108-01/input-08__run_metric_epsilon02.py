"""ROOT: bound45giây gồm owned cleanup và postchecks; không train/model."""
from pathlib import Path
import hashlib,json,sys,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import run_owned
worker=P/'check_metric_epsilon02.py';out=P/'metric_epsilon02-owned'
names=('src/knowledge_tracing/akt/evaluation.py','tests/akt/test_evaluation.py',
       'src/knowledge_tracing/gam_kt/evaluation.py','src/knowledge_tracing/bkt_baseline/metrics.py',
       'src/knowledge_tracing/paired_bootstrap.py')
expected={name:hashlib.sha256((R/name).read_bytes()).hexdigest() for name in names}
start=time.perf_counter();wall=time.time()
receipt=run_owned(worker,[],out,expected_worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),
                  approval_reference='USER_LOCAL_ENGINEERING_PAIRED_EPSILON_13METRIC_FIXTURES_0NN',
                  max_seconds=42,cleanup_reserve_seconds=3,max_output_bytes=16384)
with (out/'receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
rp=P/'metric_epsilon02/result.json';jp=P/'metric_epsilon02/junit.xml'
result=json.loads(rp.read_bytes()) if rp.exists() else None
try:suites=ET.parse(jp).getroot() if jp.exists() else None
except ET.ParseError:suites=None
counts=None if suites is None else {key:sum(int(s.get(key,'0')) for s in suites.iter('testsuite')) for key in ('tests','failures','errors','skipped')}
elapsed=max(time.perf_counter()-start,time.time()-wall)
accepted=bool(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0
              and receipt['popen_handle_closed'] and result and result['pytest_exit_code']==0 and counts
              and counts==dict(tests=13,failures=0,errors=0,skipped=0) and elapsed<45
              and result['source_unchanged'] is True and result['source_before']==result['source_after']==expected
              and result['environment_restored'] is True and result['actual_subprocess_attempts']==[]
              and result['heavy_modules_loaded']==[] and result['available_ram_end']>=1024**3
              and result['process_peak_rss_bytes'] is not None and result['process_peak_rss_bytes']<=512*1024**2
              and all(hashlib.sha256((R/name).read_bytes()).hexdigest()==digest for name,digest in expected.items()))
final=dict(status='ACCEPTED_METRIC_FIXTURE_ONLY' if accepted else 'REJECTED_METRIC_FIXTURE',
           counts=counts,elapsed_seconds=elapsed,cap_seconds=45,model_calls=0,solver_fits=0)
with (out/'final.json').open('x',encoding='utf-8') as f:json.dump(final,f,ensure_ascii=False,indent=2);f.write('\n')
if max(time.perf_counter()-start,time.time()-wall)>=45:
    with (out/'postwrite_rejection.json').open('x',encoding='utf-8') as f:json.dump({'status':'REJECTED_POSTWRITE_BUDGET'},f)
    accepted=False
print(json.dumps(final,ensure_ascii=False));raise SystemExit(0 if accepted else 1)
