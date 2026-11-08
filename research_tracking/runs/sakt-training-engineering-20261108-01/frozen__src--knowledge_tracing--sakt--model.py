"""SAKT một block theo arXiv:1907.06837v1, phương trình (1)–(6).

Không port TensorFlow/checkpoint của tác giả. Q/K/V tuyến tính không bias,
WO ghép heads, FFN d→d→d, residual từ query và post-layernorm. Chi tiết
khác mã tác giả được nêu trong báo cáo provenance; không có prerequisite graph.
"""

from dataclasses import dataclass
import math

import torch
from torch import nn

from .config import SAKTConfig
from .tensors import SAKTInputs


@dataclass(frozen=True)
class SAKTOutput:
    logits: torch.Tensor
    probabilities: torch.Tensor
    attention_weights: torch.Tensor
    valid_mask: torch.Tensor
    has_history: torch.Tensor


class SAKTCore(nn.Module):
    """Predict r[t] từ e[t] và (e[j],r[j]) với j<t.

    Input chỉ chứa prior_responses[t]=r[t-1], không chứa labels để tính loss.
    ID item 1..N, padding 0; prior -1 tại cold/padding, 0/1 ở phần còn lại.
    Padding phải ở hai đầu, không có gap nội bộ. First target có attention=0,
    score query-only hữu hạn và has_history=False; metric policy chưa được chốt.
    Logits/probabilities padding bằng 0 là sentinel, chỉ valid_mask được chấm.
    """

    def __init__(self, config: SAKTConfig):
        super().__init__()
        self.config = config
        width = config.num_heads * config.head_dim
        self.exercise_embedding = nn.Embedding(config.num_items + 1, config.d_model, padding_idx=0)
        self.interaction_embedding = nn.Embedding(2 * config.num_items + 1, config.d_model, padding_idx=0)
        self.position_embedding = nn.Embedding(config.max_length, config.d_model)
        self.query_projection = nn.Linear(config.d_model, width, bias=False)
        self.key_projection = nn.Linear(config.d_model, width, bias=False)
        self.value_projection = nn.Linear(config.d_model, width, bias=False)
        self.output_projection = nn.Linear(width, config.d_model, bias=False)
        self.attention_norm = nn.LayerNorm(config.d_model, eps=config.layer_norm_eps)
        self.feedforward = nn.Sequential(nn.Linear(config.d_model, config.d_model), nn.ReLU(),
                                         nn.Dropout(config.dropout), nn.Linear(config.d_model, config.d_model))
        self.feedforward_norm = nn.LayerNorm(config.d_model, eps=config.layer_norm_eps)
        self.dropout = nn.Dropout(config.dropout)
        self.prediction = nn.Linear(config.d_model, 1)

    def _validate(self, batch: SAKTInputs) -> torch.Tensor:
        ids, prior, valid = batch.item_ids, batch.prior_responses, batch.valid_mask
        if (ids.ndim != 2 or ids.shape != prior.shape or ids.shape != valid.shape
                or ids.shape[0] == 0 or not 0 < ids.shape[1] <= self.config.max_length
                or ids.dtype != torch.long or prior.dtype != torch.long or valid.dtype != torch.bool
                or ids.device != prior.device or ids.device != valid.device):
            raise ValueError('invalid input shape, dtype, device or sequence length')
        if (torch.any(ids < 0) or torch.any(ids > self.config.num_items)
                or not torch.equal(valid, ids != 0)):
            raise ValueError('item IDs must be known and match valid_mask')
        # Một đoạn valid liên tục; trái/phải/all padding đều hợp lệ.
        first = valid.to(torch.long).argmax(dim=1)
        last = ids.shape[1] - 1 - valid.flip(1).to(torch.long).argmax(dim=1)
        if torch.any(valid.any(dim=1) & (valid.sum(dim=1) != last - first + 1)):
            raise ValueError('internal padding gaps are not allowed')
        previous_valid = torch.zeros_like(valid)
        previous_valid[:, 1:] = valid[:, :-1]
        historical = valid & previous_valid
        if (torch.any(prior[~historical] != -1)
                or torch.any((prior[historical] != 0) & (prior[historical] != 1))):
            raise ValueError('responses must be shifted, binary, and -1 at cold/padding')
        return historical

    def forward(self, batch: SAKTInputs) -> SAKTOutput:
        historical = self._validate(batch)
        ids, prior, valid = batch.item_ids, batch.prior_responses, batch.valid_mask
        batch_size, length = ids.shape
        previous_items = torch.zeros_like(ids)
        previous_items[:, 1:] = ids[:, :-1]
        qa_ids = (previous_items + self.config.num_items * prior.clamp_min(0)).masked_fill(~historical, 0)
        # Slot j chứa interaction j-1: vị trí của interaction, không phải vị trí query.
        positions = (valid.cumsum(dim=1) - 2).clamp_min(0)
        history = self.interaction_embedding(qa_ids) + self.position_embedding(positions)
        history = self.dropout(history).masked_fill(~historical.unsqueeze(-1), 0)
        queries = self.exercise_embedding(ids)

        def split_heads(tensor: torch.Tensor) -> torch.Tensor:
            return tensor.reshape(batch_size, length, self.config.num_heads,
                                  self.config.head_dim).transpose(1, 2)

        q = split_heads(self.query_projection(queries))
        k = split_heads(self.key_projection(history))
        v = split_heads(self.value_projection(history))
        scores = (q @ k.transpose(-2, -1)) / math.sqrt(self.config.head_dim)
        # Inclusive theo slot đã shift => strict past theo event: không double-shift.
        causal = torch.ones((length, length), dtype=torch.bool, device=ids.device).tril()
        allowed = causal[None, None] & historical[:, None, None, :] & valid[:, None, :, None]
        weights = torch.softmax(scores.masked_fill(~allowed, torch.finfo(scores.dtype).min), dim=-1)
        # All-masked row được đưa về 0, tránh softmax(-inf,...,-inf) thành NaN.
        weights = weights.masked_fill(~allowed, 0)
        weights = weights / weights.sum(dim=-1, keepdim=True).clamp_min(torch.finfo(weights.dtype).tiny)
        context = (self.dropout(weights) @ v).transpose(1, 2).reshape(batch_size, length, -1)
        hidden = self.attention_norm(queries + self.dropout(self.output_projection(context)))
        hidden = self.feedforward_norm(hidden + self.dropout(self.feedforward(hidden)))
        logits = self.prediction(hidden).squeeze(-1).masked_fill(~valid, 0)
        probabilities = torch.sigmoid(logits).masked_fill(~valid, 0)
        has_history = allowed.any(dim=-1).squeeze(1)
        return SAKTOutput(logits, probabilities, weights, valid, has_history)
