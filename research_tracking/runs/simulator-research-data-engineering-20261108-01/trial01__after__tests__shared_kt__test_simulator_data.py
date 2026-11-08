"""Fixture schema/split CPU, không dùng dữ liệu learner hoặc oracle thật."""

from dataclasses import dataclass, replace

import pytest

from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from knowledge_tracing.simulator_data import (ROLES, SimulatorSplitPlan, ObservableTrajectory,
                                             training_observations, validate_role_shard)


def fixture():
    bank = SimulatorBank('fixture-data-v1', (SimulatorItem('a', 'A', 0), SimulatorItem('b', 'B', 1)))
    plan = SimulatorSplitPlan('schema-test-only', 42, tuple((role, 2) for role in ROLES))
    shards = {role: [] for role in ROLES}
    row = 0
    for assignment in plan.assignments():
        observations = []
        for rank in range(3):
            row += 1
            observations.append(Observation(ItemQuery('a', rank, row), rank % 2))
        shards[assignment.role].append(ObservableTrajectory(assignment.learner_id, plan.identity,
            identity_hash(bank.identity), 'arithmetic-fixture-only', tuple(observations)))
    return bank, plan, shards


def audit(shard, bank, plan, role='train', cap=3):
    return validate_role_shard(shard, bank=bank, plan=plan, role=role, max_events_per_learner=cap)


def test_stable_namespaces_counts_and_distinct_rng_families():
    _, plan, _ = fixture()
    reordered = SimulatorSplitPlan(plan.namespace, 42, tuple(reversed(plan.role_counts)))
    bigger = SimulatorSplitPlan(plan.namespace, 42, tuple((r, 3 if r == 'train' else c) for r, c in plan.role_counts))
    assert plan.identity == reordered.identity
    assert plan.assignments() == reordered.assignments()
    for role in ROLES[1:]:
        assert plan.assignments(role) == bigger.assignments(role)
    assert bigger.assignments('train')[:2] == plan.assignments('train')
    assignments = plan.assignments()
    seeds = [seed for a in assignments for _, seed in a.stream_seeds]
    assert len(set(seeds)) == len(seeds) == 24
    assert len({a.learner_id for a in assignments}) == 8
    assert plan.identity != bigger.identity
    assert plan.assignments() != SimulatorSplitPlan('other', 42, plan.role_counts).assignments()


@pytest.mark.parametrize('counts', [(), (('train', 1),), tuple((r, 0) for r in ROLES),
    tuple((r, True) for r in ROLES), (('train', 1),) * 4])
def test_reject_invalid_allocations(counts):
    with pytest.raises(ValueError):
        SimulatorSplitPlan('fixture', 42, counts)


def test_role_shard_audit_without_loading_other_roles_and_roundtrip():
    bank, plan, shards = fixture()
    shard = shards['train']
    result = audit(shard, bank, plan)
    assert result['learners'] == 2 and result['targets'] == 6
    assert result['unobserved_bank_items'] == ['b']
    assert result == audit(list(reversed(shard)), bank, plan)
    assert ObservableTrajectory.from_payload(shard[0].payload()) == shard[0]
    projection = training_observations(shard, bank=bank, plan=plan, max_events_per_learner=3)
    assert len(projection) == 2
    assert all(isinstance(observation, Observation) for _, rows in projection for observation in rows)
    with pytest.raises(ValueError, match='wrong-role'):
        training_observations(shards['calibration'], bank=bank, plan=plan, max_events_per_learner=3)


@pytest.mark.parametrize('level', ['trajectory', 'observation', 'query'])
def test_oracle_unknown_fields_rejected_at_every_level(level):
    _, _, shards = fixture()
    payload = shards['train'][0].payload()
    target = payload if level == 'trajectory' else payload['observations'][0]
    if level == 'query':
        target = target['query']
    target['latent_mastery'] = .8
    with pytest.raises(ValueError, match='fields'):
        ObservableTrajectory.from_payload(payload)


def test_direct_schema_cannot_serialize_oracle_subclass_fields():
    @dataclass(frozen=True)
    class OracleObservation(Observation):
        latent_mastery: float = .9

    _, _, shards = fixture()
    with pytest.raises(ValueError, match='observable trajectory'):
        replace(shards['train'][0], observations=(OracleObservation(ItemQuery('a', 0, 1), 1),))


@pytest.mark.parametrize('case', ['missing', 'duplicate', 'wrong_role', 'plan', 'domain',
                                 'unknown_item', 'chronology', 'row_collision', 'cap', 'no_role'])
def test_role_boundary_and_coverage_fail_closed(case):
    bank, plan, shards = fixture()
    shard, cap, role = list(shards['train']), 3, 'train'
    if case == 'missing':
        shard.pop()
    elif case == 'duplicate':
        shard.append(shard[0])
    elif case == 'wrong_role':
        shard[0] = shards['selection'][0]
    elif case in ('plan', 'domain'):
        shard[0] = replace(shard[0], **{case + '_sha256': '0' * 64})
    elif case == 'unknown_item':
        shard[0] = replace(shard[0], observations=(Observation(ItemQuery('alien', 0, 1), 0),))
    elif case == 'chronology':
        shard[0] = replace(shard[0], observations=tuple(reversed(shard[0].observations)))
    elif case == 'row_collision':
        shard[1] = replace(shard[1], observations=shard[0].observations)
    elif case == 'cap':
        cap = 2
    elif case == 'no_role':
        role = None
    with pytest.raises(ValueError):
        audit(shard, bank, plan, role=role, cap=cap)


@pytest.mark.parametrize('seed', [True, -1, 2**63, 4.2])
def test_root_seed_is_explicit_integer(seed):
    with pytest.raises(ValueError, match='seed'):
        SimulatorSplitPlan('fixture', seed, tuple((r, 1) for r in ROLES))
