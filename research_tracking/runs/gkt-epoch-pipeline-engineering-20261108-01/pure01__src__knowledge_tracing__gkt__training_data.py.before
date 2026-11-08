"""Role-bound observable toy data GKT; không Junyi loader hoặc scientific mapping fit."""
from collections import Counter
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path

import torch

from knowledge_tracing.shared_kt import StableVocabulary
from knowledge_tracing.simulator_bridge import SimulatorBank, identity_hash
from knowledge_tracing.simulator_data import ObservableTrajectory, SimulatorSplitPlan, validate_role_shard
from .config import GKTBinding, GKTKernelConfig
from .core import StaticGKTKernel, adjacency_sha256
from .recurrent import RECIPE_ID, GRU_VARIANT


@dataclass(frozen=True)
class GKTObservableShard:
    plan: SimulatorSplitPlan
    bank: SimulatorBank
    role: str
    max_events_per_learner: int
    trajectories: tuple[ObservableTrajectory, ...]

    def __post_init__(self):
        if (type(self.plan) is not SimulatorSplitPlan or type(self.bank) is not SimulatorBank
                or self.role not in ('train', 'selection') or type(self.max_events_per_learner) is not int
                or not 1 <= self.max_events_per_learner <= 12 or type(self.trajectories) is not tuple
                or not 1 <= len(self.trajectories) <= 2 or len(self.bank.items) > 8
                or any(type(x) is not ObservableTrajectory for x in self.trajectories)):
            raise ValueError('bounded exact observable train/selection shard required')
        self.audit

    @property
    def audit(self):
        return validate_role_shard(self.trajectories, plan=self.plan, bank=self.bank, role=self.role,
                                   max_events_per_learner=self.max_events_per_learner)


@dataclass(frozen=True)
class GKTDataRecipe:
    recipe_id: str
    mlp_hidden_dim: int
    normalization: str
    dropout: float
    initial_state_policy: str
    gru_variant: str
    precision: str
    history_policy: str
    first_target_policy: str
    oov_policy: str
    item_support_policy: str

    def __post_init__(self):
        if (self.recipe_id != RECIPE_ID or self.normalization != 'none' or self.initial_state_policy != 'zeros'
                or self.gru_variant != GRU_VARIANT or type(self.mlp_hidden_dim) is not int
                or not 1 <= self.mlp_hidden_dim <= 8 or type(self.dropout) not in (int, float) or self.dropout != 0
                or self.precision not in ('float32', 'float64') or self.history_policy != 'full_prefix'
                or self.first_target_policy not in ('query_only', 'unsupported')
                or self.oov_policy != 'unsupported_history' or self.item_support_policy != 'train_observed_items_only'):
            raise ValueError('explicit supported engineering recipe/history/support required')

    def recurrent_kwargs(self):
        value = {name: getattr(self, name) for name in ('recipe_id', 'mlp_hidden_dim', 'normalization',
                 'dropout', 'initial_state_policy', 'gru_variant')}
        value['dropout'] = float(value['dropout'])
        return value


@dataclass(frozen=True)
class GKTGraphProvenance:
    kind: str
    source_sha256: str
    domain: str
    node_order_sha256: str

    def __post_init__(self):
        if self.kind != 'caller_declared_static' or type(self.domain) is not str or not self.domain.strip():
            raise ValueError('explicit static graph provenance; no graph learning in this pipeline')
        for digest in (self.source_sha256, self.node_order_sha256):
            if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                raise ValueError('strict graph provenance SHA required')


@dataclass(frozen=True)
class GKTPreparedSequence:
    learner_id: str
    role: str
    items: tuple[str, ...]
    node_indices: tuple[int, ...]
    targets: tuple[int, ...]
    timestamps: tuple[int, ...]
    source_rows: tuple[int, ...]
    model_valid_mask: tuple[bool, ...]
    loss_mask: tuple[bool, ...]
    support_reasons: tuple[str, ...]


def source_identity():
    root = Path(__file__).resolve().parents[3]
    names = ['src/knowledge_tracing/gkt/' + n for n in ('training_data.py', 'config.py', 'core.py', 'recurrent.py', '__init__.py')]
    names += ['src/knowledge_tracing/shared_kt.py', 'src/knowledge_tracing/simulator_bridge.py',
              'src/knowledge_tracing/simulator_data.py']
    return {n: hashlib.sha256((root / n).read_bytes()).hexdigest() for n in names}


@dataclass(frozen=True)
class GKTPreparedData:
    train_shard: GKTObservableShard
    selection_shard: GKTObservableShard
    model_config: GKTKernelConfig
    binding: GKTBinding
    adjacency: torch.Tensor
    graph_provenance: GKTGraphProvenance
    recipe: GKTDataRecipe
    registry: tuple[tuple[str, str], ...]
    train_item_vocabulary: StableVocabulary
    train_item_support: tuple[tuple[str, int], ...]
    training_map: tuple[tuple[str, str], ...]
    train: tuple[GKTPreparedSequence, ...]
    selection: tuple[GKTPreparedSequence, ...]
    source_sha256: dict
    content_sha256: str
    synthetic_only: bool

    def payload(self):
        return dict(schema_version=1, role='synthetic_engineering_training_data',
            train_audit=self.train_shard.audit, selection_audit=self.selection_shard.audit,
            model_config=asdict(self.model_config), binding=asdict(self.binding),
            graph_sha256=adjacency_sha256(self.adjacency), graph_provenance=asdict(self.graph_provenance),
            recipe=asdict(self.recipe), registry=self.registry,
            train_item_vocabulary=self.train_item_vocabulary.values, train_item_support=self.train_item_support,
            training_map=self.training_map, train=[asdict(x) for x in self.train], selection=[asdict(x) for x in self.selection],
            source_sha256=self.source_sha256, synthetic_only=self.synthetic_only)

    def assert_integrity(self):
        if (self.synthetic_only is not True or self.source_sha256 != source_identity()
                or identity_hash(self.payload()) != self.content_sha256):
            raise ValueError('prepared observable data/mapping/graph/source changed')

    @property
    def training_encoding_identity(self):
        """Only TRAIN and static declared registry/provenance, no selection statistics."""
        self.assert_integrity()
        return dict(train_shard_sha256=self.train_shard.audit['shard_sha256'],
            train_item_vocabulary=self.train_item_vocabulary.values,
            train_item_vocabulary_sha256=identity_hash(self.train_item_vocabulary.values),
            node_vocabulary_sha256=self.binding.vocabulary_sha256, node_order_sha256=self.binding.node_order_sha256,
            train_item_support=self.train_item_support, training_map=self.training_map,
            mapping_sha256=identity_hash(self.training_map), registry_sha256=identity_hash(self.registry),
            graph_sha256=adjacency_sha256(self.adjacency), graph_provenance=asdict(self.graph_provenance),
            mapping_origin='caller_declared_static_registry; usage proved by actual optimization receipts')

    @property
    def recurrent_recipe_sha256(self):
        descriptor = {**self.recipe.recurrent_kwargs(), 'config': asdict(self.model_config), 'dtype': 'torch.' + self.recipe.precision}
        return hashlib.sha256(json.dumps(descriptor, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _prepare(shard, vocabulary, mapping, binding, recipe):
    result = []
    for trajectory in sorted(shard.trajectories, key=lambda x: x.learner_id):
        rows = trajectory.observations; blocked = False; nodes = []; valid = []; loss = []; reasons = []
        for rank, observation in enumerate(rows):
            item = observation.query.item_id
            if item not in vocabulary.values:
                reason = 'oov_item'; node = -1; usable = False; blocked = True
            elif blocked:
                reason = 'unsupported_history'; node = mapping[item]; usable = False
            else:
                node = mapping[item]; usable = True
                reason = ('known_history' if rank else 'cold_query_only'
                          if recipe.first_target_policy == 'query_only' else 'cold_unsupported')
            nodes.append(node); valid.append(usable); reasons.append(reason)
            loss.append(reason in ('known_history', 'cold_query_only'))
        result.append(GKTPreparedSequence(trajectory.learner_id, shard.role,
            tuple(x.query.item_id for x in rows), tuple(nodes), tuple(x.correct for x in rows),
            tuple(x.query.timestamp for x in rows), tuple(x.query.source_row for x in rows),
            tuple(valid), tuple(loss), tuple(reasons)))
    return tuple(result)


def prepare_gkt_training_data(train_shard, selection_shard, *, model_config, node_binding, adjacency,
                              graph_provenance, item_node_registry, recipe, synthetic_only):
    """No file loader/fit graph: bind exactly what is mechanically used in TRAIN."""
    if (type(train_shard) is not GKTObservableShard or type(selection_shard) is not GKTObservableShard
            or train_shard.role != 'train' or selection_shard.role != 'selection'
            or train_shard.plan != selection_shard.plan or train_shard.bank != selection_shard.bank
            or type(model_config) is not GKTKernelConfig or type(node_binding) is not GKTBinding
            or type(graph_provenance) is not GKTGraphProvenance or type(recipe) is not GKTDataRecipe
            or type(item_node_registry) is not dict or synthetic_only is not True):
        raise ValueError('explicit disjoint train/selection engineering inputs required')
    ta, va = train_shard.audit, selection_shard.audit
    train_users = {x.learner_id for x in train_shard.trajectories}
    val_users = {x.learner_id for x in selection_shard.trajectories}
    train_rows = {o.query.source_row for x in train_shard.trajectories for o in x.observations}
    val_rows = {o.query.source_row for x in selection_shard.trajectories for o in x.observations}
    if train_users & val_users or train_rows & val_rows:
        raise ValueError('train/selection learners and source rows must be disjoint')
    if (model_config.num_nodes != len(node_binding.node_ids) or model_config.node_unit != node_binding.node_unit
            or model_config.num_nodes > 4 or max(model_config.state_dim, model_config.embedding_dim, model_config.message_dim) > 8
            or model_config.message_dim != model_config.state_dim or node_binding.domain != train_shard.bank.environment_id
            or node_binding.vocabulary_sha256 != identity_hash(node_binding.node_ids)
            or graph_provenance.domain != node_binding.domain or graph_provenance.node_order_sha256 != node_binding.node_order_sha256):
        raise ValueError('explicit bounded node vocabulary/domain/graph order required')
    if (not isinstance(adjacency, torch.Tensor) or adjacency.device.type != 'cpu'
            or adjacency.dtype != getattr(torch, recipe.precision) or adjacency.requires_grad):
        raise ValueError('fixed matching CPU graph required')
    with torch.device('cpu'):
        StaticGKTKernel(model_config, node_binding, adjacency)  # Reuse graph geometry checks; no neural model.
    bank_items = {x.item_id: x for x in train_shard.bank.items}
    for item, node in item_node_registry.items():
        if (item not in bank_items or type(node) is not str or node not in node_binding.node_ids
                or (node_binding.node_unit == 'concept' and bank_items[item].concept_id != node)):
            raise ValueError('one explicit bank item must map to one matching declared node')
    support = Counter()
    for trajectory in train_shard.trajectories:
        support.update({x.query.item_id for x in trajectory.observations})
    if not set(support) <= set(item_node_registry):
        raise ValueError('every TRAIN item needs declared mapping; no hidden history skip')
    vocabulary = StableVocabulary.from_values(tuple(support))
    training_map = tuple((item, item_node_registry[item]) for item in vocabulary.values)
    encoded_map = {item: node_binding.node_ids.index(node) for item, node in training_map}
    train = _prepare(train_shard, vocabulary, encoded_map, node_binding, recipe)
    selection = _prepare(selection_shard, vocabulary, encoded_map, node_binding, recipe)
    if not any(any(x.loss_mask) for x in train):
        raise ValueError('TRAIN has no eligible targets under explicit cold policy')
    data = GKTPreparedData(train_shard, selection_shard, model_config, node_binding, adjacency.detach().clone(),
        graph_provenance, recipe, tuple(sorted(item_node_registry.items())), vocabulary, tuple(sorted(support.items())),
        training_map, train, selection, source_identity(), '', True)
    return replace(data, content_sha256=identity_hash(data.payload()))
