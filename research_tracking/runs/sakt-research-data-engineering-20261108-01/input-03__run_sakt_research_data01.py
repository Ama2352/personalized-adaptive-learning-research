"""ROOT: bound45giây gồm owned cleanup và postchecks; không train/model."""
from pathlib import Path
import hashlib,json,sys,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import run_owned
worker=P/'check_sakt_research_data01.py';out=P/'sakt_research_data01-owned'
names=('src/knowledge_tracing/sakt/research_data.py','src/knowledge_tracing/sakt/__init__.py',
       'src/knowledge_tracing/sakt/training_data.py','tests/sakt/test_research_data.py',
       'src/knowledge_tracing/akt/research_simulator_data.py','src/knowledge_tracing/simulator_corpus_reader.py')
expected={name:hashlib.sha256((R/name).read_bytes()).hexdigest() for name in names}
start=time.perf_counter();wall=time.time()
receipt=run_owned(worker,[],out,expected_worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),
                  approval_reference='USER_LOCAL_ENGINEERING_SAKT_RESEARCH_DATA_20FIXTURES_0NN',
                  max_seconds=57,cleanup_reserve_seconds=3,max_output_bytes=16384)
with (out/'receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
rp=P/'sakt_research_data01/result.json';jp=P/'sakt_research_data01/junit.xml'
result=json.loads(rp.read_bytes()) if rp.exists() else None
try:suites=ET.parse(jp).getroot() if jp.exists() else None
except ET.ParseError:suites=None
counts=None if suites is None else {key:sum(int(s.get(key,'0')) for s in suites.iter('testsuite')) for key in ('tests','failures','errors','skipped')}
elapsed=max(time.perf_counter()-start,time.time()-wall)
accepted=bool(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0
              and receipt['popen_handle_closed'] and result and result['pytest_exit_code']==0 and counts
              and counts==dict(tests=20,failures=0,errors=0,skipped=0) and elapsed<60
              and result['source_unchanged'] is True and result['source_before']==result['source_after']==expected
              and result['environment_restored'] is True and result['actual_subprocess_attempts']==[]
              and result['heavy_modules_loaded']==[] and result['available_ram_end']>=1024**3
              and result['process_peak_rss_bytes'] is not None and result['process_peak_rss_bytes']<=512*1024**2
              and all(hashlib.sha256((R/name).read_bytes()).hexdigest()==digest for name,digest in expected.items()))
final=dict(status='ACCEPTED_SAKT_DATA_FIXTURE_ONLY' if accepted else 'REJECTED_SAKT_DATA_FIXTURE',
           counts=counts,elapsed_seconds=elapsed,cap_seconds=60,model_calls=0,solver_fits=0)
with (out/'final.json').open('x',encoding='utf-8') as f:json.dump(final,f,ensure_ascii=False,indent=2);f.write('\n')
if max(time.perf_counter()-start,time.time()-wall)>=60:
    with (out/'postwrite_rejection.json').open('x',encoding='utf-8') as f:json.dump({'status':'REJECTED_POSTWRITE_BUDGET'},f)
    accepted=False
print(json.dumps(final,ensure_ascii=False));raise SystemExit(0 if accepted else 1)
