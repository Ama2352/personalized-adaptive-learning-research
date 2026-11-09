"""ROOT-only future guard admission60s. Requires real reviewed request/auth/Gate."""
import time
START,WALL=time.perf_counter(),time.time()
from pathlib import Path
import argparse
import json
import math
import os
import sys

R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
WORKER=P/'check_main_selected_guard01.py';OUT=P/'main-selected-actual-guard01';OWNED=P/'main-selected-actual-guard01-owned'
HELPER=R/'scripts/research/windows_owned_worker.py'
HELPER_SHA='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
FROZEN={
 'src/knowledge_tracing/akt/research_main_execution.py':'902018762fde6433a9bd9e33ce770df0057f6b0623327b8ff6b798e1faf4d881',
 'src/knowledge_tracing/akt/research_selected_runner.py':'fcaa0c1850a0de391e26d4b3eb915fc91b3848f1e8d834898fa7fb788e868e20',
 'tests/akt/test_research_main_execution.py':'9c102b3645528c5a2b7a4ca7830a68429f824ec0c3199b4d3ba587f88efcc0ce',
 'tests/akt/test_research_selected_runner.py':'05f85bd487e93fca925f568fdb326852dc9bcc07ef0d32f994e4051dd03fdeaa'}
CAP=60.


def main(args):
    # This import loads only the reviewed stdlib definitions. It does not call
    # worker_gate, domain modules, native preflight, corpus reader or main().
    import check_main_selected_guard01 as worker
    need,sha,read,physical=worker.need,worker.sha,worker.read,worker.physical
    elapsed=lambda:max(time.perf_counter()-START,time.time()-WALL)
    path,value=worker.request(args.request,args.request_sha256)
    need(args.approval_reference==value['approval_reference'],'exact external ROOT reference')
    need(not OUT.exists() and not OWNED.exists(),'exclusive one guard-only attempt')
    need(sha(HELPER)==HELPER_SHA and value['source_pins'].get(HELPER.relative_to(R).as_posix())==HELPER_SHA,'owned helper actual bytes')
    for name,pin in FROZEN.items():need(value['source_pins'].get(name)==sha(R/name)==pin,'four frozen production/test files')
    for file in (WORKER,Path(__file__).resolve()):need(value['source_pins'].get(file.relative_to(R).as_posix())==sha(file),'reviewed controller/worker bytes')
    before={name:sha(physical(name)) for name in value['source_pins']};need(before==value['source_pins'],'all prospective source pins')
    config_path=physical(value['native_config_file']);config=read(config_path)
    need(sha(config_path)==value['native_config_sha256'] and config['source_root'].replace('\\','/')==(R/'artifacts/akt/dependencies/upstream').as_posix(),'actual config/root')
    expected_git=dict(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul',GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',GIT_CONFIG_KEY_1='safe.directory',
        GIT_CONFIG_VALUE_1=(R/'artifacts/akt/dependencies/upstream').as_posix(),GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='true',
        GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
    need({k:v for k,v in os.environ.items() if k.startswith(('GIT_','GH_'))}==expected_git,'ROOT must supply reviewed process-only Git profile')
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import run_owned,entry,safe
    entry();safe(WORKER);safe(OUT);safe(OWNED)
    import psutil
    need(int(psutil.virtual_memory().available)>=2*1024**3,'pre-dispatch free2GiB')
    receipt=result=None;errors=[];after={}
    def write(name,data):
        raw=(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();need(len(raw)<=1024**2,'small outer receipt')
        with (OUT/name).open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    try:
        allowance=min(58.,CAP-elapsed()-2.);need(allowance>10.,'whole60 includescleanup3/final2')
        receipt=run_owned(WORKER,['--request',args.request,'--request-sha256',args.request_sha256,'--approval-reference',args.approval_reference],
            OWNED,expected_worker_sha256=before[WORKER.relative_to(R).as_posix()],approval_reference=args.approval_reference,
            max_seconds=allowance,cleanup_reserve_seconds=3,max_output_bytes=65536)
        with (OWNED/'receipt.json').open('x',encoding='utf-8') as stream:
            json.dump(receipt,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        need(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['actual_worker_in_job_before_GO']
            and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed'] and receipt['cleanup_errors']==[]
            and receipt['errors']==[] and receipt['returncode']==0,'owned actual worker/cleanup verdict')
        for name,pin in receipt['output_sha256'].items():need(name in ('stdout.log','stderr.log') and sha(OWNED/name)==pin,'raw logs')
        result=read(OUT/'result.json');admission=read(OUT/'actual-admission.json')
        need(result['status']=='ACCEPTED_ACTUAL_MAIN_GUARD_ONLY_PENDING_OUTER' and result['error'] is None
            and result['actual_guard_created'] is True and result['actual_selected_fit'] is False,'actual guard-only terminal')
        need(result['source_before']==result['source_after']==before and result['request_sha256']==args.request_sha256
            and result['inputs_before']==result['inputs_after'] and result['public_before']==result['public_after']
            and result['forbidden']==result['monitor_errors']==[] and result['monitor_stopped']
            and result['selected_environment_restored'] and result['git_environment_unchanged'],'actual source/input/resource invariants')
        need(len(result['git_calls'])==20 and len(result['metadata']['commands'])<=3 and result['metadata']['fixture_replaced'] is False,'genuine20 Git/real Windows bootstrap')
        need(all(type(result[k]) is int and result[k]==0 for k in ('model_calls','optimizer_calls','teacher_calls'))
            and admission['run_main_selected_candidate_called'] is False,'zero-work guard phase')
        need(admission['kind']=='ACTUAL_MAIN_A0_GUARD_ADMISSION_ONLY'
            and admission['authorization_sha256']==value['authorization_sha256']
            and admission['identity']['native_evidence']['gate']['status']=='PASS','actual auth/Gate binding')
        need(result['resources']['peak_rss_bytes']<=1024**3 and result['resources']['min_available_ram_bytes']>=2*1024**3
            and result['elapsed_seconds']<50 and not any((OUT/n).exists() for n in ('resource-failure.json','postwrite-rejection.json')),'actual whole resource bounds')
        need(not Path(config['output_dir']).exists(),'no configured main-fit output created')
    except BaseException as failure:errors.append(dict(type=type(failure).__name__,message=str(failure)))
    try:
        after={name:sha(physical(name)) for name in value['source_pins']}
        need(after==before and sha(path)==args.request_sha256 and sha(config_path)==value['native_config_sha256']
            and sha(physical(value['authorization_file']))==value['authorization_sha256'],'outer final source/request/config/auth bytes')
    except BaseException as failure:errors.append(dict(type=type(failure).__name__,message=str(failure)))
    if not OUT.exists():OUT.mkdir()
    outputs={}
    try:
        need(elapsed()<CAP,'whole60 before final output hashes')
        outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file()}
    except BaseException as failure:errors.append(dict(type=type(failure).__name__,message=str(failure)))
    accepted=not errors and math.isfinite(elapsed()) and 0<=elapsed()<CAP
    final=dict(status='ACCEPTED_ACTUAL_MAIN_GUARD_ONLY' if accepted else 'REJECTED_GUARD_ONLY_KEEP_PARTIAL',errors=errors,
        source_before=before,source_after=after,request_sha256=args.request_sha256,output_sha256=outputs,
        owned_receipt_sha256=sha(OWNED/'receipt.json') if (OWNED/'receipt.json').exists() else None,
        elapsed_before_receipt_seconds=elapsed(),cap_seconds=CAP,cleanup_reserve_seconds=3,automatic_retry=False,
        actual_guard_admitted=True if accepted else None,main_selected_fit_verified=False,
        scope_vi='Actual canonicalpublic-data/main guard admission only. NN/optimizer/teacher paths denied. No lifecycle/checkpoint/export/fullfit proof.')
    write('outer-final.json',final)
    if elapsed()>=CAP:write('outer-postwrite-rejection.json',dict(elapsed_seconds=elapsed()));accepted=False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_GUARD_ONLY_KEEP_PARTIAL',elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--request',required=True)
    parser.add_argument('--request-sha256',required=True);parser.add_argument('--approval-reference',required=True)
    main(parser.parse_args())
