"""Vocabulary exercise chỉ được fit trên learner train."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from knowledge_tracing.shared_kt import StableVocabulary
from .provenance import sha256_file
from .types import LearnerEvents


@dataclass(frozen=True)
class ExerciseEncoding:
    vocabulary: StableVocabulary
    train_support_students: dict[str, int]


def fit_vocabulary(learners: Iterable[LearnerEvents]) -> ExerciseEncoding:
    seen_users: set[str] = set()
    support: dict[str, int] = {}
    for learner in learners:
        user = str(learner.user_id)
        if user in seen_users:
            raise ValueError('duplicate learner in training scope')
        seen_users.add(user)
        if any(str(event.user_id) != user or event.fold != learner.fold for event in learner.events):
            raise ValueError('learner event identity mismatch')
        for exercise in {str(event.exercise) for event in learner.events}:
            support[exercise] = support.get(exercise, 0) + 1
    if not support:
        raise ValueError('empty training scope')
    vocabulary = StableVocabulary.from_values(list(support))
    return ExerciseEncoding(vocabulary, {item: support[item] for item in vocabulary.values})


def encode_exercises(exercises: Sequence[str], encoding: ExerciseEncoding) -> np.ndarray:
    lookup = {value: index for index, value in enumerate(encoding.vocabulary.values)}
    return np.asarray([lookup.get(str(value), -1) for value in exercises], dtype=np.int64)


def save_encoding(encoding: ExerciseEncoding, path: Path) -> str:
    payload = {'schema_version': 1, 'values': list(encoding.vocabulary.values),
               'train_support_students': encoding.train_support_students}
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(payload, stream, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        stream.write('\n')
    return sha256_file(path)


def load_encoding(path: Path) -> ExerciseEncoding:
    payload = json.loads(path.read_text(encoding='utf-8'))
    values = payload['values']
    support = payload['train_support_students']
    if (payload.get('schema_version') != 1 or not values
            or values != sorted(set(values)) or set(values) != set(support)
            or any(not isinstance(support[k], int) or support[k] <= 0 for k in values)):
        raise ValueError('invalid exercise encoding')
    return ExerciseEncoding(StableVocabulary(tuple(values)), {key: support[key] for key in values})
