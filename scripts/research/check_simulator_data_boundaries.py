"""Fixture CPU nhỏ: split/schema/history scope; không train hoặc mở dataset."""

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
from knowledge_tracing.graph_context import EdgeConfidence, audit_graph_context
from knowledge_tracing.shared_kt import PrerequisiteGraph
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from knowledge_tracing.simulator_data import ROLES, ObservableTrajectory, SimulatorSplitPlan, validate_role_shard


def run(run_id):
    if Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
        raise ValueError('use project .venv')
    sources = [ROOT / name for name in (
        'scripts/research/check_simulator_data_boundaries.py', 'src/knowledge_tracing/simulator_data.py',
        'src/knowledge_tracing/graph_context.py', 'src/knowledge_tracing/simulator_bridge.py',
        'src/knowledge_tracing/shared_kt.py', 'src/knowledge_tracing/evidence.py',
        'src/knowledge_tracing/akt/windows.py', 'src/knowledge_tracing/akt/types.py',
        'tests/shared_kt/test_simulator_data.py', 'tests/shared_kt/test_graph_context.py',
        'scripts/akt/refresh_gate2.py', 'tests/akt/test_gate2_refresh.py')]
    metadata = {'kind': 'CPU_SIMULATOR_DATA_GRAPH_BOUNDARY_FIXTURE', 'schema_version': 1,
                'limits': {'learners_per_role': 2, 'roles': 4, 'events_per_learner': 8,
                           'test_timeout_seconds': 60, 'neural_training_steps': 0},
                'data': 'arithmetic fixture only; no Junyi, real Holdout or latent simulator learner data',
                'methodology': 'S04/S05 pending; no selection/calibration/controller adoption'}
    note = ('# Fixture hợp đồng dữ liệu và graph context\n\n'
            'Nguồn: hai concept tổng hợp, tám learner với đáp án số học. Đây là kiểm kỹ thuật, '
            'không là thí nghiệm learner thật, KT benefit hoặc chứng minh RQ. Không train NN, '
            'không đọc Junyi/Test. Tên final ở đây chỉ là role trong fixture.\n\n'
            'proof.json lưu role coverage và counterexample full-history so với effective window; '
            'tests.log lưu các guard/negative controls. Manifest hash nguồn và output. '
            'Seed namespaces không chứng minh độc lập thống kê; confidence provenance chưa được '
            'học/calibrate. CG-AKT gate/augmentation chưa được cài ở gói này.\n')
    with record_evidence_run(ROOT, run_id, metadata=metadata, sources=sources, note=note) as directory:
        bank = SimulatorBank('arithmetic-data-context-v1', tuple(SimulatorItem(i, c, 0)
                             for i, c in [('a', 'A'), ('b', 'B'), ('oov', 'A')]))
        plan = SimulatorSplitPlan('engineering-fixture-not-study-allocation', 42, tuple((r, 2) for r in ROLES))
        shards = {role: [] for role in ROLES}
        row = 0
        for assignment in plan.assignments():
            observations = []
            for rank in range(8):
                row += 1
                observations.append(Observation(ItemQuery('a', rank, row), int(rank > 1)))
            shards[assignment.role].append(ObservableTrajectory(assignment.learner_id, plan.identity,
                identity_hash(bank.identity), 'arithmetic-only', tuple(observations)))
        role_audits = {role: validate_role_shard(shards[role], plan=plan, bank=bank, role=role,
                                               max_events_per_learner=8) for role in ROLES}
        graph = PrerequisiteGraph.from_edges(['A', 'B'], [('A', 'B')])
        confidence = EdgeConfidence('fixed_uniform', (('A', 'B', 1),), identity_hash({'source': 'fixed-one-fixture'}))
        history = shards['train'][0].observations
        kwargs = dict(bank=bank, graph=graph, confidence=confidence, history=history,
                      query=ItemQuery('b', 8, row+1), trained_items=('a', 'b'), context=3, target_block=2)
        changed = dict(kwargs, history=tuple(replace(o, correct=1-o.correct) if i < 5 else o
                                            for i, o in enumerate(history)))
        matched = audit_graph_context(**kwargs)
        matched_changed = audit_graph_context(**changed)
        full_options = dict(scope='full_history', purpose='history_sensitivity')
        full = audit_graph_context(**kwargs, **full_options)
        full_changed = audit_graph_context(**changed, **full_options)
        if matched != matched_changed or full['weighted_observed_correctness'] == full_changed['weighted_observed_correctness']:
            raise AssertionError('history-scope counterexample failed')
        proof = {'scope': 'software contract fixture only; not research evidence of improved learning',
                 'plan_sha256': plan.identity, 'role_audits': role_audits,
                 'matched_original': matched, 'matched_prefix_changed': matched_changed,
                 'full_original': full, 'full_prefix_changed': full_changed,
                 'no_signal': audit_graph_context(**kwargs, enabled=False),
                 'conclusion': 'Excluded prefix cannot change matched graph evidence; full-history can change it'}
        (directory / 'proof.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        temp = ROOT / 'artifacts/akt/local-tests' / ('data-context-' + uuid.uuid4().hex)
        command = [sys.executable, '-B', '-m', 'pytest', 'tests/shared_kt/test_simulator_data.py',
                   'tests/shared_kt/test_graph_context.py', 'tests/akt/test_gate2_refresh.py', '-q',
                   '-p', 'no:cacheprovider', '--basetemp', str(temp), '--junitxml', str(directory / 'tests.xml')]
        (directory / 'test_command.json').write_text(json.dumps(command, indent=2)+'\n', encoding='utf-8')
        env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src') + os.pathsep + str(ROOT / 'third_party'),
               'CUDA_VISIBLE_DEVICES': '', 'PYTHONDONTWRITEBYTECODE': '1'}
        with (directory / 'tests.log').open('xb') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=60)
        if result.returncode:
            raise RuntimeError('targeted tests failed; inspect immutable tests.log')
        # Không coi exit code zero là đủ; parser từ chối zero/skip/failure/error.
        import runpy
        counts = runpy.run_path(str(ROOT / 'scripts/akt/refresh_gate2.py'))['test_result'](directory / 'tests.xml')
        (directory / 'test_result.json').write_text(json.dumps(counts, indent=2)+'\n', encoding='utf-8')
    return verify_evidence_bundle(directory)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    print(json.dumps(run(parser.parse_args().run_id), ensure_ascii=False))
