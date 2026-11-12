"""Condition A1 Junyi và evidence từ đúng prefix của native window.

Chưa có estimator confidence Junyi hoặc quyền training. Không nhận labels hiện
tại, full learner history, SimulatorBank hoặc nhãn cạnh đúng/sai.
"""
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType

import numpy as np

from ..edge_confidence_artifact import _acyclic
from ..shared_kt import PrerequisiteGraph
from .research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from .types import WindowInputs


def _need(value, message):
    if not value:
        raise ValueError(message)


def _identity(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class JunyiGraphCondition:
    encoding: JunyiResearchEncoding = field(repr=False)
    graph: PrerequisiteGraph
    topology_source_sha256: str
    variant: str = 'A1'
    graph_mode: str = 'expert_declared'
    content_sha256: str = field(init=False)

    def __post_init__(self):
        _need(self.variant == 'A1' and self.graph_mode == 'expert_declared',
              'Only A1 expert is supported; fitted Junyi confidence binding is pending')
        _need(type(self.encoding) is JunyiResearchEncoding
              and self.encoding.fit_view.scope == 'select_train80', 'TRAIN80 Junyi encoding required')
        self.encoding.assert_for(self.encoding.fit_view)
        _need(type(self.topology_source_sha256) is str and len(self.topology_source_sha256) == 64
              and all(c in '0123456789abcdef' for c in self.topology_source_sha256),
              'Pinned topology SHA256 required')
        _need(type(self.graph) is PrerequisiteGraph and self.graph.edge_direction == 'prerequisite_to_dependent',
              'Typed prerequisite-to-dependent graph required')
        nodes, edges = self.graph.nodes, self.graph.edges
        _need(type(nodes) is tuple and nodes and all(type(n) is str and n for n in nodes)
              and nodes == tuple(sorted(set(nodes))), 'Unique canonical graph nodes required')
        _need(type(edges) is tuple and all(type(e) is tuple and len(e) == 2
              and all(type(n) is str for n in e) for e in edges), 'Typed graph edge pairs required')
        _need(edges == tuple(sorted(set(edges))), 'Duplicate/noncanonical graph edges')
        canonical = PrerequisiteGraph.from_edges(nodes, edges)
        _need(canonical == self.graph and _acyclic(nodes, edges), 'Canonical acyclic graph required')
        _need(set(self.encoding.native.vocabulary.values) <= set(nodes),
              'Fitted vocabulary exercise missing from graph nodes')
        object.__setattr__(self, 'content_sha256', _identity(self._payload()))

    def _payload(self):
        return dict(variant=self.variant, graph_mode=self.graph_mode, nodes=self.graph.nodes,
            edges=self.graph.edges, direction=self.graph.edge_direction,
            topology_source_sha256=self.topology_source_sha256, encoding=self.encoding.identity,
            train_view=self.encoding.fit_view.identity, roles=self.encoding.fit_view.roles.identity,
            confidence='fixed_uniform_one', history='effective_native_window_prefix',
            graph_pruning='none', role='junyi_condition_only_not_fitted_weights')

    def assert_integrity(self):
        self.encoding.assert_for(self.encoding.fit_view)
        _need(self.content_sha256 == _identity(self._payload()), 'Junyi graph condition changed')

    @property
    def identity(self):
        self.assert_integrity()
        return self.content_sha256


@dataclass(frozen=True)
class JunyiParentEvidence:
    parent: str
    support: int
    confidence: float
    mean_observed_correctness: float | None


@dataclass(frozen=True)
class JunyiGraphAudit:
    target_fitted: bool
    parents: tuple[JunyiParentEvidence, ...]
    observed_rows: tuple[int, ...]
    effective_start: int
    condition_sha256: str
    encoding_sha256: str


@dataclass(frozen=True)
class JunyiGraphQueryEvidence:
    learner_id: str
    source_row: int
    global_rank: int
    window_id: str
    local_position: int
    audit: JunyiGraphAudit


_ROLE_GROUPS = ('train_users', 'selection_users', 'calibration_users', 'outer_validation_users')


def _role_header(roles):
    return (roles.outer_fold, roles.seed, roles.algorithm, roles.rounding,
            *(id(getattr(roles, name)) for name in _ROLE_GROUPS))


def _view_header(view):
    return (id(view.roles), id(view.users), view.scope, view.identity, view.expected_roles_identity)


def _condition_header(condition):
    return (id(condition.encoding), id(condition.graph), id(condition.graph.nodes),
            id(condition.graph.edges), condition.graph.edge_direction, condition.variant,
            condition.graph_mode, condition.topology_source_sha256, condition.content_sha256)


@dataclass(frozen=True)
class JunyiGraphPhaseSession:
    """Kiểm full ở attach/boundary, giữ header bất biến và support hash khi dùng.

Caller tạo một session cho phase, dùng lại cho mọi window, rồi gọi
assert_boundary trước khi đóng phase. Các tuple frozen được giữ tham chiếu để
header kiểm O(1), không hash lại gần198nghìn learner IDs mỗi window.
"""
    condition: JunyiGraphCondition
    view: JunyiPhaseView
    _headers: tuple = field(init=False, repr=False)
    _roots: tuple = field(init=False, repr=False)
    _allowed_users: frozenset = field(init=False, repr=False)
    _parents_by_child: object = field(init=False, repr=False)
    _encoding_identity: str = field(init=False, repr=False)
    _condition_identity: str = field(init=False, repr=False)

    def __post_init__(self):
        _need(type(self.condition) is JunyiGraphCondition and type(self.view) is JunyiPhaseView,
              'Typed Junyi condition and phase required')
        self._full_check()
        fit_view = self.condition.encoding.fit_view
        roles = (fit_view.roles, self.view.roles)
        roots = (self.condition.encoding, fit_view, self.condition.graph,
                 self.condition.graph.nodes, self.condition.graph.edges,
                 fit_view.users, self.view.users, *roles,
                 *(getattr(role, name) for role in roles for name in _ROLE_GROUPS))
        object.__setattr__(self, '_roots', roots)
        object.__setattr__(self, '_headers', self._current_headers())
        object.__setattr__(self, '_allowed_users', frozenset(self.view.users))
        parents = {}
        for parent, child in self.condition.graph.edges:
            parents.setdefault(child, []).append(parent)
        object.__setattr__(self, '_parents_by_child', MappingProxyType(
            {child: tuple(values) for child, values in parents.items()}))
        object.__setattr__(self, '_encoding_identity', self.condition.encoding.identity)
        object.__setattr__(self, '_condition_identity', self.condition.content_sha256)

    def _current_headers(self):
        fit_view = self.condition.encoding.fit_view
        return (_condition_header(self.condition), _view_header(fit_view), _view_header(self.view),
                _role_header(fit_view.roles), _role_header(self.view.roles))

    def _full_check(self):
        self.condition.assert_integrity()
        self.condition.encoding.assert_for(self.view)
        for view in (self.condition.encoding.fit_view, self.view):
            role_sha = view.roles.identity
            _need(role_sha == view.expected_roles_identity and view.identity == _identity(
                dict(roles=role_sha, scope=view.scope, users=view.users)), 'Phase roles/content changed')

    def _light_check(self):
        _need(self._current_headers() == self._headers, 'Bound Junyi graph phase header changed')
        encoding = self.condition.encoding
        _need(encoding.identity == self._encoding_identity == _identity(encoding._payload()),
              'Bound Junyi encoding content changed')

    def assert_boundary(self):
        self._light_check()
        self._full_check()

    def prefix_evidence(self, window):
        self._light_check()
        _validate_window(window, self)
        result = _prefix_evidence(window, vocabulary=self.condition.encoding.native.vocabulary.values,
            parents_by_child=self._parents_by_child, condition_sha=self._condition_identity,
            encoding_sha=self._encoding_identity)
        self._light_check()
        return result


def _validate_window(window, session):
    _need(type(window) is WindowInputs, 'Typed native window required')
    inputs = window.inputs
    ids = inputs.item_ids
    size = len(ids)
    _need(1 <= size <= 200 and len(inputs.user_ids) == size
          and len(set(inputs.user_ids)) == 1 and inputs.user_ids[0] in session._allowed_users,
          'Bounded single-learner phase window required')
    arrays = (ids, inputs.timestamps, inputs.prior_responses, inputs.source_rows,
              window.global_ranks, window.history_used, window.history_available)
    _need(all(type(a) is np.ndarray and a.shape == (size,) and np.issubdtype(a.dtype, np.integer)
              for a in arrays), 'Integer window arrays must align')
    _need(np.array_equal(inputs.sequence_offsets, [0, size]), 'Single native sequence required')
    _need(np.all((ids >= 0) & (ids < len(session.condition.encoding.native.vocabulary.values))),
          'OOV or invalid item cannot enter graph model window')
    _need(inputs.prior_responses[0] == -1 and np.isin(inputs.prior_responses[1:], (0, 1)).all(),
          'Valid shifted prior responses required')
    _need(np.all(inputs.source_rows > 0) and len(set(inputs.source_rows.tolist())) == size
          and np.all(inputs.timestamps >= 0), 'Unique positive source rows and timestamps required')
    chronology = tuple(zip(inputs.timestamps.tolist(), inputs.source_rows.tolist()))
    _need(all(a < b for a, b in zip(chronology, chronology[1:])), 'Canonical chronological window required')
    _need(np.all(window.global_ranks >= 0) and np.all(np.diff(window.global_ranks) == 1)
          and np.array_equal(window.history_used, np.arange(size))
          and np.all(window.history_available >= window.history_used), 'Native rank/history geometry required')
    mask = window.target_mask
    _need(type(mask) is np.ndarray and mask.shape == (size,) and mask.dtype == np.bool_
          and mask.any() and np.all(mask[np.flatnonzero(mask)[0]:]), 'Native suffix target mask required')
    _need(type(window.window_id) is str and bool(window.window_id), 'Native window identity required')


def junyi_prefix_evidence(window, *, condition, view):
    """API đơn giản cho bounded call; production dùng session một lần/phase."""
    return JunyiGraphPhaseSession(condition, view).prefix_evidence(window)


def _prefix_evidence(window, *, vocabulary, parents_by_child, condition_sha, encoding_sha):
    """Trả một tuple cho native.bind; context positions giữ None.

Tại vị trí j, câu trả lời của item j-1 nằm ở prior_responses[j]. Cập nhật
đúng item quá khứ trước khi dựng evidence của j. Không đọc response của j.
"""
    counts, successes = {}, {}
    result = []
    for local, item_id in enumerate(window.inputs.item_ids):
        if local:
            previous = vocabulary[int(window.inputs.item_ids[local-1])]
            counts[previous] = counts.get(previous, 0)+1
            successes[previous] = successes.get(previous, 0)+int(window.inputs.prior_responses[local])
        evidence = None
        if window.target_mask[local]:
            parents = tuple(JunyiParentEvidence(parent, counts.get(parent, 0), 1.,
                successes[parent]/counts[parent] if counts.get(parent, 0) else None)
                for parent in parents_by_child.get(vocabulary[int(item_id)], ()))
            audit = JunyiGraphAudit(True, parents,
                tuple(int(row) for row in window.inputs.source_rows[:local]),
                int(window.global_ranks[0]), condition_sha, encoding_sha)
            evidence = JunyiGraphQueryEvidence(window.inputs.user_ids[0],
                int(window.inputs.source_rows[local]), int(window.global_ranks[local]),
                window.window_id, local, audit)
        result.append(evidence)
    return tuple(result)
