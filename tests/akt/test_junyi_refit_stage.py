"""Kiểm hợp đồng refit handoff; mọi cloud call được chặn/giả lập."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts/akt'), str(ROOT / 'experiments/akt')]
import modal_junyi_refit as modal_refit
import modal_junyi_staged as staged
import prepare_junyi_refit_stage as preparer
import run_junyi_refit as cli


@pytest.fixture
def worker():
    return dict(purpose='refit90', variant='A2', logical_run_id='unit-refit90', frozen_epochs=9,
        refit_request=dict(path='request.json', sha256='a' * 64),
        config=dict(phase='junyi-research', run_id='unit-refit90', batch_size=128, seed=42,
                    max_wall_seconds=30, max_seconds=25), profile=dict(max_vram_bytes=12 * 1024**3))


@pytest.fixture
def execution():
    return dict(status='USER_APPROVED', approval_reference='synthetic-test-only', execution_id='unit-attempt',
        gpu='T4', child_timeout_seconds=150, function_timeout_seconds=180, watchdog_seconds=210,
        reserved_usd_per_run=.11)


@pytest.mark.parametrize('variant', ['A0', 'A1', 'A2', 'A3'])
def test_refit_resource_contract_accepts_four_variants(worker, execution, variant):
    worker['variant'] = variant
    assert modal_refit.validate_refit_execution(execution, worker)['upper_usd'] <= .11


@pytest.mark.parametrize('key,value', [('purpose', 'main_selected'), ('variant', 'A9'),
    ('frozen_epochs', True), ('frozen_epochs', 0), ('frozen_epochs', 21), ('refit_request', None)])
def test_refit_worker_rejects_wrong_scope(worker, execution, key, value):
    worker[key] = value
    with pytest.raises(ValueError):
        modal_refit.validate_refit_execution(execution, worker)


@pytest.mark.parametrize('change', [dict(status='DRAFT'), dict(reserved_usd_per_run=.001),
    dict(gpu='unknown'), dict(watchdog_seconds=100), dict(execution_id='../invalid')])
def test_refit_retains_budget_guard(worker, execution, change):
    with pytest.raises((ValueError, PermissionError)):
        modal_refit.validate_refit_execution(dict(execution, **change), worker)


def test_unknown_gpu_worker_blocked_before_snapshot_or_cloud(tmp_path):
    with pytest.raises(ValueError):
        staged.run(tmp_path / 'missing', {}, worker_entrypoint='unrestricted.py')


@pytest.mark.parametrize('mutation', ['none', 'config', 'profile', 'epoch', 'variant'])
def test_preparer_binds_inline_worker_to_pinned_inputs(tmp_path, monkeypatch, worker, mutation):
    config = tmp_path / 'config.json'
    config.write_text(json.dumps(worker['config']))
    profile = tmp_path / 'profile.json'
    profile.write_text(json.dumps(worker['profile']))
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps(dict(candidates={'A2': dict(epochs=9)})))
    request = dict(phase='junyi_refit90', variant='A2', config=config, cuda_profile=profile, epoch_plan=plan)
    monkeypatch.setattr(cli, 'pinned', lambda value: value)
    worker = deepcopy(worker)
    if mutation == 'config':
        worker['config']['seed'] = 43
    if mutation == 'profile':
        worker['profile']['max_vram_bytes'] = 16 * 1024**3
    if mutation == 'epoch':
        worker['frozen_epochs'] = 8
    if mutation == 'variant':
        worker['variant'] = 'A3'
    if mutation == 'none':
        preparer.validate_worker(worker, request)
    else:
        with pytest.raises(ValueError):
            preparer.validate_worker(worker, request)


@pytest.mark.parametrize('invalid', [False, 'wrong_parent', 'wrong_name'])
def test_output_guard_resolves_both_volume_paths(tmp_path, monkeypatch, invalid):
    from types import SimpleNamespace
    root = tmp_path / 'repository'
    base = root / 'experiments/akt/results'
    mounted = tmp_path / 'mounted-volume'
    original = type(base).resolve
    def resolve(path, *args, **kwargs):
        if path == base:
            return mounted
        if path == base / 'logical-refit':
            return mounted / 'logical-refit'
        return original(path, *args, **kwargs)
    monkeypatch.setattr(cli, 'ROOT', root)
    monkeypatch.setattr(type(base), 'resolve', resolve)
    config = SimpleNamespace(output_dir=base / 'logical-refit', run_id='logical-refit')
    if invalid == 'wrong_parent':
        config.output_dir = tmp_path / 'unowned/logical-refit'
    if invalid == 'wrong_name':
        config.run_id = 'another-run'
    if invalid:
        with pytest.raises(ValueError, match='owned'):
            cli.validate_output_root(config)
    else:
        cli.validate_output_root(config)


@pytest.mark.parametrize('available,count,total', [(True, 1, 80), (False, 1, 80),
    (True, 2, 80), (True, 1, 8)])
def test_refit_cuda_setup_accepts_research_budget_and_checks_device(monkeypatch, available, count, total):
    from types import SimpleNamespace as NS
    calls = []
    cuda = NS(is_available=lambda: available, device_count=lambda: count,
        get_device_properties=lambda index: NS(total_memory=total * 1024**3),
        set_per_process_memory_fraction=lambda fraction, index: calls.append((fraction, index)))
    torch = NS(cuda=cuda, float32='float32', set_num_threads=lambda value: None,
        set_default_dtype=lambda value: None, use_deterministic_algorithms=lambda *a, **k: None,
        set_float32_matmul_precision=lambda value: None,
        backends=NS(cuda=NS(matmul=NS(allow_tf32=True)), cudnn=NS(allow_tf32=True, benchmark=True)))
    monkeypatch.setitem(sys.modules, 'torch', torch)
    profile = NS(max_vram_bytes=16 * 1024**3, cublas_workspace_config=':4096:8')
    if available and count == 1 and total >= 16:
        cli.configure_cuda(profile, 2)
        assert calls == [(.2, 0)]
        assert torch.backends.cuda.matmul.allow_tf32 is False
    else:
        with pytest.raises(ValueError):
            cli.configure_cuda(profile, 2)
        assert calls == []
