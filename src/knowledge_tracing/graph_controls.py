"""Graph perturbation xác định, giữ nodes và báo chính xác số cạnh đổi."""

from dataclasses import dataclass
import hashlib
import json
import random
from collections import Counter
from itertools import combinations

from .shared_kt import PrerequisiteGraph


def _acyclic(nodes, edges):
    indegree = dict.fromkeys(nodes, 0)
    children = {node: [] for node in nodes}
    for parent, child in edges:
        indegree[child] += 1
        children[parent].append(child)
    ready = [node for node in nodes if indegree[node] == 0]
    visited = 0
    while ready:
        parent = ready.pop()
        visited += 1
        for child in children[parent]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    return visited == len(nodes)


def graph_fingerprint(graph: PrerequisiteGraph) -> str:
    payload = {'nodes': sorted(graph.nodes), 'edges': sorted(graph.edges),
               'direction': graph.edge_direction}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class PerturbedGraph:
    graph: PrerequisiteGraph
    operation: str
    seed: int
    requested_changes: int
    applied_changes: int
    original_sha256: str
    result_sha256: str


def perturb_graph(graph: PrerequisiteGraph, *, operation: str, count: int, seed: int = 42) -> PerturbedGraph:
    """Từ chối nếu không đủ thay đổi hợp lệ, không âm thầm giảm noise.

    Đây là robustness perturbation, chưa là null graph khớp degree/chapter/support.
    Mức noise được caller chuyển thành số cạnh và đăng ký trước.
    """
    if operation not in {'delete', 'add', 'reverse'} or type(count) is not int or count < 0:
        raise ValueError('invalid perturbation request')
    if type(seed) is not int:
        raise ValueError('invalid seed')
    checked = PrerequisiteGraph.from_edges(graph.nodes, graph.edges)
    if graph.edge_direction != checked.edge_direction or not _acyclic(checked.nodes, checked.edges):
        raise ValueError('perturbation requires a prerequisite DAG')
    edges = set(checked.edges)
    candidates = ([(a,b) for a in checked.nodes for b in checked.nodes if a != b and (a,b) not in edges]
                  if operation == 'add' else list(checked.edges))
    random.Random(seed).shuffle(candidates)
    applied = 0
    for parent, child in candidates:
        if applied == count:
            break
        proposed = set(edges)
        if operation == 'add':
            proposed.add((parent, child))
        else:
            proposed.remove((parent, child))
            if operation == 'reverse':
                proposed.add((child, parent))
        if _acyclic(checked.nodes, proposed):
            edges = proposed
            applied += 1
    if applied != count:
        raise ValueError(f'insufficient valid perturbations: requested={count}, available={applied}')
    result = PrerequisiteGraph.from_edges(checked.nodes, list(edges))
    return PerturbedGraph(result, operation, seed, count, applied,
                          graph_fingerprint(checked), graph_fingerprint(result))


def rewire_matched_graph(graph: PrerequisiteGraph, *, swaps: int, chapters: dict[str, str],
                         seed: int = 42, node_strata: dict[str, str] | None = None) -> PerturbedGraph:
    """Double-edge swap giữ in/out-degree và số cạnh mỗi chapter pair.

    Đây là constrained sensitivity control, không lấy mẫu đều mọi DAG.
    Mỗi cạnh gốc chỉ được dùng một lần, không undo để đạt số swap giả.
    node_strata tùy chọn giữ joint chapter/stratum pair counts, ví dụ support-bin
    được caller tính trên train-only data. Không tự suy bin từ dữ liệu khác.
    """
    if type(swaps) is not int or swaps < 0 or type(seed) is not int:
        raise ValueError('invalid matched rewiring request')
    checked = PrerequisiteGraph.from_edges(graph.nodes, graph.edges)
    if set(chapters) != set(checked.nodes) or not _acyclic(checked.nodes, checked.edges):
        raise ValueError('matched rewiring requires DAG and complete chapter mapping')
    strata = dict.fromkeys(checked.nodes, '') if node_strata is None else node_strata
    if set(strata) != set(checked.nodes) or any(not isinstance(value, str) for value in strata.values()):
        raise ValueError('matched rewiring requires complete string strata')
    labels = {node: (chapters[node], strata[node]) for node in checked.nodes}
    edges = set(checked.edges)
    candidates = list(combinations(checked.edges, 2))
    random.Random(seed).shuffle(candidates)
    applied = 0
    for (a, b), (c, d) in candidates:
        if applied == swaps:
            break
        if a == c or b == d or (a, b) not in edges or (c, d) not in edges:
            continue
        replacement = {(a, d), (c, b)}
        if a == d or c == b or replacement & edges or replacement & set(checked.edges):
            continue
        old_pairs = Counter([(labels[a], labels[b]), (labels[c], labels[d])])
        new_pairs = Counter([(labels[a], labels[d]), (labels[c], labels[b])])
        proposed = edges - {(a, b), (c, d)} | replacement
        if old_pairs == new_pairs and _acyclic(checked.nodes, proposed):
            edges = proposed
            applied += 1
    if applied != swaps:
        raise ValueError(f'insufficient matched swaps: requested={swaps}, available={applied}')
    result = PrerequisiteGraph.from_edges(checked.nodes, sorted(edges))
    return PerturbedGraph(result, 'degree_chapter_rewire', seed, swaps, applied,
                          graph_fingerprint(checked), graph_fingerprint(result))
