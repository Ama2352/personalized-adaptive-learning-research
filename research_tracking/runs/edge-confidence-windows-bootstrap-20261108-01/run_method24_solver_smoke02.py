"""ROOT:30s tổng,25sactive,3scleanup/2sfinalization; không actualcorpusfit."""
import time
START=time.perf_counter();WALL=time.time()
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import run_owned
worker=P/'method24_solver_smoke02.py';out=P/'method24-solver-smoke02-owned'
receipt=run_owned(worker,[],out,expected_worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),
    approval_reference='ROOT_REVIEW_USER_SAFE_CPU_NATIVE_WINDOWS_METADATA_THEN2MANUFACTURED_FITS_0CORPUS',
    max_seconds=28,cleanup_reserve_seconds=3,max_output_bytes=32768)
with (out/'receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
rp=P/'method24-solver-smoke02/result.json';result=json.loads(rp.read_bytes()) if rp.exists() else None
accepted=bool(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0
    and receipt['popen_handle_closed'] and result and result['fit_attempts']==result['fit_completions']==2
    and result['monitor_thread_stopped'] and result['forbidden_attempts']==[]
    and result['actual_corpus_reads']==result['actual_neural_calls']==0
    and result['source_before']==result['source_after']
    and all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in result['source_before'].items())
    and result['resources']['observed_peak_rss_bytes']<=512*1024**2
    and result['resources']['observed_minimum_available_ram_bytes']>=1024**3
    and not any((rp.parent/n).exists() for n in ('failure.json','resource-failure.json'))
    and max(time.perf_counter()-START,time.time()-WALL)<30)
final=dict(status='ACCEPTED_MANUFACTURED_SOLVER_ABI_ONLY' if accepted else 'REJECTED_SOLVER_SMOKE',
    elapsed_seconds=max(time.perf_counter()-START,time.time()-WALL),cap_seconds=30,
    actual_fit_attempts=None if not result else result['fit_attempts'],actual_corpus_reads=0,actual_neural_calls=0)
with (out/'final.json').open('x',encoding='utf-8') as f:json.dump(final,f,ensure_ascii=False,indent=2);f.write('\n')
if max(time.perf_counter()-START,time.time()-WALL)>=30:
    with (out/'postwrite_rejection.json').open('x',encoding='utf-8') as f:json.dump({'status':'REJECTED_POSTWRITE_BUDGET'},f)
    accepted=False
print(json.dumps(final,ensure_ascii=False));raise SystemExit(0 if accepted else 1)
