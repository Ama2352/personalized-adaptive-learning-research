"""Candidate dữ liệu GKT concept28, không model, fitted role hoặc quyền chạy.

Bank84 là registry công khai. Vocabulary chỉ lấy từ optimization phase. Prefix
đầy đủ là observable past, khác history hash có model binding của OnlineSession.
Graph expert giữ lineage train80 khi encoding neural chuyển sang refit90.
"""
from dataclasses import InitVar, asdict, dataclass, field
import hashlib
from pathlib import Path

from knowledge_tracing.akt.research_simulator_data import (
    OPTIMIZATION_SCOPES, SCOPES, ResearchAKTEncoding, ResearchAKTShard,
    ResearchPhaseData, fit_research_encoding, prepare_research_phase,
    research_scoring_targets, source_identity as phase_sources,
)
from knowledge_tracing.simulator_bridge import ItemQuery, identity_hash
from knowledge_tracing.simulator_corpus_reader import PublicResearchCorpus
from knowledge_tracing import simulator_corpus_reader as public_reader


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _sha(value):
    _need(type(value) is str and len(value) == 64
          and all(c in '0123456789abcdef' for c in value), 'SHA256 lowercase required')


def source_identity():
    # Candidate giữ canonical logical name; byte-copy sang module mới không đổi SHA.
    return tuple(sorted((*phase_sources(),
        ('simulator_corpus_reader.py', hashlib.sha256(Path(public_reader.__file__).read_bytes()).hexdigest()),
        ('gkt/research_data.py', hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))))


@dataclass(frozen=True)
class GKTResearchDataRecipe:
    node_unit: str
    history_policy: str
    first_target_policy: str
    oov_policy: str

    def __post_init__(self):
        _need((self.node_unit, self.history_policy, self.first_target_policy, self.oov_policy)
              == ('concept', 'full_prefix', 'query_only', 'unsupported_history'),
              'Protocol21 concept/full-prefix/query-only/unsupported-history required')


@dataclass(frozen=True)
class GKTResearchGraphBinding:
    """Caller-pinned expert topology metadata, không kiểm file hay fit attestation."""
    domain_sha256: str
    node_ids: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    topology_file_sha256: str
    train80_shard_sha256: str
    graph_kind: str

    def __post_init__(self):
        for value in (self.domain_sha256, self.topology_file_sha256, self.train80_shard_sha256):
            _sha(value)
        _need(self.graph_kind == 'declared_static_expert', 'Only declared static expert topology')
        _need(type(self.node_ids) is tuple and len(self.node_ids) == 28
              and all(type(node) is str and bool(node) for node in self.node_ids)
              and self.node_ids == tuple(sorted(set(self.node_ids))), 'Exact sorted concept28 nodes')
        _need(type(self.edges) is tuple and len(self.edges) <= 28*27
              and all(type(edge) is tuple and len(edge) == 2
                      and all(type(node) is str and node in self.node_ids for node in edge)
                      and edge[0] != edge[1] for edge in self.edges), 'Bounded declared edges')
        _need(len(set(self.edges)) == len(self.edges) and self.edges == tuple(sorted(self.edges)),
              'Unique canonical edges')
        pending = set(self.node_ids)
        while pending:
            roots = {node for node in pending
                     if not any(child == node and parent in pending for parent, child in self.edges)}
            _need(bool(roots), 'Expert graph must be acyclic')
            pending.difference_update(roots)

    @property
    def identity(self):
        self.__post_init__()
        return identity_hash(asdict(self))


@dataclass(frozen=True)
class GKTResearchInputLimits:
    max_targets: int
    max_prefix_events: int

    def __post_init__(self):
        _need(type(self.max_targets) is int and 0 < self.max_targets < 2**63
              and type(self.max_prefix_events) is int and 0 <= self.max_prefix_events < 2**63,
              'Explicit total target and expanded-prefix limits required')


@dataclass(frozen=True)
class GKTResearchView:
    corpus: InitVar[PublicResearchCorpus]
    phase: ResearchPhaseData
    encoding: ResearchAKTEncoding
    recipe: GKTResearchDataRecipe
    graph: GKTResearchGraphBinding
    corpus_sha256: str = field(init=False)
    item_node_registry: tuple[tuple[str, str], ...] = field(init=False)
    train_item_node_map: tuple[tuple[str, int], ...] = field(init=False)
    sources_sha256: tuple = field(init=False, repr=False)
    content_sha256: str = field(init=False)

    def __post_init__(self, corpus):
        _need(type(corpus) is PublicResearchCorpus and type(self.phase) is ResearchPhaseData
              and type(self.encoding) is ResearchAKTEncoding
              and type(self.recipe) is GKTResearchDataRecipe
              and type(self.graph) is GKTResearchGraphBinding, 'Exact public data types required')
        corpus.assert_integrity()
        self.recipe.__post_init__()
        self.graph.identity
        for shard in self.phase.shards:
            public = corpus.role_data(shard.role)
            _need(shard.plan == corpus.plan and shard.bank == corpus.bank
                  and shard.trajectories == public.trajectories and shard.provenance == public.provenance
                  and shard.expected_provenance_sha256 == public.provenance.identity
                  and shard.limits == corpus.limits.shard_limits
                  and identity_hash(shard.audit) == identity_hash(public.audit), 'Public role binding mismatch')
        # Validator public kiểm scope↔encoding, refit freeze và canonical target hashes.
        research_scoring_targets(self.phase, self.encoding)
        registry = tuple(sorted((item.item_id, item.concept_id) for item in corpus.bank.items))
        nodes = tuple(sorted({node for _, node in registry}))
        _need(len(registry) == len(set(item for item, _ in registry)) == 84
              and nodes == self.graph.node_ids
              and all(tuple(sorted(item.difficulty for item in corpus.bank.items if item.concept_id == node))
                      == (1050, 1200, 1350) for node in nodes),
              'Exact public84 items mapped three-to-one onto concept28 required')
        _need(self.graph.domain_sha256 == identity_hash(corpus.bank.identity)
              and self.graph.train80_shard_sha256 == corpus.role_data('train').audit['audit']['shard_sha256'],
              'Graph domain and frozen TRAIN80 role mismatch')
        observed = self.encoding.exercise_encoding().vocabulary.values
        lookup = dict(registry)
        object.__setattr__(self, 'corpus_sha256', corpus.identity)
        object.__setattr__(self, 'item_node_registry', registry)
        object.__setattr__(self, 'train_item_node_map', tuple((item, nodes.index(lookup[item])) for item in observed))
        object.__setattr__(self, 'sources_sha256', source_identity())
        object.__setattr__(self, 'content_sha256', identity_hash(self._payload()))

    def _payload(self):
        return dict(model='gkt', role='research_data_only_no_fit_attestation', corpus_sha256=self.corpus_sha256,
            phase_sha256=self.phase.identity, encoding_sha256=self.encoding.identity,
            recipe=asdict(self.recipe), graph_sha256=self.graph.identity,
            item_node_registry=self.item_node_registry, train_item_node_map=self.train_item_node_map,
            sources_sha256=self.sources_sha256)

    def assert_integrity(self):
        _need(self.sources_sha256 == source_identity()
              and self.content_sha256 == identity_hash(self._payload()), 'GKT data/source/lineage changed')

    @property
    def identity(self):
        self.assert_integrity()
        return self.content_sha256


def prepare_gkt_research_view(corpus, *, scope, recipe, graph_binding, encoding=None, selection_freeze=None):
    """Public phase construction, không disk reader, neural allocation hoặc fake role."""
    _need(type(corpus) is PublicResearchCorpus and type(scope) is str and scope in SCOPES,
          'Typed public corpus and declared research scope required')
    corpus.assert_integrity()
    shards = []
    for role in SCOPES[scope]:
        data = corpus.role_data(role)
        shards.append(ResearchAKTShard(corpus.plan, corpus.bank, role, data.trajectories,
            data.provenance, data.provenance.identity, corpus.limits.shard_limits))
    phase = prepare_research_phase(scope, shards=tuple(shards), selection_freeze=selection_freeze)
    if encoding is None:
        _need(scope in OPTIMIZATION_SCOPES, 'Prediction needs optimization encoding')
        encoding = fit_research_encoding(phase)
    return GKTResearchView(corpus, phase, encoding, recipe, graph_binding)


@dataclass(frozen=True)
class GKTResearchInput:
    learner_id: str
    query: ItemQuery
    global_rank: int
    origin_role: str
    phase_scope: str
    phase_sha256: str
    encoding_sha256: str
    graph_sha256: str
    history_sha256: str
    history_hash_scheme: str
    support_reason: str
    query_node_id: int | None
    history_available: int
    history_used: int
    past_queries: tuple[ItemQuery, ...] | None
    past_node_ids: tuple[int, ...] | None
    past_responses: tuple[int, ...] | None

    @property
    def eligible(self):
        return self.support_reason in ('cold_query_only', 'known_history')


@dataclass(frozen=True)
class GKTResearchTrainingTarget:
    inputs: GKTResearchInput
    target: int  # Chỉ loss wrapper, không nằm trong predictor inputs.


def gkt_research_scoring_targets(view):
    _need(type(view) is GKTResearchView, 'Typed GKT view required')
    view.assert_integrity()
    result = research_scoring_targets(view.phase, view.encoding)
    view.assert_integrity()
    return result


def iter_gkt_research_inputs(view, *, training, limits):
    """Mọi target kể cả null. Full-prefix không reset rồi âm thầm cứu OOV suffix.

    Expanded prefix là chi phí quadratic được giới hạn trước first yield. Đây
    là representation dữ liệu; tối ưu incremental state thuộc model runner sau.
    """
    _need(type(view) is GKTResearchView and type(training) is bool
          and type(limits) is GKTResearchInputLimits, 'Typed view/training flag/limits required')
    _need(not training or view.phase.scope in OPTIMIZATION_SCOPES, 'Prediction role cannot train')
    limits.__post_init__()
    view.assert_integrity()
    trajectories = view.phase.trajectories
    count = sum(len(t.observations) for t in trajectories)
    expanded = sum(len(t.observations)*(len(t.observations)-1)//2 for t in trajectories)
    _need(count <= limits.max_targets and expanded <= limits.max_prefix_events, 'Whole population exceeds input limits')
    truth = iter(gkt_research_scoring_targets(view))
    mapping = dict(view.train_item_node_map)
    role_by_learner = {t.learner_id: shard.role for shard in view.phase.shards for t in shard.trajectories}
    phase_id, encoding_id, graph_id = view.phase.identity, view.encoding.identity, view.graph.identity
    seen = set()
    for trajectory in trajectories:
        past_queries, past_nodes, past_labels = [], [], []
        unsupported_history = False
        for rank, observation in enumerate(trajectory.observations):
            target = next(truth)
            key = (trajectory.learner_id, observation.query.source_row, rank)
            _need(key not in seen and key == (target.learner_id, target.query.source_row, target.global_rank)
                  and target.query == observation.query and target.correct == observation.correct
                  and target.origin_role == role_by_learner[trajectory.learner_id], 'Canonical target population mismatch')
            seen.add(key)
            node = mapping.get(observation.query.item_id)
            reason = ('oov_item' if node is None else 'unsupported_history' if unsupported_history
                      else 'known_history' if rank else 'cold_query_only')
            supported = reason in ('known_history', 'cold_query_only')
            record = GKTResearchInput(trajectory.learner_id, observation.query, rank, target.origin_role,
                view.phase.scope, phase_id, encoding_id, graph_id, target.history_sha256, target.history_hash_scheme,
                reason, node if supported else None, rank, rank if supported else 0,
                tuple(past_queries) if supported else None, tuple(past_nodes) if supported else None,
                tuple(past_labels) if supported else None)
            yield GKTResearchTrainingTarget(record, target.correct) if training else record
            # Current label/query chỉ trở thành past sau record hiện tại.
            unsupported_history = unsupported_history or node is None
            past_queries.append(observation.query)
            past_nodes.append(node)
            past_labels.append(observation.correct)
    _need(next(truth, None) is None and len(seen) == count, 'Complete target coverage required')
    view.assert_integrity()
