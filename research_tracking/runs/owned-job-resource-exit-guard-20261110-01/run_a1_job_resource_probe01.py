"""Root-only owned probe30/27/23, không NN hoặc cached learner data."""
import time
START=time.perf_counter()
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
WORKER=PREP/'check_a1_job_resource_probe01.py'
PACKET=PREP/'a1_job_resource_probe01_packet.json'
OWNED=PREP/'a1-job-resource-probe01-owned'
OUT=PREP/'a1-job-resource-probe01'
OUTER=PREP/'a1-job-resource-probe01-outer'


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())


def main():
    parser=argparse.ArgumentParser()
    for n in ('packet-sha256','worker-sha256','outer-sha256','approval-reference'):parser.add_argument('--'+n,required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import entry,run_owned
    entry()
    need(sha(PACKET)==args.packet_sha256 and sha(WORKER)==args.worker_sha256 and sha(Path(__file__))==args.outer_sha256
         and args.approval_reference.strip(),'Root source/packet pins')
    need(not any(p.exists() for p in (OUTER,OWNED,OUT)),'fresh probe namespaces')
    OUTER.mkdir()
    packet=json.loads(PACKET.read_bytes())
    need(all(sha(ROOT/n)==h for n,h in packet['source_pins'].items()),'all source pins before')
    import psutil
    available=int(psutil.virtual_memory().available)
    if available<2*2**30:
        write(OUTER/'final.json',dict(status='NO_GO_PROBE_ADMISSION',available_ram_bytes=available,launched=False));raise SystemExit(1)
    error=None;receipt=result=None
    try:
        receipt=run_owned(WORKER,['--packet-sha256',args.packet_sha256],OWNED,expected_worker_sha256=args.worker_sha256,
            approval_reference=args.approval_reference,max_seconds=min(27.,30.-(time.perf_counter()-START)-3.),cleanup_reserve_seconds=3,max_output_bytes=65536)
        if OWNED.exists():write(OWNED/'receipt.json',receipt)
        need(receipt['accepted']is True and receipt['returncode']==0 and receipt['cleanup_accepted']is True
             and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed']is True,'actual probe terminal/Job0')
        result=json.loads((OUT/'result.json').read_bytes())
        need(result['status']=='RESOURCE_IDENTITY_PROBE_PENDING_OUTER' and result['error']is None and result['denied']==[]
             and result['scientific_modules_absent']is True and result['model_calls']==0 and result['query_handle_closed']is True,'actual probe scope')
        proof=result['proof']
        need(proof['pure_canaries']['passed']==5 and proof['git_calls']==4 and len(proof['git_children'])==4
             and proof['new_resource_identity_post_exit_matches']==4 and result['popen_handles_closed']==4,'exact probe workload')
        need(all(row['WaitForSingleObject']==0 and row['GetExitCodeProcess']==0 and row['resource_identity_after_exit_exact']is True
                 for row in proof['git_children']),'actual exited handle and new identity matches')
        need(result['source_before']==result['source_after']==packet['source_pins']
             and result['resources']['samples']==9 and result['resources']['peak_family_rss_bytes']<=512*2**20
             and result['resources']['minimum_available_ram_bytes']>=1536*2**20,'bounded resource/source proof')
        need(all(sha(ROOT/n)==h for n,h in packet['source_pins'].items()),'all source pins after')
    except BaseException as caught:error=dict(type=type(caught).__name__,message=str(caught))
    accepted=error is None and time.perf_counter()-START<30.
    final=dict(status='ACCEPTED_OWNED_RESOURCE_IDENTITY_PROBE_NO_MODELS' if accepted else 'REJECTED_PROBE_KEEP_PARTIAL',
        error=error,owned_receipt=receipt,worker_result=result,packet_sha256=args.packet_sha256,
        elapsed_seconds=time.perf_counter()-START,whole_cap_seconds=30,
        original_failure_reproduced=False if result is None or result['proof']is None else result['proof']['old_WinError5_reproduced'],
        native_A1_retry_authorized=False,automatic_retry=False)
    write(OUTER/'final.json',final)
    if time.perf_counter()-START>=30.:
        write(OUTER/'postwrite-rejection.json',dict(reason='probe whole30'));accepted=False
    print(json.dumps(dict(status=final['status'],seconds=time.perf_counter()-START,old_WinError5_reproduced=final['original_failure_reproduced'])))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':main()
