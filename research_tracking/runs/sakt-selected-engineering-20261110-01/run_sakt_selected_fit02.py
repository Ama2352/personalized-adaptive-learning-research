"""Root-only SAKT normal entry600/580/560/540/train300; source-only chưa chạy."""
import time
START,WALL=time.perf_counter(),time.time()
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
WORKER=PREP/'check_sakt_selected_fit02.py'
MATERIALIZER=PREP/'materialize_sakt_selected_positive02.py'
REQUEST=PREP/'sakt_selected_fit02_request.ROOT.json'
OUT=PREP/'sakt-selected-fit02'
OWNED=PREP/'sakt-selected-fit02-owned'
TEMP=OWNED/'runtime-temp'
RUN_ID='sakt-selected-engineering10x84-20261110-01'
NATIVE=ROOT/'experiments/sakt/results'/RUN_ID
AUTH=ROOT/'experiments/sakt/authorizations'/(RUN_ID+'.json')


def need(ok,message):
    if not ok:
        raise ValueError(message)


def valid_sha(value):
    need(type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value), 'exact lowercase64hex SHA256 required')


def elapsed():
    return max(time.perf_counter()-START,time.time()-WALL)


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(2**20):
            need(elapsed()<600.,'whole outer hash/publication deadline');digest.update(block)
    return digest.hexdigest()


def read(path):
    need(path.is_file() and path.stat().st_size<=2**20,'bounded operational metadata')
    return json.loads(path.read_bytes())


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def main():
    parser=argparse.ArgumentParser()
    for name in ('request-sha256','worker-sha256','outer-sha256','materializer-sha256','approval-reference'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    for digest in (args.request_sha256,args.worker_sha256,args.outer_sha256,args.materializer_sha256):valid_sha(digest)
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import entry,safe,run_owned
    entry()
    need(sha(safe(WORKER))==args.worker_sha256 and sha(Path(__file__))==args.outer_sha256
         and sha(safe(MATERIALIZER))==args.materializer_sha256 and sha(safe(REQUEST))==args.request_sha256
         and args.approval_reference.strip(),'external Root reviewed exact controller and actual request')
    request=read(REQUEST);pins=request['source_pins'];inputs=request['input_pins'];runtime=request['runtime_pins']
    for mapping in (pins,inputs,runtime):
        for digest in mapping.values():valid_sha(digest)
    for key in ('proposal_sha256','dry_sha256','dry_packet_sha256','selected_spec_sha256','authorization_sha256'):valid_sha(request[key])
    need(request['kind']=='ROOT_REVIEWED_ACTUAL_SAKT_SELECTED_ENGINEERING_ONLY'
         and request['specification']['run_id']==RUN_ID and request['authorization_file']==AUTH.relative_to(ROOT).as_posix()
         and sha(safe(AUTH))==request['authorization_sha256'],'actual own SAKT authorization and run')
    need(pins[WORKER.relative_to(ROOT).as_posix()]==args.worker_sha256
         and pins[Path(__file__).resolve().relative_to(ROOT).as_posix()]==args.outer_sha256
         and pins[MATERIALIZER.relative_to(ROOT).as_posix()]==args.materializer_sha256,'request binds same dispatch sources')
    need(not any(safe(path).exists() for path in (OUT,OWNED,NATIVE)),'one exclusive actual fit attempt')
    need(all(sha(safe(ROOT/n))==h for n,h in {**pins,**inputs}.items())
         and all(sha(Path(n))==h for n,h in runtime.items()),'current source/public/runtime pins')
    import psutil
    available=int(psutil.virtual_memory().available);disk=int(psutil.disk_usage(str(ROOT)).free)
    if available<4*2**30 or disk<2**30:
        OUT.mkdir();write(OUT/'outer-final.json',dict(status='NO_GO_SAKT_FIT_RAM_OR_DISK',available_ram_bytes=available,
            disk_free_bytes=disk,required_available_ram_bytes=4*2**30,owned_launch_requested=False,automatic_retry=False))
        raise SystemExit(1)
    environment=dict(os.environ);receipt=result=None;errors=[];outputs={};launched=False
    try:
        os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
            OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',TEMP=str(TEMP),TMP=str(TEMP),TMPDIR=str(TEMP))
        remaining=600.-elapsed()-5.
        need(remaining>30.,'outer600 leaves actual cleanup/publication reserve')
        launched=True
        receipt=run_owned(WORKER,['--request-sha256',args.request_sha256,'--approval-reference',args.approval_reference],OWNED,
            expected_worker_sha256=args.worker_sha256,approval_reference=args.approval_reference,
            max_seconds=min(580.,remaining),cleanup_reserve_seconds=3,max_output_bytes=65536)
        if OWNED.exists():write(OWNED/'receipt.json',receipt)
        need(receipt['accepted'] is True and receipt['returncode']==0 and receipt['cleanup_accepted'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup']==0
             and receipt['popen_handle_closed'] is True and receipt['errors']==receipt['cleanup_errors']==[],'actual owned terminal and Job0 cleanup')
        result=read(OUT/'result.json')
        need(result['status']=='ACTUAL_SAKT_SELECTED_ENGINEERING_PENDING_OUTER' and result['error'] is None
             and result['request_sha256']==args.request_sha256 and result['authorization_sha256']==request['authorization_sha256']
             and result['source_before']==result['source_after']==pins and result['input_before']==result['input_after']==inputs
             and result['runtime_before']==result['runtime_after']==runtime,'actual source/input/auth outcome')
        need(result['observer_restored'] is result['monitor_stopped'] is result['job_query_handle_closed'] is True
             and result['environment_and_sys_restored'] is True and result['denied']==result['monitor_errors']==[]
             and result['cuda_initialized'] is False and result['elapsed_seconds']<560.,'observer/resource/environment closure')
        resources=result['resources']
        need(resources['samples']>0 and resources['maximum_job_processes']>=1
             and resources['peak_worker_rss_bytes']<=2*2**30 and resources['peak_family_rss_bytes']<=2*2**30
             and resources['minimum_available_ram_bytes']>=2*2**30,'exact Job family/worker sampled RAM')
        need(not any((OUT/n).exists() for n in ('failure.log','denials.jsonl','resource-failure.json','postwrite_rejection.json'))
             and not (NATIVE/'failure.json').exists(),'no failure/late-denial override')
        outputs=result['native_outputs'];actual_files={p.relative_to(ROOT).as_posix() for p in NATIVE.rglob('*') if p.is_file()}
        need(0<len(outputs)<=256 and actual_files==set(outputs),'all exact new native files')
        total=0
        for name,record in outputs.items():
            path=safe(ROOT/name)
            need(path.is_relative_to(NATIVE) and path.stat().st_size==record['bytes'] and sha(path)==record['sha256'],'actual unchanged opaque native artifact')
            total+=record['bytes'];need(total<=512*2**20,'native total512MiB')
        complete=read(NATIVE/'COMPLETE.json')
        need(complete['status']=='COMPLETE_SAKT_MAIN_SELECTED_ONLY'
             and sha(NATIVE/'selected-terminal.json')==complete['terminal_sha256']
             and sha(NATIVE/'selected-claim.json')==complete['claim_sha256'] and complete['system_freeze_performed'] is False,'actual native terminal/claim publication')
        need(all(sha(safe(ROOT/n))==h for n,h in {**pins,**inputs}.items()) and sha(REQUEST)==args.request_sha256
             and sha(AUTH)==request['authorization_sha256'] and all(sha(Path(n))==h for n,h in runtime.items()),'post native source/input/request/runtime bytes')
    except BaseException as caught:
        errors.append(dict(type=type(caught).__name__,message=str(caught)))
    finally:
        os.environ.clear();os.environ.update(environment)
    restored=dict(os.environ)==environment
    accepted=not errors and restored and elapsed()<600.
    if not OUT.exists():OUT.mkdir()
    final=dict(status='ACCEPTED_ACTUAL_SAKT_SELECTED_ONLY_ENGINEERING' if accepted else 'REJECTED_SAKT_KEEP_PARTIAL',
        errors=errors,owned_receipt=receipt,worker_result=result,request_sha256=args.request_sha256,
        authorization_sha256=request['authorization_sha256'],owned_launch_requested=launched,
        worker_GO_released=None if receipt is None else receipt.get('GO_released'),elapsed_seconds=elapsed(),
        prelaunch_available_ram_bytes=available,prelaunch_disk_free_bytes=disk,whole_cap_seconds=600,
        owned_cap_seconds=580,worker_cap_seconds=560,entry_cap_seconds=540,training_cap_seconds=300,
        cleanup_reserve_seconds=3,environment_restored=restored,automatic_retry=False,
        full_main_matrix_completed=False,refit_or_calibration_performed=False,gpu_ready=False,public_resume_supported=False)
    write(OUT/'outer-final.json',final)
    if elapsed()>=600.:
        write(OUT/'outer-postwrite-rejection.json',dict(reason='same outer deadline after publication'));accepted=False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_SAKT_KEEP_PARTIAL',seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    main()
