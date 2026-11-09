"""SOURCE-ONLY actual normal Main A0 entry on genuine engineering10x84.

No preliminary guard, model factory, callbacks or simulated fit. Instrumentation
calls original functions exactly once; NN methods are installed only inside the
already-called lazy _tools, after genuine public entry has admitted its guard.
"""
import time
START=time.perf_counter()
from pathlib import Path
import argparse
from collections import Counter
from dataclasses import asdict
import functools
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import threading
import traceback

R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
OUT=P/'graph29-a0-pause5-01';OWNED=P/'graph29-a0-pause5-01-owned'
CORPUS_ID='grade10-main-lifecycle-engineering10x84-20261109-01'
CORPUS=R/'artifacts/simulator/corpora'/CORPUS_ID
PUBLIC10={'corpus.json','bank.json','plan.json','train.jsonl','train.manifest.json',
    'selection.jsonl','selection.manifest.json','calibration.jsonl','calibration.manifest.json','DONE.json'}


def need(ok,why):
    if not ok:raise ValueError(why)


def deadline():
    need(math.isfinite(time.perf_counter()-START) and time.perf_counter()-START<160,'whole worker160s')


def path(relative):
    need(type(relative) is str and '\\' not in relative and not Path(relative).is_absolute()
         and '..' not in Path(relative).parts,'relative POSIX path')
    value=R
    for part in Path(relative).parts:
        value/=part;need(not value.is_symlink() and not value.is_junction(),'physical path')
    need(value.resolve()==value.absolute() and value.is_relative_to(R),'same-root path')
    return value


def sha(value,cap=64*1024**2):
    need(value.is_file() and value.stat().st_size<=cap,'bounded regular input/output')
    digest=hashlib.sha256();used=0
    with value.open('rb') as stream:
        while block:=stream.read(65536):
            deadline();used+=len(block);need(used<=cap,'stream byte cap');digest.update(block)
    return digest.hexdigest()


def read(value,cap=2*1024**2):
    need(value.stat().st_size<=cap,'bounded JSON')
    def unique(rows):
        result={}
        for key,item in rows:
            need(key not in result,'duplicate JSON key');result[key]=item
        return result
    return json.loads(value.read_bytes(),object_pairs_hook=unique,
        parse_constant=lambda value:(_ for _ in ()).throw(ValueError('nonfinite JSON')))


def write(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    need(len(raw)<=2*1024**2,'small operational receipt')
    with (OUT/name).open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())


def construct(value):
    from knowledge_tracing.akt.config import load_config
    from knowledge_tracing.akt.research_execution import SimulatorResearchSpec,ResearchResourceBudget,ResearchRuntimeEvidence
    from knowledge_tracing.akt.research_main_stage import MainSelectedStageSpec
    from knowledge_tracing.research_admission import MainSelectionContext
    from knowledge_tracing.akt.research_main_execution import MainSelectedExecutionSpec,MainGitProfile,MainGraphInput
    from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits
    config_file=path(value['native_config_file'])
    need(config_file.is_relative_to(R/'experiments/akt/configs') and sha(config_file)==value['native_config_sha256'],
         'actual new config')
    config=load_config(config_file);parameters=dict(value['main_parameters'])
    research=dict(parameters.pop('research'));research['native_config']=config
    research['budget']=ResearchResourceBudget(**research['budget'])
    stage=dict(parameters.pop('stage'));stage['context']=MainSelectionContext(**stage['context'])
    git=dict(parameters.pop('git_profile'));git['upstream_files_sha256']=tuple(tuple(row) for row in git['upstream_files_sha256'])
    spec=MainSelectedExecutionSpec(research=SimulatorResearchSpec(**research),stage=MainSelectedStageSpec(**stage),
        read_limits=CorpusReadLimits(**parameters.pop('read_limits')),graph_input=MainGraphInput(**parameters.pop('graph_input')),
        git_profile=MainGitProfile(**git),**parameters)
    budget=spec.research.budget
    need(spec.stage.candidate_id=='A0' and spec.research.corpus_id==CORPUS_ID
         and (budget.train_learners,budget.selection_learners,budget.calibration_learners)==(8,1,1)
         and (budget.train_targets,budget.selection_targets,budget.calibration_targets)==(672,84,84)
         and budget.max_events_per_learner==84,'new genuine8/1/1 corpus, not canonical60')
    need(budget.max_optimizer_steps==40 and budget.max_optimized_targets==13440
         and budget.max_training_seconds==300. and budget.max_wall_seconds==540.
         and budget.max_rss_bytes==1024**3 and budget.min_available_ram_bytes==2*1024**3
         and budget.max_checkpoint_bytes==64*1024**2 and budget.max_prediction_bytes==4*1024**2
         and spec.max_output_bytes==1536*1024**2,'reviewed finite allocation only')
    need(config.max_epochs==20 and config.patience==3 and config.context==config.target_block==100
         and config.dropout==.05 and config.batch_size==4 and config.seed==42,'frozen scientific recipe')
    need(not config.output_dir.exists(),'fresh model output, no resume')
    return spec,ResearchRuntimeEvidence(**value['runtime_evidence'])


class Observer:
    """Targeted passthrough only; no profiler, class replacement or tensor ops."""
    def __init__(self):
        self.bindings=[];self.counts={};self.times={};self.events=[]
        self.scope='outside';self.training_targets=0;self.selection_windows=0;self.selection_targets=0
        self.forward_by_scope=Counter();self.nn_installed=False

    def install(self,owner,name,key,scope=None,after=None):
        original=getattr(owner,name)
        self.counts[key]=dict(started=0,returned=0,exceptions=0)
        self.times[key]=0.
        @functools.wraps(original)
        def observed(*args,**kwargs):
            started=time.perf_counter();old=self.scope
            if scope is not None:self.scope=scope
            cap = dict(model_constructor=1,adam_constructor=1,adapter_step=10,selection_pass=5,
                native_forward=15,checkpoint_save=5,checkpoint_inspect=0,checkpoint_restore=0).get(key)
            need(cap is None or self.counts[key]['started'] < cap,'parent physical call cap before body '+key)
            self.counts[key]['started']+=1
            if key=='native_forward':self.forward_by_scope[self.scope]+=1
            try:
                result=original(*args,**kwargs)
                self.counts[key]['returned']+=1
                if after is not None:after(args,kwargs,result)
                return result
            except BaseException:
                self.counts[key]['exceptions']+=1;raise
            finally:
                self.times[key]+=time.perf_counter()-started;self.scope=old
        setattr(owner,name,observed);self.bindings.append((owner,name,original,observed))

    def install_main(self,main,runner,old):
        self.install(main.MainSelectedExecution,'revalidate','revalidate')
        self.install(main,'_auth','auth')
        self.install(main,'_metadata','metadata')
        self.install(main,'_main_native_evidence','native_evidence')
        self.install(old,'_corpus','corpus_hash_audit')
        # Do not import Torch/graph model here. Actual entry calls original
        # _tools only after require_main_selected_authorization has returned.
        self.install(runner,'_tools','lazy_tools',after=lambda a,k,tools:self.install_nn(tools))

    def install_nn(self,tools):
        need(not self.nn_installed,'one genuine lazy tools call')
        from knowledge_tracing.akt.research_graph_model import ResearchGraphNative
        self.nn_installed=True
        def step_returned(args,kwargs,result):
            need(type(result) is dict and type(result['valid_targets']) is int,'actual step result dictionary')
            self.training_targets+=result['valid_targets']
        def predicted(args,kwargs,result):
            self.selection_windows+=len(args[1])
            self.selection_targets+=sum(int(window.target_mask.sum()) for window in args[1])
        self.install(tools.graph_adapter,'__init__','model_constructor')
        self.install(tools.torch.optim.Adam,'__init__','adam_constructor')
        self.install(tools.graph_adapter,'step','adapter_step',scope='training',after=step_returned)
        self.install(tools.graph_adapter,'predict_windows','selection_pass',scope='selection',after=predicted)
        self.install(ResearchGraphNative,'forward','native_forward')
        self.install(tools.cp,'save_graph_epoch_state','checkpoint_save')
        self.install(tools.cp,'inspect_graph_epoch_state','checkpoint_inspect')
        self.install(tools.cp,'restore_graph_epoch_state','checkpoint_restore')

    def restore(self):
        errors=[]
        for owner,name,original,observed in reversed(self.bindings):
            if getattr(owner,name,None) is observed:
                setattr(owner,name,original)
            else:
                errors.append(name)
        need(not errors,'instrumentation binding changed; other owned bindings restored')
        need(all(getattr(owner,name) is original for owner,name,original,_ in self.bindings),'all original functions restored')

    def payload(self):
        return dict(counts=self.counts,inclusive_seconds=self.times,
            nested_times_must_not_be_summed=True,training_targets=self.training_targets,
            selection_windows=self.selection_windows,selection_targets=self.selection_targets,
            forward_by_scope=dict(self.forward_by_scope),
            nn_installed_only_after_actual_entry_lazy_tools=self.nn_installed,global_profiler_used=False,
            adam_step_or_backward_patched=False,extra_native_model_calls=0)


def run(args):
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner=worker_gate()
    need(not OUT.exists(),'fresh actual fit receipt directory');OUT.mkdir()
    temp=OWNED/'runtime-temp';temp.mkdir(exist_ok=False)
    os.environ.update(TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp))
    request_file=path(args.request);need(request_file.parent==P and sha(request_file)==args.request_sha256,'reviewed actual request')
    value=read(request_file)
    need(set(value)=={'schema_version','kind','source_pins','native_config_file','native_config_sha256',
        'main_parameters','runtime_evidence','authorization_file','authorization_sha256','approval_reference','pause_policy','control_reference'}
         and type(value['schema_version']) is int and value['schema_version']==1
         and value['kind']=='ROOT_REVIEWED_ACTUAL_MAIN_GRAPH29_PAUSE5_A0_ONLY'
         and value['approval_reference']==args.approval_reference,'closed Root actual tinyfit request')
    need(not any(name in sys.modules for name in ('torch','numpy','pandas','knowledge_tracing')),'cold before actual guard')
    source_before={name:sha(path(name)) for name in value['source_pins']}
    need(source_before==value['source_pins'] and 1<=len(source_before)<=256,'actual source pins')
    auth=path(value['authorization_file'])
    need(auth.is_relative_to(R/'experiments/akt/authorizations') and sha(auth)==value['authorization_sha256'],'new authorization bytes')
    write('reservation.json',dict(kind='UPPER_BOUND_NOT_ACTUAL_COUNTS',owner=owner,request_sha256=args.request_sha256,
        optimizer_steps=10,optimized_target_exposures=3360,model_constructors=1,adam_constructors=1,
        native_training_forwards=10,native_selection_forwards=5,selection_target_exposures=420,
        checkpoint_saves=5,fresh_restores=0,main_wall_seconds=540,training_seconds=300,
        worker_seconds=160,owned_seconds=170,outer_seconds=180,charged_parent_wall_seconds=180,automatic_retry=False,resume_supported=False))
    phase=['metadata'];denied=[];metadata_calls=[];git_calls=[];observer=Observer()
    cmd=os.path.normcase(os.path.abspath(str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')))
    upstream=R/'artifacts/akt/dependencies/upstream'
    tails=[('rev-parse','HEAD'),('status','--porcelain','--untracked-files=all'),('remote','get-url','origin')]
    for name in ('akt.py','README.md','LICENSE'):tails += [('hash-object',name),('rev-parse','HEAD:'+name)]
    tails += [('rev-parse','HEAD^{tree}')]
    git_argv=[subprocess.list2cmdline(['git','-C',str(upstream),*tail]) for tail in tails]
    def audit(event,values):
        if event=='import':
            name=str(values[0])
            if name in {'knowledge_tracing.paper2_reference','knowledge_tracing.simulator_research_collection',
                        'knowledge_tracing.simulator_collection'} or name.split('.')[0] in {'modal','boto3','pyBKT'}:
                denied.append('teacher_or_cloud:'+name);raise RuntimeError('no teacher/new data/cloud')
            if name.split('.')[0]=='torch' and phase[0]!='main_entry':
                denied.append('premature_torch');raise RuntimeError('Torch only inside actual admitted entry lazy tools')
        if event=='subprocess.Popen':
            if phase[0]=='metadata' and len(metadata_calls)<3 and type(values[0]) is str and type(values[1]) is str:
                allowed={cmd.casefold()+' /c "ver"','"'+cmd.casefold()+'" /c "ver"'}
                if os.path.normcase(os.path.abspath(values[0]))==cmd and values[1].strip().casefold() in allowed:
                    metadata_calls.append(values[1]);return
            if phase[0]=='main_entry' and len(git_calls)<1370 and values[0] in (None,'git') and values[1]==git_argv[len(git_calls)%10]:
                git_calls.append(values[1]);return
            denied.append(event);raise RuntimeError('undeclared process')
        if event=='os.system' or event.startswith(('os.spawn','os.posix_spawn')) or event.startswith('socket.') and not (phase[0]=='metadata' and event=='socket.gethostname'):
            denied.append(event);raise RuntimeError('network/undeclared child')
        if event in ('open','os.listdir','os.scandir') and values and isinstance(values[0],(str,bytes,os.PathLike)):
            target=Path(os.path.abspath(os.fsdecode(values[0])))
            if target.is_relative_to(R/'artifacts/simulator/corpora') and target not in {CORPUS/name for name in PUBLIC10}:
                denied.append('nonpublic_corpus');raise RuntimeError('new public10 only, never oracle/final/canonical60')
            if any(target==R/name or target.is_relative_to(R/name) for name in ('dataset','artifacts/bkt_baseline','venv','.wsl')):
                denied.append('protected');raise RuntimeError('protected data')
    sys.addaudithook(audit)
    error=None;claim=None;resources=dict(samples=0,peak_rss_bytes=0,min_available_ram_bytes=None)
    stop=threading.Event();monitor=None;monitor_errors=[];restored=False;spec=None
    try:
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
            deadline();info=process.memory_info();peak=max(info.rss,getattr(info,'peak_wset',0));free=int(psutil.virtual_memory().available)
            resources['samples']+=1;resources['peak_rss_bytes']=max(resources['peak_rss_bytes'],peak)
            old=resources['min_available_ram_bytes'];resources['min_available_ram_bytes']=free if old is None else min(old,free)
            need(peak<=1024**3 and free>=2*1024**3,'worker RSS1GiB/free2GiB')
        memory()
        def watch():
            while not stop.wait(.2):
                try:memory()
                except BaseException as exc:
                    monitor_errors.append(str(exc))
                    try:write('resource-failure.json',dict(error=str(exc),resources=resources))
                    finally:os._exit(125)
        monitor=threading.Thread(target=watch,daemon=True);monitor.start()
        sys.path.insert(0,str(R/'src'));spec,evidence=construct(value)
        from knowledge_tracing.akt import research_main_execution as main,research_execution as old,research_selected_runner as runner
        observer.install_main(main,runner,old)
        need('torch' not in sys.modules,'no model import/preliminary guard before normal public entry')
        phase[0]='main_entry'
        from knowledge_tracing.akt.research_selected_resume import SelectedPausePolicy,PAUSE_STATUS
        policy=SelectedPausePolicy(**value['pause_policy'])
        need(policy.after_epoch==5 and policy.charged_wall_seconds==180.
             and policy.max_attempts==2 and policy.max_constructors==3
             and policy.max_retained_bytes==spec.max_output_bytes
             and policy.original_allocation_sha256==spec.stage.context.allocation_sha256,'exact reviewed parent pause policy')
        pause=runner.run_main_selected_candidate(spec,evidence,authorization_file=value['authorization_file'],
            expected_authorization_sha256=value['authorization_sha256'],pause_policy=policy)
        phase[0]='post_entry';memory()
        need(pause.status==PAUSE_STATUS and pause.epoch==5,'genuine complete-epoch pause reference')
        marker_path=path(pause.marker_file)
        need(marker_path.is_relative_to(spec.research.native_config.output_dir)
             and sha(marker_path)==pause.marker_sha256,'returned actual pause marker')
        marker=read(marker_path);state=read(marker_path.parent/'state.json')
        history=read(marker_path.parent/'history.json')['epochs']
        accounting=read(marker_path.parent/'accounting.json')
        need(set(marker['files_sha256'])=={'state.json','history.json','accounting.json'},'exact three pause sidecars')
        for name,pin in marker['files_sha256'].items():
            need(name in ('state.json','history.json','accounting.json') and sha(marker_path.parent/name)==pin,'pause sidecar bytes')
        need(marker['epoch']==state['epoch']==5 and state['next_epoch']==6 and state['best_epoch']==4
             and state['stopper']['last_epoch']==5 and state['stopper']['best_epoch']==4
             and state['stopper']['stale_epochs']==1,'continuing actual latest5 versus best4')
        need(Path(state['latest']['directory']).name=='epoch-5' and Path(state['best']['directory']).name=='epoch-4'
             and state['latest']['directory']!=state['best']['directory'],'distinct latest and best checkpoints')
        for ref in state['latest'],state['best']:
            directory=Path(ref['directory'])
            need(directory.is_relative_to(spec.research.native_config.output_dir),'only current owned checkpoints')
            for name,field in (('COMPLETE.json','complete_sha256'),('metadata.json','metadata_sha256'),('state.pt','checkpoint_sha256')):
                need(sha(path(directory.relative_to(R).as_posix())/name)==ref[field],'complete checkpoint opaque bytes')
        need(accounting['steps']==dict(reserved=10,returned=10,complete=10)
             and accounting['targets']==dict(reserved=3360,returned=3360,complete=3360)
             and accounting['constructors']==dict(model=1,adam=1) and accounting['attempt']==1,'parent cumulative accounting')
        control={}
        for name,ref in value['control_reference'].items():
            source=path(ref['path']);need(sha(source)==ref['sha256'],'accepted control reference immutable')
            control[name]=read(source)
        need(len(history)==5 and len(control['history'])==7 and control['check']['selected_epoch']==4,'actual control history')
        for current,expected in zip(history,control['history'][:5]):
            need(current['epoch']==expected['epoch'] and current['selected_epoch']==expected['selected_epoch']
                 and current['receipt']==expected['receipt']
                 and current['raw_prediction_semantic_sha256']==expected['raw_prediction_semantic_sha256']
                 and current['raw_selection']==expected['raw_selection']
                 and current['training']['loss_sum']==expected['training']['loss_sum'],'exact continuous prefix before pause')
        claim=control['check']['claim']
        need(state['initial_model_sha256']==claim['initial_model_sha256']
             and state['initial_backbone_sha256']==claim['initial_backbone_sha256'],'same fresh initialization as control')
        for key,count in dict(model_constructor=1,adam_constructor=1,adapter_step=10,selection_pass=5,
                native_forward=15,checkpoint_save=5,checkpoint_inspect=0,checkpoint_restore=0,lazy_tools=1).items():
            need(observer.counts[key]==dict(started=count,returned=count,exceptions=0),'actual parent observed '+key)
        need(observer.training_targets==3360 and observer.selection_windows==5 and observer.selection_targets==420
             and observer.forward_by_scope==dict(training=10,selection=5),'parent actual full target work')
        need(len(git_calls)%10==0 and not denied and not monitor_errors
             and not sys.modules['torch'].cuda.is_initialized(),'original provenance calls and CPU-only execution')
        need(not any((spec.research.native_config.output_dir/name).exists()
             for name in ('COMPLETE.json','selected-terminal.json','selection','failure.json','refit90','calibration')),
             'pause cannot publish final best export or forbidden phase')
        write('actual-pause-check.json',dict(epoch=5,best_epoch=4,latest_epoch=5,stale_epochs=1,
            exact_control_prefix=True,observed=observer.payload(),accounting=accounting,
            pause_reference=asdict(pause),planned_charged_parent_wall_seconds=180,
            engineering_only=True,unexpected_crash_recovery_supported=False))
    except BaseException as exc:
        error=dict(type=type(exc).__name__,message=str(exc))
        with (OUT/'failure.log').open('x',encoding='utf-8') as stream:traceback.print_exc(file=stream)
    finally:
        phase[0]='closed';stop.set()
        if monitor is not None:monitor.join(timeout=.5)
        try:observer.restore();restored=True
        except BaseException as exc:
            if error is None:error=dict(type=type(exc).__name__,message=str(exc))
        write('observer.json',observer.payload())
    after={name:sha(path(name)) for name in source_before}
    need(after==source_before and sha(request_file)==args.request_sha256 and sha(auth)==value['authorization_sha256'],
         'final source/request/auth hashes')
    outputs={}
    if spec is not None and spec.research.native_config.output_dir.exists():
        used=0
        for file in spec.research.native_config.output_dir.rglob('*'):
            if file.is_file():
                used+=file.stat().st_size;need(used<=1536*1024**2,'whole output1536MiB')
                outputs[file.relative_to(R).as_posix()]=dict(sha256=sha(file),bytes=file.stat().st_size)
    accepted=error is None and not denied and not monitor_errors and restored
    accepted=accepted and (monitor is None or not monitor.is_alive()) and time.perf_counter()-START<160
    write('result.json',dict(status='ACTUAL_GRAPH29_PAUSE5_PENDING_OUTER' if accepted else 'REJECTED_KEEP_PARTIAL_NO_RESUME',
        error=error,owner=owner,source_before=source_before,source_after=after,request_sha256=args.request_sha256,
        observer=observer.payload(),observer_restored=restored,denied=denied,git_calls=git_calls,resources=resources,
        monitor_errors=monitor_errors,monitor_stopped=monitor is None or not monitor.is_alive(),
        native_outputs=outputs,elapsed_seconds=time.perf_counter()-START,worker_cap_seconds=160,
        research_main_matrix_completed=False,resume_supported=False,cuda_initialized=False if accepted else None))
    if accepted:
        write('worker-result.json',dict(schema_version=1,status=pause.status,execution_spec_sha256=spec.identity,
            authorization_file=value['authorization_file'],authorization_sha256=value['authorization_sha256'],
            request_file=args.request,request_sha256=args.request_sha256,ownership=owner,pause_reference=asdict(pause)))
    deadline();need(not denied and not monitor_errors,'final denial/resource counters')
    return 0 if accepted else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--request',required=True);parser.add_argument('--request-sha256',required=True)
    parser.add_argument('--approval-reference',required=True)
    raise SystemExit(run(parser.parse_args()))
