"""Kiểm thiết bị AKT bằng dữ liệu tổng hợp có giới hạn cố định."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import time

import numpy as np
import torch

from knowledge_tracing.akt.checkpoint import load_checkpoint, restore_checkpoint, save_checkpoint
from knowledge_tracing.akt.config import AKTConfig, PROJECT_ROOT, SOURCE_COMMIT
from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.model import AKTAdapter
from knowledge_tracing.akt.prediction import export_predictions, iter_predictions
from knowledge_tracing.akt.provenance import sha256_file, verify_upstream
from knowledge_tracing.akt.tensors import collate_windows
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows


def synthetic_learners():
    return tuple(LearnerEvents(f'synthetic-{user}', 0, tuple(
        KTEvent(f'synthetic-{user}', ('A', 'B', 'C')[index % 3], index + 1,
                user * 200 + index + 1, (index + user) % 2, 0, 0)
        for index in range(200))) for user in range(2))


def synchronize(device):
    if device == 'cuda':
        torch.cuda.synchronize()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True, choices=['cpu', 'cuda'])
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    allowed = (PROJECT_ROOT / 'experiments/akt/results').resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        parser.error('output-dir must be a new directory under experiments/akt/results')
    if args.device == 'cuda' and not torch.cuda.is_available():
        parser.error('CUDA unavailable')
    output.mkdir(parents=True, exist_ok=False)
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(2)
    if args.device == 'cuda':
        torch.cuda.manual_seed_all(42)
        torch.cuda.reset_peak_memory_stats()
    config = AKTConfig(device=args.device, output_dir=output)
    learners = synthetic_learners()
    encoding = fit_vocabulary(learners)
    entries = [entry for learner in learners
               for entry in iter_windows(learner, encoding, training=True)]
    batch = collate_windows([entry.window for entry in entries], n_items=3,
                            device=args.device, targets=[entry.targets for entry in entries])
    model = AKTAdapter(config, encoding)
    optimizer = torch.optim.Adam(model.native.parameters(), lr=config.lr, betas=config.betas,
                                 eps=config.eps, weight_decay=config.weight_decay)
    identity = {'kind': 'synthetic-device-probe-v1', 'source_commit': SOURCE_COMMIT,
                'device': args.device, 'source': verify_upstream(config.source_root, SOURCE_COMMIT),
                'build_hashes': {str(path.relative_to(PROJECT_ROOT)): sha256_file(path)
                                 for path in sorted((PROJECT_ROOT / 'src/knowledge_tracing/akt').glob('*.py'))}}
    model.native.train()
    synchronize(args.device)
    started = time.perf_counter()
    step = model.step(batch, optimizer)
    synchronize(args.device)
    training_seconds = time.perf_counter() - started
    if not step['stepped'] or not step['parameter_updated'] or step['valid_targets'] != 400:
        raise ValueError('synthetic optimizer step contract failed')
    checkpoint = output / 'synthetic-epoch-1.pt'
    save_checkpoint(checkpoint, model, optimizer, identity=identity,
                    progress={'epoch': 1, 'complete': True, 'optimizer_steps': 1})
    model.checkpoint_id = sha256_file(checkpoint)
    expected = tuple(iter_predictions(model, learners))
    clone = AKTAdapter(config, encoding)
    clone_optimizer = torch.optim.Adam(clone.native.parameters(), lr=config.lr,
                                       betas=config.betas, eps=config.eps,
                                       weight_decay=config.weight_decay)
    restore_checkpoint(clone, clone_optimizer,
                       load_checkpoint(checkpoint, expected_identity=identity, device=args.device))
    clone.checkpoint_id = model.checkpoint_id
    actual = tuple(iter_predictions(clone, learners))
    np.testing.assert_allclose([row.prediction for row in actual],
                               [row.prediction for row in expected], atol=1e-6, rtol=1e-6)
    export = export_predictions(iter(actual), output_dir=output / 'predictions',
                                identity=identity, expected_learners_factory=lambda: iter(learners))
    if export['status'] != 'complete' or export['prediction_rows'] != 400:
        raise ValueError('synthetic export contract failed')
    # Đổi đáp án hiện tại và tương lai, giữ nguyên prefix trước target50.
    altered = LearnerEvents(learners[0].user_id, 0, tuple(
        KTEvent(event.user_id, event.exercise, event.time_done, event.source_row,
                1 - event.correct if index >= 50 else event.correct, event.suggested, event.fold)
        for index, event in enumerate(learners[0].events)))
    changed = tuple(iter_predictions(clone, (altered,)))
    np.testing.assert_allclose([row.prediction for row in changed[:51]],
                               [row.prediction for row in actual[:51]], atol=1e-6, rtol=1e-6)
    report = {'status': 'passed_synthetic', 'device': args.device,
              'scope': 'one synthetic epoch, one optimizer step, 400 synthetic targets',
              'cuda_lifecycle': args.device == 'cuda', 'mid_epoch_resume_verified': False,
              'gate4_pass': False, 'training_seconds': training_seconds,
              'torch': torch.__version__, 'cuda_build': torch.version.cuda,
              'gpu_name': torch.cuda.get_device_name() if args.device == 'cuda' else None,
              'peak_vram_bytes': torch.cuda.max_memory_allocated() if args.device == 'cuda' else None,
              'python': sys.version, 'platform': platform.platform(),
              'config': json.loads(json.dumps(asdict(config), default=str)),
              'step': step, 'export': export,
              'checks': ['finite_gradient_and_update', 'checkpoint_prediction_reload',
                         'exact_target_coverage', 'current_and_future_label_invariance'],
              'checkpoint_sha256': sha256_file(checkpoint), 'identity': identity,
              'pip_freeze': subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)}
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    inventory = {str(path.relative_to(output)): sha256_file(path)
                 for path in sorted(output.rglob('*')) if path.is_file()}
    (output / 'SHA256.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': str(output / 'report.json')}))


if __name__ == '__main__':
    main()
