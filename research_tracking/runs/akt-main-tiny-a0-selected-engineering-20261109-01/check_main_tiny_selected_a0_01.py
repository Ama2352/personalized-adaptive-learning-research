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
OUT=P/'main-tiny-selected-a0-01';OWNED=P/'main-tiny-selected-a0-01-owned'
CORPUS_ID='grade10-main-lifecycle-engineering10x84-20261109-01'
CORPUS=R/'artifacts/simulator/corpora'/CORPUS_ID
PUBLIC10={'corpus.json','bank.json','plan.json','train.jsonl','train.manifest.json',
    'selection.jsonl','selection.manifest.json','calibration.jsonl','calibration.manifest.json','DONE.json'}


def need(ok,why):
    if not ok:raise ValueError(why)


def deadline():
    need(math.isfinite(time.perf_counter()-START) and time.perf_counter()-START<560,'whole worker560s')


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
        'main_parameters','runtime_evidence','authorization_file','authorization_sha256','approval_reference'}
         and type(value['schema_version']) is int and value['schema_version']==1
         and value['kind']=='ROOT_REVIEWED_ACTUAL_MAIN_TINY_SELECTED_ONLY'
         and value['approval_reference']==args.approval_reference,'closed Root actual tinyfit request')
    need(not any(name in sys.modules for name in ('torch','numpy','pandas','knowledge_tracing')),'cold before actual guard')
    source_before={name:sha(path(name)) for name in value['source_pins']}
    need(source_before==value['source_pins'] and 1<=len(source_before)<=256,'actual source pins')
    auth=path(value['authorization_file'])
    need(auth.is_relative_to(R/'experiments/akt/authorizations') and sha(auth)==value['authorization_sha256'],'new authorization bytes')
    write('reservation.json',dict(kind='UPPER_BOUND_NOT_ACTUAL_COUNTS',owner=owner,request_sha256=args.request_sha256,
        optimizer_steps=40,optimized_target_exposures=13440,model_constructors=2,adam_constructors=2,
        native_training_forwards=40,native_selection_forwards=21,selection_target_exposures=1764,
        checkpoint_saves=20,fresh_restores=1,main_wall_seconds=540,training_seconds=300,
        worker_seconds=560,owned_seconds=580,outer_seconds=600,automatic_retry=False,resume_supported=False))
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
        claim=runner.run_main_selected_candidate(spec,evidence,authorization_file=value['authorization_file'],
            expected_authorization_sha256=value['authorization_sha256'])
        phase[0]='post_entry';memory()
        terminal=read(spec.research.native_config.output_dir/'selected-terminal.json')
        complete=read(spec.research.native_config.output_dir/'COMPLETE.json')
        need(terminal['status']=='SELECTED_ONLY_COMPLETE' and complete['status']=='COMPLETE_MAIN_SELECTED_ONLY_CANDIDATE'
             and terminal['candidate_id']=='A0' and terminal['fresh_best_reload'] is True,'actual complete selected-only outputs')
        epochs=terminal['complete_fit_epochs'];saves=observer.counts['checkpoint_save']['returned']
        need(type(epochs) is int and 4<=epochs<=20 and 1<=saves<=epochs,'actual completed frozen epochs and saves')
        expected_metadata=15+4*epochs+2*saves
        for key,count in dict(model_constructor=2,adam_constructor=2,adapter_step=2*epochs,selection_pass=epochs+1,
                native_forward=3*epochs+1,checkpoint_inspect=2,checkpoint_restore=1,metadata=expected_metadata,
                auth=expected_metadata,native_evidence=expected_metadata,corpus_hash_audit=expected_metadata,
                revalidate=expected_metadata-1,lazy_tools=1).items():
            need(observer.counts[key]==dict(started=count,returned=count,exceptions=0),'actual observed '+key)
        need(observer.training_targets==672*epochs and observer.selection_windows==epochs+1
             and observer.selection_targets==84*(epochs+1)
             and observer.forward_by_scope==dict(training=2*epochs,selection=epochs+1)
             and len(git_calls)==10*(expected_metadata+observer.counts['model_constructor']['returned']),
             'actual model calls plus metadata and constructor provenance reconciliation')
        counters=terminal['counters']
        need(counters['reserved']==counters['body_returned']==counters['complete']==2*epochs
             and counters['reserved_targets']==counters['body_returned_targets']==counters['complete_targets']==672*epochs,
             'native durable tracker counters')
        journal=[json.loads(line) for line in (spec.research.native_config.output_dir/'events.jsonl').read_text().splitlines()]
        kinds=Counter(row['kind'] for row in journal)
        need(kinds['tracker_optimizer_started']==kinds['tracker_optimizer_body_returned']==kinds['step_committed']==2*epochs,
             'existing actual Adam journal, no Adam.step patch')
        need(terminal['full_selection']['full_targets']==terminal['full_selection']['supported_targets']==84
             and terminal['full_selection']['unsupported_targets']==0 and claim.complete_fit_epochs==epochs
             and claim.full_targets==claim.supported_targets==84,'all raw selection target keys supported')
        import csv
        exported={}
        for name in ('predictions.csv','targets.csv'):
            with (spec.research.native_config.output_dir/'selection'/name).open(newline='',encoding='utf-8') as stream:
                exported[name]=list(csv.DictReader(stream))
        keys=lambda rows:[(row['learner_id'],row['source_row'],row['global_rank'],row['item_id']) for row in rows]
        need(len(exported['predictions.csv'])==len(exported['targets.csv'])==84
             and len(set(keys(exported['predictions.csv'])))==84
             and keys(exported['predictions.csv'])==keys(exported['targets.csv']),'exact full raw export key population')
        need(all(row['phase_scope']=='raw_selection10' and row['origin_role']=='selection'
                 for rows in exported.values() for row in rows),'raw selection-only exports')
        need(not terminal['refit_started'] and not terminal['calibration_used_for_selection']
             and not complete['refit_calibration_performed'] and not complete['main_matrix_complete'],'no external freeze/refit/calibration promotion')
        need(not any((spec.research.native_config.output_dir/name).exists() for name in ('failure.json','refit90','calibration')),
             'no failure override or forbidden phase outputs')
        need(not denied and not monitor_errors and not sys.modules['torch'].cuda.is_initialized(),'no hidden denials/CUDA initialization')
        write('actual-completion-check.json',dict(epochs=epochs,best_saves=saves,metadata_dispatches=expected_metadata,
            selection_forward_passes=epochs+1,selection_target_exposures=observer.selection_targets,observed=observer.payload(),
            journal_counts=dict(kinds),selected_epoch=terminal['selected_epoch'],claim=asdict(claim),
            engineering_only=True,resume_supported=False))
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
        if error is None:
            final_complete=read(spec.research.native_config.output_dir/'COMPLETE.json')
            need(all(outputs[(spec.research.native_config.output_dir/name).relative_to(R).as_posix()]['sha256']==pin
                     for name,pin in final_complete['outputs_sha256'].items()),'native COMPLETE inventory unchanged')
    accepted=error is None and not denied and not monitor_errors and restored
    accepted=accepted and (monitor is None or not monitor.is_alive()) and time.perf_counter()-START<560
    write('result.json',dict(status='ACTUAL_TINY_A0_SELECTED_ONLY_PENDING_OUTER' if accepted else 'REJECTED_KEEP_PARTIAL_NO_RESUME',
        error=error,owner=owner,source_before=source_before,source_after=after,request_sha256=args.request_sha256,
        observer=observer.payload(),observer_restored=restored,denied=denied,git_calls=git_calls,resources=resources,
        monitor_errors=monitor_errors,monitor_stopped=monitor is None or not monitor.is_alive(),
        native_outputs=outputs,elapsed_seconds=time.perf_counter()-START,worker_cap_seconds=560,
        research_main_matrix_completed=False,resume_supported=False,cuda_initialized=False if accepted else None))
    deadline();need(not denied and not monitor_errors,'final denial/resource counters')
    return 0 if accepted else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--request',required=True);parser.add_argument('--request-sha256',required=True)
    parser.add_argument('--approval-reference',required=True)
    raise SystemExit(run(parser.parse_args()))
