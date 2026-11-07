"""Hợp đồng online KT: chỉ quan sát response sau predict, không nhận latent oracle.

Không chọn mastery threshold, calibration hoặc thay selector lịch sử. Reference
score là correctness trên item bank khai báo, không phải xác suất knowledge.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from numbers import Real
from typing import Protocol
import uuid


def identity_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def _identifier(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('identifier must be a nonempty string')


@dataclass(frozen=True)
class SimulatorItem:
    item_id: str
    concept_id: str
    difficulty: float

    def __post_init__(self):
        _identifier(self.item_id)
        _identifier(self.concept_id)
        if (isinstance(self.difficulty, bool) or not isinstance(self.difficulty, Real)
                or not math.isfinite(self.difficulty)):
            raise ValueError('invalid item difficulty')
        object.__setattr__(self, 'difficulty', float(self.difficulty))


@dataclass(frozen=True)
class SimulatorBank:
    environment_id: str
    items: tuple[SimulatorItem, ...]

    def __post_init__(self):
        _identifier(self.environment_id)
        if (not self.items or any(not isinstance(item, SimulatorItem) for item in self.items)
                or len({item.item_id for item in self.items}) != len(self.items)):
            raise ValueError('invalid or duplicate simulator items')
        object.__setattr__(self, 'items', tuple(sorted(self.items, key=lambda item: item.item_id)))

    @property
    def identity(self):
        return {'schema_version': 1, 'environment_id': self.environment_id, 'input_unit': 'item_id',
                'item_bank_sha256': identity_hash([asdict(item) for item in self.items])}

    @property
    def item_ids(self):
        return tuple(item.item_id for item in self.items)


@dataclass(frozen=True)
class ItemQuery:
    item_id: str
    timestamp: int
    source_row: int

    def __post_init__(self):
        _identifier(self.item_id)
        if (type(self.timestamp) is not int or self.timestamp < 0
                or type(self.source_row) is not int or self.source_row < 1):
            raise ValueError('invalid query time or source row')


@dataclass(frozen=True)
class Observation:
    query: ItemQuery
    correct: int

    def __post_init__(self):
        if not isinstance(self.query, ItemQuery) or type(self.correct) is not int or self.correct not in (0, 1):
            raise ValueError('observation must contain a query and binary outcome')


@dataclass(frozen=True)
class OnlineScore:
    probability: float | None
    prediction_kind: str
    history_available: int
    history_used: int
    context_reset: bool
    global_rank: int

    def __post_init__(self):
        if self.prediction_kind not in {'fitted', 'unseen_item'}:
            raise ValueError('invalid online prediction kind')
        if self.prediction_kind == 'unseen_item':
            if self.probability is not None:
                raise ValueError('unseen item cannot have a fitted probability')
        elif (self.probability is None or isinstance(self.probability, bool) or not isinstance(self.probability, Real)
              or not math.isfinite(self.probability) or not 0 <= self.probability <= 1):
            raise ValueError('invalid online probability')
        if self.probability is not None:
            object.__setattr__(self, 'probability', float(self.probability))
        if (any(type(value) is not int or value < 0 for value in
                (self.history_available, self.history_used, self.global_rank))
                or self.history_used > self.history_available or type(self.context_reset) is not bool):
            raise ValueError('invalid online history accounting')


class OnlineBackend(Protocol):
    domain: dict
    model_id: str

    def predict_next(self, history: tuple[Observation, ...], query: ItemQuery, *, learner_id: str) -> OnlineScore: ...


@dataclass(frozen=True)
class PredictionTicket:
    nonce: str
    session_key: str
    revision: int
    history_sha256: str
    query: ItemQuery
    score: OnlineScore


class OnlineSession:
    """Một learner; query không là interaction, observe không train weights.

    Backend phải frozen trong suốt session. Không sử dụng đồng thời với training
    trên cùng model object. Registry tickets bị xóa sau observe/reset/restore.
    """

    def __init__(self, backend: OnlineBackend, bank: SimulatorBank, *, learner_id: str,
                 max_events: int, max_pending_queries: int = 1024):
        _identifier(learner_id)
        _identifier(backend.model_id)
        if backend.domain != bank.identity:
            raise ValueError('model and simulator training domain mismatch')
        if any(type(value) is not int or value < 1 for value in (max_events, max_pending_queries)):
            raise ValueError('session requires explicit positive budgets')
        self.backend, self.bank, self.learner_id = backend, bank, learner_id
        self._model_id = backend.model_id
        self.max_events, self.max_pending_queries = max_events, max_pending_queries
        self._history: tuple[Observation, ...] = ()
        self._session_key = uuid.uuid4().hex
        self._revision = 0
        self._issued = {}

    @property
    def history(self):
        return self._history

    @property
    def history_sha256(self):
        if self.backend.model_id != self._model_id or self.backend.domain != self.bank.identity:
            raise ValueError('backend binding changed during session')
        return identity_hash({'domain': self.bank.identity, 'model_id': self.backend.model_id,
                              'learner_id': self.learner_id,
                              'observations': [asdict(item) for item in self._history]})

    def _check_query(self, query, history):
        if not isinstance(query, ItemQuery) or query.item_id not in self.bank.item_ids:
            raise ValueError('query item is outside simulator bank')
        if any(item.query.source_row == query.source_row for item in history):
            raise ValueError('duplicate observation source row')
        if history and (query.timestamp, query.source_row) <= (
                history[-1].query.timestamp, history[-1].query.source_row):
            raise ValueError('query chronology violation')

    def probe(self, query: ItemQuery) -> OnlineScore:
        self._check_query(query, self._history)
        if self.backend.domain != self.bank.identity or self.backend.model_id != self._model_id:
            raise ValueError('backend binding changed during session')
        score = self.backend.predict_next(self._history, query, learner_id=self.learner_id)
        if not isinstance(score, OnlineScore) or score.global_rank != len(self._history):
            raise ValueError('backend returned inconsistent online score')
        return score

    def predict(self, query: ItemQuery) -> PredictionTicket:
        if len(self._issued) >= self.max_pending_queries:
            raise ValueError('pending query budget exhausted')
        score = self.probe(query)
        ticket = PredictionTicket(uuid.uuid4().hex, self._session_key, self._revision,
                                  self.history_sha256, query, score)
        self._issued[ticket.nonce] = ticket
        return ticket

    def observe(self, ticket: PredictionTicket, correct: int):
        if (not isinstance(ticket, PredictionTicket) or ticket.session_key != self._session_key
                or ticket.revision != self._revision or self._issued.get(ticket.nonce) != ticket
                or ticket.history_sha256 != self.history_sha256):
            raise ValueError('foreign, stale or altered prediction ticket')
        observation = Observation(ticket.query, correct)
        if len(self._history) >= self.max_events:
            raise ValueError('session observation budget exhausted')
        self._check_query(ticket.query, self._history)
        self._history += (observation,)
        self._revision += 1
        self._issued.clear()

    def reset(self):
        self._history = ()
        self._revision += 1
        self._issued.clear()

    def snapshot(self):
        return {'schema_version': 1, 'domain': self.bank.identity, 'model_id': self.backend.model_id,
                'learner_id': self.learner_id, 'max_events': self.max_events,
                'history': [asdict(item) for item in self._history], 'history_sha256': self.history_sha256}

    def restore(self, snapshot):
        if (not isinstance(snapshot, dict) or set(snapshot) != set(self.snapshot())
                or snapshot['schema_version'] != 1 or snapshot['domain'] != self.bank.identity
                or snapshot['model_id'] != self.backend.model_id or snapshot['learner_id'] != self.learner_id
                or snapshot['max_events'] != self.max_events or not isinstance(snapshot['history'], list)
                or len(snapshot['history']) > self.max_events):
            raise ValueError('snapshot domain, learner or budget mismatch')
        history = ()
        for value in snapshot['history']:
            if not isinstance(value, dict) or set(value) != {'query', 'correct'}:
                raise ValueError('invalid observation snapshot schema')
            observation = Observation(ItemQuery(**value['query']), value['correct'])
            self._check_query(observation.query, history)
            history += (observation,)
        digest = identity_hash({'domain': self.bank.identity, 'model_id': self.backend.model_id,
                                'learner_id': self.learner_id, 'observations': [asdict(item) for item in history]})
        if digest != snapshot['history_sha256']:
            raise ValueError('snapshot history hash mismatch')
        self._history = history
        self._revision += 1
        self._issued.clear()


@dataclass(frozen=True)
class ReferenceSet:
    concept_id: str
    item_weights: tuple[tuple[str, float], ...]

    def __post_init__(self):
        _identifier(self.concept_id)
        if (not self.item_weights or len({item for item, _ in self.item_weights}) != len(self.item_weights)
                or any(not isinstance(item, str) or not item or isinstance(weight, bool)
                       or not math.isfinite(weight) or weight <= 0 for item, weight in self.item_weights)
                or not math.isclose(sum(weight for _, weight in self.item_weights), 1, rel_tol=0, abs_tol=1e-12)):
            raise ValueError('invalid or unnormalized reference weights')
        object.__setattr__(self, 'item_weights', tuple(sorted((item, float(weight))
                                                            for item, weight in self.item_weights)))


def probe_references(session: OnlineSession, references: tuple[ReferenceSet, ...], *,
                     timestamp: int, source_row: int) -> dict:
    if not references or len({entry.concept_id for entry in references}) != len(references):
        raise ValueError('invalid or duplicate reference concept')
    mapping = {item.item_id: item.concept_id for item in session.bank.items}
    for entry in references:
        if any(mapping.get(item) != entry.concept_id for item, _ in entry.item_weights):
            raise ValueError('reference item/concept mismatch')
    before = session.history_sha256
    scores = {}
    for entry in references:
        values = {item: session.probe(ItemQuery(item, timestamp, source_row)).probability
                  for item, _ in entry.item_weights}
        missing = tuple(item for item, value in values.items() if value is None)
        scores[entry.concept_id] = {'score_kind': 'mean_reference_correctness',
            'score': None if missing else sum(weight * values[item] for item, weight in entry.item_weights),
            'expected_items': len(values), 'supported_items': len(values)-len(missing),
            'missing_items': missing, 'probabilities': values}
    if session.history_sha256 != before:
        raise ValueError('reference probe modified learner history')
    return {'history_sha256': before, 'reference_sha256': identity_hash([asdict(entry) for entry in references]),
            'scores': scores, 'semantics': 'uncalibrated reference correctness; no mastery decision'}
