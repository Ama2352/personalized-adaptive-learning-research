"""SOURCE-ONLY Root launcher: child360/owned350/worker340/lineage540 CPU.

No request/auth creation or native execution on import. Root review and exact
materialized inputs are prerequisites; only the reviewed intentional resume.
"""
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
WORKER=P/'check_graph29_a0_resume01.py'
HELPER=R/'scripts/research/windows_owned_worker.py'
HELPER_SHA='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'


def need(ok,why):
    if not ok:raise ValueError(why)


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main(args):
    need(Path(sys.prefix).resolve()==R/'.venv','repository .venv')
    need(sha(WORKER)==args.worker_sha256 and sha(Path(__file__))==args.outer_sha256
         and sha(HELPER)==HELPER_SHA,'Root reviewed exact source/helper pins')
    module_spec=importlib.util.spec_from_file_location('tiny_a0_worker_definitions',WORKER)
    worker=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(worker)
    request_file=worker.path(args.request)
    need(request_file.parent==P and sha(request_file)==args.request_sha256,'exact reviewed request')
    request=worker.read(request_file)
    need(request['kind']=='ROOT_REVIEWED_ACTUAL_MAIN_GRAPH29_RESUME_A0_ONLY'
         and request['approval_reference']==args.approval_reference,'actual tiny-only operation reference')
    sources=request['source_pins']
    need(sources.get(WORKER.relative_to(R).as_posix())==args.worker_sha256
         and sources.get(Path(__file__).resolve().relative_to(R).as_posix())==args.outer_sha256
         and sources.get(HELPER.relative_to(R).as_posix())==HELPER_SHA,'request binds actual controllers')
    before={name:sha(worker.path(name)) for name in sources}
    need(before==sources and not worker.OUT.exists() and not worker.OWNED.exists(),'source identity/fresh attempt')
    config_file=worker.path(request['native_config_file']);auth_file=worker.path(request['authorization_file'])
    need(sha(config_file)==request['native_config_sha256'] and sha(auth_file)==request['authorization_sha256'],
         'new config/auth bytes')
    config=worker.read(config_file);native_output=Path(config['output_dir'])
    need(native_output.parent==R/'experiments/akt/results' and not native_output.exists(),'fresh actual selected-only output')
    expected_git=dict(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul',GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',GIT_CONFIG_KEY_1='safe.directory',
        GIT_CONFIG_VALUE_1=(R/'artifacts/akt/dependencies/upstream').as_posix(),
        GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='true',GIT_OPTIONAL_LOCKS='0',
        GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
    need({k:v for k,v in os.environ.items() if k.startswith(('GIT_','GH_'))}==expected_git,'exact supplied process Git, no stripping')
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import entry,run_owned
    entry()
    import psutil
    need(psutil.virtual_memory().available>=4*1024**3 and psutil.disk_usage(str(R)).free>=2*1024**3,
         'fresh freeRAM4GiB/disk2GiB before owned fit')
    sys.path.insert(0,str(R/'src'))
    spec,evidence=worker.construct(request)
    need('torch' not in sys.modules,'outer typed construction is metadata only')
    parent_request=request['resume_request'];parent_reference=request['parent_reference']
    parent=worker.path(parent_request['parent_directory'])
    need(parent==R/'experiments/akt/results/main-a0-graph29-pause5-engineering10x84-20261110-02'
         and parent_request['terminal_sha256']=='68a741ab3b835e60ee85c0da4afd28d1cac19ce4bd4ef8e8e8eff00e00bdc5f3',
         'only actual sealed parent02 accepted by reviewed child')
    for ref in parent_reference['references'].values():
        need(sha(worker.path(ref['path']))==ref['sha256'],'actual parent proof before child')
    retained=0
    for name,row in parent_reference['outputs'].items():
        file=worker.path((parent/name).relative_to(R).as_posix())
        need(sha(file)==row['sha256'] and file.stat().st_size==row['bytes'],'parent bytes before child')
        retained+=row['bytes']
    need(retained==parent_reference['retained_bytes'] and retained<spec.max_output_bytes
         and psutil.virtual_memory().available>=4*1024**3,'retained parent budget and fresh4GiB after preparation')
    environment=dict(os.environ);error=None;receipt=None;result=None
    try:
        os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
            OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
            TEMP=str(worker.OWNED/'runtime-temp'),TMP=str(worker.OWNED/'runtime-temp'),TMPDIR=str(worker.OWNED/'runtime-temp'))
        remaining=360-(time.perf_counter()-START)-10
        need(remaining>30,'whole360 includes finalization10')
        receipt=run_owned(WORKER,['--request',args.request,'--request-sha256',args.request_sha256,
            '--approval-reference',args.approval_reference],worker.OWNED,expected_worker_sha256=args.worker_sha256,
            approval_reference=args.approval_reference,max_seconds=min(350.,remaining),cleanup_reserve_seconds=3,
            max_output_bytes=128*1024)
        if worker.OWNED.is_dir():
            with (worker.OWNED/'receipt.json').open('x',encoding='utf-8') as stream:
                json.dump(receipt,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
        need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup']==0
             and receipt['popen_handle_closed'] is True and receipt['errors']==[] and receipt['returncode']==0,
             'actual fit worker and owned cleanup')
        result=worker.read(worker.OUT/'result.json')
        need(result['status']=='ACTUAL_GRAPH29_RESUME_PARITY_PENDING_OUTER' and result['error'] is None
             and result['source_before']==result['source_after']==before
             and result['request_sha256']==args.request_sha256 and result['observer_restored'] is True
             and result['denied']==result['monitor_errors']==[] and result['monitor_stopped'] is True
             and result['elapsed_seconds']<340 and result['cuda_initialized'] is False,'actual terminal invariants')
        need(not any((worker.OUT/name).exists() for name in ('failure.log','resource-failure.json','postwrite-rejection.json'))
             and not (native_output/'failure.json').exists(),'no failure/late override')
        need(result['resources']['peak_rss_bytes']<=1024**3
             and result['resources']['min_available_ram_bytes']>=2*1024**3,'observed worker resource bounds')
        # Actual stage journals/claim/checkpoint assertions were checked by the
        # worker. Recheck its opaque output inventory here without loading NN.
        need(result['native_outputs'] and all(Path(name).parts[:3]==('experiments','akt','results')
             and worker.path(name).is_relative_to(native_output) for name in result['native_outputs']),
             'exact selected-only output subtree')
        actual_files={file.relative_to(R).as_posix() for file in native_output.rglob('*') if file.is_file()}
        need(actual_files==set(result['native_outputs']),'no missing/extra native output files')
        total=0
        for name,row in result['native_outputs'].items():
            file=worker.path(name);total+=file.stat().st_size
            need(file.stat().st_size==row['bytes'] and sha(file)==row['sha256'],'native bytes unchanged')
            need(time.perf_counter()-START<360,'outer hash/finalization within360')
        for name,row in parent_reference['outputs'].items():
            file=worker.path((parent/name).relative_to(R).as_posix())
            need(sha(file)==row['sha256'] and file.stat().st_size==row['bytes'],'parent unchanged after child')
        need(total+retained<=1536*1024**2,'parent plus child output1536MiB')
        need(not (worker.path(parent_request['terminal_file']).parent/'postwrite_rejection.json').exists(),
             'no parent late-rejection override')
        parity=worker.read(worker.OUT/'actual-completion-check.json')
        need(parity['epochs']==7 and parity['selected_epoch']==4 and parity['exact_control_all_seven_epochs'] is True
             and parity['parent_prefix_verbatim'] is True and parity['raw84_exports_byte_exact'] is True
             and parity['restored_latest_epoch']==5 and parity['inherited_best_epoch']==4,
             'actual complete normal-entry parity receipt required')
        need(all(sha(worker.path(name))==pin for name,pin in before.items())
             and sha(request_file)==args.request_sha256 and sha(config_file)==request['native_config_sha256']
             and sha(auth_file)==request['authorization_sha256'],'all source/request/config/auth posthashes')
    except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc))
    finally:os.environ.clear();os.environ.update(environment)
    accepted=error is None and time.perf_counter()-START<360
    if not worker.OUT.exists():worker.OUT.mkdir()
    final=dict(status='ACCEPTED_ACTUAL_GRAPH29_INTENTIONAL_RESUME_PARITY_ONLY' if accepted else 'REJECTED_KEEP_PARTIAL_NO_RESUME',
        error=error,request_sha256=args.request_sha256,owned_receipt=receipt,worker_result=result,
        elapsed_seconds=time.perf_counter()-START,main_cap_seconds=540,training_cap_seconds=300,
        worker_cap_seconds=340,owned_cap_seconds=350,outer_cap_seconds=360,cleanup_seconds=3,
        environment_restored=dict(os.environ)==environment,research_matrix_completed=False,
        parent_terminal_sha256=parent_request['terminal_sha256'],planned_parent_wall_charge_seconds=180,
        lineage_charged_wall_seconds=180+time.perf_counter()-START,lineage_wall_cap_seconds=540,
        intentional_complete_epoch_resume_only=True,unexpected_crash_recovery_supported=False,
        cuda_readiness=False,automatic_retry=False)
    with (worker.OUT/'outer-final.json').open('x',encoding='utf-8') as stream:
        json.dump(final,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    if time.perf_counter()-START>=360:
        with (worker.OUT/'outer-postwrite-rejection.json').open('x',encoding='utf-8') as stream:
            json.dump(dict(status='REJECTED_OUTER_POSTWRITE_BUDGET'),stream)
        accepted=False
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--request',required=True);parser.add_argument('--request-sha256',required=True)
    parser.add_argument('--worker-sha256',required=True);parser.add_argument('--outer-sha256',required=True)
    parser.add_argument('--approval-reference',required=True)
    main(parser.parse_args())
