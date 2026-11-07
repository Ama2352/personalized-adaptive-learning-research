"""Phân tích mô tả lại approved prefix, tái dùng ba graph controls bất biến."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time

import duckdb

from knowledge_tracing.akt.authorization import ASSIGNMENTS, CANONICAL_MANIFEST, SPLIT_MANIFEST
from knowledge_tracing.akt.config import DataPaths
from knowledge_tracing.akt.data import read_development_assignments
from knowledge_tracing.akt.splits import make_inner_split
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
from knowledge_tracing.gam_kt.practice_order import compare_order_controls, summarize_practice_order
from knowledge_tracing.graph_controls import graph_fingerprint
from knowledge_tracing.shared_kt import PrerequisiteGraph

ROOT = Path(__file__).resolve().parents[2]


def validate_scope(manifest):
    if (manifest.get('kind') != 'approved_cpu_junyi_order_pilot'
            or manifest.get('outer_fold') != 0 or manifest.get('matched_controls') is not True
            or manifest.get('uses_correct_labels') is not False
            or manifest.get('scope') != 'inner-train learners only'):
        raise ValueError('source is not the approved label-free inner-train pilot')
    for key, maximum in (('max_learners', 256), ('max_events_per_learner', 300), ('max_seconds', 180)):
        if type(manifest.get(key)) is not int or not 1 <= manifest[key] <= maximum:
            raise ValueError('source exceeds approved CPU limits')
    if manifest.get('control_spec', {}).get('seeds') != [0, 1, 2]:
        raise ValueError('unexpected source control seeds')


def analyze(run_id, *, source_run_id='cpu-junyi-controls-20261107-02-expanded'):
    if Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
        raise ValueError('use project .venv interpreter')
    # Không nhận đường dẫn tùy ý bên ngoài kho evidence.
    if (not source_run_id or Path(source_run_id).name != source_run_id
            or '/' in source_run_id or '\\' in source_run_id or ':' in source_run_id):
        raise ValueError('invalid source run ID')
    started = time.perf_counter()
    source = ROOT / 'research_tracking/runs' / source_run_id
    verify_evidence_bundle(source)
    prior = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    validate_scope(prior)
    paths = DataPaths(CANONICAL_MANIFEST.parent / 'canonical', ASSIGNMENTS,
                      CANONICAL_MANIFEST, SPLIT_MANIFEST)
    sources = [Path(__file__), ROOT / 'src/knowledge_tracing/gam_kt/practice_order.py',
        ROOT / 'src/knowledge_tracing/evidence.py', ROOT / 'src/knowledge_tracing/graph_controls.py',
        ROOT / 'src/knowledge_tracing/shared_kt.py', ROOT / 'src/knowledge_tracing/akt/data.py',
        ROOT / 'src/knowledge_tracing/akt/splits.py', ROOT / 'src/knowledge_tracing/akt/config.py',
        source / 'manifest.json', source / 'corrected_graph.json', source / 'matched_controls.json',
        paths.assignments, paths.canonical_manifest, paths.split_manifest,
        ROOT / 'dataset/junyi_Exercise_table.csv']
    for path in (paths.assignments, paths.canonical_manifest, paths.split_manifest, sources[-1]):
        expected = prior['sources_sha256'].get(path.relative_to(ROOT).as_posix())
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('frozen source data identity differs from original pilot')
    metadata = {'kind': 'descriptive_common_population_order_analysis', 'rq': ['RQ2'],
        'authorization': 'User continued bounded CPU engineering; reuse delegated max256×300/180s scope',
        'source_run_id': source_run_id, 'max_learners': prior['max_learners'],
        'max_events_per_learner': prior['max_events_per_learner'], 'max_seconds': prior['max_seconds'],
        'uses_correct_labels': False, 'holdout_requested': False, 'outer_fold': 0,
        'graph_controls_reused': True, 'statistical_inference': 'none, diagnostic descriptive only'}
    note = '''# Common-population sensitivity của Junyi order

Tái dùng graph base và cả ba controls từ run mở rộng đã được duyệt. Đọc lại đúng hash-ranked inner-train cohort và bounded prefix; không correctness/Holdout, không train model, không tạo graph mới hoặc chọn seed.

So sánh equal-weight learner, trong mỗi learner lấy trung bình các observed child có incoming edges. Giữ denominator incoming degree như nhau giữa graph. Tách parent xuất hiện trước, sau, trùng timestamp và chưa xuất hiện trong prefix. Common-coobserved sensitivity dùng cùng learner–child intersection giữa hai graph, báo attrition; vẫn không có instructional/causal interpretation. Không xuất raw learner IDs hoặc p-value/CI từ pilot.
'''
    with record_evidence_run(ROOT, run_id, metadata=metadata, sources=sources, note=note) as directory:
        assignments = read_development_assignments(paths)
        split = make_inner_split(assignments, outer_fold=0)
        cohort = sorted(split.inner_train_users, key=lambda user: hashlib.sha256(
            f'order-pilot-v1|{user}'.encode()).hexdigest())[:prior['max_learners']]
        if hashlib.sha256(json.dumps(sorted(cohort)).encode()).hexdigest() != prior['cohort_sha256']:
            raise ValueError('source cohort identity mismatch')
        selected = assignments[assignments.user_id.isin(cohort)].copy()
        con = duckdb.connect(config={'memory_limit': '512MB', 'threads': '2', 'temp_directory': ''})
        timer = threading.Timer(max(.01, prior['max_seconds']-(time.perf_counter()-started)), con.interrupt)
        timer.daemon = True
        try:
            con.register('selected_inner_train', selected)
            timer.start()
            rows = con.execute("SELECT c.user_id,c.exercise,c.time_done,c.source_row,u.fold,'development' AS partition "
                "FROM read_parquet(?,hive_partitioning=true) c JOIN selected_inner_train u ON c.user_id=u.user_id "
                "QUALIFY row_number() OVER (PARTITION BY c.user_id ORDER BY c.time_done,c.source_row)<=? "
                "ORDER BY c.user_id,c.time_done,c.source_row",
                [str(paths.canonical / '**/*.parquet'), prior['max_events_per_learner']]).df().to_dict('records')
        finally:
            timer.cancel()
            con.close()
        corrected = json.loads((source / 'corrected_graph.json').read_text(encoding='utf-8'))
        controls = json.loads((source / 'matched_controls.json').read_text(encoding='utf-8'))
        if [value['seed'] for value in controls] != [0, 1, 2]:
            raise ValueError('source controls must preserve all prespecified seeds')
        base = [tuple(edge) for edge in corrected['corrected_edges']]
        base_hash = graph_fingerprint(PrerequisiteGraph.from_edges(corrected['nodes'], base))
        comparisons = []
        for control in controls:
            if time.perf_counter() - started >= prior['max_seconds']:
                raise TimeoutError('common-population diagnostic wall cap exceeded')
            if control['status'] != 'constructed':
                comparisons.append({'seed': control['seed'], 'status': 'unavailable', 'reason': control.get('reason')})
                continue
            edges = [tuple(edge) for edge in control['edges']]
            if (base_hash != control['original_sha256'] or graph_fingerprint(
                    PrerequisiteGraph.from_edges(corrected['nodes'], edges)) != control['result_sha256']):
                raise ValueError('source graph hash mismatch')
            summary = summarize_practice_order(rows, edges, allowed_users=set(cohort), outer_fold=0,
                                               max_events=prior['max_events_per_learner'])
            if summary != control['order']:
                raise ValueError('reloaded cohort does not reproduce original order summary')
            comparisons.append({'seed': control['seed'], 'status': 'analyzed', 'graph_sha256': control['result_sha256'],
                'contrast': compare_order_controls(rows, base, edges, allowed_users=set(cohort), outer_fold=0,
                                                   max_events=prior['max_events_per_learner'])})
        identity = compare_order_controls(rows, base, base, allowed_users=set(cohort), outer_fold=0,
                                          max_events=prior['max_events_per_learner'])
        if time.perf_counter() - started >= prior['max_seconds']:
            raise TimeoutError('common-population diagnostic wall cap exceeded')
        result = {'source_run_id': source_run_id, 'learners': len(cohort), 'events': len(rows),
            'cohort_sha256': prior['cohort_sha256'], 'base_graph_sha256': base_hash,
            'prefix_rows_sha256': hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest(),
            'original_control_summaries_reproduced': True, 'comparisons': comparisons,
            'identity_negative_control': identity, 'elapsed_seconds': time.perf_counter() - started}
        (directory / 'common_population.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--source-run-id', default='cpu-junyi-controls-20261107-02-expanded')
    args = parser.parse_args()
    print(analyze(args.run_id, source_run_id=args.source_run_id))
