"""ROOT-only proposed launch: owned27/cleanup3, whole30; không tự dispatch."""
from pathlib import Path
import hashlib, json, sys, time
R=Path(__file__).resolve().parents[4]; P=Path(__file__).resolve().parent
start=time.perf_counter(); wall=time.time()
assert len(sys.argv)==2
expected_packet=sys.argv[1]
raw=(P/'edge_artifact_native03_expectation.json').read_bytes()
assert len(raw)<=131072 and hashlib.sha256(raw).hexdigest()==expected_packet
a=json.loads(raw)
sha=lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert all((R/n).stat().st_size<=262144 and sha(R/n)==h for n,h in a['source_pins'].items())
assert all((R/n).stat().st_size<=262144 and sha(R/n)==h for n,h in a['prereview_test_receipts']['files_sha256'].items())
pure=json.loads((R/a['prereview_test_receipts']['outer']).read_bytes())
assert pure['status']=='ACCEPTED_66_DATA_ONLY_FIXTURES' and pure['counts']==dict(tests=66,failures=0,errors=0,skipped=0)
assert not (P/'edge-artifact-cross-ready04-owned/postwrite_rejection.json').exists()
assert not (P/'edge-artifact-native03').exists() and not (P/'edge-artifact-native03-owned').exists()
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import run_owned
receipt=run_owned(P/'check_edge_artifact_native03.py',[expected_packet],P/'edge-artifact-native03-owned',
    expected_worker_sha256=a['source_pins'][a['worker_relative']],
    approval_reference='ROOT_REVIEW_REQUIRED_READONLY_METHOD24_ARTIFACT31_30S_0FITS_0NN',
    max_seconds=27,cleanup_reserve_seconds=3,max_output_bytes=16384)
owned=P/'edge-artifact-native03-owned'
def write(name,value):
    with (owned/name).open('x',encoding='utf-8') as handle:json.dump(value,handle,ensure_ascii=False,indent=2)
write('receipt.json',receipt)
error=None; child=None; manifest=None
phase='read_child_receipts'
try:
    out=P/'edge-artifact-native03'
    assert not (out/'postbudget_failure.json').exists() and not (out/'resource-failure.json').exists()
    assert (out/'result.json').stat().st_size<=131072 and (out/'output-manifest.json').stat().st_size<=131072
    child=json.loads((out/'result.json').read_bytes()); manifest=json.loads((out/'output-manifest.json').read_bytes())
    phase='verify_child_manifest'
    assert set(manifest['files_sha256'])=={'source_before.json','source_after.json','summary.json','result.json'}
    assert manifest['expectation_sha256']==expected_packet
    assert all((out/n).stat().st_size<=131072 and sha(out/n)==h for n,h in manifest['files_sha256'].items())
    phase='verify_child_acceptance'
    assert child['status']=='READ_ONLY_COMPLETE_PENDING_OUTER' and child['error'] is None and child['score_count']==31
    assert child['source_before']==child['source_after']==a['source_pins'] and child['source_unchanged']
    assert not child['forbidden_attempts'] and not child['unexpected_heavy_modules'] and not child['monitor_errors'] and child['monitor_stopped']
    assert child['resources']['observed_peak_rss_bytes']<=536870912 and child['resources']['observed_minimum_available_ram_bytes']>=1073741824
    assert child['model_calls']==child['new_solver_calls']==0
    assert all(sha(R/n)==h for n,h in a['source_pins'].items())
except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc),phase=phase)
elapsed=max(time.perf_counter()-start,time.time()-wall)
ok=bool(error is None and receipt.get('accepted') and receipt.get('cleanup_accepted')
    and receipt.get('job_active_after_cleanup')==0 and receipt.get('popen_handle_closed')
    and receipt.get('returncode')==0 and elapsed<30)
final=dict(status='ACCEPTED_ACTUAL_ARTIFACT_READ_ONLY_NOT_MODEL_EFFICACY' if ok else 'REJECTED_ACTUAL_ARTIFACT_READ_ONLY',
    error=error,expectation_sha256=expected_packet,elapsed_seconds=elapsed,cap_seconds=30,
    model_calls=0,new_solver_calls=0,score_count=None if child is None else child['score_count'],
    child_result_sha256=None if child is None else sha(P/'edge-artifact-native03/result.json'),
    child_manifest_sha256=None if manifest is None else sha(P/'edge-artifact-native03/output-manifest.json'),
    child_error=None if child is None else child.get('error'))
write('final.json',final)
if max(time.perf_counter()-start,time.time()-wall)>=30:
    write('postwrite_rejection.json',dict(status='REJECTED_POSTPUBLICATION_TIME'));ok=False
print(json.dumps(final));raise SystemExit(0 if ok else 1)
