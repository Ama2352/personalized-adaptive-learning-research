"""Chạy diagnostic nguồn Paper2 có giới hạn và xuất evidence bundle bất biến."""

import argparse
from collections import Counter
import copy
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

import numpy as np
import pandas as pd

from knowledge_tracing.diagnostics import DecisionTrace, compare_decision_traces
from knowledge_tracing.paper2_reference import ROOT, load_reference
from knowledge_tracing.graph_controls import rewire_matched_graph
from knowledge_tracing.shared_kt import PrerequisiteGraph
from check_simulator_assumptions import check_retention_source, check_paper1_reentry_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def closed_loop_pilot(reference, empty, *, seed, profile, steps, stream):
    """Dùng dynamics/selector gốc, paired latent starts và step-indexed uniforms."""
    scope = reference['environment']
    model = reference['estimator']
    base = scope['persona_base_abilities'](profile, seed)
    uniforms = np.random.default_rng(seed).random((steps, 2))
    rows = []
    factories = {'graph_free': lambda: model['GAMKTPolicy'](False),
                 'graph_package': lambda: model['GAMKTPolicy'](True),
                 'empty_graph_package': lambda: empty['estimator']['GAMKTPolicy'](True)}
    for variant, factory in factories.items():
        environment = scope['LatentStudentEnvironment'](base)
        policy = factory()
        timestamp = pd.Timestamp('2026-01-01', tz='UTC')
        actions = []
        for step in range(steps):
            timestamp += pd.Timedelta(hours=72 if step > 0 and step % len(base) == 0 else 6)
            cid, qid, difficulty = policy.select()
            prediction = policy.predict(cid, qid, difficulty, timestamp)
            outcome = environment.interact(cid, difficulty, timestamp, *uniforms[step])
            stream.write(json.dumps({'seed': seed, 'profile': profile, 'variant': variant,
                'step': step, 'concept': cid, 'question': qid, 'prediction': prediction,
                'timestamp': timestamp.isoformat(), **outcome}, ensure_ascii=False) + '\n')
            policy.update(cid, qid, difficulty, timestamp, outcome['y'], prediction)
            actions.append(cid)
        final = environment.snapshot(timestamp)
        retained = environment.snapshot(timestamp + pd.Timedelta(days=14))
        net_gain = float(np.mean([final[cid] - base[cid] for cid in base]))
        retained_gain = float(np.mean([retained[cid] - base[cid] for cid in base]))
        if abs(retained_gain - np.exp(-.06*14)*net_gain) > 1e-10:
            raise ValueError('closed-loop retention identity failed')
        rows.append({'seed': seed, 'profile': profile, 'variant': variant,
                     'net_mean_theta_gain': net_gain, 'retained_mean_theta_gain': retained_gain,
                     'concepts_covered': len(set(actions)), 'actions': actions})
    return rows


def run(output, *, seeds=3, steps=60, mode='fixed-stream'):
    if mode not in {'fixed-stream', 'closed-loop'} or not 1 <= seeds <= 5 or not 1 <= steps <= 120:
        raise ValueError('diagnostic workload exceeds registered local cap')
    output = Path(output).resolve()
    allowed = (ROOT / 'research_tracking/runs').resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        raise ValueError('output must be a unique research_tracking/runs child')
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    manifest = {'status': 'running', 'started_utc': datetime.now(timezone.utc).isoformat(),
                'kind': 'bounded_source_diagnostic', 'rq': ['RQ1', 'RQ2'],
                'command': [sys.executable, *sys.argv], 'seeds': list(range(20000, 20000+seeds)),
                'steps_per_profile': steps, 'python': sys.executable,
                'mode': mode,
                'git_head_before_run': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
    write = lambda name, payload: (output / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write('manifest.json', manifest)
    try:
        reference = load_reference()
        empty = load_reference(estimator_edges=[])
        env_scope = reference['environment']
        model_scope = reference['estimator']
        comparisons = []
        with gzip.open(output / 'traces.jsonl.gz', 'wt', encoding='utf-8') as traces:
            for seed in manifest['seeds']:
                for profile in env_scope['PERSONAS']:
                    if mode == 'closed-loop':
                        comparisons.extend(closed_loop_pilot(reference, empty, seed=seed,
                                                            profile=profile, steps=steps, stream=traces))
                        continue
                    base = env_scope['persona_base_abilities'](profile, seed)
                    environment = env_scope['LatentStudentEnvironment'](base)
                    policies = {'graph_free': model_scope['GAMKTPolicy'](False),
                                'graph_package': model_scope['GAMKTPolicy'](True),
                                'empty_graph_package': empty['estimator']['GAMKTPolicy'](True)}
                    records = {name: [] for name in policies}
                    rng = np.random.default_rng(seed)
                    uniforms = rng.random((steps, 2))
                    items = [str(row.question_id) for frame in model_scope['questions_by_concept'].values()
                             for row in frame.itertuples(index=False)]
                    item_lookup = {str(row.question_id): (cid, float(row.elo_difficulty))
                                   for cid, frame in model_scope['questions_by_concept'].items()
                                   for row in frame.itertuples(index=False)}
                    for step in range(steps):
                        timestamp = pd.Timestamp('2026-01-01', tz='UTC') + pd.Timedelta(hours=6*(step+1))
                        qid = items[int(rng.integers(len(items)))]
                        cid, difficulty = item_lookup[qid]
                        outcome = environment.interact(cid, difficulty, timestamp, *uniforms[step])
                        for name, policy in policies.items():
                            probability = policy.predict(cid, qid, difficulty, timestamp)
                            # Preview select trên bản sao để giữ fixed-stream state nguyên vẹn.
                            preview = copy.deepcopy(policy)
                            action = preview.select()[0]
                            # Selector có anti-drill escape, ready_set gốc có thể hẹp hơn candidates.
                            ready = frozenset(policy.ready_set())
                            if action not in ready:
                                raise ValueError('preview action requires explicit eligible-set instrumentation')
                            record = DecisionTrace(str(step), f'{seed}-{profile}', outcome['y'], probability,
                                {node: policy.mastery_score(node) for node in model_scope['nodes']}, ready, action,
                                frozenset(node for node in model_scope['nodes'] if policy.is_mastered(node)))
                            records[name].append(record)
                            traces.write(json.dumps({'variant': name, **asdict(record)}, ensure_ascii=False,
                                                    default=lambda value: sorted(value)) + '\n')
                            policy.update(cid, qid, difficulty, timestamp, outcome['y'], probability)
                            policy.selection_counts[cid] += 1
                            policy.question_counts[qid] += 1
                            policy.recent_concepts.append(cid)
                            policy.current_chapter = model_scope['chapter_map'][cid]
                    for name in ('graph_package', 'empty_graph_package'):
                        comparisons.append({'seed': seed, 'profile': profile, 'candidate': name,
                            **compare_decision_traces(records['graph_free'], records[name], threshold=.5)})
        write('closed_loop_outcomes.json' if mode == 'closed-loop' else 'comparisons.json', comparisons)
        write('retention.json', check_retention_source())
        write('paper1_counterexample.json', check_paper1_reentry_source())
        graph = model_scope['graph']
        edges = [(parent, child) for parent in graph.nodes for child in graph.successors(parent)]
        matched = rewire_matched_graph(PrerequisiteGraph.from_edges(graph.nodes, edges), swaps=1,
                                      chapters={cid: model_scope['chapter_map'][cid] for cid in graph.nodes})
        write('matched_graph.json', asdict(matched))
        write('source_provenance.json', reference['provenance'])
        source_files = [Path(__file__), ROOT / 'scripts/research/check_simulator_assumptions.py',
                        ROOT / 'src/knowledge_tracing/paper2_reference.py', ROOT / 'src/knowledge_tracing/diagnostics.py',
                        ROOT / 'src/knowledge_tracing/graph_controls.py']
        manifest['implementation_sha256'] = {str(path.relative_to(ROOT)): sha(path) for path in source_files}
        manifest['status'] = 'completed'
        (output / 'README.md').write_text(
            '# Chẩn đoán RQ1 và retention Paper2\n\n'
            'Đây là bounded diagnostic trên simulator inputs lịch sử và định nghĩa nguồn được nạp bằng AST allowlist. '
            'Nguồn gốc, cell hashes và input hashes nằm trong source_provenance.json.\n\n'
            'Cùng chuỗi item, đáp án và timestamp cho graph-free, graph-package và empty-graph package. '
            'Graph môi trường và controller giữ nguyên. Empty-graph package vẫn bật adaptation cục bộ. '
            'Mastery boolean theo đúng is_mastered nguồn, khác score>=0.5. Action là preview trên bản sao.\n\n'
            'comparisons.json chứa mỗi seed/profile, traces.jsonl.gz chứa trace trước update. '
            'retention.json kiểm đẳng thức decay trên actual theta_at.\n\n'
            'paper1_counterexample.json kiểm selector nguồn với DAG A1→B1→A2 và mastery được gán theo kịch bản. '
            'matched_graph.json chứa một swap giữ degree/chapter counts, chưa matching train support.\n\n'
            'Có thể trích bằng chứng cơ chế và sự khác biệt trên các stream đã đo. '
            'Chưa là closed-loop learning-outcome comparison, chưa là causal benefit trên Junyi, '
            'chưa có CI hoặc kiểm định kết luận. Action preview trong fixed stream không phải actual served action. '
            'Seed diagnostic được công khai, không dùng lại như final unseen test.\n', encoding='utf-8')
        if mode == 'closed-loop':
            (output / 'README.md').write_text(
                '# Pilot closed-loop Paper2 trên CPU\n\n'
                'Dùng definitions/dynamics/selector nguồn với graph môi trường và controller cố định. '
                'Ba variant graph-free, full graph-package và empty-graph package dùng cùng latent starts, '
                'cùng uniforms theo step. Khi actions khác nhau thì labels cũng có thể khác.\n\n'
                'closed_loop_outcomes.json chứa net gain, retained gain, coverage và actual action sequences. '
                'traces.jsonl.gz chứa events thật được phục vụ trong simulator trước update. '
                'Lịch gap6h và72h mỗi28steps theo nguồn. Đây là pilot ngắn, chưa tái lập bảng500steps của Paper2.\n\n'
                'Không diễn giải differences prediction như paired same-target metrics. '
                'Không gán toàn bộ package effect cho edges. Retention theta gain sau14ngày được kiểm '
                'bằng hệ số exp(-.84) trên từng run, nên không là outcome độc lập với final theta gain '
                'trong điều kiện này. Chưa thực hiện inference/CI hoặc kết luận causal ngoài simulator.\n',
                encoding='utf-8')
    except Exception as error:
        manifest.update(status='failed', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        manifest['elapsed_seconds'] = time.perf_counter() - started
        (output / 'execution.log').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        manifest['outputs_sha256'] = {path.name: sha(path) for path in output.iterdir() if path.name != 'manifest.json'}
        write('manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--seeds', type=int, default=3)
    parser.add_argument('--steps', type=int, default=60)
    parser.add_argument('--mode', choices=('fixed-stream', 'closed-loop'), default='fixed-stream')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', args.run_id):
        parser.error('invalid run ID')
    print(json.dumps(run(ROOT / 'research_tracking/runs' / args.run_id,
                         seeds=args.seeds, steps=args.steps, mode=args.mode), ensure_ascii=False, indent=2))
