"""ROOT bound150s gồm ownedcleanup và postchecks; không dispatchsurrogatefit."""
from pathlib import Path
import sys,time,json,hashlib,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import run_owned
start=time.perf_counter();wall=time.time();worker=P/'check_method24_pure02.py'
out=P/'method24-pure02-owned'
expected={name:hashlib.sha256((P/name).read_bytes()).hexdigest() for name in ('method24_worker01.py','run_method24_native01.py','method24_config01.json','method24_runtime_profile01.json','test_method24_native01.py')}
receipt=run_owned(worker,[],out,expected_worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),
    approval_reference='USER_LOCAL_ENGINEERING_METHOD24_PURE21CASES_NEW_SOURCE_BRIDGE_FIX_0FITS',
    max_seconds=147,cleanup_reserve_seconds=3,max_output_bytes=16384)
with (out/'receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
result_path=P/'method24-pure02/result.json';junit=P/'method24-pure02/junit.xml'
result=json.loads(result_path.read_bytes()) if result_path.exists() else None
suite=ET.parse(junit).getroot() if junit.exists() else None
counts=None if suite is None else {k:sum(int(s.get(k,'0')) for s in suite.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
elapsed=max(time.perf_counter()-start,time.time()-wall)
accepted=bool(receipt['accepted'] and result and result['pytest_exit_code']==0 and counts and counts['tests']==21
    and not any(counts[k] for k in ('failures','errors','skipped')) and elapsed<150
    and result['source_unchanged'] and result['source_before']==result['source_after']==expected
    and not result['actual_subprocess_attempts'] and not result['heavy_modules_loaded'] and result['environment_restored']
    and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed']
    and all(hashlib.sha256((P/name).read_bytes()).hexdigest()==digest for name,digest in expected.items()))
final=dict(status='ACCEPTED_PURE_ONLY_NOT_NATIVE_FIT' if accepted else 'REJECTED_PURE_ATTEMPT',
    counts=counts,elapsed_seconds=elapsed,cap_seconds=150,owned_accepted=receipt['accepted'],model_calls=0,solver_fits=0)
with (out/'final.json').open('x',encoding='utf-8') as f:json.dump(final,f,ensure_ascii=False,indent=2);f.write('\n')
if max(time.perf_counter()-start,time.time()-wall)>=150:
    with (out/'postwrite_rejection.json').open('x',encoding='utf-8') as f:json.dump({'status':'REJECTED_POSTWRITE_BUDGET'},f)
    accepted=False;final['status']='REJECTED_POSTWRITE_BUDGET'
print(json.dumps(final,ensure_ascii=False))
raise SystemExit(0 if accepted else 1)
