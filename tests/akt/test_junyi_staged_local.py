"""Kiểm tách local/GPU bằng filesystem thật, Modal/subprocess GPU được giả lập."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import zipfile
from copy import deepcopy

import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/akt'))
import junyi_staged_io as io
import modal_junyi_staged as staged
sys.path.insert(0,str(ROOT/'scripts/akt'))
from prepare_junyi_gpu_stage import validate_baseline_metadata


def archive(path,files,*,gate=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    pins={name:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for name,raw in files.items()}
    with zipfile.ZipFile(path,'x') as saved:
        for name,raw in files.items():saved.writestr(name,raw)
        saved.writestr('SHA256.json' if gate else 'MANIFEST.json',json.dumps(pins if gate else dict(files=pins)))
    return dict(path=path.name,sha256=io.sha(path))


@pytest.fixture
def package(tmp_path):
    root=tmp_path/'repo'
    root.mkdir()
    archives={
        'source':archive(root/'source.zip',{'src/model.py':b'pass\n','scripts/worker.py':b'pass\n'}),
        'data':archive(root/'data.zip',{'artifacts/akt/cache/shard.bin':b'input'}),
        'cpu_gate':archive(root/'gate.zip',{'gate2-current.json':b'{}','gate2-tests-unit.log':b'passed'},gate=True)}
    worker=dict(variant='A2',logical_run_id='unit-a2-logical',validation_batch_size=128,
        profile=dict(max_vram_bytes=12*1024**3),
        config=dict(run_id='unit-a2-logical',batch_size=128,seed=42,max_wall_seconds=60,max_seconds=50))
    from knowledge_tracing.akt.research_junyi_prepared import CACHE_FIELDS
    worker['cpu_prepared']={name:dict(path='artifacts/akt/cache/'+name,sha256='a'*64)
                            for name,*_ in CACHE_FIELDS}
    request=dict(archives=archives,local_files={},worker=worker)
    snapshot=root/'artifacts/akt/staged/unit'
    receipt=io.prepare_project(root,request,snapshot)
    return root,snapshot,receipt,request


def test_prepare_local_snapshot_and_mutation_rejection(package):
    _,snapshot,receipt,_=package
    assert io.verify_project(snapshot)==receipt
    (snapshot/'project/artifacts/akt/cache/shard.bin').write_bytes(b'changed')
    with pytest.raises(ValueError,match='Snapshot local thay đổi'):io.verify_project(snapshot)


def test_missing_cpu_preparation_blocks_gpu_before_dispatch(package):
    _,_,_,request=package
    worker=deepcopy(request['worker'])
    del worker['cpu_prepared']['selection_graph']
    with pytest.raises(ValueError,match='CPU caches'):
        staged.validate_execution(execution_request(),worker)


@pytest.mark.parametrize('field,value', [
    ('path', '../outside'), ('path', '/outside'), ('path', 'a//b'),
    ('path', 'a/./b'), ('path', 'C:/outside'), ('path', 'a\\b'),
    ('sha256', 'A'*64), ('sha256', 'a'*63), ('sha256', None),
])
def test_cpu_prepared_contract_rejects_invalid_paths_or_pins(package, field, value):
    from knowledge_tracing.akt.research_junyi_prepared import prepared_cache_options
    _,_,_,request=package
    worker=deepcopy(request['worker'])
    worker['cpu_prepared']['train_graph'][field]=value
    with pytest.raises(ValueError,match='CPU cache'):
        prepared_cache_options(worker,Path)


def test_cpu_prepared_contract_passes_every_external_pin(package):
    from knowledge_tracing.akt.research_junyi_prepared import CACHE_FIELDS,prepared_cache_options
    _,_,_,request=package
    options,pins=prepared_cache_options(request['worker'],Path)
    assert len(options)==10 and len(pins)==5
    for name,path_key,pin_key,grant_key in CACHE_FIELDS:
        assert options[path_key]==Path(request['worker']['cpu_prepared'][name]['path'])
        assert options[pin_key]==pins[grant_key]=='a'*64


@pytest.mark.parametrize('name',['../outside','/outside','a/../../x','C:/x','a\\b','a//b'])
def test_relative_paths_reject_traversal(name):
    with pytest.raises(ValueError):io.safe_relative(name)


def test_prepare_rejects_archive_sha_before_snapshot(package,tmp_path):
    root,_,_,request=package
    changed=dict(request,archives=dict(request['archives']))
    changed['archives']['source']=dict(changed['archives']['source'],sha256='0'*64)
    target=root/'artifacts/akt/staged/other'
    with pytest.raises(ValueError,match='Archive SHA'):io.prepare_project(root,changed,target)
    assert not target.exists()


def test_prepare_rejects_archive_traversal_and_private(tmp_path):
    for index,name in enumerate(('../bad','artifacts/akt/private/modal.toml','dataset/raw.csv','venv/runtime.bin')):
        root=tmp_path/str(index)
        root.mkdir()
        source=archive(root/'source.zip',{name:b'secret'})
        data=archive(root/'data.zip',{})
        gate=archive(root/'gate.zip',{},gate=True)
        with pytest.raises(ValueError):
            io.prepare_project(root,dict(archives=dict(source=source,data=data,cpu_gate=gate),local_files={},worker={}),
                               root/'artifacts/akt/staged/snapshot')


def test_collect_requires_stop_and_preserves_bytes_retry(tmp_path):
    raw=b'checkpoint'
    receipt=dict(status='PARTIAL_SELECTED_ONLY_NOT_FINAL',files={
        'outputs/logical/checkpoints/epoch-001/state.pt':dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())})
    target=tmp_path/'result'
    with pytest.raises(PermissionError):io.collect_outputs(receipt,target,lambda name:iter([raw]),stop_acknowledged=False)
    assert not target.exists()
    with pytest.raises(ValueError,match='sai bytes/SHA'):
        io.collect_outputs(receipt,target,lambda name:iter([b'bad']),stop_acknowledged=True)
    assert list(target.rglob('*.download.*'))
    result=io.collect_outputs(receipt,target,lambda name:iter([raw]),stop_acknowledged=True)
    assert result['status']=='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
    assert io.collect_outputs(receipt,target,lambda name:iter([raw]),stop_acknowledged=True)==result
    with zipfile.ZipFile(target/'artifacts.zip') as saved:
        assert saved.read(next(iter(receipt['files'])))==raw


def execution_request():
    return dict(status='USER_APPROVED',approval_reference='synthetic-local-test',execution_id='unit-a2-attempt1',
        gpu='T4',child_timeout_seconds=200,function_timeout_seconds=230,watchdog_seconds=260,
        reserved_usd_per_run=.2,authorized_batch_usd=.2,allocation_id='unit-allocation',image_id='unit-image')


@pytest.mark.parametrize('change',[
    dict(status='DRAFT'),dict(gpu='unknown'),dict(reserved_usd_per_run=.001),
    dict(execution_id='../invalid'),dict(child_timeout_seconds=260)])
def test_execution_caps_reject_invalid_request(package,change):
    request=dict(execution_request(),**change)
    with pytest.raises((ValueError,PermissionError)):
        staged.validate_execution(request,package[3]['worker'])


@pytest.mark.parametrize('outcome',['partial','failed','interrupted'])
def test_controller_uploads_before_gpu_and_downloads_after_stop(package,monkeypatch,outcome):
    root,snapshot,prepared,_=package
    monkeypatch.setattr(staged,'ROOT',root)
    io.write_new(snapshot/'CPU_CHECK.json',dict(status='PASS_LOCAL_STAGE_INPUTS',
        inputs_sha256=io.sha(snapshot/'INPUTS.json'),worker_request_sha256=io.sha(snapshot/'project/gpu-stage-request.json')))
    io.write_new(root/'research_tracking/COMPUTE_BUDGET.json',{})
    events=[]
    remote={}
    checkpoint=b'kept-checkpoint'
    remote_receipt=dict(status='PARTIAL_SELECTED_ONLY_NOT_FINAL',files={
        'outputs/unit-a2-logical/checkpoints/epoch-001/state.pt':dict(bytes=len(checkpoint),sha256=hashlib.sha256(checkpoint).hexdigest())})
    marker=b'{}'
    remote_receipt['files']['outputs/unit-a2-logical/checkpoints/epoch-001/COMPLETE.json']=dict(
        bytes=len(marker),sha256=hashlib.sha256(marker).hexdigest())

    class Volume:
        @classmethod
        def from_name(cls,*args,**kwargs):return cls()
        def read_file(self,name):
            if name not in remote:raise FileNotFoundError(name)
            if name.startswith('outputs/'):
                assert 'stop_acknowledged' in events
                events.append('local_download')
            yield remote[name]
        @contextmanager
        def batch_upload(self,force):
            assert force is False and 'gpu_start' not in events
            events.append('local_upload')
            yield self
        def put_file(self,path,name):remote[name.lstrip('/')]=Path(path).read_bytes()
        def with_mount_options(self,**kwargs):return self
        def iterdir(self,*args,**kwargs):return iter(())

    class Image:
        @classmethod
        def from_id(cls,_):return cls()
        def add_local_file(self,*args):return self

    class Call:
        object_id='unit-call'
        def get(self,timeout):
            remote[next(iter(remote_receipt['files']))]=checkpoint
            remote['outputs/unit-a2-logical/checkpoints/epoch-001/COMPLETE.json']=marker
            events.append('gpu_result')
            if outcome=='interrupted':
                remote['outputs/unit-a2-attempt1-operation/checkpoint-index.json']=json.dumps(
                    dict(status='CHECKPOINT_RECOVERY_INDEX',files=remote_receipt['files'])).encode()
                raise ConnectionError('synthetic connection interruption')
            if outcome=='failed':remote_receipt['status']='FAILED'
            return remote_receipt

    class Function:
        def spawn(self,*args):return Call()

    class App:
        def __init__(self,name):self.name=name;self.app_id='ap-unit'
        def function(self,**kwargs):
            assert kwargs['max_containers']==1 and kwargs['retries']==0
            assert '/opt/kltn/.venv' not in kwargs['volumes']
            return lambda callback:Function()
        @contextmanager
        def run(self,**kwargs):
            assert 'local_upload' in events
            events.append('gpu_start')
            yield

    class Guard:
        def __init__(self,*args,diagnostic_path,**kwargs):self.path=diagnostic_path
        def __enter__(self):return self
        def __exit__(self,*args):
            events.append('stop_acknowledged')
            io.write_new(self.path,dict(stop_acknowledged=True))

    @contextmanager
    def enabled():yield

    async def billing():return dict(billing=dict(metered_cost='0'))
    monkeypatch.setitem(sys.modules,'modal',SimpleNamespace(Volume=Volume,Image=Image,App=App,enable_output=enabled))
    monkeypatch.setitem(sys.modules,'modal_graph_selected',SimpleNamespace(read_billing=billing))
    monkeypatch.setitem(sys.modules,'modal_junyi_main_selected',SimpleNamespace(validate_project_budget=lambda *args:{}))
    monkeypatch.setitem(sys.modules,'modal_budget_guard',SimpleNamespace(
        ModalRunDeadline=lambda seconds:SimpleNamespace(remaining=lambda:seconds),ModalAppBudgetGuard=Guard,
        PendingOwnedModalApp=lambda *args:object(),stop_owned_app_cli=lambda *args:None))
    if outcome=='partial':
        result=staged.run(snapshot,execution_request())
        assert result['worker_status']=='PARTIAL_SELECTED_ONLY_NOT_FINAL'
    else:
        with pytest.raises(ConnectionError if outcome=='interrupted' else RuntimeError):
            staged.run(snapshot,execution_request())
    assert events.index('local_upload')<events.index('gpu_start')<events.index('gpu_result')
    assert events.index('gpu_result')<events.index('stop_acknowledged')<events.index('local_download')
    suffix='recovery/artifacts.zip' if outcome=='interrupted' else 'artifacts.zip'
    assert (root/'experiments/akt/results/unit-a2-attempt1'/suffix).exists()


def test_gpu_function_persists_checkpoint_and_returns_inventory_without_zip(tmp_path,monkeypatch):
    remote=tmp_path/'remote'
    remote.mkdir()
    worker=remote/'gpu-stage-request.json'
    io.write_new(worker,dict(logical_run_id='logical-a2'))
    execution=dict(execution_id='attempt-a2',worker_request_sha256=io.sha(worker),child_timeout_seconds=30)
    operation=remote/'experiments/akt/results/attempt-a2-operation'
    results=remote/'experiments/akt/results'
    real_path=Path
    monkeypatch.setattr(staged,'Path',lambda value:remote if value=='/opt/kltn' else real_path(value))
    commits=[]
    volume=SimpleNamespace(commit=lambda:commits.append(1))
    monkeypatch.setitem(sys.modules,'modal',SimpleNamespace(Volume=SimpleNamespace(from_name=lambda *a,**k:volume)))
    checkpoint=results/'logical-a2/checkpoints/epoch-001'

    class Process:
        pid=123456
        returncode=0
        def __init__(self,*args,**kwargs):
            checkpoint.mkdir(parents=True)
            (checkpoint/'state.pt').write_bytes(b'checkpoint')
            io.write_new(checkpoint/'metadata.json',dict(checkpoint_bytes=10,checkpoint_sha256=io.sha(checkpoint/'state.pt')))
            io.write_new(checkpoint/'COMPLETE.json',dict(checkpoint_sha256=io.sha(checkpoint/'state.pt'),
                metadata_sha256=io.sha(checkpoint/'metadata.json')))
            io.write_new(operation/'result.json',dict(status='JUNYI_A2_SELECTED_ONLY_COMPLETE'))
        def poll(self):return self.returncode

    monkeypatch.setattr(staged.subprocess,'Popen',Process)
    monkeypatch.setattr(staged.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='37, 100, 1000, 20\n'))
    receipt=staged.gpu_compute(execution,'fake-volume')
    assert receipt['status']=='JUNYI_A2_SELECTED_ONLY_COMPLETE'
    assert commits and (operation/'checkpoint-index.json').exists()
    assert not list(remote.rglob('*.zip'))
    for name,pin in receipt['files'].items():
        path=results/name.removeprefix('outputs/')
        assert io.sha(path)==pin['sha256']
    assert staged.gpu_compute(execution,'fake-volume')==receipt
    with pytest.raises(ValueError,match='cấu hình khác'):
        staged.gpu_compute(dict(execution,child_timeout_seconds=31),'fake-volume')


def test_interrupted_upload_resumes_without_overwriting_inputs(package):
    _,snapshot,receipt,_=package
    first=next(iter(receipt['files']))
    remote={'project/'+first:(snapshot/'project'/first).read_bytes()}
    written=[]
    class Volume:
        def iterdir(self,*args,**kwargs):
            return iter(SimpleNamespace(path=name,type=SimpleNamespace(name='FILE')) for name in remote)
        def read_file(self,name):
            if name not in remote:raise FileNotFoundError(name)
            yield remote[name]
        @contextmanager
        def batch_upload(self,force):
            assert not force
            yield self
        def put_file(self,path,name):
            key=name.lstrip('/')
            assert key not in remote
            remote[key]=Path(path).read_bytes()
            written.append(key)
    volume=Volume()
    io.upload_snapshot(volume,snapshot,receipt)
    assert 'project/'+first not in written
    assert written[-1]=='project/INPUTS.json'
    assert remote['project/INPUTS.json']==(snapshot/'INPUTS.json').read_bytes()
    assert io.upload_snapshot(volume,snapshot,receipt) is None
    remote.pop('project/INPUTS.json')
    remote['project/'+first]=b'corrupt'
    with pytest.raises(ValueError,match='không ghi đè'):
        io.upload_snapshot(volume,snapshot,receipt)


@pytest.fixture
def comparison_case():
    from dataclasses import asdict
    from knowledge_tracing.akt.config import AKTConfig,ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.comparison_contract import TRAINING_FIELDS
    config=json.loads(json.dumps(asdict(AKTConfig()),default=str))
    profile=asdict(ResearchCUDAExecutionProfile(16*1024**3,recipe_id='cgakt-cuda-fp32-batch128-v2'))
    pins=dict(roles='a'*64,selected_manifest='b'*64,encoding='c'*64,
              encoding_receipt='d'*64,window_manifest='e'*64)
    inputs=dict(roles_sha256=pins['roles'],selected_cache_manifest_sha256=pins['selected_manifest'],
                encoding_sha256=pins['encoding'],encoding_receipt_sha256=pins['encoding_receipt'],
                train_window_manifest_sha256=pins['window_manifest'])
    worker=dict(config=config,profile=profile,inputs=inputs,validation_batch_size=128)
    reference=dict(training_config={key:config[key] for key in TRAINING_FIELDS},numeric_profile=profile,data_pins=pins)
    peers=[dict(metadata=dict(identity=dict(config=deepcopy(config),profile=deepcopy(profile)))) for _ in range(2)]
    return worker,reference,peers


def test_baseline_fields_profile_and_data_match_before_dispatch(comparison_case):
    worker,reference,peers=comparison_case
    assert validate_baseline_metadata(worker,reference,peers)==27
    worker['profile']=dict(worker['profile'],max_vram_bytes=12*1024**3)
    assert validate_baseline_metadata(worker,reference,peers)==27


@pytest.mark.parametrize('mutation',['seed','batch_size','dropout','max_epochs','profile','roles','validation'])
def test_baseline_mismatch_is_rejected_locally(comparison_case,mutation):
    worker,reference,peers=comparison_case
    if mutation in ('seed','batch_size','max_epochs'):worker['config'][mutation]+=1
    elif mutation=='dropout':worker['config'][mutation]=.2
    elif mutation=='profile':worker['profile']=dict(worker['profile'],dtype='float16')
    elif mutation=='roles':worker['inputs']['roles_sha256']='f'*64
    else:worker['validation_batch_size']=1
    with pytest.raises(ValueError):validate_baseline_metadata(worker,reference,peers)
