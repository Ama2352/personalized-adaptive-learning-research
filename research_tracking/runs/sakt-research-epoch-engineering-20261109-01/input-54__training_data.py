"""Dữ liệu in-memory synthetic, train-only vocab và sliding một target mỗi window."""

from dataclasses import asdict, dataclass, replace
import hashlib
import json

import numpy as np

from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.types import LearnerEvents
from knowledge_tracing.akt.windows import iter_window_slices, slice_causal_inputs
from knowledge_tracing.shared_kt import CausalSequenceInputs, StableVocabulary


ENGINEERING_ROLE = 'synthetic_trained_engineering_only'
MAX_SYNTHETIC_TARGETS = 256


def identity_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class SAKTDataRecipe:
    context: int
    padding_side: str
    first_target_policy: str
    window_policy: str
    position_policy: str

    def __post_init__(self):
        if (type(self.context) is not int or self.context < 0
                or self.padding_side not in {'left', 'right'}
                or self.first_target_policy not in {'query_only', 'unsupported'}
                or self.window_policy != 'sliding_last_context'
                or self.position_policy != 'window_relative_interaction_rank'):
            raise ValueError('explicit supported SAKT geometry and cold policy required')


@dataclass(frozen=True)
class SAKTTarget:
    learner_id: str
    source_row: int
    item: str
    timestamp: int
    global_rank: int
    target: int
    reason: str
    inputs: CausalSequenceInputs | None
    history_available: int
    history_used: int
    context_reset: bool

    @property
    def eligible(self):
        return self.reason in {'known_history', 'cold_query_only'}


def _target_payload(record):
    inputs = record.inputs
    value = {name: getattr(record, name) for name in (
        'learner_id', 'source_row', 'item', 'timestamp', 'global_rank', 'target',
        'reason', 'history_available', 'history_used', 'context_reset')}
    value['inputs'] = None if inputs is None else {
        'item_ids': inputs.item_ids.tolist(), 'timestamps': inputs.timestamps.tolist(),
        'prior_responses': inputs.prior_responses.tolist(), 'source_rows': inputs.source_rows.tolist(),
        'sequence_offsets': inputs.sequence_offsets.tolist(), 'user_ids': list(inputs.user_ids)}
    return value


@dataclass(frozen=True)
class SAKTTrainingData:
    domain: str
    recipe: SAKTDataRecipe
    vocabulary: StableVocabulary
    train_support_students: dict[str, int]
    train: tuple[SAKTTarget, ...]
    validation: tuple[SAKTTarget, ...]
    input_identity: dict
    content_sha256: str
    role: str = ENGINEERING_ROLE

    def payload(self):
        return {'domain': self.domain, 'recipe': asdict(self.recipe),
                'vocabulary': list(self.vocabulary.values),
                'train_support_students': self.train_support_students,
                'train': [_target_payload(x) for x in self.train],
                'validation': [_target_payload(x) for x in self.validation],
                'input_identity': self.input_identity, 'role': self.role}

    def assert_integrity(self):
        if self.role != ENGINEERING_ROLE or identity_hash(self.payload()) != self.content_sha256:
            raise ValueError('prepared synthetic data or policy binding changed')

    @property
    def identity(self):
        self.assert_integrity()
        return {'role': self.role, 'domain': self.domain, 'recipe': asdict(self.recipe),
                'vocabulary': list(self.vocabulary.values),
                'vocabulary_sha256': identity_hash(list(self.vocabulary.values)),
                'content_sha256': self.content_sha256, 'input_identity': self.input_identity}


def _validate_learners(learners, role):
    if not isinstance(learners, tuple) or not learners:
        raise ValueError('nonempty tuple of explicit learner records required')
    users, rows = set(), set()
    for learner in learners:
        if (type(learner) is not LearnerEvents or not isinstance(learner.user_id, str)
                or not learner.user_id.strip() or learner.user_id in users
                or type(learner.fold) is not int or learner.fold not in range(5)
                or not isinstance(learner.events, tuple) or not learner.events):
            raise ValueError('invalid or duplicate learner identity')
        users.add(learner.user_id)
        previous = None
        for event in learner.events:
            if (event.user_id != learner.user_id or event.fold != learner.fold
                    or not isinstance(event.exercise, str) or not event.exercise.strip()
                    or type(event.time_done) is not int or event.time_done < 0
                    or type(event.source_row) is not int or event.source_row < 1
                    or type(event.correct) is not int or event.correct not in (0, 1)
                    or event.source_row in rows):
                raise ValueError('invalid event identity/target/source row')
            key = (event.time_done, event.source_row)
            if previous is not None and key <= previous:
                raise ValueError('chronology must already be ordered; no implicit sorting')
            previous = key
            rows.add(event.source_row)
    return users, rows


def _prepare_targets(learners, vocabulary, recipe):
    lookup = {item: index for index, item in enumerate(vocabulary.values)}
    output = []
    for learner in learners:
        events = learner.events
        ids = np.asarray([lookup.get(e.exercise, -1) for e in events], dtype=np.int64)
        labels = np.asarray([e.correct for e in events], dtype=np.int8)
        prior = np.full(len(events), -1, dtype=np.int8)
        prior[1:] = labels[:-1]
        causal = CausalSequenceInputs(ids, np.asarray([e.time_done for e in events], dtype=np.int64),
                                      prior, np.asarray([e.source_row for e in events], dtype=np.int64),
                                      np.asarray([0, len(events)], dtype=np.int64), (learner.user_id,) * len(events))
        # target_block=1 khớp adapter sliding, không mang block100 geometry vào SAKT.
        for window in iter_window_slices(ids, causal.sequence_offsets, context=recipe.context, target_block=1):
            index = window.target_start
            event = events[index]
            available = min(index, recipe.context)
            if window.unseen:
                sequence, used, reset, reason = None, 0, True, 'oov_item'
            else:
                sliced = slice_causal_inputs(causal, window)
                sequence = sliced.inputs
                used = len(sequence.item_ids) - 1
                reset = window.barrier_applied
                reason = ('known_history' if used else 'cold_query_only'
                          if recipe.first_target_policy == 'query_only' else 'cold_unsupported')
                for array in (sequence.item_ids, sequence.timestamps, sequence.prior_responses,
                              sequence.source_rows, sequence.sequence_offsets):
                    array.flags.writeable = False
            output.append(SAKTTarget(learner.user_id, event.source_row, event.exercise, event.time_done,
                                     index, event.correct, reason, sequence, available, used, bool(reset)))
    return tuple(output)


def prepare_sakt_training_data(train_learners, validation_learners, *, domain: str,
                               recipe: SAKTDataRecipe, synthetic_only: bool):
    """Caller declaration synthetic, không xác thực nguồn thật; không file/data loader.

    Hard ceiling256 targets là engineering scope, không default benchmark protocol.
    """
    if synthetic_only is not True or not isinstance(domain, str) or not domain.strip() or type(recipe) is not SAKTDataRecipe:
        raise ValueError('explicit synthetic-only domain and recipe required')
    train_users, train_rows = _validate_learners(train_learners, 'train')
    val_users, val_rows = _validate_learners(validation_learners, 'validation')
    if train_users & val_users or train_rows & val_rows:
        raise ValueError('train and validation learners/source rows must be disjoint')
    if len(train_rows) + len(val_rows) > MAX_SYNTHETIC_TARGETS:
        raise ValueError('synthetic engineering batch exceeds 256 targets')
    encoding = fit_vocabulary(train_learners)
    train = _prepare_targets(train_learners, encoding.vocabulary, recipe)
    validation = _prepare_targets(validation_learners, encoding.vocabulary, recipe)
    if not any(x.eligible for x in train):
        raise ValueError('training population has no eligible targets under declared cold policy')
    origin = {'train_learners': sorted(train_users), 'validation_learners': sorted(val_users),
              'train_source_rows': sorted(train_rows), 'validation_source_rows': sorted(val_rows),
              'train_events_sha256': identity_hash([asdict(x) for x in train_learners]),
              'validation_events_sha256': identity_hash([asdict(x) for x in validation_learners]),
              'synthetic_origin': 'caller_declared_in_memory; no raw dataset loader', 'target_block': 1}
    data = SAKTTrainingData(domain, recipe, encoding.vocabulary, dict(encoding.train_support_students),
                            train, validation, origin, '')
    return replace(data, content_sha256=identity_hash(data.payload()))
