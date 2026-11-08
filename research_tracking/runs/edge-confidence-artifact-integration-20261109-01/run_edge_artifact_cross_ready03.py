"""ROOT one bounded150s software check; no analyzer/actual loader dispatch."""
from pathlib import Path
import hashlib,json,sys,time
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
start=time.perf_counter();wall=time.time()
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import run_owned
a=json.loads((P/'edge_artifact_cross_ready03_allocation.json').read_bytes())
pins=a['source_pins'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(R/n)==h for n,h in pins.items())
worker=P/'check_edge_artifact_cross_ready03.py';out=P/'edge-artifact-cross-ready03-owned'
receipt=run_owned(worker,[],out,expected_worker_sha256=a['worker_sha256'],
    approval_reference='ROOT_LOCAL_PURE58_EDGEARTIFACT_RESOURCE_SNAPSHOTS_0ACTUALDATA_0MODELS',
    max_seconds=147,cleanup_reserve_seconds=3,max_output_bytes=16384)
with (out/'receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
path=P/'edge-artifact-cross-ready03/result.json';r=json.loads(path.read_bytes()) if path.exists() else None
elapsed=max(time.perf_counter()-start,time.time()-wall)
ok=bool(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed']
    and r and r['pytest_exit_code']==0 and r['counts']==dict(tests=58,failures=0,errors=0,skipped=0)
    and r['source_unchanged'] and r['source_before']==r['source_after']==pins and r['environment_restored']
    and not r['forbidden_attempts'] and not r['unexpected_heavy_modules'] and r['monitor_stopped'] and not r['monitor_errors']
    and r['native_os_metadata']['phase_closed'] and r['native_os_metadata']['outside_phase_popen_attempts']==0
    and r['resources']['observed_peak_rss_bytes']<=512*1024**2 and r['resources']['observed_minimum_available_ram_bytes']>=1024**3
    and all(sha(R/n)==h for n,h in pins.items()) and elapsed<150)
result=dict(status='ACCEPTED_58_DATA_ONLY_FIXTURES' if ok else 'REJECTED_DATA_ONLY_FIXTURES',counts=None if r is None else r['counts'],
    elapsed_seconds=elapsed,cap_seconds=150,model_calls=0,solver_fits=0,actual_data_reads=0)
with (out/'final.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
if max(time.perf_counter()-start,time.time()-wall)>=150:
    with (out/'postwrite_rejection.json').open('x',encoding='utf-8') as f:json.dump({'status':'REJECTED_POSTWRITE_BUDGET'},f)
    ok=False
print(json.dumps(result));raise SystemExit(0 if ok else 1)
