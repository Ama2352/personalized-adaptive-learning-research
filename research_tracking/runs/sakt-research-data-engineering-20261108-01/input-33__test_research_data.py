"""Fixtures observables tự dựng in-memory; không corpus thật/teacher/Torch/fit.

Import đúng package public; root controller fresh-process kiểm tuyệt đối không
Torch. Guard cục bộ chỉ khẳng định không import/thêm Torch trong các test này,
không giả định những test SAKT khác chưa import Torch từ trước.
"""
from dataclasses import asdict, replace
import builtins
import importlib
import json
import sys

import numpy as np
import pytest

from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, PublicResearchCorpus, PublicRoleData, PUBLIC_FILES
from knowledge_tracing.simulator_data import ObservableTrajectory
from knowledge_tracing.simulator_research_data import (
    ResearchSplitPlan, ResearchProvenance, SelectionFreeze, audit_research_shard,
)


H = 'a' * 64


@pytest.fixture(autouse=True)
def no_neural_import(monkeypatch):
    original = builtins.__import__
    before = {name for name in sys.modules if name == 'torch' or name.startswith('torch.')}

    def checked(name, *args, **kwargs):
        if name == 'torch' or name.startswith('torch.') or name in (
                'knowledge_tracing.sakt.model', 'knowledge_tracing.sakt.tensors',
                'knowledge_tracing.sakt.training', 'knowledge_tracing.akt.model',
                'knowledge_tracing.akt.training'):
            raise AssertionError('SAKT research-data tests cannot import neural model/trainer')
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', checked)
    yield
    assert {name for name in sys.modules if name == 'torch' or name.startswith('torch.')} == before


@pytest.fixture
def data():
    return importlib.import_module('knowledge_tracing.sakt.research_data')


def seal(corpus):
    payload = dict(corpus_id=corpus.corpus_id, plan=asdict(corpus.plan), bank=asdict(corpus.bank),
                   roles=[asdict(role) for role in corpus.roles], corpus_manifest_json=corpus.corpus_manifest_json,
                   files_sha256=corpus.files_sha256, done_sha256=corpus.done_sha256,
                   source_bindings=corpus.source_bindings)
    return replace(corpus, content_sha256=identity_hash(payload))


@pytest.fixture
def corpus():
    plan = ResearchSplitPlan('sakt-handmade-not-collected-corpus', 42, 10, 1, H)
    bank = SimulatorBank('sakt-handmade-bank', tuple(
        SimulatorItem(f'i{concept:02}-{difficulty}', f'c{concept:02}', difficulty)
        for concept in range(28) for difficulty in (1050, 1200, 1350)))
    limits = CorpusReadLimits(2**20, 8*2**20, 2**18, 8, 8, 80, 10.)
    ordinals = {a.learner_id: i for i, a in enumerate(plan.split_plan.assignments())}
    roles = []
    for role, indices in [('train', (0, 1, 0, 1)), ('selection', (0, 2, 1, 2, 0)),
                          ('calibration', (3, 0, 1, 3))]:
        trajectories = []
        for assignment in plan.split_plan.assignments(role):
            observations = tuple(Observation(ItemQuery(bank.item_ids[index], 100+rank,
                ordinals[assignment.learner_id]*1000000+rank+1), rank % 2)
                for rank, index in enumerate(indices))
            trajectories.append(ObservableTrajectory(assignment.learner_id, plan.split_plan.identity,
                identity_hash(bank.identity), 'handmade-observable-policy', observations))
        provenance = ResearchProvenance(role, plan.identity, plan.split_plan.identity, identity_hash(bank.identity),
            'b'*64, (('collector', 'c'*64), ('environment', 'd'*64)), 'e'*64,
            'handmade-observable-policy', 'unix_seconds_utc', 'UTC', False)
        trajectories = tuple(sorted(trajectories, key=lambda t: t.learner_id))
        audit = audit_research_shard(trajectories, plan=plan, bank=bank, role=role, provenance=provenance,
            expected_provenance_sha256=provenance.identity, limits=limits.shard_limits, reference_items=bank.item_ids)
        counts = tuple(sum(o.correct == label for t in trajectories for o in t.observations) for label in (0, 1))
        roles.append(PublicRoleData(role, provenance, trajectories,
            json.dumps({'fixture_only': True}), json.dumps(audit, sort_keys=True), counts))
    # Actual typed object/seal, with explicit manufactured publication metadata.
    # No claim this object passed the disk reader or that SHA placeholders are files.
    return seal(PublicResearchCorpus('handmade-not-published', plan, bank, tuple(roles),
        json.dumps({'fixture_only': True}), tuple((name, H, 1) for name in PUBLIC_FILES),
        H, (('fixture-only-source', H),), limits, 10, 0., ''))


def recipe(data, *, cold='query_only', context=2, padding='left'):
    return data.SAKTDataRecipe(context, padding, cold, 'sliding_last_context', 'window_relative_interaction_rank')


def view(data, corpus, scope='select_train80', **kwargs):
    return data.prepare_sakt_research_view(corpus, scope=scope, recipe=recipe(data), **kwargs)


def freeze(corpus):
    return SelectionFreeze(corpus.plan.identity, identity_hash(corpus.bank.identity),
        corpus.role_data('train').audit['audit']['shard_sha256'],
        corpus.role_data('selection').audit['audit']['shard_sha256'], 'f'*64, 2, 'raw_selection_before_refit')


def changed_role(corpus, name, mutate):
    role = corpus.role_data(name)
    trajectories = mutate(role.trajectories)
    audit = audit_research_shard(trajectories, plan=corpus.plan, bank=corpus.bank, role=name,
        provenance=role.provenance, expected_provenance_sha256=role.provenance.identity,
        limits=corpus.limits.shard_limits, reference_items=corpus.bank.item_ids)
    counts = tuple(sum(o.correct == label for t in trajectories for o in t.observations) for label in (0, 1))
    updated = replace(role, trajectories=trajectories, audit_json=json.dumps(audit, sort_keys=True), class_counts=counts)
    return seal(replace(corpus, roles=tuple(updated if r.role == name else r for r in corpus.roles)))


def test_real_package_data_import_preserves_public_names_without_model_import(data):
    package = importlib.import_module('knowledge_tracing.sakt')
    assert package.__name__ == 'knowledge_tracing.sakt'
    assert package.__all__ == ['SAKTConfig', 'SAKTCore', 'SAKTOutput', 'SAKTInputs', 'collate_sequences']
    assert package.SAKTConfig.__module__ == 'knowledge_tracing.sakt.config'
    assert data.__name__ == 'knowledge_tracing.sakt.research_data'
    with pytest.raises(AttributeError):
        getattr(package, 'not_a_public_export')


def test_four_scopes_use_real_roles_limits_freeze_and_separate_vocabularies(data, corpus):
    train = view(data, corpus)
    selection = view(data, corpus, 'raw_selection10', encoding=train.encoding)
    selected = freeze(corpus)
    refit = view(data, corpus, 'refit_union90', selection_freeze=selected)
    calibration = view(data, corpus, 'calibration_predict', encoding=refit.encoding, selection_freeze=selected)
    assert [len(v.phase.trajectories) for v in (train, selection, refit, calibration)] == [8, 1, 9, 1]
    assert len(train.vocabulary.values) == 2 and len(refit.vocabulary.values) == 3
    assert refit.encoding.selection_freeze_sha256 == selected.identity
    assert {r.origin_role for r in data.sakt_research_scoring_targets(refit)} == {'train', 'selection'}
    for v in (train, selection, refit, calibration):
        for shard in v.phase.shards:
            assert shard.provenance == corpus.role_data(shard.role).provenance
            assert shard.limits == corpus.limits.shard_limits
        assert v.identity == v.identity and v._payload()['target_block'] == 1


@pytest.mark.parametrize('scope', ['raw_selection10', 'calibration_predict'])
def test_prediction_scope_cannot_create_vocab_or_optimize(data, corpus, scope):
    with pytest.raises(ValueError):
        view(data, corpus, scope)
    train = view(data, corpus)
    if scope == 'raw_selection10':
        target = view(data, corpus, scope, encoding=train.encoding)
    else:
        selected = freeze(corpus)
        refit = view(data, corpus, 'refit_union90', selection_freeze=selected)
        target = view(data, corpus, scope, encoding=refit.encoding, selection_freeze=selected)
    with pytest.raises(ValueError, match='cannot train'):
        tuple(data.iter_sakt_research_inputs(target, training=True))


@pytest.mark.parametrize('scope', ['final', 'validation', 'refit100'])
def test_unknown_final_and_legacy_roles_are_not_accepted(data, corpus, scope):
    with pytest.raises(ValueError, match='four scopes'):
        view(data, corpus, scope)


def test_refit_requires_matching_selection_freeze(data, corpus):
    for selected in (None, replace(freeze(corpus), train_shard_sha256='b'*64)):
        with pytest.raises(ValueError, match='freeze'):
            view(data, corpus, 'refit_union90', selection_freeze=selected)


def test_selection_and_calibration_reject_wrong_encoding_lineage(data, corpus):
    train = view(data, corpus)
    selected = freeze(corpus)
    refit = view(data, corpus, 'refit_union90', selection_freeze=selected)
    with pytest.raises(ValueError, match='precede refit'):
        view(data, corpus, 'raw_selection10', encoding=refit.encoding)
    with pytest.raises(ValueError, match='refit90'):
        view(data, corpus, 'calibration_predict', encoding=train.encoding, selection_freeze=selected)


def test_role_or_seed_family_identity_cannot_be_relabelled(data, corpus):
    train = corpus.role_data('train')
    selection = corpus.role_data('selection')
    wrong = replace(train, trajectories=(selection.trajectories[0], *train.trajectories[1:]))
    bad = seal(replace(corpus, roles=(wrong, *corpus.roles[1:])))
    with pytest.raises(ValueError, match='wrong-role'):
        view(data, bad)


@pytest.mark.parametrize('cold', ['query_only', 'unsupported'])
def test_cold_and_oov_keep_full_population_and_barriers(data, corpus, cold):
    train = view(data, corpus)
    selection = data.prepare_sakt_research_view(corpus, scope='raw_selection10',
        recipe=recipe(data, cold=cold), encoding=train.encoding)
    rows = tuple(data.iter_sakt_research_inputs(selection, training=False))
    assert len(rows) == len(data.sakt_research_scoring_targets(selection)) == 5
    assert [row.global_rank for row in rows] == list(range(5))
    assert [row.support_reason for row in rows] == [
        'cold_query_only' if cold == 'query_only' else 'cold_unsupported', 'oov_item',
        'cold_query_only' if cold == 'query_only' else 'cold_unsupported', 'oov_item',
        'cold_query_only' if cold == 'query_only' else 'cold_unsupported']
    assert rows[2].context_reset and rows[4].context_reset
    assert all(row.history_used == 0 for row in rows)
    assert all(row.inputs is None and row.target_mask is None for row in rows if not row.eligible)
    assert not any(hasattr(row, 'correct') or hasattr(row, 'target') for row in rows)


@pytest.mark.parametrize('padding', ['left', 'right'])
def test_terminal_only_masks_local_positions_train_truth_and_input_immutability(data, corpus, padding):
    prepared = data.prepare_sakt_research_view(corpus, scope='select_train80', recipe=recipe(data, padding=padding))
    before = corpus.identity
    rows = tuple(data.iter_sakt_research_inputs(prepared, training=True))
    truth = data.sakt_research_scoring_targets(prepared)
    assert len(rows) == len(truth) == 32
    assert len({r.inputs.query.source_row for r in rows}) == 32
    for row, target in zip(rows, truth):
        record = row.inputs
        assert row.target == target.correct
        assert record.inputs.prior_responses[0] == -1
        n = len(record.inputs.item_ids)
        assert n <= 3 and record.history_used == n-1
        assert record.target_mask.sum() == 1 and record.target_mask[-1]
        np.testing.assert_array_equal(record.position_ids, np.arange(n))
        assert record.inputs.prior_responses[-1] == (-1 if n == 1 else 1-row.target)
        for array in (record.inputs.item_ids, record.inputs.prior_responses, record.target_mask, record.position_ids):
            assert not array.flags.writeable
        with pytest.raises(ValueError):
            record.inputs.prior_responses[0] = 1
    assert corpus.identity == before


def test_unsupported_cold_training_is_accounted_without_loss_input(data, corpus):
    prepared = data.prepare_sakt_research_view(corpus, scope='select_train80', recipe=recipe(data, cold='unsupported'))
    rows = tuple(data.iter_sakt_research_inputs(prepared, training=True))
    assert len(rows) == 32 and sum(row.inputs.eligible for row in rows) == 24
    excluded = [row for row in rows if not row.inputs.eligible]
    assert len(excluded) == 8 and all(row.inputs.inputs is None for row in excluded)
    assert all(row.inputs.support_reason == 'cold_unsupported' for row in excluded)


def test_current_future_labels_change_sidecar_not_current_inputs_or_prefix(data, corpus):
    train = view(data, corpus)
    def perturb(trajectories):
        trajectory = trajectories[0]
        observations = list(trajectory.observations)
        for rank in (2, 3):
            observations[rank] = replace(observations[rank], correct=1-observations[rank].correct)
        return (replace(trajectory, observations=tuple(observations)), *trajectories[1:])
    changed = changed_role(corpus, 'train', perturb)
    after = view(data, changed)
    a = tuple(data.iter_sakt_research_inputs(train, training=False))[:3]
    b = tuple(data.iter_sakt_research_inputs(after, training=False))[:3]
    for left, right in zip(a, b):
        assert left.history_sha256 == right.history_sha256
        for name in ('item_ids', 'prior_responses', 'source_rows', 'timestamps'):
            np.testing.assert_array_equal(getattr(left.inputs, name), getattr(right.inputs, name))
    assert data.sakt_research_scoring_targets(train)[2].correct != data.sakt_research_scoring_targets(after)[2].correct


def test_peer_learner_response_changes_do_not_change_other_learner_inputs(data, corpus):
    before = view(data, corpus)
    def perturb(trajectories):
        first = trajectories[0]
        changed = replace(first, observations=tuple(replace(o, correct=1-o.correct) for o in first.observations))
        return (changed, *trajectories[1:])
    after = view(data, changed_role(corpus, 'train', perturb))
    peer = before.phase.trajectories[-1].learner_id
    a = [r for r in data.iter_sakt_research_inputs(before, training=False) if r.learner_id == peer]
    b = [r for r in data.iter_sakt_research_inputs(after, training=False) if r.learner_id == peer]
    assert len(a) == len(b) == 4
    for left, right in zip(a, b):
        assert left.history_sha256 == right.history_sha256
        np.testing.assert_array_equal(left.inputs.prior_responses, right.inputs.prior_responses)


def test_stale_public_seal_audit_and_source_are_rejected(data, corpus, monkeypatch):
    with pytest.raises(ValueError, match='result changed'):
        view(data, replace(corpus, corpus_manifest_json='{}'))
    role = corpus.role_data('train')
    forged = seal(replace(corpus, roles=(replace(role, audit_json='{}'), *corpus.roles[1:])))
    with pytest.raises(ValueError, match='audit'):
        view(data, forged)
    prepared = view(data, corpus)
    original = data.source_identity()
    monkeypatch.setattr(data, 'source_identity', lambda: (*original[:-1], ('changed', H)))
    with pytest.raises(ValueError, match='changed'):
        tuple(data.iter_sakt_research_inputs(prepared, training=False))


def test_partial_iterator_does_not_claim_completed_population(data, corpus):
    prepared = view(data, corpus)
    stream = data.iter_sakt_research_inputs(prepared, training=False)
    first = next(stream)
    assert first.global_rank == 0
    assert not hasattr(first, 'completed') and not hasattr(first, 'fitted')
    stream.close()
