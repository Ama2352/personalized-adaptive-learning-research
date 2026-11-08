"""Handmade observable records; NumPy geometry only, không NN/optimizer."""
from dataclasses import replace
import builtins
import sys

import numpy as np
import pytest

from knowledge_tracing.akt import research_simulator_data as data
from knowledge_tracing.akt.types import TrainingWindow, WindowInputs
from knowledge_tracing.akt.simulator_data import (SimulatorShard, fit_simulator_encoding,
    iter_simulator_windows)
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from knowledge_tracing.simulator_data import ObservableTrajectory
from knowledge_tracing.simulator_research_data import ResearchSplitPlan, ResearchProvenance, ShardLimits, SelectionFreeze

H = 'a'*64


@pytest.fixture(autouse=True)
def no_neural_import_or_execution(monkeypatch):
    original = builtins.__import__
    def checked(name, *args, **kwargs):
        if name == 'torch' or name.startswith('torch.') or name in (
                'knowledge_tracing.akt.model', 'knowledge_tracing.akt.training',
                'knowledge_tracing.akt.simulator_engineering'):
            raise AssertionError('neural constructor/training import forbidden in BATCH1')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', checked)
    assert 'torch' not in sys.modules
    yield
    assert 'torch' not in sys.modules


def fixture():
    plan = ResearchSplitPlan('akt-data-contract-not-generated-corpus', 42, 10, 1, H)
    bank = SimulatorBank('handmade-bank', tuple(SimulatorItem(f'i{c}-{d}', f'c{c}', d)
        for c in range(28) for d in (1050, 1200, 1350)))
    result = {}; source = 1
    for role in ('train', 'selection', 'calibration'):
        indices = (0, 1, 0) if role == 'train' else ((0, 2, 1, 2, 0) if role == 'selection' else (0, 2, 1, 3))
        trajectories = []
        for assignment in plan.split_plan.assignments(role):
            rows = []
            for rank, index in enumerate(indices):
                rows.append(Observation(ItemQuery(bank.item_ids[index], 100+rank, source), rank % 2)); source += 1
            trajectories.append(ObservableTrajectory(assignment.learner_id, plan.split_plan.identity,
                identity_hash(bank.identity), 'observed-policy', tuple(rows)))
        provenance = ResearchProvenance(role, plan.identity, plan.split_plan.identity, identity_hash(bank.identity),
            'b'*64, (('collector', 'c'*64), ('environment', 'd'*64)), 'e'*64,
            'observed-policy', 'unix_seconds_utc', 'UTC', False)
        result[role] = data.ResearchAKTShard(plan, bank, role, tuple(trajectories), provenance,
            provenance.identity, ShardLimits(len(trajectories), 5, len(trajectories)*5))
    return result


def phases():
    s = fixture(); train = data.prepare_research_phase('select_train80', shards=(s['train'],))
    selection = data.prepare_research_phase('raw_selection10', shards=(s['selection'],))
    freeze = SelectionFreeze(s['train'].plan.identity, identity_hash(s['train'].bank.identity),
        s['train'].audit['audit']['shard_sha256'], s['selection'].audit['audit']['shard_sha256'],
        'f'*64, 2, 'raw_selection_before_refit')
    refit = data.prepare_research_phase('refit_union90', shards=(s['train'],s['selection']), selection_freeze=freeze)
    calibration = data.prepare_research_phase('calibration_predict', shards=(s['calibration'],), selection_freeze=freeze)
    return s, train, selection, refit, calibration


def predicted_rows(windows):
    result = []
    for entry in windows:
        if type(entry) is data.ResearchUnseenTarget:
            result.append((entry.learner_id, entry.query.source_row, entry.global_rank, False))
        else:
            w = entry.window if type(entry) is TrainingWindow else entry
            result.extend((w.inputs.user_ids[i], int(w.inputs.source_rows[i]), int(w.global_ranks[i]), True)
                          for i in np.flatnonzero(w.target_mask))
    return result


def assert_window_equal(a, b):
    wa = a.window if type(a) is TrainingWindow else a
    wb = b.window if type(b) is TrainingWindow else b
    for name in ('item_ids', 'timestamps', 'prior_responses', 'source_rows', 'sequence_offsets'):
        np.testing.assert_array_equal(getattr(wa.inputs, name), getattr(wb.inputs, name))
    for name in ('target_mask', 'global_ranks', 'history_available', 'history_used', 'context_reset'):
        np.testing.assert_array_equal(getattr(wa, name), getattr(wb, name))
    assert wa.inputs.user_ids == wb.inputs.user_ids and wa.window_id == wb.window_id
    if type(a) is TrainingWindow: np.testing.assert_array_equal(a.targets, b.targets)


def test_explicit_four_scopes_and_separate_encoding_lineage():
    s, train, selection, refit, calibration = phases()
    e80 = data.fit_research_encoding(train); e90 = data.fit_research_encoding(refit)
    assert len(train.trajectories) == 8 and len(refit.trajectories) == 9
    assert len(e80.support) == 2 and len(e90.support) == 3
    assert e80.identity != e90.identity and e80.optimization_scope == 'select_train80'
    assert e90.optimization_scope == 'refit_union90' and e90.selection_freeze_sha256 == refit.selection_freeze.identity
    assert dict(e80.support)[s['train'].bank.item_ids[0]] == 8  # Unique learners, not16events.
    assert train.manifest['history_hash_scheme'] == e80.history_hash_scheme == data.PREFIX_SCHEME
    assert {r.origin_role for r in data.research_scoring_targets(refit,e90)} == {'train','selection'}
    assert len(data.research_scoring_targets(calibration,e90)) == 4


@pytest.mark.parametrize('scope,roles', [('select_train80', ('calibration',)), ('select_train80', ('selection',)),
    ('raw_selection10', ('train',)), ('refit_union90', ('train','calibration')),
    ('refit_union90', ('selection','train')), ('calibration_predict', ('train',))])
def test_wrong_roles_reject_without_relabel(scope, roles):
    shards = fixture()
    with pytest.raises(ValueError, match='scope/role'):
        data.prepare_research_phase(scope, shards=tuple(shards[r] for r in roles))


@pytest.mark.parametrize('scope', ['raw_selection10', 'calibration_predict'])
def test_predict_only_scope_cannot_fit_vocab_or_optimize(scope):
    _, _, selection, _, calibration = phases()
    phase = selection if scope == 'raw_selection10' else calibration
    with pytest.raises(ValueError, match='vocabulary only'): data.fit_research_encoding(phase)
    # Matched proper encoding still cannot optimize prediction roles.
    _, train, _, refit, _ = phases()
    encoding = data.fit_research_encoding(train if scope == 'raw_selection10' else refit)
    with pytest.raises(ValueError, match='cannot train'):
        tuple(data.iter_research_windows(phase, encoding, context=2, target_block=2, training=True))


def test_refit_freeze_required_and_stale_freeze_rejected():
    s, _, _, refit, _ = phases()
    for freeze in (None, replace(refit.selection_freeze, train_shard_sha256='b'*64)):
        with pytest.raises(ValueError, match='freeze'):
            data.prepare_research_phase('refit_union90', shards=(s['train'],s['selection']), selection_freeze=freeze)
    with pytest.raises(ValueError, match='freeze'):
        data.prepare_research_phase('calibration_predict', shards=(s['calibration'],))


def test_raw_selection_rejects_refit_encoding_calibration_rejects_train80():
    _, train, selection, refit, calibration = phases()
    e80, e90 = data.fit_research_encoding(train), data.fit_research_encoding(refit)
    with pytest.raises(ValueError, match='precede refit'): data.research_scoring_targets(selection,e90)
    with pytest.raises(ValueError, match='refit90'): data.research_scoring_targets(calibration,e80)
    with pytest.raises(ValueError, match='lineage mismatch'): data.research_scoring_targets(train,e90)


def test_full_selection_population_and_global_oov_anchors():
    _, train, selection, _, _ = phases(); encoding = data.fit_research_encoding(train)
    windows = tuple(data.iter_research_windows(selection,encoding,context=2,target_block=2,training=False))
    expected = data.research_scoring_targets(selection,encoding)
    actual = predicted_rows(windows)
    assert len(actual) == len(expected) == 5
    assert sorted(actual) == sorted((r.learner_id,r.query.source_row,r.global_rank,r.trained_item) for r in expected)
    assert [r.global_rank for r in expected] == list(range(5))
    assert [r.trained_item for r in expected] == [True,False,True,False,True]
    known = [w for w in windows if type(w) is WindowInputs]
    assert any(w.context_reset[w.target_mask].any() for w in known)
    assert all(w.inputs.prior_responses[0] == -1 for w in known)


@pytest.mark.parametrize('training', [False, True])
def test_exact_legacy_geometry_parity_for_original_train_role(training):
    s, train, _, _, _ = phases(); encoding = data.fit_research_encoding(train)
    original = SimulatorShard(plan=s['train'].plan.split_plan,bank=s['train'].bank,role='train',
        trajectories=s['train'].trajectories,max_events_per_learner=s['train'].limits.max_events_per_learner)
    old_encoding = fit_simulator_encoding(original)
    actual = tuple(data.iter_research_windows(train,encoding,context=2,target_block=2,training=training))
    control = tuple(iter_simulator_windows(original,old_encoding,context=2,target_block=2,training=training))
    assert len(actual) == len(control)
    for a,b in zip(actual,control): assert_window_equal(a,b)


def test_future_response_perturbation_changes_sidecar_not_current_inputs_or_prefix():
    s, train, selection, _, _ = phases(); encoding=data.fit_research_encoding(train)
    trajectory = s['selection'].trajectories[0]; rows=list(trajectory.observations)
    rows[0]=replace(rows[0],correct=1-rows[0].correct)
    changed_shard=replace(s['selection'],trajectories=(replace(trajectory,observations=tuple(rows)),))
    changed=data.prepare_research_phase('raw_selection10',shards=(changed_shard,))
    before=data.research_scoring_targets(selection,encoding); after=data.research_scoring_targets(changed,encoding)
    assert before[0].history_sha256 == after[0].history_sha256
    assert before[0].correct != after[0].correct
    assert before[1].history_sha256 != after[1].history_sha256
    # First target window contains no current response, even if its block has later targets.
    a=next(data.iter_research_windows(selection,encoding,context=2,target_block=1,training=False))
    b=next(data.iter_research_windows(changed,encoding,context=2,target_block=1,training=False))
    assert_window_equal(a,b)


def test_prefix_chain_cross_encoding_same_observed_past_and_distinct_session_scheme():
    _, train, selection, refit, _ = phases()
    e80,e90=data.fit_research_encoding(train),data.fit_research_encoding(refit)
    left=data.research_scoring_targets(selection,e80)
    right=[t for t in data.research_scoring_targets(refit,e90) if t.origin_role=='selection']
    assert [t.history_sha256 for t in left] == [t.history_sha256 for t in right]
    assert all(t.history_hash_scheme == 'observable-prefix-chain-v1' for t in left+right)
    assert [t.encoding_sha256 for t in left] != [t.encoding_sha256 for t in right]


def test_calibration_outcome_not_used_to_fit_refit_vocabulary():
    s, _, _, refit, calibration=phases(); encoding=data.fit_research_encoding(refit)
    assert s['calibration'].bank.item_ids[3] not in dict(encoding.support)
    assert not data.research_scoring_targets(calibration,encoding)[-1].trained_item
    assert encoding.identity == data.fit_research_encoding(refit).identity


def test_final_rejected_before_reading_final_events():
    class FinalCanary:
        def __iter__(self): raise AssertionError('final events read')
    s=fixture()['train']
    with pytest.raises(ValueError, match='final events'):
        data.ResearchAKTShard(s.plan,s.bank,'final',FinalCanary(),s.provenance,s.expected_provenance_sha256,s.limits)


def test_source_drift_guard_without_editing_any_actual_source(monkeypatch):
    _,train,_,_,_=phases(); encoding=data.fit_research_encoding(train)
    before=data.source_identity()
    monkeypatch.setattr(data,'source_identity',lambda: (*before[:-1],(before[-1][0],'b'*64)))
    with pytest.raises(ValueError,match='source/input drift'): train.assert_integrity()
    with pytest.raises(ValueError,match='source drift'): encoding.assert_integrity()


def test_data_mutation_and_encoding_support_drift_fail_closed():
    _,train,_,_,_=phases(); encoding=data.fit_research_encoding(train)
    with pytest.raises(ValueError,match='encoding lineage/support/source drift'):
        replace(encoding,support=((encoding.support[0][0],999),)).assert_integrity()
    object.__setattr__(train,'content_sha256','b'*64)
    with pytest.raises(ValueError,match='phase/source/input drift'): train.assert_integrity()


@pytest.mark.parametrize('context,target_block,training',[(True,2,False),(-1,2,False),(2,0,False),(2,True,False),(2,2,1)])
def test_geometry_and_training_flag_types_are_explicit(context,target_block,training):
    _,train,_,_,_=phases(); encoding=data.fit_research_encoding(train)
    with pytest.raises(ValueError): tuple(data.iter_research_windows(train,encoding,context=context,target_block=target_block,training=training))
