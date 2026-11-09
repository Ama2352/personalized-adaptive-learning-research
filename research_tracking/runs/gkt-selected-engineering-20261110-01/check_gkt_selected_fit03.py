"""Một normal entry GKT thật; counters targeted, exact owned-Job RAM, không profiler."""
import time
PERF, WALL = time.perf_counter, time.time
START, START_WALL = PERF(), WALL()
import argparse
from collections import Counter
import ctypes
from ctypes import wintypes
from dataclasses import asdict
import functools
import hashlib
from importlib.util import source_from_cache
import json
import math
import os
from pathlib import Path
import sys
import threading
import traceback
import weakref

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
OUT=PREP/'gkt-selected-fit03'
OWNED=PREP/'gkt-selected-fit03-owned'
TEMP=OWNED/'runtime-temp'
RUN_ID='gkt-selected-engineering10x84-20261110-01'
NATIVE=ROOT/'experiments/gkt/results'/RUN_ID
REQUEST=PREP/'gkt_selected_fit03_request.ROOT.json'
MATERIALIZER=PREP/'materialize_gkt_selected_positive03.py'
METADATA_HELPER=PREP/'prediction_mastery_trace_worker03.py'


def need(ok,message):
    if not ok:
        raise ValueError(message)


def resource_identity_from_handle(api,handle,expected_pid):
    """Resource PID/creation only; Kernel.token image/action provenance stays unchanged.

    GetProcessTimes with QUERY_LIMITED_INFORMATION is documented by Microsoft.
    This helper never ignores a PermissionError or substitutes a missing token.
    """
    need(type(expected_pid) is int and 0<expected_pid<2**32,'sample expected PID')
    actual_pid=int(api.check(api.k.GetProcessId(handle)))
    need(actual_pid==expected_pid,'sampled handle PID changed')
    creation,exit_time,kernel,user=(wintypes.FILETIME() for _ in range(4))
    api.check(api.k.GetProcessTimes(handle,ctypes.byref(creation),ctypes.byref(exit_time),
                                   ctypes.byref(kernel),ctypes.byref(user)))
    ticks=int(creation.dwLowDateTime)|(int(creation.dwHighDateTime)<<32)
    need(ticks>=116444736000000000,'valid process creation FILETIME')
    return dict(pid=actual_pid,created_filetime_100ns=str(ticks),
                create_time=(ticks-116444736000000000)/10000000)


def resource_exit_code(api,handle):
    wait=int(api.k.WaitForSingleObject(handle,0))
    if wait==258:return None
    if wait==0:
        code=wintypes.DWORD();api.check(api.k.GetExitCodeProcess(handle,ctypes.byref(code)))
        return int(code.value)
    if wait==0xffffffff:api.check(0)
    raise ValueError('unknown process wait result '+str(wait))


def sample_opened_resource_member(api,job_handle,handle,pid,psutil_module):
    need(int(api.check(api.k.GetProcessId(handle)))==pid,'resource handle PID mismatch')
    code=resource_exit_code(api,handle)
    if code is not None:
        return dict(kind='exited',pid=pid,phase='precheck',wait=0,exit_code=code,error=None)
    phase='membership'
    try:
        if not api.contains(handle,job_handle):
            code=resource_exit_code(api,handle)
            if code is not None:
                return dict(kind='exited',pid=pid,phase='membership_false',wait=0,exit_code=code,error=None)
            raise ValueError('live resource handle not in owned Job')
        phase='creation_identity';token=resource_identity_from_handle(api,handle,pid)
        phase='psutil_creation';child=psutil_module.Process(pid)
        need(abs(child.create_time()-token['create_time'])<=1e-5,'sampled creation identity')
        phase='rss';rss=int(child.memory_info().rss)
        need(rss>=0,'nonnegative resource RSS')
        return dict(kind='live',pid=pid,created_filetime_100ns=token['created_filetime_100ns'],rss_bytes=rss)
    except (PermissionError,psutil_module.AccessDenied,psutil_module.NoSuchProcess) as caught:
        original_traceback=traceback.format_exc(limit=8)
        try:code=resource_exit_code(api,handle)
        except BaseException as wait_error:raise caught from wait_error
        if code is None:raise
        return dict(kind='exited',pid=pid,phase=phase,wait=0,exit_code=code,
                    error=dict(type=type(caught).__name__,message=str(caught),winerror=getattr(caught,'winerror',None),traceback=original_traceback))


def valid_sha(value):
    need(type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value), 'exact lowercase64hex SHA256 required')


def elapsed():
    return max(PERF()-START,WALL()-START_WALL)


def deadline():
    need(elapsed()<560.,'one cumulative worker560 deadline')


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(2**20):
            deadline();digest.update(block)
    return digest.hexdigest()


def read(path,cap=2**20):
    need(path.is_file() and path.stat().st_size<=cap,'bounded actual metadata')
    return json.loads(path.read_bytes())


def write(name,value):
    payload=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    need(len(payload)<=2**20,'small operational receipt')
    with (OUT/name).open('xb') as stream:
        stream.write(payload);stream.flush();os.fsync(stream.fileno())


class Observer:
    """Giữ class identity, passthrough một lần, chỉ giữ metadata và weakrefs."""
    def __init__(self):
        self.bindings=[];self.counts={};self.times={};self.scope='outside'
        self.forward_by_scope=Counter();self.training_targets=0;self.selection_targets=0
        self.epoch_receipts=[];self.installed=False;self.fit_model=self.fit_optimizer=self.reload_optimizer=None
        self.release_proof={};self.constructor_metadata=[];self.initial_threads=None
        self.prediction_receipts=[];self.primitive_tail_calls=0

    def patch(self,owner,name,key,scope=None,before=None,after=None,cap=None):
        original=getattr(owner,name);own=name in vars(owner)
        self.counts[key]=dict(started=0,returned=0,exceptions=0);self.times[key]=0.
        @functools.wraps(original)
        def observed(*args,**kwargs):
            deadline();started=PERF();previous=self.scope
            if scope is not None:self.scope=scope
            if before is not None:before(args,kwargs)
            need(cap is None or self.counts[key]['started']<cap,'finite observed '+key+' cap')
            self.counts[key]['started']+=1
            if key=='forward':self.forward_by_scope[self.scope]+=1
            try:
                result=original(*args,**kwargs);self.counts[key]['returned']+=1
                if after is not None:after(args,kwargs,result)
                return result
            except BaseException:
                self.counts[key]['exceptions']+=1;raise
            finally:
                self.times[key]+=PERF()-started;self.scope=previous
        setattr(owner,name,observed);self.bindings.append((owner,name,original,observed,own))

    def install_pure(self,runner,execution):
        self.patch(runner,'require_gkt_selected_authorization','authorization',cap=1)
        self.patch(execution.AuthorizedGKTSelectedExecution,'revalidate','revalidate')
        self.patch(execution,'_inspect','metadata_inspection')
        self.patch(runner,'_lazy','lazy_tools',cap=1,after=lambda a,k,t:self.install_nn(t))

    def install_nn(self,tools):
        need(not self.installed,'one actual admitted lazy tools return')
        self.installed=True;self.initial_threads=tools.torch.get_num_threads()
        need(tools.torch.version.cuda is None and not tools.torch.cuda.is_initialized(),'actual CPU build, no CUDA initialization')
        def before_model(args,kwargs):
            if self.counts['model_constructor']['started']==1:
                self.release_proof['fit_model_released_before_reload']=self.fit_model() is None
                self.release_proof['fit_optimizer_released_before_reload']=self.fit_optimizer() is None
                need(all(self.release_proof.values()),'fit containers released before fresh best constructor')
        def after_model(args,kwargs,result):
            model=args[0];count=sum(p.numel() for p in model.parameters())
            need(count==24700 and asdict(model.config)==dict(num_nodes=28,state_dim=32,embedding_dim=32,message_dim=32,
                adjacency_kind='static',node_unit='concept',require_zero_diagonal=True,require_nonnegative=True)
                and len(model.graph.node_ids)==28 and len(model.graph.edges)==31,
                'actual GKT29 concept28/width32/static expert31 configuration')
            self.constructor_metadata.append(dict(parameter_count=count,config=asdict(model.config)))
            if self.fit_model is None:self.fit_model=weakref.ref(model)
        def after_adam(args,kwargs,result):
            if self.fit_optimizer is None:self.fit_optimizer=weakref.ref(args[0])
            else:self.reload_optimizer=weakref.ref(args[0])
        def train_before(args,kwargs):
            need(args[1].phase.scope=='select_train80','no other optimization role')
        def train_after(args,kwargs,result):
            before=result['counters_before'];ledger=result['counters']
            optimized=ledger['optimized_targets']-before['optimized_targets']
            self.training_targets+=optimized
            self.epoch_receipts.append(dict(status=result['status'],stop_reason=result['stop_reason'],
                input_targets=ledger['input_targets']-before['input_targets'],optimized_targets=optimized,
                started=ledger['adam_started']-before['adam_started'],returned=ledger['adam_returned']-before['adam_returned'],
                sequence_started=ledger['sequence_started']-before['sequence_started'],
                sequence_returned=ledger['sequence_returned']-before['sequence_returned'],
                tail_started=ledger['tail_started']-before['tail_started'],tail_returned=ledger['tail_returned']-before['tail_returned'],
                backward_returned=ledger['backward_returned']-before['backward_returned'],
                clip_returned=ledger['clip_returned']-before['clip_returned'],
                observe_events=ledger['returned_sequence_observe_events']-before['returned_sequence_observe_events'],
                padded_slots=ledger['padded_readout_slots']-before['padded_readout_slots'],
                complete=result['complete'],epoch=kwargs['spec'].epoch))
        def predict_before(args,kwargs):
            need(args[1].phase.scope=='raw_selection10','prediction remains selection-only')
            if self.counts['checkpoint_restore']['returned']==1:
                self.release_proof['reload_optimizer_released_before_final_selection']=self.reload_optimizer() is None
                need(self.release_proof['reload_optimizer_released_before_final_selection'],'release reload optimizer before final selection')
        def predict_after(args,kwargs,result):
            self.selection_targets+=len(result['predictions'])
            before=result['counters_before'];ledger=result['counters']
            self.primitive_tail_calls+=ledger['tail_returned']-before['tail_returned']
            self.prediction_receipts.append(dict(complete=result['complete'],full_targets=len(result['predictions']),
                sequence_started=ledger['sequence_started']-before['sequence_started'],
                sequence_returned=ledger['sequence_returned']-before['sequence_returned'],
                tail_started=ledger['tail_started']-before['tail_started'],tail_returned=ledger['tail_returned']-before['tail_returned'],
                model_calls=ledger['model_calls_returned']-before['model_calls_returned'],
                observe_events=ledger['returned_sequence_observe_events']-before['returned_sequence_observe_events'],
                padded_slots=ledger['padded_readout_slots']-before['padded_readout_slots'],
                state_readonly=result['model_state_before']==result['model_state_after'],
                bn_readonly=result['normalization_before']==result['normalization_after']))
        def serialization(expected):
            def before(args,kwargs):need(self.scope==expected,'serialization only inside the owned checkpoint primitive')
            return before
        self.patch(tools.model,'__init__','model_constructor',before=before_model,after=after_model,cap=2)
        self.patch(tools.torch.optim.Adam,'__init__','adam_constructor',after=after_adam,cap=2)
        self.patch(tools.model,'forward','forward',cap=151)
        self.patch(tools.model,'sequence','sequence',cap=151)
        self.patch(tools.torch.autograd,'backward','logical_backward',before=serialization('training'),cap=100)
        self.patch(tools.torch.nn.utils,'clip_grad_norm_','clip',before=serialization('training'),cap=100)
        self.patch(tools.training,'train_research_epoch','train_epoch',scope='training',before=train_before,after=train_after,cap=50)
        self.patch(tools.training,'predict_research_gkt','selection_pass',scope='selection',before=predict_before,after=predict_after,cap=51)
        self.patch(tools.cp,'save_epoch_state','checkpoint_save',scope='checkpoint_save',cap=50)
        self.patch(tools.cp,'restore_epoch_state','checkpoint_restore',scope='checkpoint_restore',cap=1)
        self.patch(tools.torch,'save','torch_save',before=serialization('checkpoint_save'),cap=50)
        self.patch(tools.torch,'load','torch_load',before=serialization('checkpoint_restore'),cap=1)
        self.patch(tools.model,'load_state_dict','model_restore',cap=1)
        self.patch(tools.torch.optim.Adam,'load_state_dict','optimizer_restore',cap=1)

    def restore(self):
        errors=[]
        for owner,name,original,observed,own in reversed(self.bindings):
            if getattr(owner,name,None) is not observed:errors.append(name);continue
            if own:setattr(owner,name,original)
            else:delattr(owner,name)
        need(not errors and all(getattr(o,n) is original for o,n,original,_,_ in self.bindings),'all owned observer bindings restored')

    def payload(self):
        return dict(counts=self.counts,inclusive_seconds=self.times,nested_times_not_additive=True,
            forward_by_scope=dict(self.forward_by_scope),training_targets=self.training_targets,selection_targets=self.selection_targets,
            epochs=self.epoch_receipts,constructor_metadata=self.constructor_metadata,release_proof=self.release_proof,
            prediction_receipts=self.prediction_receipts,primitive_tail_calls=self.primitive_tail_calls,
            tail_scope='actual primitive counters, not a wrapper on every inner readout',
            installed_after_actual_lazy_tools=self.installed,global_profiler_used=False,
            adam_step_patched=False,logical_autograd_backward_observed=True)


def main():
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate,safe,Kernel,MAX_PROCESSES
    owner=worker_gate()
    parser=argparse.ArgumentParser()
    parser.add_argument('--request-sha256',required=True);parser.add_argument('--approval-reference',required=True)
    args=parser.parse_args()
    valid_sha(args.request_sha256)
    need(sha(safe(REQUEST))==args.request_sha256 and args.approval_reference.strip(),'external Root actual request and reference')
    request=read(REQUEST)
    need(request['kind']=='ROOT_REVIEWED_ACTUAL_GKT_SELECTED_ENGINEERING_ONLY'
         and request['approval_reference']==args.approval_reference and not OUT.exists() and not NATIVE.exists(),'fresh GKT normal entry')
    pins=request['source_pins'];inputs=request['input_pins'];runtime=request['runtime_pins']
    for mapping in (pins,inputs,runtime):
        for digest in mapping.values():valid_sha(digest)
    for key in ('proposal_sha256','dry_sha256','dry_packet_sha256','selected_spec_sha256','authorization_sha256'):valid_sha(request[key])
    source_before={n:sha(safe(ROOT/n)) for n in pins};input_before={n:sha(safe(ROOT/n)) for n in inputs}
    runtime_before={n:sha(Path(n)) for n in runtime}
    need(source_before==pins and input_before==inputs and runtime_before==runtime,'current reviewed source/input/runtime')
    auth=safe(ROOT/request['authorization_file'])
    need(auth==ROOT/'experiments/gkt/authorizations'/(RUN_ID+'.json') and sha(auth)==request['authorization_sha256'],'own actual GKT authorization')
    OUT.mkdir();TEMP.mkdir()
    environment_keys=('TEMP','TMP','TMPDIR','COLUMNS','LINES')
    env={n:os.environ.get(n) for n in environment_keys};os.environ.update(TEMP=str(TEMP),TMP=str(TEMP),TMPDIR=str(TEMP),COLUMNS='80',LINES='24')
    sys_before=(sys.prefix,sys.executable,sys.dont_write_bytecode,list(sys.argv),sys.pycache_prefix)
    path_before=list(sys.path)
    prefix=str(TEMP/'fresh-bytecode');need(not Path(prefix).exists(),'fresh owned import cache');sys.pycache_prefix=prefix
    timer=threading.Timer(max(.001,560.-elapsed()),lambda:os._exit(124));timer.daemon=True;timer.start()
    write('reservation.json',dict(status='UPPER_BOUNDS_NOT_ACTUAL_COUNTS',model_constructors=2,adam_constructors=2,
        optimizer_steps=100,optimized_targets=33600,selection_passes=51,selection_targets=4284,forwards=151,
        sequences=151,primitive_tail_queries=51,top_level_model_calls=202,logical_backwards=100,clip_calls=100,
        checkpoint_saves=50,checkpoint_loads=1,complete_epoch_boundary_only=True,refit=False,calibration_fit=False))
    observer=Observer();phase=['metadata'];denied=[];metadata={};monitor_errors=[];stop=threading.Event();lock=threading.RLock()
    api=job_handle=monitor=None;handle_closed=False;observer_restored=False;error=None;claim=None;native_outputs={}
    resources=dict(samples=0,peak_worker_rss_bytes=0,peak_family_rss_bytes=0,minimum_available_ram_bytes=None,
        maximum_job_processes=0,exited_during_sample=0,verified_exit_count=0,verified_exit_examples=[],first_members=[],peak_members=[])
    public_root=ROOT/'artifacts/simulator/corpora/grade10-main-lifecycle-engineering10x84-20261109-01'
    public_files={'corpus.json','bank.json','plan.json','train.jsonl','train.manifest.json','selection.jsonl','selection.manifest.json',
        'calibration.jsonl','calibration.manifest.json','DONE.json'}
    allowed={safe(ROOT/n) for n in (*pins,*inputs)}|{REQUEST,auth}
    runtime_roots=(ROOT/'.venv',Path(sys.base_prefix).resolve())
    def owned(path):return path.is_relative_to(OUT) or path.is_relative_to(TEMP) or path.is_relative_to(NATIVE)
    def reject(event,details):
        if len(denied)<8:
            row=dict(event=event,phase=phase[0],details=details,seconds=elapsed());denied.append(row)
            with (OUT/'denials.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(row,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
        raise RuntimeError('undeclared fit operation')
    def audit(event,values):
        if event=='import':
            name=str(values[0])
            if name in {'knowledge_tracing.paper2_reference','knowledge_tracing.simulator_collection','knowledge_tracing.simulator_research_collection'} or name.split('.')[0] in {'modal','boto3','pyBKT'}:
                reject(event,name)
            if name.split('.')[0]=='torch' and phase[0]!='entry':reject(event,'Torch must be loaded by admitted normal entry')
        if event=='subprocess.Popen' and phase[0]!='metadata':reject(event,'no child after genuine Windows metadata')
        if event.startswith('socket.') and not(phase[0]=='metadata' and event=='socket.gethostname'):reject(event,'network forbidden')
        if event=='os.system' or event.startswith('os.spawn'):reject(event,'system/spawn forbidden')
        if event in ('open','os.listdir','os.scandir') and values and isinstance(values[0],(str,bytes,os.PathLike)):
            name=os.fsdecode(values[0]);path=Path(name).absolute().resolve()
            if any(path==ROOT/n or path.is_relative_to(ROOT/n) for n in ('dataset','artifacts/bkt_baseline','venv','.wsl')):reject(event,'protected data')
            if path.is_relative_to(ROOT/'artifacts/simulator/corpora') and path not in {public_root/n for n in public_files}:reject(event,'only exact public10 corpus, never oracle/final')
            if event=='open':
                mode=values[1] or '';flags=values[2] if type(values[2]) is int else 0
                writing=any(c in mode for c in 'wax+') or bool(flags&(os.O_WRONLY|os.O_RDWR))
                if phase[0]=='metadata' and name==os.devnull and not flags&(os.O_CREAT|os.O_TRUNC|os.O_APPEND):return
                if writing:
                    if not owned(path):reject(event,dict(path=str(path),mode=mode,flags=flags))
                else:
                    source=None
                    if path.suffix=='.pyc':
                        try:source=Path(source_from_cache(str(path))).resolve()
                        except ValueError:pass
                    if path not in allowed and source not in allowed and not owned(path) and not any(path.is_relative_to(r) for r in runtime_roots):reject(event,dict(path=str(path),mode=mode,flags=flags))
        if event in ('os.mkdir','os.remove','os.rmdir','os.rename'):
            paths=values[:2] if event=='os.rename' else values[:1]
            if not all(owned(Path(v).absolute().resolve()) for v in paths):reject(event,'mutation outside own run/temp/operational roots')
        if event in ('os.link','os.symlink'):reject(event,'links forbidden')
    sys.addaudithook(audit)
    try:
        import psutil
        process=psutil.Process();api=Kernel();job_handle=api.check(api.k.OpenJobObjectW(0x0004,False,owner['job_name']))
        api.k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];api.k.WaitForSingleObject.restype=wintypes.DWORD
        api.k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];api.k.GetExitCodeProcess.restype=wintypes.BOOL
        need(api.contains(api.k.GetCurrentProcess(),job_handle),'actual owned Job handle')
        class ProcessList(ctypes.Structure):
            _fields_=[('assigned',wintypes.DWORD),('listed',wintypes.DWORD),('pids',ctypes.c_size_t*MAX_PROCESSES)]
        def memory():
            with lock:
                deadline();row=ProcessList()
                api.check(api.k.QueryInformationJobObject(job_handle,3,ctypes.byref(row),ctypes.sizeof(row),None))
                pids=[int(row.pids[i]) for i in range(min(int(row.listed),MAX_PROCESSES))]
                need(0<row.listed==row.assigned<=MAX_PROCESSES and process.pid in pids and len(pids)==len(set(pids)),'complete exact Job PID query')
                family=0;members=[]
                for pid in pids:
                    handle=api.k.OpenProcess(0x1000|0x100000,False,pid)
                    if not handle:
                        failure_code=ctypes.get_last_error()
                        if failure_code in (87,1168) and not psutil.pid_exists(pid):
                            resources['exited_during_sample']+=1;continue
                        api.check(0)
                    try:
                        member=sample_opened_resource_member(api,job_handle,handle,pid,psutil)
                        if member['kind']=='exited':
                            resources['exited_during_sample']+=1;resources['verified_exit_count']+=1
                            if len(resources['verified_exit_examples'])<32:resources['verified_exit_examples'].append(member)
                            continue
                        family+=member['rss_bytes'];members.append(member)
                    finally:api.close(handle)
                info=process.memory_info();worker=max(int(info.rss),int(getattr(info,'peak_wset',0)));free=int(psutil.virtual_memory().available)
                resources['samples']+=1;need(resources['samples']<=6000,'bounded .1s resource sampling')
                resources['peak_worker_rss_bytes']=max(resources['peak_worker_rss_bytes'],worker)
                if not resources['first_members']:resources['first_members']=members
                if family>resources['peak_family_rss_bytes']:resources['peak_members']=members
                resources['peak_family_rss_bytes']=max(resources['peak_family_rss_bytes'],family)
                previous=resources['minimum_available_ram_bytes'];resources['minimum_available_ram_bytes']=free if previous is None else min(previous,free)
                resources['maximum_job_processes']=max(resources['maximum_job_processes'],len(pids))
                need(worker<=2*2**30 and family<=2*2**30 and free>=2*2**30,'GKT worker/family2GiB/free2GiB')
        memory()
        def watch():
            while not stop.wait(.1):
                try:memory()
                except BaseException as caught:
                    monitor_errors.append(dict(type=type(caught).__name__,message=str(caught),phase=phase[0],traceback=traceback.format_exc(limit=10)))
                    try:write('resource-failure.json',dict(errors=monitor_errors,resources=resources))
                    finally:os._exit(125)
        monitor=threading.Thread(target=watch,daemon=True);monitor.start()
        raw_helper=METADATA_HELPER.read_bytes();need(hashlib.sha256(raw_helper).hexdigest()==pins[METADATA_HELPER.relative_to(ROOT).as_posix()],'real Windows metadata helper pin')
        namespace=dict(__file__=str(METADATA_HELPER),__name__='gkt_real_windows_metadata_only')
        exec(compile(raw_helper,str(METADATA_HELPER),'exec'),namespace)
        namespace['native_windows_metadata'](deadline,metadata);namespace['require_metadata_closed'](metadata)
        write('windows-metadata.json',metadata);phase[0]='construct_metadata'
        sys.path[:0]=[str(ROOT/'src'),str(PREP)]
        import materialize_gkt_selected_positive03 as capsule
        need(Path(capsule.__file__).resolve()==MATERIALIZER,'exact source decoder')
        capsule.validate_dry(dry_sha256=request['dry_sha256'],proposal_sha256=request['proposal_sha256'],
            packet_sha256=request['dry_packet_sha256'])
        spec,evidence=capsule.construct(request)
        need(spec.budget.max_optimizer_steps==100 and spec.budget.max_optimized_targets==33600
             and spec.budget.max_prediction_targets==4284 and spec.budget.max_wall_seconds==540.
             and spec.budget.max_training_seconds==300. and spec.budget.cpu_threads==2
             and spec.budget.max_model_calls==202 and spec.budget.max_training_prefix_events==1394400
             and spec.budget.max_prediction_prefix_events==177786
             and spec.budget.max_worker_rss_bytes==2*2**30 and spec.budget.min_available_ram_bytes==2*2**30
             and spec.budget.prelaunch_available_ram_bytes==4*2**30,'unchanged finite GKT recipe allocation')
        from knowledge_tracing.gkt import research_execution as execution,research_runner as runner
        observer.install_pure(runner,execution)
        need('torch' not in sys.modules,'no preliminary model import or execution grant')
        phase[0]='entry'
        claim=runner.run_gkt_selected_fit(spec,evidence,authorization_file=request['authorization_file'],
            expected_authorization_sha256=request['authorization_sha256'])
        phase[0]='post_entry';memory()
        terminal=read(NATIVE/'selected-terminal.json');complete=read(NATIVE/'COMPLETE.json');history=read(NATIVE/'epochs.json')
        need(terminal['status']=='SELECTED_ONLY_COMPLETE' and terminal['candidate_id']=='GKT'
             and complete['status']=='COMPLETE_GKT_MAIN_SELECTED_ONLY','actual selected-only terminal')
        epochs=terminal['complete_fit_epochs'];saves=sum(row['checkpoint_sha256'] is not None for row in history)
        need(type(epochs) is int and 6<=epochs<=50 and len(history)==epochs and 1<=saves<=epochs,'actual early stopping epochs')
        expected=dict(authorization=1,lazy_tools=1,model_constructor=2,adam_constructor=2,train_epoch=epochs,
            selection_pass=epochs+1,forward=3*epochs+1,sequence=3*epochs+1,logical_backward=2*epochs,clip=2*epochs,
            checkpoint_save=saves,checkpoint_restore=1,
            torch_save=saves,torch_load=1,model_restore=1,optimizer_restore=1)
        for key,count in expected.items():need(observer.counts[key]==dict(started=count,returned=count,exceptions=0),'actual observed '+key)
        inspections=observer.counts['metadata_inspection']['returned'];revalidations=observer.counts['revalidate']['returned']
        need(inspections==revalidations+1 and observer.counts['metadata_inspection']==dict(started=inspections,returned=inspections,exceptions=0)
             and observer.counts['revalidate']==dict(started=revalidations,returned=revalidations,exceptions=0),'one initial actual admission plus actual revalidations')
        need(observer.forward_by_scope==dict(training=2*epochs,selection=epochs+1)
             and observer.training_targets==672*epochs and observer.selection_targets==84*(epochs+1),'actual forward and target accounting')
        need(all(row['status']=='complete' and row['complete'] is True and row['input_targets']==row['optimized_targets']==672
             and row['started']==row['returned']==row['sequence_started']==row['sequence_returned']==2
             and row['backward_returned']==row['clip_returned']==2 and row['tail_started']==row['tail_returned']==0
             and row['observe_events']==672 and row['padded_slots']==0 and row['epoch']==i+1
             for i,row in enumerate(observer.epoch_receipts)),'actual complete whole-trajectory optimization populations')
        need(len(observer.prediction_receipts)==observer.primitive_tail_calls==epochs+1
             and all(row['complete'] is True and row['full_targets']==84
                     and row['sequence_started']==row['sequence_returned']==row['tail_started']==row['tail_returned']==1
                     and row['model_calls']==2 and row['observe_events']==83 and row['padded_slots']==0
                     and row['state_readonly'] is True and row['bn_readonly'] is True
                     for row in observer.prediction_receipts),'actual prefix83 then query-tail prediction passes')
        counters=terminal['counters']
        need(counters['reserved']==counters['returned']==counters['completed']==2*epochs
             and counters['reserved_targets']==counters['returned_targets']==counters['completed_targets']==672*epochs
             and counters['prediction_passes']==epochs+1 and counters['prediction_full_targets']==84*(epochs+1),'durable cumulative ledger')
        need(terminal['physical_model_calls']==4*epochs+2
             and terminal['epoch_objective']=='gkt29_raw_response_pooled_binary64_log_loss_v1',
             'sequence plus tail workload and adopted GKT29 criterion')
        kinds=Counter()
        with (NATIVE/'events.jsonl').open() as stream:
            for line in stream:kinds[json.loads(line)['kind']]+=1
        need(kinds['adam_reserved']==kinds['adam_body_returned']==2*epochs,'native actual optimizer journal, no patched Adam.step')
        coverage=read(NATIVE/'selection/coverage.json')
        need(coverage['full_targets']==coverage['supported_targets']==84 and coverage['unsupported_targets']==0
             and claim.full_targets==claim.supported_targets==84 and claim.selected_epoch==terminal['selected_epoch'],'complete own selection84')
        need(coverage['objective']=='gkt29_raw_response_pooled_binary64_log_loss_v1'
             and type(coverage['raw_response_log_loss']) is float and math.isfinite(coverage['raw_response_log_loss'])
             and all(row['selection']['objective']==coverage['objective'] for row in history),
             'raw response-pooled binary64 LL, not copied SAKT FP32 criterion')
        import csv
        with (NATIVE/'selection/predictions.csv').open(newline='',encoding='utf-8') as stream:predictions=list(csv.DictReader(stream))
        with (NATIVE/'selection/targets.csv').open(newline='',encoding='utf-8') as stream:targets=list(csv.DictReader(stream))
        export_keys=lambda rows:[(r['learner_id'],r['item_id'],r['timestamp'],r['source_row'],r['global_rank'],r['history_hash_scheme'],r['history_sha256'],r['origin_role']) for r in rows]
        need(len(predictions)==len(targets)==len(set(export_keys(predictions)))==84 and export_keys(predictions)==export_keys(targets)
             and all(r['origin_role']=='selection' and r['phase_scope']=='raw_selection10' for r in predictions),'actual full joined export keys')
        need(not terminal['refit_started'] and not terminal['calibration_used_for_selection'] and not complete['system_freeze_performed']
             and not any((NATIVE/name).exists() for name in ('failure.json','refit90','calibration')),'no forbidden stage/promotion')
        need(all(observer.release_proof.values()) and len(observer.release_proof)==3,'all three measured release boundaries')
        need(sys.modules['torch'].get_num_threads()==observer.initial_threads and not sys.modules['torch'].cuda.is_initialized(),'caller threads restored/no CUDA initialization')
        namespace['require_metadata_closed'](metadata)
        write('actual-completion-check.json',dict(epochs=epochs,best_saves=saves,selected_epoch=claim.selected_epoch,
            claim=asdict(claim),coverage=coverage,journal_counts=dict(kinds),expected_observed_calls=expected,
            engineering_only=True,full_main_matrix_completed=False,public_resume_supported=False))
    except BaseException as caught:
        error=dict(type=type(caught).__name__,message=str(caught))
        with (OUT/'failure.log').open('x',encoding='utf-8') as stream:traceback.print_exc(file=stream)
    finally:
        phase[0]='closed';stop.set()
        if monitor is not None:monitor.join(timeout=2.)
        stopped=monitor is None or not monitor.is_alive()
        if job_handle is not None and stopped:
            try:
                with lock:api.close(job_handle);handle_closed=True
            except BaseException as caught:
                if error is None:error=dict(type=type(caught).__name__,message=str(caught))
        try:observer.restore();observer_restored=True
        except BaseException as caught:
            if error is None:error=dict(type=type(caught).__name__,message=str(caught))
        for name,value in env.items():
            if value is None:os.environ.pop(name,None)
            else:os.environ[name]=value
        sys.pycache_prefix=sys_before[4]
        sys.path[:]=path_before
        restored=env=={n:os.environ.get(n) for n in environment_keys} and sys_before==(sys.prefix,sys.executable,sys.dont_write_bytecode,list(sys.argv),sys.pycache_prefix) and sys.path==path_before
        write('observer.json',observer.payload());write('resources.json',resources)
        source_after={};input_after={};runtime_after={}
        try:
            source_after={n:sha(ROOT/n) for n in pins};input_after={n:sha(ROOT/n) for n in inputs};runtime_after={n:sha(Path(n)) for n in runtime}
            total=0
            if NATIVE.exists():
                for path in NATIVE.rglob('*'):
                    deadline();need(not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(),'no native artifact alias')
                    if path.is_file():
                        total+=path.stat().st_size;need(total<=512*2**20 and len(native_outputs)<256,'bounded actual output inventory')
                        native_outputs[path.relative_to(ROOT).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha(path))
        except BaseException as caught:
            if error is None:error=dict(type=type(caught).__name__,message=str(caught))
            else:error['postcheck_error']=dict(type=type(caught).__name__,message=str(caught))
        accepted=error is None and not denied and not monitor_errors and stopped and handle_closed and observer_restored and restored
        accepted=accepted and source_before==source_after and input_before==input_after and runtime_before==runtime_after and elapsed()<560.
        write('result.json',dict(status='ACTUAL_GKT_SELECTED_ENGINEERING_PENDING_OUTER' if accepted else 'REJECTED_GKT_KEEP_PARTIAL',
            error=error,request_sha256=args.request_sha256,authorization_sha256=request['authorization_sha256'],owner=owner,
            source_before=source_before,source_after=source_after,input_before=input_before,input_after=input_after,
            runtime_before=runtime_before,runtime_after=runtime_after,observer=observer.payload(),observer_restored=observer_restored,
            resources=resources,resource_scope='EXACT_CURRENT_OWNED_JOB_PID_QUERY_AND_WORKER_PEAK_SAMPLED',monitor_errors=monitor_errors,
            monitor_stopped=stopped,job_query_handle_closed=handle_closed,denied=denied,environment_and_sys_restored=restored,
            native_outputs=native_outputs,elapsed_seconds=elapsed(),worker_cap_seconds=560,full_main_matrix_completed=False,
            refit_or_calibration_performed=False,automatic_retry=False,cuda_initialized=False if accepted else None))
        if elapsed()>=560.:write('postwrite_rejection.json',dict(reason='same worker deadline after publication'));accepted=False
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    main()
