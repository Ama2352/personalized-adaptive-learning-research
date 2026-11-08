"""Condition dữ liệu recipe26; không model, parser artifact hay quyền execution.

Caller dùng loader Method24 đã nghiệm thu và cấp external pins. Typed objects,
SHA và role ở đây là consistency contract hợp tác, không chứng thực chống caller
giả toàn metadata. Không mở corpus/artifact/oracle hoặc import NumPy/Torch.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import hashlib
import math
from pathlib import Path

from ..edge_confidence_artifact import (LoadedEdgePredictiveScore, LoadedMethod24Scores,
                                      Method24TrainingBinding, SEMANTICS, _acyclic)
from ..simulator_bridge import SimulatorBank, identity_hash

ROOT = Path(__file__).resolve().parents[3]
RECIPE = 'cgakt-centered-parentmean-scalar-v1'
RECIPE_PATH = 'docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md'
RECIPE_SHA256 = '13a81ad6a5173e1f215e3df01f3917fcbc1cce128c87c93985b57af76faa353a'
ROLE = 'research_graph_condition_only_not_fitted_weights'
GATE_FEATURES = ('observed_support_over_one_plus_support', 'all_parent_confidence_mean',
                 'all_parent_confidence_population_variance', 'observed_parent_fraction')
SOURCE_PATHS = tuple(sorted((RECIPE_PATH, 'src/knowledge_tracing/akt/research_graph_condition.py',
    'src/knowledge_tracing/edge_confidence_artifact.py', 'src/knowledge_tracing/graph_context.py',
    'src/knowledge_tracing/graph_augmentation.py', 'src/knowledge_tracing/shared_kt.py',
    'src/knowledge_tracing/simulator_bridge.py', 'src/knowledge_tracing/akt/windows.py')))


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _sha(value):
    _need(type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'SHA256 required')


def _text(value):
    _need(type(value) is str and bool(value.strip()), 'nonempty identifier required')


def _rows(value):
    _need(type(value) is tuple and all(type(r) is tuple and len(r) == 2 for r in value), 'immutable hash rows required')
    for name, digest in value:
        _text(name); _sha(digest)
    _need(value == tuple(sorted(value)) and len(dict(value)) == len(value), 'unique canonical hash rows required')
    return dict(value)


def source_inventory():
    """Chỉ các source paths cố định; không theo arbitrary path trong metadata."""
    alias = lambda p: p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
    _need(ROOT.is_dir() and not alias(ROOT) and ROOT.resolve() == ROOT.absolute(), 'physical source root required')
    result = []
    for relative in SOURCE_PATHS:
        path = ROOT
        for part in relative.split('/'):
            path /= part
            _need(not alias(path), 'source alias rejected')
        _need(path.is_file() and path.stat().st_size <= 262144, 'bounded regular source required')
        raw = path.read_bytes()
        _need(len(raw) <= 262144, 'source byte cap')
        result.append((relative, hashlib.sha256(raw).hexdigest()))
    result = tuple(result)
    _need(dict(result)[RECIPE_PATH] == RECIPE_SHA256, 'adopted recipe26 source drift')
    return result


@dataclass(frozen=True)
class GraphTrain80Binding:
    """Lineage do entry đã audit public corpus cung cấp; không training authority."""
    corpus_id: str
    corpus_sha256: str
    corpus_done_sha256: str
    plan_sha256: str
    train_provenance_sha256: str
    train_observable_sha256: str
    domain_sha256: str
    train_shard_sha256: str
    selection_shard_sha256: str
    calibration_shard_sha256: str
    fit_scope: str = 'train80'

    def __post_init__(self):
        _text(self.corpus_id)
        for name, value in asdict(self).items():
            if name.endswith('sha256'):
                _sha(value)
        _need(self.fit_scope == 'train80', 'graph/confidence must stay train80')

    @property
    def identity(self):
        return identity_hash(asdict(self))


@dataclass(frozen=True)
class OperationalEdgeWeight:
    parent_id: str
    child_id: str
    supported: bool
    source_score: float | None
    unsupported_reason: str | None
    operational_weight: float

    def __post_init__(self):
        _text(self.parent_id); _text(self.child_id)
        _need(self.parent_id != self.child_id and type(self.supported) is bool, 'edge flag/endpoints')
        _need(type(self.operational_weight) is float and math.isfinite(self.operational_weight)
              and 0 <= self.operational_weight <= 1, 'operational weight range')
        if self.supported:
            _need(type(self.source_score) in (int, float) and math.isfinite(self.source_score)
                  and 0 <= self.source_score <= 1 and self.unsupported_reason is None
                  and self.operational_weight == self.source_score, 'supported score/weight mismatch')
        else:
            _text(self.unsupported_reason)
            _need(self.source_score is None and self.operational_weight == 0., 'unsupported must keep null plus operational zero')


@dataclass(frozen=True, init=False)
class ResearchGraphCondition:
    variant: str
    graph_mode: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    graph_sha256: str
    topology_source_sha256: str | None
    train80: GraphTrain80Binding
    edge_weights: tuple[OperationalEdgeWeight, ...]
    confidence_kind: str
    confidence_semantics: str
    method24_scores: LoadedMethod24Scores | None
    sources_sha256: tuple[tuple[str, str], ...]
    recipe: str = RECIPE
    recipe_sha256: str = RECIPE_SHA256
    role: str = ROLE
    history_scope: str = 'effective_native_window'
    graph_confidence_refit_policy: str = 'frozen_train80_through_neural_refit90'
    content_sha256: str = field(default='', repr=False)

    def __init__(self, *args, **kwargs):
        raise TypeError('use prepare_research_graph_condition')

    def _payload(self):
        return {name: value for name, value in asdict(self).items() if name != 'content_sha256'}

    def assert_integrity(self):
        _need(self.content_sha256 == identity_hash(self._payload()), 'condition payload drift')
        _need(self.sources_sha256 == source_inventory(), 'condition source drift')

    @property
    def identity(self):
        self.assert_integrity()
        return self.content_sha256

    def kernel_confidence_kwargs(self):
        """Dữ liệu cho EdgeConfidence, không import/instantiate legacy class.

        estimated_probability chỉ là tên enum kỹ thuật legacy. Semantics thật và
        null/support flags ở condition phải được checkpoint/model binding giữ lại.
        Không gọi đây là P(edge true); converter zero là quyết định recipe26.
        """
        self.assert_integrity()
        return dict(kind=self.confidence_kind,
            values=tuple((e.parent_id, e.child_id, e.operational_weight) for e in self.edge_weights),
            provenance_sha256=self.content_sha256,
            fitted_role='train' if self.confidence_kind == 'estimated_probability' else None)

    @property
    def architecture(self):
        """Recipe declarative, không module constructor/hyperparameter search."""
        self.assert_integrity()
        return dict(recipe=RECIPE, message='parent_past_correctness_mean_minus_0.5',
            normalizer='max(1,sum_confidence_on_observed_parents)', message_dimension=1,
            alpha_initial=None if self.variant == 'A0' else 0., alpha_signed=True,
            gate='sigmoid_linear_4_to_1' if self.variant == 'A3' else 'fixed_one',
            gate_features=GATE_FEATURES if self.variant == 'A3' else (),
            gate_weights_initial=(0., 0., 0., 0.) if self.variant == 'A3' else (),
            gate_bias_initial=0. if self.variant == 'A3' else None,
            bypass='graph_off_empty_or_zero_observed_mass_not_alpha_zero',
            system_fallback='independently_trained_A0_checkpoint')


def _topology(bank, nodes, edges):
    _need(type(bank) is SimulatorBank, 'typed bank required')
    concepts = tuple(sorted({item.concept_id for item in bank.items}))
    _need(type(nodes) is tuple and all(type(n) is str and n.strip() for n in nodes)
          and nodes == tuple(sorted(set(nodes))) and set(nodes) <= set(concepts), 'canonical bank concept nodes required')
    _need(type(edges) is tuple and all(type(e) is tuple and len(e) == 2 for e in edges), 'immutable graph edges required')
    _need(all(type(p) is str and type(c) is str and p in nodes and c in nodes and p != c for p, c in edges), 'graph endpoints')
    _need(edges == tuple(sorted(set(edges))), 'duplicate/noncanonical graph edges')
    _need(_acyclic(nodes, edges), 'cyclic research graph rejected')
    return identity_hash(dict(nodes=nodes, edges=edges, edge_direction='prerequisite_to_dependent'))


def _scores(loaded, expected, expected_sha, train80, nodes, edges, mode):
    _need(type(loaded) is LoadedMethod24Scores and type(expected) is Method24TrainingBinding, 'accepted typed Method24 loader data and external expectations required')
    replace(expected)  # Revalidate immutable expectation shape without file opens.
    _sha(expected_sha)
    _need(loaded.identity == expected_sha and loaded.training == expected, 'Method24 expected artifact/training identity mismatch')
    _need(loaded.score_semantics == SEMANTICS and loaded.fit_scope == 'train80'
          and loaded.oracle_inputs_used is False, 'nonoracle train80 predictive stability only')
    for key in ('corpus_id', 'corpus_sha256', 'corpus_done_sha256', 'plan_sha256',
                'train_provenance_sha256', 'train_observable_sha256', 'domain_sha256'):
        _need(getattr(expected, key) == getattr(train80, key), 'Method24 train80 lineage mismatch: ' + key)
    _need(loaded.declared_nodes == nodes and loaded.declared_edges == edges, 'Method24 declared graph mismatch')
    _need(loaded.graph_binding == ('method24_learned' if mode == 'method24_learned' else 'declared'), 'Method24 graph binding mode mismatch')
    _need(bool(_rows(loaded.artifacts_sha256)), 'accepted Method24 envelope bindings required')
    for digest in (loaded.prepared_sha256, loaded.producer_result_sha256, loaded.exported_graph_sha256):
        _sha(digest)
    _need(type(loaded.edge_scores) is tuple
          and all(type(e) is LoadedEdgePredictiveScore for e in loaded.edge_scores), 'typed edge summaries required')
    _need(tuple((e.parent_id, e.child_id) for e in loaded.edge_scores) == edges, 'missing/extra/duplicate edge scores')
    weights = []
    for edge in loaded.edge_scores:
        # Parser already checked fit/bootstrap denominators and whole envelope.
        # Here preserve supported0 versus unsupportednull and downstream mapping.
        weights.append(OperationalEdgeWeight(edge.parent_id, edge.child_id, edge.supported,
            edge.score, edge.reason, float(edge.score) if edge.supported and type(edge.score) in (int, float) else 0.))
        if mode == 'method24_learned':
            _need(edge.supported and type(edge.point_delta) in (int, float)
                  and math.isfinite(edge.point_delta) and edge.point_delta > 0, 'learned edges must be positive supported')
    if mode == 'method24_learned':
        _need(len(edges) == 31 and len(nodes) == 28, 'learned condition requires accepted28-node31-edge DAG')
    return tuple(weights)


def prepare_research_graph_condition(*, variant, graph_mode, bank, nodes, edges, train80,
        expected_sources, topology_source_sha256=None, loaded_scores=None,
        expected_method24_training=None, expected_scores_sha256=None, recipe=RECIPE):
    """Metadata-only admission/conversion; không đọc lại artifact đã được loader kiểm.

    A1 learned topology vẫn phải có Method24 accepted DAG nhưng weights uniform.
    Expert A1 không cần estimator. A0 không phụ thuộc Method24 hoặc graph artifact.
    """
    _need(variant in ('A0', 'A1', 'A2', 'A3') and recipe == RECIPE, 'adopted research variant/recipe required; no engineering/oracle tags')
    _need(graph_mode in ('none', 'expert_declared', 'method24_learned'), 'explicit graph mode required')
    _need(type(train80) is GraphTrain80Binding, 'typed train80 binding required')
    replace(train80)
    sources = source_inventory()
    _need(_rows(expected_sources) == dict(sources), 'external source pins mismatch')
    graph_sha = _topology(bank, nodes, edges)
    _need(train80.domain_sha256 == identity_hash(bank.identity), 'graph/bank domain binding mismatch')
    artifact_required = variant in ('A2', 'A3') or graph_mode == 'method24_learned'
    if variant == 'A0':
        _need(graph_mode == 'none' and nodes == edges == () and topology_source_sha256 is None, 'A0 must be graph free')
    else:
        _need(graph_mode != 'none' and bool(nodes), 'graph variant requires declared nodes/topology')
        _need(nodes == tuple(sorted({item.concept_id for item in bank.items})),
              'graph variants must preserve all bank concepts, including isolated nodes')
        _sha(topology_source_sha256)
    if artifact_required:
        weights = _scores(loaded_scores, expected_method24_training, expected_scores_sha256,
                          train80, nodes, edges, graph_mode)
        if graph_mode == 'method24_learned':
            _need(topology_source_sha256 == loaded_scores.exported_graph_sha256, 'learned graph source must bind exported artifact')
    else:
        _need(loaded_scores is expected_method24_training is expected_scores_sha256 is None, 'unexpected Method24 payload for graph-free/fixed expert condition')
        weights = ()
    if variant in ('A0', 'A1'):
        weights = tuple(OperationalEdgeWeight(p, c, True, 1., None, 1.) for p, c in edges)
    kind = 'estimated_probability' if variant in ('A2', 'A3') else 'fixed_uniform'
    result = object.__new__(ResearchGraphCondition)
    values = dict(variant=variant, graph_mode=graph_mode, nodes=nodes, edges=edges,
        graph_sha256=graph_sha, topology_source_sha256=topology_source_sha256, train80=train80,
        edge_weights=weights, confidence_kind=kind,
        confidence_semantics=SEMANTICS if variant in ('A2', 'A3') else 'fixed_uniform_declared_topology',
        method24_scores=loaded_scores, sources_sha256=sources, recipe=RECIPE, recipe_sha256=RECIPE_SHA256,
        role=ROLE, history_scope='effective_native_window',
        graph_confidence_refit_policy='frozen_train80_through_neural_refit90')
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, 'content_sha256', '')
    object.__setattr__(result, 'content_sha256', identity_hash(result._payload()))
    result.assert_integrity()
    return result


@dataclass(frozen=True)
class GraphNeuralPhaseBinding:
    condition_sha256: str
    phase_scope: str
    encoding_sha256: str
    vocabulary_sha256: str
    fit80_encoding_sha256: str
    encoding_fit_scope: str
    neural_shards_sha256: tuple[tuple[str, str], ...]
    selection_freeze_sha256: str | None
    graph_confidence_train80_sha256: str
    graph_confidence_refitted_on90: bool = False

    def __post_init__(self):
        for name in ('condition_sha256', 'encoding_sha256', 'vocabulary_sha256',
                     'fit80_encoding_sha256', 'graph_confidence_train80_sha256'):
            _sha(getattr(self, name))
        roles = {'select_train80': {'train'}, 'raw_selection10': {'selection'},
                 'refit_union90': {'train', 'selection'}, 'calibration_predict': {'calibration'}}
        _need(self.phase_scope in roles and set(_rows(self.neural_shards_sha256)) == roles[self.phase_scope],
              'neural phase/origin-role shape')
        _need(self.graph_confidence_refitted_on90 is False, 'graph/confidence stay train80')
        if self.phase_scope in ('refit_union90', 'calibration_predict'):
            _sha(self.selection_freeze_sha256)
            _need(self.encoding_fit_scope == 'refit_union90'
                  and self.encoding_sha256 != self.fit80_encoding_sha256, 'neural90 lineage required')
        else:
            _need(self.selection_freeze_sha256 is None and self.encoding_fit_scope == 'select_train80'
                  and self.encoding_sha256 == self.fit80_encoding_sha256, 'neural80 lineage required')

    @property
    def identity(self):
        return identity_hash(asdict(self))


def bind_graph_neural_phase(condition, *, phase_scope, encoding_sha256, vocabulary_sha256,
                           fit80_encoding_sha256, encoding_fit_scope,
                           neural_shards_sha256, selection_freeze_sha256=None):
    """Graph TRAIN80 cố định; neural encoding90 có identity riêng, không đổi role.

    SHA freeze chỉ bind metadata; entry vẫn phải kiểm external selector authority
    và toàn candidate allocation trước bất kỳ main refit/model constructor nào.
    """
    _need(type(condition) is ResearchGraphCondition, 'typed research condition required')
    condition.assert_integrity(); _sha(encoding_sha256); _sha(fit80_encoding_sha256); _sha(vocabulary_sha256)
    shards = _rows(neural_shards_sha256)
    t = condition.train80
    expected = {'select_train80': {'train': t.train_shard_sha256},
                'raw_selection10': {'selection': t.selection_shard_sha256},
                'refit_union90': {'train': t.train_shard_sha256, 'selection': t.selection_shard_sha256},
                'calibration_predict': {'calibration': t.calibration_shard_sha256}}
    _need(phase_scope in expected and shards == expected[phase_scope], 'exact phase/origin-role shard bindings required')
    if phase_scope in ('refit_union90', 'calibration_predict'):
        _sha(selection_freeze_sha256)
        _need(encoding_fit_scope == 'refit_union90' and encoding_sha256 != fit80_encoding_sha256,
              'refit/calibration require new neural90 encoding lineage, graph stays80')
    else:
        _need(selection_freeze_sha256 is None, 'selected-only phases must precede external freeze')
        _need(encoding_fit_scope == 'select_train80' and encoding_sha256 == fit80_encoding_sha256,
              'selected fit/selection must share train80 encoding')
    return GraphNeuralPhaseBinding(condition.identity, phase_scope, encoding_sha256, vocabulary_sha256,
        fit80_encoding_sha256, encoding_fit_scope,
        neural_shards_sha256, selection_freeze_sha256, t.identity)
