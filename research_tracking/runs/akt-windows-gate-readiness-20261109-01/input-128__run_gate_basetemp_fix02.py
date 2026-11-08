"""ROOT-only whole60s/owned55inclcleanup3/worker50; no fullGate retry."""
import time
START = time.perf_counter()
WALL = time.time()
from pathlib import Path
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/'check_gate_basetemp_fix02.py'
OUT = PREP/'gate-basetemp-fix02-owned'
CHILD = PREP/'gate-basetemp-fix02'
BASE = PREP/'g2b02'
PINS = {'scripts/akt/refresh_gate2.py':'9608ddfe1450b2d78699d5ec95d26b8cd65d4439fcc7bda209f698b2e4a7f9ef',
        'tests/akt/test_gate2_refresh.py':'255c07a3a1af2d458c8586bd206a3151baadeae76d1fa0a2ce3362409da8d5df'}


def need(ok,reason):
    if not ok: raise ValueError(reason)


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed(): return max(time.perf_counter()-START,time.time()-WALL)


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n'); stream.flush()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker-sha256',required=True); parser.add_argument('--approval-reference',required=True)
    args=parser.parse_args()
    need(args.approval_reference.strip() and sha(WORKER)==args.worker_sha256,'reviewed controller/review')
    need(sha(ROOT/'scripts/research/windows_owned_worker.py')=='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1','unchanged accepted helper')
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import run_owned,safe,entry
    entry()
    for path in (WORKER,OUT,CHILD,BASE): safe(path)
    need(not any(path.exists() for path in (OUT,CHILD,BASE)),'exclusive attempt/fresh basetemp; no deletion/overwrite')
    need(all(sha(ROOT/name)==digest for name,digest in PINS.items()),'reviewed source2pins')
    import psutil
    need(psutil.virtual_memory().available>=1024**3,'fresh1GiB admission')
    owned_seconds=min(55.,60.-elapsed()-3.)
    need(owned_seconds>53,'setup must leave worker50/ownedcleanup3 and outerpostcheck reserve')
    receipt=run_owned(WORKER,[],OUT,expected_worker_sha256=args.worker_sha256,
        approval_reference=args.approval_reference,max_seconds=owned_seconds,cleanup_reserve_seconds=3,max_output_bytes=32768)
    write(OUT/'receipt.json',receipt)
    errors=[]; result=counts=None
    try:
        result=json.loads((CHILD/'result.json').read_bytes())
        tree=ET.parse(CHILD/'junit.xml').getroot()
        counts={k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
        need(len(list(tree.iter('testcase')))==77 and counts==dict(tests=77,failures=0,errors=0,skipped=0),'exact actual77 noFES')
        need(receipt['accepted'] is True and receipt['returncode']==0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['cleanup_errors']==[],'owned worker/cleanup')
        need(result['status']=='ACCEPTED_FOCUSED_GATE_FIX_PENDING_OUTER' and result['pytest_exit_code']==0
             and result['counts']==counts and result['errors']==result['forbidden_attempts']==result['heavy_modules_loaded']==[]
             and result['source_before']==result['source_after']==PINS
             and result['monitor_stopped'] is True and result['environment_restored'] is True
             and result['test_environment_unchanged'] is True
             and result['native_os_metadata']['phase_closed'] is True,'actual child result/purity/restoration')
        need(len(result['actual_nodeids'])==len(set(result['actual_nodeids']))==77
             and set(result['actual_nodeids'])==set(result['expected_nodeids']),'exact old76 plusnewregression identities')
        need(result['resources']['observed_peak_bytes']<=512*1024**2
             and result['resources']['observed_minimum_available_ram_bytes']>=1024**3
             and result['elapsed_seconds']<50,'worker resource bounds')
        need(not any((CHILD/name).exists() for name in ('resource-failure.json','postwrite-rejection.json')),'late child failure')
        need(all(sha(ROOT/name)==digest for name,digest in PINS.items()) and sha(WORKER)==args.worker_sha256,'postsource pins')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__,message=str(error)))
    accepted=not errors and elapsed()<60
    final=dict(status='ACCEPTED_GATE_BASETEMP_FIX_FIXTURES_ONLY' if accepted else 'REJECTED_GATE_BASETEMP_FIX',
        counts=counts,errors=errors,elapsed_seconds=elapsed(),whole_cap_seconds=60,owned_cap_seconds=55,
        cleanup_seconds=3,worker_cap_seconds=50,source_pins=PINS,worker_sha256=args.worker_sha256,
        owned_allocated_seconds=owned_seconds,
        owned_receipt=receipt,child_result_sha256=sha(CHILD/'result.json') if (CHILD/'result.json').exists() else None,
        junit_sha256=sha(CHILD/'junit.xml') if (CHILD/'junit.xml').exists() else None,
        pytest_log_sha256=sha(CHILD/'pytest.log') if (CHILD/'pytest.log').exists() else None,
        scope_vi='77 real targeted fixture cases expected; real TempPathFactory/filesystem, fake publisher subprocess/report. Not fullGate/CUDA/research readiness. No retries.')
    write(OUT/'final.json',final)
    if elapsed()>=60:
        write(OUT/'postwrite-rejection.json',dict(status='REJECTED_OUTER_POSTWRITE_BUDGET',elapsed_seconds=elapsed()));accepted=False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_GATE_BASETEMP_FIX',counts=counts,elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__': main()
