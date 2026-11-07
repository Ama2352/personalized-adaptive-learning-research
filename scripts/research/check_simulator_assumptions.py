"""Kiểm đại số retention bằng method nguồn Paper2 và fixture nhỏ."""

import ast
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / ('paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/'
                   'source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb')


def check_retention_source():
    notebook = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    method = None
    rate = None
    for index, cell in enumerate(notebook['cells']):
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TRUE_FORGET_RATE'
                                                    for t in node.targets):
                rate = ast.literal_eval(node.value)
            if isinstance(node, ast.ClassDef) and node.name == 'LatentStudentEnvironment':
                method = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == 'theta_at')
                method_source = ast.get_source_segment(source, method)
                cell_index = index
    if method is None or rate is None:
        raise ValueError('required historical method or constant missing')
    namespace = {'pd': pd, 'math': math, 'TRUE_FORGET_RATE': rate}
    # Chỉ compile method đã kiểm tra, không execute notebook hoặc chạy experiment.
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(NOTEBOOK), 'exec'), namespace)
    theta_at = namespace['theta_at']
    timestamp = pd.Timestamp('2026-01-20', tz='UTC')
    environment = SimpleNamespace(base={'A': 1000., 'B': 1100.}, theta={'A': 1200., 'B': 1150.},
                                  last_seen={'A': timestamp-pd.Timedelta(days=2),
                                             'B': timestamp-pd.Timedelta(days=7)})
    final = sum(theta_at(environment, c, timestamp)-environment.base[c] for c in environment.base)
    retained = sum(theta_at(environment, c, timestamp+pd.Timedelta(days=14))-environment.base[c]
                   for c in environment.base)
    factor = math.exp(-14*rate)
    error = abs(retained-factor*final)
    if error > 1e-10:
        raise AssertionError('historical retention violates expected scaling')
    return {'status': 'passed_source_fixture', 'notebook': str(NOTEBOOK.relative_to(ROOT)),
            'notebook_sha256': hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
            'cell_index': cell_index, 'method_sha256': hashlib.sha256(method_source.encode()).hexdigest(),
            'true_forget_rate': rate, 'retention_days': 14, 'scaling_factor': factor,
            'absolute_error': error,
            'scope': 'No practice after T, homogeneous decay, nonnegative gain fixture. '
                     'Final state still depends on earlier practice order. No empirical graph-benefit claim.'}


def check_paper1_reentry_source():
    """Phản ví dụ dùng selector nguồn đã tìm, không tái lập bảng trong PDF."""
    path = ROOT / 'paper1/AdaptiveEngineSimulation_Enhanced.ipynb'
    notebook = json.loads(path.read_text(encoding='utf-8'))
    matches = []
    for index, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            for node in ast.parse(source).body:
                if isinstance(node, ast.FunctionDef) and node.name == 'select_adaptive_question':
                    matches.append((index, node, ast.get_source_segment(source, node)))
    if len(matches) != 1:
        raise ValueError('ambiguous Paper1 selector source')
    index, node, source = matches[0]
    namespace = {'pd': pd}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<Paper1 selector fixture>', 'exec'), namespace)
    nodes = ['A1', 'B1', 'A2']
    parents = {'A1': [], 'B1': ['A1'], 'A2': ['B1']}
    graph = SimpleNamespace(nodes=lambda: nodes, predecessors=lambda cid: parents[cid])
    profiles = pd.DataFrame([{f'elo_{cid}': 1200.0 for cid in nodes}], index=['fixture'])
    questions = pd.DataFrame([{'concept_id': cid, 'question_id': cid, 'elo_difficulty': 1200.0} for cid in nodes])
    chapters = {'A1': 'A', 'A2': 'A', 'B1': 'B'}
    routes = {}
    for strategy in ('lowest_elo', 'cross_chapter_unlock'):
        profiles.loc['fixture'] = 1200.0
        route = []
        previous = set()
        for _ in nodes:
            _, info = namespace['select_adaptive_question'](
                'fixture', profiles, questions, graph, chapters, selection_strategy=strategy,
                prev_ready_nodes=previous, cross_edges={('A1', 'B1'), ('B1', 'A2')})
            cid = info['target_concept']
            route.append(cid)
            profiles.loc['fixture', f'elo_{cid}'] = 1400.0
            previous = set(info['ready_nodes'])
        assert route == ['A1', 'B1', 'A2']
        routes[strategy] = {'concepts': route, 'chapters': [chapters[cid] for cid in route], 'chapter_reentries': 1}
    return {'status': 'passed_source_counterexample', 'notebook': str(path.relative_to(ROOT)),
            'notebook_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'cell': index,
            'selector_sha256': hashlib.sha256(source.encode()).hexdigest(), 'routes': routes,
            'scope': 'Actual available selector on synthetic DAG, externally scripted mastery transitions. '
                     'No guarantee of zero reentry in this revision. PDF/source equivalence remains unresolved.'}


if __name__ == '__main__':
    print(json.dumps({'retention': check_retention_source(), 'paper1': check_paper1_reentry_source()},
                     ensure_ascii=False, indent=2))
