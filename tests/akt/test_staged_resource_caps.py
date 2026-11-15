"""Khóa cận CPU/RAM của controller, giữ cấu hình model không đổi."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('staged_resource_caps', ROOT/'experiments/akt/modal_junyi_staged.py')
STAGED = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STAGED)


@pytest.fixture
def inputs():
    here = ROOT/'research_tracking/runs/junyi-refit-pipeline-20261114-01'
    request = json.loads((here/'a3-refit-execution04.json').read_text())
    worker = json.loads((here/'stage-inputs-a3-short01.json').read_text())['worker']
    return request, worker


def test_defaults_preserve_previous_resource_cost(inputs):
    request, worker = inputs
    result = STAGED.validate_resource_budget(request, worker)
    assert result['upper_usd'] == pytest.approx(.22986)
    assert result['gpu_cpu_max'] == 4
    assert result['gpu_memory_max_mib'] == 12288


def test_two_threads_eight_gib_fit_without_model_change(inputs):
    request, worker = inputs
    original = copy.deepcopy(worker)
    request.update(gpu_cpu_max=2, gpu_memory_max_mib=8192, reserved_usd_per_run=.18)
    result = STAGED.validate_resource_budget(request, worker)
    assert result['upper_usd'] == pytest.approx(.1771)
    assert worker == original


@pytest.mark.parametrize('field,value', [('gpu_cpu_max',1), ('gpu_cpu_max',True),
    ('gpu_cpu_max',5), ('gpu_memory_max_mib',6144), ('gpu_memory_max_mib',16384)])
def test_invalid_caps_rejected(inputs, field, value):
    request, worker = inputs
    request[field] = value
    with pytest.raises(ValueError):
        STAGED.validate_resource_budget(request, worker)


def test_cap_below_worker_rss_rejected(inputs):
    request, worker = inputs
    request['gpu_memory_max_mib'] = 8192
    worker['config']['max_rss_bytes'] = 9*1024**3
    with pytest.raises(ValueError):
        STAGED.validate_resource_budget(request, worker)


def test_active_function_budget_bounds_both_cpu_and_gpu_startup(inputs):
    request, worker = inputs
    request.update(gpu_cpu_max=2, gpu_memory_max_mib=8192,
                   active_function_budget=True, watchdog_seconds=900, reserved_usd_per_run=.20)
    result = STAGED.validate_resource_budget(request, worker)
    assert result['upper_usd'] == pytest.approx(.1988828)
    request['reserved_usd_per_run'] = .19
    with pytest.raises(PermissionError):
        STAGED.validate_resource_budget(request, worker)


def test_active_function_budget_rejects_implicit_string_flag(inputs):
    request, worker = inputs
    request['active_function_budget'] = 'true'
    with pytest.raises(ValueError):
        STAGED.validate_resource_budget(request, worker)
