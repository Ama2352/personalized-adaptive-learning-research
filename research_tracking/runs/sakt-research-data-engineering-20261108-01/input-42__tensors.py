"""Đóng gói sequence đã có prior_responses; không nhận target hiện tại."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from knowledge_tracing.shared_kt import CausalSequenceInputs


@dataclass(frozen=True)
class SAKTInputs:
    item_ids: torch.Tensor
    prior_responses: torch.Tensor
    valid_mask: torch.Tensor


def collate_sequences(sequences: Sequence[CausalSequenceInputs], *, num_items: int,
                      max_length: int, padding_side: str, device: str) -> SAKTInputs:
    """Mỗi phần tử là một learner/window; giữ thứ tự, không cắt ngầm history.

    Shared IDs 0..N-1 chuyển thành 1..N; ID 0 dành riêng padding. Caller
    phải dùng vocabulary train-only và chuẩn bị window/context trước khi gọi.
    """
    if (not sequences or type(num_items) is not int or num_items <= 0
            or type(max_length) is not int or max_length <= 0
            or padding_side not in {'left', 'right'}):
        raise ValueError('invalid sequences, dimensions or padding_side')
    lengths = [len(sequence.item_ids) for sequence in sequences]
    if min(lengths) <= 0 or max(lengths) > max_length:
        raise ValueError('empty or overlength sequence; explicit windowing is required')
    shape = (len(sequences), max(lengths))
    items = np.zeros(shape, dtype=np.int64)
    prior = np.full(shape, -1, dtype=np.int64)
    valid = np.zeros(shape, dtype=bool)
    for row, (sequence, length) in enumerate(zip(sequences, lengths)):
        ids = np.asarray(sequence.item_ids)
        responses = np.asarray(sequence.prior_responses)
        if (ids.shape != (length,) or responses.shape != (length,)
                or not np.issubdtype(ids.dtype, np.integer)
                or not np.issubdtype(responses.dtype, np.integer)
                or np.any(ids < 0) or np.any(ids >= num_items)
                or responses[0] != -1 or not np.isin(responses[1:], (0, 1)).all()
                or not np.array_equal(sequence.sequence_offsets, [0, length])
                or len(sequence.user_ids) != length or len(set(sequence.user_ids)) != 1):
            raise ValueError('invalid single-learner causal sequence')
        start = 0 if padding_side == 'right' else shape[1] - length
        region = slice(start, start + length)
        items[row, region] = ids + 1
        prior[row, region] = responses
        valid[row, region] = True
    return SAKTInputs(torch.as_tensor(items, dtype=torch.long, device=device),
                      torch.as_tensor(prior, dtype=torch.long, device=device),
                      torch.as_tensor(valid, dtype=torch.bool, device=device))
