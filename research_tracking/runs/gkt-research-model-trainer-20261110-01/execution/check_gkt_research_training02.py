"""ROOT-only8manufactured GKT trainer fixtures, tối đa4actual Adam steps."""
import time
PERF,WALL,MONO=time.perf_counter,time.time,time.monotonic
START,START_WALL,START_MONO=PERF(),WALL(),MONO()
import ctypes
from ctypes import wintypes
from contextlib import redirect_stdout,redirect_stderr
import functools
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import tempfile
import threading
import weakref
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
PACKET=PREP/'gkt_research_training02_packet.json'
OUT=PREP/'gkt-research-training02'
BASE=ROOT/'artifacts/akt/local-tests/grt02'
sys.path.insert(0,str(ROOT/'scripts/research'))
from windows_owned_worker import worker_gate,safe,Kernel,MAX_PROCESSES
owner=worker_gate()


def need(value,message):
    if not value:raise ValueError(message)


def elapsed():return max(PERF()-START,WALL()-START_WALL,MONO()-START_MONO)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


need(len(sys.argv)==3,'ROOT packet SHA and accepted model11 outer SHA required')
raw=safe(PACKET).read_bytes()
need(len(raw)<=131072 and hashlib.sha256(raw).hexdigest()==sys.argv[1],'reviewed packet')
packet=json.loads(raw);pins=packet['source_pins'];runtime=packet['runtime_pins'];caps=packet['expected_counters']
need(all(sha(safe(ROOT/n))==h for n,h in pins.items()) and all(sha(Path(n))==h for n,h in runtime.items()),'actual canonical source/runtime')
model11_path=safe(ROOT/packet['required_model11']['path'])
need(model11_path.is_file() and model11_path.stat().st_size<=1024**2 and sha(model11_path)==sys.argv[2],
    'actual externally pinned model11 result required')
model11=json.loads(model11_path.read_bytes())
need(model11['status']=='ACCEPTED_GKT11_CPU_COMPUTE_NOT_FITTED' and model11['errors']==[]
    and model11['counts']==dict(tests=11,failures=0,errors=0,skipped=0)
    and model11['owned_receipt']['accepted'] is True and model11['owned_receipt']['cleanup_accepted'] is True
    and model11['owned_receipt']['job_active_after_cleanup']==0 and model11['elapsed_seconds']<60
    and not (model11_path.parent/'postwrite_rejection.json').exists(),
    'actual model11 acceptance, not AST or query probe')
for name in ('src/knowledge_tracing/gkt/research_model.py','tests/gkt/test_research_model.py'):
    need(model11['source_before'][name]==model11['source_after'][name]==pins[name],'model11 source binding')
probe_ref=packet['required_job_query_proof'];probe_path=safe(ROOT/probe_ref['path'])
need(sha(probe_path)==probe_ref['sha256'],'actual Kernel Job metadata proof pin')
probe=json.loads(probe_path.read_bytes())
need(probe['status']=='ACCEPTED_JOB_QUERY_METADATA_NOT_NATIVE' and probe['error'] is None
    and len(probe['child']['samples'])==6 and probe['child']['handle_closed'] is True
    and probe['receipt']['accepted'] is True and probe['receipt']['cleanup_accepted'] is True
    and probe['receipt']['job_active_after_cleanup']==0,'accepted query API proof only')
need(not safe(OUT).exists() and not safe(BASE).exists(),'fresh GKT02 output/basetemp')
OUT.mkdir();temporary=OUT/'runtime-temp';temporary.mkdir()
timer=threading.Timer(max(.001,80-elapsed()),lambda:os._exit(124));timer.daemon=True;timer.start()
env_keys=('TEMP','TMP','TMPDIR','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS',
          'CUDA_VISIBLE_DEVICES','NVIDIA_VISIBLE_DEVICES','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')
env_before={n:os.environ.get(n) for n in env_keys}
temp_before=tempfile.tempdir;cache_before=sys.pycache_prefix
os.environ.update(TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
    PYTEST_ADDOPTS='',PYTEST_PLUGINS='',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
    OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
tempfile.tempdir=None;sys.pycache_prefix=str(temporary/'fresh-bytecode')


def write(name,value):
    encoded=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    need(len(encoded.encode('utf-8'))<=1024**2,'bounded metadata output')
    with (OUT/name).open('x',encoding='utf-8') as stream:
        stream.write(encoded);stream.flush();os.fsync(stream.fileno())


phase=['windows_metadata'];metadata_commands=[];forbidden=[]
system_cmd=Path(os.environ['SystemRoot'])/'System32/cmd.exe'


def deny(label):
    forbidden.append(label)
    raise RuntimeError(label)


def audit(kind,values):
    if kind=='subprocess.Popen':
        fixed=os.path.normcase(str(system_cmd))
        commands={fixed.casefold()+' /c "ver"','"'+fixed.casefold()+'" /c "ver"'}
        if (phase[0]=='windows_metadata' and len(metadata_commands)<3 and type(values[0]) is str
            and type(values[1]) is str and os.path.normcase(os.path.abspath(values[0]))==fixed
            and values[1].strip().casefold() in commands):
            metadata_commands.append(dict(executable=values[0],command=values[1]));return
        deny('no subprocess outside exact Windows metadata bootstrap')
    if kind=='os.system' or kind.startswith('os.spawn') or kind.startswith('socket.') and kind!='socket.gethostname':
        deny('no system/spawn/network connection')
    if kind=='import' and str(values[0]).split('.')[0] in ('sklearn','scipy','modal','boto3'):
        deny('no solver/cloud dependency')
    if kind=='import' and (str(values[0]).startswith('knowledge_tracing.gam_kt') or str(values[0]) in (
        'knowledge_tracing.simulator_collection','knowledge_tracing.simulator_research_collection',
        'knowledge_tracing.gkt.pipeline','knowledge_tracing.akt.model')):
        deny('no teacher/legacy trainer/producer imports')
    if kind in ('open','os.listdir','os.scandir','os.mkdir') and values and isinstance(values[0],(str,bytes,os.PathLike)):
        path=Path(os.path.abspath(os.fsdecode(values[0])))
        for relative in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','venv','.wsl','experiments'):
            if path==ROOT/relative or path.is_relative_to(ROOT/relative):deny('no actual/protected data or research outputs')
        if kind=='open':
            mode=values[1] or '';flags=values[2] if type(values[2]) is int else 0
            writing=any(c in mode for c in 'wax+') or bool(flags&(os.O_WRONLY|os.O_RDWR))
            if writing and not(path.is_relative_to(OUT) or path.is_relative_to(BASE)) and os.fsdecode(values[0])!=os.devnull:
                deny('write outside owned GKT fixture outputs')
            if path.suffix in ('.pt','.pth','.ckpt','.safetensors'):deny('no checkpoint/startup payload reads')


sys.addaudithook(audit)
import method_patch_observer02 as observer
patches=observer.MethodPatches()
counts={name:0 for name in caps};ctor_depth=[0]
model_refs=[];shape_proofs=[];gradient_proofs=[];clip_proofs=[];step_proofs=[];phase_proofs=[]
last_model=[None];last_training_targets=[None];active_node=[None]
stop=threading.Event();monitor=None;monitor_errors=[];memory_lock=threading.Lock()
api=job_handle=None;job_query_closed=False
resources=dict(samples=0,peak_worker_rss_bytes=0,peak_family_rss_bytes=0,minimum_available_ram_bytes=None,
    maximum_job_processes=0,exited_during_sample=0,scope='SAMPLED_EXACT_OWNED_JOB_RSS_AND_WORKER_HIGHWATER_NOT_OS_QUOTA')
rc=actual_counts=error=xml_error=None;nodes=[];restoration=None;torch_info=None;old_threads=None;old_dtype=None
value_rejections=[]


def tick(name,amount=1):
    counts[name]+=amount
    need(counts[name]<=caps[name],'bounded actual counter '+name)


def journal(kind,**fields):
    with (OUT/'events.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(kind=kind,elapsed_seconds=elapsed(),counters=counts.copy(),**fields),allow_nan=False)+'\n')
        stream.flush();os.fsync(stream.fileno())


try:
    import psutil
    process=psutil.Process();api=Kernel()
    job_handle=api.check(api.k.OpenJobObjectW(0x0004,False,owner['job_name']))
    need(api.contains(api.k.GetCurrentProcess(),job_handle),'actual worker owned Job')
    class ProcessList(ctypes.Structure):
        _fields_=[('assigned',wintypes.DWORD),('listed',wintypes.DWORD),('pids',ctypes.c_size_t*MAX_PROCESSES)]
    def memory():
        with memory_lock:
            need(elapsed()<80,'same80s worker deadline')
            row=ProcessList()
            api.check(api.k.QueryInformationJobObject(job_handle,3,ctypes.byref(row),ctypes.sizeof(row),None))
            pids=[int(row.pids[i]) for i in range(min(int(row.listed),MAX_PROCESSES))]
            need(0<row.listed==row.assigned<=MAX_PROCESSES and process.pid in pids and len(pids)==len(set(pids)),'complete bounded Job process list')
            family=0
            for pid in pids:
                handle=api.k.OpenProcess(0x1000,False,pid)
                if not handle:
                    need(not psutil.pid_exists(pid),'live family process query denied');resources['exited_during_sample']+=1;continue
                try:
                    need(api.contains(handle,job_handle),'same Job membership at sample')
                    token=api.token(handle);child=psutil.Process(pid)
                    need(abs(child.create_time()-token['create_time'])<=1e-5,'process creation identity')
                    family+=int(child.memory_info().rss)
                except psutil.NoSuchProcess:resources['exited_during_sample']+=1
                finally:api.close(handle)
            info=process.memory_info();worker=max(int(info.rss),int(info.peak_wset));free=int(psutil.virtual_memory().available)
            resources['samples']+=1;resources['peak_worker_rss_bytes']=max(resources['peak_worker_rss_bytes'],worker)
            resources['peak_family_rss_bytes']=max(resources['peak_family_rss_bytes'],family)
            old=resources['minimum_available_ram_bytes'];resources['minimum_available_ram_bytes']=free if old is None else min(old,free)
            resources['maximum_job_processes']=max(resources['maximum_job_processes'],len(pids))
            need(worker<=1024**3 and family<=1024**3 and free>=2*1024**3,'GKT family/worker1GiB/free2GiB')
    memory()
    def watch():
        while not stop.wait(.1):
            try:memory()
            except BaseException as exc:
                monitor_errors.append(str(exc))
                try:write('resource-failure.json',dict(error=str(exc),resources=resources,counters=counts))
                finally:os._exit(125)
    monitor=threading.Thread(target=watch,daemon=True);monitor.start()
    need(system_cmd.is_file() and not system_cmd.is_symlink(),'real System32 cmd')
    real_os=platform.uname();platform.processor();platform.platform()
    os_metadata=dict(system=real_os.system,machine=real_os.machine,release=real_os.release,commands=metadata_commands)
    write('native_metadata.json',os_metadata);phase[0]='native_tests'
    cold={name:not any(key==name or key.startswith(name+'.') for key in sys.modules)
          for name in ('torch','numpy','pandas')}
    need(all(cold.values()),'cold scientific imports before genuine fixture libraries')
    write('cold_canary.json',dict(absent_before_native=cold,owner_pid=os.getpid()))
    sys.path[:0]=[str(ROOT),str(ROOT/'src')]
    import torch
    import numpy as np
    need(torch.__version__=='2.7.1+cpu' and torch.version.cuda is None and torch.cuda.is_initialized() is False
        and np.__version__=='2.5.4' and Path(torch.__file__).resolve().is_relative_to(ROOT/'.venv')
        and Path(np.__file__).resolve().is_relative_to(ROOT/'.venv'),'actual CPU library profile/origins')
    old_threads,old_dtype=torch.get_num_threads(),torch.get_default_dtype()
    need(old_dtype==torch.float32,'CPU FP32 ambient profile, no default-device query')
    torch.set_num_threads(2)
    torch_info=dict(version=torch.__version__,origin=torch.__file__,numpy_version=np.__version__,numpy_origin=np.__file__,cuda_build=torch.version.cuda)
    from knowledge_tracing.gkt import research_model as model,recurrent
    from knowledge_tracing.gkt import research_training as trainer,training as legacy_training
    from knowledge_tracing.sakt import training as sakt_training
    from knowledge_tracing.sakt.model import SAKTCore
    trainer_clock_before=trainer._now
    from knowledge_tracing import simulator_corpus_reader as reader
    need(sha(ROOT/'docs/thesis_recovery/29_GKT_RESEARCH_NUMERICAL_RECIPE_V1.md')==model.RECIPE_SOURCE_SHA256,
        'actual recipe29 bytes match model constant')
    targets=[(model.GKTResearchModel,'__init__'),(model._MaskedOutputMLP,'__init__'),
        (model._MaskedOutputMLP,'forward'),(model.GKTResearchModel,'forward'),
        (model.GKTResearchModel,'sequence'),(model.GKTResearchModel,'predict'),
        (model.GKTResearchModel,'observe'),(torch.nn.Module,'register_parameter'),
        (recurrent.ChoResetBeforeGRU,'forward'),(torch.autograd,'backward'),(torch.autograd,'grad'),
        (torch.nn.utils,'clip_grad_norm_'),(torch.optim.Optimizer,'__init__'),(torch.optim.Adam,'__init__'),
        (torch.optim.Adam,'step'),(torch.optim.AdamW,'__init__'),(torch.optim.AdamW,'step'),
        (torch.optim.SGD,'__init__'),(torch.optim.SGD,'step'),(torch,'save'),(torch,'load'),
        (reader,'read_public_research_corpus'),(legacy_training,'train_gkt_batch'),
        (sakt_training,'train_synthetic_sakt'),(SAKTCore,'__init__'),(SAKTCore,'forward'),
        (recurrent.GKTStaticRecurrentCandidate,'__init__'),
        (trainer,'train_research_epoch'),(trainer,'predict_research_gkt'),(trainer,'score_raw_predictions'),
        (torch.cuda,'is_available'),(torch.cuda,'is_initialized'),
        *[(torch.cuda,n) for n in ('init','_lazy_init','set_device','synchronize','manual_seed','manual_seed_all')],
        (torch.Tensor,'cuda'),(torch.nn.Module,'cuda')]
    patches.capture_many(targets)
    register=torch.nn.Module.register_parameter
    def registered(self,name,parameter):
        tick('parameter_registrations')
        if parameter is not None:tick('nonnull_parameter_registrations')
        return register(self,name,parameter)
    patches.patch(torch.nn.Module,'register_parameter',registered)
    real_ctor=model.GKTResearchModel.__init__
    def ctor(self,*args,**kwargs):
        tick('model_ctor_attempts');before=counts['parameter_registrations'];ctor_depth[0]+=1
        try:
            result=real_ctor(self,*args,**kwargs);tick('model_ctor_returns')
            parameters=dict(self.named_parameters())
            need(len(parameters)==32 and sum(p.numel() for p in parameters.values())==24700,'model24700/32')
            need(all(p.device.type=='cpu' and p.dtype==torch.float32 for p in parameters.values()),'CPU FP32 parameters')
            shape_proofs.append(dict(elements=24700,named_parameters=32,registration_delta=counts['parameter_registrations']-before))
            last_model[0]=weakref.ref(self);model_refs.append(last_model[0]);return result
        finally:ctor_depth[0]-=1
    patches.patch(model.GKTResearchModel,'__init__',ctor)
    real_mlp=model._MaskedOutputMLP.__init__
    def mlp_ctor(self,*args,**kwargs):
        need(ctor_depth[0]>0,'no standalone neural fixtures in trainer8')
        tick('nested_mlp_ctors');return real_mlp(self,*args,**kwargs)
    patches.patch(model._MaskedOutputMLP,'__init__',mlp_ctor)
    def wrap_model(name,original):
        @functools.wraps(original)
        def call(self,*args,**kwargs):
            tick(name+'_attempts')
            if name=='forward' and self.training and torch.is_grad_enabled():
                last_training_targets[0]=int(args[2].sum())
                need(last_training_targets[0]==16,'declared manufactured training batch16targets')
            result=original(self,*args,**kwargs);tick(name+'_returns');return result
        return call
    for name in ('forward','sequence','predict'):
        patches.patch(model.GKTResearchModel,name,wrap_model(name,getattr(model.GKTResearchModel,name)))
    real_observe=model.GKTResearchModel.observe
    def observe(self,state,ids,answers,mask,**kwargs):
        tick('observe_attempts');valid=int(mask.sum());slots=int(mask.numel())
        need(mask.dtype==torch.bool and mask.device.type=='cpu' and 1<=slots<=4,'bounded manufactured observe')
        result=real_observe(self,state,ids,answers,mask,**kwargs);tick('observe_returns')
        tick('valid_learner_events',valid);tick('masked_learner_slots',slots-valid)
        return result
    patches.patch(model.GKTResearchModel,'observe',observe)
    real_mlp_forward=model._MaskedOutputMLP.forward
    def mlp_forward(self,rows):
        tick('mlp_forwards');return real_mlp_forward(self,rows)
    patches.patch(model._MaskedOutputMLP,'forward',mlp_forward)
    real_gru=recurrent.ChoResetBeforeGRU.forward
    def gru(self,inputs,previous):
        tick('gru_forwards');return real_gru(self,inputs,previous)
    patches.patch(recurrent.ChoResetBeforeGRU,'forward',gru)
    def current_model():
        value=last_model[0]() if last_model[0] is not None else None
        need(value is not None,'actual live owned model witness');return value
    real_backward=torch.autograd.backward
    def backward(*args,**kwargs):
        tick('backward_started');result=real_backward(*args,**kwargs);tick('backward_returned')
        present=[(n,p.grad) for n,p in current_model().named_parameters() if p.grad is not None]
        need(present and all(bool(torch.isfinite(g).all()) for n,g in present),'finite participating gradients')
        nonzero=[n for n,g in present if bool((g!=0).any())]
        need(nonzero,'nonzero actual gradient witness')
        gradient_proofs.append(dict(node=active_node[0],names=[n for n,g in present],nonzero_names=nonzero))
        return result
    patches.patch(torch.autograd,'backward',backward)
    real_clip=torch.nn.utils.clip_grad_norm_
    def clip(*args,**kwargs):
        tick('clip_started');result=real_clip(*args,**kwargs);tick('clip_returned')
        gradients=[p.grad for p in current_model().parameters() if p.grad is not None]
        post=math.sqrt(math.fsum(float(g.detach().double().square().sum()) for g in gradients))
        need(bool(torch.isfinite(result)) and math.isfinite(post) and post<=1.00001,'actual live postclip L2<=1')
        clip_proofs.append(dict(node=active_node[0],native_returned_norm=float(result),actual_postclip_l2=post))
        return result
    patches.patch(torch.nn.utils,'clip_grad_norm_',clip)
    real_base_ctor=torch.optim.Optimizer.__init__
    def base_ctor(self,*args,**kwargs):
        need(type(self) is torch.optim.Adam,'only owned native Adam base ctor')
        tick('optimizer_base_ctors');return real_base_ctor(self,*args,**kwargs)
    patches.patch(torch.optim.Optimizer,'__init__',base_ctor)
    real_adam_ctor=torch.optim.Adam.__init__
    def adam_ctor(self,*args,**kwargs):
        tick('adam_ctor_attempts');result=real_adam_ctor(self,*args,**kwargs);tick('adam_ctor_returns')
        expected={id(p) for p in current_model().parameters()}
        actual=[p for group in self.param_groups for p in group['params']]
        need(len(actual)==len(expected)==32 and {id(p) for p in actual}==expected,'actual Adam owns32registered parameters')
        return result
    patches.patch(torch.optim.Adam,'__init__',adam_ctor)
    real_step=torch.optim.Adam.step
    @functools.wraps(real_step)
    def adam_step(self,*args,**kwargs):
        tick('adam_step_started');native=current_model();parameters=dict(native.named_parameters())
        actual=[p for group in self.param_groups for p in group['params']]
        need(len(actual)==32 and {id(p) for p in actual}=={id(p) for p in parameters.values()},'actual step ownership')
        before={name:p.detach().clone() for name,p in parameters.items()}
        result=real_step(self,*args,**kwargs);tick('adam_step_returned')
        tick('actual_optimized_target_exposures',last_training_targets[0])
        changed=[name for name,p in parameters.items() if not torch.equal(before[name],p)]
        need(changed,'atleastone real parameter update')
        need(all(s['step'].dtype==torch.float32 and s['step'].ndim==0 for s in self.state.values() if s),'actual ordinary Adam stepFP32')
        step_proofs.append(dict(node=active_node[0],targets=last_training_targets[0],changed_names=changed))
        return result
    patches.patch(torch.optim.Adam,'step',adam_step)
    def project_phase(name,result,before):
        after=result['counters']
        phase_proofs.append(dict(api=name,node=active_node[0],status=result['status'],complete=result['complete'],
            deltas={key:after[key]-before[key] for key in before},pending_batch_targets=len(result['pending_batch_keys']),
            unreturned_sequence_work=result['unreturned_sequence_work'],rollback=result['rollback'],
            raw_prediction_rows=len(result['predictions']),
            raw_null_rows=sum(row['probability'] is None for row in result['predictions'])))
    def wrap_phase(name,original):
        @functools.wraps(original)
        def call(*args,**kwargs):
            tick(name+'_attempts');progress=kwargs['progress'];before=progress.counters.copy()
            try:result=original(*args,**kwargs)
            except trainer.GKTResearchExecutionError as exc:
                tick(name+'_execution_errors');project_phase(name,exc.result,before);raise
            except ValueError:
                tick(name+'_value_errors');raise
            except KeyboardInterrupt:
                tick(name+'_interrupts')
                need(progress.poisoned is True,'original cancellation must poison cumulative progress')
                phase_proofs.append(dict(api=name,node=active_node[0],status='ORIGINAL_KEYBOARDINTERRUPT_RETHROWN',
                    poisoned=True,deltas={key:progress.counters[key]-before[key] for key in before},
                    structured_result_available=False,inner_work='unknown in API; independent method counters retained'))
                raise
            tick(name+'_returns');project_phase(name,result,before);return result
        return call
    for name in ('train_research_epoch','predict_research_gkt'):
        patches.patch(trainer,name,wrap_phase(name,getattr(trainer,name)))
    real_score=trainer.score_raw_predictions
    def score(*args,**kwargs):
        tick('score_attempts')
        try:result=real_score(*args,**kwargs)
        except ValueError:tick('score_value_errors');raise
        tick('score_returns');return result
    patches.patch(trainer,'score_raw_predictions',score)
    def forbidden_call(label,counter=None):
        def call(*args,**kwargs):
            if counter is not None:counts[counter]+=1
            deny(label)
        return call
    for obj,name,label,counter in ((torch.autograd,'grad','extra autograd.grad',None),
        (torch.optim.AdamW,'__init__','AdamW ctor','other_optimizer_attempts'),
        (torch.optim.AdamW,'step','AdamW step','other_optimizer_attempts'),
        (torch.optim.SGD,'__init__','SGD ctor','other_optimizer_attempts'),
        (torch.optim.SGD,'step','SGD step','other_optimizer_attempts'),
        (torch,'save','checkpoint save','checkpoint_save_attempts'),(torch,'load','checkpoint load','checkpoint_load_attempts'),
        (reader,'read_public_research_corpus','actual corpus reader','corpus_reader_attempts'),
        (legacy_training,'train_gkt_batch','oldtoy trainer body',None),(sakt_training,'train_synthetic_sakt','SAKT toy body',None),
        (SAKTCore,'__init__','SAKT constructor',None),(SAKTCore,'forward','SAKT forward',None),
        (recurrent.GKTStaticRecurrentCandidate,'__init__','old engineering GKT constructor',None)):
        patches.patch(obj,name,forbidden_call(label,counter))
    cuda_queries=[]
    for name in ('is_available','is_initialized'):
        original=getattr(torch.cuda,name)
        def query(*args,original=original,name=name,**kwargs):
            need(len(cuda_queries)<64,'bounded real CPU availability queries');value=original(*args,**kwargs)
            cuda_queries.append(dict(kind=name,value=value));need(value is False,'actual CUDA metadata false');return value
        patches.patch(torch.cuda,name,query)
    for name in ('init','_lazy_init','set_device','synchronize','manual_seed','manual_seed_all'):
        patches.patch(torch.cuda,name,forbidden_call('CUDA execution '+name))
    patches.patch(torch.Tensor,'cuda',forbidden_call('Tensor.cuda'));patches.patch(torch.nn.Module,'cuda',forbidden_call('Module.cuda'))
    import pytest
    from _pytest.junitxml import mangle_test_address
    class Plugin:
        def pytest_collection_finish(self,session):
            nodes.extend(item.nodeid for item in session.items)
            need(nodes==packet['expected_nodeids'] and len(nodes)==8 and not any(counts.values()),'exact fresh8 collection before bodies')
            write('collection.json',dict(nodeids=nodes,counters=counts.copy()))
        def pytest_runtest_logstart(self,nodeid,location):
            active_node[0]=nodeid
            journal('test_start',nodeid=nodeid)
        def pytest_runtest_logreport(self,report):journal(report.when,nodeid=report.nodeid,outcome=report.outcome)
    need(not BASE.exists(),'fresh basetemp before Pytest deletion API')
    with (OUT/'pytest.log').open('x',encoding='utf-8') as log,redirect_stdout(log),redirect_stderr(log):
        rc=int(pytest.main(['tests/gkt/test_research_training.py','--noconftest','-p','no:terminal','-p','no:cacheprovider',
            '-o','addopts=','--basetemp',str(BASE),'--log-file='+str(OUT/'pytest-file.log'),'--junitxml',str(OUT/'junit.xml')],plugins=[Plugin()]))
    memory()
    need(not any(key=='pandas' or key.startswith('pandas.') for key in sys.modules),'no pandas dataset loading')
    need(trainer._now is trainer_clock_before,'fixture fake clock restored, watchdog uses captured real clocks')
    need(counts==caps and len(shape_proofs)==8 and len(gradient_proofs)==len(clip_proofs)==len(step_proofs)==4,
        'exact finite trainer/model/Adam workload')
    training=[row for row in phase_proofs if row['api']=='train_research_epoch']
    prediction=[row for row in phase_proofs if row['api']=='predict_research_gkt']
    need(len(training)==7 and len(prediction)==4,'six ordinary train results plus original cancellation, four raw results')
    need(sum(row['deltas']['input_targets'] for row in phase_proofs)==225
        and sum(row['deltas']['input_prefix_events'] for row in phase_proofs)==326
        and sum(row['deltas']['sequence_started'] for row in phase_proofs)==10
        and sum(row['deltas']['sequence_returned'] for row in phase_proofs)==8,
        'cumulative API input and partial-sequence accounting')
    need(sum(row['deltas']['adam_returned'] for row in training)==3
        and sum(row['deltas']['optimized_targets'] for row in training)==48,
        'API confirmed returned Adam3/optimized48 distinct from actual observer4/64')
    need(sum(row.get('pending_batch_targets',0) for row in training
             if row['deltas']['adam_started']>row['deltas']['adam_returned'])==16,
        'actual late-step failure pending16, not zero work or API-confirmed optimization')
    cancelled=[row for row in training if row['status']=='ORIGINAL_KEYBOARDINTERRUPT_RETHROWN']
    need(len(cancelled)==1 and cancelled[0]['poisoned'] is True
        and cancelled[0]['structured_result_available'] is False
        and cancelled[0]['deltas']['sequence_started']==1 and cancelled[0]['deltas']['sequence_returned']==0
        and cancelled[0]['deltas']['adam_started']==cancelled[0]['deltas']['adam_returned']==0,
        'original cancellation has poisoned progress and unknown unreturned inner work, no result assumption')
    need(sum(row['raw_prediction_rows'] for row in prediction)==32
        and sum(row['raw_null_rows'] for row in prediction)==4,'full raw population32 includes four null OOV suffix rows')
except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc))
finally:
    stop.set()
    if monitor is not None:monitor.join(timeout=.5)
    if job_handle is not None and (monitor is None or not monitor.is_alive()):
        try:api.close(job_handle);job_query_closed=True
        except BaseException as exc:error=error or dict(type=type(exc).__name__,message=str(exc))
    try:restoration=patches.restore()
    except BaseException as exc:error=error or dict(type=type(exc).__name__,message=str(exc))
    try:
        if old_threads is not None:torch.set_num_threads(old_threads)
        if old_dtype is not None:need(torch.get_default_dtype()==old_dtype,'dtype restored by fixtures')
        if torch_info is not None:torch_info['cuda_initialized_after']=torch.cuda.is_initialized()
    except BaseException as exc:error=error or dict(type=type(exc).__name__,message=str(exc))
    for name,value in env_before.items():
        if value is None:os.environ.pop(name,None)
        else:os.environ[name]=value
    tempfile.tempdir=temp_before;sys.pycache_prefix=cache_before
    try:
        cases=list(ET.parse(OUT/'junit.xml').iter('testcase'))
        actual_counts=dict(tests=len(cases),failures=sum(len(list(c.iter('failure'))) for c in cases),
            errors=sum(len(list(c.iter('error'))) for c in cases),skipped=sum(len(list(c.iter('skipped'))) for c in cases))
        ids=[(c.get('classname'),c.get('name')) for c in cases]
        need(len(ids)==len(set(ids))==8 and ids==[('tests.gkt.test_research_training',n.split('::',1)[1]) for n in packet['expected_nodeids']],'exact8JUnit identities')
    except BaseException as exc:xml_error=dict(type=type(exc).__name__,message=str(exc))
    after={n:sha(safe(ROOT/n)) for n in pins};r_after={n:sha(Path(n)) for n in runtime}
    restored=env_before=={n:os.environ.get(n) for n in env_keys} and tempfile.tempdir==temp_before and sys.pycache_prefix==cache_before
    accepted=(error is None and xml_error is None and rc==0 and actual_counts==dict(tests=8,failures=0,errors=0,skipped=0)
        and counts==caps and not forbidden and not monitor_errors and job_query_closed and (monitor is None or not monitor.is_alive())
        and restoration is not None and restoration['accepted'] is True and after==pins and r_after==runtime and restored
        and torch_info is not None and torch_info['cuda_initialized_after'] is False and elapsed()<80)
    write('result.json',dict(status='ACCEPTED_GKT8_TRAINER_CPU_COMPUTE_PENDING_OUTER' if accepted else 'REJECTED_GKT_KEEP_ALL',
        counts=actual_counts,pytest_exit_code=rc,error=error,junit_error=xml_error,counters=counts,expected_counters=caps,
        shape_proofs=shape_proofs,gradient_proofs=gradient_proofs,clip_proofs=clip_proofs,step_proofs=step_proofs,
        phase_proofs=phase_proofs,source_before=pins,source_after=after,
        runtime_before=runtime,runtime_after=r_after,nodeids=nodes,resources=resources,forbidden=forbidden,monitor_errors=monitor_errors,
        monitor_stopped=monitor is None or not monitor.is_alive(),job_query_handle_closed=job_query_closed,
        method_restoration=restoration,environment_restored=restored,torch_profile=torch_info,
        cuda_false_queries=cuda_queries if 'cuda_queries' in globals() else [],elapsed_seconds=elapsed(),cap_seconds=80,
        model11_result_sha256=sys.argv[2],job_query_proof_sha256=probe_ref['sha256'],
        trainer_clock_restored='trainer_clock_before' in globals() and trainer._now is trainer_clock_before,
        recipe_semantics='manufactured_compute_only_actual_Adam4_not_corpus_fit_or_authority'))
    if elapsed()>=80:write('postwrite_rejection.json',dict(elapsed_seconds=elapsed()));accepted=False
    timer.cancel()
raise SystemExit(0 if accepted else 1)
