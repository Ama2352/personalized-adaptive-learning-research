"""Synthetic observable records only; no environment/predictor/optimizer calls."""
from dataclasses import dataclass, replace

import pytest

from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from knowledge_tracing.simulator_data import ObservableTrajectory, validate_role_shard
from knowledge_tracing.simulator_research_data import (
    MAX_PLAN_LEARNERS, ResearchSplitPlan, ResearchProvenance, SelectionFreeze,
    ShardLimits, audit_research_shard, prepare_refit_view,
)

SHA = 'a'*64


def fixture():
    plan = ResearchSplitPlan('unit-observables-not-a-research-corpus', 42, 10, 2, SHA)
    bank = SimulatorBank('unit-research-domain', tuple(
        SimulatorItem(f'item-{concept:02}-{i}', f'concept-{concept:02}', difficulty)
        for concept in range(28) for i, difficulty in enumerate((1050., 1200., 1350.))))
    provenance, shards, limits = {}, {}, {}
    row = 1
    for role in ('train', 'selection', 'calibration'):
        trajectories = []
        for index, assignment in enumerate(plan.split_plan.assignments(role)):
            # Train covers all84 bank items across eight12-event learners (96targets).
            indices = [(index*12 + j) % 84 for j in range(12)] if role == 'train' else [0, 1, 2]
            observations = []
            for rank, item_index in enumerate(indices):
                observations.append(Observation(ItemQuery(bank.item_ids[item_index], 100+rank, row), rank % 2))
                row += 1
            trajectories.append(ObservableTrajectory(assignment.learner_id, plan.split_plan.identity,
                identity_hash(bank.identity), 'custom-observable-policy', tuple(observations)))
        provenance[role] = ResearchProvenance(role, plan.identity, plan.split_plan.identity,
            identity_hash(bank.identity), 'b'*64, (('environment', 'c'*64), ('collector', 'd'*64)),
            'e'*64, 'custom-observable-policy', 'unix_seconds_utc', 'UTC', False)
        shards[role] = tuple(trajectories)
        limits[role] = ShardLimits(len(trajectories), 12, len(trajectories)*12)
    return plan, bank, provenance, shards, limits


def audit(values, role='train', **changes):
    plan, bank, provenance, shards, limits = values
    args = dict(plan=plan, bank=bank, role=role, provenance=provenance[role],
        expected_provenance_sha256=provenance[role].identity, limits=limits[role], reference_items=bank.item_ids)
    args.update(changes)
    return audit_research_shard(shards[role], **args)


def refit(values, **changes):
    plan, bank, provenance, shards, limits = values
    tr, se = audit(values), audit(values, 'selection')
    freeze = SelectionFreeze(plan.identity, identity_hash(bank.identity), tr['audit']['shard_sha256'],
        se['audit']['shard_sha256'], 'f'*64, 2, 'raw_selection_before_refit')
    args = dict(plan=plan, bank=bank, train_provenance=provenance['train'],
        selection_provenance=provenance['selection'], expected_train_provenance_sha256=provenance['train'].identity,
        expected_selection_provenance_sha256=provenance['selection'].identity, train_limits=limits['train'],
        selection_limits=limits['selection'], reference_items=bank.item_ids, freeze=freeze)
    args.update(changes)
    return prepare_refit_view(shards['train'], shards['selection'], **args)


def test_exact_split_identity_disjoint_roles_seeds_and_final_metadata_only():
    p = ResearchSplitPlan('real-corpus-plan-shape', 42, 100, 6, SHA)
    m = p.manifest()
    assert m['role_counts'] == dict(train=80, selection=10, calibration=10, final=6)
    a = m['assignments']
    assert len({x['learner_id'] for x in a}) == 106
    assert len({x['seed_family'] for x in a}) == 106
    assert len({seed for x in a for _, seed in x['stream_seeds']}) == 318
    assert not m['final_events_read'] and not m['calibration_in_refit']
    assert p == ResearchSplitPlan('real-corpus-plan-shape', 42, 100, 6, SHA)
    assert p.identity != replace(p, protocol_sha256='b'*64).identity
    assert p.identity != replace(p, root_seed=43).identity


@pytest.mark.parametrize('field,value', [('development_learners', 11), ('development_learners', True),
    ('development_learners', 0), ('final_learners', 0), ('root_seed', True),
    ('protocol_sha256', 'x'*64), ('namespace', ''), ('development_learners', MAX_PLAN_LEARNERS)])
def test_plan_fails_before_large_allocation_or_silent_rounding(field, value):
    args = dict(namespace='bounded', root_seed=42, development_learners=10, final_learners=1, protocol_sha256=SHA)
    args[field] = value
    with pytest.raises(ValueError):
        ResearchSplitPlan(**args)


def test_full_support_counts_events_and_unique_learners_not_independent_exposures():
    values = fixture()
    r = audit(values)
    assert r['reference_complete'] and not r['missing_reference_items']
    assert r['audit']['learners'] == 8 and r['audit']['targets'] == 96
    assert len(r['train_vocabulary']) == 84
    support = {x['item_id']: x for x in r['item_support']}
    assert support['item-00-0']['events'] == 2 and support['item-00-0']['learners'] == 2
    assert support['item-27-2']['events'] == 1
    assert identity_hash({k: v for k, v in r.items() if k != 'receipt_sha256'}) == r['receipt_sha256']
    # No restriction by arbitrary policy name: explicit oracle-access provenance is the gate.
    assert r['provenance']['collection_policy_id'] == 'custom-observable-policy'


def test_train_support_cannot_be_rescued_by_calibration_and_counts_repeat_learner_once():
    values = fixture()
    plan, bank, provenance, shards, limits = values
    shards['train'] = tuple(replace(t, observations=tuple(replace(o,
        query=replace(o.query, item_id=bank.item_ids[0])) for o in t.observations)) for t in shards['train'])
    r = audit(values)
    assert not r['reference_complete'] and len(r['missing_reference_items']) == 83
    assert r['train_vocabulary'] == [bank.item_ids[0]]
    assert r['item_support'][0]['events'] == 96 and r['item_support'][0]['learners'] == 8
    cal = audit(values, 'calibration')
    assert cal['train_vocabulary'] is None and cal['audit']['observed_items'] == list(bank.item_ids[:3])
    assert audit(values) == r  # Inspecting calibration has no effect on train vocabulary/support.


def test_final_rejected_before_any_event_iteration():
    class FinalCanary:
        def __iter__(self):
            raise AssertionError('final events were read')
    with pytest.raises(ValueError, match='final events'):
        audit_research_shard(FinalCanary(), plan=None, bank=None, role='final', provenance=None,
            expected_provenance_sha256=None, limits=None, reference_items=None)


@pytest.mark.parametrize('field,value', [('logging_policy_oracle_access', True),
    ('logging_policy_oracle_access', 0), ('timestamp_unit', 'milliseconds'), ('timezone', 'local'),
    ('source_bindings', (('collector', SHA),)), ('source_bindings', (('collector', SHA), ('collector', SHA))),
    ('environment_graph_sha256', 'bad')])
def test_invalid_or_oracle_provenance_rejected(field, value):
    p = fixture()[2]['train']
    with pytest.raises(ValueError):
        replace(p, **{field: value})


@pytest.mark.parametrize('field,value', [('role', 'calibration'), ('bank_sha256', '0'*64),
    ('research_plan_sha256', '0'*64), ('split_plan_sha256', '0'*64),
    ('environment_graph_sha256', '0'*64), ('collection_recipe_sha256', '0'*64)])
def test_role_domain_source_recipe_or_plan_drift_cannot_reuse_expected_binding(field, value):
    values = fixture()
    with pytest.raises(ValueError, match='binding'):
        audit(values, provenance=replace(values[2]['train'], **{field: value}))


@pytest.mark.parametrize('case', ['calibration_learner', 'missing', 'duplicate', 'chronology', 'source_row',
                                 'foreign_policy', 'plan', 'domain', 'item', 'total_cap', 'event_cap',
                                 'learner_cap', 'reference_subset', 'reference_duplicate', 'wrong_bank_shape'])
def test_coverage_identity_and_caps_fail_closed(case):
    values = fixture()
    plan, bank, provenance, shards, limits = values
    tr = list(shards['train']); args = {}
    if case == 'calibration_learner': tr[0] = shards['calibration'][0]
    elif case == 'missing': tr.pop()
    elif case == 'duplicate': tr[-1] = tr[0]
    elif case in ('chronology', 'source_row', 'item'):
        obs = list(tr[0].observations)
        q = replace(obs[1].query, **({'timestamp': 0} if case == 'chronology' else
            {'source_row': obs[0].query.source_row} if case == 'source_row' else {'item_id': 'OOV'}))
        obs[1] = replace(obs[1], query=q); tr[0] = replace(tr[0], observations=tuple(obs))
    elif case == 'foreign_policy': tr[0] = replace(tr[0], collection_policy_id='unbound')
    elif case in ('plan', 'domain'): tr[0] = replace(tr[0], **{case+'_sha256': '0'*64})
    elif case == 'total_cap': args['limits'] = ShardLimits(8, 12, 95)
    elif case == 'event_cap': args['limits'] = ShardLimits(8, 11, 96)
    elif case == 'learner_cap': args['limits'] = ShardLimits(7, 12, 96)
    elif case == 'reference_subset': args['reference_items'] = bank.item_ids[:-1]
    elif case == 'reference_duplicate': args['reference_items'] = bank.item_ids+(bank.item_ids[0],)
    elif case == 'wrong_bank_shape':
        bad = replace(bank, items=bank.items[:-1]); args.update(bank=bad, reference_items=bad.item_ids)
        p = replace(provenance['train'], bank_sha256=identity_hash(bad.identity))
        args.update(provenance=p, expected_provenance_sha256=p.identity)
    shards['train'] = tuple(tr)
    with pytest.raises(ValueError):
        audit(values, **args)


def test_oracle_trajectory_subclass_is_rejected_even_if_old_validator_accepts_base_shape():
    @dataclass(frozen=True)
    class OracleTrajectory(ObservableTrajectory):
        latent: float = .8
    values = fixture()
    tr = values[3]['train'][0]
    leaked = OracleTrajectory(tr.learner_id, tr.plan_sha256, tr.domain_sha256,
                              tr.collection_policy_id, tr.observations)
    values[3]['train'] = (leaked,) + values[3]['train'][1:]
    with pytest.raises(ValueError, match='exact observable'):
        audit(values)


def test_refit_is_explicit_ninety_percent_union_not_fake_legacy_train():
    values = fixture()
    before = audit(values)
    view = refit(values)
    assert len(view.trajectories) == 9 and len(view.learner_origin_roles) == 9
    assert CounterRoles(view.learner_origin_roles) == {'train': 8, 'selection': 1}
    assert view.role == 'refit_train_plus_selection'
    assert view.freeze.selected_epoch == 2
    assert len(view.observable_sequences()) == 9
    assert view.identity == refit(values).identity
    assert audit(values) == before  # Original80% support/identity never relabeled or overwritten.
    p, b = values[:2]
    with pytest.raises(ValueError, match='wrong-role'):
        validate_role_shard(view.trajectories, plan=p.split_plan, bank=b, role='train', max_events_per_learner=12)


def CounterRoles(rows):
    return {r: sum(value == r for _, value in rows) for r in ('train', 'selection')}


@pytest.mark.parametrize('field', ['research_plan_sha256', 'bank_sha256', 'train_shard_sha256', 'selection_shard_sha256'])
def test_refit_rejects_stale_foreign_freeze(field):
    values = fixture(); current = refit(values)
    with pytest.raises(ValueError, match='freeze'):
        refit(values, freeze=replace(current.freeze, **{field: '0'*64}))


def test_refit_rejects_calibration_as_selection_and_cross_role_row_collision():
    values = fixture()
    values[3]['selection'] = values[3]['calibration']
    with pytest.raises(ValueError):
        refit(values)
    values = fixture(); tr = values[3]['train'][0]; se = values[3]['selection'][0]
    obs = list(se.observations); obs[0] = replace(obs[0], query=replace(obs[0].query,
        source_row=tr.observations[0].query.source_row)); values[3]['selection'] = (replace(se, observations=tuple(obs)),)
    with pytest.raises(ValueError, match='unique across'):
        refit(values)


@pytest.mark.parametrize('stage', ['after_refit', 'calibrated_selection', '', True])
def test_selection_freeze_stage_cannot_silently_change(stage):
    with pytest.raises(ValueError, match='before refit'):
        SelectionFreeze(SHA, SHA, SHA, SHA, SHA, 1, stage)
