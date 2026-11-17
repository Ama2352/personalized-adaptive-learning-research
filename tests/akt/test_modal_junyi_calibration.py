"""Kiểm schema, budget và tách resource bằng Modal giả; không gọi cloud."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/akt'/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request():
    pin = dict(path='/artifacts/staged/file.json', sha256='a'*64)
    return dict(kind='JUNYI_CLOUD_CALIBRATION_REQUEST_V1', workspace='honguyenminhsang2016',
        mode='full', run_id='calib-20261117', variant='A0', exports={v:dict(pin) for v in ('A0','A1','A2','A3')},
        data_paths={v:dict(pin) for v in ('canonical','assignments','canonical_manifest','split_manifest')},
        population=pin, source_pins={}, cache_receipt=pin,
        numeric_budget=dict(max_seconds=240, max_rss_bytes=6*1024**3, max_vram_bytes=16*1024**3,
            expected_records=20000, expected_windows=20000, expected_targets=1621484, expected_oov_targets=0,
            batch_size=128), cpu_budget={}, gpu_output='calib-20261117/a0-numeric/payloads',
        full_cohort_approved=True, max_cost_usd=.40, source_identity='b'*64)


def test_full_calibration_is_explicit_and_readonly_validation():
    worker = load('calibration_cloud_worker')
    assert worker.validate_request(request(), 'gpu')['mode'] == 'full'


@pytest.mark.parametrize('mode', ['workspace', 'approval', 'variant', 'extra', 'cost', 'timeout', 'batch', 'output', 'source'])
def test_reject_invalid_request(mode):
    worker = load('calibration_cloud_worker')
    value = request()
    if mode == 'workspace': value['workspace']='other'
    elif mode == 'approval': value['full_cohort_approved']=False
    elif mode == 'variant': value['variant']='GKT'
    elif mode == 'extra': value['holdout']='forbidden'
    elif mode == 'cost': value['max_cost_usd']=1
    elif mode == 'timeout': value['numeric_budget']['max_seconds']=241
    elif mode == 'batch': value['numeric_budget']['batch_size']=129
    elif mode == 'output': value['gpu_output']='/outside'
    else: value['source_identity']='invalid'
    with pytest.raises((ValueError, PermissionError)):
        worker.validate_request(value, 'gpu')


def test_pilot_cannot_truncate_full_cache_or_fit():
    worker = load('calibration_cloud_worker')
    value = request(); value['mode']='pilot'; value['full_cohort_approved']=False
    with pytest.raises(ValueError, match='dedicated bounded cache'):
        worker.validate_request(value, 'gpu')
    value['numeric_budget'].update(expected_records=1,expected_windows=1,expected_targets=110)
    worker.validate_request(value, 'gpu')
    with pytest.raises(PermissionError): worker.validate_request(value, 'cpu-join')


def test_pinned_inputs_reject_mutation_and_outside(tmp_path):
    worker=load('calibration_cloud_worker')
    path=tmp_path/'file.json';path.write_text('{}')
    entry=dict(path=str(path),sha256=worker.sha(path))
    assert worker.pinned(entry,tmp_path)==path
    path.write_text('changed')
    with pytest.raises(ValueError,match='SHA'):worker.pinned(entry,tmp_path)
    with pytest.raises(ValueError):worker.pinned(dict(path=str(tmp_path.parent),sha256='a'*64),tmp_path)


@pytest.mark.parametrize('mode', ['workspace','stage','sha','allocation','cost'])
def test_budget_requires_external_matching_allocation(mode):
    controller=load('modal_junyi_calibration')
    entry=dict(path='/artifacts/request.json',sha256='a'*64)
    auth=dict(workspace='honguyenminhsang2016',stage='gpu',allocation_id='allocation',
              reserved_usd=.4,request_sha256='a'*64)
    controller.validate_authorization(auth,entry,'gpu')
    if mode=='workspace':auth['workspace']='other'
    elif mode=='stage':auth['stage']='cpu-join'
    elif mode=='sha':auth['request_sha256']='b'*64
    elif mode=='allocation':auth['allocation_id']=''
    else:auth['reserved_usd']=1
    with pytest.raises(PermissionError):controller.validate_authorization(auth,entry,'gpu')


def test_modal_secrets_only_cpu_join_and_bounded_gpu(monkeypatch):
    controller=load('modal_junyi_calibration')
    functions=[];image_calls=[]
    class Image:
        @classmethod
        def from_id(cls,value):
            assert value==controller.IMAGE_ID
            return cls()
        def __getattr__(self,name):
            def call(*args,**kwargs):image_calls.append((name,args,kwargs));return self
            return call
    class App:
        def __init__(self,name):pass
        def function(self,**kwargs):
            def decorate(function):functions.append((function.__name__,kwargs));return function
            return decorate
    fake=SimpleNamespace(Image=Image,App=App,
        Volume=SimpleNamespace(from_name=lambda *a,**k:object()),
        Secret=SimpleNamespace(from_name=lambda *a,**k:'cpu-drive-secret'))
    monkeypatch.setitem(sys.modules,'modal',fake)
    monkeypatch.setenv('MODAL_CONFIG_PATH','test');monkeypatch.setenv('MODAL_PROFILE','test')
    controller.create_app()
    options=dict(functions)
    assert options['predict']['gpu']=='H100!'
    assert options['predict']['timeout']==300 and options['predict']['max_containers']==1
    assert 'secrets' not in options['predict'] and 'secrets' not in options['prepare']
    assert options['join_fit']['secrets']==['cpu-drive-secret']
    assert options['join_fit']['cpu']==1 and options['join_fit']['memory']==16384
    assert options['preflight']['cpu']==1 and options['preflight']['memory']==4096
    assert options['preflight']['timeout']==120
    assert 'gpu' not in options['preflight'] and 'secrets' not in options['preflight']
    assert 'gpu' not in options['put_request'] and 'secrets' not in options['put_request']
    assert options['put_request']['memory']==1024
    assert options['publish_metadata']['secrets']==['cpu-drive-secret']
    assert 'gpu' not in options['publish_metadata']
    assert all(value['retries']==0 and value['single_use_containers'] for value in options.values())
    assert all(value['serialized'] is True for value in options.values())
    local_files=[str(args[0]) for name,args,kwargs in image_calls if name=='add_local_file']
    assert not any('private' in name for name in local_files)
    assert any('26_ADOPTED' in name for name in local_files)
    commands=[command for name,args,kwargs in image_calls if name=='run_commands' for command in args]
    ensurepip=next(i for i,command in enumerate(commands) if '-m ensurepip --upgrade' in command)
    installation=next(i for i,command in enumerate(commands) if '-m pip install' in command)
    assert ensurepip < installation
    assert commands[ensurepip].startswith('/opt/kltn/.venv/bin/python ')
    environment=next(args[0] for name,args,kwargs in image_calls if name=='env')
    assert environment['PYTHONPATH']=='/opt/kltn/src:/opt/kltn/scripts/akt:/opt/kltn/.venv/lib/python3.13/site-packages'


def test_real_sdk_nested_scope_requires_explicit_serialization():
    from modal._utils.function_utils import FunctionSourceInfo, LocalFunctionError
    def nested():
        return 1
    with pytest.raises(LocalFunctionError):
        FunctionSourceInfo(nested)
    info=FunctionSourceInfo(nested,serialized=True)
    assert info.is_serialized()
    assert len(info.serialized_function()) > 0


def test_cuda_metadata_does_not_open_canonical_and_keeps_config_owned_path(tmp_path, monkeypatch):
    worker=load('calibration_cloud_worker')
    monkeypatch.syspath_prepend(str(ROOT/'scripts/akt'))
    import knowledge_tracing.akt.research_junyi_inference as inference
    import knowledge_tracing.akt.config as config
    value=request()
    population=tmp_path/'population.json';population.write_text('{"source_pins": {}}')
    calls=[]
    def fake_pin(entry,root):
        calls.append(entry)
        return population if entry is value['population'] else tmp_path/'MODEL_INDEX.json'
    monkeypatch.setattr(worker,'pinned',fake_pin)
    monkeypatch.setattr(inference,'JunyiCPUInferenceBudget',lambda **kwargs: object())
    def inspect(export,**kwargs):
        assert kwargs['output']==config.PROJECT_ROOT/'experiments/akt/results'/value['run_id']
        return {'cuda': True}
    monkeypatch.setattr(inference,'inspect_cuda_refit_export',inspect)
    assets,paths,pop=worker.load_inputs(value,tmp_path,cuda=True)
    assert assets=={'cuda':True} and paths is None
    assert len(calls)==5  # Bốn MODEL_INDEX và population metadata, không canonical.


def test_numeric_archive_over_256_files_publishes_three(tmp_path):
    import json
    import zipfile
    worker=load('calibration_cloud_worker')
    value=request()
    numeric_root=tmp_path/value['gpu_output']
    numeric_root.mkdir(parents=True)
    (numeric_root/'config.json').write_text(json.dumps(value))
    shards=[]
    for index in range(130):
        payload=numeric_root/f'shard-{index:06d}.npz'
        payload.write_bytes(b'synthetic-numeric-bytes')
        manifest=payload.with_suffix('.json')
        manifest.write_text(json.dumps(dict(payload_sha256=worker.sha(payload))))
        shards.append(dict(manifest_path=str(manifest),manifest_sha256=worker.sha(manifest)))
    numeric=dict(shards=shards)
    receipt=numeric_root/'RECEIPT.json';receipt.write_text(json.dumps(numeric))
    before={path.name:worker.sha(path) for path in numeric_root.iterdir()}
    publication=worker.archive_numeric_snapshot(value,numeric,receipt,tmp_path)
    assert publication['files']==['config.json','NUMERIC.zip','COMPLETE.json']
    payloads=tmp_path/value['run_id']/publication['tranche_id']/'payloads'
    with zipfile.ZipFile(payloads/'NUMERIC.zip') as archive:
        assert len(archive.namelist())==263
        inventory=json.loads(archive.read('INVENTORY.json'))
        assert len(inventory)==262
        for name,pin in inventory.items():
            import hashlib
            assert hashlib.sha256(archive.read(name)).hexdigest()==pin['sha256']
    assert before=={path.name:worker.sha(path) for path in numeric_root.iterdir()}


def test_numeric_archive_cap_failure_preserves_sources(tmp_path):
    import json
    worker=load('calibration_cloud_worker')
    value=request();numeric_root=tmp_path/value['gpu_output'];numeric_root.mkdir(parents=True)
    (numeric_root/'config.json').write_text(json.dumps(value))
    numeric=dict(shards=[])
    receipt=numeric_root/'RECEIPT.json';receipt.write_text(json.dumps(numeric))
    with pytest.raises(ValueError,match='byte cap'):
        worker.archive_numeric_snapshot(value,numeric,receipt,tmp_path,max_archive_bytes=1)
    assert receipt.exists()


def test_cpu_preflight_uses_real_verifier_contract_and_no_cuda_probe(tmp_path, monkeypatch):
    worker=load('calibration_cloud_worker')
    import platform
    import knowledge_tracing.akt.provenance as provenance
    import knowledge_tracing.akt.research_junyi_calibration as calibration
    import knowledge_tracing.akt.config as config
    scripts=tmp_path/'scripts/akt';scripts.mkdir(parents=True)
    for name in ('calibration_cloud_worker.py','modal_junyi_calibration.py','prepare_junyi_calibration_caches.py',
                 'run_junyi_refit.py','drive_artifact_sink.py','drive_resumable_upload.py'):
        (scripts/name).write_text('synthetic-source')
    calls=[]
    def verify(path,commit):
        calls.append((path,commit))
        return dict(commit=commit,files={'akt.py':'a'*64})
    monkeypatch.setattr(provenance,'verify_upstream',verify)
    monkeypatch.setattr(calibration,'inference_source_identity',lambda:'b'*64)
    monkeypatch.setattr(platform,'python_version',lambda:'3.13.18')
    fake=SimpleNamespace(__version__='2.7.1+cu126',version=SimpleNamespace(cuda='12.6'),
        cuda=SimpleNamespace(is_initialized=lambda:False))
    monkeypatch.setitem(sys.modules,'torch',fake)
    result=worker.runtime_preflight(tmp_path)
    assert calls==[(tmp_path/'artifacts/akt/dependencies/upstream',config.SOURCE_COMMIT)]
    assert result['source_identity']=='b'*64 and len(result['worker_sources'])==6
    assert result['gpu_started'] is False and result['cuda_initialized'] is False
    fake.cuda.is_initialized=lambda:True
    with pytest.raises(ValueError,match='runtime'):
        worker.runtime_preflight(tmp_path)


def test_put_request_is_small_atomic_immutable_and_retryable(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'scripts/akt'))
    controller=load('modal_junyi_calibration')
    value=request()
    first=controller.put_request_atomic(value,'requests/a0-full.json',tmp_path)
    assert first==controller.put_request_atomic(value,'requests/a0-full.json',tmp_path)
    assert first['bytes'] < 2*1024**2
    changed=request();changed['max_cost_usd']=.5
    with pytest.raises(FileExistsError):
        controller.put_request_atomic(changed,'requests/a0-full.json',tmp_path)
    assert not list((tmp_path/'requests').glob('*.partial'))


@pytest.mark.parametrize('path',['../outside.json','/outside.json','other/file.json',
                                'requests/../file.json','requests/file.txt','requests\\file.json'])
def test_put_request_rejects_outside_paths(tmp_path,monkeypatch,path):
    monkeypatch.syspath_prepend(str(ROOT/'scripts/akt'))
    controller=load('modal_junyi_calibration')
    with pytest.raises(ValueError):
        controller.put_request_atomic(request(),path,tmp_path)


def test_put_request_rejects_large_metadata(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'scripts/akt'))
    controller=load('modal_junyi_calibration')
    value=request();value['source_pins']={'synthetic':'x'*(2*1024**2)}
    with pytest.raises(ValueError,match='2MiB'):
        controller.put_request_atomic(value,'requests/large.json',tmp_path)


def test_request_producer_consumer_normalization(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'scripts/akt'))
    controller=load('modal_junyi_calibration');worker=load('calibration_cloud_worker')
    produced=controller.put_request_atomic(request(),'requests/a0.json',tmp_path)
    with pytest.raises(ValueError,match='path/SHA'):
        worker.pinned(produced,tmp_path)
    normalized=controller.request_pin(produced)
    assert set(normalized)=={'path','sha256'}
    assert worker.pinned(normalized,tmp_path).exists()
    with pytest.raises(ValueError):controller.request_pin(dict(produced,unknown=True))


def test_attempt_paths_reuse_exact_gpu_request_without_overwrite(tmp_path):
    import json
    controller=load('modal_junyi_calibration');worker=load('calibration_cloud_worker')
    value=request();before=json.dumps(value,sort_keys=True)
    numeric_root=tmp_path/value['gpu_output'];numeric_root.mkdir(parents=True)
    (numeric_root/'config.json').write_text(json.dumps(value))
    numeric=dict(shards=[]);receipt=numeric_root/'RECEIPT.json';receipt.write_text(json.dumps(numeric))
    outputs=[]
    for attempt in ('allocation-first','allocation-retry'):
        publication=worker.archive_numeric_snapshot(value,numeric,receipt,tmp_path,attempt_id=attempt)
        outputs.append(publication['tranche_id'])
    assert outputs[0]!=outputs[1]
    assert worker.cpu_tranches('A0','allocation-first')['raw']!=worker.cpu_tranches('A0','allocation-retry')['raw']
    assert controller.operation_tranche('A0','cpu-join','allocation-first')!=controller.operation_tranche('A0','cpu-join','allocation-retry')
    assert json.dumps(value,sort_keys=True)==before
    changed=dict(value,max_cost_usd=.5)
    with pytest.raises(ValueError,match='config changed'):
        worker.archive_numeric_snapshot(changed,numeric,receipt,tmp_path,attempt_id='third')
    with pytest.raises(ValueError):worker.cpu_tranches('A0','../unsafe')


def test_metadata_finalizer_failure_empty_logs_and_retry(tmp_path,monkeypatch):
    import json
    monkeypatch.syspath_prepend(str(ROOT/'scripts/akt'))
    controller=load('modal_junyi_calibration')
    name='a0-gpu-operation-test'
    source=tmp_path/'run'/name/'payloads';source.mkdir(parents=True)
    (source/'config.json').write_text('{}')
    (source/'FAILED.json').write_text('{"error_type":"SyntheticError"}')
    (source/'worker.log').write_bytes(b'')
    (source/'gpu-utilization.jsonl').write_text('{"gpu_utilization":70}\n')
    (source/'model.pt').write_bytes(b'not-metadata')
    (source/'token.json').write_text('synthetic-private')
    publications=[]
    def publish(snapshot,publication):
        assert 'worker.log' not in publication['files']
        assert 'model.pt' not in publication['files'] and 'token.json' not in publication['files']
        metadata=json.loads((snapshot/'PUBLICATION.json').read_text())
        assert 'worker.log' in metadata['empty_files'] and 'result.json' in metadata['missing_files']
        publications.append(publication)
        return {'status':'DRIVE_SHA256_VERIFIED'}
    for _ in range(2):
        controller.publish_operation_metadata(tmp_path,'run',[name],publish=publish,volume_commit=lambda:None)
    assert publications[0]==publications[1]
    assert not (source/'PUBLICATION.json').exists()
    (source/'COMPLETE.json').write_text('{}')
    controller.publish_operation_metadata(tmp_path,'run',[name],publish=publish,volume_commit=lambda:None)
    assert publications[-1]['tranche_id']!=publications[0]['tranche_id']


@pytest.mark.parametrize('mode',['running','empty_config','unsafe'])
def test_metadata_finalizer_refuses_invalid_sources(tmp_path,monkeypatch,mode):
    monkeypatch.syspath_prepend(str(ROOT/'scripts/akt'))
    controller=load('modal_junyi_calibration')
    name='a0-cpu-cache-operation-test'
    source=tmp_path/'run'/name/'payloads';source.mkdir(parents=True)
    (source/'config.json').write_text('' if mode=='empty_config' else '{}')
    if mode!='running':(source/'FAILED.json').write_text('{}')
    if mode=='unsafe':name='../outside-operation'
    with pytest.raises(ValueError):
        controller.publish_operation_metadata(tmp_path,'run',[name],publish=lambda *a:pytest.fail('must refuse'),volume_commit=lambda:None)


def test_gpu_monitor_records_sample_and_reaps_child():
    import io
    controller=load('modal_junyi_calibration')
    class Process:
        running=True
        def poll(self):return None if self.running else 0
        def wait(self,timeout):assert not self.running;return 0
    process=Process();calls=[]
    def popen(*args,**kwargs):calls.append(kwargs);return process
    telemetry=io.StringIO()
    controller.run_gpu_monitored(['worker'],io.BytesIO(),telemetry,timeout=10,environment={},
        popen=popen,query=lambda *a,**k:SimpleNamespace(stdout='72,512,81920\n'),clock=lambda:0,
        sleep=lambda seconds:setattr(process,'running',False))
    import json
    assert json.loads(telemetry.getvalue())['gpu_utilization']==72
    assert calls[0]['start_new_session'] is True


def test_gpu_monitor_query_error_terminates_waits_and_kills():
    import io
    import subprocess
    controller=load('modal_junyi_calibration')
    class Process:
        running=True
        terminated=False
        killed=False
        def poll(self):return None if self.running else -9
        def terminate(self):self.terminated=True
        def wait(self,timeout):
            if not self.killed:raise subprocess.TimeoutExpired('worker',timeout)
            self.running=False;return -9
        def kill(self):self.killed=True
    process=Process()
    def fail(*args,**kwargs):raise RuntimeError('synthetic NVML failure')
    with pytest.raises(RuntimeError,match='NVML'):
        controller.run_gpu_monitored(['worker'],io.BytesIO(),io.StringIO(),timeout=10,environment={},
            popen=lambda *a,**k:process,query=fail,clock=lambda:0,sleep=lambda _:None)
    assert process.terminated and process.killed and not process.running


def test_gpu_monitor_timeout_stops_child_without_query():
    import io
    controller=load('modal_junyi_calibration')
    class Process:
        running=True
        terminated=False
        def poll(self):return None if self.running else -15
        def terminate(self):self.terminated=True;self.running=False
        def wait(self,timeout):return -15
    process=Process();times=iter((0,11))
    with pytest.raises(TimeoutError):
        controller.run_gpu_monitored(['worker'],io.BytesIO(),io.StringIO(),timeout=10,environment={},
            popen=lambda *a,**k:process,query=lambda *a,**k:pytest.fail('must stop first'),
            clock=lambda:next(times),sleep=lambda _:None)
    assert process.terminated and not process.running


@pytest.mark.parametrize('variant',['A0','A1'])
def test_gpu_host_timings_partition_and_preserve_numeric_contract(tmp_path,monkeypatch,variant):
    import json
    monkeypatch.syspath_prepend(str(ROOT/'scripts/akt'))
    worker=load('calibration_cloud_worker')
    import knowledge_tracing.akt.cache_artifacts as cache_artifacts
    import knowledge_tracing.akt.research_junyi_calibration as calibration
    import knowledge_tracing.akt.research_junyi_window_cache as window_cache
    import knowledge_tracing.akt.research_junyi_graph_cache as graph_cache
    import knowledge_tracing.akt.research_junyi_graph as graph
    import knowledge_tracing.akt.research_junyi_cached_numeric as numeric
    import run_junyi_refit
    value=request();value['variant']=variant;value['gpu_output']=value['run_id']+'/'+variant.lower()+'-numeric/payloads'
    value['numeric_budget'].update(expected_records=1,expected_windows=1,expected_targets=3)
    view=SimpleNamespace(identity='c'*64)
    encoding=SimpleNamespace(identity='d'*64)
    assets=dict(calibration=view,encoding=encoding,condition=object(),cuda_profile=object(),
        index={'checkpoint_sha256':'a'*64},config=SimpleNamespace(threads=1))
    population=dict(identity='f'*64,targets=3)
    info=dict(population=population,source_pins={},source_data_sha256='a'*64,
        windows=dict(path=str(tmp_path/'windows'),manifest_sha256='e'*64,
            admission_path=str(tmp_path/'admission.json'),admission_sha256='a'*64),
        graphs={variant:dict(path=str(tmp_path/'graph.sqlite'),sha256='a'*64)})
    cache_file=tmp_path/'cache.json';cache_file.write_text(json.dumps(info))
    monkeypatch.setattr(worker,'pinned',lambda *a:cache_file)
    monkeypatch.setattr(worker,'load_inputs',lambda *a,**k:(assets,None,population))
    monkeypatch.setattr(calibration,'inference_source_identity',lambda:value['source_identity'])
    monkeypatch.setattr(cache_artifacts,'JunyiCacheArtifactRoot',lambda root:SimpleNamespace(validate=lambda path:path))
    monkeypatch.setattr(window_cache,'JunyiWindowCacheSession',lambda *a,**k:'admitted-cache')
    monkeypatch.setattr(graph,'JunyiGraphPhaseSession',lambda *a:'graph-phase')
    monkeypatch.setattr(graph_cache,'GraphContextCache',SimpleNamespace(open=lambda *a,**k:'graph-cache'))
    monkeypatch.setattr(run_junyi_refit,'configure_cuda',lambda profile,threads:None)
    received=[]
    def run(loaded,cache,**kwargs):
        received.append(kwargs)
        assert loaded is assets and cache=='admitted-cache'
        kwargs['output_root'].mkdir(parents=True)
        return dict(receipt_path=str(kwargs['output_root']/'RECEIPT.json'),receipt_sha256='a'*64,counts={'targets':3})
    monkeypatch.setattr(numeric,'run_cuda_cached_numeric',run)
    ticks=iter(index*.125 for index in range(100))
    monkeypatch.setattr(worker,'time',SimpleNamespace(monotonic=lambda:next(ticks)))
    committed=[]
    result=worker.gpu_predict(value,tmp_path,volume_commit=lambda:committed.append(True))
    phases=result['host_phase_seconds']
    assert set(phases)=={'request_validation','imports','cache_receipt_read','load_inputs','source_checks',
        'window_session','graph_cache','numeric_binding','configure_cuda','numeric_core','config_write','volume_commit'}
    assert all(seconds>=0 for seconds in phases.values())
    assert sum(phases.values())==pytest.approx(result['worker_seconds'])
    assert result['volume_commit_seconds']==phases['volume_commit']
    assert received[0]['binding'].variant==variant
    assert received[0]['graph_cache']==(None if variant=='A0' else 'graph-cache')
    assert received[0]['budget'].batch_size==128 and committed==[True]
    assert json.loads((tmp_path/value['gpu_output']/'config.json').read_text())==value
