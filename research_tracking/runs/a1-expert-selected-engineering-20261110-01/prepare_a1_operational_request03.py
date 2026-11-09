"""Root-only request mới, giữ auth/spec sau monitor failure0NN; không fit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
OLD=PREP/'a1_expert_engineering01_request.ROOT.json'
OLD_SHA='1d6b7a7c2696500552eab45c8930810d2c340f124fc74581ea5e4ca8f9cc4816'
PROBE=PREP/'a1-job-resource-probe02-outer/final.json'
PROBE_SHA='d2096399c0b250395bf52d0585b4d0ca8d079f161a34b105b6277c07c0bb881a'
MEMBERSHIP=PREP/'a1-membership-exit-probe-root01-outer/final.json'
MEMBERSHIP_SHA='3537b524a3036d1c501fb1707b9563c4651f433348e7298c6c4ee4fb4a49d925'
CANARIES=PREP/'a1-resource-wait-guard-canaries02/result.json'
CANARIES_SHA='608aa127dfd07ffbbee776cf94d1e4afa5305a0763f0620acecbf9469eb37b64'
WORKER=PREP/'check_a1_expert_engineering03.py'
WORKER_SHA='a6fa2e3838d27e288ad1be8ecb33058ef3f7062c0258b4d8b3fb6c765038cc42'
OUTER=PREP/'run_a1_expert_engineering03.py'
OUTER_SHA='126ad0a9c14ab5c5cd6de6d78bd59efc62a5e4aafb68599f408bf687c74c442c'
REQUEST=PREP/'a1_expert_engineering03_request.ROOT.json'
OUT=PREP/'a1-expert-operational-request03'


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    need(path.is_file() and path.stat().st_size<=8*2**20,'bounded source/metadata')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def publish(path,value):
    raw=(json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n').encode()
    need(len(raw)<=2**20,'small operational metadata')
    with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    need(sha(path)==hashlib.sha256(raw).hexdigest(),'exact byte readback')


def main():
    start=time.perf_counter()
    parser=argparse.ArgumentParser();parser.add_argument('--self-sha256',required=True);parser.add_argument('--approval-reference',required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import entry,safe
    entry()
    need(len(args.self_sha256)==64 and sha(Path(__file__))==args.self_sha256 and args.approval_reference.strip(),'Root reviewed exact preparer')
    for path,digest in ((OLD,OLD_SHA),(PROBE,PROBE_SHA),(MEMBERSHIP,MEMBERSHIP_SHA),(CANARIES,CANARIES_SHA),(WORKER,WORKER_SHA),(OUTER,OUTER_SHA)):
        need(len(digest)==64 and sha(path)==digest,'external actual proof/source bytes')
    previous=read(OLD);receipt=read(PREP/'a1-expert-engineering01-owned/receipt.json')
    need(receipt['cleanup_accepted']is True and receipt['job_active_after_cleanup']==0 and receipt['returncode']==125,'original monitor hard-exit and Job0')
    failed=read(PREP/'a1-expert-engineering01/resource-failure.json')
    need(len(failed['errors'])==1 and failed['errors'][0]['type']=='PermissionError'
         and '[WinError 5]' in failed['errors'][0]['message'],'preserved actual original Win5')
    image31_count=0
    for path in (PROBE,MEMBERSHIP):
        actual=read(path)
        need(actual['status']=='ACCEPTED_OWNED_RESOURCE_IDENTITY_PROBE_NO_MODELS' and actual['error']is None
             and actual['owned_receipt']['cleanup_accepted']is True and actual['owned_receipt']['job_active_after_cleanup']==0
             and actual['original_failure_reproduced']is False,'two accepted probes did not reproduce Win5')
        rows=actual['worker_result']['proof']['git_children']
        need(len(rows)==4 and all(row['old_after_exit_error']is not None
             and row['old_after_exit_error']['winerror']==31 for row in rows),'actual four known-exit image-query Win31 per probe')
        image31_count+=len(rows)
    membership_rows=read(MEMBERSHIP)['worker_result']['proof']['git_children']
    need(len(membership_rows)==4 and all(row['membership_after_exit']==dict(returned=True,error=None) for row in membership_rows),
         'actual known-exit IsProcessInJob returned true')
    image31=any(row['old_after_exit_error']is not None and row['old_after_exit_error']['winerror']==31 for row in membership_rows)
    need(image31,'actual known-exit image-query Win31 observation')
    canaries=read(CANARIES)
    expected={'check_a1_expert_engineering03.py':WORKER_SHA,'test_a1_resource_wait_guard01.py':'7f7715c74c7bea80abc9d02ca9f61e6c4a0795f12ec764bd0fc9a78f4320311a'}
    need(canaries['returncode']==0 and canaries['source_before']==canaries['source_after']==expected
         and canaries['source_unchanged']is True and canaries['elapsed_seconds']<canaries['timeout_seconds']==5,'actual current-source canaries')
    log=(PREP/'a1-resource-wait-guard-canaries02/stderr.log').read_bytes().replace(b'\r\n',b'\n')
    need(b'Ran 9 tests' in log and b'\nOK\n' in log,'actual nine-method unittest log')
    config_path=safe(ROOT/previous['native_config_file']);auth=safe(ROOT/previous['authorization_file'])
    need(sha(config_path)==previous['native_config_sha256'] and sha(auth)==previous['authorization_sha256'],'same actual config and authorization')
    native=Path(read(config_path)['output_dir'])
    need(native==ROOT/'experiments/akt/results/main-a1-expert-engineering10x84-20261110-01' and not native.exists(),
         'same unallocated native output; frozen public runner creates it before lazy NN')
    need(not any(path.exists() for path in (REQUEST,OUT,PREP/'a1-expert-engineering03',PREP/'a1-expert-engineering03-owned')),'new operational namespaces')
    for name,digest in previous['source_pins'].items():need(sha(safe(ROOT/name))==digest,'unchanged original source set')
    request=json.loads(json.dumps(previous))
    proof_paths=[Path(__file__).resolve(),WORKER,OUTER,OLD,PROBE,MEMBERSHIP,CANARIES,
        PREP/'a1-expert-engineering01/resource-failure.json',PREP/'a1-expert-engineering01-owned/receipt.json',
        PREP/'a1_job_resource_probe02_packet.json',PREP/'check_a1_job_resource_probe02.py',PREP/'run_a1_job_resource_probe02.py',
        PREP/'a1-membership-exit-probe-root01/result.json',PREP/'a1-resource-wait-guard-canaries02/stdout.log',
        PREP/'a1-resource-wait-guard-canaries02/stderr.log',PREP/'test_a1_resource_wait_guard01.py']
    for path in proof_paths:request['source_pins'][path.relative_to(ROOT).as_posix()]=sha(path)
    request['approval_reference']=args.approval_reference
    need(len(request['source_pins'])<=256,'existing source-count guard')
    for name in previous:
        if name not in ('source_pins','approval_reference'):need(request[name]==previous[name],'same scientific spec/auth/config/runtime/allocation')
    need(time.perf_counter()-start<25.,'bounded metadata preparation')
    OUT.mkdir()
    publish(OUT/'before.json',dict(old_request_sha256=OLD_SHA,authorization_sha256=sha(auth),native_existed=False,
        source_pins=request['source_pins'],prior_monitor_elapsed_seconds=receipt['elapsed_seconds'],prior_NN_updates=0,
        zero_NN_basis='Immutable selected runner creates native output before _tools; native output absent plus owned Job0.',
        original_Win5_cause_confirmed=False,known_exited_image_query_Win31_observed=image31,
        known_exited_image_query_Win31_count=image31_count,operational_Git_children=8,new_research_N=0))
    publish(REQUEST,request)
    need(sha(OLD)==OLD_SHA and sha(auth)==previous['authorization_sha256'] and not native.exists(),'parent authority/source unchanged, no model execution')
    publish(OUT/'result.json',dict(status='PREPARED_OPERATIONAL_A1_REQUEST03_SAME_AUTH_NO_NN',request_sha256=sha(REQUEST),
        authorization_sha256=sha(auth),auth_written=False,models_executed=False,original_failure_preserved=True,
        elapsed_seconds=time.perf_counter()-start))


if __name__=='__main__':main()
