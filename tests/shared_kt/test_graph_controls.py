import random

import pytest

from knowledge_tracing.graph_controls import graph_fingerprint, perturb_graph
from knowledge_tracing.shared_kt import PrerequisiteGraph


def graph():
    return PrerequisiteGraph.from_edges(['A','B','C','isolated'], [('A','B'),('B','C')])


@pytest.mark.parametrize('operation', ['delete', 'add', 'reverse'])
def test_changes_are_deterministic_and_preserve_nodes_and_global_rng(operation):
    original = graph()
    before = random.getstate()
    a = perturb_graph(original, operation=operation, count=1)
    b = perturb_graph(original, operation=operation, count=1)
    assert a == b
    assert a.applied_changes == a.requested_changes == 1
    assert a.graph.nodes == original.nodes
    assert a.original_sha256 != a.result_sha256
    assert original == graph()
    assert random.getstate() == before


def test_empty_graph_addition_cannot_silently_introduce_cycle():
    empty = PrerequisiteGraph.from_edges(['A','B'], [])
    with pytest.raises(ValueError, match='insufficient'):
        perturb_graph(empty, operation='add', count=2)


def test_cycle_input_and_insufficient_delete_are_rejected():
    cyclic = PrerequisiteGraph.from_edges(['A','B'], [('A','B'),('B','A')])
    with pytest.raises(ValueError, match='DAG'):
        perturb_graph(cyclic, operation='delete', count=1)
    with pytest.raises(ValueError, match='insufficient'):
        perturb_graph(graph(), operation='delete', count=3)


def test_zero_noise_is_identity_including_isolated_nodes():
    original = graph()
    result = perturb_graph(original, operation='reverse', count=0)
    assert result.graph == original
    assert result.original_sha256 == result.result_sha256 == graph_fingerprint(original)


@pytest.mark.parametrize('operation,count', [('wrong',1), ('add',True), ('delete',-1)])
def test_invalid_noise_requests_are_rejected(operation,count):
    with pytest.raises(ValueError):
        perturb_graph(graph(), operation=operation, count=count)
