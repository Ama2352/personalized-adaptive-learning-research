"""ROOT-owned source-only launcher; one fresh fixture operation, no auto-retry."""
import time
START=time.perf_counter()
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import sys

R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
WORKER=P/'collect_main_engineering10x84_01.py'
HELPER=R/'scripts/research/windows_owned_worker.py'
HELPER_SHA='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'


def need(ok,why):
    if not ok:raise ValueError(why)


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main(args):
    need(Path(sys.prefix).resolve()==R/'.venv' and sha(HELPER)==HELPER_SHA,'reviewed repository environment/helper')
    need(sha(WORKER)==args.worker_sha256 and sha(Path(__file__))==args.outer_sha256,'ROOT reviewed controller pins')
    spec=importlib.util.spec_from_file_location('reviewed_engineering10x84_metadata',WORKER)
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    relative=Path(args.request)
    need(not relative.is_absolute() and '..' not in relative.parts and '\\' not in args.request,'relative POSIX request')
    path=R/relative
    need(path.parent==P and path.is_file() and path.stat().st_size<=128*1024 and sha(path)==args.request_sha256,'exact request')
    request=worker.validate_contract(json.loads(path.read_bytes()))
    need(request['approval_reference']==args.approval_reference,'ROOT operation reference')
    sources=request['collection_sources']|request['extra_sources']
    need(sources[WORKER.relative_to(R).as_posix()]==args.worker_sha256
         and sources[Path(__file__).resolve().relative_to(R).as_posix()]==args.outer_sha256,
         'request binds exact controllers')
    need(all(sha(R/name)==digest for name,digest in sources.items()),'all source bytes before dispatch')
    need(not worker.OUT.exists() and not worker.OWNED.exists() and not worker.CORPUS.exists(),'exclusive attempt and corpus')
    git_profile=dict(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul',GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',GIT_CONFIG_KEY_1='safe.directory',
        GIT_CONFIG_VALUE_1=(R/'artifacts/akt/dependencies/upstream').as_posix(),
        GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='true',GIT_OPTIONAL_LOCKS='0',
        GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
    need({k:v for k,v in os.environ.items() if k.startswith(('GIT_','GH_'))}==git_profile,
         'exact supplied process-only Git profile, no stripping')
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import entry,run_owned
    entry()
    import psutil
    need(psutil.virtual_memory().available>=2*1024**3,'fresh2GiB before collection')
    env=dict(os.environ);receipt=None;result=None;error=None
    try:
        os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
            OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        left=70-(time.perf_counter()-START)-5
        need(left>10,'whole70 includescleanup3/final5')
        receipt=run_owned(WORKER,['--request',args.request,'--request-sha256',args.request_sha256,
            '--approval-reference',args.approval_reference],worker.OWNED,expected_worker_sha256=args.worker_sha256,
            approval_reference=args.approval_reference,max_seconds=min(65.,left),cleanup_reserve_seconds=3,max_output_bytes=65536)
        with (worker.OWNED/'receipt.json').open('x',encoding='utf-8') as stream:
            json.dump(receipt,stream,ensure_ascii=False,indent=2,allow_nan=False)
        need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup']==0 and receipt['actual_worker_in_job_before_GO'] is True
             and receipt['popen_handle_closed'] is True and receipt['returncode']==0 and receipt['errors']==[],
             'actual worker/cleanup acceptance')
        need(not any((worker.OUT/name).exists() for name in ('failure.json','failure.log','postwrite-rejection.json')),
             'no scientific/late/resource failure')
        result=json.loads((worker.OUT/'worker_result.json').read_bytes())
        need(result['status']=='GENUINE_ENGINEERING_CORPUS_PENDING_OUTER'
             and result['request_sha256']==args.request_sha256 and result['source_before']==result['source_after']==sources
             and result['interact_attempts']==result['interact_returns']==result['reserved_teacher_attempts']==840
             and result['role_attempts']==dict(train=672,selection=84,calibration=84)
             and result['final_events']==result['model_calls']==result['optimizer_calls']==0
             and result['denied']==[] and result['elapsed_seconds']<60,'complete genuine engineering scope')
        need(all(sha(R/name)==digest for name,digest in sources.items()) and sha(path)==args.request_sha256,'postsource/request hashes')
        files=result['publication']['files']
        need(len(files)==17 and {name for name,_,_ in files}==worker.PUBLIC10|
             {'oracle/train.json','oracle/train.collection.json','oracle/selection.json','oracle/selection.collection.json',
              'oracle/calibration.json','oracle/calibration.collection.json','oracle/publication-inventory.json'},
             'exact existing-schema17 outputs, no final events')
        for name,digest,size in files:
            target=worker.CORPUS/name
            need(target.is_file() and target.stat().st_size==size and sha(target)==digest,'all published bytes exact')
        need((worker.CORPUS/'DONE.json').is_file() and not (worker.CORPUS/'failure.json').exists(),'complete publication')
        need(all(len(result['coverage_per_learner'][role])==worker.COUNTS[role]
                 and set(result['coverage_per_learner'][role].values())=={84} for role in worker.ROLES),'all10reference complete')
    except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc))
    finally:os.environ.clear();os.environ.update(env)
    accepted=error is None and time.perf_counter()-START<70
    if not worker.OUT.exists():worker.OUT.mkdir()
    final=dict(status='ACCEPTED_GENUINE_ENGINEERING10X84_ONLY' if accepted else 'REJECTED_KEEP_PARTIAL_NO_RETRY',
        error=error,request_sha256=args.request_sha256,owned_receipt=receipt,worker_result=result,
        elapsed_seconds=time.perf_counter()-START,outer_cap_seconds=70,worker_cap_seconds=60,
        canonical60_modified=False,research_allocation_changed=False,research_fit=False,automatic_retry=False,
        environment_restored=dict(os.environ)==env)
    with (worker.OUT/'outer-final.json').open('x',encoding='utf-8') as stream:
        json.dump(final,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    if time.perf_counter()-START>=70:
        with (worker.OUT/'postwrite-rejection.json').open('x',encoding='utf-8') as stream:
            json.dump(dict(status='REJECTED_OUTER_POSTWRITE_BUDGET'),stream)
        accepted=False
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--request',required=True);parser.add_argument('--request-sha256',required=True)
    parser.add_argument('--approval-reference',required=True)
    parser.add_argument('--worker-sha256',required=True);parser.add_argument('--outer-sha256',required=True)
    main(parser.parse_args())
