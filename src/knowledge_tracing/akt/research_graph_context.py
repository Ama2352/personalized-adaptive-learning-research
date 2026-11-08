"""Index graph past-only cho research windows; NumPy data, không Torch/model.

Reuse geometry và audit hiện có. Index không giữ phase, bank, trajectories,
labels hoặc full corpus. Metadata lineage là consistency, không fitted authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

from ..graph_context import EdgeConfidence, audit_graph_context
from ..shared_kt import CausalSequenceInputs, PrerequisiteGraph
from ..simulator_bridge import ItemQuery, identity_hash
from . import research_graph_condition as conditions
from . import research_simulator_data as data
from .types import WindowInputs

ROOT = Path(__file__).resolve().parents[3]
ROLE = 'research_graph_causal_context_index_only'


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def source_inventory():
    rows = dict(conditions.source_inventory())
    rows.update(('src/knowledge_tracing/' + name, digest) for name, digest in data.source_identity())
    rows['src/knowledge_tracing/akt/research_graph_context.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return tuple(sorted(rows.items()))


@dataclass(frozen=True)
class ResearchGraphContextLimits:
    max_total_events: int
    max_events_per_learner: int
    max_targets: int
    max_windows: int
    max_window_tokens: int
    max_parent_records: int
    max_observed_rows: int
    max_cache_bytes: int
    max_seconds: float

    def __post_init__(self):
        for name, value in asdict(self).items():
            if name == 'max_seconds':
                _need(type(value) in (int, float) and math.isfinite(value) and value > 0, 'positive finite context deadline')
            else:
                _need(type(value) is int and value > 0, 'positive explicit context limits')


@dataclass(frozen=True)
class ResearchParentEvidence:
    parent: str
    support: int
    confidence: float
    mean_observed_correctness: float | None


@dataclass(frozen=True)
class ResearchGraphAudit:
    domain_sha256: str
    trained_items_sha256: str
    query: ItemQuery
    parents: tuple[ResearchParentEvidence, ...]
    observed_rows: tuple[int, ...]
    effective_start: int
    graph_sha256: str
    confidence_sha256: str
    confidence_kind: str
    scoped_observations_sha256: str
    target_fitted: bool


@dataclass(frozen=True)
class ResearchGraphQueryEvidence:
    learner_id: str
    source_row: int
    global_rank: int
    window_id: str
    local_position: int
    audit: ResearchGraphAudit


@dataclass(frozen=True)
class ResearchGraphUnsupportedTarget:
    learner_id: str
    query: ItemQuery
    global_rank: int
    reason: str


@dataclass(frozen=True)
class ResearchGraphIndexedWindow:
    window_id: str
    learner_id: str
    inputs_sha256: str
    contexts: tuple[ResearchGraphQueryEvidence | None, ...]


def _window_payload(window, max_tokens):
    _need(type(window) is WindowInputs, 'exact WindowInputs required; OOV targets cannot enter graph/native batch')
    inputs = window.inputs
    _need(type(inputs) is CausalSequenceInputs, 'exact label-free CausalSequenceInputs required')
    n = len(inputs.item_ids)
    _need(0 < n <= max_tokens and inputs.concept_ids is None,
          'bounded item-only causal window required; concept IDs are not native AKT inputs')
    arrays = {name: getattr(inputs, name) for name in
              ('item_ids', 'timestamps', 'prior_responses', 'source_rows', 'sequence_offsets')}
    arrays.update((name, getattr(window, name)) for name in
                  ('target_mask', 'global_ranks', 'history_available', 'history_used', 'context_reset'))
    _need(all(type(a) is np.ndarray and a.ndim == 1 for a in arrays.values()), 'one-dimensional NumPy window arrays required')
    _need(len(inputs.user_ids) == n and len(set(inputs.user_ids)) == 1
          and all(len(a) == (2 if name == 'sequence_offsets' else n) for name, a in arrays.items()),
          'single learner window shape')
    return dict(window_id=window.window_id, user_ids=inputs.user_ids,
        arrays={name: dict(dtype=a.dtype.str, values=a.tolist()) for name, a in arrays.items()})


@dataclass(frozen=True, init=False)
class ContextAccessSeal:
    """Process-local cache access; không checkpoint/capability/fit authority."""
    root_sha256: str
    header_sha256: str
    record_sha256: tuple[tuple[str, str], ...]
    index_object_id: int
    windows_object_id: int
    unsupported_object_id: int
    manifest_object_id: int

    def __init__(self, *args, **kwargs):
        raise TypeError('use index.seal_for_access after full audit')


@dataclass(frozen=True, init=False)
class ResearchGraphContextIndex:
    condition_sha256: str
    phase_sha256: str
    encoding_sha256: str
    vocabulary_sha256: str
    neural_binding: conditions.GraphNeuralPhaseBinding
    sources_sha256: tuple[tuple[str, str], ...]
    context: int
    target_block: int
    windows: tuple[ResearchGraphIndexedWindow, ...]
    unsupported_targets: tuple[ResearchGraphUnsupportedTarget, ...]
    full_targets: int
    limits: ResearchGraphContextLimits
    role: str = ROLE
    content_sha256: str = field(default='', repr=False)

    def __init__(self, *args, **kwargs):
        raise TypeError('use prepare_research_graph_context')

    def _payload(self):
        return {name: value for name, value in asdict(self).items() if name != 'content_sha256'}

    def assert_integrity(self):
        _need(self.content_sha256 == identity_hash(self._payload()), 'context index payload drift')
        _need(self.sources_sha256 == source_inventory(), 'context index source drift')

    def _access_header(self):
        # Không contexts/observed rows hoặc full unsupported ledger ở hot path.
        return dict(condition=self.condition_sha256, phase=self.phase_sha256,
            encoding=self.encoding_sha256, vocabulary=self.vocabulary_sha256,
            neural_binding=asdict(self.neural_binding), sources=self.sources_sha256,
            context=self.context, target_block=self.target_block, full_targets=self.full_targets,
            limits=asdict(self.limits), role=self.role, windows=len(self.windows),
            unsupported=len(self.unsupported_targets))

    def seal_for_access(self):
        self.assert_integrity()
        manifest = tuple((w.window_id, identity_hash(asdict(w))) for w in self.windows)
        seal = object.__new__(ContextAccessSeal)
        values = dict(root_sha256=self.content_sha256, header_sha256=identity_hash(self._access_header()),
            record_sha256=manifest, index_object_id=id(self), windows_object_id=id(self.windows),
            unsupported_object_id=id(self.unsupported_targets), manifest_object_id=id(manifest))
        for name, value in values.items():
            object.__setattr__(seal, name, value)
        # Bind manifest và header chỉ khi full payload vẫn nguyên tại boundary.
        self.assert_integrity()
        self.check_access_header(seal)
        return seal

    def check_access_header(self, seal):
        _need(type(seal) is ContextAccessSeal and id(self) == seal.index_object_id,
              'foreign context access seal')
        _need(id(self.windows) == seal.windows_object_id
              and id(self.unsupported_targets) == seal.unsupported_object_id
              and id(seal.record_sha256) == seal.manifest_object_id,
              'context/manifest tuple replacement')
        _need(self.content_sha256 == seal.root_sha256
              and identity_hash(self._access_header()) == seal.header_sha256,
              'context header/root drift')
        _need(self.sources_sha256 == source_inventory(), 'context index source drift')

    def check_selected_records(self, window_ids, *, access_seal):
        self.check_access_header(access_seal)
        _need(type(window_ids) is tuple and 0 < len(window_ids) <= self.limits.max_windows
              and all(type(i) is str for i in window_ids)
              and len(set(window_ids)) == len(window_ids), 'bounded unique selected window IDs')
        lookup = {record.window_id: record for record in self.windows}
        manifest = dict(access_seal.record_sha256)
        for name in window_ids:
            _need(name in lookup and name in manifest, 'foreign selected record')
            _need(identity_hash(asdict(lookup[name])) == manifest[name], 'selected evidence drift')

    @property
    def identity(self):
        self.assert_integrity()
        return self.content_sha256

    def for_windows(self, windows, *, access_seal=None):
        """Trả context theo từng vị trí; non-target=None, không dựng lại quá khứ."""
        if access_seal is None:
            self.assert_integrity()
        else:
            self.check_access_header(access_seal)
        _need(type(windows) is tuple and 0 < len(windows) <= self.limits.max_windows, 'bounded immutable window request')
        lookup = {record.window_id: record for record in self.windows}
        manifest = None if access_seal is None else dict(access_seal.record_sha256)
        result, seen = [], set()
        for window in windows:
            payload = _window_payload(window, self.limits.max_window_tokens)
            _need(window.window_id in lookup and window.window_id not in seen, 'foreign/duplicate window identity')
            record = lookup[window.window_id]
            if manifest is not None:
                _need(window.window_id in manifest and identity_hash(asdict(record)) == manifest[window.window_id],
                      'selected evidence drift')
            _need(identity_hash(payload) == record.inputs_sha256, 'window/query/prior/geometry payload drift')
            seen.add(window.window_id); result.append(record.contexts)
        return tuple(result)


def prepare_research_graph_context(phase, encoding, condition, *, limits,
                                   fit80_encoding_sha256, context, target_block):
    """Build một index immutable; source/phase checks ở cache boundaries.

    Prefix chỉ dùng để gọi audit_graph_context. Nó không được giữ trong result.
    Hash full phase/window có thể đổi bởi future labels; audit p_t vẫn past-only.
    """
    started = time.perf_counter()
    _need(type(phase) is data.ResearchPhaseData and type(encoding) is data.ResearchAKTEncoding
          and type(condition) is conditions.ResearchGraphCondition and type(limits) is ResearchGraphContextLimits,
          'typed research phase/encoding/condition/limits required')
    _need(type(context) is type(target_block) is int and context == target_block == 100,
          'recipe26 preserves native context100/targetblock100')
    def guard():
        _need(time.perf_counter() - started < limits.max_seconds, 'context preparation deadline')
    guard(); phase.assert_integrity(); encoding.assert_integrity(); condition.assert_integrity()
    sources = source_inventory(); phase_id = phase.identity; encoding_id = encoding.identity
    bank = phase.shards[0].bank
    train80 = condition.train80
    _need(phase.shards[0].plan.identity == train80.plan_sha256
          and identity_hash(bank.identity) == train80.domain_sha256, 'condition phase plan/bank mismatch')
    # Existing data validator checks all role/encoding/freeze geometry invariants.
    data._check_pair(phase, encoding, False)
    optimization_shards = {'select_train80': (('train', train80.train_shard_sha256),),
        'refit_union90': (('train', train80.train_shard_sha256), ('selection', train80.selection_shard_sha256))}
    _need(encoding.origin_shard_sha256 == optimization_shards[encoding.optimization_scope], 'encoding original train/selection lineage mismatch')
    neural_binding = conditions.bind_graph_neural_phase(condition, phase_scope=phase.scope,
        encoding_sha256=encoding_id, vocabulary_sha256=identity_hash(list(encoding.exercise_encoding().vocabulary.values)),
        fit80_encoding_sha256=fit80_encoding_sha256, encoding_fit_scope=encoding.optimization_scope,
        neural_shards_sha256=tuple(sorted((s.role, s.audit['audit']['shard_sha256']) for s in phase.shards)),
        selection_freeze_sha256=None if phase.selection_freeze is None else phase.selection_freeze.identity)
    vocabulary = encoding.exercise_encoding().vocabulary.values
    graph = PrerequisiteGraph.from_edges(condition.nodes, condition.edges)
    confidence = EdgeConfidence(**condition.kernel_confidence_kwargs())
    _need(identity_hash(asdict(graph)) == condition.graph_sha256, 'graph canonical identity mismatch')
    trajectories = {trajectory.learner_id: trajectory for trajectory in phase.trajectories}
    total = sum(len(t.observations) for t in trajectories.values())
    _need(total <= limits.max_total_events and total <= limits.max_targets
          and all(len(t.observations) <= limits.max_events_per_learner for t in trajectories.values()),
          'phase events/targets exceed context limits')
    windows, unsupported, seen = [], [], set()
    parent_count, observed_count, cache_size = 0, 0, 0
    stream = data.iter_research_windows(phase, encoding, context=context, target_block=target_block, training=False)
    try:
        for window in stream:
            guard()
            if type(window) is data.ResearchUnseenTarget:
                key = (window.learner_id, window.query.source_row, window.global_rank)
                _need(window.learner_id in trajectories and type(window.global_rank) is int
                      and 0 <= window.global_rank < len(trajectories[window.learner_id].observations), 'OOV learner/rank mismatch')
                _need(key not in seen and window.phase_sha256 == phase_id
                      and window.query == trajectories[window.learner_id].observations[window.global_rank].query
                      and window.query.item_id not in vocabulary, 'duplicate/foreign OOV target')
                seen.add(key)
                record = ResearchGraphUnsupportedTarget(window.learner_id, window.query, window.global_rank, window.support_reason)
                unsupported.append(record)
                cache_size += len(json.dumps(asdict(record), allow_nan=False).encode())
            else:
                payload = _window_payload(window, limits.max_window_tokens)
                _need(len(windows) < limits.max_windows, 'window count cap')
                learner = window.inputs.user_ids[0]
                _need(learner in trajectories, 'foreign learner window')
                observations = trajectories[learner].observations
                records = [None] * len(window.inputs.item_ids)
                for local in np.flatnonzero(window.target_mask):
                    guard(); local = int(local)
                    rank = int(window.global_ranks[local]); source_row = int(window.inputs.source_rows[local])
                    _need(0 <= rank < len(observations), 'global target rank outside learner')
                    query = observations[rank].query
                    key = learner, source_row, rank
                    _need(key not in seen and query.source_row == source_row
                          and query.timestamp == int(window.inputs.timestamps[local])
                          and query.item_id == vocabulary[int(window.inputs.item_ids[local])], 'query/source/encoding alignment mismatch')
                    seen.add(key)
                    audit = audit_graph_context(bank=bank, graph=graph, confidence=confidence,
                        history=observations[:rank], query=query, trained_items=vocabulary,
                        context=context, target_block=target_block)
                    expected_start = rank - int(window.history_used[local])
                    _need(audit['target_fitted'] and audit['information_matched']
                          and audit['effective_start'] == expected_start
                          and tuple(audit['observed_rows']) == tuple(int(r) for r in window.inputs.source_rows[:local]),
                          'graph/native effective past mismatch')
                    parents = tuple(ResearchParentEvidence(**p) for p in audit['parents'])
                    evidence = ResearchGraphAudit(audit['domain_sha256'], audit['trained_items_sha256'], query,
                        parents, tuple(audit['observed_rows']), audit['effective_start'], audit['graph_sha256'],
                        audit['confidence_sha256'], confidence.kind, audit['scoped_observations_sha256'], audit['target_fitted'])
                    records[local] = ResearchGraphQueryEvidence(learner, source_row, rank, window.window_id, local, evidence)
                    parent_count += len(parents); observed_count += len(evidence.observed_rows)
                    _need(parent_count <= limits.max_parent_records and observed_count <= limits.max_observed_rows,
                          'parent/observed context record cap')
                record = ResearchGraphIndexedWindow(window.window_id, learner, identity_hash(payload), tuple(records))
                windows.append(record)
                cache_size += len(json.dumps(asdict(record), allow_nan=False).encode())
            _need(len(seen) <= limits.max_targets and cache_size <= limits.max_cache_bytes, 'context cache target/byte cap')
    finally:
        stream.close()
    expected = {(t.learner_id, o.query.source_row, rank) for t in trajectories.values()
                for rank, o in enumerate(t.observations)}
    _need(seen == expected and len({w.window_id for w in windows}) == len(windows), 'full target/window population mismatch')
    phase.assert_integrity(); encoding.assert_integrity(); condition.assert_integrity()
    _need(phase.identity == phase_id and encoding.identity == encoding_id and source_inventory() == sources,
          'context source/phase drift during preparation')
    result = object.__new__(ResearchGraphContextIndex)
    values = dict(condition_sha256=condition.identity, phase_sha256=phase_id, encoding_sha256=encoding_id,
        vocabulary_sha256=neural_binding.vocabulary_sha256, neural_binding=neural_binding, sources_sha256=sources,
        context=context, target_block=target_block, windows=tuple(windows), unsupported_targets=tuple(unsupported),
        full_targets=len(seen), limits=limits, role=ROLE, content_sha256='')
    for name, value in values.items():
        object.__setattr__(result, name, value)
    payload = result._payload()
    _need(len(json.dumps(payload, sort_keys=True, allow_nan=False).encode()) <= limits.max_cache_bytes, 'final context cache byte cap')
    object.__setattr__(result, 'content_sha256', identity_hash(payload))
    guard()
    return result
