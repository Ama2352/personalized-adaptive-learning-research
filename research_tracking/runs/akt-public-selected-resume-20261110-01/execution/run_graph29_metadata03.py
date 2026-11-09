"""Root-only collect trước, test120s sau external collection review; không native."""
import time
PERF,WALL,MONO=time.perf_counter,time.time,time.monotonic
START,START_WALL,START_MONO=PERF(),WALL(),MONO()
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
WORKER=PREP/'check_graph29_metadata03.py'
PACKET=PREP/'graph29_metadata03_packet.json'


def need(ok,message):
    if not ok:raise ValueError(message)


def elapsed():return max(PERF()-START,WALL()-START_WALL,MONO()-START_MONO)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    need(path.is_file() and path.stat().st_size<=1024**2,'bounded actual receipt')
    return json.loads(path.read_bytes())


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('collect','tests'),required=True)
    parser.add_argument('--attempt',required=True)
    for name in ('packet-sha256','worker-sha256','controller-sha256','approval-reference'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--collection-sha256');args=parser.parse_args()
    need(len(args.attempt)==2 and all('0'<=c<='9' for c in args.attempt),'attempt requires exactly two ASCII digits')
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import entry,safe,run_owned
    entry()
    need(sha(safe(PACKET))==args.packet_sha256 and sha(WORKER)==args.worker_sha256
         and sha(Path(__file__).resolve())==args.controller_sha256 and args.approval_reference.strip(),'Root source/packet approval')
    packet=read(PACKET);pins=packet['source_pins'];runtime_pins=packet['runtime_pins'];allocation=packet['allocations'][args.mode]
    before={n:sha(safe(ROOT/n)) for n in pins};runtime_before={n:sha(Path(n)) for n in runtime_pins}
    need(before==pins and runtime_before==runtime_pins,'current canonical source/runtime bytes')
    need(not any(n.split('.')[0] in ('torch','numpy','pandas') for n in sys.modules),'fresh metadata outer')
    stem='graph29-metadata-'+('collection' if args.mode=='collect' else 'tests')+args.attempt
    child=PREP/stem;out=PREP/(stem+'-owned')
    base=ROOT/'artifacts/akt/local-tests'/(('g29c' if args.mode=='collect' else 'g29t')+args.attempt)
    need(not any(safe(p).exists() for p in (child,out,base)),'new attempt and short basetemp')
    collection_path=safe(PREP/('graph29-metadata-collection'+args.attempt+'-owned/final.json'))
    if args.mode=='tests':
        need(args.collection_sha256 and sha(collection_path)==args.collection_sha256,'external Root collection verdict pin')
        collection=read(collection_path)
        need(collection['attempt']==args.attempt and collection['child_result']['attempt']==args.attempt
             and collection['status']=='ACCEPTED_BATCHC_COLLECTION_ONLY_NOT_TEST_PASS'
             and not (collection_path.parent/'postwrite_rejection.json').exists() and collection['errors']==[]
             and collection['source_after']==pins and collection['runtime_after']==runtime_pins,'current accepted collection only')
    else:need(args.collection_sha256 is None,'collect first without fabricated expected outcome')
    import psutil
    available=int(psutil.virtual_memory().available)
    prelaunch_floor=1280*1024**2
    need(packet['resource_profile']['prelaunch_minimum_available_ram_bytes']==prelaunch_floor,'reviewed prelaunch cushion')
    if available<prelaunch_floor:
        out.mkdir();write(out/'final.json',dict(status='NO_GO_METADATA_RAM',mode=args.mode,attempt=args.attempt,available_ram_bytes=available,
            prelaunch_minimum_available_ram_bytes=prelaunch_floor,owned_launch_started=False,automatic_retry=False));raise SystemExit(1)
    worker_args=['--mode',args.mode,'--attempt',args.attempt,'--packet-sha256',args.packet_sha256]
    if args.collection_sha256:worker_args.extend(['--collection-sha256',args.collection_sha256])
    post_reserve=5 if args.mode=='tests' else 3
    owned_seconds=min(allocation['owned_seconds'],allocation['whole_seconds']-elapsed()-post_reserve)
    need(owned_seconds>3,'same whole deadline reserve before GO')
    receipt=run_owned(WORKER,worker_args,out,expected_worker_sha256=args.worker_sha256,
        approval_reference=args.approval_reference,max_seconds=owned_seconds,cleanup_reserve_seconds=3,max_output_bytes=65536)
    write(out/'receipt.json',receipt)
    errors=[];result=None;outputs={}
    try:
        need(receipt['accepted'] is True and receipt['returncode']==0 and receipt['cleanup_accepted'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup']==0
             and receipt['popen_handle_closed'] is True and receipt['errors']==receipt['cleanup_errors']==[],'actual owned terminal/cleanup')
        result=read(child/'result.json')
        need(result['accepted'] is True and result['mode']==args.mode and result['attempt']==args.attempt and result['pytest_exit_code']==0
             and result['error'] is None and result['collection_errors']==result['denied']==[],'actual metadata outcome')
        need(result['source_before']==result['source_after']==pins and result['runtime_before']==result['runtime_after']==runtime_pins
             and result['environment_and_sys_restored'] is True and result['actual_scientific_modules_absent'] is True
             and result['packet_sha256']==args.packet_sha256 and result['elapsed_seconds']<allocation['worker_seconds'],
             'source/runtime/clock/fake-module restoration')
        need(result['owned_pycache_prefix_used'] is True,'fresh owned cache prefix used and restored')
        links=result['optional_pytest_symlink_blocks']
        need(result['path_open_restored'] is True and type(links['count']) is int and 0<=links['count']<=1024
             and len(links['records'])==min(links['count'],8),'bound logging restored and bounded optional links denied')
        need(result['deselected_nodeids']==packet['deselect_nodeids'] and result['actual_selected_count']==len(result['nodeids'])>0
             and len(set(result['nodeids']))==len(result['nodeids']),'physical selected population')
        checkpoint_ids=packet['checkpoint38_reference']['expected_nodeids']
        prior_ids=[n for n in packet['expected_nodeids'] if n not in packet['expected_new_nodeids'] and n not in checkpoint_ids]
        need(result['actual_new_nodeids']==packet['expected_new_nodeids']
             and result['actual_checkpoint_nodeids']==checkpoint_ids and result['actual_prior_nodeids']==prior_ids
             and (len(prior_ids),len(result['actual_new_nodeids']),len(checkpoint_ids))==(221,40,38),'exact old221/new40/checkpoint38 population')
        if args.mode=='collect':
            need(result['test_protocol_entries']==result['test_body_entries']==0,'collection has no test bodies')
        else:
            expected=collection['child_result']['nodeids']
            need(result['nodeids']==expected and result['collection_outer_sha256']==args.collection_sha256
                 and result['counts']==dict(tests=len(expected),failures=0,errors=0,skipped=0)
                 and result['test_protocol_entries']==result['test_body_entries']==len(expected),'exact collected cases all executed')
        memory=result['resources']
        need(memory['samples']>0 and memory['observed_peak_rss_bytes']<=128*1024**2
             and memory['observed_minimum_available_ram_bytes']>=1024*1024**2,'cooperative worker resource samples')
        need(not (child/'postwrite_rejection.json').exists(),'no late child verdict')
    except BaseException as error:errors.append(dict(type=type(error).__name__,message=str(error)))
    after={n:sha(safe(ROOT/n)) for n in pins};runtime_after={n:sha(Path(n)) for n in runtime_pins}
    if child.is_dir():
        for path in child.iterdir():
            if path.is_file():
                need(path.stat().st_size<=4*1024**2,'small retained metadata evidence')
                outputs[path.name]=dict(bytes=path.stat().st_size,sha256=sha(path))
    accepted=not errors and after==before and runtime_after==runtime_before and sha(PACKET)==args.packet_sha256 and elapsed()<allocation['whole_seconds']
    status=('ACCEPTED_BATCHC_COLLECTION_ONLY_NOT_TEST_PASS' if args.mode=='collect' else 'ACCEPTED_BATCHC_METADATA_TESTS_NOT_NATIVE') if accepted else 'REJECTED_BATCHC_METADATA_KEEP_ALL'
    final=dict(status=status,mode=args.mode,attempt=args.attempt,errors=errors,receipt=receipt,child_result=result,source_before=before,source_after=after,
        runtime_before=runtime_before,runtime_after=runtime_after,outputs=outputs,packet_sha256=args.packet_sha256,
        collection_outer_sha256=args.collection_sha256,elapsed_seconds=elapsed(),allocation=allocation,
        actual_native_authority=False,actual_gpu_proof=False,automatic_retry=False,
        prelaunch_available_ram_bytes=available,prelaunch_minimum_available_ram_bytes=prelaunch_floor)
    write(out/'final.json',final)
    if elapsed()>=allocation['whole_seconds']:
        write(out/'postwrite_rejection.json',dict(status='REJECTED_OUTER_POSTWRITE_BUDGET',elapsed_seconds=elapsed()));accepted=False
    print(json.dumps(dict(status=status if accepted else 'REJECTED_BATCHC_METADATA_KEEP_ALL',elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':main()
