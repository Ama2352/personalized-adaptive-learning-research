"""Mocked hardware contracts only; không CUDA device/training/Modal execution."""
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from knowledge_tracing.akt import runner
from knowledge_tracing.akt.config import PROJECT_ROOT, load_config, validate_config
from knowledge_tracing.akt.device_budget import configure_cuda_budget, cuda_budget_snapshot


class FakeCuda:
    def __init__(self):self.calls=[];self.available=True;self.count=1;self.total=8*1024**3
    def is_available(self):return self.available
    def device_count(self):return self.count
    def get_device_properties(self,index):return SimpleNamespace(total_memory=self.total)
    def get_device_name(self,index):return 'MOCK_GPU_NOT_ACTUAL_DEVICE'
    def set_per_process_memory_fraction(self,*args):self.calls.append(('fraction',args))
    def reset_peak_memory_stats(self,*args):self.calls.append(('reset',args))
    def memory_allocated(self,index):return 128
    def memory_reserved(self,index):return 256
    def max_memory_allocated(self,index):return 512
    def max_memory_reserved(self,index):return 1024


def test_cuda_allocator_budget_and_snapshot():
    cuda=FakeCuda();cap=2*1024**3
    report=configure_cuda_budget(cuda,max_vram_bytes=cap)
    assert cuda.calls==[('fraction',(0.25,0)),('reset',(0,))]
    assert report['visible_devices']==1 and report['max_vram_bytes']==cap
    assert cuda_budget_snapshot(cuda,max_vram_bytes=cap)['max_memory_allocated']==512


@pytest.mark.parametrize('field,value',[('available',False),('count',0),('count',2),('count',True),('total',1024)])
def test_cuda_budget_refuses_wrong_device_or_unavailable_hardware(field,value):
    cuda=FakeCuda();setattr(cuda,field,value)
    with pytest.raises(ValueError):configure_cuda_budget(cuda,max_vram_bytes=2*1024**3)
    assert cuda.calls==[]


@pytest.mark.parametrize('cap',[True,1,3*1024**3])
def test_cuda_budget_rejects_unbounded_or_invalid_allocation(cap):
    with pytest.raises(ValueError):configure_cuda_budget(FakeCuda(),max_vram_bytes=cap)


def test_cuda_peak_memory_stops_on_budget_exhaustion():
    with pytest.raises(MemoryError,match='budget'):
        cuda_budget_snapshot(FakeCuda(),max_vram_bytes=512)


def cuda_config(tmp_path):
    base=load_config(PROJECT_ROOT/'experiments/akt/configs/smoke.json')
    return replace(base,phase='cuda-smoke',device='cuda',run_id='c',output_dir=tmp_path/'c',execution_enabled=True)


def test_new_cuda_phase_does_not_enable_cuda_on_legacy_cpu_phase(tmp_path):
    config=cuda_config(tmp_path);validate_config(config)
    for invalid in (replace(config,phase='smoke'),replace(config,device='cpu'),replace(config,max_steps=21)):
        with pytest.raises(ValueError):validate_config(invalid)


def test_cuda_entry_requires_context_before_any_runtime_or_data_access(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'_require_authorization',lambda *a,**k:pytest.fail('must reject before auth'))
    with pytest.raises(ValueError,match='context'):runner.run_cuda_smoke(cuda_config(tmp_path))


def test_cuda_setup_failure_keeps_original_error_and_manifest(tmp_path,monkeypatch):
    config=cuda_config(tmp_path)
    context=SimpleNamespace(validate_for=lambda cfg:None,cuda_limits=SimpleNamespace(max_vram_bytes=2*1024**3))
    names=('max_train_users','max_val_users','max_targets_per_side','max_steps','max_seconds',
           'max_wall_seconds','max_rss_bytes','min_available_ram_bytes')
    approval={'caps':{n:getattr(config,n) for n in names},'identity':{'fixture':'no_real_authorization'},
              'approval_reference':'Synthetic error-path fixture; no actual GPU'}
    monkeypatch.setattr(runner,'_require_authorization',lambda *a,**k:approval)
    monkeypatch.setattr(runner,'_require_gate2_evidence',lambda *a,**k:{'fixture':True})
    monkeypatch.setattr(runner,'_check_resource_budget',lambda *a,**k:0)
    monkeypatch.setattr(runner,'_load_phase_inputs',lambda *a,**k:pytest.fail('no loader before CUDA setup'))
    def fail(*args,**kwargs):raise ValueError('MOCK_CUDA_SETUP_FAILURE')
    monkeypatch.setattr(runner,'configure_cuda_budget',fail)
    with pytest.raises(ValueError,match='MOCK_CUDA_SETUP_FAILURE'):
        runner.run_cuda_smoke(config,authorization=approval,context=context)
    result=json.loads((config.output_dir/'manifest.json').read_text(encoding='utf-8'))
    assert result['error']=='MOCK_CUDA_SETUP_FAILURE' and result['status']=='incomplete'
    assert not list(config.output_dir.glob('*.pt'))
