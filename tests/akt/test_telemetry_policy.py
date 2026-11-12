"""Telemetry giới hạn giữ mẫu mới và không đổi default của trainer."""
import pytest

from knowledge_tracing.akt.telemetry_policy import resource_sample_policy


def test_legacy_default_keeps_all_samples():
    samples, include = resource_sample_policy({})
    for index in range(1000):
        samples.append(index)
    assert samples == list(range(1000)) and include is True


def test_bounded_progress_retains_latest_samples():
    samples, include = resource_sample_policy(dict(resource_sample_limit=128,progress_resource_samples=False))
    for index in range(10000):
        samples.append(index)
    assert list(samples)==list(range(9872,10000)) and include is False


@pytest.mark.parametrize('value',[True,0,1,4097,2.5,'128'])
def test_invalid_ring_limit(value):
    with pytest.raises(ValueError):
        resource_sample_policy(dict(resource_sample_limit=value))


def test_progress_policy_requires_boolean():
    with pytest.raises(ValueError):
        resource_sample_policy(dict(progress_resource_samples=0))


def test_explicit_recovery_cadence_for_new_phase():
    from knowledge_tracing.akt.recovery import checkpoint_cadence
    from knowledge_tracing.akt.config import AKTConfig,RecoveryOptions
    assert checkpoint_cadence(AKTConfig(),dict(checkpoint_every_steps=1000))==1000
    assert checkpoint_cadence(AKTConfig(recovery=RecoveryOptions(5)),{})==5
    with pytest.raises(ValueError):
        checkpoint_cadence(AKTConfig(recovery=RecoveryOptions(5)),dict(checkpoint_every_steps=6))
    with pytest.raises(ValueError):
        checkpoint_cadence(AKTConfig(),{})
