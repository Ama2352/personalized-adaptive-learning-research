"""Bảo toàn hai endpoint nguồn và kiểm local effects khi không có cạnh."""

import numpy as np
import pandas as pd
import pytest

from knowledge_tracing.paper2_reference import load_reference
from knowledge_tracing.gam_kt.simulator_pathways import build_pathway_policy


@pytest.mark.parametrize('enabled', [False, True])
def test_pathway_endpoints_match_historical_context_prediction_and_updates(enabled):
    reference = load_reference()
    scope = reference['estimator']
    original = scope['GAMKTPolicy'](enabled)
    candidate = build_pathway_policy(reference, signal=enabled, parent_adaptation=enabled, local_adaptation=enabled)
    cid = next(node for node in scope['nodes'] if scope['graph'].predecessors(node))
    item = scope['questions_by_concept'][cid].iloc[0]
    qid, difficulty = str(item.question_id), float(item.elo_difficulty)
    # Bao gồm struggling và forgotten state, không chỉ neutral initialization.
    for policy in (original, candidate):
        state = policy.states[cid]
        state.attempts = 7
        state.recent_outcomes.extend([0, 0, 1, 0, 0, 0])
        state.times_forgotten = 2
        state.last_timestamp = pd.Timestamp('2026-01-01', tz='UTC')
    for step, label in enumerate([0, 1, 0, 1, 1, 0]):
        timestamp = pd.Timestamp('2026-01-03', tz='UTC') + pd.Timedelta(hours=6*step)
        a, b = original._context(cid), candidate._context(cid)
        for key in a:
            assert a[key] == pytest.approx(b[key], abs=1e-15)
        p = original.predict(cid, qid, difficulty, timestamp)
        q = candidate.predict(cid, qid, difficulty, timestamp)
        assert p == pytest.approx(q, abs=1e-15)
        original.update(cid, qid, difficulty, timestamp, label, p)
        candidate.update(cid, qid, difficulty, timestamp, label, q)
        assert original.states[cid].theta == pytest.approx(candidate.states[cid].theta, abs=1e-12)
        np.testing.assert_allclose(original.states[cid].memory, candidate.states[cid].memory, atol=1e-12, rtol=0)


def test_local_pathway_is_active_without_edges_and_does_not_change_parent_terms():
    reference = load_reference(estimator_edges=[])
    off = build_pathway_policy(reference, signal=False, parent_adaptation=False, local_adaptation=False)
    local = build_pathway_policy(reference, signal=False, parent_adaptation=False, local_adaptation=True)
    cid = reference['estimator']['nodes'][0]
    for policy in (off, local):
        state = policy.states[cid]
        state.attempts = 5
        state.recent_outcomes.extend([0]*5)
        state.times_forgotten = 2
    before, after = off._context(cid), local._context(cid)
    assert before['q_task'] == after['q_task']
    assert before['graph_signal'] == after['graph_signal'] == 0
    assert after['r_neg'] == .9 * before['r_neg']
    assert after['decay'] == before['decay'] + .008
