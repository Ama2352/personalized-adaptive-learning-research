"""Manufactured metadata consistency; fake receipts never prove process/runtime authority."""
from dataclasses import asdict,dataclass,replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as N

import pytest

from knowledge_tracing.akt import research_selected_resume as resume
from test_research_main_execution import make_case,auth_value,H


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True)+'\n',encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manufactured_parent(tmp_path,monkeypatch):
    case=make_case(tmp_path,monkeypatch);root=case.root
    parent=root/'experiments/akt/results/parent';parent.mkdir(parents=True)
    journal=parent/'events.jsonl';journal.write_bytes(b'UNIT_METADATA_ONLY_NOT_ACTUAL_OPTIMIZER_EVENTS\n')
    refs=[]
    for epoch in (1,2):
        directory=parent/'checkpoints'/f'epoch-{epoch}';directory.mkdir(parents=True)
        (directory/'state.pt').write_bytes(b'OPAQUE_NOT_TORCH_SAVE')
        meta=dict(receipt=dict(completed_epochs=epoch,optimizer_body_returns=epoch*2,optimized_targets=epoch*24))
        meta_pin=put(directory/'metadata.json',meta)
        complete_pin=put(directory/'COMPLETE.json',dict(manufactured=True))
        refs.append(dict(directory=str(directory),complete_sha256=complete_pin,metadata_sha256=meta_pin,
            checkpoint_sha256=hashlib.sha256((directory/'state.pt').read_bytes()).hexdigest()))
    history=[dict(epoch=e,epoch_objective='native_torch_bce_float32_exported_supported_mean_v1',
        raw_selection=dict(native_bce_mean=loss),raw_prediction_semantic_sha256=H,
        receipt=dict(completed_epochs=e,epoch_targets=24,optimized_targets=e*24)) for e,loss in ((1,.6),(2,.7))]
    policy=resume.SelectedPausePolicy(2,case.spec.stage.context.allocation_sha256,5.,2,3,case.spec.max_output_bytes)
    state=dict(epoch=2,next_epoch=3,best_epoch=1,latest=refs[1],best=refs[0],initial_model_sha256=H,
        initial_backbone_sha256=H,semantic_spec=resume.semantic_spec(case.spec),checkpoint_identity={},checkpoint_profile={},
        stopper=dict(patience=case.spec.research.native_config.patience,min_delta=case.spec.research.native_config.min_delta,
                     best_epoch=1,best_loss=.6,stale_epochs=1,last_epoch=2),policy=asdict(policy))
    accounting=dict(steps=dict(reserved=4,returned=4,complete=4),targets=dict(reserved=48,returned=48,complete=48),
        training_seconds=1.5,output_bytes_before_pause=0,journal_sha256=hashlib.sha256(journal.read_bytes()).hexdigest(),
        journal_bytes=journal.stat().st_size,constructors=dict(model=1,adam=1),attempt=1)
    directory=parent/'selected-pause/epoch-2';directory.mkdir(parents=True)
    files={name:put(directory/name,value) for name,value in
        (('state.json',state),('history.json',dict(epochs=history)),('accounting.json',accounting))}
    marker=dict(schema_version=1,status=resume.PAUSE_STATUS,epoch=2,files_sha256=files,
        latest_complete_sha256=refs[1]['complete_sha256'],best_complete_sha256=refs[0]['complete_sha256'])
    marker_pin=put(directory/'COMPLETE.json',marker)
    owned_dir=root/'artifacts/akt/local-tests/parent-owned';owned_dir.mkdir(parents=True)
    from knowledge_tracing.akt import research_execution as old
    config=replace(case.spec.research.native_config,run_id='parent',output_dir=parent)
    parent_spec=replace(case.spec,research=replace(case.spec.research,native_config=config),
        stage=replace(case.spec.stage,config_sha256=old.native_auth.config_hash(config)))
    auth_file='experiments/akt/authorizations/parent-pause.json'
    authorization=auth_value(N(spec=parent_spec),{})
    authorization.update(decision='AUTHORIZE_BOUNDED_MAIN_SELECTED_INTENTIONAL_PAUSE',
        resume=resume.control_binding(parent_spec,(policy,None)))
    auth_pin=put(root/auth_file,authorization)
    put(parent/'invocation.json',dict(spec=parent_spec.metadata(),authorization_file=auth_file,authorization_sha256=auth_pin))
    request_file=(owned_dir/'request.json').relative_to(root).as_posix()
    request_pin=put(root/request_file,dict(manufactured_metadata_only=True))
    worker_file=root/'artifacts/akt/local-tests/parent-worker.py'
    worker_file.write_bytes(b'MANUFACTURED_NOT_EXECUTED\n')
    worker_pin=hashlib.sha256(worker_file.read_bytes()).hexdigest()
    def token(pid,image):
        return dict(pid=pid,created_filetime_100ns=str(10000+pid),create_time=100.+pid,image=str(image))
    entry=root/'.venv/Scripts/python.exe'
    owner=token(100,root/'base-python.exe');shim=token(101,entry);worker=token(102,root/'base-python.exe')
    nonce='b'*64;job='KLTN_OWNED_'+nonce
    args=['--request',request_file,'--request-sha256',request_pin,'--approval-reference','MANUFACTURED_NOT_AUTHORITY']
    launch=dict(schema_version=1,nonce=nonce,parent=owner,entry=str(entry),worker_relative=worker_file.relative_to(root).as_posix(),
        worker_args=args,worker_sha256=worker_pin,helper_sha256=resume.HELPER_SHA256,job_name=job,
        active_deadline=20.,gate_deadline=10.,approval_reference='MANUFACTURED_NOT_AUTHORITY')
    ready=dict(schema_version=1,nonce=nonce,worker=worker,parent_pid=shim['pid'],entry=str(entry),prefix=str(root/'.venv'),
        worker_sha256=worker_pin,helper_sha256=resume.HELPER_SHA256,
        argv_sha256=hashlib.sha256(json.dumps(args,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),forbidden_imports=[])
    launch_pin=put(owned_dir/'launch.json',launch);ready_pin=put(owned_dir/'ready.json',ready)
    go=dict(nonce=nonce,ready_sha256=ready_pin,worker=worker,job_name=job)
    go_pin=put(owned_dir/'GO.json',go)
    ownership=dict(status='OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE',worker=worker,parent_owner=owner,
        os_parent_pid=shim['pid'],nonce=nonce,ready_sha256=ready_pin,job_name=job,preGO_forbidden_imports=[])
    owned=dict(status='ACCEPTED_OWNED_PROCESS_LAUNCH_NOT_SCIENTIFIC_ACCEPTANCE',
        accepted=True,returncode=0,cleanup_accepted=True,job_active_after_cleanup=0,actual_worker_in_job_before_GO=True,
        popen_handle_closed=True,cleanup_errors=[],errors=[],worker_sha256=worker_pin,helper_sha256=resume.HELPER_SHA256,elapsed_seconds=2.,
        actual_worker=worker,parent=owner,popen=shim,job_name=job,GO_released=True,worker_returncode_before_cleanup=0,
        approval_reference=launch['approval_reference'],command=[str(entry),'-B',str(worker_file),*args])
    owned_pin=put(owned_dir/'receipt.json',owned)
    result_file=(owned_dir/'worker-result.json').relative_to(root).as_posix()
    result=dict(schema_version=1,status=resume.PAUSE_STATUS,execution_spec_sha256=parent_spec.identity,
        authorization_file=auth_file,authorization_sha256=auth_pin,request_file=request_file,request_sha256=request_pin,
        ownership=ownership,pause_reference={})
    proof=dict(worker_result_file=result_file,worker_result_sha256=H,request_file=request_file,request_sha256=request_pin,
        execution_spec_sha256=parent_spec.identity,authorization_file=auth_file,authorization_sha256=auth_pin,
        protocol_sha256={'launch.json':launch_pin,'ready.json':ready_pin,'GO.json':go_pin},ownership=ownership)
    terminal=dict(schema_version=1,status=resume.TERMINAL_STATUS,parent_directory=parent.relative_to(root).as_posix(),
        marker_file=(directory/'COMPLETE.json').relative_to(root).as_posix(),marker_sha256=marker_pin,
        owned_receipt_file=(owned_dir/'receipt.json').relative_to(root).as_posix(),owned_receipt_sha256=owned_pin,
        outputs={},charged_wall_seconds=5.,charged_training_seconds=1.5,constructors=dict(model=1,adam=1),attempt=1,launch_proof=proof)
    value=N(case=case,parent=parent,directory=directory,owned_dir=owned_dir,state=state,history=history,
        accounting=accounting,marker=marker,terminal=terminal,policy=policy,parent_spec=parent_spec,worker_pin=worker_pin,
        result=result,proof=proof,launch=launch,ready=ready,go=go,owned=owned)
    refresh(value)
    return value


def refresh(value):
    root=value.case.root
    value.marker['files_sha256']={name:put(value.directory/name,row) for name,row in
        (('state.json',value.state),('history.json',dict(epochs=value.history)),('accounting.json',value.accounting))}
    marker_pin=put(value.directory/'COMPLETE.json',value.marker)
    value.terminal['marker_sha256']=marker_pin
    value.result['pause_reference']=dict(status=resume.PAUSE_STATUS,epoch=value.marker['epoch'],
        marker_file=value.terminal['marker_file'],marker_sha256=marker_pin)
    value.proof['worker_result_sha256']=put(root/value.proof['worker_result_file'],value.result)
    value.terminal['outputs']={p.relative_to(value.parent).as_posix():dict(bytes=p.stat().st_size,
        sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in value.parent.rglob('*') if p.is_file()}
    terminal_pin=put(value.owned_dir/'final.json',value.terminal)
    value.request=resume.SelectedResumeRequest(value.parent.relative_to(root).as_posix(),marker_pin,
        (value.owned_dir/'final.json').relative_to(root).as_posix(),terminal_pin,value.worker_pin,
        value.proof['request_sha256'],value.parent_spec.identity,
        value.case.spec.stage.context.allocation_sha256,2,2,3,value.case.spec.max_output_bytes)


def test_parent_metadata_distinguishes_latest_from_best_without_torch_load(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch)
    inspected=resume.inspect_parent(value.case.spec,value.request)
    assert inspected['state']['epoch']==2 and inspected['state']['best_epoch']==1
    assert inspected['accounting']['steps']['complete']==4 and inspected['history']==value.history
    assert not hasattr(inspected,'revalidate')  # Returned metadata is not MainSelectedExecution.


@pytest.mark.parametrize('kind',('pending','latest_epoch','history_gap','objective','journal_tail','failure','file_drift','foreign_parent'))
def test_parent_metadata_negatives_before_any_deserializer(tmp_path,monkeypatch,kind):
    value=manufactured_parent(tmp_path,monkeypatch)
    if kind=='pending':value.accounting['steps']['reserved']=5
    elif kind=='latest_epoch':value.state['latest']=value.state['best']
    elif kind=='history_gap':value.history[1]['epoch']=3
    elif kind=='objective':value.history[1]['epoch_objective']='calibrated'
    elif kind=='journal_tail':(value.parent/'events.jsonl').write_bytes(b'POST_BOUNDARY_ACTIVITY')
    elif kind=='failure':put(value.parent/'failure.json',dict(failed=True))
    elif kind=='file_drift':(value.parent/'checkpoints/epoch-2/state.pt').write_bytes(b'changed')
    elif kind=='foreign_parent':value.state['semantic_spec']['research']['native_config']['seed']=43
    if kind not in ('journal_tail','file_drift'):refresh(value)
    with pytest.raises(ValueError):resume.inspect_parent(value.case.spec,value.request)


def test_parent_owned_receipt_failure_does_not_become_clean_pause(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch)
    owned=json.loads((value.owned_dir/'receipt.json').read_bytes());owned['job_active_after_cleanup']=1
    value.terminal['owned_receipt_sha256']=put(value.owned_dir/'receipt.json',owned);refresh(value)
    with pytest.raises(ValueError,match='owned terminal'):resume.inspect_parent(value.case.spec,value.request)


def test_boolean_counters_and_repeated_attempt_are_not_integer_authority(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch)
    value.accounting['steps']=dict(reserved=True,returned=True,complete=True);refresh(value)
    with pytest.raises(ValueError):resume.inspect_parent(value.case.spec,value.request)
    with pytest.raises(ValueError):replace(value.request,attempt=3)


def test_semantic_projection_changes_only_attempt_paths_and_derived_config_sha(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch);spec=value.case.spec
    config=replace(spec.research.native_config,run_id='new',output_dir=value.case.root/'experiments/akt/results/new')
    research=replace(spec.research,native_config=config)
    from knowledge_tracing.akt import research_execution as old
    stage=replace(spec.stage,config_sha256=old.native_auth.config_hash(config))
    changed=replace(spec,research=research,stage=stage)
    assert resume.semantic_spec(changed)==resume.semantic_spec(spec)
    drift=changed.metadata()
    drift['research']['native_config']['lr']*=2
    assert resume.semantic_spec(N(metadata=lambda:drift))!=resume.semantic_spec(spec)


def test_real_stopper_replay_preserves_earliest_tie_and_nonbest_latest(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch)
    stopper=resume.replay_stopper(value.history,value.case.spec.research.native_config,value.state['stopper'])
    assert stopper.best_epoch==1 and stopper.last_epoch==2 and stopper.stale_epochs==1
    tied=[dict(row,raw_selection=dict(native_bce_mean=.6)) for row in value.history]
    assert resume.replay_stopper(tied,value.case.spec.research.native_config,value.state['stopper']).best_epoch==1
    with pytest.raises(ValueError):resume.replay_stopper(value.history,value.case.spec.research.native_config,
        dict(value.state['stopper'],best_epoch=2))


def test_real_stopper_natural_stop_refuses_resume(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch)
    config=replace(value.case.spec.research.native_config,patience=1)
    stored=dict(value.state['stopper'],patience=1)
    with pytest.raises(ValueError,match='continuing stopper'):resume.replay_stopper(value.history,config,stored)


def test_control_binding_is_metadata_and_preserves_default_spec_wire(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch);before=value.case.spec.metadata()
    binding=resume.control_binding(value.case.spec,(None,value.request))
    assert binding['mode']=='resume' and binding['request_sha256']==value.request.identity
    assert value.case.spec.metadata()==before and 'resume' not in before
    assert binding.get('execution_authority') is None


def test_pause_sidecar_failure_cannot_publish_complete_marker(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch)
    output=value.case.spec.research.native_config.output_dir;output.mkdir(parents=True)
    (output/'events.jsonl').write_bytes(b'COMPLETE_EPOCH_FIXTURE_ONLY\n')
    calls=[]
    def write(name,payload):
        calls.append(Path(name).name)
        if Path(name).name=='history.json':raise OSError('manufactured sidecar write failure')
        from knowledge_tracing.akt.research_main_execution import canonical
        return put(output/name,canonical(payload))
    run=N(batch_targets=None,training_started=None,config=value.case.spec.research.native_config,spec=value.case.spec,
        output=output,event=lambda *a,**k:None,reserved_steps=4,returned_steps=4,completed_steps=4,
        reserved_targets=48,returned_targets=48,completed_targets=48,clocks=lambda:dict(training_seconds=1.5),
        output_bytes=0,constructors=1,optimizer_constructors=1,parent=None,json=write,
        boundary=lambda:pytest.fail('failed sidecar cannot reach accepted publication boundary'))
    from knowledge_tracing.akt import research_graph_checkpoint as cp
    latest=cp.GraphCheckpointRef(**(value.state['latest']|{'directory':Path(value.state['latest']['directory'])}))
    best=cp.GraphCheckpointRef(**(value.state['best']|{'directory':Path(value.state['best']['directory'])}))
    profile=cp.GraphCheckpointProfile(H,cp.RECIPE_SHA256,H,H,H,H,'selected_fit_candidate',None)
    @dataclass
    class Stopper:
        best_epoch:int=1
        stale_epochs:int=1
        patience:int=3
    with pytest.raises(OSError,match='sidecar write failure'):
        resume.publish_pause(run,value.policy,value.history,latest,best,H,H,profile,{},Stopper())
    assert calls==['state.json','history.json']
    assert not (output/'selected-pause/epoch-2/COMPLETE.json').exists()


def test_outer_postwrite_rejection_prevents_pause_seal_even_with_clean_job(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch);root=value.case.root
    worker=value.owned_dir/'worker.json';put(worker,dict(status=resume.PAUSE_STATUS,pause_reference={}))
    put(value.owned_dir/'postwrite_rejection.json',dict(rejected=True))
    destination=value.owned_dir/'new-terminal.json'
    with pytest.raises(ValueError,match='outer postwrite rejection'):
        resume.seal_pause_terminal(value.case.spec,worker_result_file=worker.relative_to(root).as_posix(),
            owned_receipt_file=(value.owned_dir/'receipt.json').relative_to(root).as_posix(),
            destination=destination.relative_to(root).as_posix(),expected_worker_sha256=value.worker_pin,
            expected_request_file=value.proof['request_file'],expected_request_sha256=value.proof['request_sha256'],outer_elapsed_seconds=3.)
    assert not destination.exists()


@pytest.mark.parametrize('kind',('steps','targets','training','wall'))
def test_exhausted_original_budget_rejects_parent_before_deserialization(tmp_path,monkeypatch,kind):
    value=manufactured_parent(tmp_path,monkeypatch);budget=value.case.spec.research.budget
    if kind=='steps':
        value.accounting['steps']=dict.fromkeys(('reserved','returned','complete'),budget.max_optimizer_steps)
    elif kind=='targets':
        value.accounting['targets']=dict.fromkeys(('reserved','returned','complete'),budget.max_optimized_targets)
    elif kind=='training':
        value.accounting['training_seconds']=value.terminal['charged_training_seconds']=budget.max_training_seconds
    else:
        value.state['policy']['charged_wall_seconds']=value.terminal['charged_wall_seconds']=budget.max_wall_seconds
    refresh(value)
    with pytest.raises(ValueError,match='remaining complete-epoch cumulative budget'):
        resume.inspect_parent(value.case.spec,value.request)


@pytest.mark.parametrize('kind',('other_job','other_token','expected_request','expected_spec','wrong_GO','stale_result','wrong_argv'))
def test_same_source_crosswired_or_stale_launch_cannot_admit_parent(tmp_path,monkeypatch,kind):
    value=manufactured_parent(tmp_path,monkeypatch)
    if kind in ('other_job','other_token'):
        owned=dict(value.owned)
        if kind=='other_job':owned['job_name']+='-OTHER_OPERATION'
        else:owned['actual_worker']=dict(owned['actual_worker'],create_time=999.)
        assert owned['worker_sha256']==value.worker_pin  # Same source never proves same operation.
        value.terminal['owned_receipt_sha256']=put(value.owned_dir/'receipt.json',owned)
        refresh(value)
    elif kind=='expected_request':value.request=replace(value.request,expected_parent_request_sha256='c'*64)
    elif kind=='expected_spec':value.request=replace(value.request,expected_parent_execution_spec_sha256='c'*64)
    elif kind=='wrong_GO':
        value.go['worker']=dict(value.go['worker'],create_time=999.)
        value.proof['protocol_sha256']['GO.json']=put(value.owned_dir/'GO.json',value.go)
        refresh(value)
    elif kind=='stale_result':
        path=value.case.root/value.proof['worker_result_file'];path.write_bytes(path.read_bytes()+b' ')
    else:
        value.launch['worker_args']=list(value.launch['worker_args']);value.launch['worker_args'][3]='c'*64
        value.proof['protocol_sha256']['launch.json']=put(value.owned_dir/'launch.json',value.launch)
        refresh(value)
    with pytest.raises(ValueError):resume.inspect_parent(value.case.spec,value.request)


def test_direct_worker_without_venv_shim_preserves_actual_parent_rule(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch)
    value.owned['popen']=dict(value.owned['actual_worker'])
    value.ready['parent_pid']=value.owned['parent']['pid']
    value.proof['ownership']['os_parent_pid']=value.owned['parent']['pid']
    ready_pin=put(value.owned_dir/'ready.json',value.ready)
    value.go['ready_sha256']=ready_pin;value.proof['ownership']['ready_sha256']=ready_pin
    value.proof['protocol_sha256']['ready.json']=ready_pin
    value.proof['protocol_sha256']['GO.json']=put(value.owned_dir/'GO.json',value.go)
    value.terminal['owned_receipt_sha256']=put(value.owned_dir/'receipt.json',value.owned)
    refresh(value)
    assert resume.inspect_parent(value.case.spec,value.request)['state']['epoch']==2


def test_declared_pause_epoch_must_match_marker_state_and_worker_return(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch)
    value.state['policy']['after_epoch']=3;refresh(value)
    with pytest.raises(ValueError,match='declared/returned pause epoch'):
        resume.inspect_parent(value.case.spec,value.request)


@pytest.mark.parametrize('control',('policy','request'))
def test_retained_quota_is_single_exact_spec_cap(control,tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch)
    if control=='policy':controls=(replace(value.policy,max_retained_bytes=value.policy.max_retained_bytes-1),None)
    else:controls=(None,replace(value.request,max_retained_bytes=value.request.max_retained_bytes-1))
    with pytest.raises(ValueError,match='retained quota'):
        resume.control_binding(value.case.spec,controls)


def test_sealer_binds_manufactured_full_launch_bytes_before_consumer(tmp_path,monkeypatch):
    value=manufactured_parent(tmp_path,monkeypatch);root=value.case.root
    destination=value.owned_dir/'sealed-final.json'
    sealed_pin=resume.seal_pause_terminal(value.parent_spec,
        worker_result_file=value.proof['worker_result_file'],
        owned_receipt_file=(value.owned_dir/'receipt.json').relative_to(root).as_posix(),
        destination=destination.relative_to(root).as_posix(),expected_worker_sha256=value.worker_pin,
        expected_request_file=value.proof['request_file'],expected_request_sha256=value.proof['request_sha256'],
        outer_elapsed_seconds=3.)
    request=replace(value.request,terminal_file=destination.relative_to(root).as_posix(),terminal_sha256=sealed_pin)
    inspected=resume.inspect_parent(value.case.spec,request)
    assert inspected['terminal']['launch_proof']['request_sha256']==value.proof['request_sha256']
    assert inspected['terminal']['launch_proof']['worker_result_sha256']==value.proof['worker_result_sha256']
    assert inspected['terminal']['launch_proof']['ownership']['worker']==value.owned['actual_worker']
