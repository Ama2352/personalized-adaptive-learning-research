"""Checkpoint atom và kiểm danh tính run AKT."""

import os
from pathlib import Path
import random
import uuid

import numpy as np
import torch

from .model import AKTAdapter
from .config import PROJECT_ROOT
from .filesystem import publish_new_file


def save_checkpoint(path: Path, adapter: AKTAdapter, optimizer: torch.optim.Optimizer, *,
                    identity: dict, progress: dict) -> None:
    if progress.get('complete') is not True:
        raise ValueError('only complete epoch checkpoints are supported')
    _save_payload(path, adapter, optimizer, identity=identity, progress=progress)


def _save_payload(path, adapter, optimizer, *, identity, progress, resume_state=None):
    output = path.resolve()
    protected = (PROJECT_ROOT / 'dataset', PROJECT_ROOT / 'artifacts/bkt_baseline',
                 PROJECT_ROOT / 'venv', PROJECT_ROOT / '.wsl')
    if any(output.is_relative_to(item.resolve()) for item in protected):
        raise ValueError('protected checkpoint path')
    if path.exists():
        raise FileExistsError(path)
    numpy_state = np.random.get_state()
    payload = {'model_state_dict': adapter.native.state_dict(), 'optimizer_state_dict': optimizer.state_dict(),
               'identity': identity, 'progress': progress,
               'encoding': {'values': list(adapter.encoding.vocabulary.values),
                            'train_support_students': adapter.encoding.train_support_students},
               'python_rng': random.getstate(),
               'numpy_rng': (numpy_state[0], numpy_state[1].tolist(), *numpy_state[2:]),
               'torch_rng': torch.get_rng_state(),
               'cuda_rng': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}
    if resume_state is not None:
        payload['checkpoint_kind'] = 'training_recovery_v1'
        payload['resume_state'] = resume_state
    # Không nhân đôi basename dài: nested run paths trên Windows có thể vượt MAX_PATH.
    temp = path.with_name('.akt-' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('xb') as stream:
            torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        publish_new_file(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def load_checkpoint(path: Path, *, expected_identity: dict, device: str) -> dict:
    payload = torch.load(path, map_location=device, weights_only=True)
    if payload.get('identity') != expected_identity:
        raise ValueError('checkpoint identity mismatch')
    if payload.get('progress', {}).get('complete') is not True:
        raise ValueError('checkpoint is incomplete')
    return payload


def load_training_snapshot(path: Path, *, expected_identity: dict, device: str) -> dict:
    """Đọc một lần để phân loại snapshot; không giữ thêm bản model/Adam trên GPU."""
    payload = torch.load(path, map_location=device, weights_only=True)
    if payload.get('identity') != expected_identity:
        raise ValueError('checkpoint identity mismatch')
    if payload.get('checkpoint_kind') == 'training_recovery_v1':
        if payload.get('progress', {}).get('complete') is not False:
            raise ValueError('invalid recovery checkpoint progress')
        _validate_resume_state(payload.get('resume_state'))
        if payload['progress'].get('epoch') != payload['resume_state']['epoch']:
            raise ValueError('recovery epoch mismatch')
    elif payload.get('progress', {}).get('complete') is not True:
        raise ValueError('checkpoint is incomplete')
    return payload


def restore_checkpoint(adapter: AKTAdapter, optimizer: torch.optim.Optimizer, payload: dict) -> None:
    """Restore a same-runtime complete checkpoint, including its random streams."""
    progress = payload.get('progress', {})
    if progress.get('complete') is not True or int(progress.get('epoch', 0)) < 1:
        raise ValueError('checkpoint is incomplete')
    _restore_payload(adapter, optimizer, payload)


def _restore_payload(adapter, optimizer, payload):
    saved_encoding = payload.get('encoding', {})
    if (saved_encoding.get('values') != list(adapter.encoding.vocabulary.values)
            or saved_encoding.get('train_support_students') != adapter.encoding.train_support_students):
        raise ValueError('checkpoint encoding mismatch')
    adapter.native.load_state_dict(payload['model_state_dict'])
    optimizer.load_state_dict(payload['optimizer_state_dict'])
    _restore_adam_step_devices(optimizer)
    random.setstate(_nested_tuple(payload['python_rng']))
    numpy_state = payload['numpy_rng']
    np.random.set_state((numpy_state[0], np.asarray(numpy_state[1], dtype=np.uint32),
                         *numpy_state[2:]))
    torch.set_rng_state(payload['torch_rng'].cpu())
    cuda_states = payload.get('cuda_rng', [])
    if torch.cuda.is_available() and cuda_states:
        # map_location=cuda cũng chuyển RNG byte tensors lên GPU; generator cần CPU state.
        torch.cuda.set_rng_state_all([state.cpu() for state in cuda_states])


def _restore_adam_step_devices(optimizer):
    """Giữ bộ đếm Adam trên CPU theo chính sách non-capturable của PyTorch.

    load_state_dict giữ nguyên thiết bị của step khi fused/capturable tắt.
    Vì vậy map_location=cuda cần được đảo lại riêng cho bộ đếm này.
    """
    if not isinstance(optimizer, (torch.optim.Adam, torch.optim.AdamW)):
        return
    for group in optimizer.param_groups:
        if group.get('capturable', False) or group.get('fused', False):
            continue
        for parameter in group['params']:
            state = optimizer.state.get(parameter, {})
            step = state.get('step')
            if isinstance(step, torch.Tensor):
                state['step'] = step.cpu()


def _validate_resume_state(state: dict) -> None:
    if not isinstance(state, dict) or state.get('schema_version') != 1:
        raise ValueError('invalid recovery schema')
    for key in ('epoch', 'optimizer_steps'):
        if type(state.get(key)) is not int or state[key] < 1:
            raise ValueError(f'invalid recovery {key}')
    for key in ('sampler_state', 'trainer_state'):
        if not isinstance(state.get(key), dict) or not state[key]:
            raise ValueError(f'missing recovery {key}')


def save_recovery_checkpoint(path: Path, adapter: AKTAdapter,
                             optimizer: torch.optim.Optimizer, *, identity: dict,
                             resume_state: dict) -> None:
    """Lưu tại ranh giới optimizer step, tách khỏi checkpoint chọn mô hình."""
    _validate_resume_state(resume_state)
    _save_payload(path, adapter, optimizer, identity=identity,
                  progress={'complete': False, 'epoch': resume_state['epoch']},
                  resume_state=resume_state)


def load_recovery_checkpoint(path: Path, *, expected_identity: dict, device: str) -> dict:
    payload = torch.load(path, map_location=device, weights_only=True)
    if payload.get('identity') != expected_identity:
        raise ValueError('checkpoint identity mismatch')
    if (payload.get('checkpoint_kind') != 'training_recovery_v1'
            or payload.get('progress', {}).get('complete') is not False):
        raise ValueError('not a training recovery checkpoint')
    _validate_resume_state(payload.get('resume_state'))
    if payload['progress'].get('epoch') != payload['resume_state']['epoch']:
        raise ValueError('recovery epoch mismatch')
    return payload


def restore_recovery_checkpoint(adapter: AKTAdapter, optimizer: torch.optim.Optimizer,
                                payload: dict) -> dict:
    """Phục hồi model/optimizer/RNG, trả state cho sampler và trainer kiểm tra."""
    if (payload.get('checkpoint_kind') != 'training_recovery_v1'
            or payload.get('progress', {}).get('complete') is not False):
        raise ValueError('not a training recovery checkpoint')
    state = payload.get('resume_state')
    _validate_resume_state(state)
    if payload['progress'].get('epoch') != state['epoch']:
        raise ValueError('recovery epoch mismatch')
    _restore_payload(adapter, optimizer, payload)
    return state


def _nested_tuple(value):
    if isinstance(value, (tuple, list)):
        return tuple(_nested_tuple(item) for item in value)
    return value
