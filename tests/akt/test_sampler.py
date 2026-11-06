from dataclasses import replace
import json
import random

import pytest

from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.sampler import ReplayableWindowCursor
from knowledge_tracing.akt.training import _shuffle_windows
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows


def factory():
    learner = LearnerEvents('u', 1, tuple(KTEvent('u', 'A', i+1, i+1, i%2, 0, 1)
                                        for i in range(17)))
    encoding = fit_vocabulary([learner])
    return lambda: iter_windows(learner, encoding, context=2, target_block=2, training=True)


def ids(entries):
    return [e.window.window_id for e in entries]


@pytest.mark.parametrize('buffer_size', [1,3,1024])
@pytest.mark.parametrize('cut', [0,1,5,9])
def test_resume_preserves_existing_shuffle_order_exactly(buffer_size, cut):
    make = factory()
    expected = ids(_shuffle_windows(make, seed=43, buffer_size=buffer_size))
    rng_before = random.getstate()
    cursor = ReplayableWindowCursor(make, seed=43, stream_identity='fixture', buffer_size=buffer_size)
    prefix = ids(next(cursor) for _ in range(cut))
    saved = json.loads(json.dumps(cursor.state_dict()))
    resumed = ReplayableWindowCursor(make, seed=43, stream_identity='fixture',
                                     buffer_size=buffer_size, state=saved)
    assert prefix + ids(resumed) == expected
    assert len(set(expected)) == len(expected)
    assert random.getstate() == rng_before


def test_resume_rejects_changed_prefix_and_identity():
    make = factory()
    cursor = ReplayableWindowCursor(make, seed=43, stream_identity='fixture', buffer_size=1)
    next(cursor)
    state = cursor.state_dict()
    def changed():
        for entry in make():
            yield replace(entry, targets=1-entry.targets)
    with pytest.raises(ValueError, match='content'):
        ReplayableWindowCursor(changed, seed=43, stream_identity='fixture', buffer_size=1, state=state)
    with pytest.raises(ValueError, match='identity'):
        ReplayableWindowCursor(make, seed=43, stream_identity='other', buffer_size=1, state=state)
    with pytest.raises(ValueError, match='exceeds'):
        ReplayableWindowCursor(make, seed=43, stream_identity='fixture', buffer_size=1,
                               state={**state, 'consumed_windows': 999})
