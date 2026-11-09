"""SOURCE-ONLY prepared worker. ROOT request/auth/fresh Gate required to run."""
import time
START,WALL=time.perf_counter(),time.time()
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import threading

R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
OUT=P/'main-selected-actual-guard01';OWNED=P/'main-selected-actual-guard01-owned'
BENCH=R/'research_tracking/runs/cgakt-context-api-cost-benchmark-20261109-01/attempt02__config.json'
BENCH_SHA='c5cc433a4368e9e13fea354b608172bdfc06684be7de8bb4f59f3d35d8265ba3'
PUBLIC_ROOT=R/'artifacts/simulator/corpora/grade10-development-lifecycle01-20261108'
WORKER_CAP=50.
HASH_CAP_SECONDS=60.  # Parent metadata preparation uses its whole60 allocation.
BLOCKED={'torch','pandas','sklearn','scipy','joblib','pyBKT','modal','boto3'}
DENY_DOMAIN={'knowledge_tracing.paper2_reference','knowledge_tracing.simulator_collection',
 'knowledge_tracing.simulator_research_collection','knowledge_tracing.akt.research_selected_runner',
 'knowledge_tracing.akt.research_runner','knowledge_tracing.akt.model','knowledge_tracing.akt.research_graph_model'}


def need(ok,message):
    if not ok:raise ValueError(message)


def elapsed():return max(time.perf_counter()-START,time.time()-WALL)


def physical(relative):
    need(type(relative) is str and '\\' not in relative and ':' not in relative,'relative POSIX input required')
    from pathlib import PurePosixPath
    parts=PurePosixPath(relative)
    need(parts.parts and not parts.is_absolute() and '..' not in parts.parts and parts.as_posix()==relative,'safe input path')
    cursor=R
    for part in parts.parts:
        cursor/=part;need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'physical input path')
    need(cursor.resolve()==cursor.absolute(),'input alias rejected');return cursor


def sha(path):
    need(path.is_file() and not path.is_symlink(),'regular pinned file')
    digest=hashlib.sha256();total=0
    with path.open('rb') as stream:
        while block:=stream.read(65536):
            total+=len(block)
            need(total<=32*1024**2 and elapsed()<HASH_CAP_SECONDS,'bounded input/source bytes and shared preparation clock')
            digest.update(block)
    return digest.hexdigest()


def read(path,cap=1024**2):
    with path.open('rb') as stream:raw=stream.read(cap+1)
    need(len(raw)<=cap,'bounded JSON input')
    def unique(rows):
        result={}
        for key,value in rows:need(key not in result,'duplicate JSON key');result[key]=value
        return result
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
    json.dumps(value,allow_nan=False);return value


def write(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();need(len(raw)<=1024**2,'small worker receipt')
    with (OUT/name).open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())


def request(relative,pin):
    path=physical(relative);need(path.parent==P and path.suffix=='.json' and sha(path)==pin,'actual reviewed request SHA')
    value=read(path)
    need(set(value)=={'schema_version','kind','source_pins','native_config_file','native_config_sha256','main_parameters',
        'runtime_evidence','authorization_file','authorization_sha256','approval_reference'},'closed guard-only request')
    need(type(value['schema_version']) is int and value['schema_version']==1
        and value['kind']=='ROOT_REVIEWED_ACTUAL_MAIN_GUARD_ONLY','guard-only operation')
    for item in (pin,value['native_config_sha256'],value['authorization_sha256']):
        need(type(item) is str and len(item)==64 and all(c in '0123456789abcdef' for c in item),'exact lowercase SHA256')
    need(type(value['source_pins']) is dict and 1<=len(value['source_pins'])<=256 and type(value['approval_reference']) is str
        and value['approval_reference'].strip(),'external source/review bindings')
    source_prefixes=('src/knowledge_tracing/','tests/akt/','tests/shared_kt/','scripts/akt/','scripts/research/',
        'docs/thesis_recovery/','paper1/','paper2/')
    local_prefix=P.relative_to(R).as_posix()+'/'
    for name,digest in value['source_pins'].items():
        physical(name)
        need(name.startswith(source_prefixes) or name.startswith(local_prefix)
            or name.startswith('requirements-akt') and '/' not in name,'source scope excludes protected/private files')
        need(type(digest) is str and len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'source SHA256 format')
    return path,value


def construct(value):
    from knowledge_tracing.akt.config import load_config
    from knowledge_tracing.akt.research_execution import SimulatorResearchSpec,ResearchResourceBudget,ResearchRuntimeEvidence
    from knowledge_tracing.akt.research_main_stage import MainSelectedStageSpec
    from knowledge_tracing.research_admission import MainSelectionContext
    from knowledge_tracing.akt.research_main_execution import MainSelectedExecutionSpec,MainGitProfile,MainGraphInput
    from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits
    config_path=physical(value['native_config_file'])
    need(config_path.is_relative_to(R/'experiments/akt/configs') and sha(config_path)==value['native_config_sha256'],'actual config bytes')
    config=load_config(config_path);p=dict(value['main_parameters']);research=dict(p.pop('research'))
    need(set(research)=={'corpus_id','expected_corpus_sha256','expected_protocol_sha256','budget'},'research constructor fields')
    research['native_config']=config;research['budget']=ResearchResourceBudget(**research['budget'])
    stage=dict(p.pop('stage'));stage['context']=MainSelectionContext(**stage['context'])
    git=dict(p.pop('git_profile'));git['upstream_files_sha256']=tuple(tuple(row) for row in git['upstream_files_sha256'])
    spec=MainSelectedExecutionSpec(research=SimulatorResearchSpec(**research),stage=MainSelectedStageSpec(**stage),
        read_limits=CorpusReadLimits(**p.pop('read_limits')),graph_input=MainGraphInput(**p.pop('graph_input')),
        git_profile=MainGitProfile(**git),**p)
    budget=spec.research.budget
    need(spec.stage.candidate_id=='A0' and spec.research.corpus_id==PUBLIC_ROOT.name,'canonical independent A0 admission only')
    need((budget.train_learners,budget.selection_learners,budget.calibration_learners)==(48,6,6)
        and (budget.train_targets,budget.selection_targets,budget.calibration_targets)==(10080,1260,1260)
        and budget.max_events_per_learner==210,'full canonical population, no slice')
    need(budget.max_optimizer_steps==budget.max_optimized_targets==1 and budget.max_training_seconds==1.
        and budget.max_wall_seconds<=45 and budget.max_rss_bytes<=1024**3 and budget.min_available_ram_bytes>=2*1024**3,
        'guard-only resource allocation cannot complete an optimization batch')
    need(not config.output_dir.exists(),'guard-only configured run output must remain absent')
    return spec,ResearchRuntimeEvidence(**value['runtime_evidence'])


def main(relative,pin,approval):
    global HASH_CAP_SECONDS
    HASH_CAP_SECONDS=WORKER_CAP
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import worker_gate
    ownership=worker_gate()
    req_path,value=request(relative,pin);need(value['approval_reference']==approval,'same ROOT operation reference')
    need(not OUT.exists(),'exclusive actual admission attempt');OUT.mkdir()
    source_before={name:sha(physical(name)) for name in value['source_pins']}
    need(source_before==value['source_pins'] and sha(BENCH)==BENCH_SHA,'current source and committed corpus proof')
    public=read(BENCH)['public_inputs_sha256'];need(len(public)==10,'canonical public10 reference')
    actual_inputs={value['native_config_file']:value['native_config_sha256'],value['authorization_file']:value['authorization_sha256']}
    for name,digest in actual_inputs.items():need(sha(physical(name))==digest,'actual config/auth input SHA')
    runtime_temp=OWNED/'runtime-temp';runtime_temp.mkdir()
    envkeys=('TEMP','TMP','TMPDIR','PYTHONDONTWRITEBYTECODE','CUDA_VISIBLE_DEVICES','NVIDIA_VISIBLE_DEVICES')
    env_before={key:os.environ.get(key) for key in envkeys};git_before={k:v for k,v in os.environ.items() if k.startswith(('GIT_','GH_'))}
    os.environ.update(TEMP=str(runtime_temp),TMP=str(runtime_temp),TMPDIR=str(runtime_temp),PYTHONDONTWRITEBYTECODE='1',
        CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
    phase=['windows_metadata'];forbidden=[];metadata_calls=[];git_calls=[]
    system_cmd=Path(os.environ['SystemRoot'])/'System32/cmd.exe';upstream=R/'artifacts/akt/dependencies/upstream'
    tails=[('rev-parse','HEAD'),('status','--porcelain','--untracked-files=all'),('remote','get-url','origin')]
    for name in ('akt.py','README.md','LICENSE'):tails.extend([('hash-object',name),('rev-parse','HEAD:'+name)])
    tails.append(('rev-parse','HEAD^{tree}'))
    git_order=[subprocess.list2cmdline(['git','-C',str(upstream),*tail]) for tail in tails]
    def audit(event,args):
        if event=='import':
            name=str(args[0])
            if name.split('.')[0] in BLOCKED or name in DENY_DOMAIN:
                forbidden.append('import:'+name);raise RuntimeError('actual guard-only domain boundary')
        if event=='subprocess.Popen':
            if phase[0]=='windows_metadata':
                fixed=os.path.normcase(os.path.abspath(str(system_cmd)))
                allowed={fixed.casefold()+' /c "ver"','"'+fixed.casefold()+'" /c "ver"'}
                ok=(len(metadata_calls)<3 and type(args[0]) is str and type(args[1]) is str
                    and os.path.normcase(os.path.abspath(args[0]))==fixed and args[1].strip().casefold() in allowed)
                if ok:metadata_calls.append(dict(executable=args[0],command=args[1]));return
            elif phase[0]=='actual_admission' and len(git_calls)<20 and args[0] in (None,'git') and args[1]==git_order[len(git_calls)%10]:
                git_calls.append(dict(round=len(git_calls)//10+1,command=args[1]));return
            forbidden.append(event);raise RuntimeError('undeclared provenance/metadata child')
        if event=='os.system' or event.startswith(('os.spawn','os.posix_spawn')) or event.startswith('socket.') and not (phase[0]=='windows_metadata' and event=='socket.gethostname'):
            forbidden.append(event);raise RuntimeError('network/undeclared process forbidden')
        if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
            path=Path(os.path.abspath(os.fsdecode(args[0])))
            if path.is_relative_to(R/'artifacts/simulator/corpora') and path not in {PUBLIC_ROOT/name for name in public}:
                forbidden.append('nonpublic_corpus');raise RuntimeError('exact public10 only')
            for name in ('dataset','artifacts/bkt_baseline','venv','.wsl'):
                if path==R/name or path.is_relative_to(R/name):forbidden.append('protected');raise RuntimeError('protected data')
            if path.is_relative_to(R/'experiments') and path not in {physical(name) for name in actual_inputs}:
                forbidden.append('unowned_experiment');raise RuntimeError('only reviewed config/auth bytes')
            if path.suffix.lower() in ('.pt','.pth','.ckpt','.safetensors','.parquet'):
                forbidden.append('model_binary');raise RuntimeError('guard-only model binary forbidden')
    sys.addaudithook(audit)
    error=None;metadata=None;guard=None;after={};input_after={};public_before={};public_after={};monitor=None
    stop=threading.Event();monitor_errors=[];lock=threading.Lock();resources=dict(samples=0,peak_rss_bytes=0,min_available_ram_bytes=None)
    timer=threading.Timer(52.,lambda:os._exit(124));timer.daemon=True;timer.start()
    def deadline():need(math.isfinite(elapsed()) and 0<=elapsed()<WORKER_CAP,'guard-only global worker cap')
    try:
        deadline();need(sys.platform=='win32' and not any(n.split('.')[0] in BLOCKED|{'numpy'} or n=='knowledge_tracing' for n in sys.modules),'cold Windows owner')
        try:
            native=platform.uname();processor=platform.processor()
            metadata=dict(system=native.system,release=native.release,version=native.version,machine=native.machine,
                processor_cache_warmed=type(processor) is str,commands=metadata_calls,fixture_replaced=False)
            need(native.system=='Windows','actual Windows metadata')
        finally:phase[0]='closed_metadata'
        write('windows-metadata.json',metadata)
        import psutil
        process=psutil.Process()
        def memory():
            with lock:
                deadline();info=process.memory_info();peak=max(int(info.rss),int(info.peak_wset));free=int(psutil.virtual_memory().available)
                resources['samples']+=1;resources['peak_rss_bytes']=max(resources['peak_rss_bytes'],peak)
                old=resources['min_available_ram_bytes'];resources['min_available_ram_bytes']=free if old is None else min(old,free)
                need(peak<=1024**3 and free>=2*1024**3,'RSS1GiB/free2GiB bounds')
        memory()
        def watch():
            while not stop.wait(.1):
                try:memory()
                except BaseException as failure:
                    monitor_errors.append(str(failure))
                    try:write('resource-failure.json',dict(error=str(failure),resources=resources))
                    finally:os._exit(125)
        monitor=threading.Thread(target=watch,daemon=True);monitor.start()
        sys.path.insert(0,str(R/'src'));spec,evidence=construct(value)
        from knowledge_tracing.akt.research_main_execution import MainSelectedExecution,require_main_selected_authorization
        need(spec.research.expected_corpus_sha256==public['corpus.json'],'expected actual corpus bytes')
        public_before={name:sha(PUBLIC_ROOT/name) for name in public};need(public_before==public,'actual canonical public10 before')
        phase[0]='actual_admission'
        guard=require_main_selected_authorization(spec,evidence,authorization_file=value['authorization_file'],
            expected_authorization_sha256=value['authorization_sha256'])
        phase[0]='after_admission';memory()
        need(type(guard) is MainSelectedExecution and guard.spec is spec and len(git_calls)==20,'actual guard type and two genuine provenance rounds')
        identity=json.loads(guard.identity_json)
        need(identity['native_evidence']['gate']['status']=='PASS' and guard._condition.variant=='A0'
            and guard._condition.identity==spec.graph_input.implementation_condition_sha256,'genuine Gate and actual A0 condition')
        roles={role:dict(learners=len(guard._corpus.role_data(role).trajectories),targets=guard._corpus.role_data(role).audit['audit']['targets'],
            reference_complete=guard._corpus.role_data(role).reference_complete) for role in ('train','selection','calibration')}
        need(roles==dict(train=dict(learners=48,targets=10080,reference_complete=True),selection=dict(learners=6,targets=1260,reference_complete=True),
            calibration=dict(learners=6,targets=1260,reference_complete=True)),'full canonical role audit')
        need(not spec.research.native_config.output_dir.exists(),'configured fit output remains absent')
        write('actual-admission.json',dict(kind='ACTUAL_MAIN_A0_GUARD_ADMISSION_ONLY',execution_spec_sha256=spec.identity,
            authorization_sha256=value['authorization_sha256'],identity=identity,roles=roles,condition_sha256=guard._condition.identity,
            actual_model_calls=0,actual_optimizer_calls=0,actual_teacher_calls=0,run_main_selected_candidate_called=False))
    except BaseException as failure:error=dict(type=type(failure).__name__,message=str(failure));phase[0]='closed_after_failure'
    finally:
        stop.set()
        if monitor is not None:monitor.join(timeout=.5)
        try:
            after={name:sha(physical(name)) for name in value['source_pins']};input_after={name:sha(physical(name)) for name in actual_inputs}
            public_after={name:sha(PUBLIC_ROOT/name) for name in public}
            need(after==source_before and input_after==actual_inputs and public_after==public and sha(req_path)==pin,'source/request/config/auth/public after')
        except BaseException as failure:
            if error is None:error=dict(type=type(failure).__name__,message=str(failure))
        for key,previous in env_before.items():
            if previous is None:os.environ.pop(key,None)
            else:os.environ[key]=previous
        git_same=git_before=={k:v for k,v in os.environ.items() if k.startswith(('GIT_','GH_'))}
        selected_env_same=all(os.environ.get(k)==v for k,v in env_before.items())
        accepted=(error is None and guard is not None and not forbidden and not monitor_errors
            and (monitor is None or not monitor.is_alive()) and git_same and selected_env_same and elapsed()<WORKER_CAP)
        result=dict(status='ACCEPTED_ACTUAL_MAIN_GUARD_ONLY_PENDING_OUTER' if accepted else 'REJECTED_KEEP_ALL',error=error,
            request_sha256=pin,source_before=source_before,source_after=after,inputs_before=actual_inputs,inputs_after=input_after,
            public_before=public_before,public_after=public_after,ownership=ownership,metadata=metadata,git_calls=git_calls,
            forbidden=forbidden,monitor_errors=monitor_errors,monitor_stopped=monitor is None or not monitor.is_alive(),resources=resources,
            selected_environment_restored=selected_env_same,git_environment_unchanged=git_same,
            elapsed_seconds=elapsed(),worker_cap_seconds=WORKER_CAP,model_calls=0,optimizer_calls=0,teacher_calls=0,
            actual_selected_fit=False,actual_guard_created=guard is not None)
        write('result.json',result);timer.cancel()
        if elapsed()>=WORKER_CAP:write('postwrite-rejection.json',dict(elapsed_seconds=elapsed()));accepted=False
    print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_KEEP_ALL',elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--request',required=True)
    parser.add_argument('--request-sha256',required=True);parser.add_argument('--approval-reference',required=True);args=parser.parse_args()
    main(args.request,args.request_sha256,args.approval_reference)
