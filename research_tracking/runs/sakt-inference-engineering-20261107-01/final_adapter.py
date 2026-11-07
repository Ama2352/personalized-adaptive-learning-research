"""Inference SAKT đóng băng, chưa phải trainer hoặc fitted OnlineSession backend.

Caller khai báo đầy đủ geometry/first-target policy và metadata domain/vocab.
Checkpoint dùng raw PyTorch state_dict, không tạo format training mới. Hash và
metadata equality xác nhận identity, không chứng minh weights đã được fit.
"""

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path

import numpy as np
import torch

from knowledge_tracing.shared_kt import CausalSequenceInputs, StableVocabulary
from knowledge_tracing.simulator_bridge import (
    ItemQuery, Observation, SimulatorBank, identity_hash,
)
from .config import SAKTConfig
from .model import SAKTCore
from .tensors import collate_sequences


def _sha(value):
    if (not isinstance(value, str) or len(value) != 64
            or any(character not in '0123456789abcdef' for character in value)):
        raise ValueError('expected SHA-256 identity')


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('expected nonempty identifier')


@dataclass(frozen=True)
class SAKTInferenceSpec:
    """Conventions caller chọn, không là protocol S04/S05 được mặc định duyệt.

    context = số past interactions tối đa, query chiếm thêm một slot.
    Zero usable history sau OOV barrier cũng theo first_target_policy.
    """

    context: int
    window_policy: str
    position_policy: str
    first_target_policy: str
    padding_side: str
    batch_size: int
    device: str
    precision: str

    def __post_init__(self):
        if (type(self.context) is not int or self.context < 0
                or type(self.batch_size) is not int or self.batch_size < 1
                or self.window_policy != 'sliding_last_context'
                or self.position_policy != 'window_relative_interaction_rank'
                or self.first_target_policy not in {'query_only', 'unsupported'}
                or self.padding_side not in {'left', 'right'}
                or self.device != 'cpu' or self.precision != 'float32'):
            raise ValueError('invalid or unsupported explicit inference convention')


@dataclass(frozen=True)
class SAKTHistory:
    """History một learner; caller vẫn chịu trách nhiệm đúng nguồn observations."""

    learner_id: str
    observations: tuple[Observation, ...]

    def __post_init__(self):
        _text(self.learner_id)
        if (not isinstance(self.observations, tuple)
                or any(type(item) is not Observation or type(item.query) is not ItemQuery
                       for item in self.observations)):
            raise ValueError('history requires typed prior observations')


@dataclass(frozen=True)
class SAKTInferenceScore:
    probability: float | None
    support_reason: str
    learner_id: str
    source_row: int
    global_rank: int
    history_available: int
    history_used: int
    context_reset: bool
    has_history: bool
    weight_role: str
    checkpoint_sha256: str
    binding_sha256: str


def inference_identity(config: SAKTConfig, vocabulary: StableVocabulary,
                       bank: SimulatorBank, spec: SAKTInferenceSpec, *, weight_role: str) -> dict:
    """Metadata caller phải cung cấp/đối chiếu; không là training certificate."""
    if (type(config) is not SAKTConfig or type(vocabulary) is not StableVocabulary
            or type(bank) is not SimulatorBank or type(spec) is not SAKTInferenceSpec):
        raise ValueError('invalid inference binding types')
    values = vocabulary.values
    if (not isinstance(values, tuple) or not values
            or any(not isinstance(value, str) or not value.strip() for value in values)
            or values != tuple(sorted(set(values))) or len(values) != config.num_items
            or not set(values).issubset(bank.item_ids)):
        raise ValueError('vocabulary/config/domain mismatch')
    if config.max_length < spec.context + 1:
        raise ValueError('context plus query exceeds configured core geometry')
    if weight_role not in {'random_fixture', 'unverified_state'}:
        raise ValueError('selected/fitted provenance requires a trainer; unsupported weight role')
    source_directory = Path(__file__).resolve().parent
    return {
        'schema_version': 1,
        'model': 'sakt_paper_equation_single_block_frozen_inference',
        'config': asdict(config),
        'inference_spec': asdict(spec),
        'inference_domain': bank.identity,
        'vocabulary_sha256': identity_hash(list(values)),
        'weight_role': weight_role,
        'vocabulary_provenance': 'caller_declared; no trainer/split verification',
        'core_source_sha256': {
            name: hashlib.sha256((source_directory / name).read_bytes()).hexdigest()
            for name in ('config.py', 'model.py', 'tensors.py', 'adapter.py')
        },
    }


def _state_digest(model):
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode())
        digest.update(str((value.dtype, tuple(value.shape))).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


class FrozenSAKTAdapter:
    """CPU FP32 inference-only. predict không nhận labels, fit luôn từ chối.

    Không expose OnlineScore(kind='fitted') cho random/unverified weights.
    predict_details trả support rõ; predict ndarray từ chối nếu có unsupported
    targets, tránh vô tình chấm OOV/cold sentinel như finite predictions.
    """

    def __init__(self, model, vocabulary, bank, spec, *, checkpoint_sha256, identity):
        raise TypeError('use load_frozen_sakt for hash-bound state_dict loading')

    @classmethod
    def _loaded(cls, model, vocabulary, bank, spec, *, checkpoint_sha256, identity):
        self = object.__new__(cls)
        self._model, self._vocabulary, self._bank, self._spec = model, vocabulary, bank, spec
        self._checkpoint_sha256 = checkpoint_sha256
        self._identity = identity
        self._binding_sha256 = identity_hash(identity)
        self._state_sha256 = _state_digest(model)
        return self

    @property
    def binding(self):
        # Trả object mới để caller không sửa identity nội bộ qua metadata trả về.
        import json
        return json.loads(json.dumps(self._identity))

    def _assert_frozen(self):
        current = inference_identity(self._model.config, self._vocabulary, self._bank,
                                     self._spec, weight_role=self._identity['weight_role'])
        if (current != self._identity or self._model.training
                or any(parameter.requires_grad for parameter in self._model.parameters())
                or _state_digest(self._model) != self._state_sha256):
            raise ValueError('frozen model/config/vocabulary/domain/source binding changed')

    def fit(self, inputs, targets):
        raise NotImplementedError('inference only; SAKT trainer/selection is not implemented')

    def as_online_backend(self):
        raise NotImplementedError('fitted OnlineSession bridge requires selected-fit provenance and protocol')

    def _validate(self, inputs):
        if type(inputs) is not CausalSequenceInputs:
            raise ValueError('expected causal sequence inputs without current labels')
        n = len(inputs.item_ids)
        fields = (inputs.item_ids, inputs.timestamps, inputs.prior_responses, inputs.source_rows)
        if (any(not isinstance(field, np.ndarray) or field.shape != (n,)
                or not np.issubdtype(field.dtype, np.integer) for field in fields)
                or not isinstance(inputs.sequence_offsets, np.ndarray)
                or inputs.sequence_offsets.ndim != 1
                or not np.issubdtype(inputs.sequence_offsets.dtype, np.integer)
                or len(inputs.user_ids) != n
                or any(not isinstance(user, str) or not user.strip() for user in inputs.user_ids)
                or np.any(inputs.item_ids < -1) or np.any(inputs.item_ids >= len(self._vocabulary.values))
                or np.any(inputs.timestamps < 0) or np.any(inputs.source_rows < 1)
                or len(set(inputs.source_rows.tolist())) != n
                or (inputs.concept_ids is not None and np.shape(inputs.concept_ids) != (n,))):
            raise ValueError('invalid sequence dimensions, IDs, timestamps or source rows')
        offsets = inputs.sequence_offsets.tolist()
        if n == 0:
            if offsets != [0]:
                raise ValueError('invalid empty sequence offsets')
            return []
        if (len(offsets) < 2 or offsets[0] != 0 or offsets[-1] != n
                or any(left >= right for left, right in zip(offsets, offsets[1:]))):
            raise ValueError('invalid sequence offsets')
        segments, users = [], set()
        for start, stop in zip(offsets, offsets[1:]):
            user = inputs.user_ids[start]
            if (user in users or set(inputs.user_ids[start:stop]) != {user}
                    or inputs.prior_responses[start] != -1
                    or not np.isin(inputs.prior_responses[start + 1:stop], (0, 1)).all()):
                raise ValueError('learner segmentation or shifted prior responses invalid')
            order = list(zip(inputs.timestamps[start:stop].tolist(), inputs.source_rows[start:stop].tolist()))
            if any(left >= right for left, right in zip(order, order[1:])):
                raise ValueError('chronology violation; adapter never sorts inputs')
            users.add(user)
            segments.append((start, stop))
        return segments

    def _score_sequences(self, sequences, metadata):
        scores = [None] * len(metadata)
        active = []
        for index, (sequence, info) in enumerate(zip(sequences, metadata)):
            if info['support_reason'] in {'oov_item', 'cold_unsupported'}:
                scores[index] = SAKTInferenceScore(None, **info)
            else:
                active.append((index, sequence, info))
        with torch.inference_mode():
            for offset in range(0, len(active), self._spec.batch_size):
                block = active[offset:offset + self._spec.batch_size]
                batch = collate_sequences([entry[1] for entry in block], num_items=self._model.config.num_items,
                                          max_length=self._model.config.max_length,
                                          padding_side=self._spec.padding_side, device=self._spec.device)
                output = self._model(batch)
                for row, (index, sequence, info) in enumerate(block):
                    length = len(sequence.item_ids)
                    position = length - 1 if self._spec.padding_side == 'right' else batch.item_ids.shape[1] - 1
                    probability = float(output.probabilities[row, position])
                    if not np.isfinite(probability) or not 0 <= probability <= 1:
                        raise ValueError('invalid SAKT inference probability')
                    if bool(output.has_history[row, position]) != info['has_history']:
                        raise ValueError('core/adapter history geometry mismatch')
                    scores[index] = SAKTInferenceScore(probability, **info)
        self._assert_frozen()
        return tuple(scores)

    def _prepare(self, inputs, segment_start, index):
        rank = index - segment_start
        start = max(segment_start, index - self._spec.context)
        available = index - start
        barriers = np.flatnonzero(inputs.item_ids[start:index] == -1)
        if len(barriers):
            start += int(barriers[-1]) + 1
        used = index - start
        oov = inputs.item_ids[index] == -1
        reason = ('oov_item' if oov else 'known_history' if used else
                  'cold_query_only' if self._spec.first_target_policy == 'query_only' else 'cold_unsupported')
        info = {
            'support_reason': reason, 'learner_id': inputs.user_ids[index],
            'source_row': int(inputs.source_rows[index]), 'global_rank': rank,
            'history_available': available, 'history_used': 0 if oov else used,
            'context_reset': bool(len(barriers) or oov), 'has_history': bool(used and not oov),
            'weight_role': self._identity['weight_role'],
            'checkpoint_sha256': self._checkpoint_sha256, 'binding_sha256': self._binding_sha256,
        }
        sequence = None
        if reason not in {'oov_item', 'cold_unsupported'}:
            prior = inputs.prior_responses[start:index + 1].copy()
            prior[0] = -1  # Không kéo response bên ngoài declared context hoặc qua OOV barrier.
            length = index - start + 1
            sequence = CausalSequenceInputs(inputs.item_ids[start:index + 1].copy(),
                inputs.timestamps[start:index + 1].copy(), prior, inputs.source_rows[start:index + 1].copy(),
                np.asarray([0, length], dtype=np.int64), (inputs.user_ids[index],) * length)
        return sequence, info

    def predict_details(self, inputs: CausalSequenceInputs) -> tuple[SAKTInferenceScore, ...]:
        self._assert_frozen()
        segments = self._validate(inputs)
        prepared = [self._prepare(inputs, start, index) for start, stop in segments for index in range(start, stop)]
        return self._score_sequences([p[0] for p in prepared], [p[1] for p in prepared])

    def predict(self, inputs: CausalSequenceInputs) -> np.ndarray:
        scores = self.predict_details(inputs)
        if any(score.probability is None for score in scores):
            raise ValueError('unsupported targets; use predict_details and explicit coverage accounting')
        return np.asarray([score.probability for score in scores], dtype=np.float64)

    def query_many(self, history: SAKTHistory, queries: tuple[ItemQuery, ...], *,
                   learner_id: str) -> tuple[SAKTInferenceScore, ...]:
        self._assert_frozen()
        _text(learner_id)
        if (type(history) is not SAKTHistory or history.learner_id != learner_id
                or not isinstance(queries, tuple)):
            raise ValueError('history learner binding or query batch invalid')
        sequences, metadata = [], []
        lookup = {name: index for index, name in enumerate(self._vocabulary.values)}
        for query in queries:
            if type(query) is not ItemQuery:
                raise ValueError('query accepts item/time/source row only, no current outcome')
            events = [entry.query for entry in history.observations] + [query]
            if any(event.item_id not in self._bank.item_ids for event in events):
                raise ValueError('query/history outside bound simulator domain')
            n = len(events)
            inputs = CausalSequenceInputs(np.asarray([lookup.get(e.item_id, -1) for e in events], dtype=np.int64),
                np.asarray([e.timestamp for e in events], dtype=np.int64),
                np.asarray([-1, *[entry.correct for entry in history.observations]], dtype=np.int64),
                np.asarray([e.source_row for e in events], dtype=np.int64),
                np.asarray([0, n], dtype=np.int64), (learner_id,) * n)
            self._validate(inputs)
            sequence, info = self._prepare(inputs, 0, n - 1)
            sequences.append(sequence)
            metadata.append(info)
        return self._score_sequences(sequences, metadata)

    def query(self, history: SAKTHistory, query: ItemQuery, *, learner_id: str) -> SAKTInferenceScore:
        return self.query_many(history, (query,), learner_id=learner_id)[0]


def load_frozen_sakt(path: Path, config: SAKTConfig, vocabulary: StableVocabulary,
                     bank: SimulatorBank, spec: SAKTInferenceSpec, *, expected_sha256: str,
                     expected_identity: dict, weight_role: str, max_checkpoint_bytes: int) -> FrozenSAKTAdapter:
    """Strict raw state_dict load, hash trước/sau; không optimizer/training/format mới."""
    _sha(expected_sha256)
    required = inference_identity(config, vocabulary, bank, spec, weight_role=weight_role)
    if expected_identity != required:
        raise ValueError('checkpoint config/vocabulary/domain/geometry/source identity mismatch')
    path = Path(path)
    if (type(max_checkpoint_bytes) is not int or max_checkpoint_bytes < 1
            or not 0 < path.stat().st_size <= max_checkpoint_bytes):
        raise ValueError('checkpoint byte budget exceeded')
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError('checkpoint SHA-256 mismatch')
    state = torch.load(path, map_location='cpu', weights_only=True)
    if (not isinstance(state, dict) or not state
            or any(not isinstance(name, str) or type(value) is not torch.Tensor
                   or value.device.type != 'cpu' or value.dtype != torch.float32
                   or not torch.isfinite(value).all() for name, value in state.items())):
        raise ValueError('checkpoint must be a finite CPU FP32 raw state_dict')
    with torch.random.fork_rng(devices=[]), torch.device('cpu'):
        model = SAKTCore(config).to(dtype=torch.float32)
        model.load_state_dict(state, strict=True)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError('checkpoint changed during loading')
    model.eval().requires_grad_(False)
    return FrozenSAKTAdapter._loaded(model, vocabulary, bank, spec,
                                     checkpoint_sha256=expected_sha256, identity=required)
