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
    output = path.resolve()
    protected = (PROJECT_ROOT / 'dataset', PROJECT_ROOT / 'artifacts/bkt_baseline',
                 PROJECT_ROOT / 'venv', PROJECT_ROOT / '.wsl')
    if any(output.is_relative_to(item.resolve()) for item in protected):
        raise ValueError('protected checkpoint path')
    if progress.get('complete') is not True:
        raise ValueError('only complete epoch checkpoints are supported')
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
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
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


def restore_checkpoint(adapter: AKTAdapter, optimizer: torch.optim.Optimizer, payload: dict) -> None:
    """Restore a same-runtime complete checkpoint, including its random streams."""
    saved_encoding = payload.get('encoding', {})
    if (saved_encoding.get('values') != list(adapter.encoding.vocabulary.values)
            or saved_encoding.get('train_support_students') != adapter.encoding.train_support_students):
        raise ValueError('checkpoint encoding mismatch')
    progress = payload.get('progress', {})
    if progress.get('complete') is not True or int(progress.get('epoch', 0)) < 1:
        raise ValueError('checkpoint is incomplete')
    adapter.native.load_state_dict(payload['model_state_dict'])
    optimizer.load_state_dict(payload['optimizer_state_dict'])
    random.setstate(_nested_tuple(payload['python_rng']))
    numpy_state = payload['numpy_rng']
    np.random.set_state((numpy_state[0], np.asarray(numpy_state[1], dtype=np.uint32),
                         *numpy_state[2:]))
    torch.set_rng_state(payload['torch_rng'].cpu())
    cuda_states = payload.get('cuda_rng', [])
    if torch.cuda.is_available() and cuda_states:
        torch.cuda.set_rng_state_all(cuda_states)


def _nested_tuple(value):
    if isinstance(value, (tuple, list)):
        return tuple(_nested_tuple(item) for item in value)
    return value
