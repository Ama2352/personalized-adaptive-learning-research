"""Intentional complete-epoch pause metadata; không execution authority/crash recovery."""
from dataclasses import asdict,dataclass
import hashlib
import json
import math
from pathlib import Path

from . import research_execution as old
from ..simulator_bridge import identity_hash

PAUSE_STATUS='PAUSED_MAIN_SELECTED_COMPLETE_EPOCH'
TERMINAL_STATUS='ACCEPTED_MAIN_SELECTED_INTENTIONAL_PAUSE'
HELPER_SHA256='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'


def need(value,message):
    if not value:raise ValueError(message)


def finite(value):
    need(type(value) in (int,float) and math.isfinite(value) and value>=0,'finite nonnegative duration')


def closed(value,names):
    need(type(value) is dict and set(value)==set(names),'closed selected-pause schema')


@dataclass(frozen=True)
class SelectedPausePolicy:
    after_epoch:int
    original_allocation_sha256:str
    charged_wall_seconds:float
    max_attempts:int
    max_constructors:int
    max_retained_bytes:int

    def __post_init__(self):
        old._positive(self.after_epoch);old._sha(self.original_allocation_sha256);finite(self.charged_wall_seconds)
        need(self.charged_wall_seconds>0 and self.max_attempts==2 and self.max_constructors==3,'one reviewed resume child only')
        old._positive(self.max_retained_bytes)


@dataclass(frozen=True)
class SelectedResumeRequest:
    parent_directory:str
    marker_sha256:str
    terminal_file:str
    terminal_sha256:str
    expected_parent_worker_sha256:str
    expected_parent_request_sha256:str
    expected_parent_execution_spec_sha256:str
    original_allocation_sha256:str
    attempt:int
    max_attempts:int
    max_constructors:int
    max_retained_bytes:int

    def __post_init__(self):
        for value in (self.marker_sha256,self.terminal_sha256,self.expected_parent_worker_sha256,
                      self.expected_parent_request_sha256,self.expected_parent_execution_spec_sha256,
                      self.original_allocation_sha256):old._sha(value)
        old._text(self.parent_directory);old._text(self.terminal_file);old._positive(self.max_retained_bytes)
        need(type(self.attempt) is int and self.attempt==self.max_attempts==2 and self.max_constructors==3,'only second intentional-pause attempt')

    @property
    def identity(self):return identity_hash(asdict(self))


@dataclass(frozen=True)
class SelectedEpochPauseRef:
    status:str
    epoch:int
    marker_file:str
    marker_sha256:str


def _semantic_metadata(metadata):
    value=json.loads(json.dumps(metadata,sort_keys=True,allow_nan=False))
    config=value['research']['native_config']
    for key in ('run_id','output_dir'):config.pop(key)
    value['stage'].pop('config_sha256')
    return value


def semantic_spec(spec):
    return _semantic_metadata(spec.metadata())


def _pinned_json(root,relative,digest,cap):
    old._sha(digest)
    value,actual,_=old._read_json(old._path(root,relative),cap)
    need(actual==digest,'immutable launch/request/result bytes changed')
    return value


def _launch_proof(spec,parent,owned_path,owned,proof,*,expected_worker_sha256,
                  expected_request_sha256,expected_spec_sha256):
    """Chỉ nối bytes/actual helper tokens đã ghi; không query PID đã chết."""
    root=spec.research.native_config.project_root;cap=spec.research.budget.max_input_bytes
    closed(proof,('worker_result_file','worker_result_sha256','request_file','request_sha256',
        'execution_spec_sha256','authorization_file','authorization_sha256','protocol_sha256','ownership'))
    need(proof['request_sha256']==expected_request_sha256 and proof['execution_spec_sha256']==expected_spec_sha256,
         'external expected parent request/spec binding')
    for name in ('worker_result_file','request_file'):
        need(old._path(root,proof[name]).is_relative_to(root/'artifacts/akt/local-tests'),'local reviewed worker/request path')
    auth_path=old._path(root,proof['authorization_file'])
    need(auth_path.is_relative_to(root/'experiments/akt/authorizations') or auth_path.is_relative_to(root/'artifacts/akt'),
         'actual parent authorization path')
    result=_pinned_json(root,proof['worker_result_file'],proof['worker_result_sha256'],cap)
    closed(result,('schema_version','status','execution_spec_sha256','authorization_file','authorization_sha256',
        'request_file','request_sha256','ownership','pause_reference'))
    need(type(result['schema_version']) is int and result['schema_version']==1 and result['status']==PAUSE_STATUS,
         'closed actual pause worker result')
    for key in ('execution_spec_sha256','authorization_file','authorization_sha256','request_file','request_sha256','ownership'):
        need(result[key]==proof[key],'worker result/terminal launch binding')
    _pinned_json(root,proof['request_file'],proof['request_sha256'],cap)
    authorization=_pinned_json(root,proof['authorization_file'],proof['authorization_sha256'],cap)
    invocation,_,_=old._read_json(parent/'invocation.json',cap)
    need(identity_hash(invocation['spec'])==expected_spec_sha256
         and _semantic_metadata(invocation['spec'])==semantic_spec(spec)
         and invocation['authorization_file']==proof['authorization_file']
         and invocation['authorization_sha256']==proof['authorization_sha256'], 'actual parent invocation/spec/auth binding')
    need(authorization['execution_spec_sha256']==expected_spec_sha256
         and authorization['decision']=='AUTHORIZE_BOUNDED_MAIN_SELECTED_INTENTIONAL_PAUSE', 'parent intentional pause authorization')
    pins=proof['protocol_sha256'];closed(pins,('launch.json','ready.json','GO.json'))
    protocol={name:_pinned_json(root,(owned_path.parent/name).relative_to(root).as_posix(),pin,cap)
              for name,pin in pins.items()}
    launch,ready,go=(protocol[name] for name in ('launch.json','ready.json','GO.json'))
    closed(launch,('schema_version','nonce','parent','entry','worker_relative','worker_args','worker_sha256',
        'helper_sha256','job_name','active_deadline','approval_reference','gate_deadline'))
    closed(ready,('schema_version','nonce','worker','parent_pid','entry','prefix','worker_sha256','helper_sha256',
        'argv_sha256','forbidden_imports'))
    ownership=proof['ownership']
    closed(ownership,('status','worker','parent_owner','os_parent_pid','nonce','ready_sha256','job_name','preGO_forbidden_imports'))
    need(type(launch['schema_version']) is type(ready['schema_version']) is int
         and launch['schema_version']==ready['schema_version']==1,'exact helper protocol versions')
    need(ownership['status']=='OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE'
         and ownership['preGO_forbidden_imports']==ready['forbidden_imports']==[], 'actual preGO import gate')
    need(ownership['worker']==ready['worker']==owned['actual_worker']
         and ownership['parent_owner']==launch['parent']==owned['parent'], 'same actual worker/owner token')
    for token in (ownership['worker'],ownership['parent_owner'],owned['popen']):
        closed(token,('pid','created_filetime_100ns','create_time','image'))
        old._positive(token['pid']);finite(token['create_time']);old._text(token['image'])
        need(type(token['created_filetime_100ns']) is str and token['created_filetime_100ns'].isdigit(),'native FILETIME token')
    expected_parent=(owned['parent']['pid'] if owned['actual_worker']['pid']==owned['popen']['pid'] else owned['popen']['pid'])
    need(owned['actual_worker']['pid']!=owned['popen']['pid'] or owned['actual_worker']==owned['popen'],'direct worker exact native token')
    need(ready['parent_pid']==ownership['os_parent_pid']==expected_parent,'direct worker or venv shim parent PID')
    old._sha(launch['nonce'])
    need(launch['nonce']==ready['nonce']==ownership['nonce'] and launch['job_name']==ownership['job_name']==owned['job_name']
         and launch['job_name']=='KLTN_OWNED_'+launch['nonce'], 'same launch nonce/job')
    expected_go=dict(nonce=launch['nonce'],ready_sha256=pins['ready.json'],worker=ownership['worker'],job_name=launch['job_name'])
    need(go==expected_go and ownership['ready_sha256']==pins['ready.json'],'exact same GO/ready binding')
    need(owned['status']=='ACCEPTED_OWNED_PROCESS_LAUNCH_NOT_SCIENTIFIC_ACCEPTANCE'
         and owned['GO_released'] is True and owned['worker_returncode_before_cleanup']==0,'genuine released terminal worker')
    entry=root/'.venv/Scripts/python.exe'
    need(Path(launch['entry'])==Path(ready['entry'])==entry and Path(ready['prefix'])==root/'.venv','fixed actual venv entry/prefix')
    old._path(root,entry.relative_to(root).as_posix())
    worker=old._path(root,launch['worker_relative'])
    need(worker.is_relative_to(root/'artifacts/akt/local-tests') or worker.is_relative_to(root/'scripts/research'),'reviewed worker source location')
    need(old._hash_file(worker,cap=256*1024)[0]==launch['worker_sha256']==ready['worker_sha256']==owned['worker_sha256']==expected_worker_sha256
         and launch['helper_sha256']==ready['helper_sha256']==owned['helper_sha256']==HELPER_SHA256,'exact genuine worker/helper sources')
    args=['--request',proof['request_file'],'--request-sha256',proof['request_sha256'],
          '--approval-reference',launch['approval_reference']]
    argv_digest=hashlib.sha256(json.dumps(args,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
    need(launch['worker_args']==args and ready['argv_sha256']==argv_digest
         and owned['approval_reference']==launch['approval_reference']
         and owned['command']==[launch['entry'],'-B',str(worker),*args],'exact actual launch request/argv')
    return result


def reference(value,root):
    from .research_graph_checkpoint import GraphCheckpointRef
    closed(value,('directory','complete_sha256','metadata_sha256','checkpoint_sha256'))
    directory=Path(value['directory'])
    need(directory.is_absolute() and directory.is_relative_to(root/'experiments/akt/results'),'parent CP within results')
    old._path(root,directory.relative_to(root).as_posix())
    for name in ('complete_sha256','metadata_sha256','checkpoint_sha256'):old._sha(value[name])
    return GraphCheckpointRef(directory,value['complete_sha256'],value['metadata_sha256'],value['checkpoint_sha256'])


def validate_history(history,state,train_targets):
    need(type(history) is list and len(history)==state['epoch'] and history,'continuous nonempty epoch history')
    for epoch,row in enumerate(history,1):
        need(type(row['epoch']) is int and row['epoch']==epoch
             and row['epoch_objective']=='native_torch_bce_float32_exported_supported_mean_v1','epoch/objective mismatch')
        loss=row['raw_selection']['native_bce_mean'];finite(loss)
        receipt=row['receipt']
        need(receipt['completed_epochs']==epoch and receipt['epoch_targets']==train_targets
             and receipt['optimized_targets']==epoch*train_targets,'full epoch/target history')
        old._sha(row['raw_prediction_semantic_sha256'])
    need(type(state['best_epoch']) is int and 1<=state['best_epoch']<=state['epoch'],'best epoch within history')


def replay_stopper(history,config,stored):
    # Lazy genuine class, after actual admission; no hand-written selection rule.
    from .training import EarlyStopping
    stopper=EarlyStopping(config.patience,config.min_delta)
    for row in history:
        need(stopper.stale_epochs<stopper.patience,'history continues after natural stop')
        stopper.observe(row['epoch'],row['raw_selection']['native_bce_mean'])
    need(asdict(stopper)==stored and stopper.stale_epochs<stopper.patience
         and stopper.last_epoch<config.max_epochs,'exact continuing stopper state required')
    return stopper


def inspect_parent(spec,request):
    """Byte/metadata consistency only; genuine factory additionally checks authority/current inputs."""
    need(type(request) is SelectedResumeRequest,'typed resume request')
    request.__post_init__();root=spec.research.native_config.project_root;b=spec.research.budget
    parent=old._path(root,request.parent_directory)
    need(parent.parent==root/'experiments/akt/results' and parent!=spec.research.native_config.output_dir,'different direct results parent')
    terminal_path=old._path(root,request.terminal_file)
    need(terminal_path.is_relative_to(root/'artifacts/akt/local-tests'),'owned Root terminal receipt location')
    terminal,pin,_=old._read_json(terminal_path,b.max_input_bytes)
    closed(terminal,('schema_version','status','parent_directory','marker_file','marker_sha256','owned_receipt_file',
        'owned_receipt_sha256','outputs','charged_wall_seconds','charged_training_seconds','constructors','attempt','launch_proof'))
    need(pin==request.terminal_sha256 and terminal['schema_version']==1 and terminal['status']==TERMINAL_STATUS
         and terminal['parent_directory']==request.parent_directory and terminal['marker_sha256']==request.marker_sha256
         and terminal['attempt']==1,'actual bound first intentional-pause terminal')
    owned_path=old._path(root,terminal['owned_receipt_file'])
    need(owned_path.parent==terminal_path.parent,'owned receipt colocated with terminal')
    owned,owned_pin,_=old._read_json(owned_path,b.max_input_bytes)
    need(owned_pin==terminal['owned_receipt_sha256'] and owned['accepted'] is True and owned['returncode']==0
         and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup']==0
         and owned['actual_worker_in_job_before_GO'] is True and owned['popen_handle_closed'] is True
         and owned['cleanup_errors']==owned['errors']==[] and owned['worker_sha256']==request.expected_parent_worker_sha256
         and owned['helper_sha256']==HELPER_SHA256,'genuine owned terminal/cleanup/source binding')
    need(not (terminal_path.parent/'postwrite_rejection.json').exists(),'no terminal deadline rejection')
    worker_result=_launch_proof(spec,parent,owned_path,owned,terminal['launch_proof'],
        expected_worker_sha256=request.expected_parent_worker_sha256,
        expected_request_sha256=request.expected_parent_request_sha256,
        expected_spec_sha256=request.expected_parent_execution_spec_sha256)
    need(worker_result['pause_reference']==dict(status=PAUSE_STATUS,epoch=worker_result['pause_reference']['epoch'],
        marker_file=terminal['marker_file'],marker_sha256=terminal['marker_sha256']),'actual worker returned exact pause marker')
    for name in ('charged_wall_seconds','charged_training_seconds'):finite(terminal[name])
    need(terminal['charged_wall_seconds']>=owned['elapsed_seconds'] and terminal['constructors']==dict(model=1,adam=1),'parent charges/physical construction')
    outputs=terminal['outputs'];need(type(outputs) is dict and 0<len(outputs)<=256,'bounded full parent output inventory')
    actual=set();pending=[parent];directories=0
    while pending:
        directory=pending.pop();directories+=1;need(directories<=128,'bounded parent directories')
        for path in directory.iterdir():
            need(not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(),'no parent output aliases')
            if path.is_dir():pending.append(path)
            else:actual.add(path.relative_to(parent).as_posix());need(len(actual)<=256,'bounded parent files')
    need(actual==set(outputs) and not any(Path(n).name in ('failure.json','postwrite_rejection.json') for n in actual),'exact clean parent output population')
    total=0
    for name,row in outputs.items():
        closed(row,('sha256','bytes'));old._sha(row['sha256'])
        need(type(row['bytes']) is int and row['bytes']>=0,'nonnegative output size')
        path=old._path(parent,name)
        digest,size=old._hash_file(path,cap=max(b.max_checkpoint_bytes,b.max_prediction_bytes))
        need(digest==row['sha256'] and size==row['bytes'],'parent output changed');total+=size
        need(total<=request.max_retained_bytes<=spec.max_output_bytes,'cumulative retained output quota')
    marker_path=old._path(root,terminal['marker_file'])
    need(marker_path.is_relative_to(parent) and marker_path.name=='COMPLETE.json','pause marker within parent')
    marker,marker_pin,_=old._read_json(marker_path,b.max_input_bytes)
    closed(marker,('schema_version','status','epoch','files_sha256','latest_complete_sha256','best_complete_sha256'))
    need(marker_pin==request.marker_sha256 and marker['status']==PAUSE_STATUS and marker['schema_version']==1
         and set(marker['files_sha256'])=={'state.json','history.json','accounting.json'},'exact pause marker')
    values={}
    for name,digest in marker['files_sha256'].items():
        value,actual_pin,_=old._read_json(marker_path.parent/name,b.max_input_bytes)
        need(actual_pin==digest,'pause sidecar SHA');values[name]=value
    state=values['state.json'];history=values['history.json'];accounting=values['accounting.json']
    closed(state,('epoch','next_epoch','best_epoch','latest','best','initial_model_sha256','initial_backbone_sha256',
        'semantic_spec','checkpoint_identity','checkpoint_profile','stopper','policy'))
    closed(history,('epochs',));closed(accounting,('steps','targets','training_seconds','output_bytes_before_pause',
        'journal_sha256','journal_bytes','constructors','attempt'))
    need(type(state['epoch']) is int and 1<=state['epoch']<spec.research.native_config.max_epochs
         and type(state['next_epoch']) is int and state['epoch']==marker['epoch']
         and state['next_epoch']==state['epoch']+1 and state['semantic_spec']==semantic_spec(spec),'same current semantic spec/next epoch')
    policy=SelectedPausePolicy(**state['policy'])
    need(policy.after_epoch==state['epoch']==worker_result['pause_reference']['epoch'],'exact declared/returned pause epoch')
    need(policy.original_allocation_sha256==request.original_allocation_sha256==spec.stage.context.allocation_sha256
         and policy.max_attempts==request.max_attempts and policy.max_constructors==request.max_constructors
         and policy.max_retained_bytes==request.max_retained_bytes==spec.max_output_bytes,'same original allocation/finite lineage quota')
    need(policy.charged_wall_seconds==terminal['charged_wall_seconds'],'declared conservative whole parent charge')
    for name in ('steps','targets'):
        row=accounting[name];closed(row,('reserved','returned','complete'))
        need(all(type(n) is int and n>0 for n in row.values()) and len(set(row.values()))==1,'no pending reservation/body/commit')
    finite(accounting['training_seconds'])
    need(accounting['training_seconds']==terminal['charged_training_seconds'],'parent training duration binding')
    need(accounting['steps']['complete']<b.max_optimizer_steps
         and accounting['targets']['complete']+b.train_targets<=b.max_optimized_targets
         and accounting['training_seconds']<b.max_training_seconds
         and terminal['charged_wall_seconds']<b.max_wall_seconds,'remaining complete-epoch cumulative budget before construction')
    need(accounting['constructors']==terminal['constructors'] and accounting['attempt']==terminal['attempt'],'actual parent constructor/attempt accounting')
    journal=parent/'events.jsonl';journal_pin,journal_size=old._hash_file(journal,cap=spec.max_output_bytes)
    need(journal_pin==accounting['journal_sha256'] and journal_size==accounting['journal_bytes'],'no post-boundary journal activity')
    validate_history(history['epochs'],state,b.train_targets)
    latest=reference(state['latest'],root);best=reference(state['best'],root)
    need(latest.directory.is_relative_to(parent) and best.directory.is_relative_to(parent)
         and latest.complete_sha256==marker['latest_complete_sha256'] and best.complete_sha256==marker['best_complete_sha256'],'parent-only latest/best refs')
    for ref,epoch in ((latest,state['epoch']),(best,state['best_epoch'])):
        meta,meta_pin,_=old._read_json(ref.directory/'metadata.json',b.max_prediction_bytes)
        need(meta_pin==ref.metadata_sha256 and meta['receipt']['completed_epochs']==epoch,'latest/best exact CP epoch')
    latest_meta,_,_=old._read_json(latest.directory/'metadata.json',b.max_prediction_bytes)
    need(latest_meta['receipt']['optimizer_body_returns']==accounting['steps']['complete']
         and latest_meta['receipt']['optimized_targets']==accounting['targets']['complete'],'checkpoint/cumulative ledger binding')
    return dict(state=state,history=history['epochs'],accounting=accounting,terminal=terminal,retained_bytes=total)


def control_binding(spec,control):
    policy,request=control
    need(policy is None or type(policy) is SelectedPausePolicy,'typed intentional pause policy')
    need(request is None or type(request) is SelectedResumeRequest,'typed resume request')
    need(policy is not None or request is not None,'explicit selected control')
    c=spec.research.native_config
    need(spec.cuda_profile is None and c.device=='cpu' and c.recovery is None,'CPU complete-epoch only, no generic recovery')
    if policy is not None:
        policy.__post_init__();need(policy.after_epoch<c.max_epochs and policy.original_allocation_sha256==spec.stage.context.allocation_sha256,'pause before natural maximum')
        need(policy.max_retained_bytes==spec.max_output_bytes and policy.charged_wall_seconds<spec.research.budget.max_wall_seconds,'exact retained quota and bounded pause allocation')
    if request is not None:
        request.__post_init__()
        need(request.max_retained_bytes==spec.max_output_bytes,'exact original retained quota')
    return dict(mode='pause' if request is None else 'resume',pause_policy=None if policy is None else asdict(policy),
        request=None if request is None else asdict(request),request_sha256=None if request is None else request.identity)


def check_parent_refs(spec,request,parent):
    root=spec.research.native_config.project_root;cap=spec.research.budget.max_input_bytes
    terminal,pin,_=old._read_json(old._path(root,request.terminal_file),cap)
    need(pin==request.terminal_sha256 and terminal==parent['terminal'],'parent terminal changed')
    marker_pin,_=old._hash_file(old._path(root,terminal['marker_file']),cap=cap)
    owned_pin,_=old._hash_file(old._path(root,terminal['owned_receipt_file']),cap=cap)
    need(marker_pin==request.marker_sha256 and owned_pin==terminal['owned_receipt_sha256'],'parent immutable marker/owner changed')
    proof=terminal['launch_proof']
    for name in ('worker_result','request','authorization'):
        _pinned_json(root,proof[name+'_file'],proof[name+'_sha256'],cap)
    owned_dir=old._path(root,terminal['owned_receipt_file']).parent
    for name,pin in proof['protocol_sha256'].items():
        _pinned_json(root,(owned_dir/name).relative_to(root).as_posix(),pin,cap)


def publish_pause(run,policy,history,latest,best,initial_model,initial_backbone,profile,identity,stopper):
    need(type(policy) is SelectedPausePolicy and run.batch_targets is None and run.training_started is None,'idle complete pause boundary')
    epoch=history[-1]['epoch'];need(epoch==policy.after_epoch and epoch<run.config.max_epochs and stopper.stale_epochs<stopper.patience,'continuing intentional pause only')
    run.event('intentional_pause_boundary',epoch=epoch)
    directory=run.output/'selected-pause'/f'epoch-{epoch}';directory.mkdir(parents=True,exist_ok=False)
    state=dict(epoch=epoch,next_epoch=epoch+1,best_epoch=stopper.best_epoch,latest=asdict(latest),best=asdict(best),
        initial_model_sha256=initial_model,initial_backbone_sha256=initial_backbone,semantic_spec=semantic_spec(run.spec),
        checkpoint_identity=identity,checkpoint_profile=asdict(profile),stopper=asdict(stopper),policy=asdict(policy))
    journal=run.output/'events.jsonl';journal_pin,journal_size=old._hash_file(journal,cap=run.spec.max_output_bytes)
    accounting=dict(steps=dict(reserved=run.reserved_steps,returned=run.returned_steps,complete=run.completed_steps),
        targets=dict(reserved=run.reserved_targets,returned=run.returned_targets,complete=run.completed_targets),
        training_seconds=run.clocks()['training_seconds'],output_bytes_before_pause=run.output_bytes,journal_sha256=journal_pin,journal_bytes=journal_size)
    accounting.update(constructors=dict(model=run.constructors,adam=run.optimizer_constructors),attempt=1 if run.parent is None else 2)
    files={}
    for name,value in (('state.json',state),('history.json',dict(epochs=history)),('accounting.json',accounting)):
        files[name]=run.json((directory/name).relative_to(run.output),value)
    marker=dict(schema_version=1,status=PAUSE_STATUS,epoch=epoch,files_sha256=files,
        latest_complete_sha256=latest.complete_sha256,best_complete_sha256=best.complete_sha256)
    marker_pin=run.json((directory/'COMPLETE.json').relative_to(run.output),marker)
    run.boundary()
    return SelectedEpochPauseRef(PAUSE_STATUS,epoch,(directory/'COMPLETE.json').relative_to(run.config.project_root).as_posix(),marker_pin)


def seal_pause_terminal(spec,*,worker_result_file,owned_receipt_file,destination,expected_worker_sha256,
                        expected_request_file,expected_request_sha256,outer_elapsed_seconds):
    """ROOT outer sau cleanup; metadata seal, không cấp authorization hoặc khởi chạy."""
    root=spec.research.native_config.project_root;b=spec.research.budget
    worker_path=old._path(root,worker_result_file);owned_path=old._path(root,owned_receipt_file);target=old._path(root,destination)
    need(worker_path.is_relative_to(root/'artifacts/akt/local-tests') and owned_path.parent==target.parent
         and target.is_relative_to(root/'artifacts/akt/local-tests') and not target.exists(),'fresh owned outer seal path')
    result,result_pin,_=old._read_json(worker_path,b.max_input_bytes);owned,owned_pin,_=old._read_json(owned_path,b.max_input_bytes)
    old._sha(expected_worker_sha256);finite(outer_elapsed_seconds)
    need(owned['accepted'] is True and owned['returncode']==0 and owned['cleanup_accepted'] is True
         and owned['job_active_after_cleanup']==0 and owned['actual_worker_in_job_before_GO'] is True
         and owned['popen_handle_closed'] is True and owned['errors']==owned['cleanup_errors']==[]
         and owned['worker_sha256']==expected_worker_sha256 and owned['helper_sha256']==HELPER_SHA256,'actual terminal cleanup before pause seal')
    need(not (target.parent/'postwrite_rejection.json').exists(),'no outer postwrite rejection before pause seal')
    closed(result,('schema_version','status','execution_spec_sha256','authorization_file','authorization_sha256',
        'request_file','request_sha256','ownership','pause_reference'))
    need(result['status']==PAUSE_STATUS and result['request_file']==expected_request_file,'actual worker pause request/result')
    protocol_pins={name:old._hash_file(owned_path.parent/name,cap=b.max_input_bytes)[0]
                   for name in ('launch.json','ready.json','GO.json')}
    proof=dict(worker_result_file=worker_result_file,worker_result_sha256=result_pin,
        request_file=result['request_file'],request_sha256=result['request_sha256'],execution_spec_sha256=result['execution_spec_sha256'],
        authorization_file=result['authorization_file'],authorization_sha256=result['authorization_sha256'],
        protocol_sha256=protocol_pins,ownership=result['ownership'])
    _launch_proof(spec,spec.research.native_config.output_dir,owned_path,owned,proof,
        expected_worker_sha256=expected_worker_sha256,expected_request_sha256=expected_request_sha256,
        expected_spec_sha256=spec.identity)
    reference_value=result['pause_reference'];closed(reference_value,SelectedEpochPauseRef.__dataclass_fields__)
    need(reference_value['status']==PAUSE_STATUS,'typed pause result status')
    marker_path=old._path(root,reference_value['marker_file']);parent=spec.research.native_config.output_dir
    need(marker_path.is_relative_to(parent),'pause marker in exact actual output')
    marker,marker_pin,_=old._read_json(marker_path,b.max_input_bytes)
    need(marker_pin==reference_value['marker_sha256'] and marker['epoch']==reference_value['epoch'],'actual returned marker SHA')
    state,state_pin,_=old._read_json(marker_path.parent/'state.json',b.max_input_bytes)
    accounting,accounting_pin,_=old._read_json(marker_path.parent/'accounting.json',b.max_input_bytes)
    need(state_pin==marker['files_sha256']['state.json'] and accounting_pin==marker['files_sha256']['accounting.json'],'sealed state/accounting bytes')
    policy=SelectedPausePolicy(**state['policy'])
    need(policy.after_epoch==marker['epoch'] and policy.max_retained_bytes==spec.max_output_bytes,'exact parent pause epoch/retained quota')
    need(outer_elapsed_seconds<=policy.charged_wall_seconds and owned['elapsed_seconds']<=outer_elapsed_seconds,'conservative whole-parent wall charge')
    outputs={};total=0;pending=[parent];directory_count=0
    while pending:
        directory=pending.pop();directory_count+=1;need(directory_count<=128,'bounded paused output directories')
        for path in directory.iterdir():
            need(not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(),'no paused output alias')
            if path.is_dir():pending.append(path);continue
            need(path.name not in ('failure.json','postwrite_rejection.json'),'no parent failure after pause marker')
            digest,size=old._hash_file(path,cap=max(b.max_checkpoint_bytes,b.max_prediction_bytes));total+=size
            need(total<=policy.max_retained_bytes and len(outputs)<256,'retained pause output limits')
            outputs[path.relative_to(parent).as_posix()]=dict(sha256=digest,bytes=size)
    value=dict(schema_version=1,status=TERMINAL_STATUS,parent_directory=parent.relative_to(root).as_posix(),
        marker_file=reference_value['marker_file'],marker_sha256=marker_pin,owned_receipt_file=owned_receipt_file,
        owned_receipt_sha256=owned_pin,outputs=outputs,charged_wall_seconds=policy.charged_wall_seconds,
        charged_training_seconds=accounting['training_seconds'],constructors=accounting['constructors'],attempt=accounting['attempt'],launch_proof=proof)
    from .research_runner import _write_json
    return _write_json(target,value,b.max_input_bytes)


def copy_best(reference_value,run,tools,identity,limits):
    ref=reference(reference_value,run.config.project_root)
    tools.cp.inspect_graph_epoch_state(ref.directory,expected_identity=identity,expected_complete_sha256=ref.complete_sha256,limits=limits)
    destination=run.output/'checkpoints'/ref.directory.name
    need(not destination.exists(),'fresh inherited best destination')
    sizes=sum((ref.directory/name).stat().st_size for name in ('state.pt','metadata.json','COMPLETE.json'))
    need(run.output_bytes+sizes<=run.spec.max_output_bytes,'inherited best copy quota')
    destination.mkdir()
    from .recovery import preserve_checkpoint
    inventory=[]
    for name in ('state.pt','metadata.json','COMPLETE.json'):
        source=ref.directory/name;before,_=old._hash_file(source,cap=limits.max_checkpoint_bytes if name=='state.pt' else limits.max_metadata_bytes)
        preserve_checkpoint(source,destination/name)
        after,_=old._hash_file(destination/name,cap=max(limits.max_checkpoint_bytes,limits.max_metadata_bytes))
        need(before==after==old._hash_file(source,cap=max(limits.max_checkpoint_bytes,limits.max_metadata_bytes))[0],'source/copy/source-after exact bytes')
        inventory.append(dict(source=str(source),copy=str(destination/name),sha256=before))
    run.output_bytes+=sizes;run.json('inherited-best-relocation.json',inventory)
    return tools.cp.GraphCheckpointRef(destination,ref.complete_sha256,ref.metadata_sha256,ref.checkpoint_sha256)
