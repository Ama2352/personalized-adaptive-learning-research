"""GKT static-message/readout equations; chưa gate, recurrence, trainer hay fitted model.

Nguồn: Nakagawa et al., RLiGM2019 §2.1–2.2 Eq1–2 và journal2021 §3.2–3.3.
Caller cung cấp state, embeddings và messages đã biến đổi bởi f_self/out/in.
Không chọn MLP, normalization, erase–add, initial state hoặc policy mastery.
"""

from dataclasses import dataclass
import hashlib

import torch

from .config import GKTBinding, GKTKernelConfig


def _tensor(value, shape, reference=None):
    if (not isinstance(value, torch.Tensor) or tuple(value.shape) != tuple(shape)
            or value.device.type != 'cpu' or value.dtype not in (torch.float32, torch.float64)
            or not torch.isfinite(value).all()):
        raise ValueError('finite CPU FP32/FP64 tensor with exact shape required')
    if reference is not None and value.dtype != reference.dtype:
        raise ValueError('tensor dtypes must match')


def adjacency_sha256(adjacency):
    """Bind actual matrix bytes, dtype và shape; không attest graph training origin."""
    payload = adjacency.detach().contiguous().numpy().tobytes()
    header = f'{adjacency.dtype}:{tuple(adjacency.shape)}:'.encode('ascii')
    return hashlib.sha256(header + payload).hexdigest()


def dense_adjacency(num_nodes, *, dtype):
    """Paper Dense: off-diagonal 1/(N−1), diagonal0; N1 chưa có convention."""
    if type(num_nodes) is not int or num_nodes <= 1 or dtype not in (torch.float32, torch.float64):
        raise ValueError('Dense requires N>1 and explicit FP32/FP64 dtype')
    result = torch.full((num_nodes, num_nodes), 1 / (num_nodes - 1), dtype=dtype)
    result.fill_diagonal_(0)
    return result


@dataclass(frozen=True)
class GKTMessages:
    values: torch.Tensor
    support_mask: torch.Tensor


@dataclass(frozen=True)
class GKTReadout:
    logits: torch.Tensor
    probabilities: torch.Tensor
    evidence_role: str = 'caller_tensor_kernel_no_fit_attestation'


class StaticGKTKernel:
    """Stateless arithmetic. Query trước observe do caller điều phối, chưa session API.

    Mỗi call yêu cầu binding và expected actual adjacency digest. Không đọc file,
    không fit, không giữ learner history. Support mask chỉ mô tả graph support,
    không quyết định sparse GRU update policy.
    """

    def __init__(self, config: GKTKernelConfig, binding: GKTBinding, adjacency: torch.Tensor):
        if not isinstance(config, GKTKernelConfig) or not isinstance(binding, GKTBinding):
            raise ValueError('typed config and binding required')
        if len(binding.node_ids) != config.num_nodes or binding.node_unit != config.node_unit:
            raise ValueError('node identity/geometry mismatch')
        _tensor(adjacency, (config.num_nodes, config.num_nodes))
        if adjacency.requires_grad:
            raise ValueError('Batch A adjacency is fixed, not a learned graph')
        if torch.any(adjacency < 0) or torch.any(adjacency.diagonal() != 0):
            raise ValueError('adjacency must be nonnegative with diagonal zero')
        if config.adjacency_kind == 'dense' and not torch.equal(adjacency, dense_adjacency(config.num_nodes, dtype=adjacency.dtype)):
            raise ValueError('Dense adjacency must match the paper formula exactly')
        self.config = config
        self.binding = binding
        self._adjacency = adjacency.detach().clone()
        self.adjacency_sha256 = adjacency_sha256(self._adjacency)

    def _bound(self, binding, graph_sha256):
        if binding != self.binding or graph_sha256 != self.adjacency_sha256:
            raise ValueError('domain/vocabulary/node order/graph binding mismatch')
        if adjacency_sha256(self._adjacency) != self.adjacency_sha256:
            raise ValueError('internal graph changed after binding')

    def _ids(self, ids, batch):
        if (not isinstance(ids, torch.Tensor) or ids.dtype != torch.long
                or ids.device.type != 'cpu' or ids.shape != (batch,)
                or torch.any(ids < 0) or torch.any(ids >= self.config.num_nodes)):
            raise ValueError('known CPU node IDs required; no padding/OOV convention')

    def aggregate_after_observation(self, state, answered_ids, responses, concept_embeddings,
                                    interaction_embeddings, *, binding, graph_sha256):
        """z[i]=[H[i],E_x(i,r)], z[j]=[H[j],E_c(j)]. Không cập nhật H.

        Phải gọi readout cho current query trước khi caller cung cấp response.
        Kernel không attest caller chronology hoặc origin của labels.
        """
        self._bound(binding, graph_sha256)
        c = self.config
        batch = state.shape[0] if isinstance(state, torch.Tensor) and state.ndim == 3 else 0
        if batch <= 0:
            raise ValueError('nonempty [batch,node,state] required')
        _tensor(state, (batch, c.num_nodes, c.state_dim), self._adjacency)
        self._ids(answered_ids, batch)
        if (not isinstance(responses, torch.Tensor) or responses.shape != (batch,)
                or responses.device.type != 'cpu' or responses.dtype != torch.long
                or torch.any((responses != 0) & (responses != 1))):
            raise ValueError('post-observation responses must be binary CPU integers')
        _tensor(concept_embeddings, (c.num_nodes, c.embedding_dim), state)
        _tensor(interaction_embeddings, (2 * c.num_nodes, c.embedding_dim), state)
        nodes = torch.arange(c.num_nodes)[None, :]
        observed = nodes == answered_ids[:, None]
        qa = interaction_embeddings[answered_ids + responses * c.num_nodes]
        embeddings = torch.where(observed[..., None], qa[:, None, :], concept_embeddings[None, :, :])
        return torch.cat((state, embeddings), dim=-1)

    def combine_messages(self, answered_ids, self_messages, outgoing_messages, incoming_messages,
                         *, binding, graph_sha256):
        """Eq2: A[i,j]*f_out([z_i,z_j])+A[j,i]*f_in([z_i,z_j]).

        Caller phải tính f independently cho mỗi row; precomputed messages
        không được kernel attest tính nhân quả, normalization hay peer isolation.
        """
        self._bound(binding, graph_sha256)
        c = self.config
        batch = self_messages.shape[0] if isinstance(self_messages, torch.Tensor) and self_messages.ndim == 2 else 0
        if batch <= 0:
            raise ValueError('nonempty [batch,message] required')
        _tensor(self_messages, (batch, c.message_dim), self._adjacency)
        self._ids(answered_ids, batch)
        _tensor(outgoing_messages, (batch, c.num_nodes, c.message_dim), self_messages)
        _tensor(incoming_messages, (batch, c.num_nodes, c.message_dim), self_messages)
        out_weights = self._adjacency[answered_ids]
        in_weights = self._adjacency[:, answered_ids].T
        values = out_weights[..., None] * outgoing_messages + in_weights[..., None] * incoming_messages
        self_mask = torch.arange(c.num_nodes)[None, :] == answered_ids[:, None]
        values = torch.where(self_mask[..., None], self_messages[:, None, :], values)
        _tensor(values, (batch, c.num_nodes, c.message_dim), self_messages)
        support = self_mask | (out_weights != 0) | (in_weights != 0)
        return GKTMessages(values, support)

    def readout(self, state, query_ids, weight, node_bias, *, binding, graph_sha256):
        """σ(w @ H[query]+b_query); signature không nhận current answer."""
        self._bound(binding, graph_sha256)
        c = self.config
        batch = state.shape[0] if isinstance(state, torch.Tensor) and state.ndim == 3 else 0
        if batch <= 0:
            raise ValueError('nonempty [batch,node,state] required')
        _tensor(state, (batch, c.num_nodes, c.state_dim), self._adjacency)
        self._ids(query_ids, batch)
        _tensor(weight, (c.state_dim,), state)
        _tensor(node_bias, (c.num_nodes,), state)
        selected = state[torch.arange(batch), query_ids]
        logits = (selected * weight).sum(-1) + node_bias[query_ids]
        _tensor(logits, (batch,), state)
        return GKTReadout(logits, logits.sigmoid())
