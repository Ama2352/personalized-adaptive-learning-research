"""Pure temporary-filesystem/stdlib orchestration. No actual Job/process/Thread/ML imports.

Manufactured count fixtures cannot certify2352fits/OOF/ABI/RAM feasibility.
ROOT alone executes these tests after source/command review.
"""
import builtins
from contextlib import nullcontext
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import time

import pytest

HERE = Path(__file__).resolve().parent
H = 'a'*64


def load(name):
    spec = importlib.util.spec_from_file_location('pure_'+name, HERE/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def no_real_heavy_imports(monkeypatch):
    original = builtins.__import__
    attempts = []
    def guarded(name,*args,**kwargs):
        if name.split('.')[0] in ('numpy','pandas','scipy','sklearn','torch','joblib','threadpoolctl','psutil') or name.startswith('knowledge_tracing'):
            attempts.append(name)
            raise AssertionError('pure tests cannot import runtime/native: '+name)
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',guarded)
    yield
    assert attempts == []


@pytest.fixture
def case(tmp_path_factory,monkeypatch):
    w,o = load('method24_worker01'),load('run_method24_native01')
    root = tmp_path_factory.mktemp('m24')/'w'
    root.mkdir()
    monkeypatch.setattr(w,'ROOT',root);monkeypatch.setattr(o,'ROOT',root)
    prep = root/w.PREP_REL
    prep.mkdir(parents=True)
    monkeypatch.setattr(o,'PREP',prep)
    config = json.loads((HERE/'method24_config01.json').read_bytes())
    profile = json.loads((HERE/'method24_runtime_profile01.json').read_bytes())
    def put(relative,payload):
        path = root/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(payload)
        return w.hash_file(relative)
    for name in w.SOURCES:
        put(name,b'# DECLARED PURE ENGINEERING SOURCE FIXTURE\n')
    c = config['corpus'];prefix = 'artifacts/simulator/corpora/'+c['id']+'/'
    public = {name:put(prefix+name,w.encode(dict(manufactured_public_fixture=name))) for name in w.PUBLIC}
    prior = dict(corpus_id=c['id'],files={prefix+name:dict(sha256=digest,bytes=(root/prefix/name).stat().st_size)
        for name,digest in public.items()})
    c['prior_inventory_sha256'] = put(c['prior_inventory_relative'],w.encode(prior))
    c.update(corpus_sha256=public['corpus.json'],done_sha256=public['DONE.json'],train_observable_sha256=public['train.jsonl'])
    profile['entry_sha256'] = put('.venv/Scripts/python.exe',b'NOT_EXECUTABLE_VENV_FIXTURE')
    profile['cfg_sha256'] = put('.venv/pyvenv.cfg',b'include-system-site-packages = false\n')
    profile['lock_sha256'] = put(profile['lock_relative'],b'NOT_AN_INSTALLED_LOCK_FIXTURE')
    profile['protocol_sha256'] = put(profile['protocol_relative'],b'NOT_A_METHOD_ADOPTION_FIXTURE')
    for path in profile['extra_sources']:
        profile['extra_sources'][path] = put(path,b'NOT_EXECUTED_PUBLIC_SOLVER_SOURCE_FIXTURE')
    for name,item in profile['packages'].items():
        for kind in ('metadata','record','module'):
            item[kind+'_sha256'] = put(item[kind+'_relative'],('NOT_IMPORTED_'+name+'_'+kind).encode())
    profile['method_source_sha256'] = w.hash_file('src/knowledge_tracing/edge_confidence.py')
    put(w.CONFIG,w.encode(config));put(w.PROFILE,w.encode(profile))
    request = o.prepare_request(w,'PURE_STUB_TEST_NOT_EXECUTION_APPROVAL')
    args = w.parse_args(o.worker_argv(w,request['request_sha256'],time.perf_counter()+60,time.time()+60))
    owner = dict(status='OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE',worker=dict(pid=os.getpid()),
        nonce='fixture-nonce',parent_owner={'pid':1},job_name='FAKE_JOB_NOT_CREATED')
    request_data = w.read_json(w.REQUEST,request['request_sha256'])
    owned_dir = prep/'method24-owned01'
    owned_dir.mkdir()
    launch = owned_dir/'launch.json'
    launch.write_bytes(w.encode(dict(schema_version=1,nonce=owner['nonce'],parent=owner['parent_owner'],job_name=owner['job_name'],
        worker_relative=w.SELF,worker_sha256=request_data['source_sha256'][w.SELF],
        helper_sha256=request_data['source_sha256']['scripts/research/windows_owned_worker.py'],
        worker_args=o.worker_argv(w,request['request_sha256'],args.active_deadline_perf,args.active_deadline_wall),
        entry=str(root/'.venv/Scripts/python.exe'),approval_reference=request_data['approval_reference'],
        active_deadline=args.active_deadline_perf)))
    monkeypatch.setenv('KLTN_WINDOWS_LAUNCH_MANIFEST',str(launch))
    # Execute only real helper's stdlib path/bounded reader, never entry/Kernel/Job.
    helper_path = HERE.parents[3]/'scripts/research/windows_owned_worker.py'
    spec = importlib.util.spec_from_file_location('pure_owned_path_helper',helper_path)
    helper = importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    monkeypatch.setattr(helper,'ROOT',root)
    monkeypatch.setitem(sys.modules,'windows_owned_worker',helper)
    return SimpleNamespace(w=w,o=o,root=root,prep=prep,config=config,profile=profile,args=args,owner=owner,put=put,launch=launch)


def memory(free=2**31, rss=20*1024**2):
    return dict(process_rss_bytes=rss,process_peak_rss_bytes=rss,system_available_ram_bytes=free)


def manufactured_metadata(w, *, helpers=1):
    # Explicit test fixture; never actual OS discovery/runtime evidence.
    executable = str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')
    return dict(public_api='platform.uname',phase='NATIVE_WINDOWS_METADATA_BOOTSTRAP_ONLY',
        system='Windows',release='MOCK',version='MOCK_NOT_RUNTIME_EVIDENCE',machine='MOCK',
        helper_calls=helpers,allowed_executable=executable,
        commands=[dict(executable=executable,command=executable+' /c "ver"') for _ in range(helpers)],
        outside_phase_popen_attempts=0,blocked_bootstrap_attempts=0,phase_closed=True,seconds=.01)


def manufactured_runtime(w, *, helpers=1):
    metadata=manufactured_metadata(w,helpers=helpers)
    return dict(native_windows_metadata=metadata,process_counts=dict(metadata_bootstrap_helpers=helpers,
        fit_phase_popen_attempts=0,outside_metadata_phase_popen_attempts=0,
        overall_permitted_worker_child_popen_events=helpers))


def test_complete_worker_argv_parser_contract_and_missing_deadline():
    w,o = load('method24_worker01'),load('run_method24_native01')
    args = w.parse_args(o.worker_argv(w,H,10.,20.))
    assert (args.request,args.request_sha256,args.active_deadline_perf,args.active_deadline_wall) == (w.REQUEST,H,10.,20.)
    with pytest.raises(SystemExit): w.parse_args(['--request',w.REQUEST,'--request-sha256',H])


def test_runtime_packet_includes_optional_pandas_without_forbidding_it(case):
    request,config,profile,files = case.w.validate_request(case.w.REQUEST,case.args.request_sha256)
    assert len(request['source_sha256']) == request['source_count'] == config['counts']['source_files'] == 11
    assert 'src/knowledge_tracing/akt/__init__.py' in request['source_sha256'] and len(request['public_sha256']) == 10
    assert profile['packages']['pandas']['required'] is False
    assert profile['packages']['sklearn']['required'] is True
    assert all('/oracle/' not in path for path in files)


def test_protected_source_rejected_before_unapproved_open(case,monkeypatch):
    w = case.w
    request = w.read_json(w.REQUEST,case.args.request_sha256)
    request['source_sha256']['dataset/private.csv'] = H
    case.put(w.REQUEST,w.encode(request))
    original = w.hash_file
    def checked(path,**kwargs):
        assert not path.startswith('dataset/'),'protected path opened'
        return original(path,**kwargs)
    monkeypatch.setattr(w,'hash_file',checked)
    with pytest.raises(ValueError,match='exact eleven'): w.validate_request(w.REQUEST,original(w.REQUEST))


def test_valid_absolute_owned_manifest_uses_real_helper_path_guards(case):
    request = case.w.read_json(case.w.REQUEST,case.args.request_sha256)
    launch = case.w.owned_launch_manifest(case.args,case.owner,request)
    assert case.launch.is_absolute() and launch['worker_relative'] == case.w.SELF
    assert launch['parent'] == case.owner['parent_owner'] and launch['nonce'] == case.owner['nonce']


@pytest.mark.parametrize('kind',['outside','unowned','nonce','parent','source'])
def test_unowned_or_forged_absolute_manifest_rejects_before_runtime_or_fit(case,monkeypatch,kind):
    w = case.w
    if kind in ('outside','unowned'):
        path = case.root.parent/'launch.json' if kind == 'outside' else case.prep/'unowned'/'launch.json'
        monkeypatch.setenv('KLTN_WINDOWS_LAUNCH_MANIFEST',str(path))
    else:
        manifest = json.loads(case.launch.read_bytes())
        if kind == 'nonce': manifest['nonce'] = 'wrong-owner'
        elif kind == 'parent': manifest['parent'] = {'pid':-1}
        else: manifest['worker_sha256'] = 'b'*64
        case.launch.write_bytes(w.encode(manifest))
    monkeypatch.setattr(w,'_memory_api',lambda:pytest.fail('unowned manifest reached runtime'))
    monkeypatch.setattr(w,'_domain_api',lambda:pytest.fail('unowned manifest reached fit'))
    with pytest.raises(ValueError,match='owned'): w.run(case.args,case.owner)
    assert not (case.root/w.OUTPUT).exists()


@pytest.mark.parametrize('kind',['existing_output','recipe','caps','alias'])
def test_exclusive_and_frozen_config_guards(case,monkeypatch,kind):
    w = case.w
    if kind == 'existing_output': (case.root/w.OUTPUT).mkdir()
    elif kind == 'alias':
        original = Path.is_symlink
        monkeypatch.setattr(Path,'is_symlink',lambda path: path == case.root/w.OUTPUT or original(path))
    else:
        config = deepcopy(case.config)
        if kind == 'recipe': config['recipe']['C'] = 2.
        else: config['caps']['max_rss_bytes'] += 1
        digest = case.put(w.CONFIG,w.encode(config))
        request = w.read_json(w.REQUEST,case.args.request_sha256)
        request['config_sha256'] = digest
        case.args.request_sha256 = case.put(w.REQUEST,w.encode(request))
    with pytest.raises(ValueError): w.validate_request(w.REQUEST,case.args.request_sha256)


def test_wrong_owner_rejected_before_writes_or_runtime(case,monkeypatch):
    monkeypatch.setattr(case.w,'_memory_api',lambda:pytest.fail('wrong owner reached runtime'))
    with pytest.raises(ValueError,match='owned worker'): case.w.run(case.args,{'worker':{'pid':-1}})
    assert not (case.root/case.w.OUTPUT).exists()


def test_fresh_ram_floor_before_heavy_import_or_output(case,monkeypatch):
    monkeypatch.setattr(case.w,'_memory_api',lambda:lambda:memory(free=1))
    monkeypatch.setattr(case.w,'_domain_api',lambda:pytest.fail('low RAM reached domain imports'))
    with pytest.raises(ValueError,match='RAM floor'): case.w.run(case.args,case.owner)
    assert not (case.root/case.w.OUTPUT).exists()


def fake_flow(case,monkeypatch,*,low_after_reader=False):
    w = case.w;state = dict(read=False,roles=[],fit_calls=0,monitor_started=0,monitor_stopped=0,stages=[])
    monkeypatch.setattr(w,'_memory_api',lambda:lambda:memory(free=1 if low_after_reader and state['read'] else 2**31))
    class DummyMonitor:
        def __init__(self,*args): pass
        def start(self): state['monitor_started'] += 1
        def stop(self): state['monitor_stopped'] += 1
    monkeypatch.setattr(w,'Monitor',DummyMonitor)
    def metadata(guard):
        state['stages'].append('metadata')
        guard.left()
        return manufactured_metadata(w,helpers=0)
    def guards(_):
        state['stages'].append('guards')
        return dict(public_opens=set(w.PUBLIC),forbidden_imports=[],subprocess_attempts=0)
    monkeypatch.setattr(w,'native_windows_metadata',metadata)
    monkeypatch.setattr(w,'install_access_guards',guards)
    monkeypatch.setattr(w,'runtime_origins',lambda *args,**kwargs: {'engineering':'NOT_ACTUAL_ORIGINS'})
    class Public:
        plan = SimpleNamespace(identity=case.config['corpus']['plan_sha256'])
        bank = object()
        def role_data(self,role):
            state['roles'].append(role)
            return 'TRAIN_ONLY_SYNTHETIC_ROLE'
    def read(*args,**kwargs):
        state['read'] = True
        return Public()
    reader = SimpleNamespace(CorpusReadLimits=lambda *args:args,read_public_research_corpus=read)
    prepared = SimpleNamespace(learner_ids=range(48),rows=range(10080),concepts=range(28),identity=H)
    result = SimpleNamespace(fit_records=(SimpleNamespace(solver_called=False),)*2352,oof_rows=range(272160),
                             edges=(SimpleNamespace(supported=False),)*756,identity=H)
    graph = SimpleNamespace(status='UNSUPPORTED_EDGE_BUDGET',edges=())
    def fit(*args,**kwargs):
        state['fit_calls'] += 1  # Fake orchestration call, never a solver/model.
        return result
    ec = SimpleNamespace(EdgeConfidenceRecipe=lambda **kw:kw,EdgePreparationLimits=lambda *args:args,
        EdgeRuntimeBinding=lambda *args:args,EdgeFitLimits=lambda *args:args,
        prepare_train_lagged_rows=lambda *args,**kwargs:prepared,fit_crossfit_edge_confidence=fit,
        select_positive_dag=lambda *args,**kwargs:graph)
    def domain():
        state['stages'].append('domain')
        return ec,reader
    monkeypatch.setattr(w,'_domain_api',domain)
    pool = SimpleNamespace(threadpool_limits=lambda **kw:nullcontext(),threadpool_info=lambda:[{'num_threads':1}])
    monkeypatch.setitem(sys.modules,'threadpoolctl',pool)
    def export(writer,*args):
        for name in w.DATA_FILES: writer.json(name,{'scope':'MANUFACTURED_NO_ACTUAL_FITS_OR_OOF_ROWS'})
    monkeypatch.setattr(w,'export_result',export)
    return state


def test_ram_after_reader_overrides_success_and_never_reaches_fit(case,monkeypatch):
    state = fake_flow(case,monkeypatch,low_after_reader=True)
    assert case.w.run(case.args,case.owner) == 1
    assert state['fit_calls'] == 0 and not (case.root/case.w.OUTPUT/'DONE.json').exists()
    failure = json.loads((case.root/case.w.OUTPUT/'failure.json').read_bytes())
    assert failure['reserved_solver_calls'] == 2352 and failure['actual_solver_calls'] is None


def test_fake_positive_flow_is_pending_outer_no_real_solver_or_dag_promotion(case,monkeypatch):
    state = fake_flow(case,monkeypatch)
    assert case.w.run(case.args,case.owner) == 0
    assert state['roles'] == ['train'] and state['fit_calls'] == 1
    assert state['stages'] == ['metadata','guards','domain']
    directory = case.root/case.w.OUTPUT
    result = json.loads((directory/'worker_result.json').read_bytes())
    reserve = json.loads((directory/'reservation.json').read_bytes())
    done = json.loads((directory/'DONE.json').read_bytes())
    assert result['status'].endswith('PENDING_OUTER_ACCEPTANCE') and result['actual_solver_calls'] == 0
    assert result['processed_fit_slots'] == 2352 and reserve['solver_calls'] is None
    assert result['graph_status'] == 'UNSUPPORTED_EDGE_BUDGET' and result['teacher_calls'] == result['neural_optimizer_steps'] == 0
    assert set(done['files_sha256']) == set(case.w.OUTPUT_FILES)-{'DONE.json'}
    assert state['monitor_started'] == 1 and state['monitor_stopped'] == 1
    runtime=json.loads((directory/'runtime.json').read_bytes())
    assert runtime['native_windows_metadata']['phase_closed'] is True
    assert runtime['process_counts']['fit_phase_popen_attempts']==0


def test_writer_caps_and_roundtrip_rows_without_large_asdict(case):
    w = case.w
    directory = case.prep/'writer-engineering'
    directory.mkdir()
    guard = SimpleNamespace(left=lambda:10.)
    writer = w.Writer(directory,{**w.CAPS,'max_total_output_bytes':64},guard)
    writer.csv('baseline-oof.csv',('p','null'),[(.12345678912345678,None)])
    assert '0.12345678912345678' in (directory/'baseline-oof.csv').read_text()
    with pytest.raises(ValueError,match='byte cap'): writer.json('recipe.json',{'too_big':'X'*100})
    assert 'recipe.json' not in writer.files


def test_monitor_violation_uses_exact_self_exit_marker_without_actual_thread(case,monkeypatch):
    w = case.w;exits=[]
    class ExitControl(BaseException): pass
    class FakeThread:
        def __init__(self,**kwargs): self.target=kwargs['target']
        def start(self): self.target()
    class FakeEvent:
        def wait(self,timeout): return False
        def set(self): pass
    monkeypatch.setattr(w,'threading',SimpleNamespace(Thread=FakeThread,Event=FakeEvent))
    def reject(): raise ValueError('ENGINEERING_RSS_CONTROL')
    guard = SimpleNamespace(caps=w.CAPS,left=reject,summary=lambda:{'manufactured':True})
    def not_exit(code):
        exits.append(code)
        raise ExitControl()
    monkeypatch.setattr(w,'os',SimpleNamespace(_exit=not_exit,fsync=os.fsync))
    with pytest.raises(ExitControl): w.Monitor(guard,case.prep).start()
    receipt = json.loads((case.prep/'resource-failure.json').read_bytes())
    assert exits == [125] and receipt['actual_solver_calls'] is None and receipt['reservation_solver_calls'] == 2352


def test_parent_resource_guard_and_cleanup_rejection_precede_artifact_reads(case):
    o,w=case.o,case.w
    with pytest.raises(ValueError,match='RAM'): o.resource_preflight(memory(free=1),w.CAPS)
    owned=dict(accepted=False,cleanup_accepted=False,cleanup_errors=['ENGINEERING_FAILURE'],job_active_after_cleanup=1,
               popen_handle_closed=False,worker_returncode_before_cleanup=0,returncode=0,actual_worker_in_job_before_GO=True)
    with pytest.raises(ValueError,match='cleanup'): o.accept_worker(w,H,{},owned,lambda:1.)


def test_outer_post_receipt_hash_time_overrides_prior_success_without_process(case,monkeypatch):
    # Only outer finalization is under test: owner acceptance and child are fake.
    w,o=case.w,case.o
    # This case stubs child launch; keep exclusive outer attempt path initially absent.
    case.launch.unlink();case.launch.parent.rmdir()
    clock=[0.]
    monkeypatch.setattr(o,'time',SimpleNamespace(perf_counter=lambda:clock[0],time=lambda:clock[0]))
    monkeypatch.setattr(o,'START',0.);monkeypatch.setattr(o,'WALL',0.)
    monkeypatch.setattr(o,'sys',SimpleNamespace(executable=str(case.root/'.venv/Scripts/python.exe'),
        prefix=str(case.root/'.venv'),path=list(sys.path)))
    monkeypatch.setattr(o,'os',SimpleNamespace(environ=dict(os.environ),fsync=os.fsync))
    monkeypatch.setattr(o,'_memory_api',lambda:lambda:memory())
    monkeypatch.setattr(o,'_owned_api',lambda:lambda *args,**kwargs:{'cleanup_accepted':True,'scope':'NOT_ACTUAL_JOB'})
    monkeypatch.setattr(o,'accept_worker',lambda *args:({'actual_solver_calls':0,'graph_status':'UNSUPPORTED_EDGE_BUDGET'},{}))
    original=w.hash_file
    def delayed(relative,**kwargs):
        digest=original(relative,**kwargs)
        if relative.endswith('/method24_run01.json'): clock[0]=121.
        return digest
    monkeypatch.setattr(w,'hash_file',delayed)
    assert o.run(w,case.args.request_sha256) == 1
    assert (case.prep/'method24_postbudget_failure01.json').is_file()
    receipt=json.loads((case.prep/'method24_run01.json').read_bytes())
    assert receipt['status'].startswith('ACCEPTED_')  # Preserved but superseded; terminalRC1/failure marker rejects.


@pytest.mark.parametrize('quoted',[False,True])
def test_metadata_command_accepts_only_fixed_ver_form(quoted):
    w=load('method24_worker01')
    executable=str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')
    command=('"'+executable+'"' if quoted else executable)+' /c "ver"'
    assert w.windows_metadata_command(executable,command,executable,phase=True,calls=2)==dict(executable=executable,command=command)


@pytest.mark.parametrize('kind',['executable','command','operator_prefix','ver_arguments','count','phase','nonstring'])
def test_metadata_command_rejects_other_processes_phases_and_excess_calls(kind):
    w=load('method24_worker01')
    expected=str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')
    executable=expected;command=expected+' /c "ver"';phase=True;calls=0
    if kind=='executable':executable=str(HERE/'cmd.exe')
    if kind=='command':command=expected+' /c "whoami"'
    if kind=='operator_prefix':command=expected+' /c "echo BAD" & '+expected+' /c "ver"'
    if kind=='ver_arguments':command=expected+' /c "ver /?"'
    if kind=='count':calls=3
    if kind=='phase':phase=False
    if kind=='nonstring':command=[command]
    with pytest.raises(ValueError):w.windows_metadata_command(executable,command,expected,phase=phase,calls=calls)


def test_metadata_bootstrap_records_native_api_shape_and_then_closes_phase(monkeypatch):
    w=load('method24_worker01');hooks=[];checks=[]
    monkeypatch.setattr(w.sys,'addaudithook',hooks.append)
    expected=str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')
    def discover():
        hooks[0]('subprocess.Popen',(expected,expected+' /c "ver"',None,None))
        return SimpleNamespace(system='Windows',release='MOCK',version='MOCK',machine='MOCK',node='NEVER_STORE_HOSTNAME')
    monkeypatch.setattr(w,'platform',SimpleNamespace(uname=discover))
    receipt=w.native_windows_metadata(SimpleNamespace(left=lambda:checks.append('guard') or 10.))
    assert receipt['helper_calls']==1 and receipt['phase_closed'] is True and receipt['blocked_bootstrap_attempts']==0
    assert 'node' not in receipt and 'NEVER_STORE_HOSTNAME' not in json.dumps(receipt) and len(checks)>=4
    with pytest.raises(RuntimeError,match='outside bootstrap'):
        hooks[0]('subprocess.Popen',(expected,expected+' /c "ver"',None,None))
    assert receipt['outside_phase_popen_attempts']==1  # Same receipt tracks forbidden post-bootstrap attempts.


def test_metadata_bootstrap_finally_closes_after_disallowed_command(monkeypatch):
    w=load('method24_worker01');hooks=[];checks=[]
    monkeypatch.setattr(w.sys,'addaudithook',hooks.append)
    expected=str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')
    def bad_discovery():
        hooks[0]('subprocess.Popen',(expected,expected+' /c "whoami"',None,None))
        pytest.fail('disallowed command was accepted')
    monkeypatch.setattr(w,'platform',SimpleNamespace(uname=bad_discovery))
    with pytest.raises(ValueError,match='literal ver'):
        w.native_windows_metadata(SimpleNamespace(left=lambda:checks.append('guard') or 10.))
    with pytest.raises(RuntimeError,match='outside bootstrap'):
        hooks[0]('subprocess.Popen',(expected,expected+' /c "ver"',None,None))
    assert len(checks)>=4  # Includes finally guard; no actual process/OS metadata call.


@pytest.mark.parametrize('helpers',[0,1,3])
def test_outer_accepts_closed_metadata_and_counts_helpers_in_overall(helpers):
    w=load('method24_worker01');o=load('run_method24_native01')
    runtime=manufactured_runtime(w,helpers=helpers)
    o.validate_runtime_process_receipt(w,runtime)
    assert runtime['process_counts']['overall_permitted_worker_child_popen_events']==helpers


@pytest.mark.parametrize('kind',['hostname','phase','count','overall_zero','fit_popen','nonver','nonfinite'])
def test_outer_rejects_invalid_metadata_even_when_fit_counts_are_zero(kind):
    w=load('method24_worker01');o=load('run_method24_native01');runtime=manufactured_runtime(w)
    metadata=runtime['native_windows_metadata']
    if kind=='hostname':metadata['node']='NOT_ALLOWED'
    if kind=='phase':metadata['phase_closed']=False
    if kind=='count':metadata['helper_calls']=4
    if kind=='overall_zero':runtime['process_counts']['overall_permitted_worker_child_popen_events']=0
    if kind=='fit_popen':runtime['process_counts']['fit_phase_popen_attempts']=1
    if kind=='nonver':metadata['commands'][0]['command']=metadata['allowed_executable']+' /c "echo BAD"'
    if kind=='nonfinite':metadata['seconds']=float('nan')
    with pytest.raises(ValueError):o.validate_runtime_process_receipt(w,runtime)


def test_fit_access_guard_still_denies_even_system_ver_command(case,monkeypatch):
    w=case.w;hooks=[]
    monkeypatch.setattr(w.sys,'addaudithook',hooks.append)
    original=builtins.__import__
    try:
        observed=w.install_access_guards(case.config['corpus']['id'])
        executable=str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')
        with pytest.raises(RuntimeError,match='cannot create child'):
            hooks[0]('subprocess.Popen',(executable,executable+' /c "ver"',None,None))
        assert observed['subprocess_attempts']==1
    finally:
        builtins.__import__=original


@pytest.mark.parametrize('late_file',['runtime.json','DONE.json'])
def test_caught_late_metadata_attempt_rejects_even_with_prior_zero_runtime_snapshot(case,monkeypatch,late_file):
    w,o=case.w,case.o
    real_metadata=w.native_windows_metadata
    state=fake_flow(case,monkeypatch)
    hooks=[];caught=[]
    monkeypatch.setattr(w.sys,'addaudithook',hooks.append)
    monkeypatch.setattr(w,'platform',SimpleNamespace(uname=lambda:SimpleNamespace(
        system='Windows',release='MOCK',version='MOCK_NOT_RUNTIME_EVIDENCE',machine='MOCK')))
    def bootstrap(guard):
        state['stages'].append('metadata')
        state['live_metadata']=real_metadata(guard)  # Real closure; only uname is a pure fixture.
        return state['live_metadata']
    monkeypatch.setattr(w,'native_windows_metadata',bootstrap)
    original_json=w.Writer.json
    executable=str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')
    def write_then_caught_attempt(writer,name,value):
        original_json(writer,name,value)
        if name==late_file:
            # Invoke the actual installed audit callback, NOT Popen/Job/solver.
            # Emulate a dependency catching the denied attempt and continuing.
            try:hooks[0]('subprocess.Popen',(executable,executable+' /c "ver"',None,None))
            except RuntimeError as error:caught.append(str(error))
    monkeypatch.setattr(w.Writer,'json',write_then_caught_attempt)
    assert w.run(case.args,case.owner)==1
    directory=case.root/w.OUTPUT
    assert len(caught)==1 and state['live_metadata']['outside_phase_popen_attempts']==1
    assert state['fit_calls']==1  # Manufactured orchestration only; actual solver calls0.
    runtime=json.loads((directory/'runtime.json').read_bytes())
    assert runtime['native_windows_metadata']['outside_phase_popen_attempts']==0
    assert runtime['process_counts']['fit_phase_popen_attempts']==0  # Stale snapshot cannot authorize completion.
    failure=json.loads((directory/'failure.json').read_bytes())
    assert failure['status']=='REJECTED_KEEP_PARTIAL_NO_RETRY' and 'Popen denial' in failure['reason']
    assert failure['process_attempts_at_failure']==dict(outside_metadata_phase_popen_attempts=1,
        blocked_bootstrap_attempts=0,fit_phase_popen_attempts=0)
    assert (directory/'DONE.json').exists()==(late_file=='DONE.json')
    owned=dict(accepted=True,cleanup_accepted=True,cleanup_errors=[],job_active_after_cleanup=0,
        popen_handle_closed=True,worker_returncode_before_cleanup=0,returncode=0,actual_worker_in_job_before_GO=True)
    with pytest.raises(ValueError,match='exact output population'):
        o.accept_worker(w,H,{},owned,lambda:1.)  # Failure overrides even an already-written pending DONE.
