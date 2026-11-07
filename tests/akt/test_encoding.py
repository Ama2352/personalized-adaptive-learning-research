from dataclasses import replace

import pytest

from knowledge_tracing.akt.encoding import encode_exercises, fit_vocabulary, load_encoding, save_encoding
from knowledge_tracing.akt.types import KTEvent, LearnerEvents


def learner(user, exercises):
    events = tuple(KTEvent(user, ex, 100 + i, i + 1, i % 2, 0, 0)
                   for i, ex in enumerate(exercises))
    return LearnerEvents(user, 0, events)


def test_sorted_vocabulary_support_and_oov_without_resize():
    train = [learner('u1', ['A', 'A', 'B']), learner('u2', ['A'])]
    enc = fit_vocabulary(train)
    assert enc.vocabulary.values == ('A', 'B')
    assert encode_exercises(['B', 'X', 'A'], enc).tolist() == [1, -1, 0]
    assert enc.train_support_students == {'A': 2, 'B': 1}
    assert enc.vocabulary.encode(['B', 'A']).tolist() == [1, 0]
    assert fit_vocabulary(list(reversed(train))) == enc


def test_encoding_does_not_use_labels_and_rejects_empty_or_duplicate_users():
    u = learner('u1', ['A', 'B'])
    changed = replace(u, events=tuple(replace(e, correct=1-e.correct, suggested=1) for e in u.events))
    assert fit_vocabulary([u]) == fit_vocabulary([changed])
    with pytest.raises(ValueError, match='empty'):
        fit_vocabulary([])
    with pytest.raises(ValueError, match='duplicate'):
        fit_vocabulary([u, u])


def test_encoding_roundtrip_preserves_mapping_and_hash(tmp_path):
    enc = fit_vocabulary([learner('u1', ['B', 'A'])])
    path = tmp_path / 'encoding.json'
    digest = save_encoding(enc, path)
    assert len(digest) == 64
    assert load_encoding(path) == enc
    assert encode_exercises(['A', 'X', 'B'], load_encoding(path)).tolist() == [0, -1, 1]
