"""Chuẩn bị đối chứng topology TRAIN80, chưa đo exposure của cạnh mới."""

from collections import Counter
import hashlib
import json

from knowledge_tracing.graph_controls import graph_fingerprint, rewire_matched_graph
from knowledge_tracing.shared_kt import PrerequisiteGraph

SUPPORT_BINS = ['0', '1-9', '10-99', '100-999', '1000-9999', '10000+']

def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def support_bin(count):
    if type(count) is not int or count < 0:
        raise ValueError('TRAIN learner support must be a nonnegative integer')
    if count == 0:
        return '0'
    if count < 10:
        return '1-9'
    if count < 100:
        return '10-99'
    if count < 1000:
        return '100-999'
    if count < 10000:
        return '1000-9999'
    return '10000+'


def construct_control(*, graph, topics, areas, train_support, phase, recipe, seed):
    """Gọi thuật toán swap hiện có, trả pending thay vì đoán exposure mới.

    Hàm không đọc file, labels hoặc stream. Caller phải bind các input đã pin.
    Không tự retry seed hoặc giảm số swap khi điều kiện không khả thi.
    """
    if phase.get('scope') != 'select_train80' or phase.get('outer_fold') != 4:
        raise ValueError('Only current outer4 TRAIN80 phase is allowed')
    for name in ('phase_view_identity', 'encoding_identity', 'roles_sha256', 'cache_manifest_sha256'):
        value = phase.get(name)
        if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('Missing source/phase pin: ' + name)
    if recipe['kind'] != 'junyi_outer4_train80_degree_topic_area_support_control_v1':
        raise ValueError('Frozen recipe kind required')
    if recipe['support_bins'] != SUPPORT_BINS:
        raise ValueError('Frozen log10 support bins required')
    if seed not in recipe['seeds'] or type(seed) is not int:
        raise ValueError('Seed is not in the frozen recipe')
    if type(graph) is not PrerequisiteGraph or graph.edge_direction != 'prerequisite_to_dependent':
        raise ValueError('Typed prerequisite DAG required')
    nodes = set(graph.nodes)
    if set(topics) != nodes or set(areas) != nodes:
        raise ValueError('Complete catalog topic/area maps required')
    if set(train_support) - nodes:
        raise ValueError('Foreign support exercise')
    if any(type(value) is not str for value in [*topics.values(), *areas.values()]):
        raise ValueError('Static catalog labels must be strings')
    strata = {node: json.dumps([areas[node], support_bin(train_support.get(node, 0))]) for node in graph.nodes}
    original_payload = dict(nodes=graph.nodes, edges=graph.edges, topics=topics, areas=areas,
                            train_support=train_support, phase=phase, recipe=recipe)
    input_sha = identity(original_payload)
    try:
        result = rewire_matched_graph(graph, swaps=recipe['swaps'], chapters=topics,
                                     seed=seed, node_strata=strata)
    except ValueError as error:
        return dict(status='INCONCLUSIVE_CONSTRUCTION_UNAVAILABLE', seed=seed,
                    requested_swaps=recipe['swaps'], reason=str(error), input_sha256=input_sha,
                    recipe_sha256=identity(recipe), benchmark_eligible=False,
                    effective_exposure_status='NOT_MEASURED', retries=0)
    old, new = set(graph.edges), set(result.graph.edges)
    removed, added = sorted(old - new), sorted(new - old)
    if len(removed) != len(added) or len(removed) != 2 * recipe['swaps']:
        raise ValueError('Swap did not achieve the frozen changed-edge workload')
    for endpoint in (0, 1):
        if Counter(edge[endpoint] for edge in old) != Counter(edge[endpoint] for edge in new):
            raise ValueError('Degree drift')
    def joint_counts(edges):
        return Counter(((topics[p], strata[p]), (topics[c], strata[c])) for p, c in edges)
    if joint_counts(old) != joint_counts(new):
        raise ValueError('Joint topic/area/support stratum drift')
    if input_sha != identity(original_payload):
        raise ValueError('Input mutation during construction')
    return dict(status='CONSTRUCTED_PENDING_NEW_EDGE_EXPOSURE_AUDIT', seed=seed,
                nodes=result.graph.nodes, edges=result.graph.edges, removed_edges=removed, added_edges=added,
                original_graph_sha256=graph_fingerprint(graph), control_graph_sha256=graph_fingerprint(result.graph),
                input_sha256=input_sha, phase=phase, recipe_sha256=identity(recipe),
                applied_swaps=result.applied_changes, changed_entries=len(removed) + len(added),
                effective_exposure_status='NOT_MEASURED', benchmark_eligible=False,
                active_new_edge_counts=None, retries=0,
                scope_vi='Constrained sensitivity graph, chưa uniform DAG null hoặc prerequisite truth.')
