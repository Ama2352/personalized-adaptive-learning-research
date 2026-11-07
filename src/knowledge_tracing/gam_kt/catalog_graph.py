"""Tái dựng graph từ catalog hiện có bằng đúng SCC rule nguồn Paper2."""

import argparse
import ast
import hashlib
import json
import re

import networkx as nx
import pandas as pd

from knowledge_tracing.evidence import record_evidence_run
from knowledge_tracing.paper2_reference import ROOT, PACKAGE

NOTEBOOK = PACKAGE / 'source/junyi_cycle_corrected_ablation_confirmation.ipynb'


def correct_with_historical_rule(nodes, edges):
    notebook = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    matches = []
    for index, cell in enumerate(notebook['cells']):
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        tree = ast.parse(source)
        names = {'sccs','component_by_node','cyclic_sccs','removed_cycle_edges','graph_dag'}
        selected = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in node.targets):
                selected.append(node)
            elif (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                  and isinstance(node.value.func, ast.Attribute)
                  and isinstance(node.value.func.value, ast.Name)
                  and node.value.func.value.id == 'graph_dag' and node.value.func.attr == 'remove_edges_from'):
                selected.append(node)
        if any(isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='removed_cycle_edges' for t in node.targets) for node in selected):
            matches.append((index, source, selected))
    if len(matches) != 1 or len(matches[0][2]) != 6:
        raise ValueError('historical SCC transform source changed')
    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from((a,b) for a,b in edges if a != b)
    index, source, selected = matches[0]
    scope = {'nx':nx, 'graph':graph}
    exec(compile(ast.Module(body=selected,type_ignores=[]),'<Historical Paper2 SCC rule>','exec'),scope)
    corrected = scope['graph_dag']
    if not nx.is_directed_acyclic_graph(corrected):
        raise ValueError('historical correction did not produce DAG')
    output = {'nodes':sorted(corrected.nodes),'raw_edges_without_self_loops':sorted(graph.edges),
              'corrected_edges':sorted(corrected.edges),'removed_edges':sorted(scope['removed_cycle_edges']),
              'cyclic_sccs':sorted(sorted(group) for group in scope['cyclic_sccs']),
              'corrected_is_DAG':True,'source_cell':index,
              'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
              'notebook_sha256':hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest()}
    output['corrected_edge_set_sha256'] = hashlib.sha256(json.dumps(output['corrected_edges'],sort_keys=True).encode()).hexdigest()
    return output


def run(run_id):
    catalog = ROOT/'dataset/junyi_Exercise_table.csv'
    table = pd.read_csv(catalog).fillna('')
    edges = {(parent.strip(),str(row['name'])) for row in table.to_dict('records')
             for parent in re.split(r'[;,|]+',str(row['prerequisites'])) if parent.strip()}
    sources = [catalog,NOTEBOOK,ROOT/'src/knowledge_tracing/gam_kt/catalog_graph.py']
    note = '''# Tái dựng SCC graph bằng nguồn Paper2

Dùng catalog hiện tại và chọn lọc đúng6AST statements của SCC-removal trong notebook Paper2. Không chạy notebook toàn bộ, không đọc learner logs hoặc outcomes. Graph.json chứa nodes/raw edges/removed edges/corrected DAG và hashes. Self-loops được loại trước theo preprocessing nguồn.

Đây là graph version mới tái dựng từ bytes hiện có. Counts khớp979→976 là bằng chứng consistency với lịch sử, chưa chứng minh identical historical edge bytes vì artifact cũ không đóng băng raw Junyi hashes. Không tự thay graph của experiment lịch sử hoặc benchmark đã frozen. Phải chốt graph version cho experiment tương lai.
'''
    with record_evidence_run(ROOT,run_id,metadata={'kind':'historical_graph_reconstruction','rq':['RQ2'],
            'uses_response_targets':False},sources=sources,note=note) as directory:
        result = correct_with_historical_rule(table.name.astype(str).tolist(),edges)
        (directory/'graph.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id',required=True)
    print(run(parser.parse_args().run_id))
