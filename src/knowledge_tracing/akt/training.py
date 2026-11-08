"""Training protocol AKT trên learner Development đã tách."""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from pathlib import Path
import random
import time
import uuid
from collections.abc import Callable, Iterator

import numpy as np
import torch

from .checkpoint import (load_checkpoint, restore_checkpoint, save_checkpoint,
                         load_recovery_checkpoint, restore_recovery_checkpoint, save_recovery_checkpoint,
                         load_training_snapshot)
from .config import AKTConfig
from .encoding import ExerciseEncoding, fit_vocabulary
from .model import AKTAdapter
from .resources import memory_snapshot
from .recovery import training_config_hash, training_budget, preserve_checkpoint
from .sampler import ReplayableWindowCursor
from .splits import InnerSplit
from .tensors import AKTBatch, collate_windows
from .types import LearnerEvents, TrainingWindow, UnseenTarget
from .windows import iter_windows


@dataclass(frozen=True)
class EpochStats:
    loss_sum: float
    valid_targets: int
    optimizer_steps: int
    complete: bool
    resource: dict
    nonzero_gradient_steps: int = 0
    parameter_update_steps: int = 0
    max_pre_clip_grad_norm: float = 0.0
    max_post_clip_grad_norm: float = 0.0
    windows_processed: int = 0
    processed_target_rows: int = 0
    optimized_target_rows: int = 0
    batches: int = 0
    collated_windows: int = 0
    sequence_length_counts: dict[int, int] = field(default_factory=dict)
    batch_shape_counts: dict[str, int] = field(default_factory=dict)
    valid_tokens: int = 0
    target_tokens: int = 0
    context_tokens: int = 0
    padding_tokens: int = 0
    forward_seconds: float = 0.0
    backward_seconds: float = 0.0
    gradient_clip_seconds: float = 0.0
    optimizer_seconds: float = 0.0
    clipped_steps: int = 0
    stop_reason: str = 'epoch_complete'


def _rss_bytes() -> int:
    """Return the process peak working set when the OS exposes it."""
    snapshot = memory_snapshot()
    peak = snapshot['process_peak_rss_bytes']
    return max(snapshot['process_rss_bytes'], peak or 0)


def _check_resource_budget(budget: dict, *, samples: list[dict] | None = None,
                           observer: Callable[[dict], None] | None = None) -> int:
    snapshot = memory_snapshot()
    if samples is not None:
        samples.append(snapshot)
    if observer is not None:
        observer(snapshot)
    rss = max(snapshot['process_rss_bytes'], snapshot['process_peak_rss_bytes'] or 0)
    cap = budget.get('max_rss_bytes')
    minimum = budget.get('min_available_ram_bytes')
    phase = budget.get('phase', 'akt')
    run_id = budget.get('run_id', 'unbound')
    detail = (f"phase={phase}, run_id={run_id}, pid={snapshot['pid']}, "
              f"worker_rss_bytes={snapshot['process_rss_bytes']}, "
              f"worker_peak_rss_bytes={snapshot['process_peak_rss_bytes']}, "
              f"worker_cap_value_bytes={rss}, "
              f"system_available_ram_bytes={snapshot['system_available_ram_bytes']}, "
              f"system_total_ram_bytes={snapshot['system_total_ram_bytes']}, "
              f"max_rss_bytes={cap}, min_available_ram_bytes={minimum}")
    if cap is not None and rss > cap:
        raise MemoryError(f'AKT worker RSS ceiling exceeded: {detail}')
    if minimum is not None and snapshot['system_available_ram_bytes'] < minimum:
        raise MemoryError(f'AKT system available-RAM floor violated: {detail}')
    return rss


def _shuffle_windows(factory: Callable[[], Iterator[TrainingWindow]], *, seed: int,
                     buffer_size: int = 1024) -> Iterator[TrainingWindow]:
    rng = random.Random(seed)
    source = iter(factory())
    buffer = []
    for window in source:
        if not isinstance(window, TrainingWindow):
            raise ValueError('training contains an unseen target')
        if len(buffer) < buffer_size:
            buffer.append(window)
            continue
        index = rng.randrange(len(buffer))
        yield buffer[index]
        buffer[index] = window
    rng.shuffle(buffer)
    yield from buffer


def train_epoch(adapter: AKTAdapter, windows_factory: Callable[[], Iterator[TrainingWindow]], *,
                optimizer: torch.optim.Optimizer, epoch: int, budget: dict,
                progress_callback: Callable[[dict], None] | None = None,
                resource_callback: Callable[[dict], None] | None = None,
                recovery: dict | None = None,
                batch_factory: Callable[[tuple[TrainingWindow, ...]], AKTBatch] | None = None) -> EpochStats:
    if epoch < 1:
        raise ValueError('invalid epoch')
    if batch_factory is not None:
        if not callable(batch_factory):
            raise ValueError('batch_factory must be callable')
        if recovery is not None:
            raise ValueError('custom batch factory has no recovery contract')
    adapter.native.train()
    started = time.perf_counter()
    loss_sum, valid_targets, steps, complete = 0.0, 0, 0, True
    nonzero_gradient_steps, parameter_update_steps = 0, 0
    windows_processed, processed_target_rows = 0, 0
    max_pre_clip_grad_norm, max_post_clip_grad_norm = 0.0, 0.0
    max_rss = 0
    batches = collated_windows = valid_tokens = target_tokens = context_tokens = padding_tokens = 0
    clipped_steps = 0
    forward_seconds = backward_seconds = gradient_clip_seconds = optimizer_seconds = 0.0
    stop_reason = 'training_in_progress'
    sequence_length_counts: dict[int, int] = {}
    batch_shape_counts: dict[str, int] = {}
    resource_samples: list[dict] = []
    pending: list[TrainingWindow] = []

    cursor = None
    saved_steps = 0
    last_checkpoint = None
    committed_state = None
    if recovery is not None:
        payload = None
        sampler_state = None
        if recovery.get('resume_checkpoint') is not None:
            payload = load_recovery_checkpoint(recovery['resume_checkpoint'],
                expected_identity=recovery['identity'], device=adapter.config.device)
            state = payload['resume_state']
            if state['epoch'] != epoch:
                raise ValueError('recovery epoch mismatch')
            trainer = state['trainer_state']
            if trainer.get('role') != 'epoch_accounting_v1':
                raise ValueError('invalid epoch accounting schema')
            saved = EpochStats(**trainer['stats'])
            if (saved.optimizer_steps != state['optimizer_steps'] or saved.valid_targets < 1
                    or saved.collated_windows != state['sampler_state']['consumed_windows']
                    or not math.isfinite(saved.loss_sum) or saved.loss_sum < 0
                    or not math.isfinite(saved.resource['wall_seconds']) or saved.resource['wall_seconds'] < 0):
                raise ValueError('invalid epoch recovery accounting')
            loss_sum, valid_targets, steps = saved.loss_sum, saved.valid_targets, saved.optimizer_steps
            nonzero_gradient_steps, parameter_update_steps = saved.nonzero_gradient_steps, saved.parameter_update_steps
            windows_processed, processed_target_rows = saved.windows_processed, saved.processed_target_rows
            max_pre_clip_grad_norm, max_post_clip_grad_norm = saved.max_pre_clip_grad_norm, saved.max_post_clip_grad_norm
            max_rss = saved.resource['peak_rss_bytes']
            resource_samples = list(saved.resource['samples'])
            batches, collated_windows = saved.batches, saved.collated_windows
            valid_tokens, target_tokens = saved.valid_tokens, saved.target_tokens
            context_tokens, padding_tokens = saved.context_tokens, saved.padding_tokens
            clipped_steps = saved.clipped_steps
            forward_seconds, backward_seconds = saved.forward_seconds, saved.backward_seconds
            gradient_clip_seconds, optimizer_seconds = saved.gradient_clip_seconds, saved.optimizer_seconds
            sequence_length_counts, batch_shape_counts = dict(saved.sequence_length_counts), dict(saved.batch_shape_counts)
            started -= saved.resource['wall_seconds']
            sampler_state = state['sampler_state']
        cursor = ReplayableWindowCursor(windows_factory, seed=adapter.config.seed + epoch,
                    stream_identity=hashlib.sha256(json.dumps(recovery['identity'], sort_keys=True).encode()).hexdigest(),
                    state=sampler_state)
        if payload is not None:
            # Replay trước restore để factory không tiêu thụ RNG của model vừa phục hồi.
            restore_recovery_checkpoint(adapter, optimizer, payload)
            saved_steps = steps
            last_checkpoint = recovery['resume_checkpoint']
            del payload

    def snapshot_stats(is_complete=False):
        return EpochStats(loss_sum, valid_targets, steps, is_complete,
            {'wall_seconds': time.perf_counter()-started, 'peak_rss_bytes': max_rss,
             'samples': list(resource_samples)}, nonzero_gradient_steps, parameter_update_steps,
            max_pre_clip_grad_norm, max_post_clip_grad_norm, windows_processed,
            processed_target_rows, valid_targets, batches=batches, collated_windows=collated_windows,
            sequence_length_counts=dict(sequence_length_counts), batch_shape_counts=dict(batch_shape_counts),
            valid_tokens=valid_tokens, target_tokens=target_tokens, context_tokens=context_tokens,
            padding_tokens=padding_tokens, forward_seconds=forward_seconds, backward_seconds=backward_seconds,
            gradient_clip_seconds=gradient_clip_seconds, optimizer_seconds=optimizer_seconds,
            clipped_steps=clipped_steps, stop_reason=stop_reason)

    def save_batch():
        nonlocal saved_steps, last_checkpoint
        if recovery is None or steps == saved_steps:
            return
        prefix = recovery.get('prefix', 'inner')
        path = recovery['checkpoint_dir'] / f'{prefix}-batch-epoch-{epoch}-step-{steps}-{uuid.uuid4().hex}.pt'
        save_recovery_checkpoint(path, adapter, optimizer, identity=recovery['identity'], resume_state=committed_state)
        saved_steps, last_checkpoint = steps, path
        if recovery.get('checkpoint_callback') is not None:
            recovery['checkpoint_callback'](path)

    def progress(*, complete_epoch: bool) -> None:
        if progress_callback is None:
            return
        progress_callback({
            'epoch': epoch,
            'complete_epoch': complete_epoch,
            'stop_reason': stop_reason,
            'training': {
                'loss_sum': loss_sum,
                'valid_targets': valid_targets,
                'optimizer_steps': steps,
                'batches': batches,
                'windows_processed': windows_processed,
                'collated_windows': collated_windows,
                'processed_target_rows': processed_target_rows,
                'optimized_target_rows': valid_targets,
                'sequence_length_counts': dict(sequence_length_counts),
                'batch_shape_counts': dict(batch_shape_counts),
                'valid_tokens': valid_tokens,
                'target_tokens': target_tokens,
                'context_tokens': context_tokens,
                'padding_tokens': padding_tokens,
                'nonzero_gradient_steps': nonzero_gradient_steps,
                'parameter_update_steps': parameter_update_steps,
                'clipped_steps': clipped_steps,
                'max_pre_clip_grad_norm': max_pre_clip_grad_norm,
                'max_post_clip_grad_norm': max_post_clip_grad_norm,
                'forward_seconds': forward_seconds,
                'backward_seconds': backward_seconds,
                'gradient_clip_seconds': gradient_clip_seconds,
                'optimizer_seconds': optimizer_seconds,
                'resource': {'wall_seconds': time.perf_counter() - started,
                             'peak_rss_bytes': max_rss,
                             'samples': list(resource_samples)},
            },
        })

    def flush() -> bool:
        nonlocal loss_sum, valid_targets, steps, max_rss, nonzero_gradient_steps
        nonlocal parameter_update_steps, max_pre_clip_grad_norm, max_post_clip_grad_norm
        nonlocal batches, collated_windows, valid_tokens, target_tokens, context_tokens, padding_tokens
        nonlocal clipped_steps, forward_seconds, backward_seconds, gradient_clip_seconds, optimizer_seconds
        nonlocal stop_reason
        nonlocal committed_state
        if not pending:
            return True
        rss = _check_resource_budget(budget, samples=resource_samples, observer=resource_callback)
        max_rss = max(max_rss, rss)
        batch_targets = sum(int(np_window.window.target_mask.sum()) for np_window in pending)
        if budget.get('max_steps') is not None and steps >= budget['max_steps']:
            stop_reason = 'step_budget'
            return False
        if budget.get('max_seconds') is not None and time.perf_counter() - started >= budget['max_seconds']:
            stop_reason = 'time_budget'
            return False
        if budget.get('max_targets') is not None and valid_targets + batch_targets > budget['max_targets']:
            stop_reason = 'target_budget'
            return False
        if batch_factory is None:
            batch = collate_windows([entry.window for entry in pending],
                                    n_items=len(adapter.encoding.vocabulary.values),
                                    device=adapter.config.device, targets=[entry.targets for entry in pending])
        else:
            # Preserve learner/window/global identities until the owned adapter seals the batch.
            batch = batch_factory(tuple(pending))
            if type(batch) is not AKTBatch or batch.q_data.shape[0] != len(pending):
                raise ValueError('custom factory must return an AKTBatch for every pending window')
        batches += 1
        collated_windows += len(pending)
        batch_shape = f'{batch.q_data.shape[0]}x{batch.q_data.shape[1]}'
        batch_shape_counts[batch_shape] = batch_shape_counts.get(batch_shape, 0) + 1
        batch_valid_tokens = int(batch.valid_mask.sum().item())
        batch_target_tokens = int((batch.target_mask & batch.valid_mask).sum().item())
        valid_tokens += batch_valid_tokens
        target_tokens += batch_target_tokens
        context_tokens += batch_valid_tokens - batch_target_tokens
        padding_tokens += int(batch.valid_mask.numel()) - batch_valid_tokens
        result = adapter.step(batch, optimizer)
        if result['stepped']:
            loss_sum += result['loss_sum']
            valid_targets += result['valid_targets']
            steps += 1
            pre_clip = float(result.get('pre_clip_norm', 0.0))
            post_clip = float(result.get('post_clip_norm', 0.0))
            if not math.isfinite(pre_clip) or not math.isfinite(post_clip):
                raise ValueError('nonfinite gradient norm')
            nonzero_gradient_steps += int(pre_clip > 0)
            parameter_update_steps += int(result.get('parameter_updated', False))
            clipped_steps += int(pre_clip > adapter.config.max_grad_norm)
            max_pre_clip_grad_norm = max(max_pre_clip_grad_norm, pre_clip)
            max_post_clip_grad_norm = max(max_post_clip_grad_norm, post_clip)
            forward_seconds += float(result.get('forward_seconds', 0.0))
            backward_seconds += float(result.get('backward_seconds', 0.0))
            gradient_clip_seconds += float(result.get('gradient_clip_seconds', 0.0))
            optimizer_seconds += float(result.get('optimizer_seconds', 0.0))
        pending.clear()
        if recovery is not None:
            committed_state = {'schema_version': 1, 'epoch': epoch, 'optimizer_steps': steps,
                'sampler_state': cursor.state_dict(),
                'trainer_state': {'role': 'epoch_accounting_v1', 'stats': asdict(snapshot_stats()),
                                  'selection_state': recovery.get('selection_state')}}
        if recovery is not None and steps % adapter.config.recovery.checkpoint_every_steps == 0:
            save_batch()
        # Record a completed optimizer step before checking its post-update memory use.
        # If the cap is crossed here, the bounded run still persists the work just done.
        try:
            rss = _check_resource_budget(budget, samples=resource_samples, observer=resource_callback)
            max_rss = max(max_rss, rss)
        except MemoryError:
            stop_reason = 'resource_budget'
            progress(complete_epoch=False)
            raise
        progress(complete_epoch=False)
        return True

    for entry in (cursor if cursor is not None else _shuffle_windows(windows_factory, seed=adapter.config.seed + epoch)):
        windows_processed += 1
        processed_target_rows += int(entry.window.target_mask.sum())
        length = len(entry.window.inputs.item_ids)
        sequence_length_counts[length] = sequence_length_counts.get(length, 0) + 1
        pending.append(entry)
        # Flush trước lần lấy window kế tiếp: snapshot luôn ở committed batch boundary.
        if len(pending) >= adapter.config.batch_size and not flush():
            complete = False
            break
    if complete and not flush():
        complete = False
    if complete and not valid_targets:
        raise ValueError('empty training epoch')
    if complete:
        stop_reason = 'epoch_complete'
    elif stop_reason == 'training_in_progress':
        stop_reason = 'bounded_budget'
    save_batch()
    if (recovery is not None and last_checkpoint is not None
            and Path(last_checkpoint).parent.resolve() != recovery['checkpoint_dir'].resolve()):
        local = preserve_checkpoint(Path(last_checkpoint), recovery['checkpoint_dir'] / Path(last_checkpoint).name)
        if recovery.get('checkpoint_callback') is not None:
            recovery['checkpoint_callback'](local)
    stats = snapshot_stats(complete)
    if progress_callback is not None:
        progress(complete_epoch=complete)
    return stats


@dataclass
class EarlyStopping:
    patience: int
    min_delta: float
    best_epoch: int | None = None
    best_loss: float = math.inf
    stale_epochs: int = 0
    last_epoch: int = 0

    def observe(self, epoch: int, loss: float) -> bool:
        if epoch <= self.last_epoch or not math.isfinite(loss) or self.patience <= 0 or self.min_delta < 0:
            raise ValueError('invalid early stopping input')
        self.last_epoch = epoch
        if loss < self.best_loss - self.min_delta:
            self.best_epoch, self.best_loss, self.stale_epochs = epoch, loss, 0
        else:
            self.stale_epochs += 1
        return self.stale_epochs >= self.patience


@dataclass(frozen=True)
class SelectionResult:
    selected_epoch: int | None
    split_hash: str
    checkpoint: Path | None
    history: list[dict]
    status: str = 'completed'
    stop_reason: str | None = None
    complete_epoch: bool = True


def _seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _encoding_hash(encoding: ExerciseEncoding) -> str:
    raw = json.dumps({'values': encoding.vocabulary.values,
                      'support': encoding.train_support_students},
                     sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _bounded_epoch_budget(budget: dict | None) -> dict:
    if not isinstance(budget, dict) or not budget:
        raise ValueError('an explicit training budget is required')
    for key in ('max_steps', 'max_targets', 'max_seconds'):
        value = budget.get(key)
        if value is not None and (not math.isfinite(float(value)) or value <= 0):
            raise ValueError('invalid training budget')
    if not any(budget.get(key) is not None for key in ('max_steps', 'max_targets', 'max_seconds')):
        raise ValueError('training budget must cap steps, targets, or time')
    return dict(budget)


def _prepare_output(config: AKTConfig) -> Path:
    output = config.output_dir.resolve()
    root = config.project_root.resolve()
    protected = (root / 'dataset', root / 'artifacts/bkt_baseline', root / 'venv', root / '.wsl')
    if any(output.is_relative_to(path.resolve()) for path in protected):
        raise ValueError('protected training output')
    output.mkdir(parents=True, exist_ok=True)
    return output


def _scoped(factory: Callable[[], Iterator[LearnerEvents]], allowed_users: tuple[str, ...],
            outer_fold: int) -> Iterator[LearnerEvents]:
    if outer_fold not in range(5):
        raise ValueError('invalid outer fold')
    allowed = set(allowed_users)
    if not allowed or len(allowed) != len(allowed_users):
        raise ValueError('invalid learner scope')
    seen = set()
    for learner in factory():
        if (learner.user_id not in allowed or learner.user_id in seen
                or learner.fold not in range(5) or learner.fold == outer_fold
                or any(event.fold != learner.fold for event in learner.events)):
            raise ValueError('learner scope violation: invalid fold')
        seen.add(learner.user_id)
        yield learner
    if seen != allowed:
        raise ValueError('learner scope is incomplete')


def _training_windows(factory: Callable[[], Iterator[LearnerEvents]], allowed_users: tuple[str, ...],
                      outer_fold: int, encoding: ExerciseEncoding, config: AKTConfig) -> Iterator[TrainingWindow]:
    for learner in _scoped(factory, allowed_users, outer_fold):
        for entry in iter_windows(learner, encoding, context=config.context,
                                  target_block=config.target_block, training=True):
            if not isinstance(entry, TrainingWindow):
                raise ValueError('training scope contains an unseen exercise')
            yield entry


def evaluate_inner(adapter: AKTAdapter, factory: Callable[[], Iterator[LearnerEvents]],
                   allowed_users: tuple[str, ...], *, budget: dict | None = None,
                   resource_callback: Callable[[dict], None] | None = None) -> tuple[float, dict]:
    started = time.perf_counter()
    loss_sum, count, unseen = 0.0, 0, 0
    windows = valid_tokens = target_tokens = 0
    sequence_lengths: dict[int, int] = {}
    batch_shapes: dict[str, int] = {}
    prior_mode = adapter.native.training
    adapter.native.eval()
    try:
        with torch.no_grad():
            for learner in _scoped(factory, allowed_users, adapter.config.outer_fold):
                for entry in iter_windows(learner, adapter.encoding, context=adapter.config.context,
                                          target_block=adapter.config.target_block, training=True):
                    if isinstance(entry, UnseenTarget):
                        unseen += 1
                        continue
                    windows += 1
                    length = len(entry.window.inputs.item_ids)
                    sequence_lengths[length] = sequence_lengths.get(length, 0) + 1
                    batch = collate_windows([entry.window], n_items=len(adapter.encoding.vocabulary.values),
                                            device=adapter.config.device, targets=[entry.targets])
                    if budget is not None:
                        _check_resource_budget(budget, observer=resource_callback)
                    shape = f'{batch.q_data.shape[0]}x{batch.q_data.shape[1]}'
                    batch_shapes[shape] = batch_shapes.get(shape, 0) + 1
                    valid_tokens += int(batch.valid_mask.sum().item())
                    target_tokens += int((batch.target_mask & batch.valid_mask).sum().item())
                    loss, predictions, n = adapter.native(batch.q_data, batch.qa_data, batch.loss_targets)
                    if budget is not None:
                        _check_resource_budget(budget, observer=resource_callback)
                    if not torch.isfinite(loss) or not torch.isfinite(predictions).all():
                        raise ValueError('nonfinite inner validation')
                    loss_sum += float(loss.item())
                    count += int(n.item())
    finally:
        adapter.native.train(prior_mode)
    if count == 0:
        raise ValueError('inner validation has no known predictions')
    return loss_sum / count, {
        'predicted_rows': count, 'unseen_rows': unseen, 'expected_rows': count + unseen,
        'windows': windows, 'sequence_length_counts': sequence_lengths,
        'batch_shape_counts': batch_shapes, 'valid_tokens': valid_tokens,
        'target_tokens': target_tokens, 'context_tokens': valid_tokens - target_tokens,
        'padding_tokens': 0, 'elapsed_seconds': time.perf_counter() - started,
    }


def _epoch_stats_payload(stats: EpochStats) -> dict:
    payload = asdict(stats)
    payload['mean_loss'] = stats.loss_sum / stats.valid_targets if stats.valid_targets else None
    payload['complete_epoch'] = stats.complete
    return payload


def select_checkpoint(config: AKTConfig, *, inner_split: InnerSplit,
                      train_learners_factory: Callable[[], Iterator[LearnerEvents]],
                      val_learners_factory: Callable[[], Iterator[LearnerEvents]],
                      identity: dict, budget: dict | None = None,
                      progress_callback: Callable[[dict], None] | None = None,
                      resource_callback: Callable[[dict], None] | None = None,
                      save_recovery: bool = False,
                      resume_checkpoint: Path | None = None,
                      checkpoint_callback: Callable[[Path, Path | None], None] | None = None) -> SelectionResult:
    epoch_budget = _bounded_epoch_budget(budget)
    output_dir = _prepare_output(config)
    if (inner_split.outer_fold != config.outer_fold
            or set(inner_split.inner_train_users) & set(inner_split.inner_val_users)):
        raise ValueError('invalid inner split scope')
    _seed(config.seed)
    encoding = fit_vocabulary(_scoped(train_learners_factory, inner_split.inner_train_users, config.outer_fold))
    adapter = AKTAdapter(config, encoding)
    optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr, betas=config.betas,
                                 eps=config.eps, weight_decay=config.weight_decay)
    stopper = EarlyStopping(config.patience, config.min_delta)
    history: list[dict] = []
    chosen: Path | None = None
    run_identity = {**identity, 'split_hash': inner_split.split_hash, 'encoding_hash': _encoding_hash(encoding)}
    config_hash = training_config_hash(config)
    recovery_identity = {**run_identity, 'selection_recovery': {
        'config_sha256': config_hash, 'budget': training_budget(config, epoch_budget)}}
    first_epoch = 1
    batch_resume = None
    if resume_checkpoint is not None:
        if not save_recovery:
            raise ValueError('selection resume requires recovery snapshots')
        payload = load_training_snapshot(Path(resume_checkpoint), expected_identity=recovery_identity,
                                          device='cpu')
        partial = payload.get('checkpoint_kind') == 'training_recovery_v1'
        if partial:
            if config.recovery is None:
                raise ValueError('batch resume requires recovery configuration')
            progress = payload['resume_state']['trainer_state'].get('selection_state', {})
            batch_resume = Path(resume_checkpoint)
        else:
            progress = payload['progress']
        saved_history = progress.get('history')
        if (progress.get('role') != ('selection_batch_v1' if partial else 'selection_recovery_v1')
                or type(progress.get('epoch')) is not int
                or not 1 <= progress['epoch'] <= config.max_epochs
                or not isinstance(saved_history, list)
                or len(saved_history) != progress['epoch'] - int(partial)
                or (partial and payload['resume_state']['epoch'] != progress['epoch'])):
            raise ValueError('invalid selection recovery history')
        for expected_epoch, entry in enumerate(saved_history, start=1):
            if (entry.get('epoch') != expected_epoch or entry.get('complete_epoch') is not True
                    or stopper.stale_epochs >= stopper.patience):
                raise ValueError('invalid selection recovery epoch order')
            stopper.observe(expected_epoch, entry['validation_loss'])
        if stopper.best_epoch != progress.get('selected_epoch'):
            raise ValueError('selection recovery best epoch mismatch')
        best_name = progress.get('best_checkpoint')
        if stopper.best_epoch is not None:
            if not isinstance(best_name, str) or Path(best_name).name != best_name:
                raise ValueError('invalid selection recovery checkpoint path')
            chosen = Path(resume_checkpoint).parent / best_name
            if hashlib.sha256(chosen.read_bytes()).hexdigest() != progress.get('best_checkpoint_sha256'):
                raise ValueError('selection recovery best checkpoint mismatch')
            best = load_checkpoint(chosen, expected_identity=run_identity, device=config.device)
            if best['progress'].get('epoch') != stopper.best_epoch:
                raise ValueError('selection recovery best checkpoint epoch mismatch')
            del best
            if config.recovery is not None:
                chosen = preserve_checkpoint(chosen, output_dir / chosen.name)
        elif not partial or best_name is not None or progress.get('best_checkpoint_sha256') is not None:
            raise ValueError('invalid selection recovery empty best checkpoint')
        if not partial:
            restore_checkpoint(adapter, optimizer, payload)
        history = saved_history
        first_epoch = progress['epoch'] + int(not partial)
        del payload
    for epoch in range(first_epoch, config.max_epochs + 1):
        if stopper.stale_epochs >= stopper.patience:
            break
        factory = lambda: _training_windows(train_learners_factory, inner_split.inner_train_users,
                                            config.outer_fold, encoding, config)
        train_kwargs = {'optimizer': optimizer, 'epoch': epoch, 'budget': epoch_budget}
        if progress_callback is not None:
            train_kwargs['progress_callback'] = lambda payload: progress_callback({
                'epoch': epoch, **payload})
        if resource_callback is not None:
            train_kwargs['resource_callback'] = resource_callback
        if config.recovery is not None:
            if not save_recovery:
                raise ValueError('configured recovery requires snapshots')
            selection_state = {'role': 'selection_batch_v1', 'epoch': epoch,
                'history': list(history), 'selected_epoch': stopper.best_epoch,
                'best_checkpoint': chosen.name if chosen else None,
                'best_checkpoint_sha256': hashlib.sha256(chosen.read_bytes()).hexdigest() if chosen else None}
            train_kwargs['recovery'] = {'checkpoint_dir': output_dir, 'identity': recovery_identity,
                'selection_state': selection_state, 'resume_checkpoint': batch_resume,
                'checkpoint_callback': (lambda path: checkpoint_callback(path, chosen)) if checkpoint_callback else None}
        stats = train_epoch(adapter, factory, **train_kwargs)
        batch_resume = None
        if not stats.complete:
            history.append({'epoch': epoch, 'complete_epoch': False,
                            'stop_reason': stats.stop_reason,
                            'training': _epoch_stats_payload(stats),
                            'validation': None, 'checkpoint': None})
            return SelectionResult(stopper.best_epoch, inner_split.split_hash, chosen, history,
                                   status='bounded', stop_reason=stats.stop_reason,
                                   complete_epoch=False)
        evaluation_kwargs = ({'budget': epoch_budget, 'resource_callback': resource_callback}
                             if resource_callback is not None else {})
        loss, coverage = evaluate_inner(adapter, val_learners_factory, inner_split.inner_val_users,
                                        **evaluation_kwargs)
        old_best = stopper.best_epoch
        stop = stopper.observe(epoch, loss)
        training = _epoch_stats_payload(stats)
        training['sampler_seed'] = config.seed + epoch
        history.append({'epoch': epoch, 'complete_epoch': True, 'validation_loss': loss,
                        'validation': coverage, 'coverage': coverage, 'training': training})
        if stopper.best_epoch != old_best:
            suffix = f'-{uuid.uuid4().hex}' if save_recovery else ''
            chosen = output_dir / f'inner-best-epoch-{epoch}{suffix}.pt'
            if resource_callback is not None:
                _check_resource_budget(epoch_budget, observer=resource_callback)
            checkpoint_started = time.perf_counter()
            save_checkpoint(chosen, adapter, optimizer, identity=run_identity,
                            progress={'epoch': epoch, 'sampler_seed': config.seed + epoch,
                                      'complete': True, 'history': list(history)})
            history[-1]['checkpoint_save_seconds'] = time.perf_counter() - checkpoint_started
            if resource_callback is not None:
                _check_resource_budget(epoch_budget, observer=resource_callback)
        if save_recovery:
            recovery_path = output_dir / f'inner-recovery-epoch-{epoch}.pt'
            save_checkpoint(recovery_path, adapter, optimizer,
                            identity=recovery_identity,
                            progress={'role': 'selection_recovery_v1', 'epoch': epoch,
                                      'complete': True, 'history': list(history),
                                      'selected_epoch': stopper.best_epoch,
                                      'best_checkpoint': chosen.name,
                                      'best_checkpoint_sha256': hashlib.sha256(chosen.read_bytes()).hexdigest()})
            if checkpoint_callback is not None:
                checkpoint_callback(recovery_path, chosen)
        if stop:
            break
    if chosen is None or stopper.best_epoch is None:
        raise ValueError('no valid selection checkpoint')
    if resume_checkpoint is not None and first_epoch > len(history) and checkpoint_callback is not None:
        # Selection đã hoàn tất trước interruption tại export: vẫn có snapshot ở attempt mới.
        snapshot = preserve_checkpoint(Path(resume_checkpoint), output_dir / Path(resume_checkpoint).name)
        checkpoint_callback(snapshot, chosen)
    return SelectionResult(stopper.best_epoch, inner_split.split_hash, chosen, history)


def refit_outer_train(config: AKTConfig, *, outer_train_users: tuple[str, ...],
                      train_learners_factory: Callable[[], Iterator[LearnerEvents]],
                      selected_epochs: int, identity: dict, budget: dict | None = None,
                      save_recovery: bool = False,
                      resume_checkpoint: Path | None = None,
                      checkpoint_callback: Callable[[Path, Path | None], None] | None = None) -> AKTAdapter:
    epoch_budget = _bounded_epoch_budget(budget)
    if not 1 <= selected_epochs <= config.max_epochs:
        raise ValueError('invalid refit epoch budget')
    _seed(config.seed)
    encoding = fit_vocabulary(_scoped(train_learners_factory, outer_train_users, config.outer_fold))
    adapter = AKTAdapter(config, encoding)
    adapter.run_identity = {**identity, 'encoding_hash': _encoding_hash(encoding)}
    optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr, betas=config.betas,
                                 eps=config.eps, weight_decay=config.weight_decay)
    history = []
    recovery_identity = {**adapter.run_identity, 'refit_recovery': {
        'config_sha256': training_config_hash(config),
        'outer_train_users': sorted(outer_train_users), 'selected_epochs': selected_epochs,
        'budget': training_budget(config, epoch_budget)}}
    first_epoch = 1
    batch_resume = None
    output = _prepare_output(config) if save_recovery else None
    if resume_checkpoint is not None:
        if not save_recovery:
            raise ValueError('refit resume requires recovery snapshots')
        payload = load_training_snapshot(Path(resume_checkpoint), expected_identity=recovery_identity, device='cpu')
        partial = payload.get('checkpoint_kind') == 'training_recovery_v1'
        if partial:
            if config.recovery is None:
                raise ValueError('batch resume requires recovery configuration')
            progress = payload['resume_state']['trainer_state'].get('selection_state', {})
            batch_resume = Path(resume_checkpoint)
        else:
            progress = payload['progress']
        history = progress.get('history')
        if (progress.get('role') != ('refit_batch_v1' if partial else 'refit_recovery_v1')
                or type(progress.get('epoch')) is not int
                or not 1 <= progress['epoch'] <= selected_epochs or not isinstance(history, list)
                or len(history) != progress['epoch'] - int(partial)
                or (partial and payload['resume_state']['epoch'] != progress['epoch'])
                or any(entry.get('epoch') != index or entry.get('valid_targets', 0) <= 0
                       or not math.isfinite(entry.get('loss_sum', math.nan))
                       for index, entry in enumerate(history, start=1))):
            raise ValueError('invalid refit recovery history')
        if not partial:
            restore_checkpoint(adapter, optimizer, payload)
        first_epoch = progress['epoch'] + int(not partial)
        del payload
    for epoch in range(first_epoch, selected_epochs + 1):
        factory = lambda: _training_windows(train_learners_factory, outer_train_users,
                                            config.outer_fold, encoding, config)
        recovery = None
        if config.recovery is not None:
            if not save_recovery:
                raise ValueError('configured recovery requires snapshots')
            recovery = {'prefix': 'refit', 'checkpoint_dir': output, 'identity': recovery_identity,
                'selection_state': {'role': 'refit_batch_v1', 'epoch': epoch, 'history': list(history)},
                'resume_checkpoint': batch_resume,
                'checkpoint_callback': (lambda path: checkpoint_callback(path, None)) if checkpoint_callback else None}
        stats = train_epoch(adapter, factory, optimizer=optimizer, epoch=epoch, budget=epoch_budget,
                            **({'recovery': recovery} if recovery is not None else {}))
        batch_resume = None
        if not stats.complete:
            raise RuntimeError('incomplete refit epoch')
        history.append({'epoch': epoch, 'loss_sum': stats.loss_sum, 'valid_targets': stats.valid_targets,
                        'mean_loss': stats.loss_sum / stats.valid_targets, 'sampler_seed': config.seed + epoch,
                        'optimizer_steps': stats.optimizer_steps, 'resource': stats.resource})
        if save_recovery:
            snapshot = output / f'refit-recovery-epoch-{epoch}.pt'
            save_checkpoint(snapshot, adapter, optimizer,
                            identity=recovery_identity,
                            progress={'role': 'refit_recovery_v1', 'epoch': epoch,
                                      'complete': True, 'history': list(history)})
            if checkpoint_callback is not None:
                checkpoint_callback(snapshot, None)
    if resume_checkpoint is not None and first_epoch > len(history) and checkpoint_callback is not None:
        snapshot = preserve_checkpoint(Path(resume_checkpoint), output / Path(resume_checkpoint).name)
        checkpoint_callback(snapshot, None)
    adapter.optimizer = optimizer
    adapter.training_history = history
    adapter.completed_epochs = selected_epochs
    return adapter


def fit_fixed_budget_outer_train(config: AKTConfig, *, outer_train_users: tuple[str, ...],
                                 train_learners_factory: Callable[[], Iterator[LearnerEvents]],
                                 epochs: int, identity: dict, budget: dict) -> AKTAdapter:
    """Explicit fixed-epoch fallback; does not inspect inner-validation scores."""
    if not 1 <= epochs <= config.max_epochs:
        raise ValueError('invalid fixed epoch budget')
    epoch_budget = _bounded_epoch_budget(budget)
    output_dir = _prepare_output(config)
    _seed(config.seed)
    encoding = fit_vocabulary(_scoped(train_learners_factory, outer_train_users, config.outer_fold))
    adapter = AKTAdapter(config, encoding)
    adapter.run_identity = {**identity, 'protocol': 'fixed-budget-explicit',
                            'encoding_hash': _encoding_hash(encoding)}
    optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr, betas=config.betas,
                                 eps=config.eps, weight_decay=config.weight_decay)
    history = []
    for epoch in range(1, epochs + 1):
        factory = lambda: _training_windows(train_learners_factory, outer_train_users,
                                            config.outer_fold, encoding, config)
        stats = train_epoch(adapter, factory, optimizer=optimizer, epoch=epoch, budget=epoch_budget)
        if not stats.complete:
            raise RuntimeError('incomplete fixed-budget epoch')
        history.append({'epoch': epoch, 'loss_sum': stats.loss_sum, 'valid_targets': stats.valid_targets,
                        'mean_loss': stats.loss_sum / stats.valid_targets, 'sampler_seed': config.seed + epoch,
                        'optimizer_steps': stats.optimizer_steps, 'resource': stats.resource})
        save_checkpoint(output_dir / f'fixed-budget-epoch-{epoch}.pt', adapter, optimizer,
                        identity=adapter.run_identity,
                        progress={'epoch': epoch, 'sampler_seed': config.seed + epoch,
                                  'complete': True, 'history': list(history)})
    adapter.optimizer = optimizer
    adapter.training_history = history
    adapter.completed_epochs = epochs
    return adapter
