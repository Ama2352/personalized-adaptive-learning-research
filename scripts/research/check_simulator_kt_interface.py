"""Kiểm nối Paper2 item bank với AKT bằng fixture CPU tổng hợp, không RQ experiment."""

import argparse
import csv
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import time

import torch

from knowledge_tracing.akt.checkpoint import save_checkpoint
from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.model import AKTAdapter
from knowledge_tracing.akt.online import load_online_akt, simulator_model_identity
from knowledge_tracing.akt.provenance import sha256_file
from knowledge_tracing.akt.training import train_epoch
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
from knowledge_tracing.simulator_bridge import (SimulatorBank, SimulatorItem, OnlineSession,
    ItemQuery, ReferenceSet, probe_references)

ROOT = Path(__file__).resolve().parents[2]
INPUTS = ROOT / 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs'


def tensor_state_hash(model):
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode())
        digest.update(str(value.dtype).encode())
        digest.update(str(tuple(value.shape)).encode())
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def check(run_id):
    if Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
        raise ValueError('use project .venv interpreter')
    started = time.perf_counter()
    sources = [Path(__file__), ROOT / 'src/knowledge_tracing/simulator_bridge.py',
        ROOT / 'src/knowledge_tracing/evidence.py', INPUTS / 'question_bank.csv', INPUTS / 'nodes.csv']
    sources += list((ROOT / 'src/knowledge_tracing/akt').glob('*.py'))
    metadata = {'kind': 'simulator_kt_interface_cpu_engineering', 'rq': ['RQ1','RQ3'],
        'authorization': 'User continue autonomous CPU engineering2026-11-07',
        'data_scope': 'Paper2 public item metadata; response sequences synthesized arithmetically',
        'max_training_learners': 2, 'max_training_targets': 168, 'max_epochs': 1,
        'max_optimizer_steps': 2, 'max_train_seconds': 30, 'max_total_seconds': 120,
        'device': 'cpu', 'seed': 42, 'checkpoint_selection': 'none; fixed one-epoch engineering fixture',
        'reference_weights': 'equal three-item weights for fixture only; not approved mastery definition',
        'junyi_requested': False, 'holdout_requested': False, 'cuda_executed': False,
        'scientific_inference': 'none; no predictive/learning benefit result'}
    note = '''# Kiểm hợp đồng simulator–AKT trên CPU

Dùng đúng28concept/84item của Paper2; không đổi simulator hoặc chạy latent environment. Response labels là chuỗi arithmetic fixture, không phải học sinh hoặc model simulator. Chỉ train168targets,1epoch≤2updates để có checkpoint fitted thật cho kỹ thuật; không dùng random weights rồi gọi fitted, không báo accuracy/mastery gain.

Reference weights1/3 chỉ để kiểm API, chưa là mastery protocol. Probes không commit history, snapshot/reset/cross-learner isolation và domain/recipe rejects phải pass. Lưu checkpoint ngoài bundle ở experiments/akt/results/<run-id>, bundle chỉ giữ hash/provenance/results. Không dùng kết quả làm bằng chứng CG-AKT có ích hoặc GPU/real-data ready.
'''
    with record_evidence_run(ROOT, run_id, metadata=metadata, sources=sources, note=note) as directory:
        with (INPUTS / 'question_bank.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        with (INPUTS / 'nodes.csv').open(encoding='utf-8-sig', newline='') as stream:
            concepts = {row['concept_id'] for row in csv.DictReader(stream)}
        bank = SimulatorBank('paper2-grade10-interface-fixture-v1', tuple(SimulatorItem(
            row['question_id'], row['concept_id'], float(row['elo_difficulty'])) for row in rows))
        if len(bank.items) != 84 or len(concepts) != 28 or {item.concept_id for item in bank.items} != concepts:
            raise ValueError('unexpected Paper2 item/concept mapping')
        refs = tuple(ReferenceSet(concept, tuple((item.item_id, 1/3) for item in bank.items
                                               if item.concept_id == concept)) for concept in sorted(concepts))
        learners = tuple(LearnerEvents(f'fixture-train-{n}', 1, tuple(
            KTEvent(f'fixture-train-{n}', item.item_id, i, n*84+i+1, (i+n)%2, 0, 1)
            for i, item in enumerate(bank.items))) for n in range(2))
        encoding = fit_vocabulary(learners)
        output = ROOT / 'experiments/akt/results' / run_id
        output.mkdir(parents=True, exist_ok=False)
        config = AKTConfig(output_dir=output, run_id=run_id, d_model=16, heads=2,
            d_ff=32, final_fc=16, dropout=.2, max_epochs=1, batch_size=2)
        torch.manual_seed(42)
        adapter = AKTAdapter(config, encoding)
        optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr,
                                      betas=config.betas, eps=config.eps, weight_decay=config.weight_decay)
        def windows():
            for learner in learners:
                yield from iter_windows(learner, encoding, context=100, target_block=100, training=True)
        stats = train_epoch(adapter, windows, optimizer=optimizer, epoch=1,
            budget={'max_steps':2, 'max_seconds':30, 'max_targets':168,
                    'max_rss_bytes':2*1024**3, 'min_available_ram_bytes':256*1024**2})
        if not stats.complete or stats.valid_targets != 168 or stats.optimizer_steps > 2:
            raise ValueError('synthetic fixture did not complete bounded training')
        identity = {**simulator_model_identity(config, bank, encoding),
            'artifact_role':'synthetic_interface_fixture', 'seed':42, 'training_targets':168,
            'input_sources_sha256':{path.name:sha256_file(path) for path in (INPUTS/'question_bank.csv',INPUTS/'nodes.csv')}}
        checkpoint = output / 'synthetic-final.pt'
        save_checkpoint(checkpoint, adapter, optimizer, identity=identity,
            progress={'complete':True, 'epoch':1, 'role':'synthetic_final', 'training':asdict(stats)})
        backend = load_online_akt(checkpoint, config, bank, expected_sha256=sha256_file(checkpoint),
                                  expected_identity=identity)
        native = backend._adapter.native
        before_weights, before_rng = tensor_state_hash(native), torch.get_rng_state().clone()
        a = OnlineSession(backend, bank, learner_id='fixture-eval-a', max_events=8)
        b = OnlineSession(backend, bank, learner_id='fixture-eval-b', max_events=8)
        before = a.snapshot()
        cold = probe_references(a, refs, timestamp=0, source_row=10001)
        if a.snapshot() != before or any(value['supported_items']!=3 for value in cold['scores'].values()):
            raise ValueError('cold reference probe changed history or coverage')
        for index, item in enumerate(bank.items[:8]):
            if time.perf_counter()-started >= 120:
                raise TimeoutError('synthetic interface workload wall cap exceeded')
            ticket = a.predict(ItemQuery(item.item_id, index, 10001+index))
            a.observe(ticket, index%2)
        snapshot = a.snapshot()
        after = probe_references(a, refs, timestamp=8, source_row=10009)
        if a.snapshot() != snapshot:
            raise ValueError('reference probes became practice events')
        clone = OnlineSession(backend, bank, learner_id='fixture-eval-a', max_events=8)
        clone.restore(json.loads(json.dumps(snapshot)))
        restored = probe_references(clone, refs, timestamp=8, source_row=10009)
        if restored != after:
            raise ValueError('history snapshot changed reference predictions')
        independent = probe_references(b, refs, timestamp=0, source_row=10001)
        if independent['scores'] != cold['scores'] or b.history:
            raise ValueError('cross-learner state contamination')
        a.reset()
        reset = probe_references(a, refs, timestamp=0, source_row=10001)
        if reset != cold:
            raise ValueError('reset did not reproduce cold state')
        rejections = {}
        for label, other_config, other_bank in (
                ('cross_environment', config, replace(bank, environment_id='Junyi-fixture')),
                ('window_recipe_drift', replace(config, context=50), bank)):
            try:
                load_online_akt(checkpoint, other_config, other_bank,
                                expected_sha256=sha256_file(checkpoint), expected_identity=identity)
            except ValueError:
                rejections[label] = True
            else:
                raise ValueError('incompatible checkpoint accepted')
        if tensor_state_hash(native) != before_weights or not torch.equal(before_rng, torch.get_rng_state()):
            raise ValueError('online evaluation changed model weights or RNG')
        elapsed = time.perf_counter()-started
        if elapsed >= 120:
            raise TimeoutError('synthetic interface workload wall cap exceeded')
        result = {'status':'passed_cpu_interface_fixture','concepts':28,'items':84,
            'training':asdict(stats), 'observed_eval_events':8, 'reference_items_per_concept':3,
            'checkpoint':str(checkpoint.relative_to(ROOT)), 'checkpoint_sha256':sha256_file(checkpoint),
            'checkpoint_identity':identity, 'frozen_state_sha256':before_weights,
            'weights_unchanged':True,'torch_rng_unchanged':True,'reference_queries_do_not_commit':True,
            'snapshot_roundtrip_exact':True,'reset_exact':True,'cross_learner_isolated':True,
            'incompatible_checkpoint_rejected':rejections,'elapsed_seconds':elapsed,
            'inference_features':{'item_id':True,'past_responses':True,'interaction_positions':True,
                                  'elapsed_calendar_time':False,'raw_difficulty_numeric':False,'latent_theta':False},
            'scope':'Engineering fixture; no calibration/mastery/learning-benefit claim'}
        (directory/'interface_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (directory/'reference_probes.json').write_text(json.dumps({'cold':cold,'after8':after},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (directory/'session_snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {'bundle':str(directory),'integrity':verify_evidence_bundle(directory)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.run_id),ensure_ascii=False,indent=2))
