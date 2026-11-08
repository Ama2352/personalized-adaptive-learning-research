"""Kernel hợp đồng residual graph, chưa tích hợp hoặc huấn luyện CG-AKT.

Reuse audit_graph_context cho support/geometry/provenance. Kernel chỉ thực hiện
sum(c * observed * message) / max(1, sum(c * observed)), rồi gate * readout.
Không chọn f, gate features, optimizer hoặc hook latent/logit vào native AKT.
Messages phải do caller tạo từ evidence bên dưới và embeddings train-only;
không thể chứng minh provenance của một tensor tùy ý tại boundary này.
"""

from dataclasses import dataclass

import torch
from torch import Tensor

from .graph_context import EdgeConfidence, audit_graph_context
from .shared_kt import PrerequisiteGraph
from .simulator_bridge import ItemQuery, Observation, SimulatorBank


@dataclass(frozen=True)
class GraphContextBinding:
    """Identity của domain và vocabulary phải khớp base model bên gọi."""

    domain_sha256: str
    trained_items_sha256: str


@dataclass(frozen=True)
class ParentEvidence:
    parent: str
    support: int
    confidence: float
    mean_observed_correctness: float | None


@dataclass(frozen=True)
class PreparedGraphContext:
    binding: GraphContextBinding
    query: ItemQuery
    parents: tuple[ParentEvidence, ...]
    observed_rows: tuple[int, ...]
    effective_start: int
    graph_sha256: str
    confidence_sha256: str
    confidence_kind: str
    scoped_observations_sha256: str
    target_fitted: bool


def prepare_graph_context(*, bank: SimulatorBank, graph: PrerequisiteGraph,
                          confidence: EdgeConfidence, history: tuple[Observation, ...],
                          query: ItemQuery, trained_items: tuple[str, ...], context: int,
                          target_block: int, oracle_reference: bool = False) -> PreparedGraphContext:
    """Chỉ effective window; oracle chỉ được chuẩn bị khi khai báo reference.

Không nhận current outcome hoặc sidecar. History phải thuộc một learner do
session bên gọi cô lập; Observation hiện không chứa learner_id để tự xác minh.
"""
    if type(oracle_reference) is not bool:
        raise ValueError('oracle_reference must be boolean')
    audited = audit_graph_context(
        bank=bank, graph=graph, confidence=confidence, history=history, query=query,
        trained_items=trained_items, context=context, target_block=target_block,
        purpose='oracle_reference' if oracle_reference else 'matched_audit')
    return PreparedGraphContext(
        binding=GraphContextBinding(audited['domain_sha256'], audited['trained_items_sha256']),
        query=query, parents=tuple(ParentEvidence(**parent) for parent in audited['parents']),
        observed_rows=tuple(audited['observed_rows']), effective_start=audited['effective_start'],
        graph_sha256=audited['graph_sha256'], confidence_sha256=audited['confidence_sha256'],
        confidence_kind=confidence.kind,
        scoped_observations_sha256=audited['scoped_observations_sha256'],
        target_fitted=audited['target_fitted'])


@dataclass(frozen=True)
class GraphResidualOutput:
    logit: Tensor
    residual: Tensor
    applied: bool
    confidence_mass: float
    normalizer: float


def _tensor_contract(value: Tensor, *, shape: tuple[int, ...], reference: Tensor, name: str) -> None:
    if (not isinstance(value, Tensor) or value.shape != shape
            or value.dtype != reference.dtype or value.device != reference.device
            or not torch.isfinite(value).all().item()):
        raise ValueError(f'invalid {name}: shape, floating dtype, device or finiteness')


def apply_graph_residual(base_logit: Tensor, *, evidence: PreparedGraphContext,
                         binding: GraphContextBinding, edge_messages: Tensor | None = None,
                         readout: Tensor | None = None, gate: Tensor | None = None,
                         enabled: bool = True, oracle_reference: bool = False) -> GraphResidualOutput:
    """Một fitted query: scalar base/gate, messages[E,D], readout[D].

Gate là influence explicit [0,1], không phải confidence của cạnh. Caller có
thể cấp 1 cho fixed/weighted, sigmoid scalar cho prototype gate, hoặc disable.
Không detach active tensors: hỗ trợ kiểm gradient nhưng không train ở đây.
Disabled, graph-empty, no support, all c=0 hoặc gate=0 trả đúng cùng object
base_logit, không sigmoid/logit roundtrip. Không phải system fallback sang A0
checkpoint riêng; chưa có integration vào backbone đã jointly train.

Binding phải lấy từ metadata base model được bên gọi xác minh. Dataclass là
contract trong process, không phải chứng thực chống giả mạo/cross-domain tensor.
"""
    if type(enabled) is not bool or type(oracle_reference) is not bool:
        raise ValueError('enabled and oracle_reference must be boolean')
    if not isinstance(evidence, PreparedGraphContext) or evidence.binding != binding:
        raise ValueError('graph/base domain or vocabulary binding mismatch')
    if evidence.confidence_kind == 'oracle_label' and not oracle_reference:
        raise ValueError('oracle confidence is restricted to reference mode')
    if not evidence.target_fitted:
        raise ValueError('graph cannot rescue an unfitted/OOV base target')
    if not isinstance(base_logit, Tensor) or not base_logit.is_floating_point():
        raise ValueError('base_logit must be a floating scalar tensor')
    _tensor_contract(base_logit, shape=(), reference=base_logit, name='base_logit')
    mass = sum(parent.confidence for parent in evidence.parents if parent.support > 0)
    normalizer = max(1.0, mass)

    def bypass() -> GraphResidualOutput:
        return GraphResidualOutput(base_logit, torch.zeros_like(base_logit), False, mass, normalizer)

    if not enabled or mass == 0:
        return bypass()
    _tensor_contract(gate, shape=(), reference=base_logit, name='gate')
    if not 0 <= gate.item() <= 1:
        raise ValueError('gate must lie in [0,1]')
    if gate.item() == 0:
        return bypass()
    if not isinstance(readout, Tensor) or readout.ndim != 1 or readout.numel() < 1:
        raise ValueError('readout must have shape [D] with D >= 1')
    _tensor_contract(readout, shape=(readout.numel(),), reference=base_logit, name='readout')
    _tensor_contract(edge_messages, shape=(len(evidence.parents), readout.numel()),
                     reference=base_logit, name='edge_messages')
    weights = base_logit.new_tensor([p.confidence if p.support > 0 else 0 for p in evidence.parents])
    message = (weights[:, None] * edge_messages).sum(dim=0) / normalizer
    residual = gate * torch.dot(readout, message)
    if not torch.isfinite(residual).item():
        raise ValueError('nonfinite graph residual')
    augmented = base_logit + residual
    if not torch.isfinite(augmented).item():
        raise ValueError('nonfinite augmented logit')
    return GraphResidualOutput(augmented, residual, True, mass, normalizer)
