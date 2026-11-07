"""Graph-context information boundaries; không đo hiệu quả CG-AKT."""

from dataclasses import replace

import pytest

from knowledge_tracing.graph_context import EdgeConfidence, audit_graph_context
from knowledge_tracing.shared_kt import PrerequisiteGraph
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem


def fixture():
    bank = SimulatorBank('context-fixture', tuple(SimulatorItem(i, c, 0) for i, c in
                                                [('a', 'A'), ('b', 'B'), ('oov', 'A')]))
    graph = PrerequisiteGraph.from_edges(['A', 'B'], [('A', 'B')])
    confidence = EdgeConfidence('fixed_uniform', (('A', 'B', 1),), '1' * 64)
    history = tuple(Observation(ItemQuery('a', rank, rank + 1), int(rank > 1)) for rank in range(8))
    return dict(bank=bank, graph=graph, confidence=confidence, history=history,
                query=ItemQuery('b', 8, 9), trained_items=('a', 'b'), context=3, target_block=2)


def test_effective_window_excludes_old_prefix_but_full_history_detects_it():
    kwargs = fixture()
    result = audit_graph_context(**kwargs)
    assert result['effective_start'] == 5
    assert result['observed_rows'] == [6, 7, 8]
    assert result['weighted_observed_correctness'] == 1
    changed = dict(kwargs, history=tuple(replace(o, correct=1-o.correct) if i < 5 else o
                                        for i, o in enumerate(kwargs['history'])))
    assert result == audit_graph_context(**changed)
    full = dict(scope='full_history', purpose='history_sensitivity')
    original = audit_graph_context(**kwargs, **full)
    perturbed = audit_graph_context(**changed, **full)
    assert original['weighted_observed_correctness'] != perturbed['weighted_observed_correctness']
    assert not original['information_matched']


def test_oov_barrier_and_global_block_not_last_h_slice():
    kwargs = fixture()
    kwargs['history'] = kwargs['history'][:7]
    kwargs['query'] = ItemQuery('b', 7, 8)
    result = audit_graph_context(**kwargs)
    assert result['effective_start'] == 3  # block6 - H3; four prior events, not last H3
    assert result['observed_rows'] == [4, 5, 6, 7]
    observations = list(kwargs['history'])
    observations[5] = Observation(ItemQuery('oov', 5, 6), 1)
    result = audit_graph_context(**dict(kwargs, history=tuple(observations)))
    assert result['effective_start'] == 6 and result['context_reset']
    assert result['observed_rows'] == [7]


@pytest.mark.parametrize('rank,start', [(0, 0), (99, 0), (100, 0), (199, 0), (200, 100), (204, 100)])
def test_default_global_anchors(rank, start):
    kwargs = fixture()
    kwargs.update(history=tuple(Observation(ItemQuery('a', i, i+1), i % 2) for i in range(rank)),
                  query=ItemQuery('b', rank, rank+1), context=100, target_block=100)
    result = audit_graph_context(**kwargs)
    assert result['effective_start'] == start
    assert len(result['observed_rows']) == rank - start
    assert rank+1 not in result['observed_rows']


@pytest.mark.parametrize('condition', ['disabled', 'empty', 'zero', 'unseen_target', 'unobserved_parent'])
def test_no_signal_conditions_are_explicit(condition):
    kwargs = fixture()
    if condition == 'disabled':
        kwargs['enabled'] = False
    elif condition == 'empty':
        kwargs['graph'] = PrerequisiteGraph.from_edges(['A', 'B'], [])
        kwargs['confidence'] = EdgeConfidence('fixed_uniform', (), '1' * 64)
    elif condition == 'zero':
        kwargs['confidence'] = EdgeConfidence('structural_score', (('A', 'B', 0),), '1' * 64)
    elif condition == 'unseen_target':
        kwargs['query'] = ItemQuery('oov', 8, 9)
    else:
        kwargs['history'] = tuple(replace(o, query=replace(o.query, item_id='b')) for o in kwargs['history'])
    result = audit_graph_context(**kwargs)
    assert result['weighted_observed_correctness'] is None
    assert result['observed_confidence_mass'] == 0
    if condition == 'unseen_target':
        assert not result['target_fitted'] and not result['parents'] and not result['observed_rows']


def test_oracle_requires_reference_and_estimation_requires_train():
    kwargs = fixture()
    kwargs['confidence'] = EdgeConfidence('oracle_label', (('A', 'B', 1),), '2' * 64)
    with pytest.raises(ValueError, match='reference mode'):
        audit_graph_context(**kwargs)
    assert audit_graph_context(**kwargs, purpose='oracle_reference')['purpose'] == 'oracle_reference'
    with pytest.raises(ValueError, match='train-only'):
        EdgeConfidence('estimated_probability', (('A', 'B', .8),), '2' * 64, 'calibration')
    estimated = EdgeConfidence('estimated_probability', (('A', 'B', .8),), '2' * 64, 'train')
    assert estimated.kind == 'estimated_probability'


@pytest.mark.parametrize('value', [-.1, 1.1, float('nan'), float('inf'), True])
def test_invalid_confidence_rejected(value):
    with pytest.raises(ValueError):
        EdgeConfidence('structural_score', (('A', 'B', value),), '1' * 64)


@pytest.mark.parametrize('case', ['scope', 'current_outcome', 'future', 'duplicate_row', 'alien_item',
                                 'graph_domain', 'direction', 'edge_coverage', 'vocabulary'])
def test_information_and_domain_guards(case):
    kwargs = fixture()
    if case == 'scope':
        kwargs['scope'] = 'full_history'
    elif case == 'current_outcome':
        kwargs['history'] += (Observation(kwargs['query'], 1),)
    elif case == 'future':
        kwargs['history'] += (Observation(ItemQuery('a', 9, 10), 0),)
    elif case == 'duplicate_row':
        kwargs['query'] = ItemQuery('b', 8, 1)
    elif case == 'alien_item':
        kwargs['query'] = ItemQuery('alien', 8, 9)
    elif case == 'graph_domain':
        kwargs['graph'] = PrerequisiteGraph.from_edges(['alien'], [])
    elif case == 'direction':
        kwargs['graph'] = replace(kwargs['graph'], edge_direction='reverse')
    elif case == 'edge_coverage':
        kwargs['confidence'] = EdgeConfidence('fixed_uniform', (), '1' * 64)
    elif case == 'vocabulary':
        kwargs['trained_items'] = ('a', 'alien')
    with pytest.raises(ValueError):
        audit_graph_context(**kwargs)


def test_parent_is_concept_not_exercise_id_and_confidences_do_not_create_support():
    kwargs = fixture()
    kwargs['trained_items'] = ('a', 'b', 'oov')
    kwargs['history'] = (Observation(ItemQuery('oov', 0, 1), 0), Observation(ItemQuery('a', 1, 2), 1))
    kwargs['query'] = ItemQuery('b', 2, 3)
    result = audit_graph_context(**kwargs)
    assert result['parents'][0]['support'] == 2
    assert result['weighted_observed_correctness'] == .5


def test_confidence_weighting_normalizes_observed_parents_not_interactions():
    bank = SimulatorBank('weighted-fixture', tuple(SimulatorItem(i, i.upper(), 0) for i in 'abc'))
    graph = PrerequisiteGraph.from_edges(['A', 'B', 'C'], [('A', 'C'), ('B', 'C')])
    confidence = EdgeConfidence('structural_score', (('A', 'C', .25), ('B', 'C', .75)), '1' * 64)
    observations = tuple(Observation(ItemQuery(item, i, i+1), int(item == 'a'))
                         for i, item in enumerate('aaab'))
    kwargs = dict(bank=bank, graph=graph, confidence=confidence, history=observations,
                  query=ItemQuery('c', 4, 5), trained_items=tuple('abc'), context=100, target_block=100)
    result = audit_graph_context(**kwargs)
    assert result['weighted_observed_correctness'] == .25
    assert result['observed_confidence_mass'] == 1
    result = audit_graph_context(**dict(kwargs, history=observations[:3]))
    assert result['weighted_observed_correctness'] == 1
    assert result['observed_confidence_mass'] == .25


@pytest.mark.parametrize('kind,values', [
    ('fixed_uniform', (('A', 'B', .5),)),
    ('oracle_label', (('A', 'B', .5),)),
    ('structural_score', (('A', 'B', .5), ('A', 'B', .7)))])
def test_confidence_kind_semantics_and_duplicates(kind, values):
    with pytest.raises(ValueError):
        EdgeConfidence(kind, values, '1' * 64)
