"""AKT frozen checkpoint → next-item query, giữ global anchors và OOV barriers.

Module không train, chọn threshold hoặc truy cập latent learner state.
"""

from pathlib import Path

import numpy as np
import torch

from knowledge_tracing.shared_kt import CausalSequenceInputs, StableVocabulary
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, OnlineScore, SimulatorBank, identity_hash
from .checkpoint import load_checkpoint
from .config import AKTConfig, validate_config
from .encoding import ExerciseEncoding, encode_exercises
from .model import AKTAdapter
from .provenance import sha256_file
from .windows import iter_window_slices, slice_causal_inputs


RECIPE_FIELDS = ('source_commit', 'd_model', 'heads', 'blocks', 'd_ff', 'final_fc', 'dropout',
                 'kq_same', 'separate_qa', 'n_pid', 'graph', 'device', 'context', 'target_block', 'max_length')


def inference_recipe(config: AKTConfig) -> dict:
    return {'schema_version': 1, 'model': 'upstream_akt_nonrasch',
            **{name: getattr(config, name) for name in RECIPE_FIELDS}}


def simulator_model_identity(config: AKTConfig, bank: SimulatorBank, encoding: ExerciseEncoding) -> dict:
    values = encoding.vocabulary.values
    if not values or not set(values).issubset(bank.item_ids):
        raise ValueError('trained vocabulary is outside simulator item bank')
    return {'training_domain': bank.identity, 'inference_recipe': inference_recipe(config),
            'vocabulary_sha256': identity_hash(list(values))}


class AKTOnlineBackend:
    """Chỉ tạo qua checkpoint loader đã kiểm SHA/domain/recipe/encoding.

    Không migrate Junyi weights bằng cách đổi indices. Mỗi backend chia sẻ
    frozen weights giữa sessions; lịch sử nằm ở OnlineSession, không ở model.
    """

    def __init__(self, adapter: AKTAdapter, bank: SimulatorBank, *, checkpoint_id: str,
                 checkpoint_identity: dict):
        required = simulator_model_identity(adapter.config, bank, adapter.encoding)
        if any(checkpoint_identity.get(key) != value for key, value in required.items()):
            raise ValueError('checkpoint simulator domain, recipe or vocabulary mismatch')
        if len(checkpoint_id) != 64 or any(value not in '0123456789abcdef' for value in checkpoint_id):
            raise ValueError('invalid checkpoint SHA-256')
        self._adapter, self._bank = adapter, bank
        self._checkpoint_id = checkpoint_id
        self._recipe = inference_recipe(adapter.config)
        self._vocabulary = tuple(adapter.encoding.vocabulary.values)
        self._parameter_versions = tuple((name, id(parameter), parameter._version)
            for name, parameter in adapter.native.named_parameters())

    @property
    def model_id(self):
        return self._checkpoint_id

    @property
    def domain(self):
        return self._bank.identity

    def _prepare_query(self, history: tuple[Observation, ...], query: ItemQuery, *, learner_id: str):
        if (inference_recipe(self._adapter.config) != self._recipe
                or tuple(self._adapter.encoding.vocabulary.values) != self._vocabulary
                or self._parameter_versions != tuple((name, id(parameter), parameter._version)
                    for name, parameter in self._adapter.native.named_parameters())):
            raise ValueError('frozen inference model changed during online use')
        if not isinstance(query, ItemQuery) or not learner_id or query.item_id not in self._bank.item_ids:
            raise ValueError('invalid next-item query or simulator domain')
        # Valider cả direct backend caller, không chỉ session wrapper.
        previous = None
        rows = set()
        if any(not isinstance(item, Observation) for item in history):
            raise ValueError('invalid observation history')
        all_queries = [item.query for item in history] + [query]
        for item in all_queries:
            if item.item_id not in self._bank.item_ids:
                raise ValueError('invalid or cross-domain observation')
            key = item.timestamp, item.source_row
            if item.source_row in rows or (previous is not None and key <= previous):
                raise ValueError('online observation chronology violation')
            rows.add(item.source_row)
            previous = key
        ids = encode_exercises([item.item_id for item in all_queries], self._adapter.encoding)
        rank = len(history)
        if ids[-1] == -1:
            block_start = (rank // self._adapter.config.target_block) * self._adapter.config.target_block
            base = max(0, block_start-self._adapter.config.context)
            return OnlineScore(None, 'unseen_item', rank-base, 0, True, rank)
        prior = np.asarray([-1] + [item.correct for item in history], dtype=np.int8)
        inputs = CausalSequenceInputs(ids, np.asarray([item.timestamp for item in all_queries], dtype=np.int64),
            prior, np.asarray([item.source_row for item in all_queries], dtype=np.int64),
            np.asarray([0, len(ids)], dtype=np.int64), tuple(learner_id for _ in ids))
        config = self._adapter.config
        # Không re-anchor lịch sử đã cắt. Window cuối được dựng bằng đúng offline geometry.
        geometry = None
        for candidate in iter_window_slices(ids, inputs.sequence_offsets, context=config.context,
                                             target_block=config.target_block):
            if candidate.stop == len(ids):
                geometry = candidate
        if geometry is None or geometry.unseen:
            raise ValueError('missing supported next-item window')
        window = slice_causal_inputs(inputs, geometry)
        return window

    def predict_many(self, history: tuple[Observation, ...], queries: tuple[ItemQuery, ...], *,
                     learner_id: str) -> tuple[OnlineScore, ...]:
        prepared = [self._prepare_query(history, query, learner_id=learner_id) for query in queries]
        windows = [entry for entry in prepared if not isinstance(entry, OnlineScore)]
        values = iter(self._adapter.predict_windows(windows))
        results = []
        for entry in prepared:
            if isinstance(entry, OnlineScore):
                results.append(entry)
            else:
                prediction = next(values)
                results.append(OnlineScore(float(prediction[-1]),'fitted',int(entry.history_available[-1]),
                    int(entry.history_used[-1]),bool(entry.context_reset[-1]),len(history)))
        return tuple(results)

    def predict_next(self, history: tuple[Observation, ...], query: ItemQuery, *, learner_id: str) -> OnlineScore:
        return self.predict_many(history,(query,),learner_id=learner_id)[0]


def load_online_akt(path: Path, config: AKTConfig, bank: SimulatorBank, *,
                    expected_sha256: str, expected_identity: dict) -> AKTOnlineBackend:
    """Chỉ complete checkpoint, same recipe/domain; không chạy training hoặc selection."""
    validate_config(config)
    path = Path(path)
    if sha256_file(path) != expected_sha256:
        raise ValueError('online checkpoint SHA-256 mismatch')
    if (expected_identity.get('training_domain') != bank.identity
            or expected_identity.get('inference_recipe') != inference_recipe(config)):
        raise ValueError('online checkpoint domain or inference recipe mismatch')
    payload = load_checkpoint(path, expected_identity=expected_identity, device='cpu')
    if payload['progress'].get('role') in {'selection_recovery_v1', 'refit_recovery_v1'}:
        raise ValueError('recovery snapshot is not a selected inference checkpoint')
    values, support = payload['encoding']['values'], payload['encoding']['train_support_students']
    if (not values or values != sorted(set(values)) or set(values) != set(support)
            or any(type(support[key]) is not int or support[key] < 1 for key in values)):
        raise ValueError('invalid online checkpoint vocabulary')
    encoding = ExerciseEncoding(StableVocabulary(tuple(values)), dict(support))
    required = simulator_model_identity(config, bank, encoding)
    if any(expected_identity.get(key) != value for key, value in required.items()):
        raise ValueError('online checkpoint vocabulary identity mismatch')
    if sha256_file(path) != expected_sha256:
        raise ValueError('online checkpoint changed during load')
    # Khởi tạo container model không được làm lệch random stream của simulator.
    with torch.random.fork_rng(devices=[] if config.device == 'cpu' else [torch.cuda.current_device()]):
        adapter = AKTAdapter(config, encoding)
        adapter.native.load_state_dict(payload['model_state_dict'])
    return AKTOnlineBackend(adapter, bank, checkpoint_id=expected_sha256, checkpoint_identity=payload['identity'])
