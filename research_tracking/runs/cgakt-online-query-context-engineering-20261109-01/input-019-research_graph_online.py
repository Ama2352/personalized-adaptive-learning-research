"""GRAPH16: evidence động từ observables; chưa backend/model/fitted authority.

Mỗi query độc lập có cùng lịch sử nhưng item khác được seal riêng. Giữ nguyên
geometry/OOV của A0 và guard index offline. NumPy data, không import Torch.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import hashlib
from pathlib import Path

import numpy as np

from ..graph_context import EdgeConfidence, audit_graph_context
from ..shared_kt import CausalSequenceInputs, PrerequisiteGraph
from ..simulator_bridge import ItemQuery, Observation, SimulatorBank, identity_hash
from . import research_graph_condition as conditions
from . import research_graph_context as contexts
from . import research_simulator_data as data
from .encoding import encode_exercises
from .types import WindowInputs
from .windows import iter_window_slices, slice_causal_inputs

NAMESPACE = 'grade10_simulator_item_id'
ROLE = 'constructed_observable_online_query_not_fitted'


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def source_inventory():
    rows = dict(contexts.source_inventory())
    rows['src/knowledge_tracing/akt/research_graph_online.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return tuple(sorted(rows.items()))


@dataclass(frozen=True)
class ResearchGraphOnlineLimits:
    max_history_events: int
    max_window_tokens: int

    def __post_init__(self):
        _need(type(self.max_history_events) is type(self.max_window_tokens) is int
              and self.max_history_events > 0 and 0 < self.max_window_tokens <= 200,
              'positive explicit history/token limits, maximum200 window tokens')


def _window_payload(window):
    if window is None:
        return None
    _need(type(window) is WindowInputs and type(window.inputs) is CausalSequenceInputs,
          'exact causal window required')
    arrays = {name: getattr(window.inputs, name) for name in
              ('item_ids', 'timestamps', 'prior_responses', 'source_rows', 'sequence_offsets')}
    arrays.update((name, getattr(window, name)) for name in
                  ('target_mask', 'global_ranks', 'history_available', 'history_used', 'context_reset'))
    _need(window.inputs.concept_ids is None and all(type(a) is np.ndarray and a.ndim == 1 for a in arrays.values()),
          'item-only NumPy window required')
    return dict(window_id=window.window_id, user_ids=window.inputs.user_ids,
                arrays={name: dict(dtype=a.dtype.str, values=a.tolist()) for name, a in arrays.items()})


@dataclass(frozen=True, init=False)
class ResearchGraphOnlineQuery:
    namespace: str
    learner_id: str
    query: ItemQuery
    condition_sha256: str
    encoding_sha256: str
    vocabulary_sha256: str
    domain_sha256: str
    history_sha256: str
    context: int
    target_block: int
    global_rank: int
    history_available: int
    history_used: int
    context_reset: bool
    support_reason: str
    audit: contexts.ResearchGraphAudit
    evidence: contexts.ResearchGraphQueryEvidence | None
    window: WindowInputs | None
    sources_sha256: tuple[tuple[str, str], ...]
    role: str = ROLE
    content_sha256: str = field(default='', repr=False)

    def __init__(self, *args, **kwargs):
        raise TypeError('use prepare_research_graph_online')

    def _payload(self):
        return {name: (_window_payload(value) if name == 'window' else asdict(value)
                      if name in ('query', 'audit', 'evidence') and value is not None else value)
                for name, value in vars(self).items() if name != 'content_sha256'}

    def assert_integrity(self):
        _need(self.role == ROLE and self.namespace == NAMESPACE
              and identity_hash(self._payload()) == self.content_sha256, 'online query payload drift')
        _need(self.sources_sha256 == source_inventory(), 'online query source drift')

    @property
    def identity(self):
        self.assert_integrity()
        return self.content_sha256


def prepare_research_graph_online(*, bank, encoding, condition, history, query,
                                 learner_id, namespace, limits, context, target_block):
    """Không nhận current response/future/peer state; không score hoặc update.

History là tuple của MỘT learner do caller cấp; không attestation session origin.
Chỉ Grade10 simulator namespace hiện có; cùng raw item strings không cho phép
chuyển encoding/domain Junyi. Source/lineage seals là cooperative consistency.
"""
    _need(type(bank) is SimulatorBank and type(encoding) is data.ResearchAKTEncoding
          and type(condition) is conditions.ResearchGraphCondition
          and type(limits) is ResearchGraphOnlineLimits, 'typed bank/encoding/condition/limits required')
    _need(namespace == NAMESPACE and type(namespace) is str, 'Grade10 simulator namespace required; no Junyi migration')
    _need(type(context) is type(target_block) is int and context == target_block == 100,
          'recipe26 native geometry context100/targetblock100')
    _need(type(learner_id) is str and bool(learner_id.strip()) and type(history) is tuple
          and len(history) <= limits.max_history_events and type(query) is ItemQuery,
          'bounded single learner immutable history/query required')
    _need(all(type(o) is Observation and type(o.query) is ItemQuery for o in history), 'typed observable history required')
    # Revalidate frozen public values; never read latent/profile/teacher state.
    replace(query)
    for observation in history:
        replace(observation.query); replace(observation)
    encoding.assert_integrity(); condition.assert_integrity()
    sources = source_inventory(); condition_id, encoding_id = condition.identity, encoding.identity
    domain = identity_hash(bank.identity)
    vocabulary = tuple(item for item, _ in encoding.support)
    _need(domain == encoding.domain_sha256 == condition.train80.domain_sha256
          and encoding.research_plan_sha256 == condition.train80.plan_sha256
          and set(vocabulary).issubset(bank.item_ids), 'encoding/condition bank domain or plan mismatch')
    expected_shards = dict(train=condition.train80.train_shard_sha256,
                           selection=condition.train80.selection_shard_sha256)
    _need(all(expected_shards.get(role) == digest for role, digest in encoding.origin_shard_sha256),
          'encoding neural-origin shard mismatch')
    graph = PrerequisiteGraph.from_edges(condition.nodes, condition.edges)
    _need(identity_hash(asdict(graph)) == condition.graph_sha256
          and set(graph.nodes) == {item.concept_id for item in bank.items}, 'graph/bank concept domain mismatch')
    confidence = EdgeConfidence(**condition.kernel_confidence_kwargs())
    audit_raw = audit_graph_context(bank=bank, graph=graph, confidence=confidence,
        history=history, query=query, trained_items=vocabulary, context=context, target_block=target_block)
    audit = contexts.ResearchGraphAudit(audit_raw['domain_sha256'], audit_raw['trained_items_sha256'], query,
        tuple(contexts.ResearchParentEvidence(**p) for p in audit_raw['parents']), tuple(audit_raw['observed_rows']),
        audit_raw['effective_start'], audit_raw['graph_sha256'], audit_raw['confidence_sha256'],
        confidence.kind, audit_raw['scoped_observations_sha256'], audit_raw['target_fitted'])
    rank = len(history)
    history_sha = identity_hash(dict(namespace=namespace, domain=domain, learner_id=learner_id,
                                    observations=[asdict(o) for o in history]))
    query_binding = dict(namespace=namespace, domain=domain, learner_id=learner_id,
        history=history_sha, query=asdict(query), encoding=encoding_id, vocabulary=identity_hash(list(vocabulary)),
        condition=condition_id, context=context, target_block=target_block)
    window_id = identity_hash(query_binding)
    window, evidence = None, None
    base = max(0, (rank // target_block)*target_block-context)
    available, used, reset = rank-base, 0, True
    if audit.target_fitted:
        queries = tuple(o.query for o in history)+(query,)
        ids = encode_exercises([q.item_id for q in queries], encoding.exercise_encoding())
        inputs = CausalSequenceInputs(ids, np.asarray([q.timestamp for q in queries], dtype=np.int64),
            np.asarray([-1]+[o.correct for o in history], dtype=np.int8),
            np.asarray([q.source_row for q in queries], dtype=np.int64),
            np.asarray([0,len(queries)], dtype=np.int64), tuple(learner_id for _ in queries), None)
        geometry = None
        for candidate in iter_window_slices(ids, inputs.sequence_offsets, context=context, target_block=target_block):
            if candidate.stop == len(ids):
                geometry = candidate
        _need(geometry is not None and not geometry.unseen, 'supported next-item geometry missing')
        window = replace(slice_causal_inputs(inputs, geometry), window_id=window_id)
        _need(len(window.inputs.item_ids) <= limits.max_window_tokens, 'online window token cap')
        local = len(window.inputs.item_ids)-1
        available, used, reset = int(window.history_available[-1]), int(window.history_used[-1]), bool(window.context_reset[-1])
        _need(audit.effective_start == rank-used
              and audit.observed_rows == tuple(int(r) for r in window.inputs.source_rows[:-1]),
              'graph/native effective past mismatch')
        evidence = contexts.ResearchGraphQueryEvidence(learner_id, query.source_row, rank, window_id, local, audit)
        # Arrays are owned copies, read-only by default; integrity also detects forced mutation.
        for container, names in ((window.inputs, ('item_ids','timestamps','prior_responses','source_rows','sequence_offsets')),
                                 (window, ('target_mask','global_ranks','history_available','history_used','context_reset'))):
            for name in names:
                getattr(container, name).setflags(write=False)
    _need(sources == source_inventory() and condition_id == condition.identity and encoding_id == encoding.identity,
          'online preparation source/encoding/condition drift')
    result = object.__new__(ResearchGraphOnlineQuery)
    values = dict(namespace=namespace, learner_id=learner_id, query=query, condition_sha256=condition_id,
        encoding_sha256=encoding_id, vocabulary_sha256=identity_hash(list(vocabulary)), domain_sha256=domain,
        history_sha256=history_sha, context=context, target_block=target_block, global_rank=rank,
        history_available=available, history_used=used, context_reset=reset,
        support_reason='supported' if audit.target_fitted else 'unseen_item', audit=audit, evidence=evidence,
        window=window, sources_sha256=sources, role=ROLE, content_sha256='')
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, 'content_sha256', identity_hash(result._payload()))
    return result
