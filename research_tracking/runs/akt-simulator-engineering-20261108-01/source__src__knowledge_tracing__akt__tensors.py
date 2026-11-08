"""Tensor hóa cửa sổ AKT mà không đưa target hiện tại vào response input."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from .types import WindowInputs


@dataclass(frozen=True)
class AKTBatch:
    q_data: torch.Tensor
    qa_data: torch.Tensor
    loss_targets: torch.Tensor
    valid_mask: torch.Tensor
    target_mask: torch.Tensor
    source_rows: np.ndarray


def causal_masks(length: int, device: str) -> tuple[torch.Tensor, torch.Tensor]:
    if length < 0:
        raise ValueError('invalid sequence length')
    matrix = torch.ones((length, length), dtype=torch.bool, device=device)
    return torch.tril(matrix), torch.tril(matrix, diagonal=-1)


def collate_windows(windows: Sequence[WindowInputs], *, n_items: int, device: str,
                    targets: Sequence[np.ndarray] | None = None) -> AKTBatch:
    if not windows or n_items <= 0 or (targets is not None and len(targets) != len(windows)):
        raise ValueError('invalid windows, item count or targets')
    lengths = [len(window.inputs.item_ids) for window in windows]
    if min(lengths) <= 0:
        raise ValueError('empty windows are not supported')
    shape = (len(windows), max(lengths))
    q = np.zeros(shape, dtype=np.int64)
    qa = np.zeros(shape, dtype=np.int64)
    loss = np.full(shape, -1, dtype=np.float32)
    valid = np.zeros(shape, dtype=bool)
    mask = np.zeros(shape, dtype=bool)
    source_rows = np.full(shape, -1, dtype=np.int64)
    for row, (window, length) in enumerate(zip(windows, lengths)):
        inputs = window.inputs
        ids = np.asarray(inputs.item_ids, dtype=np.int64)
        prior = np.asarray(inputs.prior_responses, dtype=np.int64)
        target_mask = np.asarray(window.target_mask, dtype=bool)
        if (len(prior) != length or len(target_mask) != length or len(inputs.source_rows) != length
                or np.any(ids < 0) or np.any(ids >= n_items) or prior[0] != -1
                or not np.isin(prior[1:], (0, 1)).all()):
            raise ValueError('invalid causal window inputs')
        question = ids + 1
        responses = np.zeros(length, dtype=np.int64)
        responses[:-1] = prior[1:]
        q[row, :length] = question
        qa[row, :length] = question + n_items * responses
        valid[row, :length] = True
        mask[row, :length] = target_mask
        source_rows[row, :length] = inputs.source_rows
        if targets is not None:
            labels = np.asarray(targets[row])
            if labels.shape != (length,) or not np.isin(labels, (0, 1)).all():
                raise ValueError('invalid target labels')
            loss[row, :length][target_mask] = labels[target_mask]
    return AKTBatch(torch.as_tensor(q, dtype=torch.long, device=device),
                    torch.as_tensor(qa, dtype=torch.long, device=device),
                    torch.as_tensor(loss, dtype=torch.float32, device=device),
                    torch.as_tensor(valid, dtype=torch.bool, device=device),
                    torch.as_tensor(mask, dtype=torch.bool, device=device), source_rows)
