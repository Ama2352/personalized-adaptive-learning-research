"""Frozen SAKT inference trên random weights: không trainer/fitted efficacy."""

from copy import deepcopy
from dataclasses import replace
import hashlib

import numpy as np
import pytest
import torch

from knowledge_tracing.sakt.config import SAKTConfig
from knowledge_tracing.sakt.model import SAKTCore
from knowledge_tracing.sakt.tensors import collate_sequences
from knowledge_tracing.sakt.adapter import (
    FrozenSAKTAdapter, SAKTHistory, SAKTInferenceSpec, inference_identity, load_frozen_sakt,
)
from knowledge_tracing.shared_kt import CausalSequenceInputs, StableVocabulary
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem


@pytest.fixture(autouse=True)
def bounded_cpu_rng():
    threads = torch.get_num_threads()
    torch.set_num_threads(1)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(42)
        yield
    torch.set_num_threads(threads)


@pytest.fixture
def case(tmp_path):
    config = SAKTConfig(num_items=3, max_length=4, d_model=8, num_heads=2,
                        head_dim=4, dropout=0.2, layer_norm_eps=1e-5)
    vocabulary = StableVocabulary(('A', 'B', 'C'))
    bank = SimulatorBank('synthetic-sakt-fixture-not-trained', tuple(
        SimulatorItem(name, 'concept-' + name, 1000 + 100 * i) for i, name in enumerate('ABCD')))
    spec = SAKTInferenceSpec(context=2, window_policy='sliding_last_context',
        position_policy='window_relative_interaction_rank', first_target_policy='query_only',
        padding_side='right', batch_size=3, device='cpu', precision='float32')
    core = SAKTCore(config)
    path = tmp_path / 'random_fixture_raw_state_dict.pt'
    torch.save(core.state_dict(), path)
    return dict(path=path, config=config, vocabulary=vocabulary, bank=bank, spec=spec,
                expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                expected_identity=inference_identity(config, vocabulary, bank, spec, weight_role='random_fixture'),
                weight_role='random_fixture', max_checkpoint_bytes=1_000_000)


def load(case, **changes):
    return load_frozen_sakt(**{**case, **changes})


def inputs(items=(0, 1, 2, 0, 1), labels=(1, 0, 1, 0, 1), user='a', source_start=1):
    n = len(items)
    return CausalSequenceInputs(np.asarray(items, dtype=np.int64), np.arange(n, dtype=np.int64),
        np.asarray([-1, *labels[:-1]], dtype=np.int64), np.arange(source_start, source_start + n),
        np.asarray([0, n]), (user,) * n)


def history(labels=(1, 0), learner='a', items=('A', 'B')):
    return SAKTHistory(learner, tuple(Observation(ItemQuery(name, i, i + 1), label)
                                      for i, (name, label) in enumerate(zip(items, labels))))


def probabilities(scores):
    return np.asarray([np.nan if score.probability is None else score.probability for score in scores])


def test_load_and_inference_preserve_rng_checkpoint_and_inputs(case):
    rng = torch.get_rng_state().clone()
    checkpoint = case['path'].read_bytes()
    adapter = load(case)
    sequence = inputs()
    before = deepcopy(sequence)
    predictions = adapter.predict(sequence)
    assert predictions.shape == (5,) and np.isfinite(predictions).all()
    assert torch.equal(rng, torch.get_rng_state())
    assert case['path'].read_bytes() == checkpoint
    for name in ('item_ids', 'timestamps', 'prior_responses', 'source_rows', 'sequence_offsets'):
        np.testing.assert_array_equal(getattr(sequence, name), getattr(before, name))
    assert not adapter._model.training
    assert all(not parameter.requires_grad and parameter.grad is None for parameter in adapter._model.parameters())
    assert {score.weight_role for score in adapter.predict_details(sequence)} == {'random_fixture'}


def test_direct_constructor_fit_and_fitted_online_path_are_not_available(case):
    with pytest.raises(TypeError, match='load_frozen_sakt'):
        FrozenSAKTAdapter(None, None, None, None, checkpoint_sha256='0' * 64, identity={})
    adapter = load(case)
    with pytest.raises(NotImplementedError, match='trainer'):
        adapter.fit(inputs(), np.zeros(5))
    with pytest.raises(NotImplementedError, match='selected-fit'):
        adapter.as_online_backend()
    with pytest.raises(ValueError, match='fitted provenance'):
        inference_identity(case['config'], case['vocabulary'], case['bank'], case['spec'], weight_role='selected_fitted')


@pytest.mark.parametrize('change', ['sha', 'config', 'vocabulary', 'domain', 'bank_metadata', 'geometry', 'source'])
def test_loader_rejects_wrong_hash_and_binding(case, change):
    changes = {}
    if change == 'sha':
        changes['expected_sha256'] = '0' * 64
    elif change == 'config':
        changes['config'] = replace(case['config'], dropout=0.0)
    elif change == 'vocabulary':
        changes['vocabulary'] = StableVocabulary(('A', 'B', 'D'))
    elif change == 'domain':
        changes['bank'] = replace(case['bank'], environment_id='other-domain')
    elif change == 'bank_metadata':
        changes['bank'] = replace(case['bank'], items=(replace(case['bank'].items[0], difficulty=900.0), *case['bank'].items[1:]))
    elif change == 'geometry':
        changes['spec'] = replace(case['spec'], context=1)
    else:
        identity = deepcopy(case['expected_identity'])
        identity['core_source_sha256']['model.py'] = '0' * 64
        changes['expected_identity'] = identity
    with pytest.raises(ValueError, match='identity|SHA-256'):
        load(case, **changes)


@pytest.mark.parametrize('change', ['envelope', 'nan', 'float64', 'missing_parameter'])
def test_loader_requires_finite_raw_matching_state_dict(case, change):
    state = torch.load(case['path'], weights_only=True)
    if change == 'envelope':
        state = {'model_state_dict': state, 'optimizer': None}
    elif change == 'nan':
        state[next(iter(state))].flatten()[0] = float('nan')
    elif change == 'float64':
        state = {name: value.to(torch.float64) for name, value in state.items()}
    else:
        state.pop(next(iter(state)))
    torch.save(state, case['path'])
    with pytest.raises((ValueError, RuntimeError), match='raw state_dict|Missing key'):
        load(case, expected_sha256=hashlib.sha256(case['path'].read_bytes()).hexdigest())


def test_checkpoint_byte_budget_is_enforced(case):
    with pytest.raises(ValueError, match='budget'):
        load(case, max_checkpoint_bytes=1)


@pytest.mark.parametrize('field,value', [
    ('context', -1), ('window_policy', 'akt_anchored'), ('position_policy', 'absolute_global'),
    ('first_target_policy', 'automatic_mastery'), ('padding_side', 'middle'),
    ('batch_size', 0), ('device', 'cuda'), ('precision', 'float16'),
])
def test_unimplemented_or_invalid_conventions_are_rejected(case, field, value):
    with pytest.raises(ValueError, match='convention'):
        replace(case['spec'], **{field: value})


def test_context_counts_past_interactions_plus_one_query(case):
    with pytest.raises(ValueError, match='geometry'):
        inference_identity(case['config'], case['vocabulary'], case['bank'],
                           replace(case['spec'], context=4), weight_role='random_fixture')
    adapter = load(case)
    scores = adapter.predict_details(inputs())
    assert [s.history_used for s in scores] == [0, 1, 2, 2, 2]
    assert [s.global_rank for s in scores] == list(range(5))
    assert [s.has_history for s in scores] == [False, True, True, True, True]


@pytest.mark.parametrize('policy', ['query_only', 'unsupported'])
def test_zero_history_policy_is_explicit_and_never_a_mastery_decision(case, policy):
    spec = replace(case['spec'], first_target_policy=policy)
    adapter = load(case, spec=spec, expected_identity=inference_identity(
        case['config'], case['vocabulary'], case['bank'], spec, weight_role='random_fixture'))
    score = adapter.predict_details(inputs())[0]
    assert score.support_reason == ('cold_query_only' if policy == 'query_only' else 'cold_unsupported')
    assert score.has_history is False
    assert (score.probability is not None) == (policy == 'query_only')
    if policy == 'unsupported':
        with pytest.raises(ValueError, match='unsupported targets'):
            adapter.predict(inputs())


def test_current_and_future_responses_cannot_change_earlier_offline_scores(case):
    adapter = load(case)
    labels = (1, 0, 1, 0, 1)
    baseline = adapter.predict(inputs(labels=labels))
    for target in range(5):
        changed = labels[:target] + tuple(1 - value for value in labels[target:])
        np.testing.assert_allclose(adapter.predict(inputs(labels=changed))[:target + 1],
                                   baseline[:target + 1], rtol=0, atol=1e-7)


def test_future_items_do_not_change_past_predictions_and_context_has_positive_controls(case):
    adapter = load(case)
    baseline = adapter.predict(inputs())
    changed = adapter.predict(inputs(items=(0, 1, 2, 2, 2)))
    np.testing.assert_allclose(changed[:3], baseline[:3], rtol=0, atol=1e-7)
    assert abs(adapter.predict(inputs(labels=(0, 0, 1, 0, 1)))[1] - baseline[1]) > 1e-6
    # Trước sliding context không còn được đọc tại target cuối; position được re-anchor theo spec.
    np.testing.assert_allclose(adapter.predict(inputs(items=(2, 2, 2, 0, 1)))[-1], baseline[-1], rtol=0, atol=1e-7)


def test_offline_geometry_matches_independent_core_windows(case):
    adapter = load(case)
    source = inputs()
    scores = adapter.predict_details(source)
    with torch.inference_mode():
        for target, score in enumerate(scores):
            start = max(0, target - 2)
            prior = source.prior_responses[start:target + 1].copy()
            prior[0] = -1
            window = CausalSequenceInputs(source.item_ids[start:target + 1], source.timestamps[start:target + 1],
                prior, source.source_rows[start:target + 1], np.asarray([0, target - start + 1]), ('a',) * (target - start + 1))
            output = adapter._model(collate_sequences([window], num_items=3, max_length=4,
                                                      padding_side='right', device='cpu'))
            assert score.probability == pytest.approx(float(output.probabilities[0, -1]), abs=1e-7)


def test_oov_is_unsupported_and_resets_only_history_after_its_barrier(case):
    adapter = load(case)
    source = inputs(items=(0, -1, 2, 0, 1))
    scores = adapter.predict_details(source)
    assert scores[1].probability is None and scores[1].support_reason == 'oov_item'
    assert scores[2].history_available == 2 and scores[2].history_used == 0 and scores[2].context_reset
    assert scores[3].history_used == 1 and scores[4].history_used == 2
    changed = adapter.predict_details(inputs(items=(1, -1, 2, 0, 1), labels=(0, 1, 1, 0, 1)))
    np.testing.assert_allclose(probabilities(changed)[2:], probabilities(scores)[2:], rtol=0, atol=1e-7)
    with pytest.raises(ValueError, match='unsupported targets'):
        adapter.predict(source)


def test_candidate_queries_are_independent_do_not_commit_and_match_offline(case):
    adapter = load(case)
    prior = history()
    before = deepcopy(prior)
    queries = tuple(ItemQuery(name, 2, 3) for name in 'ACDB')
    batch = adapter.query_many(prior, queries, learner_id='a')
    single = tuple(adapter.query(prior, query, learner_id='a') for query in queries)
    np.testing.assert_allclose(probabilities(batch), probabilities(single), rtol=0, atol=1e-7, equal_nan=True)
    assert batch[2].support_reason == 'oov_item' and batch[2].probability is None
    assert prior == before
    np.testing.assert_allclose(batch[0].probability,
        adapter.predict(inputs(items=(0, 1, 0), labels=(1, 0, 1)))[-1], rtol=0, atol=1e-7)
    with pytest.raises(TypeError):
        adapter.query(prior, queries[0], learner_id='a', correct=1)
    with pytest.raises(ValueError, match='no current outcome'):
        adapter.query(prior, Observation(queries[0], 1), learner_id='a')


def test_stateless_learner_isolation_and_bound_history_rejects_other_learner(case):
    adapter = load(case)
    a, b = history(learner='a'), history(learner='b')
    query = ItemQuery('C', 2, 3)
    baseline = adapter.query(b, query, learner_id='b')
    changed_a = history(labels=(0, 1), learner='a')
    assert adapter.query(changed_a, query, learner_id='a').probability != baseline.probability
    assert adapter.query(b, query, learner_id='b') == baseline
    with pytest.raises(ValueError, match='learner binding'):
        adapter.query(a, query, learner_id='b')


@pytest.mark.parametrize('padding', ['left', 'right'])
def test_batch_size_permutation_and_peer_invariance(case, padding):
    many_spec = replace(case['spec'], padding_side=padding, batch_size=4)
    one_spec = replace(many_spec, batch_size=1)
    def configured(spec):
        return load(case, spec=spec, expected_identity=inference_identity(
            case['config'], case['vocabulary'], case['bank'], spec, weight_role='random_fixture'))
    many, one = configured(many_spec), configured(one_spec)
    source = inputs()
    np.testing.assert_allclose(many.predict(source), one.predict(source), rtol=0, atol=1e-6)
    prior = history()
    queries = tuple(ItemQuery(name, 2, 3) for name in 'ABC')
    result = many.query_many(prior, queries, learner_id='a')
    reordered = many.query_many(prior, queries[::-1], learner_id='a')
    np.testing.assert_allclose(probabilities(result), probabilities(reordered)[::-1], rtol=0, atol=1e-6)


@pytest.mark.parametrize('change', ['weight', 'training_mode', 'requires_grad', 'recipe'])
def test_runtime_mutation_rejected_including_data_bypass(case, change):
    adapter = load(case)
    if change == 'weight':
        next(adapter._model.parameters()).data.flatten()[0] += 1
    elif change == 'training_mode':
        adapter._model.train()
    elif change == 'requires_grad':
        next(adapter._model.parameters()).requires_grad_(True)
    else:
        adapter._spec = replace(case['spec'], first_target_policy='unsupported')
    with pytest.raises(ValueError, match='frozen'):
        adapter.predict(inputs())


@pytest.mark.parametrize('change', ['current_prior', 'duplicate_row', 'reverse_time', 'mixed_learner', 'duplicate_segment', 'bad_id'])
def test_invalid_input_cannot_silently_sort_resegment_or_cross_learners(case, change):
    adapter = load(case)
    sequence = inputs()
    if change == 'current_prior':
        sequence.prior_responses[0] = 1
    elif change == 'duplicate_row':
        sequence.source_rows[1] = 1
    elif change == 'reverse_time':
        sequence.timestamps[3] = 0
    elif change == 'mixed_learner':
        sequence = replace(sequence, user_ids=('a', 'a', 'b', 'b', 'b'))
    elif change == 'duplicate_segment':
        sequence.prior_responses[2] = -1
        sequence = replace(sequence, sequence_offsets=np.asarray([0, 2, 5]))
    else:
        sequence.item_ids[-1] = 3
    with pytest.raises(ValueError):
        adapter.predict_details(sequence)


def test_direct_queries_reject_cross_domain_duplicate_and_chronology(case):
    adapter = load(case)
    for query in [ItemQuery('elsewhere', 2, 3), ItemQuery('A', 2, 2), ItemQuery('A', 0, 3)]:
        with pytest.raises(ValueError):
            adapter.query(history(), query, learner_id='a')


def test_binding_copy_is_not_mutable_internal_identity_and_empty_input_is_valid(case):
    adapter = load(case)
    public = adapter.binding
    public['weight_role'] = 'fitted'
    assert adapter.binding['weight_role'] == 'random_fixture'
    empty = CausalSequenceInputs(*(np.asarray([], dtype=np.int64) for _ in range(4)), np.asarray([0]), ())
    assert adapter.predict(empty).size == 0
    assert adapter.query_many(SAKTHistory('a', ()), (), learner_id='a') == ()


@pytest.mark.parametrize('padding', ['left', 'right'])
def test_offline_multi_learner_batch_peer_and_order_are_isolated(case, padding):
    spec = replace(case['spec'], padding_side=padding, batch_size=8)
    adapter = load(case, spec=spec, expected_identity=inference_identity(
        case['config'], case['vocabulary'], case['bank'], spec, weight_role='random_fixture'))
    a = inputs(user='a')
    b = inputs(items=(2, 0, 1), labels=(0, 1, 0), user='b', source_start=11)
    def concatenate(left, right):
        fields = [np.concatenate((getattr(left, name), getattr(right, name)))
                  for name in ('item_ids', 'timestamps', 'prior_responses', 'source_rows')]
        n, m = len(left.item_ids), len(right.item_ids)
        return CausalSequenceInputs(*fields, np.asarray([0, n, n + m]), left.user_ids + right.user_ids)
    combined = adapter.predict(concatenate(a, b))
    np.testing.assert_allclose(combined, np.concatenate((adapter.predict(a), adapter.predict(b))), rtol=0, atol=1e-6)
    reverse = adapter.predict(concatenate(b, a))
    np.testing.assert_allclose(reverse, np.concatenate((combined[5:], combined[:5])), rtol=0, atol=1e-6)
    changed_a = inputs(labels=(0, 1, 0, 1, 0), user='a')
    np.testing.assert_allclose(adapter.predict(concatenate(changed_a, b))[5:], combined[5:], rtol=0, atol=1e-6)


@pytest.mark.parametrize('context', [0, 2])
def test_unsupported_cold_policy_applies_to_zero_context_and_oov_reset(case, context):
    spec = replace(case['spec'], context=context, first_target_policy='unsupported')
    adapter = load(case, spec=spec, expected_identity=inference_identity(
        case['config'], case['vocabulary'], case['bank'], spec, weight_role='random_fixture'))
    scores = adapter.predict_details(inputs(items=(0, -1, 2, 0, 1)))
    assert scores[0].support_reason == scores[2].support_reason == 'cold_unsupported'
    assert scores[0].probability is scores[2].probability is None
    if context == 0:
        assert all(score.probability is None for score in scores)
    else:
        assert scores[3].probability is not None


def test_clock_gap_is_chronology_metadata_not_implicit_forgetting(case):
    adapter = load(case)
    prior = history()
    near = adapter.query(prior, ItemQuery('C', 2, 3), learner_id='a')
    delayed = adapter.query(prior, ItemQuery('C', 2 + 14 * 86400, 3), learner_id='a')
    assert near == delayed
