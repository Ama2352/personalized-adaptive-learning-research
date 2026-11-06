from dataclasses import replace

import pytest

from knowledge_tracing.experimental_controls import FactorialOutcome, paired_mechanism_contrasts


def rows():
    return [FactorialOutcome(42, 'Low', graph, mechanism, 'latent1', 'stream1', outcome)
            for graph, mechanism, outcome in [(False,False,10), (True,False,12),
                                              (False,True,15), (True,True,20)]]


def test_interaction_uses_same_profile_and_paired_state():
    result = paired_mechanism_contrasts(list(reversed(rows())))[0]
    assert result['graph_effect_mechanism_on'] == 5
    assert result['graph_effect_mechanism_off'] == 2
    assert result['interaction_contrast'] == 3


@pytest.mark.parametrize('change', [dict(latent_identity='other'),
                                   dict(random_stream_identity='other'),
                                   dict(outcome=float('nan'))])
def test_changed_counterfactual_identity_or_invalid_outcome_is_rejected(change):
    outcomes = rows()
    outcomes[0] = replace(outcomes[0], **change)
    with pytest.raises(ValueError):
        paired_mechanism_contrasts(outcomes)


def test_high_profile_cannot_fill_missing_low_control():
    outcomes = rows()
    outcomes[0] = replace(outcomes[0], profile='High')
    with pytest.raises(ValueError, match='missing'):
        paired_mechanism_contrasts(outcomes)


def test_duplicate_and_missing_conditions_are_rejected():
    for outcomes in (rows()[:-1], rows() + rows()[:1], []):
        with pytest.raises(ValueError):
            paired_mechanism_contrasts(outcomes)
