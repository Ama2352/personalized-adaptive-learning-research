"""Bảo toàn lambda.55 và cô lập thay đổi learning penalty trong prototype."""

import pandas as pd
import pytest

from knowledge_tracing.paper2_reference import load_reference
from knowledge_tracing.gam_kt.simulator_mechanisms import build_mechanism_environment


def test_historical_strength_preserves_actual_environment_exactly():
    reference = load_reference()
    scope = reference['environment']
    base = {cid: 1000.0 for cid in scope['nodes']}
    original = scope['LatentStudentEnvironment'](base)
    candidate = build_mechanism_environment(reference, prerequisite_strength=.55)(base)
    for step in range(8):
        cid = scope['nodes'][step % len(base)]
        timestamp = pd.Timestamp('2026-01-01', tz='UTC') + pd.Timedelta(days=step)
        args = (cid, 1200.0, timestamp, .2, .7)
        assert candidate.interact(*args) == original.interact(*args)
        assert candidate.theta == original.theta
        assert candidate.last_seen == original.last_seen


def test_zero_strength_changes_gain_but_not_response_at_identical_pre_state():
    reference = load_reference()
    scope = reference['environment']
    base = {cid: 900.0 for cid in scope['nodes']}
    cid = next(cid for cid in scope['nodes'] if scope['graph'].predecessors(cid))
    historical = build_mechanism_environment(reference, prerequisite_strength=.55)(base)
    control = build_mechanism_environment(reference, prerequisite_strength=0)(base)
    args = (cid, 1100.0, pd.Timestamp('2026-01-01', tz='UTC'), .3, .5)
    a, b = historical.interact(*args), control.interact(*args)
    assert a['prerequisite_deficit'] > 0
    assert a['y'] == b['y'] and a['p_true'] == b['p_true']
    assert b['learning_gain'] > a['learning_gain']


@pytest.mark.parametrize('strength', [True, -1, 2, float('nan')])
def test_mechanism_rejects_invalid_strength(strength):
    with pytest.raises(ValueError, match='strength'):
        build_mechanism_environment({}, prerequisite_strength=strength)
