"""Factory Junyi-shaped toy: nguyên thuật toán nguồn, namespace/identity riêng.

Không dataset loader, global fit, CV, simulator policy hay fitted OnlineSession.
Hai flags native giữ nguyên: adaptation ghép cả parent và local pathways.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import sys
from types import MappingProxyType, ModuleType
from uuid import uuid4

import networkx as nx
import numpy as np
import pandas as pd

from .replay import predict_then_update

ROLE = 'synthetic_online_state_engineering_only'
SOURCE = Path(__file__).with_name('original_junyi.py')
MAX_SOURCE_BYTES = 65536
MAX_INTERACTIONS = 32
DIRECTION = 'prerequisite_to_dependent'


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _text(value):
    if type(value) is not str or not value.strip() or len(value) > 128:
        raise ValueError('nonempty bounded text identifier required')


def _sha(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('explicit lowercase SHA256 required')


def _source_payload():
    with SOURCE.open('rb') as stream:
        payload = stream.read(MAX_SOURCE_BYTES + 1)
    if not payload or len(payload) > MAX_SOURCE_BYTES:
        raise ValueError('native source exceeds bounded read')
    return payload


def native_source_sha256():
    """Hash module vendored hiện tại, không import model/global metadata của nó."""
    return hashlib.sha256(_source_payload()).hexdigest()


def _implementation_sources():
    paths = (SOURCE, Path(__file__), Path(__file__).with_name('replay.py'))
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def graph_sha256(*, domain, nodes, edges, direction):
    return _hash({'domain': domain, 'nodes': nodes, 'edges': edges, 'direction': direction})


@dataclass(frozen=True)
class GAMVariantRecipe:
    domain: str
    label: str
    graph_signal_enabled: bool
    graph_adaptation_enabled: bool
    graph_weight: float
    time_decay_rate: float
    source_sha256: str

    def __post_init__(self):
        _text(self.domain); _text(self.label); _sha(self.source_sha256)
        if not self.domain.startswith('synthetic-'):
            raise ValueError('explicit synthetic domain required')
        if type(self.graph_signal_enabled) is not bool or type(self.graph_adaptation_enabled) is not bool:
            raise ValueError('native pathway flags must be explicit booleans')
        for value in (self.graph_weight, self.time_decay_rate):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('finite nonnegative native recipe numbers required')


@dataclass(frozen=True)
class GAMGraphBinding:
    domain: str
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    direction: str
    origin: str
    provenance_id: str
    provenance_sha256: str
    graph_sha256: str

    def __post_init__(self):
        _text(self.domain); _text(self.provenance_id)
        _sha(self.provenance_sha256); _sha(self.graph_sha256)
        if (not self.domain.startswith('synthetic-') or self.direction != DIRECTION
                or self.origin != 'caller_declared_synthetic_fixture'
                or type(self.nodes) is not tuple or not 1 <= len(self.nodes) <= 16
                or any(type(node) is not str or not node.strip() or len(node) > 128 for node in self.nodes)
                or self.nodes != tuple(sorted(set(self.nodes)))
                or type(self.edges) is not tuple or len(self.edges) > 64
                or any(type(edge) is not tuple or len(edge) != 2
                       or any(type(node) is not str or node not in self.nodes for node in edge)
                       or edge[0] == edge[1] for edge in self.edges)
                or self.edges != tuple(sorted(set(self.edges)))):
            raise ValueError('canonical tiny directed synthetic graph required')
        if self.graph_sha256 != graph_sha256(domain=self.domain, nodes=self.nodes,
                                             edges=self.edges, direction=self.direction):
            raise ValueError('graph SHA binding mismatch')
        graph = nx.DiGraph()
        graph.add_nodes_from(self.nodes); graph.add_edges_from(self.edges)
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError('toy prerequisite graph must be a DAG')


@dataclass(frozen=True)
class GAMQuery:
    exercise: str
    problem_type: str
    difficulty: float
    timestamp: pd.Timestamp
    source_row: int

    def __post_init__(self):
        _text(self.exercise); _text(self.problem_type)
        if (type(self.difficulty) not in (int, float) or not math.isfinite(self.difficulty)
                or not isinstance(self.timestamp, pd.Timestamp) or pd.isna(self.timestamp)
                or self.timestamp.tzinfo is None
                or type(self.source_row) is not int or self.source_row < 1):
            raise ValueError('finite difficulty, explicit aware timestamp and source row required')


@dataclass(frozen=True)
class GAMStepScore:
    probability: float
    learner_id: str
    source_row: int
    prior_interactions: int
    binding_sha256: str
    role: str = ROLE


class _ImmutableGraph:
    def __init__(self, binding):
        self._nodes = binding.nodes
        self._parents = MappingProxyType({node: tuple(a for a, b in binding.edges if b == node)
                                         for node in binding.nodes})

    def __contains__(self, node):
        return node in self._nodes

    def predecessors(self, node):
        return self._parents[node]


class GAMVariantFactory:
    """Mỗi factory có metadata/cache namespace riêng; mỗi learner có state mới.

    Private namespace chạy nguyên bytes của module nguồn đã hash, không nhận
    source path/code từ caller. Temporary module registration chỉ phục vụ
    dataclass annotations, được dọn ngay; không thay module native hiện có.
    """

    def __init__(self, topics, areas, *, recipe, graph_binding, synthetic_only):
        if (synthetic_only is not True or type(recipe) is not GAMVariantRecipe
                or type(graph_binding) is not GAMGraphBinding or recipe.domain != graph_binding.domain):
            raise ValueError('typed explicit matching synthetic recipe/graph required')
        graph_binding.__post_init__(); recipe.__post_init__()
        maps = []
        for value in (topics, areas):
            if type(value) is not dict or set(value) != set(graph_binding.nodes):
                raise ValueError('metadata must exactly cover bound exercise nodes')
            for key, item in value.items():
                _text(key); _text(item)
            maps.append(MappingProxyType(dict(value)))
        payload = _source_payload()
        if hashlib.sha256(payload).hexdigest() != recipe.source_sha256:
            raise ValueError('native source SHA mismatch')
        name = f'_gam_toy_variant_{uuid4().hex}'
        module = ModuleType(name)
        sys.modules[name] = module
        try:
            exec(compile(payload, str(SOURCE), 'exec'), module.__dict__)
        finally:
            del sys.modules[name]
        module.configure_metadata(*maps)
        self._scope = module.__dict__
        self._recipe, self._graph_binding = recipe, graph_binding
        self._graph = _ImmutableGraph(graph_binding)
        self._binding = self._current_binding()
        self._binding_sha256 = _hash(self._binding)

    def _current_binding(self):
        return {'schema_version': 1, 'role': ROLE, 'recipe': asdict(self._recipe),
                'graph': asdict(self._graph_binding),
                'topics': dict(self._scope['topic_map']), 'areas': dict(self._scope['area_map']),
                'implementation_source_sha256': _implementation_sources(),
                'source_algorithm': 'original_junyi.py; Paper2 Junyi cell11 extraction',
                'metadata_provenance': 'caller_declared_toy_snapshot; not train-fitted difficulty/vocab',
                'native_adaptation_semantics': 'coupled parent and local adaptation; not edge-only effect',
                'max_interactions_per_session': MAX_INTERACTIONS}

    def _assert_bound(self):
        if (_hash(self._current_binding()) != self._binding_sha256
                or native_source_sha256() != self._recipe.source_sha256):
            raise ValueError('source/metadata/graph/recipe binding changed')

    @property
    def binding(self):
        self._assert_bound()
        return json.loads(json.dumps(self._binding))

    def new_learner(self, learner_id):
        _text(learner_id); self._assert_bound()
        recipe = self._recipe
        model = self._scope['GAMKTModel'](
            use_graph_context=recipe.graph_signal_enabled or recipe.graph_adaptation_enabled,
            time_decay_rate=recipe.time_decay_rate, graph_weight=recipe.graph_weight,
            graph_source=self._graph, graph_signal_enabled=recipe.graph_signal_enabled,
            graph_adaptation_enabled=recipe.graph_adaptation_enabled, name=recipe.label)
        return GAMVariantSession._create(self, learner_id, model)


class GAMVariantSession:
    def __init__(self, factory, learner_id, model):
        raise TypeError('use factory.new_learner for source-bound fresh learner state')

    @classmethod
    def _create(cls, factory, learner_id, model):
        self = object.__new__(cls)
        self._factory, self._learner_id, self._model = factory, learner_id, model
        self._calls, self._completed, self._last = 0, 0, None
        self._rows = set()
        return self

    def _assert_bound(self):
        self._factory._assert_bound()
        recipe = self._factory._recipe
        if (self._model.graph_signal_enabled is not recipe.graph_signal_enabled
                or self._model.graph_adaptation_enabled is not recipe.graph_adaptation_enabled
                or self._model.use_graph_context is not (recipe.graph_signal_enabled or recipe.graph_adaptation_enabled)
                or self._model.graph_weight != recipe.graph_weight
                or self._model.time_decay_rate != recipe.time_decay_rate
                or self._model.graph_source is not self._factory._graph):
            raise ValueError('native variant settings changed')

    def step(self, query, correct):
        """Một response event: source predict trước source update; không global fit."""
        if type(query) is not GAMQuery or type(correct) is not int or correct not in (0, 1):
            raise ValueError('typed query and binary current response required')
        query.__post_init__(); self._assert_bound()
        if query.exercise not in self._factory._graph:
            raise ValueError('query outside bound toy domain')
        key = (query.timestamp.value, query.source_row)
        if query.source_row in self._rows or (self._last is not None and key <= self._last):
            raise ValueError('duplicate source row or chronology violation')
        if self._calls >= MAX_INTERACTIONS:
            raise ValueError('toy session exceeds32 attempted interactions')
        self._calls += 1
        probability = predict_then_update(self._model, query.exercise, query.problem_type,
            query.difficulty, query.timestamp, correct)
        self._assert_bound()
        self._rows.add(query.source_row); self._last = key
        prior = self._completed; self._completed += 1
        return GAMStepScore(probability, self._learner_id, query.source_row, prior,
                            self._factory._binding_sha256)

    def state_snapshot(self):
        """Copy để kiểm parity; không checkpoint hoặc fitted-state certificate."""
        self._assert_bound()
        return {name: {'theta': state.theta, 'memory': state.memory.tolist(),
                       'pi_task': state.pi_task, 'pi_time': state.pi_time,
                       'attempts': state.attempts,
                       'last_timestamp': None if state.last_timestamp is None else state.last_timestamp.isoformat(),
                       'recent_outcomes': list(state.recent_outcomes), 'times_forgotten': state.times_forgotten}
                for name, state in sorted(self._model.states.items())}

    def as_online_backend(self):
        raise NotImplementedError('toy native state is not a selected-fit OnlineSession artifact')


def build_variant_factory(topics, areas, *, recipe, graph_binding, synthetic_only):
    return GAMVariantFactory(topics, areas, recipe=recipe, graph_binding=graph_binding,
                             synthetic_only=synthetic_only)
