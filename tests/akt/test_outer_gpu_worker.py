"""GPUworkerrequest/hook tests chỉcallbackgiả, không importTorch/Modal."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def worker():
    path = Path(__file__).resolve().parents[2]/'scripts/akt/outer_gpu_worker.py'
    spec = importlib.util.spec_from_file_location('outer_gpu_worker_test', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture
def outer_request():
    pin = dict(path='/artifacts/input/file.json',sha256='a'*64)
    return dict(kind='JUNYI_OUTER_GPU_REQUEST_V1',workspace='honguyenminhsang2016',
        run_id='junyi-outer-real-20261117-01',variant='A2',
        source_identity='7c72414eedf9507d514430aed4734f0a192ab14914a4984b17fdfcbfebd39123',
        exports={v:dict(pin) for v in ('A0','A1','A2','A3')},
        calibrators={v:dict(pin,identity='b'*64) for v in ('A0','A1','A2','A3')},
        compatibility={v:dict(pin) for v in ('A0','A1','A2','A3')},
        calibration_data_sha256='c'*64,
        cache_receipt=dict(pin),window_location='/artifacts/outer/windows',
        admission_location='/artifacts/outer/WINDOW_ADMISSION.json',
        graph_locations={v:'/artifacts/outer/'+v+'.sqlite' for v in ('A1','A2','A3')},
        numeric_budget=dict(max_seconds=240,max_rss_bytes=6*1024**3,max_vram_bytes=64*1024**3,
            expected_records=72567,expected_windows=72423,expected_targets=4137050,
            expected_oov_targets=144,batch_size=128),
        cpu_budget=dict(max_targets=4137050,max_users=39616,max_learner_events=21908,
            max_seconds=240,max_rss_bytes=6*1024**3,min_available_ram_bytes=512*1024**2,
            prediction_batch_size=128),gpu_output='junyi-outer-real-20261117-01/a2-outer-numeric/payloads',
        full_cohort_approved=True,max_cost_usd=.75)


def test_request_strict_full_outer(worker, outer_request):
    assert worker.validate_outer_request(outer_request) is outer_request


@pytest.mark.parametrize('field,value', [('source_identity','d'*64),('max_cost_usd',.76),
    ('full_cohort_approved',False),('workspace','other')])
def test_bad_request_refused(worker, outer_request, field, value):
    outer_request[field]=value
    with pytest.raises((ValueError,PermissionError)):
        worker.validate_outer_request(outer_request)


@pytest.mark.parametrize('field,value',[('max_seconds',float('nan')),('max_seconds',301),
    ('batch_size',4),('expected_oov_targets',0)])
def test_bad_numeric_contract_refused(worker, outer_request, field,value):
    outer_request['numeric_budget'][field]=value
    with pytest.raises(ValueError):
        worker.validate_outer_request(outer_request)


def test_null_calibrator_pins_fail_before_gpu(worker,outer_request):
    outer_request['calibrators']['A3']['sha256']=None
    with pytest.raises(ValueError):worker.validate_outer_request(outer_request)


def test_cpu_budget_cannot_mismatch_outer(worker,outer_request):
    outer_request['cpu_budget']['max_users']=15847
    with pytest.raises(ValueError):worker.validate_outer_request(outer_request)


@pytest.mark.parametrize('fail',[False,True])
def test_admitted_builder_sets_outer_before_check_and_always_restores(worker,fail):
    calls=[]
    predictor=SimpleNamespace(adapter=SimpleNamespace(set_phase=lambda phase,**kw:calls.append('phase')))
    def original(*args,**kwargs):
        calls.append('build')
        return predictor
    module=SimpleNamespace(build_cuda_refit_predictor=original)
    def admit(*args,**kwargs):
        calls.append('admit')
        if fail:
            raise ValueError('synthetic rejected admission')
        return dict(status='admitted')
    admission={}
    def run():
        with worker.admitted_predictor_builder(module,admit=admit,view='outer',graph_cache='graph',
                phase='outerphase',calibration='frozenT',compatibility='receipt',
                source_sha256='a'*64,outer_data_sha256='b'*64,calibration_data_sha256='c'*64,
                admission_output=admission):
            assert module.build_cuda_refit_predictor({},domain_sha256='b'*64) is predictor
    if fail:
        with pytest.raises(ValueError):run()
    else:
        run()
        assert admission==dict(status='admitted')
    assert calls==['build','phase','admit']
    assert module.build_cuda_refit_predictor is original


def test_gpu_factory_only_declares_one_h100_function(monkeypatch):
    import sys
    path = Path(__file__).resolve().parents[2]/'scripts/akt/modal_junyi_outer.py'
    spec = importlib.util.spec_from_file_location('outer_factory_fake_test',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    declarations=[]
    class App:
        def __init__(self,name):self.name=name
        def function(self,**kwargs):
            declarations.append(kwargs)
            return lambda function:function
    monkeypatch.setitem(sys.modules,'modal',SimpleNamespace(App=App))
    app, function = module.create_outer_gpu_app('provided-image','provided-volume')
    assert len(declarations)==1
    assert declarations[0]['gpu']=='H100!'
    assert declarations[0]['timeout']==300
    assert declarations[0]['max_containers']==1
    assert declarations[0]['retries']==0
    assert declarations[0]['single_use_containers'] is True
    assert 'secrets' not in declarations[0]
