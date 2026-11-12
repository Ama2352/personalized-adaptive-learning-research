"""Một epoch CUDA Junyi để nghiệm thu lifecycle trước training nghiên cứu chính."""
from dataclasses import asdict
import gc
import hashlib
import json
from pathlib import Path
import time

from .config import AKTConfig, ResearchCUDAExecutionProfile, validate_config
from .research_junyi_data import (JunyiPhaseView, fit_junyi_research_encoding,
                                iter_junyi_phase_learners, iter_junyi_research_windows)
from .research_junyi_roles import JunyiResearchRoles


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False, default=str)
        stream.write('\n')


def prepare_inputs(cohort_root, roles_path, *, cohort_sha256, roles_sha256):
    """Kiểm dữ liệu trước import Torch; chỉ trả train và selection."""
    if file_sha(roles_path) != roles_sha256 or file_sha(cohort_root/'manifest.json') != cohort_sha256:
        raise ValueError('Pinned Junyi inputs changed')
    payload = json.loads(roles_path.read_text(encoding='utf-8'))
    for key in ('train_users', 'selection_users', 'calibration_users', 'outer_validation_users'):
        payload[key] = tuple(payload[key])
    roles = JunyiResearchRoles(**payload)
    manifest = json.loads((cohort_root/'manifest.json').read_text(encoding='utf-8'))
    views = {role: JunyiPhaseView(roles, scope, tuple(manifest['roles'][role]['users']), roles.identity)
             for role, scope in (('train', 'select_train80'), ('selection', 'raw_selection10'))}
    if (len(views['train'].users) != 256 or len(views['selection'].users) != 32
            or manifest['max_events_per_user'] != 300
            or any(view.full_role_coverage for view in views.values())):
        raise ValueError('Approved engineering256/32x300 cohort required')
    options = dict(cache_root=cohort_root, expected_cache_manifest_sha256=cohort_sha256)
    encoding = fit_junyi_research_encoding(None, views['train'], **options)
    learners = {role: tuple(iter_junyi_phase_learners(None, view, **options))
                for role, view in views.items()}
    counts = {role: sum(len(x.events) for x in values) for role, values in learners.items()}
    if counts != dict(train=11833, selection=1530):
        raise ValueError('Approved target population changed')
    return views, encoding, learners, options


def engineering_config(run_id):
    from .config import PROJECT_ROOT
    return AKTConfig(phase='junyi-research', run_id=run_id, execution_enabled=True,
        output_dir=PROJECT_ROOT/'experiments/akt/results'/run_id, device='cuda', outer_fold=4,
        max_train_users=256, max_val_users=32, max_targets_per_side=11833,
        max_total_targets=13363, max_steps=79, max_seconds=600, max_wall_seconds=740,
        max_rss_bytes=6*1024**3, min_available_ram_bytes=256*1024**2)


def run_one_epoch(config, profile, *, cohort_root, roles_path, cohort_sha256, roles_sha256):
    """Không lựa epoch hoặc mở calibration; lưu checkpoint epoch hoàn chỉnh."""
    validate_config(config, cuda_profile=profile)
    if config != engineering_config(config.run_id) or type(profile) is not ResearchCUDAExecutionProfile:
        raise ValueError('Exact bounded engineering config required')
    views, encoding, learners, options = prepare_inputs(cohort_root, roles_path,
        cohort_sha256=cohort_sha256, roles_sha256=roles_sha256)
    output = config.output_dir
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    import torch
    from .checkpoint import save_checkpoint, load_checkpoint, restore_checkpoint
    from .model import AKTAdapter
    from .prediction import iter_predictions
    from .research_graph_model import _cuda_execution_check
    from ..gam_kt.evaluation import _metrics
    from .training import train_epoch
    import pandas as pd

    _cuda_execution_check(profile, synchronize=True)
    identity = dict(kind='junyi_a0_one_epoch_engineering_v1', roles=views['train'].roles.identity,
        cohort_sha256=cohort_sha256, encoding_identity=encoding.identity,
        config=asdict(config), profile=asdict(profile))
    # Checkpoint weights_only identity chứa các kiểu JSON nguyên thủy.
    identity = json.loads(json.dumps(identity, default=str))
    write_json(output/'run-manifest.json', dict(identity=identity,
        architecture='AKT_NonRasch_A0', full_junyi_benchmark=False, selected_epoch=None,
        max_workload_epochs=1, scheduler=None, sampler='seed43_shuffle_buffer1024',
        resume_scope='complete_epoch_model_optimizer_rng_only'))

    def new_model():
        torch.random.default_generator.manual_seed(42)
        with torch.device('cpu'):
            adapter = AKTAdapter(config, encoding.native)
        optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr, betas=config.betas,
            eps=config.eps, weight_decay=config.weight_decay, foreach=False, fused=False,
            capturable=False, differentiable=False, amsgrad=False, maximize=False,
            decoupled_weight_decay=False)
        return adapter, optimizer

    adapter, optimizer = new_model()
    events_path = output/'training-events.jsonl'
    with events_path.open('x', encoding='utf-8') as stream:
        def progress(event):
            stream.write(json.dumps(event, allow_nan=False)+'\n')
            stream.flush()
        stats = train_epoch(adapter,
            lambda: iter_junyi_research_windows(None, views['train'], encoding, **options),
            optimizer=optimizer, epoch=1,
            budget=dict(max_steps=79, max_targets=11833, max_seconds=600,
                        max_rss_bytes=config.max_rss_bytes,
                        min_available_ram_bytes=config.min_available_ram_bytes,
                        phase=config.phase, run_id=config.run_id), progress_callback=progress)
    if not stats.complete or stats.optimizer_steps != 79 or stats.valid_targets != 11833:
        raise ValueError('Incomplete approved epoch')
    _cuda_execution_check(profile, synchronize=True)
    write_json(output/'epoch01.json', asdict(stats))
    checkpoint = output/'checkpoints/epoch-001'
    checkpoint.mkdir(parents=True)
    save_checkpoint(checkpoint/'state.pt', adapter, optimizer, identity=identity,
                    progress=dict(complete=True, epoch=1, optimizer_steps=79, valid_targets=11833))
    checkpoint_sha = file_sha(checkpoint/'state.pt')
    write_json(checkpoint/'metadata.json', dict(kind='native_junyi_a0_complete_epoch_v1',
        identity=identity, epoch=1, selected_epoch=None, checkpoint_sha256=checkpoint_sha,
        checkpoint_bytes=(checkpoint/'state.pt').stat().st_size))
    # Marker cuối cùng để controller đồng bộ một checkpoint đã ghi xong.
    write_json(checkpoint/'COMPLETE.json', dict(metadata_sha256=file_sha(checkpoint/'metadata.json'),
        checkpoint_sha256=checkpoint_sha))
    adapter.checkpoint_id = checkpoint_sha
    baseline = tuple(iter_predictions(adapter, learners['selection']))
    del adapter, optimizer
    gc.collect()
    torch.cuda.empty_cache()
    payload = load_checkpoint(checkpoint/'state.pt', expected_identity=identity, device='cuda')
    adapter, optimizer = new_model()
    restore_checkpoint(adapter, optimizer, payload)
    del payload, optimizer
    adapter.checkpoint_id = checkpoint_sha
    reloaded = tuple(iter_predictions(adapter, learners['selection']))
    if baseline != reloaded:
        raise ValueError('Fresh checkpoint reload changed exported predictions or target identities')
    records = [asdict(x) for x in reloaded]
    supported = [x for x in records if x['prediction'] is not None]
    if len(records) != 1530 or len(supported) != 1405 or len({x['source_row'] for x in records}) != 1530:
        raise ValueError('Selection/OOV/export population mismatch')
    with (output/'selection-predictions.jsonl').open('x', encoding='utf-8') as stream:
        for record in records:
            stream.write(json.dumps(record, allow_nan=False)+'\n')
    metrics = _metrics(pd.DataFrame(supported))
    native_bce = float(torch.nn.functional.binary_cross_entropy(
        torch.tensor([x['prediction'] for x in supported], dtype=torch.float32, device='cpu'),
        torch.tensor([x['correct'] for x in supported], dtype=torch.float32, device='cpu')).item())
    terminal = dict(status='ACTUAL_JUNYI_A0_CUDA_ONE_EPOCH_COMPLETE',
        full_junyi_benchmark=False, main_matrix_completed=False, selected_epoch=None,
        complete_epochs=1, optimizer_steps=79, trained_targets=11833,
        selection_targets=1530, supported_targets=1405, oov_targets=125,
        supported_metrics=metrics, full_population_metrics=None,
        epoch_selection_objective_native_bce=native_bce, fresh_checkpoint_reload=True,
        checkpoint_sha256=checkpoint_sha, elapsed_seconds=time.monotonic()-started,
        resource=_cuda_execution_check(profile, synchronize=True))
    if terminal['elapsed_seconds'] > config.max_wall_seconds:
        raise TimeoutError('Junyi engineering wall budget exceeded')
    write_json(output/'engineering-terminal.json', terminal)
    write_json(output/'COMPLETE.json', dict(status='COMPLETE_JUNYI_A0_ONE_EPOCH_ENGINEERING',
        terminal_sha256=file_sha(output/'engineering-terminal.json')))
    return terminal
