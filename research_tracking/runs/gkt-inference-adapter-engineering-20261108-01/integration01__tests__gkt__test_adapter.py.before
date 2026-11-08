"""Portable unit contracts: mocked loader + explicitly UNVERIFIED random container.

Không artifact dependency/training. Actual trained checkpoint integration nằm ở
artifact controller riêng, không giả mock thành trained hoặc fitted evidence.
"""
from dataclasses import replace
import inspect

import numpy as np
import pytest
import torch

from knowledge_tracing.gkt import GKTBinding, GKTKernelConfig
from knowledge_tracing.gkt.recurrent import GKTStaticRecurrentCandidate, RECIPE_ID, GRU_VARIANT
from knowledge_tracing.gkt import adapter as ga
from knowledge_tracing.gkt import training_checkpoint as cp
from knowledge_tracing.shared_kt import CausalSequenceInputs, StableVocabulary
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, OnlineScore, SimulatorBank, SimulatorItem


@pytest.fixture(autouse=True)
def bounded_cpu_no_optimizer(monkeypatch):
    threads = torch.get_num_threads(); torch.set_num_threads(2)
    monkeypatch.setattr(torch.optim.Adam, 'step', lambda *a, **k: pytest.fail('no optimizer allowed'))
    try:
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(42)
            yield
    finally:
        torch.set_num_threads(threads)


@pytest.fixture
def case(monkeypatch):
    config = GKTKernelConfig(3, 2, 2, 2, 'static', 'concept', True, True)
    binding = GKTBinding('unverified-unit-only-GKT', 'a' * 64, ('A', 'B', 'C'), 'concept')
    graph = torch.tensor([[0., .4, 0.], [.2, 0., .7], [0., .3, 0.]], dtype=torch.float64, device='cpu')
    model = GKTStaticRecurrentCandidate(config, binding, graph, recipe_id=RECIPE_ID, mlp_hidden_dim=3,
        normalization='none', dropout=0, initial_state_policy='zeros', gru_variant=GRU_VARIANT)
    loaded = cp.GKTLoadedEngineeringWeights(model,
        {'weight_role': 'unverified_fixture', 'purpose': 'MOCK_UNIT_CONTAINER_NOT_TRAINED_RECEIPT'}, 'f' * 64)
    calls = []
    def mock_loader(*args, **kwargs):
        calls.append('MOCK_ONLY_NOT_ACTUAL_CHECKPOINT_LOAD'); return loaded
    monkeypatch.setattr(cp, 'load_engineering_weights', mock_loader)
    unverified = cp.load_engineering_weights(None)
    bank = SimulatorBank(binding.domain, tuple(SimulatorItem(item, node, 1.) for item, node in
        [('a', 'A'), ('a2', 'A'), ('b', 'B'), ('c', 'C'), ('u', 'C'), ('o', 'B')]))
    vocabulary = StableVocabulary(('a', 'b', 'c', 'a2', 'u'))
    mapping = {'a': 'A', 'a2': 'A', 'b': 'B', 'c': 'C'}
    spec = ga.GKTInferenceSpec('full_prefix', 'query_only', 'unsupported_history', 12, 'cpu', 'float64')
    identity = ga._binding_identity(unverified, bank, vocabulary, mapping, spec)
    adapter = ga.FrozenGKTAdapter._from_loaded(unverified, bank, vocabulary, mapping, spec,
                                             expected_inference_binding=identity)
    return dict(adapter=adapter, loaded=loaded, bank=bank, vocabulary=vocabulary, mapping=mapping,
                spec=spec, identity=identity, loader_calls=calls)


def inputs(case, names=('a', 'b', 'c', 'a2'), labels=(0, 1, 1, 0), *, user='one', start_row=1):
    lookup = {x: i for i, x in enumerate(case['vocabulary'].values)}; n = len(names)
    return CausalSequenceInputs(np.asarray([lookup.get(x, -1) for x in names], dtype=np.int64),
        np.arange(n, dtype=np.int64), np.asarray([-1, *labels[:-1]], dtype=np.int64) if n else np.asarray([], dtype=np.int64),
        np.arange(start_row, start_row + n, dtype=np.int64), np.asarray([0, n] if n else [0], dtype=np.int64), (user,) * n)


def test_offline_queries_and_manual_predict_before_observe_match(case):
    adapter = case['adapter']; source = inputs(case); scores = adapter.predict_details(source)
    observations = tuple(Observation(ItemQuery(item, i, i + 1), answer)
                         for i, (item, answer) in enumerate(zip(('a', 'b', 'c', 'a2'), (0, 1, 1, 0))))
    model = case['loaded'].model; kwargs = dict(binding=model.binding, graph_sha256=model.graph_sha256)
    with torch.inference_mode(), torch.device('cpu'):
        state = model.initial_state(1, **kwargs)
        for i, observation in enumerate(observations):
            queried = adapter.query(ga.GKTHistory('one', observations[:i]), observation.query, learner_id='one')
            node = model.binding.node_ids.index(case['mapping'][observation.query.item_id])
            expected = float(model.predict(state, torch.tensor([node], device='cpu'), **kwargs).probabilities[0])
            assert scores[i].probability == queried.probability == expected
            state = model.observe(state, torch.tensor([node], device='cpu'),
                torch.tensor([observation.correct], device='cpu'), torch.tensor([True], device='cpu'), **kwargs)
    assert [x.global_rank for x in scores] == [0, 1, 2, 3]
    assert [x.history_used for x in scores] == [0, 1, 2, 3]
    assert {x.weight_role for x in scores} == {'unverified_fixture'}
    assert not any(x.research_fitted for x in scores)
    assert case['loader_calls'] == ['MOCK_ONLY_NOT_ACTUAL_CHECKPOINT_LOAD']


def test_full_target_population_includes_oov_unmapped_and_history_failure(case):
    source = inputs(case, ('a', 'b', 'u', 'c', 'o', 'a'), (0, 1, 0, 1, 0, 1))
    scores = case['adapter'].predict_details(source)
    assert [x.support_reason for x in scores] == ['cold_query_only', 'known_history', 'unmapped_item',
                                                'unsupported_history', 'oov_item', 'unsupported_history']
    assert [x.global_rank for x in scores] == list(range(6))
    assert [x.history_available for x in scores] == list(range(6))
    assert [x.history_used for x in scores] == [0, 1, 0, 0, 0, 0]
    assert not any(x.context_reset for x in scores)
    summary = ga.population_summary(scores, expected_source_rows=tuple(source.source_rows.tolist()))
    assert summary['expected_targets'] == 6 and summary['scored_targets'] == 2
    assert summary['unsupported_targets'] == 4 and summary['research_fitted_targets'] == 0
    with pytest.raises(ValueError): case['adapter'].predict(source)
    with pytest.raises(ValueError): ga.population_summary(scores[:-1], expected_source_rows=tuple(source.source_rows.tolist()))


def test_explicit_cold_unsupported_still_observes_real_history(case):
    spec = replace(case['spec'], first_target_policy='unsupported')
    identity = ga._binding_identity(case['loaded'], case['bank'], case['vocabulary'], case['mapping'], spec)
    adapter = ga.FrozenGKTAdapter._from_loaded(case['loaded'], case['bank'], case['vocabulary'], case['mapping'], spec,
                                             expected_inference_binding=identity)
    scores = adapter.predict_details(inputs(case))
    assert scores[0].probability is None and scores[0].support_reason == 'cold_unsupported'
    assert scores[1].probability is not None and scores[1].history_used == 1


def test_query_probes_order_no_fake_practice_and_learner_binding(case):
    adapter = case['adapter']; history = ga.GKTHistory('one', (Observation(ItemQuery('a', 0, 1), 0),))
    queries = (ItemQuery('b', 1, 2), ItemQuery('a2', 1, 2))
    before = history.observations; model_sha = ga.tr.model_digest(case['loaded'].model)
    first = adapter.query_many(history, queries, learner_id='one')
    reverse = adapter.query_many(history, queries[::-1], learner_id='one')
    assert tuple(x.probability for x in first) == tuple(x.probability for x in reversed(reverse))
    assert history.observations == before and all(x.global_rank == 1 for x in first)
    assert ga.tr.model_digest(case['loaded'].model) == model_sha
    aliases = adapter.query_many(history, (ItemQuery('a', 1, 2), ItemQuery('a2', 1, 2)), learner_id='one')
    assert aliases[0].probability == aliases[1].probability  # Declared node-only readout, no invented item difficulty.
    with pytest.raises(ValueError): adapter.query(history, queries[0], learner_id='other')
    with pytest.raises(ValueError): adapter.query(history, Observation(queries[0], 1), learner_id='one')
    assert 'correct' not in inspect.signature(adapter.query).parameters


def test_current_future_labels_and_foreign_learners_cannot_change_current_score(case):
    adapter = case['adapter']; baseline = adapter.predict_details(inputs(case))
    changed = adapter.predict_details(inputs(case, labels=(0, 1, 0, 1)))
    assert [x.probability for x in baseline[:3]] == [x.probability for x in changed[:3]]
    a = inputs(case); b = inputs(case, labels=(1, 0, 0, 1), user='two', start_row=10)
    joined = CausalSequenceInputs(np.concatenate([a.item_ids, b.item_ids]), np.concatenate([a.timestamps, b.timestamps]),
        np.concatenate([a.prior_responses, b.prior_responses]), np.concatenate([a.source_rows, b.source_rows]),
        np.asarray([0, 4, 8]), a.user_ids + b.user_ids)
    scores = adapter.predict_details(joined)
    assert [x.probability for x in scores[:4]] == [x.probability for x in baseline]
    assert [x.global_rank for x in scores] == [0, 1, 2, 3, 0, 1, 2, 3]


def test_cpu_default_meta_rng_and_inputs_preserved(case):
    adapter = case['adapter']; source = inputs(case); before = [x.copy() for x in
        (source.item_ids, source.timestamps, source.prior_responses, source.source_rows, source.sequence_offsets)]
    rng = torch.random.get_rng_state().clone(); old = torch.get_default_device()
    try:
        torch.set_default_device('meta'); adapter.predict_details(source)
    finally:
        torch.set_default_device(old)
    assert torch.equal(rng, torch.random.get_rng_state())
    assert all(np.array_equal(a, b) for a, b in zip(before,
        (source.item_ids, source.timestamps, source.prior_responses, source.source_rows, source.sequence_offsets)))
    metadata = adapter.binding; metadata['item_to_node'].clear(); adapter.predict_details(source)


def test_no_fitted_online_promotion_or_fake_production_load(case, monkeypatch):
    adapter = case['adapter']
    with pytest.raises(TypeError): ga.FrozenGKTAdapter()
    with pytest.raises(NotImplementedError): adapter.fit(None, None)
    with pytest.raises(NotImplementedError, match='fitted'): adapter.as_online_backend()
    with pytest.raises(ValueError): OnlineScore(.5, 'unverified_fixture', 0, 0, False, 0)
    # Actual production validator must reject this explicitly unverified mock receipt.
    with pytest.raises(ValueError): ga.load_frozen_engineering_gkt(None,
        expected_manifest_sha256='f' * 64, expected_checkpoint_identity=case['loaded'].identity,
        bank=case['bank'], item_vocabulary=case['vocabulary'], item_to_node=case['mapping'],
        spec=case['spec'], expected_inference_binding=case['identity'], max_checkpoint_bytes=1_000_000)
    # Separately mock prevalidation to isolate the final returned-container promotion guard.
    monkeypatch.setattr(ga, 'inference_identity', lambda *a, **k: case['identity'])
    with pytest.raises(ValueError, match='no fixture promotion'): ga.load_frozen_engineering_gkt(None,
        expected_manifest_sha256='f' * 64, expected_checkpoint_identity={'weight_role': ga.tr.WEIGHT_ROLE},
        bank=case['bank'], item_vocabulary=case['vocabulary'], item_to_node=case['mapping'],
        spec=case['spec'], expected_inference_binding=case['identity'], max_checkpoint_bytes=1_000_000)


@pytest.mark.parametrize('case_name', ['domain', 'multi_tag', 'foreign_node', 'concept_disagree', 'foreign_item', 'precision'])
def test_mapping_domain_and_geometry_fail_closed(case, case_name):
    bank, mapping, spec = case['bank'], dict(case['mapping']), case['spec']
    if case_name == 'domain': bank = SimulatorBank('Grade10', bank.items)
    elif case_name == 'multi_tag': mapping['a'] = ['A', 'B']
    elif case_name == 'foreign_node': mapping['a'] = 'Z'
    elif case_name == 'concept_disagree': mapping['a'] = 'B'
    elif case_name == 'foreign_item': mapping['outside'] = 'A'
    elif case_name == 'precision': spec = replace(spec, precision='float32')
    with pytest.raises(ValueError): ga._binding_identity(case['loaded'], bank, case['vocabulary'], mapping, spec)


@pytest.mark.parametrize('case_name', ['source', 'weights', 'mode', 'gradient', 'mapping'])
def test_mutation_detected_before_inference(case, case_name, monkeypatch):
    adapter = case['adapter']; model = case['loaded'].model
    if case_name == 'source': monkeypatch.setattr(ga, 'source_identity', lambda: {})
    elif case_name == 'weights':
        with torch.no_grad(): model.node_bias.add_(.1)
    elif case_name == 'mode': model.train()
    elif case_name == 'gradient': model.node_bias.requires_grad_(True)
    elif case_name == 'mapping': adapter._mapping['a'] = 'B'
    monkeypatch.setattr(model, 'predict', lambda *a, **k: pytest.fail('guard before model prediction'))
    with pytest.raises(ValueError): adapter.predict_details(inputs(case))


@pytest.mark.parametrize('case_name', ['duplicate_rows', 'chronology', 'prior', 'offsets', 'user', 'negative_id', 'concept_sidechannel'])
def test_malformed_sequence_not_silently_dropped(case, case_name):
    source = inputs(case)
    if case_name == 'duplicate_rows': source.source_rows[1] = source.source_rows[0]
    elif case_name == 'chronology': source.timestamps[1] = -1
    elif case_name == 'prior': source.prior_responses[1] = -1
    elif case_name == 'offsets': source.sequence_offsets[1] = 3
    elif case_name == 'user': source = replace(source, user_ids=('one', 'other', 'one', 'one'))
    elif case_name == 'negative_id': source.item_ids[0] = -2
    elif case_name == 'concept_sidechannel': source = replace(source, concept_ids=np.asarray([0, 1, 2, 0]))
    with pytest.raises(ValueError): case['adapter'].predict_details(source)


def test_empty_population_and_bank_known_oov_query(case):
    empty = case['adapter'].predict_details(inputs(case, (), ()))
    assert empty == () and ga.population_summary(empty, expected_source_rows=())['expected_targets'] == 0
    history = ga.GKTHistory('one', ())
    assert case['adapter'].query(history, ItemQuery('o', 0, 1), learner_id='one').support_reason == 'oov_item'
    with pytest.raises(ValueError): case['adapter'].query(history, ItemQuery('outside', 0, 1), learner_id='one')


@pytest.mark.parametrize('changes', [{'history_policy': 'sliding'}, {'oov_policy': 'skip'},
    {'first_target_policy': 'implicit'}, {'max_events': 13}, {'max_events': True}, {'device': 'cuda'}])
def test_explicit_inference_spec_required(changes):
    settings = dict(history_policy='full_prefix', first_target_policy='query_only', oov_policy='unsupported_history',
                    max_events=12, device='cpu', precision='float64')
    settings.update(changes)
    with pytest.raises(ValueError): ga.GKTInferenceSpec(**settings)
