"""Refit Junyi theo epoch đã đóng băng, dùng lại trainer và checkpoint native.

Chuẩn bị trên CPU riêng. Entrypoint CUDA yêu cầu grant, Gate và runtime ghim.
Plan chỉ đóng băng epoch cho nhóm A0–A3 expert, giữ mọi candidate để so sánh.
"""
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import time
import uuid

from .config import AKTConfig, ResearchCUDAExecutionProfile, validate_config
from .research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from .research_junyi_selection import _identity, _make_selected_adapter
from .research_junyi_engineering import file_sha, write_json


@dataclass(frozen=True)
class JunyiRefitInputs:
    view: JunyiPhaseView
    targets: int
    source_identity: str
    selected_inputs_identity: str

    def __post_init__(self):
        if (type(self.view) is not JunyiPhaseView or self.view.scope != 'refit_union90'
                or not self.view.full_role_coverage or type(self.targets) is not int or self.targets <= 0
                or type(self.source_identity) is not str or len(self.source_identity) != 64
                or any(char not in '0123456789abcdef' for char in self.source_identity)
                or type(self.selected_inputs_identity) is not str or len(self.selected_inputs_identity) != 64):
            raise ValueError('Full refit90 view and pinned target population required')

    @property
    def identity(self):
        return _identity(dict(view=self.view.identity, targets=self.targets, source=self.source_identity,
                              selected_inputs=self.selected_inputs_identity))


def refit_view(selected_inputs):
    roles = selected_inputs.train.roles
    view = JunyiPhaseView(roles, 'refit_union90',
        tuple(sorted((*roles.train_users, *roles.selection_users))), roles.identity)
    return JunyiRefitInputs(view, selected_inputs.train_targets + selected_inputs.selection_targets,
                            selected_inputs.source_identity, selected_inputs.identity)


def make_epoch_plan(indices, *, roles_identity):
    """Tái dùng epoch đã chọn; kiểm các index cùng protocol trước tạo plan."""
    from .comparison_contract import TRAINING_FIELDS
    if set(indices) != {'A0', 'A1', 'A2', 'A3'}:
        raise ValueError('All four expert candidate indices required')
    reference = indices['A0']['metadata']['identity']
    records = {}
    population = indices['A0']['selection_metrics']['population_sha256']
    for variant, index in indices.items():
        identity = index['metadata']['identity']
        if (index['phase'] != 'selected_fit80' or type(index['selected_epoch']) is not int
                or index['model'].split('_')[0] != variant
                or index['metadata']['epoch'] != index['selected_epoch']
                or any(value != identity['profile'].get(key) for key, value in reference['profile'].items()
                       if key != 'max_vram_bytes')
                or not 1 <= index['selected_epoch'] <= index['complete_epochs'] <= 20
                or identity['inputs'] != reference['inputs'] or identity['encoding'] != reference['encoding']
                or any(identity['config'][name] != reference['config'][name] for name in TRAINING_FIELDS)
                or index['selection_metrics']['population_sha256'] != population
                or index['refit_completed'] is not False or index['calibration_completed'] is not False):
            raise ValueError('Selected candidates differ in data/training or completed phase')
        records[variant] = dict(epochs=index['selected_epoch'], checkpoint_sha256=index['checkpoint_sha256'],
                               selected_index_sha256=_identity(index))
    payload = dict(schema='junyi-expert-epoch-plan-v1', scope='A0_A1_A2_A3_EXPERT_FOLD4',
        roles_identity=roles_identity, candidates=records,
        training_config={name: reference['config'][name] for name in TRAINING_FIELDS},
        selected_inputs_identity=reference['inputs'], selected_encoding_identity=reference['encoding'],
        numeric_profile=reference['profile'], selection_population_sha256=population,
        confidence_policy='frozen_train80_through_neural_refit90', system_winner_selected=False,
        a0_full_epoch_ranking_batch128_replayed=False)
    return dict(payload, identity=_identity(payload))


def validate_epoch_plan(plan, *, config, profile, inputs):
    from .comparison_contract import TRAINING_FIELDS
    payload = {key: value for key, value in plan.items() if key != 'identity'}
    if (plan.get('identity') != _identity(payload) or plan.get('schema') != 'junyi-expert-epoch-plan-v1'
            or plan.get('scope') != 'A0_A1_A2_A3_EXPERT_FOLD4'
            or plan.get('roles_identity') != inputs.view.roles.identity
            or plan.get('selected_inputs_identity') != inputs.selected_inputs_identity
            or plan.get('confidence_policy') != 'frozen_train80_through_neural_refit90'
            or plan.get('system_winner_selected') is not False
            or set(plan.get('candidates', {})) != {'A0', 'A1', 'A2', 'A3'}):
        raise ValueError('Frozen scoped epoch plan or roles changed')
    values = json.loads(json.dumps(asdict(config), default=str))
    if any(values[key] != plan['training_config'][key] for key in TRAINING_FIELDS):
        raise ValueError('Refit training configuration differs from selected candidates')
    actual_profile = asdict(profile)
    if any(value != actual_profile.get(key) for key, value in plan['numeric_profile'].items()
           if key != 'max_vram_bytes'):
        raise ValueError('Refit numeric recipe differs from selected candidates')
    if any(type(row.get('epochs')) is not int or not 1 <= row['epochs'] <= 20
           for row in plan['candidates'].values()):
        raise ValueError('Invalid frozen epoch count')


def _run_epochs(adapter, windows_factory, *, optimizer, output, identity, epochs, targets,
                max_seconds, budget, checkpoint_every_steps=1000, resume=None, checkpoint_callback=None,
                launch_evidence=None, total_max_steps=None, total_max_targets=None):
    """Dùng train_epoch hiện có, lưu cả sampler/RNG khi chạm giới hạn tranche."""
    from .checkpoint import load_training_snapshot, restore_checkpoint, save_checkpoint
    from .training import train_epoch
    output = Path(output)
    output.mkdir(parents=True, exist_ok=resume is not None)
    manifest = output / 'run-manifest.json'
    if resume is None:
        write_json(manifest, identity)
    elif json.loads(manifest.read_text()) != identity or (output / 'COMPLETE.json').exists():
        raise ValueError('Resume requires identical unfinished refit')
    history, first, epoch_resume = [], 1, None
    if resume is not None:
        payload = load_training_snapshot(resume, expected_identity=identity, device='cpu')
        if payload.get('checkpoint_kind') == 'training_recovery_v1':
            state = payload['resume_state']['trainer_state']['selection_state']
            first, epoch_resume = payload['resume_state']['epoch'], resume
        else:
            state = payload['progress']
            restore_checkpoint(adapter, optimizer, payload)
            first = state['epoch'] + 1
        history = list(state['history'])
        if (state.get('role') != 'junyi_refit90' or len(history) != first - 1
                or [row['epoch'] for row in history] != list(range(1, first))
                or any(row['valid_targets'] != targets for row in history)):
            raise ValueError('Invalid refit checkpoint history or target count')
        del payload
    started = time.monotonic()
    recovery_root = output / 'batch-recovery'
    recovery_root.mkdir(exist_ok=True)
    def publish(path):
        directory = output / 'checkpoints' / (path.stem if path.parent == recovery_root else path.parent.name)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / 'state.pt'
        if path != target:
            os.link(path, target)
        digest = file_sha(target)
        metadata = directory / 'metadata.json'
        write_json(metadata, dict(checkpoint_sha256=digest, checkpoint_bytes=target.stat().st_size, identity=identity))
        write_json(directory / 'COMPLETE.json', dict(checkpoint_sha256=digest, metadata_sha256=file_sha(metadata)))
        if checkpoint_callback is not None:
            checkpoint_callback(target)
    attempt = uuid.uuid4().hex
    write_json(output / ('attempt-' + attempt + '.json'), dict(
        resume_sha256=None if resume is None else file_sha(resume), launch_evidence=launch_evidence))
    for epoch in range(first, epochs + 1):
        remaining = max_seconds - (time.monotonic() - started)
        if remaining <= 5:
            break
        previous_wall = 0.
        if epoch_resume is not None:
            payload = load_training_snapshot(epoch_resume, expected_identity=identity, device='cpu')
            previous_wall = payload['resume_state']['trainer_state']['stats']['resource']['wall_seconds']
            del payload
        epoch_budget = dict(budget, max_seconds=previous_wall + min(budget['max_seconds'], remaining - 5))
        if total_max_steps is not None:
            left = total_max_steps - sum(row['optimizer_steps'] for row in history)
            if left <= 0:
                break
            epoch_budget['max_steps'] = min(epoch_budget['max_steps'], left)
        if total_max_targets is not None:
            left = total_max_targets - sum(row['valid_targets'] for row in history)
            if left <= 0:
                break
            epoch_budget['max_targets'] = min(epoch_budget['max_targets'], left)
        state = dict(role='junyi_refit90', epoch=epoch, history=list(history))
        kwargs = {}
        if hasattr(adapter, 'collate_training'):
            kwargs['batch_factory'] = adapter.collate_training
        with (output / f'epoch-{epoch:03}-{attempt}-progress.jsonl').open('x', encoding='utf-8') as log:
            def progress(event):
                if event['training']['optimizer_steps'] % 100 == 0 or event['complete_epoch']:
                    log.write(json.dumps(event, allow_nan=False) + '\n')
                    log.flush()
            stats = train_epoch(adapter, windows_factory, optimizer=optimizer, epoch=epoch, budget=epoch_budget,
                recovery=dict(prefix='refit', checkpoint_dir=recovery_root, identity=identity,
                    checkpoint_every_steps=checkpoint_every_steps, resume_checkpoint=epoch_resume,
                    selection_state=state, checkpoint_callback=publish), progress_callback=progress, **kwargs)
        epoch_resume = None
        write_json(output / f'epoch-{epoch:03}-{attempt}.json', asdict(stats))
        if not stats.complete:
            break
        if stats.valid_targets != targets:
            raise ValueError('Complete refit epoch target population differs')
        history.append(dict(epoch=epoch, valid_targets=stats.valid_targets,
                            optimizer_steps=stats.optimizer_steps, loss_sum=stats.loss_sum, resource=stats.resource))
        checkpoint = output / 'checkpoints' / f'epoch-{epoch:03}' / 'state.pt'
        checkpoint.parent.mkdir(parents=True)
        save_checkpoint(checkpoint, adapter, optimizer, identity=identity,
            progress=dict(role='junyi_refit90', complete=True, epoch=epoch, history=list(history)))
        publish(checkpoint)
    finished = len(history) == epochs
    result = dict(status='JUNYI_REFIT90_COMPLETE' if finished else 'PARTIAL_JUNYI_REFIT90',
        complete_epochs=len(history), frozen_epochs=epochs, history=history,
        calibration_performed=False, independent_evaluation_performed=False)
    if finished:
        checkpoint = output / 'checkpoints' / f'epoch-{epochs:03}' / 'state.pt'
        # Kiểm lại serialization, model/optimizer/RNG theo cùng API checkpoint.
        payload = load_training_snapshot(checkpoint, expected_identity=identity, device='cpu')
        import torch
        if not all(torch.isfinite(value).all().item() for value in payload['model_state_dict'].values()):
            raise ValueError('Nonfinite final refit checkpoint')
        result.update(checkpoint=checkpoint.relative_to(output).as_posix(), checkpoint_sha256=file_sha(checkpoint))
        write_json(output / 'COMPLETE.json', result)
    else:
        write_json(output / ('partial-' + attempt + '.json'), result)
    return result


def refit_grant_binding(*, config, inputs, encoding, variant, plan, window_cache, gate_sha256,
                        runtime_sha256, graph_condition=None, graph_cache=None):
    """Dữ liệu cần ghim trong grant do caller được ủy quyền lập."""
    from .authorization import config_hash
    return dict(phase='junyi_refit90', variant=variant, plan_sha256=plan['identity'],
        config_sha256=config_hash(config),
        inputs=inputs.identity, encoding=encoding.identity, window_identity=window_cache.expected_manifest_sha256,
        gate_sha256=gate_sha256, runtime_sha256=runtime_sha256,
        condition=None if graph_condition is None else graph_condition.identity,
        graph_cache=None if graph_cache is None else graph_cache.identity,
        epochs=plan['candidates'][variant]['epochs'])


def validate_selected_lineage(plan, variant, selected_index, graph_condition):
    """Khóa đúng index đã đóng băng và dựng lại condition80 để kiểm confidence."""
    if _identity(selected_index) != plan['candidates'][variant]['selected_index_sha256']:
        raise ValueError('Selected model index differs from frozen plan')
    if graph_condition is not None:
        from .research_junyi_graph import JunyiGraphCondition
        selected_condition = JunyiGraphCondition(graph_condition.train80_origin, graph_condition.graph,
            graph_condition.topology_source_sha256, variant=variant, confidence=graph_condition.confidence)
        if selected_condition.identity != selected_index['graph_condition_sha256']:
            raise ValueError('Refit topology/confidence differs from selected TRAIN80 condition')


def run_junyi_refit(config: AKTConfig, profile: ResearchCUDAExecutionProfile, inputs: JunyiRefitInputs,
                    encoding: JunyiResearchEncoding, *, variant, plan, expected_plan_sha256,
                    selected_index, grant, runtime_report, lock_file, gate2_report, window_cache,
                    graph_condition=None, graph_cache=None, resume=None, expected_resume_sha256=None,
                    checkpoint_callback=None):
    """Entrypoint thật chỉ nhận input đã chuẩn bị và grant khớp byte/source/runtime."""
    from .authorization import preflight, require_gate2_evidence
    from .training import _seed
    validate_config(config, cuda_profile=profile)
    if config.phase != 'junyi-research' or type(inputs) is not JunyiRefitInputs:
        raise ValueError('Explicit Junyi research refit required')
    validate_epoch_plan(plan, config=config, profile=profile, inputs=inputs)
    if plan['identity'] != expected_plan_sha256:
        raise ValueError('Epoch plan pin changed')
    encoding.assert_for(inputs.view)
    from .research_junyi_window_cache import JunyiWindowCacheSession
    if (type(window_cache) is not JunyiWindowCacheSession or window_cache.view.identity != inputs.view.identity
            or window_cache.encoding.identity != encoding.identity
            or window_cache.source_data_sha256 != inputs.source_identity
            or window_cache.expected_target_rows != inputs.targets):
        raise ValueError('Pinned refit90 window cache required')
    if variant not in plan['candidates'] or (variant == 'A0') != (graph_condition is None):
        raise ValueError('Refit variant/graph mismatch')
    if graph_condition is not None:
        graph_condition.assert_integrity()
        if (graph_condition.variant != variant or graph_condition.encoding is not encoding
                or graph_condition.train80_origin is None
                or graph_condition.train80_origin.identity != plan['selected_encoding_identity']):
            raise ValueError('Refit graph must retain frozen TRAIN80 lineage')
    validate_selected_lineage(plan, variant, selected_index, graph_condition)
    gate = require_gate2_evidence(config, gate2_report=gate2_report, lock_file=lock_file)
    preflight(config, runtime_report_path=runtime_report, lock_file=lock_file, cuda_profile=profile)
    epochs = plan['candidates'][variant]['epochs']
    binding = refit_grant_binding(config=config, inputs=inputs, encoding=encoding, variant=variant,
        plan=plan, window_cache=window_cache, gate_sha256=gate['report_sha256'],
        runtime_sha256=file_sha(runtime_report), graph_condition=graph_condition, graph_cache=graph_cache)
    if (grant.get('status') != 'USER_APPROVED' or grant.get('binding') != binding
            or not isinstance(grant.get('approval_reference'), str) or not grant['approval_reference'].strip()):
        raise PermissionError('Exact authorized refit grant required')
    if (resume is None) != (expected_resume_sha256 is None):
        raise ValueError('Resume file and SHA must be supplied together')
    if resume is not None and file_sha(resume) != expected_resume_sha256:
        raise ValueError('Refit resume checkpoint changed')
    from .research_graph_model import _cuda_execution_check
    _cuda_execution_check(profile, synchronize=True)
    import torch
    _seed(config.seed)
    with torch.device('cpu'):
        adapter = _make_selected_adapter(config, profile, encoding, inputs.view, graph_condition, context_cache=graph_cache)
    optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr, betas=config.betas,
        eps=config.eps, weight_decay=config.weight_decay, foreach=False, fused=False)
    from types import SimpleNamespace
    from .research_runner import _state_hash
    initial = _state_hash(adapter if graph_condition is None else SimpleNamespace(native=adapter.native.backbone))
    # Runtime receipt được kiểm riêng từng lần gọi, còn identity resume giữ recipe ổn định.
    identity = dict({key: value for key, value in binding.items() if key != 'runtime_sha256'},
        profile=asdict(profile), confidence_policy=plan['confidence_policy'], initial_backbone_sha256=initial)
    if graph_condition is not None:
        identity['batch_factory'] = adapter.audit_context_boundary()
    budget = dict(max_steps=config.max_steps, max_targets=inputs.targets, max_seconds=config.max_seconds,
        max_rss_bytes=config.max_rss_bytes, min_available_ram_bytes=config.min_available_ram_bytes,
        run_id=config.run_id, phase=config.phase, resource_sample_limit=128, progress_resource_samples=False)
    return _run_epochs(adapter, window_cache.iter_windows, optimizer=optimizer, output=config.output_dir,
        identity=identity, epochs=epochs, targets=inputs.targets, max_seconds=config.max_wall_seconds,
        budget=budget, resume=resume, checkpoint_callback=checkpoint_callback,
        launch_evidence=dict(runtime_sha256=binding['runtime_sha256'], grant_sha256=_identity(grant)),
        total_max_steps=config.max_steps, total_max_targets=config.max_total_targets)
