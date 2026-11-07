"""Role-aware simulator windows; fixtures số học, không train NN."""

from dataclasses import replace

import numpy as np
import pytest

from knowledge_tracing.akt.simulator_data import (SimulatorShard, SimulatorEncoding, SimulatorUnseenQuery,
    fit_simulator_encoding, iter_simulator_windows, scoring_targets)
from knowledge_tracing.akt.types import KTEvent, LearnerEvents, TrainingWindow
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem, ItemQuery, Observation, identity_hash
from knowledge_tracing.simulator_data import ROLES, SimulatorSplitPlan, ObservableTrajectory


def fixture():
    bank = SimulatorBank('sim-window-unit-fixture', tuple(SimulatorItem(i, i.upper(), 0) for i in 'abz'))
    plan = SimulatorSplitPlan('role-aware-unit-only', 42, tuple((r, 1) for r in ROLES))
    shards = {}
    for ordinal, role in enumerate(ROLES):
        assignment = plan.assignments(role)[0]
        items = 'abababababa' if role == 'train' else 'azbabzaabba'
        observations = tuple(Observation(ItemQuery(item, i, ordinal*20+i+1), i % 2) for i, item in enumerate(items))
        trajectory = ObservableTrajectory(assignment.learner_id, plan.identity, identity_hash(bank.identity),
                                          'arithmetic-role-fixture', observations)
        shards[role] = SimulatorShard(plan, bank, role, 12, (trajectory,))
    return shards, fit_simulator_encoding(shards['train'])


def records(shard, encoding, training=False, context=3, target_block=2):
    return list(iter_simulator_windows(shard, encoding, training=training, context=context, target_block=target_block))


def test_train_only_encoding_support_immutable_and_no_fake_fold():
    shards, encoding = fixture()
    assert encoding.support == (('a', 1), ('b', 1))
    changed = encoding.exercise_encoding()
    changed.train_support_students['alien'] = 7
    assert 'alien' not in encoding.exercise_encoding().train_support_students
    with pytest.raises(ValueError, match='only fit train'):
        fit_simulator_encoding(shards['selection'])
    windows = records(shards['train'], encoding, training=True)
    assert all(isinstance(w, TrainingWindow) for w in windows)
    assert sum(int(w.window.target_mask.sum()) for w in windows) == 11
    assert all(not hasattr(w, 'fold') for w in windows)
    assert all(w.window.inputs.concept_ids is None for w in windows)


@pytest.mark.parametrize('context,target_block', [(3, 2), (0, 2), (100, 100)])
def test_matches_existing_akt_geometry_without_using_junyi_types_in_production(context, target_block):
    shards, encoding = fixture()
    trajectory = shards['train'].trajectories[0]
    # Chỉ test legacy-reference parity; adapter production không tạo fold.
    learner = LearnerEvents(trajectory.learner_id, 1, tuple(KTEvent(trajectory.learner_id,
        o.query.item_id, o.query.timestamp, o.query.source_row, o.correct, 0, 1) for o in trajectory.observations))
    old = list(iter_windows(learner, encoding.exercise_encoding(), context=context, target_block=target_block, training=True))
    new = records(shards['train'], encoding, training=True, context=context, target_block=target_block)
    assert len(old) == len(new)
    for left, right in zip(old, new, strict=True):
        assert np.array_equal(left.targets, right.targets)
        for name in ('target_mask', 'global_ranks', 'history_available', 'history_used', 'context_reset'):
            assert np.array_equal(getattr(left.window, name), getattr(right.window, name))
        for name in ('item_ids', 'timestamps', 'prior_responses', 'source_rows', 'sequence_offsets'):
            assert np.array_equal(getattr(left.window.inputs, name), getattr(right.window.inputs, name))
        assert left.window.window_id == right.window.window_id


def test_selection_oov_coverage_and_barrier_target_population():
    shards, encoding = fixture()
    targets = scoring_targets(shards['selection'], encoding)
    windows = records(shards['selection'], encoding)
    unseen = [w for w in windows if isinstance(w, SimulatorUnseenQuery)]
    assert [w.global_rank for w in unseen] == [1, 5]
    assert all(not hasattr(w, 'correct') for w in unseen)
    scored = [int(rank) for w in windows if not isinstance(w, SimulatorUnseenQuery)
              for rank in w.global_ranks[w.target_mask]]
    assert sorted(scored + [w.global_rank for w in unseen]) == list(range(11))
    assert len(set(scored)) == 9 and sum(t.trained_item for t in targets) == 9
    for window in windows:
        if isinstance(window, SimulatorUnseenQuery):
            continue
        assert window.inputs.prior_responses[0] == -1
        assert np.all(window.inputs.item_ids >= 0)
        if 6 in window.global_ranks[window.target_mask]:
            assert window.global_ranks[0] == 6 and window.context_reset[-1]


def test_current_and_future_labels_never_change_input_prefix_for_current_target():
    shards, encoding = fixture()
    original = shards['selection']
    trajectory = original.trajectories[0]
    changed = replace(trajectory, observations=tuple(replace(o, correct=1-o.correct) if i >= 7 else o
                                                     for i, o in enumerate(trajectory.observations)))
    alternate = replace(original, trajectories=(changed,))
    before, after = records(original, encoding), records(alternate, encoding)
    for left, right in zip(before, after, strict=True):
        if isinstance(left, SimulatorUnseenQuery):
            continue
        for local, global_rank in enumerate(left.global_ranks):
            if global_rank <= 7:
                assert np.array_equal(left.inputs.prior_responses[:local+1], right.inputs.prior_responses[:local+1])
        assert not hasattr(left, 'targets')
    assert scoring_targets(original, encoding)[7].correct != scoring_targets(alternate, encoding)[7].correct


@pytest.mark.parametrize('role,training', [('selection', True), ('calibration', True), ('calibration', False),
                                        ('final', True), ('final', False)])
def test_role_guards_do_not_enable_refit_calibration_or_final(role, training):
    shards, encoding = fixture()
    with pytest.raises(ValueError, match='no calibration/refit/final'):
        records(shards[role], encoding, training=training)
    if role in {'calibration', 'final'}:
        with pytest.raises(ValueError, match='no calibration/refit/final'):
            scoring_targets(shards[role], encoding)


@pytest.mark.parametrize('case', ['plan', 'domain', 'vocabulary', 'train_data'])
def test_encoding_binding_fails_closed(case):
    shards, encoding = fixture()
    train = shards['train']
    if case == 'plan':
        encoding = replace(encoding, plan_sha256='0'*64)
    elif case == 'domain':
        encoding = replace(encoding, domain_sha256='0'*64)
    elif case == 'vocabulary':
        encoding = replace(encoding, support=(('alien', 1),))
    else:
        trajectory = train.trajectories[0]
        train = replace(train, trajectories=(replace(trajectory, observations=trajectory.observations[:10]),))
    with pytest.raises(ValueError):
        records(train, encoding, training=True)


def test_encoding_normalizes_mutable_support_and_shard_rejects_wrong_role():
    shards, encoding = fixture()
    mutable = [['a', 1], ['b', 1]]
    normalized = replace(encoding, support=mutable)
    mutable[0][0] = 'alien'
    assert normalized.support == encoding.support
    with pytest.raises(ValueError, match='wrong-role'):
        replace(shards['train'], trajectories=shards['selection'].trajectories)


@pytest.mark.parametrize('context,target_block', [(True, 2), (-1, 2), (3, 0), (3, True)])
def test_bad_window_budget_rejected(context, target_block):
    shards, encoding = fixture()
    with pytest.raises(ValueError, match='geometry'):
        records(shards['train'], encoding, context=context, target_block=target_block)


def test_existing_cpu_collator_accepts_adapter_and_scores_exact_target_rows():
    from knowledge_tracing.akt.tensors import collate_windows
    shards, encoding = fixture()
    windows = records(shards['train'], encoding, training=True)
    batch = collate_windows([w.window for w in windows], targets=[w.targets for w in windows],
                            n_items=len(encoding.support), device='cpu')
    expected = {target.query.source_row: target.correct for target in scoring_targets(shards['train'], encoding)}
    rows = batch.source_rows[batch.target_mask.numpy()]
    labels = batch.loss_targets[batch.target_mask].numpy()
    assert len(rows) == 11 and len(set(rows)) == 11
    assert labels.tolist() == [expected[row] for row in rows]
    selection_windows = [w for w in records(shards['selection'], encoding) if not isinstance(w, SimulatorUnseenQuery)]
    prediction = collate_windows(selection_windows, n_items=len(encoding.support), device='cpu')
    assert (prediction.loss_targets == -1).all().item()
