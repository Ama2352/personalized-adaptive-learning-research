"""Bounded DATA05/06 evidence: source environment -> observable -> KT windows.

Không fit NN, mở dataset/Holdout hoặc chạy notebook lịch sử top-level.
"""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from knowledge_tracing.akt.simulator_data import SimulatorShard, fit_simulator_encoding, iter_simulator_windows
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
from knowledge_tracing.simulator_bridge import identity_hash
from knowledge_tracing.simulator_collection import CollectionRecipe, collect_training_fixture
from knowledge_tracing.simulator_data import ROLES, SimulatorSplitPlan


def check(run_id):
    if Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
        raise ValueError('use project .venv')
    sources = [ROOT / name for name in (
        'scripts/research/check_simulator_collection.py', 'src/knowledge_tracing/simulator_collection.py',
        'src/knowledge_tracing/simulator_data.py', 'src/knowledge_tracing/simulator_bridge.py',
        'src/knowledge_tracing/paper2_reference.py', 'src/knowledge_tracing/evidence.py',
        'src/knowledge_tracing/shared_kt.py', 'src/knowledge_tracing/akt/simulator_data.py',
        'src/knowledge_tracing/akt/windows.py', 'src/knowledge_tracing/akt/encoding.py',
        'src/knowledge_tracing/akt/types.py', 'src/knowledge_tracing/akt/tensors.py',
        'tests/akt/test_simulator_role_windows.py', 'tests/shared_kt/test_simulator_collection.py')]
    package = ROOT / 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
    sources += [package / 'source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb']
    sources += sorted((package / 'data/simulator_inputs').glob('*.csv'))
    note = ('# Collector và adapter simulator — fixture CPU\n\n'
            'Dùng phương trình môi trường Paper2 và84item/28concept; train-only fixture '
            '2learner×12events với logging policy không đọc latent theta. Các roles khác chỉ '
            'có assignments, không sinh dữ liệu trong collector. Không train NN, dùng Junyi/Test '
            'hoặc GPU; không có kết luận predictive/learning benefit.\n\n'
            'observable.json là whitelist có thể đưa vào KT. oracle_sidecar.json chỉ cho replay/'
            'đối chiếu, không đưa vào features. collection_manifest.json ghi source/recipe/RNG/'
            'clock/support; proof.json ghi repeat và windows/collation. tests.log/JUnit kiểm '
            'guards/parity/OOV. Counts, profile allocation và gap là fixture, chưa là protocol nghiên cứu.\n')
    with record_evidence_run(ROOT, run_id, metadata={'kind': 'CPU_SIMULATOR_COLLECTOR_RUNNER_FIXTURE',
            'max_learners_per_collection': 2, 'max_events_per_learner': 12, 'collections': 2,
            'max_collection_wall_seconds': 30, 'max_test_seconds': 60, 'optimizer_steps': 0,
            'scope': 'engineering only; S04/S05 pending; no final cohort/real data/cloud'},
            sources=sources, note=note) as directory:
        def save(name, payload):
            (directory / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

        plan = SimulatorSplitPlan('collector-adapter-engineering-only', 42, tuple((r, 2 if r == 'train' else 1) for r in ROLES))
        profiles = {a.learner_id: 'PY' if i == 0 else 'PG' for i, a in enumerate(plan.assignments('train'))}
        recipe = CollectionRecipe('uniform_items', 12, 1767225600, 1800, 30)
        collected = collect_training_fixture(plan, profiles=profiles, recipe=recipe)
        repeated = collect_training_fixture(plan, profiles=profiles, recipe=recipe)
        if collected.trajectories != repeated.trajectories or collected.oracle_sidecar != repeated.oracle_sidecar:
            raise AssertionError('collector deterministic replay failed')
        save('observable.json', [t.payload() for t in collected.trajectories])
        save('oracle_sidecar.json', collected.oracle_sidecar)
        save('collection_manifest.json', collected.manifest)
        save('split_plan.json', {'recipe': asdict(plan), 'identity': plan.identity,
                                 'scope': 'assignments only; only train trajectories generated'})
        shard = SimulatorShard(plan, collected.bank, 'train', 12, collected.trajectories)
        encoding = fit_simulator_encoding(shard)
        windows = list(iter_simulator_windows(shard, encoding, context=3, target_block=2, training=True))
        from knowledge_tracing.akt.tensors import collate_windows
        batch = collate_windows([w.window for w in windows], targets=[w.targets for w in windows],
                                n_items=len(encoding.support), device='cpu')
        scored = batch.source_rows[batch.target_mask.numpy()].tolist()
        if len(scored) != 24 or len(set(scored)) != 24:
            raise AssertionError('window target population changed')
        save('proof.json', {'repeat_observable_exact': True, 'repeat_oracle_exact': True,
            'observable_sha256': identity_hash([t.payload() for t in collected.trajectories]),
            'oracle_sha256': identity_hash(collected.oracle_sidecar), 'shard_sha256': shard.identity,
            'encoding': asdict(encoding), 'encoding_sha256': encoding.identity,
            'windows': len(windows), 'scored_target_rows': scored, 'collated_shape': list(batch.q_data.shape),
            'optimizer_steps': 0, 'model_instantiated': False, 'purpose': 'contract/counting only; no fitted prediction'})
        temporary = ROOT / 'artifacts/akt/local-tests' / ('collector-' + uuid.uuid4().hex[:12])
        command = [sys.executable, '-B', '-m', 'pytest', 'tests/shared_kt/test_simulator_collection.py',
            'tests/akt/test_simulator_role_windows.py', 'tests/shared_kt/test_simulator_data.py', '-q',
            '-p', 'no:cacheprovider', '--basetemp', str(temporary), '--junitxml', str(directory / 'tests.xml')]
        save('test_command.json', command)
        env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src') + os.pathsep + str(ROOT / 'third_party'),
               'CUDA_VISIBLE_DEVICES': '', 'PYTHONDONTWRITEBYTECODE': '1'}
        with (directory / 'tests.log').open('xb') as stream:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
        if result.returncode:
            raise RuntimeError('collector/adapter tests failed; preserve log before remediation')
        counts = runpy.run_path(str(ROOT / 'scripts/akt/refresh_gate2.py'))['test_result'](directory / 'tests.xml')
        save('test_result.json', counts)
    return verify_evidence_bundle(directory)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    print(json.dumps(check(parser.parse_args().run_id), ensure_ascii=False))
