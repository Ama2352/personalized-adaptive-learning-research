"""ROOT-only whole60s/owned57inclcleanup3/worker54, focused JUnit fixtures."""
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
WORKER = PREP/'check_gate_junit_items01.py'
OUT = PREP/'gate-junit-items01-owned'
CHILD = PREP/'gate-junit-items01'
BASE = PREP/'gji01'
PACKET = PREP/'gate_junit_items01_packet.json'
PACKET_SHA = 'ce48d3d576c68503e84d56edb2d9b431d30aa3e7d28bd952e4ab87ddaa8b367a'
PINS = {'scripts/akt/refresh_gate2.py':'8689c5b4737f4eae00459f4a3bc85c22206f58974274304fa4411e36f9acc055',
        'tests/akt/test_gate2_refresh.py':'268ace8716285c35db15caaae1efc819776795e3ef931f2e14f41b9cbe2a1e3c'}


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
    need(sha(PACKET)==PACKET_SHA,'expected99 explicit identities packet')
    import psutil
    need(psutil.virtual_memory().available>=2*1024**3,'fresh2GiB admission')
    owned_seconds=min(57.,60.-elapsed()-1.)
    need(owned_seconds>55,'setup must leave worker54/ownedcleanup3 allowance')
    receipt=run_owned(WORKER,[],OUT,expected_worker_sha256=args.worker_sha256,
        approval_reference=args.approval_reference,max_seconds=owned_seconds,cleanup_reserve_seconds=3,max_output_bytes=32768)
    write(OUT/'receipt.json',receipt)
    errors=[]; result=counts=None
    try:
        result=json.loads((CHILD/'result.json').read_bytes())
        tree=ET.parse(CHILD/'junit.xml').getroot()
        counts={k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
        need(len(list(tree.iter('testcase')))==99 and counts==dict(tests=99,failures=0,errors=0,skipped=0)
             and not any(list(tree.iter(tag)) for tag in ('failure','error','skipped')),'exact actual99 noFES')
        need(receipt['accepted'] is True and receipt['returncode']==0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['cleanup_errors']==[],'owned worker/cleanup')
        need(result['status']=='ACCEPTED_FOCUSED_GATE_FIX_PENDING_OUTER' and result['pytest_exit_code']==0
             and result['counts']==counts and result['errors']==result['forbidden_attempts']==result['heavy_modules_loaded']==[]
             and result['source_before']==result['source_after']==PINS
             and result['monitor_stopped'] is True and result['environment_restored'] is True
             and result['test_environment_unchanged'] is True
             and result['temporary_cache_restored'] is True and result['packet_sha256']==PACKET_SHA
             and result['native_os_metadata']['phase_closed'] is True,'actual child result/purity/restoration')
        expected_packet=json.loads(PACKET.read_bytes())
        need(len(result['actual_nodeids'])==len(set(result['actual_nodeids']))==99
             and set(result['actual_nodeids'])==set(result['expected_nodeids'])==set(expected_packet['expected_nodeids']),
             'exact old77 plusnew22 identities')
        need(result['resources']['observed_peak_bytes']<=1024**3
             and result['resources']['observed_minimum_available_ram_bytes']>=2*1024**3
             and result['elapsed_seconds']<54,'worker resource bounds')
        need(not any((CHILD/name).exists() for name in ('resource-failure.json','postwrite-rejection.json')),'late child failure')
        need(all(sha(ROOT/name)==digest for name,digest in PINS.items()) and sha(WORKER)==args.worker_sha256
             and sha(PACKET)==PACKET_SHA,'postsource pins')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__,message=str(error)))
    accepted=not errors and elapsed()<60
    final=dict(status='ACCEPTED_GATE_JUNIT_ITEM_FIXTURES_ONLY' if accepted else 'REJECTED_GATE_JUNIT_ITEM_FIXTURES',
        counts=counts,errors=errors,elapsed_seconds=elapsed(),whole_cap_seconds=60,owned_cap_seconds=57,
        cleanup_seconds=3,worker_cap_seconds=54,source_pins=PINS,worker_sha256=args.worker_sha256,packet_sha256=PACKET_SHA,
        owned_allocated_seconds=owned_seconds,
        owned_receipt=receipt,child_result_sha256=sha(CHILD/'result.json') if (CHILD/'result.json').exists() else None,
        junit_sha256=sha(CHILD/'junit.xml') if (CHILD/'junit.xml').exists() else None,
        pytest_log_sha256=sha(CHILD/'pytest.log') if (CHILD/'pytest.log').exists() else None,
        scope_vi='99 explicit targeted fixture identities, real XML/TempPathFactory/filesystem and synthetic publisher reports.')
    write(OUT/'final.json',final)
    if elapsed()>=60:
        write(OUT/'postwrite-rejection.json',dict(status='REJECTED_OUTER_POSTWRITE_BUDGET',elapsed_seconds=elapsed()));accepted=False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_GATE_BASETEMP_FIX',counts=counts,elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__': main()
