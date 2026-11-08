"""Frozen GKT engineering inference; không fitted OnlineSession promotion.

Mapping item→node là caller-declared inference binding, KHÔNG train-attested.
Full-prefix/unsupported-history là explicit engineering recipe, chưa S04/S05.
"""
from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np
import torch

from knowledge_tracing.shared_kt import CausalSequenceInputs, StableVocabulary
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, identity_hash
from . import training as tr
from . import training_checkpoint as checkpoint


@dataclass(frozen=True)
class GKTInferenceSpec:
    history_policy: str
    first_target_policy: str
    oov_policy: str
    max_events: int
    device: str
    precision: str

    def __post_init__(self):
        if (self.history_policy != 'full_prefix' or self.oov_policy != 'unsupported_history'
                or self.first_target_policy not in ('query_only', 'unsupported')
                or type(self.max_events) is not int or not 1 <= self.max_events <= 12
                or self.device != 'cpu' or self.precision not in ('float32', 'float64')):
            raise ValueError('explicit bounded engineering inference conventions required')


@dataclass(frozen=True)
class GKTHistory:
    learner_id: str
    observations: tuple[Observation, ...]

    def __post_init__(self):
        if (type(self.learner_id) is not str or not self.learner_id.strip()
                or type(self.observations) is not tuple
                or any(type(x) is not Observation or type(x.query) is not ItemQuery for x in self.observations)):
            raise ValueError('typed immutable history and learner identity required')


@dataclass(frozen=True)
class GKTInferenceScore:
    probability: float | None
    support_reason: str
    learner_id: str
    source_row: int
    global_rank: int
    history_available: int
    history_used: int
    context_reset: bool
    item_id: str | None
    node_id: str | None
    weight_role: str
    checkpoint_manifest_sha256: str
    binding_sha256: str
    research_fitted: bool = False
    score_kind: str = 'uncalibrated_node_response_probability'


def source_identity():
    root = Path(__file__).resolve().parents[3]
    names = ('src/knowledge_tracing/gkt/adapter.py', 'src/knowledge_tracing/gkt/__init__.py',
             'src/knowledge_tracing/shared_kt.py', 'src/knowledge_tracing/simulator_bridge.py')
    return {**checkpoint.source_identity(), **{name: checkpoint._sha((root / name).read_bytes()) for name in names}}


def _binding_identity(loaded, bank, vocabulary, item_to_node, spec):
    """Pure binding helper; private unverified containers are for honest unit fixtures."""
    if (type(loaded) is not checkpoint.GKTLoadedEngineeringWeights or type(bank) is not SimulatorBank
            or type(vocabulary) is not StableVocabulary or type(spec) is not GKTInferenceSpec
            or type(item_to_node) is not dict or not tr._sha(loaded.manifest_sha256)):
        raise ValueError('typed explicit checkpoint/bank/vocabulary/map/spec required')
    model = loaded.model
    return _identity_fields(model.config, model.binding, model.graph_sha256, model.recipe_sha256,
        model.mlp_hidden_dim, str(model.adjacency.dtype).split('.')[-1], loaded.identity,
        loaded.manifest_sha256, bank, vocabulary, item_to_node, spec)


def _identity_fields(config, node_binding, graph_sha256, recipe_sha256, mlp_hidden_dim, precision,
                     artifact_identity, manifest_sha256, bank, vocabulary, item_to_node, spec):
    if (type(bank) is not SimulatorBank or type(vocabulary) is not StableVocabulary
            or type(spec) is not GKTInferenceSpec or type(item_to_node) is not dict or not tr._sha(manifest_sha256)):
        raise ValueError('explicit inference identity components required')
    values = vocabulary.values
    if (type(values) is not tuple or not 1 <= len(values) <= 8 or len(set(values)) != len(values)
            or any(type(x) is not str or not x for x in values) or not set(values) <= set(bank.item_ids)
            or len(bank.items) > 8 or node_binding.domain != bank.environment_id
            or config.num_nodes > 4 or max(config.state_dim, config.embedding_dim,
                config.message_dim, mlp_hidden_dim) > 8
            or precision != spec.precision
            or not set(item_to_node) <= set(values)):
        raise ValueError('explicit item/node/domain/precision geometry mismatch')
    items = {x.item_id: x for x in bank.items}
    for item, node in item_to_node.items():
        if type(node) is not str or node not in node_binding.node_ids:
            raise ValueError('one item must map to one existing bound node; no multi-tag inference')
        if node_binding.node_unit == 'concept' and items[item].concept_id != node:
            raise ValueError('declared concept mapping disagrees with bound bank')
    role = artifact_identity.get('weight_role')
    if role not in (tr.WEIGHT_ROLE, 'unverified_fixture'):
        raise ValueError('engineering or explicitly unverified unit-fixture role required')
    value = dict(schema_version=1, model='frozen_gkt_engineering_inference',
        checkpoint_manifest_sha256=manifest_sha256, checkpoint_identity_sha256=identity_hash(artifact_identity),
        node_binding=asdict(node_binding), config=asdict(config), graph_sha256=graph_sha256,
        recipe_sha256=recipe_sha256, engineering_bank_identity=bank.identity,
        input_item_vocabulary=list(values), item_to_node=dict(item_to_node), inference_spec=asdict(spec),
        mapping_provenance='caller_declared_inference_mapping_NOT_training_attested',
        score_kind='uncalibrated_node_response_probability',
        weight_role=role, research_fitted=False, source_sha256=source_identity())
    return json.loads(json.dumps(value, allow_nan=False))


def inference_identity(checkpoint_identity, *, checkpoint_manifest_sha256, bank, item_vocabulary, item_to_node, spec):
    """Validate expected binding before weights deserialization; no model allocation."""
    c, binding, recipe = checkpoint._validate_identity(checkpoint_identity)
    return _identity_fields(c, binding, checkpoint_identity['graph_sha256'], checkpoint_identity['recipe_sha256'],
        recipe['mlp_hidden_dim'], recipe['precision'], checkpoint_identity, checkpoint_manifest_sha256,
        bank, item_vocabulary, item_to_node, spec)


class FrozenGKTAdapter:
    """No implicit state cache: every query replays only supplied real history.

    _from_loaded is internal assembly, not a public authorization boundary.
    Public loader below accepts only the existing strict GKT04 trained receipt.
    """
    def __init__(self, *args, **kwargs):
        raise TypeError('use load_frozen_engineering_gkt')

    @classmethod
    def _from_loaded(cls, loaded, bank, vocabulary, item_to_node, spec, *, expected_inference_binding):
        identity = _binding_identity(loaded, bank, vocabulary, item_to_node, spec)
        if identity != expected_inference_binding:
            raise ValueError('expected inference binding mismatch')
        self = object.__new__(cls)
        self._loaded, self._bank, self._vocabulary, self._spec = loaded, bank, vocabulary, spec
        self._mapping = dict(item_to_node)
        self._identity = json.loads(json.dumps(identity))
        self._binding_sha256 = identity_hash(self._identity)
        self._model = loaded.model
        self._model.eval().requires_grad_(False)
        self._model_sha256 = tr.model_digest(self._model)
        return self

    @property
    def binding(self):
        return json.loads(json.dumps(self._identity))

    @property
    def artifact_id(self):
        return self._loaded.manifest_sha256

    def _assert_frozen(self):
        current = _binding_identity(self._loaded, self._bank, self._vocabulary, self._mapping, self._spec)
        if (current != self._identity or tr.model_digest(self._model) != self._model_sha256
                or any(x.training for x in self._model.modules())
                or any(p.requires_grad or p.grad is not None for p in self._model.parameters())):
            raise ValueError('frozen engineering model/source/binding changed')
        self._model._bound(self._model.binding, self._model.graph_sha256)

    def fit(self, *args, **kwargs):
        raise NotImplementedError('engineering frozen inference only; no corpus trainer')

    def as_online_backend(self):
        raise NotImplementedError('OnlineScore requires fitted; engineering role must not be promoted')

    def _node(self, item):
        if item not in self._vocabulary.values:
            return None, 'oov_item'
        node = self._mapping.get(item)
        return ((self._model.binding.node_ids.index(node), '') if node is not None else (None, 'unmapped_item'))

    def _prefix_state(self, nodes, responses):
        if any(x is None for x in nodes):
            return None
        model = self._model; kwargs = dict(binding=model.binding, graph_sha256=model.graph_sha256)
        state = model.initial_state(1, **kwargs)
        for node, correct in zip(nodes, responses):
            state = model.observe(state, torch.tensor([node], dtype=torch.long, device='cpu'),
                torch.tensor([correct], dtype=torch.long, device='cpu'), torch.tensor([True], device='cpu'), **kwargs)
        return state

    def _score(self, state, nodes, item, reason, *, learner_id, source_row):
        rank = len(nodes); node, node_reason = self._node(item) if item is not None else (None, 'oov_item')
        reason = reason or node_reason
        if not reason:
            reason = ('unsupported_history' if state is None else 'known_history' if rank else
                      'cold_query_only' if self._spec.first_target_policy == 'query_only' else 'cold_unsupported')
        probability = None
        if reason in ('known_history', 'cold_query_only'):
            output = self._model.predict(state, torch.tensor([node], dtype=torch.long, device='cpu'),
                binding=self._model.binding, graph_sha256=self._model.graph_sha256)
            probability = float(output.probabilities[0])
            if not np.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError('finite node-response probability required')
        return GKTInferenceScore(probability, reason, learner_id, source_row, rank, rank,
            rank if probability is not None else 0, False, item,
            None if node is None else self._model.binding.node_ids[node], self._identity['weight_role'],
            self.artifact_id, self._binding_sha256)

    def _validate_inputs(self, inputs):
        if type(inputs) is not CausalSequenceInputs or inputs.concept_ids is not None:
            raise ValueError('shared causal item inputs only; node mapping must be explicit')
        n = len(inputs.item_ids)
        arrays = (inputs.item_ids, inputs.timestamps, inputs.prior_responses, inputs.source_rows)
        if (n > 24 or any(not isinstance(x, np.ndarray) or x.shape != (n,) or not np.issubdtype(x.dtype, np.integer) for x in arrays)
                or type(inputs.user_ids) is not tuple or len(inputs.user_ids) != n
                or any(type(x) is not str or not x.strip() for x in inputs.user_ids)
                or np.any(inputs.item_ids < -1) or np.any(inputs.item_ids >= len(self._vocabulary.values))
                or np.any(inputs.timestamps < 0) or np.any(inputs.source_rows < 1)
                or len(set(inputs.source_rows.tolist())) != n or not isinstance(inputs.sequence_offsets, np.ndarray)
                or inputs.sequence_offsets.ndim != 1 or not np.issubdtype(inputs.sequence_offsets.dtype, np.integer)):
            raise ValueError('bounded integer causal event identity required')
        offsets = inputs.sequence_offsets.tolist()
        if n == 0:
            if offsets != [0]:
                raise ValueError('empty sequence offsets required')
            return []
        if (not 2 <= len(offsets) <= 3 or offsets[0] != 0 or offsets[-1] != n
                or any(a >= b for a, b in zip(offsets, offsets[1:]))):
            raise ValueError('at most two explicit learner segments required')
        users = set(); segments = []
        for start, stop in zip(offsets, offsets[1:]):
            user = inputs.user_ids[start]
            order = list(zip(inputs.timestamps[start:stop].tolist(), inputs.source_rows[start:stop].tolist()))
            if (stop - start > self._spec.max_events or user in users or set(inputs.user_ids[start:stop]) != {user}
                    or inputs.prior_responses[start] != -1 or not np.isin(inputs.prior_responses[start + 1:stop], (0, 1)).all()
                    or any(a >= b for a, b in zip(order, order[1:]))):
                raise ValueError('causal segmentation/chronology/shifted prior responses invalid')
            users.add(user); segments.append((start, stop))
        return segments

    def predict_details(self, inputs):
        self._assert_frozen(); segments = self._validate_inputs(inputs); scores = []
        with torch.inference_mode(), torch.device('cpu'):
            for start, stop in segments:
                nodes = []
                for i in range(start, stop):
                    responses = inputs.prior_responses[start + 1:i + 1].tolist()
                    state = self._prefix_state(nodes, responses)
                    item = None if inputs.item_ids[i] == -1 else self._vocabulary.values[int(inputs.item_ids[i])]
                    scores.append(self._score(state, nodes, item, '', learner_id=inputs.user_ids[i], source_row=int(inputs.source_rows[i])))
                    nodes.append(None if item is None else self._node(item)[0])
        self._assert_frozen()
        return tuple(scores)

    def predict(self, inputs):
        scores = self.predict_details(inputs)
        if any(x.probability is None for x in scores):
            raise ValueError('unsupported targets: use predict_details and full population coverage')
        return np.asarray([x.probability for x in scores], dtype=np.float64)

    def query_many(self, history, queries, *, learner_id):
        self._assert_frozen()
        if (type(history) is not GKTHistory or history.learner_id != learner_id
                or type(queries) is not tuple or len(queries) > 8
                or len(history.observations) + 1 > self._spec.max_events):
            raise ValueError('bounded learner-bound query history required')
        past = tuple(x.query for x in history.observations)
        for query in queries:
            if type(query) is not ItemQuery:
                raise ValueError('current query accepts no label')
        for sequence in (past, *(past + (q,) for q in queries)):
            keys = [(q.timestamp, q.source_row) for q in sequence]
            if (any(q.item_id not in self._bank.item_ids for q in sequence)
                    or len({q.source_row for q in sequence}) != len(sequence)
                    or any(a >= b for a, b in zip(keys, keys[1:]))):
                raise ValueError('query/history domain/source/chronology mismatch')
        nodes = [self._node(x.item_id)[0] for x in past]
        with torch.inference_mode(), torch.device('cpu'):
            state = self._prefix_state(nodes, [x.correct for x in history.observations])
            scores = tuple(self._score(state, nodes, q.item_id, '', learner_id=learner_id, source_row=q.source_row) for q in queries)
        self._assert_frozen()
        return scores

    def query(self, history, query, *, learner_id):
        return self.query_many(history, (query,), learner_id=learner_id)[0]


def population_summary(scores, *, expected_source_rows):
    if (type(scores) is not tuple or type(expected_source_rows) is not tuple
            or any(type(x) is not GKTInferenceScore for x in scores)
            or len(set(expected_source_rows)) != len(expected_source_rows)
            or tuple(x.source_row for x in scores) != expected_source_rows
            or any(x.research_fitted for x in scores)):
        raise ValueError('every original target must remain aligned with explicit research role')
    scored = sum(x.probability is not None for x in scores)
    return dict(expected_targets=len(scores), scored_targets=scored, unsupported_targets=len(scores) - scored,
        research_fitted_targets=0, support_reasons={reason: sum(x.support_reason == reason for x in scores)
        for reason in sorted({x.support_reason for x in scores})})


def load_frozen_engineering_gkt(checkpoint_directory, *, expected_manifest_sha256, expected_checkpoint_identity,
        bank, item_vocabulary, item_to_node, spec, expected_inference_binding, max_checkpoint_bytes):
    """Production entry uses strict GKT04 loader; private fixture assembly is not a certificate."""
    required = inference_identity(expected_checkpoint_identity, checkpoint_manifest_sha256=expected_manifest_sha256,
        bank=bank, item_vocabulary=item_vocabulary, item_to_node=item_to_node, spec=spec)
    if required != expected_inference_binding:
        raise ValueError('expected inference binding mismatch before checkpoint load')
    loaded = checkpoint.load_engineering_weights(checkpoint_directory,
        expected_manifest_sha256=expected_manifest_sha256, expected_identity=expected_checkpoint_identity,
        max_checkpoint_bytes=max_checkpoint_bytes)
    if (loaded.identity != expected_checkpoint_identity or loaded.identity.get('weight_role') != tr.WEIGHT_ROLE
            or loaded.manifest_sha256 != expected_manifest_sha256):
        raise ValueError('strict actual trained engineering checkpoint required; no fixture promotion')
    return FrozenGKTAdapter._from_loaded(loaded, bank, item_vocabulary, item_to_node, spec,
                                        expected_inference_binding=expected_inference_binding)
