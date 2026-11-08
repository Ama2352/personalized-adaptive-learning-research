"""Nạp chọn lọc định nghĩa Paper2, giữ riêng graph môi trường/model/controller."""

import ast
from collections import Counter, deque
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
NOTEBOOK = PACKAGE / 'source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb'
DEFINITIONS = ('ConceptDAG', 'question_level', 'item_feature', 'elo_probability',
               'persona_base_abilities', 'LatentStudentEnvironment', 'dynamic_k',
               'choose_question', 'CoverageAwareSelectorMixin', 'sigmoid', 'clip_norm',
               'AdaptiveLMSPolicy', 'MemoryState', 'GAMKTPolicy')
CONSTANTS = ('GLOBAL_SEED', 'PERSONAS', 'MASTERY_ELO', 'PREREQUISITE_READY_ELO',
             'MODEL_INITIAL_ELO', 'TRUE_GAIN_SCALE', 'TRUE_FORGET_RATE',
             'MAX_CONSECUTIVE_CONCEPT', 'MIN_PREREQUISITE_EXPOSURES')


def load_reference(*, estimator_edges=None, controller_edges=None):
    """Chỉ thực thi definitions allowlist, không chạy notebook top-level.

    Các namespace độc lập để đổi graph estimator không thay response dynamics
    hoặc selector. Không biến đổi phương trình nguồn. Dữ liệu là simulator inputs
    được cung cấp trong artifact, không đọc Junyi/Holdout.
    """
    notebook = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    definitions, constants, provenance = {}, {}, {}
    for index, cell in enumerate(notebook['cells']):
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        for node in ast.parse(source).body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in DEFINITIONS:
                if node.name in definitions:
                    raise ValueError('duplicate reference definition')
                definitions[node.name] = node
                provenance[node.name] = {'cell': index, 'sha256': hashlib.sha256(
                    ast.get_source_segment(source, node).encode()).hexdigest()}
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in CONSTANTS:
                        constants[target.id] = ast.literal_eval(node.value)
    if set(definitions) != set(DEFINITIONS) or set(constants) != set(CONSTANTS):
        raise ValueError('incomplete Paper2 reference')
    data = PACKAGE / 'data/simulator_inputs'
    paths = {key: data / name for key, name in {
        'nodes': 'nodes.csv', 'edges': 'edges.csv', 'questions': 'question_bank.csv',
        'chapters': 'concept_to_chapter_map.csv'}.items()}
    nodes = pd.read_csv(paths['nodes']).concept_id.drop_duplicates().tolist()
    edges = list(pd.read_csv(paths['edges'])[['source', 'target']].itertuples(index=False, name=None))
    questions = pd.read_csv(paths['questions'])
    chapters = dict(pd.read_csv(paths['chapters'])[['concept_id', 'chapter']].values)
    chapter_names = sorted({chapters[node] for node in nodes})

    def namespace(edge_pairs):
        scope = {**constants, 'np': np, 'pd': pd, 'math': math, 're': re,
                 'Counter': Counter, 'deque': deque, 'dataclass': dataclass, 'field': field,
                 'nodes': nodes, 'chapter_map': chapters, 'chapters': chapter_names,
                 'levels': ('NB', 'TH', 'VD', 'UNK'),
                 'concept_index': {node: i for i, node in enumerate(nodes)},
                 'chapter_index': {name: i for i, name in enumerate(chapter_names)},
                 'level_index': {name: i for i, name in enumerate(('NB', 'TH', 'VD', 'UNK'))},
                 'FEATURE_DIM': len(nodes) + len(chapter_names) + 7,
                 'questions_by_concept': {cid: frame.sort_values(['elo_difficulty', 'question_id']).reset_index(drop=True)
                                          for cid, frame in questions.groupby('concept_id', sort=False)}}
        for name in DEFINITIONS:
            exec(compile(ast.Module(body=[definitions[name]], type_ignores=[]), str(NOTEBOOK), 'exec'), scope)
        scope['graph'] = scope['ConceptDAG'](nodes, edge_pairs)
        scope['topological_order'] = scope['graph'].topological_order()
        scope['question_features'] = {str(row.question_id): scope['item_feature'](
            str(row.concept_id), str(row.question_id), float(row.elo_difficulty))
            for row in questions.itertuples(index=False)}
        scope['concept_features'] = {cid: scope['item_feature'](cid, None, scope['MASTERY_ELO']) for cid in nodes}
        return scope

    environment = namespace(edges)
    controller = namespace(edges if controller_edges is None else controller_edges)
    estimator = namespace(edges if estimator_edges is None else estimator_edges)
    # Recompile policy classes with the original selector bound to controller scope.
    estimator['CoverageAwareSelectorMixin'] = controller['CoverageAwareSelectorMixin']
    for name in ('AdaptiveLMSPolicy', 'GAMKTPolicy'):
        exec(compile(ast.Module(body=[definitions[name]], type_ignores=[]), str(NOTEBOOK), 'exec'), estimator)
    return {'environment': environment, 'estimator': estimator, 'controller': controller,
            'provenance': {'notebook': str(NOTEBOOK.relative_to(ROOT)),
                           'notebook_sha256': hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
                           'definitions': provenance,
                           'inputs': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                      for path in paths.values()}}}
