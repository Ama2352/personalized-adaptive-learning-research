"""Hợp đồng adapter nguồn và quyết định mastery gốc."""

from collections import Counter

import pytest

from knowledge_tracing.paper2_reference import load_reference
from knowledge_tracing.graph_controls import rewire_matched_graph
from knowledge_tracing.shared_kt import PrerequisiteGraph
from knowledge_tracing.diagnostics import DecisionTrace, compare_decision_traces


def test_reference_separates_environment_estimator_and_controller_graphs():
    source = load_reference(estimator_edges=[])
    env, model, controller = [source[name] for name in ('environment', 'estimator', 'controller')]
    assert len(model['nodes']) == 28
    assert sum(map(len, model['graph'].pred.values())) == 0
    assert sum(map(len, env['graph'].pred.values())) == 31
    assert sum(map(len, controller['graph'].pred.values())) == 31
    assert model['GAMKTPolicy'].ready_set.__globals__ is controller
    assert model['GAMKTPolicy']._graph_summary.__globals__ is model
    assert env['LatentStudentEnvironment'].interact.__globals__ is env
    policy = model['GAMKTPolicy'](True)
    assert len(policy.ready_set()) > 0
    cid, qid, difficulty = policy.select()
    timestamp = env['pd'].Timestamp('2026-01-01', tz='UTC')
    p = policy.predict(cid, qid, difficulty, timestamp)
    assert 0 < p < 1
    policy.update(cid, qid, difficulty, timestamp, 1, p)


def test_explicit_mastery_drives_crossings_instead_of_probability_threshold():
    left = DecisionTrace('event', 'learner', 1, .6, {'A': .6}, frozenset({'A'}), 'A', frozenset())
    right = DecisionTrace('event', 'learner', 1, .6, {'A': .6}, frozenset({'A'}), 'A', frozenset({'A'}))
    assert compare_decision_traces([left], [right], threshold=.5)['mastery_crossings'] == 1
    missing = DecisionTrace('event', 'learner', 1, .6, {'A': .6}, frozenset({'A'}), 'A')
    with pytest.raises(ValueError, match='semantics'):
        compare_decision_traces([left], [missing], threshold=.5)


def test_matched_rewire_preserves_degrees_chapter_counts_and_isolated_node():
    graph = PrerequisiteGraph.from_edges(['A', 'B', 'C', 'D', 'Z'], [('A', 'C'), ('B', 'D')])
    chapters = {'A': 'X', 'B': 'X', 'C': 'Y', 'D': 'Y', 'Z': 'Z'}
    result = rewire_matched_graph(graph, swaps=1, chapters=chapters)
    assert result.graph.nodes == graph.nodes
    for index in (0, 1):
        assert Counter(edge[index] for edge in graph.edges) == Counter(edge[index] for edge in result.graph.edges)
    assert result.graph.edges != graph.edges
    assert result == rewire_matched_graph(graph, swaps=1, chapters=chapters)
    with pytest.raises(ValueError, match='insufficient'):
        rewire_matched_graph(graph, swaps=2, chapters=chapters)
