"""Collector fixture: reuse phương trình nguồn, không cần model/GPU."""

from dataclasses import replace
import copy
import hashlib
import json
import runpy

import numpy as np
import pandas as pd
import pytest

from knowledge_tracing.paper2_reference import load_reference
from knowledge_tracing.simulator_bridge import identity_hash
from knowledge_tracing.simulator_collection import (CollectionRecipe, collect_training_fixture, response_channels,
                                                    canonical_source_provenance, environment_semantics)
from knowledge_tracing.simulator_data import ROLES, SimulatorSplitPlan, ObservableTrajectory


def setup(policy='uniform_items', *, count=2):
    plan = SimulatorSplitPlan('collector-unit-fixture-only', 42, tuple((r, count if r == 'train' else 1) for r in ROLES))
    profiles = {a.learner_id: ('PY' if i == 0 else 'PG') for i, a in enumerate(plan.assignments('train'))}
    recipe = CollectionRecipe(policy, 12, 1767225600, 1800, 30)
    return plan, profiles, recipe


@pytest.fixture(scope='module')
def collected():
    plan, profiles, recipe = setup()
    return collect_training_fixture(plan, profiles=profiles, recipe=recipe)


def test_deterministic_collection_and_observable_oracle_separation(collected):
    plan, profiles, recipe = setup()
    repeated = collect_training_fixture(plan, profiles=profiles, recipe=recipe)
    assert collected.trajectories == repeated.trajectories
    assert collected.oracle_sidecar == repeated.oracle_sidecar
    assert collected.manifest['audit'] == repeated.manifest['audit']
    assert len(collected.bank.items) == 84
    assert collected.manifest['audit']['targets'] == 24
    assert {t.learner_id for t in collected.trajectories} == set(profiles)
    assert collected.manifest['timestamp_unit'] == 'unix_seconds_utc'
    assert not collected.manifest['logging_policy_oracle_access']
    for trajectory in collected.trajectories:
        assert ObservableTrajectory.from_payload(json.loads(json.dumps(trajectory.payload()))) == trajectory
        assert trajectory.observations[0].query.timestamp == recipe.start_unix_seconds + recipe.gap_seconds
        assert 'profile' not in json.dumps(trajectory.payload())
    assert identity_hash(collected.oracle_sidecar) == collected.manifest['oracle_sidecar_sha256']


def test_original_environment_replay_exact_state_outcome_and_clock(collected):
    scope = load_reference()['environment']
    items = {i.item_id: i for i in collected.bank.items}
    for trajectory in collected.trajectories:
        oracle = collected.oracle_sidecar['learners'][trajectory.learner_id]
        base = scope['persona_base_abilities'](oracle['profile'], dict(oracle['assignment']['stream_seeds'])['latent'])
        assert base == oracle['initial_state']
        environment = scope['LatentStudentEnvironment'](base)
        for observation, detail in zip(trajectory.observations, oracle['events'], strict=True):
            item = items[observation.query.item_id]
            timestamp = pd.to_datetime(observation.query.timestamp, unit='s', utc=True)
            actual = environment.interact(item.concept_id, item.difficulty, timestamp,
                                          detail['outcome_uniform'], detail['learning_uniform'])
            assert actual == detail['oracle_result']
            assert actual['y'] == observation.correct
        assert environment.snapshot(timestamp) == oracle['final_snapshot']


def test_profile_changes_do_not_change_behavior_or_response_rng(collected):
    plan, profiles, recipe = setup()
    changed = collect_training_fixture(plan, profiles={key: 'PYH' for key in profiles}, recipe=recipe)
    for before, after in zip(collected.trajectories, changed.trajectories, strict=True):
        assert [o.query for o in before.observations] == [o.query for o in after.observations]
        old = collected.oracle_sidecar['learners'][before.learner_id]
        new = changed.oracle_sidecar['learners'][after.learner_id]
        assert old['response_rng'] == new['response_rng']
        assert old['initial_state_sha256'] != new['initial_state_sha256']


def test_response_channel_prefix_stable_and_global_rng_untouched():
    plan, profiles, recipe = setup('cyclic_items')
    assignment = plan.assignments('train')[0]
    a, _ = response_channels(assignment, 4)
    b, _ = response_channels(assignment, 12)
    assert all(np.array_equal(a[name], b[name][:4]) for name in a)
    assert not np.array_equal(b['outcome'], b['learning'])
    state = np.random.get_state()
    result = collect_training_fixture(plan, profiles=profiles, recipe=recipe)
    current = np.random.get_state()
    assert state[0] == current[0] and np.array_equal(state[1], current[1]) and state[2:] == current[2:]
    assert [o.query.item_id for o in result.trajectories[0].observations] == list(result.bank.item_ids[:12])


def test_collector_cannot_generate_final_or_exceed_learner_cap():
    plan, profiles, recipe = setup(count=3)
    with pytest.raises(ValueError, match='learner cap'):
        collect_training_fixture(plan, profiles=profiles, recipe=recipe)
    plan, profiles, recipe = setup()
    profiles[plan.assignments('final')[0].learner_id] = 'PY'
    with pytest.raises(ValueError, match='exactly train'):
        collect_training_fixture(plan, profiles=profiles, recipe=recipe)


@pytest.mark.parametrize('field,value', [('events_per_learner', 13), ('events_per_learner', True),
    ('start_unix_seconds', -1), ('gap_seconds', 0), ('max_wall_seconds', 31), ('policy', 'oracle_theta')])
def test_recipe_fails_before_collection(field, value):
    _, _, recipe = setup()
    with pytest.raises(ValueError):
        replace(recipe, **{field: value})


def test_unknown_profile_and_response_cap_rejected():
    plan, profiles, recipe = setup()
    with pytest.raises(ValueError, match='unknown Paper2'):
        collect_training_fixture(plan, profiles={key: 'unknown' for key in profiles}, recipe=recipe)
    with pytest.raises(ValueError, match='fixture cap'):
        response_channels(plan.assignments('train')[0], 13)


def test_wall_timeout_checked_and_preserves_failure(monkeypatch):
    import knowledge_tracing.simulator_collection as module
    plan, profiles, recipe = setup()
    ticks = iter([0, 31])
    monkeypatch.setattr(module.time, 'perf_counter', lambda: next(ticks))
    with pytest.raises(TimeoutError, match='wall budget'):
        collect_training_fixture(plan, profiles=profiles, recipe=recipe)


def test_source_identity_uses_same_paths_on_windows_and_linux():
    windows = {'notebook': 'paper2\\source.ipynb', 'inputs': {'paper2\\data\\question_bank.csv': 'hash'},
               'definitions': {'x': {'cell': 1, 'sha256': 'same'}}}
    linux = {'notebook': 'paper2/source.ipynb', 'inputs': {'paper2/data/question_bank.csv': 'hash'},
             'definitions': windows['definitions']}
    assert canonical_source_provenance(windows) == canonical_source_provenance(linux)


@pytest.mark.parametrize('already_stripped', [False, True])
def test_actual_bundle_and_already_stripped_copy_preserve_semantic_environment_identity(already_stripped):
    from knowledge_tracing.paper2_reference import ROOT, NOTEBOOK
    reference = load_reference()
    contents, _ = runpy.run_path(str(ROOT / 'scripts/akt/build_colab_bundle.py'))['bundle_contents']()
    packaged = contents[NOTEBOOK.relative_to(ROOT).as_posix()]
    original = NOTEBOOK.read_bytes()
    assert [c['source'] for c in json.loads(original)['cells']] == [c['source'] for c in json.loads(packaged)['cells']]
    before = packaged if already_stripped else original
    after = packaged
    # Portable checkout có thể đã strip: không buộc transform idempotent phải đổi bytes.
    if hashlib.sha256(before).digest() == hashlib.sha256(after).digest():
        metadata_only = json.loads(after)
        metadata_only['metadata']['domain_identity_test'] = True
        after = json.dumps(metadata_only).encode('utf-8')
    assert [c['source'] for c in json.loads(before)['cells']] == [c['source'] for c in json.loads(after)['cells']]
    assert hashlib.sha256(before).digest() != hashlib.sha256(after).digest()
    left = {**reference, 'provenance': copy.deepcopy(reference['provenance'])}
    right = {**reference, 'provenance': copy.deepcopy(reference['provenance'])}
    left['provenance']['notebook_sha256'] = hashlib.sha256(before).hexdigest()
    right['provenance']['notebook_sha256'] = hashlib.sha256(after).hexdigest()
    assert environment_semantics(left) == environment_semantics(right)


@pytest.mark.parametrize('change', ['equation', 'constant', 'graph_input'])
def test_semantic_identity_detects_scientific_changes(change):
    reference = load_reference()
    changed = {**reference, 'environment': dict(reference['environment']),
               'provenance': copy.deepcopy(reference['provenance'])}
    if change == 'equation':
        changed['provenance']['definitions']['LatentStudentEnvironment']['sha256'] = '0'*64
    elif change == 'constant':
        changed['environment']['TRUE_GAIN_SCALE'] += 1
    else:
        key = next(name for name in changed['provenance']['inputs'] if name.replace('\\', '/').endswith('/edges.csv'))
        changed['provenance']['inputs'][key] = '0'*64
    assert identity_hash(environment_semantics(changed)) != identity_hash(environment_semantics(reference))
