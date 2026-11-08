"""Handmade typed observable phases; NumPy geometry, không NN/teacher/artifact.

Hai selection learners x205event; train/calibration records nhỏ chỉ để có typed
role/vocabulary lineage thật của fixture. Không corpus/trained-weight attestation.
"""
from dataclasses import asdict, FrozenInstanceError, replace
import builtins
import importlib
from types import SimpleNamespace

import numpy as np
import pytest

from knowledge_tracing.akt import research_graph_condition as condition
from knowledge_tracing.akt import research_graph_context as context
from knowledge_tracing.akt import research_simulator_data as data
from knowledge_tracing.akt.types import WindowInputs
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from knowledge_tracing.simulator_data import ObservableTrajectory
from knowledge_tracing.simulator_research_data import ResearchSplitPlan, ResearchProvenance, ShardLimits

H = 'a' * 64
HELD_CONTEXT_INDEX_CLASS = context.ResearchGraphContextIndex


@pytest.fixture(autouse=True)
def no_torch_model_solver(monkeypatch):
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split('.')[0] in {'torch', 'sklearn', 'scipy', 'pandas', 'joblib'} or name in {
            'knowledge_tracing.graph_augmentation', 'knowledge_tracing.akt.graph_prototype',
            'knowledge_tracing.akt.research_graph_model', 'knowledge_tracing.akt.model'}:
            raise AssertionError('data index must not import neural/solver code: ' + name)
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)


def limits(**changes):
    values = dict(max_total_events=500, max_events_per_learner=205, max_targets=500,
        max_windows=20, max_window_tokens=200, max_parent_records=500,
        max_observed_rows=60000, max_cache_bytes=2*1024**2, max_seconds=20.)
    values.update(changes)
    return context.ResearchGraphContextLimits(**values)


def make_shards():
    plan = ResearchSplitPlan('HANDMADE_CONTEXT_NOT_GENERATED_OR_FITTED', 42, 20, 1, H)
    bank = SimulatorBank('HANDMADE_GEOMETRY_NO_RESEARCH_FIT', tuple(
        SimulatorItem(f'i{c}-{difficulty}', f'c{c}', difficulty)
        for c in range(28) for difficulty in (1050, 1200, 1350)))
    parent, child, oov = 'i0-1050', 'i1-1050', 'i2-1050'
    shards = {}
    for role_id, role in enumerate(('train', 'selection', 'calibration')):
        trajectories = []
        for ordinal, assignment in enumerate(plan.split_plan.assignments(role)):
            count = 205 if role == 'selection' else 3
            rows = tuple(Observation(ItemQuery(oov if role == 'selection' and rank == 102
                else parent if rank % 2 == 0 else child, 1000 + rank,
                1 + role_id*100000 + ordinal*1000 + rank), int(rank % 3 == 0)) for rank in range(count))
            trajectories.append(ObservableTrajectory(assignment.learner_id, plan.split_plan.identity,
                identity_hash(bank.identity), 'handmade_observable_only', rows))
        provenance = ResearchProvenance(role, plan.identity, plan.split_plan.identity, identity_hash(bank.identity),
            H, (('collector', H), ('environment', H)), H, 'handmade_observable_only', 'unix_seconds_utc', 'UTC', False)
        shards[role] = data.ResearchAKTShard(plan, bank, role, tuple(trajectories), provenance,
            provenance.identity, ShardLimits(len(trajectories), count, len(trajectories)*count))
    return shards


def make_case(shards):
    train = data.prepare_research_phase('select_train80', shards=(shards['train'],))
    phase = data.prepare_research_phase('raw_selection10', shards=(shards['selection'],))
    encoding = data.fit_research_encoding(train)
    bank = shards['train'].bank
    binding = condition.GraphTrain80Binding('HANDMADE_NO_PUBLIC_JSONL_OR_RUNTIME_AUTHORITY', H, H,
        shards['train'].plan.identity, shards['train'].provenance.identity, H, identity_hash(bank.identity),
        shards['train'].audit['audit']['shard_sha256'], shards['selection'].audit['audit']['shard_sha256'],
        shards['calibration'].audit['audit']['shard_sha256'])
    setup = condition.prepare_research_graph_condition(variant='A1', graph_mode='expert_declared',
        bank=bank, nodes=tuple(sorted({i.concept_id for i in bank.items})), edges=(('c0', 'c1'),),
        train80=binding, expected_sources=condition.source_inventory(), topology_source_sha256=H)
    index = context.prepare_research_graph_context(phase, encoding, setup, limits=limits(),
        fit80_encoding_sha256=encoding.identity, context=100, target_block=100)
    windows = tuple(w for w in data.iter_research_windows(phase, encoding, context=100, target_block=100,
        training=False) if type(w) is WindowInputs)
    return dict(shards=shards, train=train, phase=phase, encoding=encoding, condition=setup, index=index, windows=windows)


@pytest.fixture(scope='module')
def case():
    return make_case(make_shards())


def evidence(case, learner_ordinal, rank):
    learner = sorted(t.learner_id for t in case['shards']['selection'].trajectories)[learner_ordinal]
    return next(record for window in case['index'].windows for record in window.contexts
                if record is not None and record.learner_id == learner and record.global_rank == rank)


def numerical(audit):
    # Full phase/condition/confidence provenance can change when future labels
    # change. It is the effective evidence (not all metadata) that is causal.
    return (audit.query, audit.parents, audit.observed_rows, audit.effective_start,
            audit.scoped_observations_sha256, audit.domain_sha256, audit.trained_items_sha256)


def changed(case, learner_ordinal, ranks):
    shards = dict(case['shards'])
    trajectories = list(shards['selection'].trajectories)
    learner = sorted(t.learner_id for t in trajectories)[learner_ordinal]
    index = next(i for i, t in enumerate(trajectories) if t.learner_id == learner)
    observations = list(trajectories[index].observations)
    for rank in ranks:
        observations[rank] = replace(observations[rank], correct=1-observations[rank].correct)
    trajectories[index] = replace(trajectories[index], observations=tuple(observations))
    shards['selection'] = replace(shards['selection'], trajectories=tuple(trajectories))
    return make_case(shards)


def test_cached_import_preserves_class_identity_without_optional_imports():
    # Đây là cached-import/alias check. Fresh no-Torch import được controller
    # kiểm riêng; combined collection có thể đã import Torch hợp lệ ở modeltest.
    cached = importlib.import_module('knowledge_tracing.akt.research_graph_context')
    assert cached is context
    assert cached.ResearchGraphContextIndex is HELD_CONTEXT_INDEX_CLASS


def test_full_population_and_no_oov_rescue(case):
    index = case['index']
    assert index.full_targets == 410
    assert len(index.unsupported_targets) == 2
    assert {r.global_rank for r in index.unsupported_targets} == {102}
    assert {r.reason for r in index.unsupported_targets} == {'oov_item'}
    known = [r for window in index.windows for r in window.contexts if r is not None]
    assert len(known) == 408 and all(r.audit.target_fitted for r in known)
    assert not any(r.global_rank == 102 for r in known)
    assert len({(r.learner_id, r.source_row, r.global_rank) for r in known}) == 408


@pytest.mark.parametrize('rank,start,used', [(99, 0, 99), (100, 0, 100), (199, 103, 96), (200, 103, 97)])
def test_exact_global_boundaries_and_oov_effective_past(case, rank, start, used):
    record = evidence(case, 0, rank)
    assert record.audit.effective_start == start
    assert len(record.audit.observed_rows) == used
    matching = next(w for w in case['windows'] if w.window_id == record.window_id)
    assert matching.history_used[record.local_position] == used
    assert matching.global_ranks[record.local_position] == rank
    assert record.audit.observed_rows == tuple(int(r) for r in matching.inputs.source_rows[:record.local_position])
    if rank == 200:
        assert matching.history_available[record.local_position] == 100 != used


def test_post_oov_cold_context_is_empty_not_full_prefix(case):
    record = evidence(case, 0, 103)
    assert record.audit.effective_start == 103 and record.audit.observed_rows == ()
    assert len(record.audit.parents) == 1
    assert record.audit.parents[0].support == 0
    assert record.audit.parents[0].mean_observed_correctness is None


def test_current_and_future_response_invariance(case):
    alternate = changed(case, 0, (99, 150, 204))
    assert numerical(evidence(case, 0, 99).audit) == numerical(evidence(alternate, 0, 99).audit)
    assert case['index'].phase_sha256 != alternate['index'].phase_sha256
    assert case['index'].identity != alternate['index'].identity


def test_past_response_positive_control(case):
    alternate = changed(case, 0, (100,))
    before, after = evidence(case, 0, 101).audit, evidence(alternate, 0, 101).audit
    assert before.observed_rows == after.observed_rows
    assert before.parents[0].support == after.parents[0].support == 51
    assert before.parents[0].mean_observed_correctness != after.parents[0].mean_observed_correctness
    assert before.scoped_observations_sha256 != after.scoped_observations_sha256


def test_peer_learner_isolation(case):
    alternate = changed(case, 1, (0, 50, 100, 204))
    for rank in (0, 99, 100, 103, 199, 200, 204):
        assert numerical(evidence(case, 0, rank).audit) == numerical(evidence(alternate, 0, rank).audit)


def test_for_windows_exact_position_alignment_and_non_targets(case):
    result = case['index'].for_windows(case['windows'])
    for window, contexts in zip(case['windows'], result):
        assert len(contexts) == len(window.inputs.item_ids)
        for local, record in enumerate(contexts):
            assert (record is None) == (not window.target_mask[local])
            if record is not None:
                assert record.local_position == local and record.window_id == window.window_id
                assert record.source_row == int(window.inputs.source_rows[local])
                assert record.global_rank == int(window.global_ranks[local])


@pytest.mark.parametrize('kind', ['missing', 'ducktyped_label_carrier'])
def test_wrong_causal_input_type_rejected_before_read(case, kind):
    original = case['windows'][0]
    inputs = None if kind == 'missing' else SimpleNamespace(**vars(original.inputs), labels=np.zeros(len(original.inputs.item_ids)))
    with pytest.raises(ValueError, match='exact label-free CausalSequenceInputs'):
        case['index'].for_windows((replace(original, inputs=inputs),))


def test_non_native_concept_input_is_not_silently_ignored(case):
    original = case['windows'][0]
    inputs = replace(original.inputs, concept_ids=np.zeros(len(original.inputs.item_ids), dtype=np.int64))
    with pytest.raises(ValueError, match='item-only'):
        case['index'].for_windows((replace(original, inputs=inputs),))


@pytest.mark.parametrize('field', ['item_ids', 'timestamps', 'prior_responses', 'source_rows', 'user_ids'])
def test_original_input_binding_rejects_mutation(case, field):
    original = case['windows'][0]
    if field == 'user_ids':
        inputs = replace(original.inputs, user_ids=('foreign',)*len(original.inputs.user_ids))
    else:
        array = getattr(original.inputs, field).copy()
        array[-1] += 1
        inputs = replace(original.inputs, **{field: array})
    with pytest.raises(ValueError):
        case['index'].for_windows((replace(original, inputs=inputs),))


@pytest.mark.parametrize('field', ['target_mask', 'global_ranks', 'history_available', 'history_used', 'context_reset', 'window_id'])
def test_original_geometry_binding_rejects_mutation(case, field):
    original = case['windows'][0]
    if field == 'window_id':
        value = H
    else:
        value = getattr(original, field).copy()
        if value.dtype == bool:
            value[-1] = not value[-1]
        else:
            value[-1] += 1
    with pytest.raises(ValueError):
        case['index'].for_windows((replace(original, **{field: value}),))


def test_duplicate_window_and_unsupported_object_rejected(case):
    with pytest.raises(ValueError, match='duplicate'):
        case['index'].for_windows((case['windows'][0], case['windows'][0]))
    oov = next(w for w in data.iter_research_windows(case['phase'], case['encoding'],
        context=100, target_block=100, training=False) if type(w) is data.ResearchUnseenTarget)
    with pytest.raises(ValueError, match='OOV'):
        case['index'].for_windows((oov,))


def test_index_keeps_no_phase_trajectories_labels_or_arrays(case):
    index = case['index']
    assert not any(hasattr(index, name) for name in ('phase', 'encoding', 'condition', 'bank', 'trajectories', 'corpus'))
    def inspect(value):
        assert not isinstance(value, np.ndarray)
        if isinstance(value, dict):
            assert not {'trajectories', 'observations', 'correct', 'labels'} & value.keys()
            for item in value.values(): inspect(item)
        elif isinstance(value, (tuple, list)):
            for item in value: inspect(item)
    inspect(asdict(index))
    with pytest.raises(FrozenInstanceError):
        index.full_targets = 1


@pytest.mark.parametrize('changes', [dict(context=99), dict(target_block=99), dict(fit80_encoding_sha256=H)])
def test_wrong_geometry_or_fit80_encoding_rejected(case, changes):
    args = dict(limits=limits(), fit80_encoding_sha256=case['encoding'].identity, context=100, target_block=100)
    args.update(changes)
    with pytest.raises(ValueError):
        context.prepare_research_graph_context(case['phase'], case['encoding'], case['condition'], **args)


@pytest.mark.parametrize('limit,value', [('max_total_events', 409), ('max_events_per_learner', 204),
    ('max_targets', 409), ('max_windows', 1), ('max_window_tokens', 99),
    ('max_parent_records', 1), ('max_observed_rows', 1), ('max_cache_bytes', 1)])
def test_explicit_cache_bounds(case, limit, value):
    with pytest.raises(ValueError, match='cap|limit|bounded'):
        context.prepare_research_graph_context(case['phase'], case['encoding'], case['condition'],
            limits=limits(**{limit: value}), fit80_encoding_sha256=case['encoding'].identity, context=100, target_block=100)


@pytest.mark.parametrize('field', ['plan_sha256', 'selection_shard_sha256', 'train_shard_sha256'])
def test_foreign_condition_plan_and_role_cannot_be_relabelled(case, field):
    binding = replace(case['condition'].train80, **{field: H})
    setup = condition.prepare_research_graph_condition(variant='A1', graph_mode='expert_declared',
        bank=case['shards']['train'].bank, nodes=case['condition'].nodes, edges=case['condition'].edges,
        train80=binding, expected_sources=condition.source_inventory(), topology_source_sha256=H)
    with pytest.raises(ValueError, match='lineage|mismatch|bindings'):
        context.prepare_research_graph_context(case['phase'], case['encoding'], setup,
            limits=limits(), fit80_encoding_sha256=case['encoding'].identity, context=100, target_block=100)


def test_encoding_fit_on_different_train_inputs_rejected(case):
    shard = case['shards']['train']
    trajectory = shard.trajectories[0]
    first = replace(trajectory.observations[0], correct=1-trajectory.observations[0].correct)
    alternate_shard = replace(shard, trajectories=(replace(trajectory,
        observations=(first,)+trajectory.observations[1:]),)+shard.trajectories[1:])
    alternate_phase = data.prepare_research_phase('select_train80', shards=(alternate_shard,))
    alternate_encoding = data.fit_research_encoding(alternate_phase)
    with pytest.raises(ValueError, match='lineage'):
        context.prepare_research_graph_context(case['phase'], alternate_encoding, case['condition'],
            limits=limits(), fit80_encoding_sha256=alternate_encoding.identity, context=100, target_block=100)


def test_context_payload_and_sources_are_sealed(case, monkeypatch):
    sources = case['index'].sources_sha256
    monkeypatch.setattr(context, 'source_inventory', lambda: sources[:-1])
    with pytest.raises(ValueError, match='source drift'):
        case['index'].for_windows((case['windows'][0],))
