"""Adapter dữ liệu simulator role-aware, không giả fold Junyi.

Chỉ chuẩn bị train/selection windows. Không fit NN, chọn epoch/calibrator,
refit hoặc mở final; các bước đó cần runner/protocol riêng đã được duyệt.
"""

from collections import Counter
from dataclasses import dataclass

import numpy as np

from knowledge_tracing.shared_kt import CausalSequenceInputs, StableVocabulary
from knowledge_tracing.simulator_bridge import ItemQuery, SimulatorBank, identity_hash
from knowledge_tracing.simulator_data import ObservableTrajectory, SimulatorSplitPlan, validate_role_shard
from .encoding import ExerciseEncoding, encode_exercises
from .types import TrainingWindow
from .windows import iter_window_slices, slice_causal_inputs


@dataclass(frozen=True)
class SimulatorShard:
    plan: SimulatorSplitPlan
    bank: SimulatorBank
    role: str
    max_events_per_learner: int
    trajectories: tuple[ObservableTrajectory, ...]

    def __post_init__(self):
        rows = tuple(self.trajectories)
        if any(type(row) is not ObservableTrajectory for row in rows):
            raise ValueError('simulator shard requires exact observable schema')
        validate_role_shard(rows, plan=self.plan, bank=self.bank, role=self.role,
                            max_events_per_learner=self.max_events_per_learner)
        object.__setattr__(self, 'trajectories', tuple(sorted(rows, key=lambda t: t.learner_id)))

    @property
    def audit(self):
        return validate_role_shard(self.trajectories, plan=self.plan, bank=self.bank, role=self.role,
                                    max_events_per_learner=self.max_events_per_learner)

    @property
    def identity(self):
        return identity_hash({'schema_version': 1, 'audit': self.audit,
                              'max_events_per_learner': self.max_events_per_learner})


@dataclass(frozen=True)
class SimulatorEncoding:
    plan_sha256: str
    domain_sha256: str
    train_shard_sha256: str
    train_learners: int
    support: tuple[tuple[str, int], ...]

    def __post_init__(self):
        for value in (self.plan_sha256, self.domain_sha256, self.train_shard_sha256):
            if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('invalid simulator encoding binding')
        support = tuple(self.support)
        if (type(self.train_learners) is not int or self.train_learners < 1 or not support
                or any(not isinstance(item, str) or not item or type(count) is not int
                       or not 1 <= count <= self.train_learners for item, count in support)
                or len({item for item, _ in support}) != len(support)):
            raise ValueError('invalid train-only simulator support')
        object.__setattr__(self, 'support', tuple(sorted((item, count) for item, count in support)))

    @property
    def identity(self):
        return identity_hash({'schema_version': 1, 'plan': self.plan_sha256, 'domain': self.domain_sha256,
            'train_shard': self.train_shard_sha256, 'train_learners': self.train_learners, 'support': self.support})

    def exercise_encoding(self):
        # Tạo fresh support dict để caller không sửa binding đã fit.
        return ExerciseEncoding(StableVocabulary(tuple(item for item, _ in self.support)), dict(self.support))


def fit_simulator_encoding(train: SimulatorShard):
    if type(train) is not SimulatorShard or train.role != 'train':
        raise ValueError('simulator vocabulary may only fit train shard')
    support = Counter()
    for trajectory in train.trajectories:
        support.update({o.query.item_id for o in trajectory.observations})
    return SimulatorEncoding(train.plan.identity, identity_hash(train.bank.identity), train.identity,
                             len(train.trajectories), tuple(support.items()))


@dataclass(frozen=True)
class SimulatorTarget:
    learner_id: str
    query: ItemQuery
    correct: int
    global_rank: int
    trained_item: bool


@dataclass(frozen=True)
class SimulatorUnseenQuery:
    learner_id: str
    query: ItemQuery
    global_rank: int


def _check_scope(shard, encoding, *, training):
    if type(shard) is not SimulatorShard or type(encoding) is not SimulatorEncoding or type(training) is not bool:
        raise ValueError('invalid simulator window scope')
    if shard.role not in {'train', 'selection'} or (training and shard.role != 'train'):
        raise ValueError('only train optimization and train/selection prediction are supported; no calibration/refit/final')
    if encoding.plan_sha256 != shard.plan.identity or encoding.domain_sha256 != identity_hash(shard.bank.identity):
        raise ValueError('simulator encoding plan/domain mismatch')
    if not {item for item, _ in encoding.support}.issubset(shard.bank.item_ids):
        raise ValueError('simulator encoding vocabulary outside bank')
    if shard.role == 'train' and encoding.train_shard_sha256 != shard.identity:
        raise ValueError('train data changed after vocabulary fit')


def iter_simulator_windows(shard: SimulatorShard, encoding: SimulatorEncoding, *, context=100,
                           target_block=100, training: bool):
    """Reuse AKT window geometry, không cần KTEvent/LearnerEvents.fold.

    Prediction trả WindowInputs hoặc SimulatorUnseenQuery OOV. Labels ở scoring_targets
riêng; chỉ TrainingWindow mới chứa unshifted targets dùng optimize.
"""
    _check_scope(shard, encoding, training=training)
    if type(context) is not int or context < 0 or type(target_block) is not int or target_block < 1:
        raise ValueError('invalid simulator window geometry')
    exercise_encoding = encoding.exercise_encoding()
    for trajectory in shard.trajectories:
        rows = trajectory.observations
        ids = encode_exercises([o.query.item_id for o in rows], exercise_encoding)
        labels = np.asarray([o.correct for o in rows], dtype=np.int8)
        prior = np.asarray([-1] + labels[:-1].tolist(), dtype=np.int8)
        offsets = np.asarray([0, len(rows)], dtype=np.int64)
        inputs = CausalSequenceInputs(ids, np.asarray([o.query.timestamp for o in rows], dtype=np.int64), prior,
            np.asarray([o.query.source_row for o in rows], dtype=np.int64), offsets,
            tuple(trajectory.learner_id for _ in rows), None)
        for geometry in iter_window_slices(ids, offsets, context=context, target_block=target_block):
            if geometry.unseen:
                if training:
                    raise ValueError('unexpected OOV in original train shard')
                observation = rows[geometry.start]
                yield SimulatorUnseenQuery(trajectory.learner_id, observation.query, int(geometry.global_ranks[0]))
            else:
                window = slice_causal_inputs(inputs, geometry)
                yield TrainingWindow(window, labels[geometry.start:geometry.stop].copy()) if training else window


def scoring_targets(shard: SimulatorShard, encoding: SimulatorEncoding):
    """Ground truth/identity cho đối chiếu coverage, không là model inputs."""
    _check_scope(shard, encoding, training=False)
    vocabulary = {item for item, _ in encoding.support}
    return tuple(SimulatorTarget(t.learner_id, o.query, o.correct, rank, o.query.item_id in vocabulary)
                 for t in shard.trajectories for rank, o in enumerate(t.observations))
