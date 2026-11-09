"""Root-only owned dry metadata60s; không materialize SAKT authorization."""
import time
START, WALL = time.perf_counter(), time.time()
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/'prepare_sakt_selected_positive01.py'
PACKET = PREP/'sakt_selected_positive01_packet.json'
OUT = PREP/'sakt-selected-positive-package01-owned'
CHILD = PREP/'sakt-selected-positive-package01'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    for name in ('packet-sha256','worker-sha256','controller-sha256','approval-reference'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import entry, run_owned, safe
    entry()
    need(sha(safe(PACKET)) == args.packet_sha256 and sha(safe(WORKER)) == args.worker_sha256
         and sha(Path(__file__)) == args.controller_sha256 and args.approval_reference.strip(), 'reviewed exact dry sources')
    packet = json.loads(PACKET.read_bytes()); pins = packet['source_pins']; inputs = packet['input_pins']; runtime = packet['runtime_pins']
    need(not OUT.exists() and not CHILD.exists() and not (ROOT/packet['future_result']).exists()
         and not (ROOT/packet['future_authorization']).exists(), 'new dry and execution namespaces')
    need(all(sha(safe(ROOT/n)) == h for n,h in {**pins,**inputs}.items())
         and all(sha(Path(n)) == h for n,h in runtime.items()), 'current actual dry source/input/runtime pins')
    import psutil
    available = int(psutil.virtual_memory().available)
    if available < 1280*2**20:
        OUT.mkdir(); write(OUT/'final.json',dict(status='NO_GO_SAKT_DRY_RAM',available_ram_bytes=available,
            required_available_ram_bytes=1280*2**20,owned_launch_started=False,automatic_retry=False));raise SystemExit(1)
    owned = min(57.,60.-elapsed()-3.)
    need(owned > 3., 'one dry whole deadline')
    receipt = run_owned(WORKER, ['--packet-sha256',args.packet_sha256], OUT,
        expected_worker_sha256=args.worker_sha256,approval_reference=args.approval_reference,
        max_seconds=owned,cleanup_reserve_seconds=3,max_output_bytes=65536)
    if not OUT.exists(): OUT.mkdir()
    write(OUT/'receipt.json',receipt)
    errors=[]; child=proposal=None
    try:
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup'] == 0
             and receipt['popen_handle_closed'] is True and receipt['errors'] == receipt['cleanup_errors'] == [], 'owned terminal/cleanup')
        need((CHILD/'result.json').stat().st_size <= 2**20 and (CHILD/'proposal.json').stat().st_size <= 2**20,'bounded dry results')
        child=json.loads((CHILD/'result.json').read_bytes());proposal=json.loads((CHILD/'proposal.json').read_bytes())
        need(child['status']=='ACCEPTED_SAKT_GENUINE_DRY_PENDING_OUTER_NOT_NN' and child['accepted'] is True
             and child['error'] is None and child['denied']==[] and child['scientific_modules_absent'] is True
             and child['authorization_written'] is False and child['model_calls']==0 and child['elapsed_seconds']<50.,'genuine dry only')
        need(child['source_before']==child['source_after']==pins and child['input_before']==child['input_after']==inputs
             and child['runtime_before']==child['runtime_after']==runtime and child['packet_sha256']==args.packet_sha256
             and child['proposal_sha256']==sha(CHILD/'proposal.json'),'actual unchanged provenance and proposal')
        need(proposal['status']=='GENUINE_SAKT_DRY_IDENTITY_NOT_EXECUTION_AUTHORITY'
             and proposal['explicit_root_review_and_materialization_required'] is True
             and proposal['requested_phases']==['select_train80','raw_selection10']
             and not (CHILD/'postwrite_rejection.json').exists(),'not an NN grant or late dry')
        memory=child['resources']
        need(memory['samples']>0 and memory['peak_worker_rss_bytes']<=256*2**20
             and memory['minimum_available_ram_bytes']>=2**30,'cooperative dry worker resource observations')
    except BaseException as caught:
        errors.append(dict(type=type(caught).__name__,message=str(caught)))
    after={n:sha(ROOT/n) for n in pins};input_after={n:sha(ROOT/n) for n in inputs};runtime_after={n:sha(Path(n)) for n in runtime}
    accepted=not errors and after==pins and input_after==inputs and runtime_after==runtime and sha(PACKET)==args.packet_sha256 and elapsed()<60.
    accepted=accepted and not (ROOT/packet['future_result']).exists() and not (ROOT/packet['future_authorization']).exists()
    final=dict(status='ACCEPTED_SAKT_GENUINE_DRY_NOT_NN_AUTHORITY' if accepted else 'REJECTED_SAKT_DRY_KEEP_ALL',
        errors=errors,child_result=child,owned_receipt=receipt,source_after=after,input_after=input_after,runtime_after=runtime_after,
        proposal_sha256=None if proposal is None else sha(CHILD/'proposal.json'),packet_sha256=args.packet_sha256,
        elapsed_seconds=elapsed(),whole_cap_seconds=60,owned_allocated_seconds=owned,worker_cap_seconds=50,
        prelaunch_available_ram_bytes=available,automatic_retry=False,actual_fit_authorized=False)
    write(OUT/'final.json',final)
    if elapsed()>=60.:
        write(OUT/'postwrite_rejection.json',dict(reason='same dry whole deadline after publication'));accepted=False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_SAKT_DRY_KEEP_ALL',seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    main()
