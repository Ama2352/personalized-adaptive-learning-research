"""Mock environment only; actual Paper2 loading/interaction explicitly prohibited."""
from dataclasses import asdict, replace
from types import SimpleNamespace

import numpy as np
import pytest

import knowledge_tracing.simulator_research_collection as m
from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem
from knowledge_tracing.simulator_research_data import ResearchSplitPlan

SHA = 'a'*64


@pytest.fixture(autouse=True)
def deny_actual_native_source(monkeypatch):
    def denied():
        raise AssertionError('actual native source load is forbidden in pure mock suite')
    monkeypatch.setattr(m, 'load_reference', denied)
    monkeypatch.setattr(m, 'source_inventory', denied)


@pytest.fixture
def setup(monkeypatch):
    calls = {'loads': 0, 'environments': 0, 'interacts': 0, 'source_reads': 0}
    clock = SimpleNamespace(now=0.)
    monkeypatch.setattr(m, 'time', SimpleNamespace(perf_counter=lambda: clock.now))
    sample = {'process_rss_bytes': 128*1024**2, 'process_peak_rss_bytes': None,
              'system_available_ram_bytes': 8*1024**3}
    monkeypatch.setattr(m, 'memory_snapshot', lambda: dict(sample))
    plan = ResearchSplitPlan('collector-mock-not-corpus', 42, 10, 2, SHA)
    bank = SimulatorBank('mock-world', tuple(SimulatorItem(f'item-{c:02}-{i}', f'concept-{c:02}', d)
        for c in range(28) for i, d in enumerate((1050., 1200., 1350.))))
    sources = {m.PROTOCOL_PATH: SHA, m.COLLECTOR_PATH: 'b'*64,
               'paper2/mock.ipynb': 'c'*64, 'paper2/mock/question_bank.csv': 'd'*64}
    def inventory():
        calls['source_reads'] += 1
        return dict(sources)
    monkeypatch.setattr(m, 'source_inventory', inventory)
    def base(profile, seed):
        return {f'concept-{c:02}': float({'PG': 1, 'PY': 2, 'PYH': 3}[profile] + seed % 7)
                for c in range(28)}
    class MockEnvironment:
        def __init__(self, initial):
            calls['environments'] += 1
            self.state = dict(initial)
        @property
        def theta(self):
            raise AssertionError('logging policy must not inspect latent theta')
        def interact(self, concept, difficulty, timestamp, outcome, learning):
            calls['interacts'] += 1
            if 'on_interact' in calls:
                calls['on_interact']()
            self.state[concept] += learning
            return {'y': int(outcome < .5), 'theta_before': self.state[concept]-learning,
                    'difficulty': difficulty, 'timestamp': timestamp.isoformat()}
        def snapshot(self, timestamp):
            return dict(self.state)
    reference = {'environment': {'PERSONAS': ('PG', 'PY', 'PYH'),
        'persona_base_abilities': base, 'LatentStudentEnvironment': MockEnvironment},
        'provenance': {'notebook': 'paper2/mock.ipynb', 'notebook_sha256': sources['paper2/mock.ipynb'],
                       'inputs': {'paper2/mock/question_bank.csv': sources['paper2/mock/question_bank.csv']},
                       'definitions': {}}}
    def loader():
        calls['loads'] += 1
        return reference
    monkeypatch.setattr(m, 'load_reference', loader)
    monkeypatch.setattr(m, '_bank_and_graph', lambda ref: (bank, 'e'*64, {'mock_semantics': 'not_native'}))
    recipe = m.ResearchCollectionRecipe('uniform_items', 3, 1767225600, 21600)
    limits = m.ResearchCollectionLimits(8, 20, 160, 10., 512*1024**2, 1024**3)
    return SimpleNamespace(plan=plan, bank=bank, sources=sources, recipe=recipe, limits=limits,
        calls=calls, clock=clock, memory=sample, reference=reference, monkeypatch=monkeypatch)


def collect(s, role='train', **changes):
    args = dict(role=role, profiles={a.learner_id: 'PG' for a in s.plan.split_plan.assignments(role)},
                recipe=s.recipe, limits=s.limits, expected_sources=s.sources)
    args.update(changes)
    return m.collect_research_role(s.plan, **args)


@pytest.mark.parametrize('role,count', [('train', 8), ('selection', 1), ('calibration', 1)])
def test_requested_role_complete_and_oracle_sidecar_not_model_features(setup, role, count):
    s = setup; result = collect(s, role)
    assert len(result.trajectories) == count
    assert s.calls['environments'] == count and s.calls['interacts'] == count*3
    assert result.manifest['interact_attempts'] == result.manifest['interact_returns'] == count*3
    assert result.manifest['status'] == 'COMPLETE_REQUESTED_ROLE_NOT_MODEL_FITTED'
    assert result.provenance.role == role and result.manifest['sources_before'] == result.manifest['sources_after']
    assert not result.manifest['logging_policy_oracle_access']
    for trajectory in result.trajectories:
        payload = trajectory.payload()
        assert set(payload) == {'learner_id', 'plan_sha256', 'domain_sha256', 'collection_policy_id', 'observations'}
        assert all(set(row) == {'query', 'correct'} for row in payload['observations'])
        assert all(set(row['query']) == {'item_id', 'timestamp', 'source_row'} for row in payload['observations'])
    assert all('initial_state' in row and 'profile' in row and 'channel_seeds' in row
               for row in result.oracle_sidecar['learners'].values())


@pytest.mark.parametrize('policy', ['uniform_items', 'cyclic_items_seeded_offset'])
def test_event_and_uniform_prefix_stable_when_event_limit_changes(setup, policy):
    s = setup
    a = collect(s, recipe=replace(s.recipe, policy=policy, events_per_learner=2))
    b = collect(s, recipe=replace(s.recipe, policy=policy, events_per_learner=5))
    for left, right in zip(a.trajectories, b.trajectories, strict=True):
        assert left.observations == right.observations[:2]
        x, y = (result.oracle_sidecar['learners'][left.learner_id] for result in (a, b))
        assert x['events'] == y['events'][:2] and x['channel_seeds'] == y['channel_seeds']
        assert len(set(x['channel_seeds'].values())) == 3


def test_global_role_event_ids_are_disjoint_and_clock_explicit(setup):
    s = setup; rows = []
    for role in ('calibration', 'train', 'selection'):
        result = collect(s, role)
        rows.extend(o.query.source_row for t in result.trajectories for o in t.observations)
        for t in result.trajectories:
            assert t.observations[0].query.timestamp == s.recipe.start_unix_seconds+s.recipe.gap_seconds
    assert len(rows) == len(set(rows)) == 30
    assert s.calls['environments'] == 10  # Never the two planned final learners.


def test_profile_does_not_change_behavior_or_response_learning_channels(setup):
    s = setup; first = collect(s)
    changed = collect(s, profiles={a.learner_id: 'PYH' for a in s.plan.split_plan.assignments('train')})
    for a, b in zip(first.trajectories, changed.trajectories, strict=True):
        assert [o.query for o in a.observations] == [o.query for o in b.observations]
        x, y = first.oracle_sidecar['learners'][a.learner_id], changed.oracle_sidecar['learners'][a.learner_id]
        assert x['initial_state'] != y['initial_state']
        assert x['channel_seeds'] == y['channel_seeds']
        assert [(e['outcome_uniform'], e['learning_uniform']) for e in x['events']] == [
            (e['outcome_uniform'], e['learning_uniform']) for e in y['events']]
    assert first.provenance.identity != changed.provenance.identity


def test_final_rejected_before_source_or_environment_access():
    with pytest.raises(ValueError, match='final events forbidden'):
        m.collect_research_role(None, role='final', profiles=None, recipe=None, limits=None, expected_sources=None)


@pytest.mark.parametrize('case', ['missing_profile', 'final_profile', 'unknown_profile', 'learners', 'events', 'total', 'row_ceiling'])
def test_preflight_invalid_inputs_do_not_interact(setup, case):
    s = setup; changes = {}
    profiles = {a.learner_id: 'PG' for a in s.plan.split_plan.assignments('train')}
    if case == 'missing_profile': profiles.pop(next(iter(profiles))); changes['profiles'] = profiles
    elif case == 'final_profile': profiles[next(iter(profiles))] = 'PG'; profiles[s.plan.split_plan.assignments('final')[0].learner_id] = 'PG'; changes['profiles'] = profiles
    elif case == 'unknown_profile': changes['profiles'] = {k: 'UNKNOWN' for k in profiles}
    elif case == 'learners': changes['limits'] = replace(s.limits, max_learners=7)
    elif case == 'events': changes['limits'] = replace(s.limits, max_events_per_learner=2)
    elif case == 'total': changes['limits'] = replace(s.limits, max_total_events=23)
    elif case == 'row_ceiling': s.monkeypatch.setattr(m, 'MAX_SOURCE_ROW', 1)
    with pytest.raises((ValueError, m.ResearchCollectionFailure)):
        collect(s, **changes)
    assert s.calls['environments'] == s.calls['interacts'] == 0


@pytest.mark.parametrize('field,value', [('events_per_learner', True), ('events_per_learner', 0),
    ('events_per_learner', m.EVENT_STRIDE+1), ('start_unix_seconds', -1), ('gap_seconds', 0),
    ('policy', 'oracle_theta_policy'), ('start_unix_seconds', 2**63),
    ('start_unix_seconds', 2**63-4)])
def test_recipe_no_implicit_or_oracle_policy_or_unbounded_clock(field, value):
    args = dict(policy='uniform_items', events_per_learner=3, start_unix_seconds=100, gap_seconds=1)
    args[field] = value
    with pytest.raises((ValueError, OverflowError)):
        m.ResearchCollectionRecipe(**args)


def test_exact_supported_clock_boundary_is_valid_next_second_rejected():
    m.ResearchCollectionRecipe('uniform_items', 3, m.MAX_UNIX_SECONDS-3, 1)
    with pytest.raises(ValueError, match='UTC timestamp range'):
        m.ResearchCollectionRecipe('uniform_items', 3, m.MAX_UNIX_SECONDS-2, 1)


@pytest.mark.parametrize('field,value', [('max_wall_seconds', True), ('max_wall_seconds', float('nan')),
    ('max_wall_seconds', 601), ('max_rss_bytes', True), ('max_rss_bytes', 3*1024**3),
    ('min_available_ram_bytes', 1024**3-1), ('max_total_events', 0)])
def test_explicit_resource_limits_fail_closed(setup, field, value):
    with pytest.raises(ValueError):
        replace(setup.limits, **{field: value})


@pytest.mark.parametrize('case', ['free_ram', 'rss', 'peak_rss', 'unknown_memory'])
def test_memory_failure_precedes_source_load(setup, case):
    s = setup
    if case == 'free_ram': s.memory['system_available_ram_bytes'] = 1024**3-1
    elif case == 'rss': s.memory['process_rss_bytes'] = s.limits.max_rss_bytes+1
    elif case == 'peak_rss': s.memory['process_peak_rss_bytes'] = s.limits.max_rss_bytes+1
    else: s.memory['process_rss_bytes'] = True
    with pytest.raises(m.ResearchCollectionFailure) as caught:
        collect(s)
    assert s.calls['loads'] == s.calls['interacts'] == 0
    assert caught.value.receipt['interact_attempts'] == 0


@pytest.mark.parametrize('case', ['deadline', 'free_ram', 'rss'])
def test_post_interact_guard_retains_real_completed_work_without_success(setup, case):
    s = setup
    def fail_after_call():
        if case == 'deadline': s.clock.now = 11
        elif case == 'free_ram': s.memory['system_available_ram_bytes'] = 0
        else: s.memory['process_rss_bytes'] = s.limits.max_rss_bytes+1
    s.calls['on_interact'] = fail_after_call
    with pytest.raises(m.ResearchCollectionFailure) as caught:
        collect(s)
    receipt = caught.value.receipt
    assert receipt['status'] == 'FAILED_NO_USABLE_ROLE_RESULT'
    assert receipt['interact_attempts'] == receipt['interact_returns'] == receipt['completed_events'] == 1
    assert not receipt['partial_environment_work_rolled_back'] and not receipt['automatic_retry']


def test_telemetry_operator_overrun_checked_after_telemetry(setup):
    s = setup
    def slow_snapshot():
        s.clock.now = 11
        return dict(s.memory)
    s.monkeypatch.setattr(m, 'memory_snapshot', slow_snapshot)
    with pytest.raises(m.ResearchCollectionFailure, match='after telemetry'):
        collect(s)
    assert s.calls['loads'] == s.calls['interacts'] == 0


def test_expected_source_pin_mismatch_cannot_load_environment(setup):
    s = setup; expected = {**s.sources, m.COLLECTOR_PATH: 'f'*64}
    with pytest.raises(m.ResearchCollectionFailure, match='inventory mismatch'):
        collect(s, expected_sources=expected)
    assert s.calls['loads'] == s.calls['interacts'] == 0


def test_source_drift_after_generation_rejects_instead_of_returning_corpus(setup):
    s = setup; reads = 0
    def changing_sources():
        nonlocal reads
        reads += 1
        return dict(s.sources) if reads == 1 else {**s.sources, m.COLLECTOR_PATH: 'f'*64}
    s.monkeypatch.setattr(m, 'source_inventory', changing_sources)
    with pytest.raises(m.ResearchCollectionFailure, match='source inventory drift') as caught:
        collect(s)
    assert caught.value.receipt['completed_events'] == 24 and s.calls['interacts'] == 24


def test_loaded_reference_payload_binding_mismatch_and_bad_bank_stop_before_interact(setup):
    s = setup
    s.reference['provenance']['notebook_sha256'] = 'f'*64
    with pytest.raises(m.ResearchCollectionFailure, match='loaded native reference'):
        collect(s)
    assert s.calls['environments'] == 0
    s.reference['provenance']['notebook_sha256'] = s.sources['paper2/mock.ipynb']
    s.monkeypatch.setattr(m, '_bank_and_graph', lambda ref: (replace(s.bank, items=s.bank.items[:-1]), 'e'*64, {}))
    with pytest.raises(m.ResearchCollectionFailure, match='reference bank'):
        collect(s)
    assert s.calls['environments'] == 0


def test_invalid_native_outcome_cannot_be_silently_coerced(setup):
    s = setup; original = s.reference['environment']['LatentStudentEnvironment']
    class InvalidOutcome(original):
        def interact(self, *args):
            result = super().interact(*args); result['y'] = .5; return result
    s.reference['environment']['LatentStudentEnvironment'] = InvalidOutcome
    with pytest.raises(m.ResearchCollectionFailure, match='invalid binary outcome') as caught:
        collect(s)
    assert caught.value.receipt['interact_returns'] == 1 and caught.value.receipt['completed_events'] == 0


def test_private_channels_do_not_mutate_numpy_global_rng(setup):
    before = np.random.get_state()
    collect(setup)
    after = np.random.get_state()
    assert before[0] == after[0] and np.array_equal(before[1], after[1]) and before[2:] == after[2:]


def test_channel_collision_fails_closed_without_native_interaction(setup):
    s = setup; s.monkeypatch.setattr(m, 'identity_hash', lambda value: 'a'*64)
    with pytest.raises(ValueError, match='channel seeds collide'):
        m._channels(s.plan.split_plan.assignments('train')[0])
    assert s.calls['interacts'] == 0
