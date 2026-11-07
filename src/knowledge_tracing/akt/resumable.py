"""Vòng train một epoch có checkpoint tại batch boundary, chưa nối CLI real-data."""

import math
from pathlib import Path
import time

from .checkpoint import load_recovery_checkpoint, restore_recovery_checkpoint, save_recovery_checkpoint
from .config import PROJECT_ROOT
from .sampler import ReplayableWindowCursor
from .tensors import collate_windows
from .training import _check_resource_budget


def train_resumable_epoch(adapter, optimizer, windows_factory, *, epoch: int,
                          stream_identity: str, identity: dict, checkpoint_dir: Path,
                          max_steps: int, max_seconds: float, resume_checkpoint=None,
                          resource_budget=None, checkpoint_callback=None,
                          max_targets: int | None = None,
                          checkpoint_every_steps: int = 1) -> dict:
    """Giữ nguyên native optimizer step, batch size và shuffle seed hiện tại.

    Caps là tổng trong epoch, kể cả prefix đã khôi phục. Checkpoint được ghi
    theo chu kỳ batch và khi dừng bình thường. Caller phải dùng stream identity bao gồm data,
    vocabulary và window configuration. Factory phải xác định và không dùng
    global RNG của model. Chưa chọn epoch/best checkpoint hoặc final refit.
    """
    if (type(epoch) is not int or epoch < 1 or type(max_steps) is not int or max_steps < 1
            or not math.isfinite(max_seconds) or max_seconds <= 0
            or type(checkpoint_every_steps) is not int or checkpoint_every_steps < 1
            or (max_targets is not None and (type(max_targets) is not int or max_targets < 1))):
        raise ValueError('invalid resumable epoch limits')
    checkpoint_dir = Path(checkpoint_dir).resolve()
    allowed = (PROJECT_ROOT / 'experiments/akt/results').resolve()
    if not checkpoint_dir.is_relative_to(allowed) or checkpoint_dir == allowed:
        raise ValueError('unsafe recovery output directory')
    steps = valid_targets = 0
    loss_sum = elapsed = 0.0
    sampler_state = None
    if resume_checkpoint is not None:
        payload = load_recovery_checkpoint(Path(resume_checkpoint), expected_identity=identity,
                                           device=adapter.config.device)
        state = payload['resume_state']
        if state['epoch'] != epoch:
            raise ValueError('recovery epoch mismatch')
        trainer = state['trainer_state']
        steps = state['optimizer_steps']
        valid_targets, loss_sum, elapsed = [trainer[name] for name in
                                            ('valid_targets', 'loss_sum', 'wall_seconds')]
        if (type(valid_targets) is not int or valid_targets < 1
                or not math.isfinite(loss_sum) or loss_sum < 0
                or not math.isfinite(elapsed) or elapsed < 0
                or trainer.get('batch_size') != adapter.config.batch_size):
            raise ValueError('invalid recovery trainer state')
        sampler_state = state['sampler_state']
        # Validate sampler before changing model/optimizer/RNG.
    started = time.perf_counter() - elapsed
    cursor = ReplayableWindowCursor(windows_factory, seed=adapter.config.seed + epoch,
                                    stream_identity=stream_identity, state=sampler_state)
    if resume_checkpoint is not None:
        restore_recovery_checkpoint(adapter, optimizer, payload)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    committed_sampler = cursor.state_dict()
    saved_steps = steps

    def save_progress():
        nonlocal saved_steps
        state = {'schema_version': 1, 'epoch': epoch, 'optimizer_steps': steps,
                 'sampler_state': committed_sampler,
                 'trainer_state': {'valid_targets': valid_targets, 'loss_sum': loss_sum,
                                   'wall_seconds': time.perf_counter()-started,
                                   'batch_size': adapter.config.batch_size}}
        path = checkpoint_dir / f'recovery-epoch-{epoch}-step-{steps}.pt'
        save_recovery_checkpoint(path, adapter, optimizer, identity=identity, resume_state=state)
        saved_steps = steps
        if checkpoint_callback is not None:
            checkpoint_callback(path, state)

    adapter.native.train()
    complete = False
    stop_reason = 'step_budget'
    while steps < max_steps:
        if time.perf_counter() - started >= max_seconds:
            stop_reason = 'time_budget'
            break
        _check_resource_budget(resource_budget or {})
        pending = []
        for _ in range(adapter.config.batch_size):
            try:
                pending.append(next(cursor))
            except StopIteration:
                break
        if not pending:
            complete = True
            stop_reason = 'epoch_complete'
            break
        batch_targets = sum(int(entry.window.target_mask.sum()) for entry in pending)
        if max_targets is not None and valid_targets + batch_targets > max_targets:
            stop_reason = 'target_budget'
            break
        batch = collate_windows([entry.window for entry in pending],
                                n_items=len(adapter.encoding.vocabulary.values),
                                device=adapter.config.device, targets=[entry.targets for entry in pending])
        result = adapter.step(batch, optimizer)
        if not result['stepped']:
            raise ValueError('recovery batch has no scored targets')
        steps += 1
        valid_targets += result['valid_targets']
        loss_sum += result['loss_sum']
        committed_sampler = cursor.state_dict()
        if steps % checkpoint_every_steps == 0:
            save_progress()
        _check_resource_budget(resource_budget or {})
    if steps == max_steps and stop_reason == 'step_budget':
        try:
            cursor.peek()
        except StopIteration:
            complete = True
            stop_reason = 'epoch_complete'
    if steps > saved_steps:
        save_progress()
    if complete and not valid_targets:
        raise ValueError('empty training epoch')
    return {'complete': complete, 'stop_reason': stop_reason, 'epoch': epoch,
            'optimizer_steps': steps, 'valid_targets': valid_targets, 'loss_sum': loss_sum,
            'sampler_state': committed_sampler, 'wall_seconds': time.perf_counter()-started}
