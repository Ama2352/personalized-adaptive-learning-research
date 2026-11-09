"""GKT research28 theo recipe29, compute-only, chưa có fit attestation.

Candidate cho knowledge_tracing.gkt.research_model, chưa áp dụng canonical.
Caller kiểm source/files/authority và ngân sách trước allocation nghiên cứu.
Forward dùng CPU RNG thông thường. Trainer sau này sở hữu dropout stream,
không chạy đồng thời fork_rng trong nhiều threads.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import re

import torch
from torch import nn
from torch.nn import functional as F

from knowledge_tracing.gkt.config import GKTBinding, GKTKernelConfig
from knowledge_tracing.gkt.core import StaticGKTKernel, adjacency_sha256
from knowledge_tracing.gkt.recurrent import (
    ChoResetBeforeGRU, GKTRecurrentReadout, GKTRecurrentSequence, GKTRecurrentState,
)
from knowledge_tracing.gkt.research_data import GKTResearchGraphBinding


RECIPE_ID = 'gkt-grade10-static-expert-r32-bn-d5-v1'
RECIPE_SOURCE_SHA256 = '059c98909c38856afd830d1cd296ce8875682ba9c7c226ad923c432e4328ce64'
EVIDENCE_ROLE = 'gkt_research_computation_no_fit_attestation'
_SOURCE_NAMES = ('config', 'core', 'recurrent', 'research_model')
_NUMERICAL = dict(state_dim=32, embedding_dim=32, message_dim=32, mlp_hidden_dim=32,
    dropout=0.5, bn_eps=1e-5, bn_momentum=0.1, bn_pool='current_time_valid_nonself_pairs',
    singleton='frozen_running_statistics', h0='zeros', erase_add='unary_message',
    gru='cho_reset_before_bias_free', max_batch_size=4, max_sequence_steps=210)


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(value):
    _need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None,
          'Lowercase SHA256 required')


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def _float_tensor(value, shape):
    _need(isinstance(value, torch.Tensor) and tuple(value.shape) == tuple(shape)
          and value.device.type == 'cpu' and value.dtype == torch.float32
          and bool(torch.isfinite(value).all()), 'Finite CPU FP32 tensor with exact shape required')


def _integer_tensor(value, shape):
    _need(isinstance(value, torch.Tensor) and tuple(value.shape) == tuple(shape)
          and value.device.type == 'cpu' and value.dtype == torch.long,
          'CPU integer tensor with exact shape required')


@dataclass(frozen=True)
class GKTResearchModelSpec:
    recipe_id: str
    recipe_source_sha256: str
    phase_scope: str
    phase_sha256: str
    encoding_sha256: str
    vocabulary_sha256: str
    sources_sha256: tuple[tuple[str, str], ...]
    initialization_seed: int
    evidence_role: str

    def __post_init__(self):
        _need(self.recipe_id == RECIPE_ID and self.recipe_source_sha256 == RECIPE_SOURCE_SHA256,
              'Recipe29 identity required')
        _need(self.phase_scope in ('select_train80', 'refit_union90'), 'Optimization phase required')
        for value in (self.phase_sha256, self.encoding_sha256, self.vocabulary_sha256):
            _sha(value)
        _need(type(self.sources_sha256) is tuple and len(self.sources_sha256) == len(_SOURCE_NAMES)
              and all(type(row) is tuple and len(row) == 2 for row in self.sources_sha256),
              'Explicit source inventory required')
        _need(tuple(name for name, _ in self.sources_sha256) == _SOURCE_NAMES,
              'Exact ordered model source inventory required')
        for _, value in self.sources_sha256:
            _sha(value)
        _need(type(self.initialization_seed) is int and self.initialization_seed == 42,
              'Recipe29 initialization seed42 required')
        _need(self.evidence_role == EVIDENCE_ROLE, 'Compute-only evidence role required')


class _MaskedOutputMLP(nn.Module):
    """Nhận gathered rows tại một time, không tự flatten batch/time/node."""

    def __init__(self, input_width):
        super().__init__()
        self.input_width = input_width
        self.first = nn.Linear(input_width, 32, device='cpu', dtype=torch.float32)
        self.dropout = nn.Dropout(0.5)
        self.second = nn.Linear(32, 32, device='cpu', dtype=torch.float32)
        self.bn = nn.BatchNorm1d(32, eps=1e-5, momentum=0.1, affine=True,
                               track_running_stats=True, device='cpu', dtype=torch.float32)
        self.register_buffer('singleton_fallbacks', torch.zeros((), dtype=torch.long, device='cpu'))

    def forward(self, rows):
        _need(isinstance(rows, torch.Tensor) and rows.ndim == 2, 'Gathered 2D rows required')
        _float_tensor(rows, (rows.shape[0], self.input_width))
        count = rows.shape[0]
        if count == 0:
            return rows.new_empty((0, 32))
        _need(self.bn.training == self.training and self.dropout.training == self.training,
              'MLP module modes must agree')
        counter = self.singleton_fallbacks if count == 1 else self.bn.num_batches_tracked
        if self.training:
            _need(int(counter) < torch.iinfo(torch.long).max, 'BN counter would overflow')
        output = F.elu(self.first(rows))
        output = self.dropout(output)
        output = F.elu(self.second(output))
        if self.training and count == 1:
            output = F.batch_norm(output, self.bn.running_mean, self.bn.running_var,
                self.bn.weight, self.bn.bias, training=False, momentum=0.0, eps=self.bn.eps)
            self.singleton_fallbacks.add_(1)
        else:
            output = self.bn(output)
        _float_tensor(output, (count, 32))
        return output


class GKTResearchModel(nn.Module):
    """Primary-equation candidate BN-D5 V1, chưa xác nhận author-code parity.

    Source/graph claims ở spec là bindings, không kiểm file hoặc cấp authority.
    Direct forward consume global torch CPU RNG như module dropout thông thường.
    initial_dropout_rng_state trả clone của actual post-init stream cho trainer.
    """

    def __init__(self, config, binding, graph, adjacency, *, spec):
        super().__init__()
        _need(type(config) is GKTKernelConfig and type(binding) is GKTBinding
              and type(graph) is GKTResearchGraphBinding and type(spec) is GKTResearchModelSpec,
              'Exact model config/binding/graph/spec types required')
        spec.__post_init__()
        graph.__post_init__()
        _need((config.num_nodes, config.state_dim, config.embedding_dim, config.message_dim,
               config.adjacency_kind, config.node_unit) == (28, 32, 32, 32, 'static', 'concept'),
              'Recipe29 static concept28/width32 required')
        _need(binding.node_ids == graph.node_ids and binding.node_unit == 'concept'
              and binding.domain == graph.domain_sha256
              and binding.vocabulary_sha256 == spec.vocabulary_sha256,
              'Domain/node order/vocabulary binding mismatch')
        _float_tensor(adjacency, (28, 28))
        _need(not adjacency.requires_grad, 'Expert graph must be fixed')
        expected = torch.zeros((28, 28), dtype=torch.float32, device='cpu')
        positions = {node: index for index, node in enumerate(graph.node_ids)}
        for parent, child in graph.edges:
            expected[positions[parent], positions[child]] = 1.0
        _need(torch.equal(adjacency, expected), 'Actual adjacency and declared directed edges differ')
        self.config, self.binding, self.graph, self.spec = config, binding, graph, spec
        with torch.device('cpu'):
            self._kernel = StaticGKTKernel(config, binding, adjacency)
        self.register_buffer('adjacency', adjacency.detach().clone())
        self.graph_sha256 = self._kernel.adjacency_sha256
        with torch.random.fork_rng(devices=[]), torch.device('cpu'):
            torch.random.default_generator.manual_seed(spec.initialization_seed)
            self.concept_embedding = nn.Embedding(28, 32, device='cpu', dtype=torch.float32)
            self.interaction_embedding = nn.Embedding(56, 32, device='cpu', dtype=torch.float32)
            self.self_mlp = _MaskedOutputMLP(64)
            self.out_mlp = _MaskedOutputMLP(128)
            self.in_mlp = _MaskedOutputMLP(128)
            self.erase = nn.Linear(32, 32, device='cpu', dtype=torch.float32)
            self.add = nn.Linear(32, 32, device='cpu', dtype=torch.float32)
            self.gru = ChoResetBeforeGRU(32, dtype=torch.float32)
            self.readout_weight = nn.Parameter(torch.empty(32, device='cpu', dtype=torch.float32))
            self.node_bias = nn.Parameter(torch.zeros(28, device='cpu', dtype=torch.float32))
            nn.init.normal_(self.readout_weight, std=32**-0.5)
            self._initial_dropout_rng_state = torch.get_rng_state().clone()
        self._parameter_shapes = tuple((name, tuple(value.shape)) for name, value in self.named_parameters())
        self.model_binding_sha256 = self._identity()

    @property
    def initial_dropout_rng_state(self):
        return self._initial_dropout_rng_state.clone()

    @property
    def normalization_counts(self):
        return {name: dict(training_updates=int(module.bn.num_batches_tracked),
                           singleton_fallbacks=int(module.singleton_fallbacks))
                for name, module in (('self', self.self_mlp), ('out', self.out_mlp), ('in', self.in_mlp))}

    def _identity(self):
        return _digest(dict(config=asdict(self.config), binding=asdict(self.binding),
            graph=asdict(self.graph), spec=asdict(self.spec), numerical=_NUMERICAL,
            adjacency_sha256=self.graph_sha256, parameter_shapes=self._parameter_shapes))

    def _bound(self, binding, graph_sha256):
        _need(binding == self.binding and graph_sha256 == self.graph_sha256
              and self._identity() == self.model_binding_sha256, 'Model/source/recipe binding mismatch')
        self._kernel._bound(binding, graph_sha256)
        _float_tensor(self.adjacency, (28, 28))
        _need(adjacency_sha256(self.adjacency) == graph_sha256, 'Registered adjacency changed')
        _need(tuple((name, tuple(value.shape)) for name, value in self.named_parameters())
              == self._parameter_shapes, 'Registered parameter geometry changed')
        for parameter in self.parameters():
            _float_tensor(parameter, parameter.shape)
        _need(all(module.training == self.training for module in self.modules()),
              'Research model module modes must agree')
        for module in (self.self_mlp, self.out_mlp, self.in_mlp):
            width = 64 if module is self.self_mlp else 128
            _need(type(module) is _MaskedOutputMLP and module.input_width == width
                  and type(module.first) is nn.Linear and type(module.second) is nn.Linear
                  and (module.first.in_features, module.first.out_features,
                       module.second.in_features, module.second.out_features) == (width, 32, 32, 32)
                  and type(module.dropout) is nn.Dropout and module.dropout.p == 0.5
                  and module.dropout.inplace is False and type(module.bn) is nn.BatchNorm1d
                  and module.bn.num_features == 32 and module.bn.eps == 1e-5
                  and module.bn.momentum == 0.1 and module.bn.affine is True
                  and module.bn.track_running_stats is True, 'MLP/BN/dropout recipe changed')
            _float_tensor(module.bn.running_mean, (32,))
            _float_tensor(module.bn.running_var, (32,))
            _need(bool((module.bn.running_var >= 0).all()), 'BN running variance must be nonnegative')
            for counter in (module.bn.num_batches_tracked, module.singleton_fallbacks):
                _integer_tensor(counter, ())
                _need(int(counter) >= 0, 'BN counters must be nonnegative')

    def _state(self, state, binding, graph_sha256):
        self._bound(binding, graph_sha256)
        _need(type(state) is GKTRecurrentState and state.binding == self.binding
              and state.graph_sha256 == graph_sha256
              and state.recipe_sha256 == self.model_binding_sha256, 'State binding mismatch')
        _need(isinstance(state.values, torch.Tensor) and state.values.ndim == 3
              and 1 <= state.values.shape[0] <= 4, 'Research learner batch must be1..4')
        batch = state.values.shape[0]
        _float_tensor(state.values, (batch, 28, 32))
        _integer_tensor(state.history_counts, (batch,))
        _need(bool((state.history_counts >= 0).all()), 'History counts must be nonnegative')
        return batch

    def initial_state(self, batch_size, *, binding, graph_sha256):
        self._bound(binding, graph_sha256)
        _need(type(batch_size) is int and 1 <= batch_size <= 4, 'Research learner batch must be1..4')
        return GKTRecurrentState(torch.zeros((batch_size, 28, 32), device='cpu', dtype=torch.float32),
            torch.zeros(batch_size, device='cpu', dtype=torch.long), self.binding,
            graph_sha256, self.model_binding_sha256)

    def predict(self, state, query_ids, *, binding, graph_sha256):
        batch = self._state(state, binding, graph_sha256)
        _integer_tensor(query_ids, (batch,))
        with torch.device('cpu'):
            output = self._kernel.readout(state.values, query_ids, self.readout_weight, self.node_bias,
                                         binding=binding, graph_sha256=graph_sha256)
        return GKTRecurrentReadout(output.logits, output.probabilities,
                                   state.history_counts.clone(), EVIDENCE_ROLE)

    def observe(self, state, answered_ids, responses, event_valid_mask, *, binding, graph_sha256):
        batch = self._state(state, binding, graph_sha256)
        _integer_tensor(answered_ids, (batch,))
        _integer_tensor(responses, (batch,))
        _need(isinstance(event_valid_mask, torch.Tensor) and event_valid_mask.shape == (batch,)
              and event_valid_mask.device.type == 'cpu' and event_valid_mask.dtype == torch.bool,
              'Explicit CPU boolean event mask required')
        valid = event_valid_mask
        ids, answers = answered_ids[valid], responses[valid]
        _need(bool(((ids >= 0) & (ids < 28)).all())
              and bool(((answers == 0) | (answers == 1)).all()), 'Known active node/binary answer required')
        _need(bool((state.history_counts[valid] < torch.iinfo(torch.long).max).all()),
              'History counter would overflow')
        if not bool(valid.any()):
            return state
        active_state = state.values[valid]
        with torch.device('cpu'):
            z = self._kernel.aggregate_after_observation(active_state, ids, answers,
                self.concept_embedding.weight, self.interaction_embedding.weight,
                binding=binding, graph_sha256=graph_sha256)
            count = ids.shape[0]
            observed = z[torch.arange(count, device='cpu'), ids]
            pairs = torch.cat((observed[:, None, :].expand(-1, 28, -1), z), dim=-1)
            nonself = torch.arange(28, device='cpu')[None, :] != ids[:, None]
            self_messages = self.self_mlp(observed)
            outgoing = pairs.new_zeros((count, 28, 32))
            incoming = pairs.new_zeros((count, 28, 32))
            outgoing[nonself] = self.out_mlp(pairs[nonself])
            incoming[nonself] = self.in_mlp(pairs[nonself])
            messages = self._kernel.combine_messages(ids, self_messages, outgoing, incoming,
                                                     binding=binding, graph_sha256=graph_sha256)
        erased = messages.values * (1 - torch.sigmoid(self.erase(messages.values)))
        added = torch.tanh(self.add(messages.values))
        proposed = self.gru(erased + added, active_state)
        _float_tensor(proposed, active_state.shape)
        active_values = torch.where(messages.support_mask[..., None], proposed, active_state)
        values = state.values.clone()
        values[valid] = active_values
        return GKTRecurrentState(values, state.history_counts + valid.long(), self.binding,
                                 graph_sha256, self.model_binding_sha256)

    def sequence(self, query_ids, responses, valid_mask, *, initial_state, binding, graph_sha256):
        self._bound(binding, graph_sha256)
        _need(isinstance(query_ids, torch.Tensor) and query_ids.ndim == 2
              and 1 <= query_ids.shape[0] <= 4 and query_ids.shape[1] <= 210,
              'Whole current-corpus sequence requires B1..4/T0..210, no truncation')
        _integer_tensor(query_ids, query_ids.shape)
        _integer_tensor(responses, query_ids.shape)
        _need(isinstance(valid_mask, torch.Tensor) and valid_mask.shape == query_ids.shape
              and valid_mask.device.type == 'cpu' and valid_mask.dtype == torch.bool,
              'Explicit CPU boolean sequence mask required')
        batch, steps = query_ids.shape
        active_ids, active_answers = query_ids[valid_mask], responses[valid_mask]
        _need(bool(((active_ids >= 0) & (active_ids < 28)).all())
              and bool(((active_answers == 0) | (active_answers == 1)).all()),
              'Whole sequence requires known active nodes and binary answers')
        if initial_state is not None:
            _need(self._state(initial_state, binding, graph_sha256) == batch,
                  'Sequence state batch mismatch')
            _need(bool((initial_state.history_counts
                        <= torch.iinfo(torch.long).max-valid_mask.sum(dim=1)).all()),
                  'Whole sequence history counter would overflow')
        state = (self.initial_state(batch, binding=binding, graph_sha256=graph_sha256)
                 if initial_state is None else initial_state)
        _need(self._state(state, binding, graph_sha256) == batch, 'Sequence state batch mismatch')
        logits, probabilities, counts = [], [], []
        for time in range(steps):
            valid = valid_mask[:, time]
            ids = torch.where(valid, query_ids[:, time], torch.zeros_like(query_ids[:, time]))
            output = self.predict(state, ids, binding=binding, graph_sha256=graph_sha256)
            logits.append(torch.where(valid, output.logits, torch.zeros_like(output.logits)))
            probabilities.append(torch.where(valid, output.probabilities, torch.zeros_like(output.probabilities)))
            counts.append(output.history_counts)
            state = self.observe(state, query_ids[:, time], responses[:, time], valid,
                                 binding=binding, graph_sha256=graph_sha256)
        empty = torch.zeros((batch, 0), device='cpu', dtype=torch.float32)
        return GKTRecurrentSequence(torch.stack(logits, 1) if steps else empty,
            torch.stack(probabilities, 1) if steps else empty.clone(), valid_mask.clone(),
            torch.stack(counts, 1) if steps else torch.zeros((batch, 0), device='cpu', dtype=torch.long),
            state, EVIDENCE_ROLE)

    def forward(self, query_ids, responses, valid_mask, *, initial_state, binding, graph_sha256):
        return self.sequence(query_ids, responses, valid_mask, initial_state=initial_state,
                             binding=binding, graph_sha256=graph_sha256)
