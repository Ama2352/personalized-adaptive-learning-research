"""Đọc và kiểm checkpoint A3 đã tải bằng CPU, không train hoặc gọi cloud."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=int, required=True)
    args = parser.parse_args()
    output = ROOT / f'experiments/akt/results/modal-junyi-a3-refit-h100-20261115-{args.attempt:02}'
    receipt = json.loads((output / 'remote-inventory.json').read_text())
    assert json.loads((output / 'COMPLETE.json').read_text())['status'] == 'LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
    assert json.loads((output / 'app-budget-guard.json').read_text())['stop_acknowledged']
    prefix = 'outputs/junyi-a3-refit-20261114-01/'
    candidates = []
    for name, pin in receipt['files'].items():
        match = re.fullmatch(prefix + r'checkpoints/refit-batch-epoch-(\d+)-step-(\d+)-[a-f0-9]+/state.pt', name)
        if match:
            candidates.append(((int(match[1]), int(match[2])), name, pin))
    position, name, pin = max(candidates)
    checkpoint = output / 'files' / name
    with checkpoint.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert digest == pin['sha256'] and checkpoint.stat().st_size == pin['bytes']
    identity = json.loads((output / 'files' / prefix / 'run-manifest.json').read_text())
    from knowledge_tracing.akt.checkpoint import load_training_snapshot
    import torch
    payload = load_training_snapshot(checkpoint, expected_identity=identity, device='cpu')
    state = payload['resume_state']
    assert state['epoch'] == position[0] and state['optimizer_steps'] == position[1]
    for tensor in payload['model_state_dict'].values():
        assert torch.isfinite(tensor).all().item()
    optimizer_tensors = 0
    for values in payload['optimizer_state_dict']['state'].values():
        for tensor in values.values():
            if isinstance(tensor, torch.Tensor):
                assert torch.isfinite(tensor).all().item()
                optimizer_tensors += 1
    assert optimizer_tensors and state['sampler_state'] and state['trainer_state']
    for key in ('python_rng', 'numpy_rng', 'torch_rng', 'cuda_rng'):
        assert key in payload
    assert payload['cuda_rng']
    history = state['trainer_state']['selection_state']['history']
    assert len(history) == position[0] - 1
    assert all(row['valid_targets'] == 14947674 and row['optimizer_steps'] == 2040 for row in history)
    result = dict(status='PASS_A3_LOCAL_RECOVERY_CHECKPOINT',
        source_receipt=(output / 'remote-inventory.json').relative_to(ROOT).as_posix(),
        checkpoint=checkpoint.relative_to(ROOT).as_posix(), remote_checkpoint='experiments/akt/results/' + name[len('outputs/'):],
        checkpoint_sha256=digest, checkpoint_bytes=pin['bytes'], complete_epochs=len(history),
        partial_epoch=position[0], partial_optimizer_step=position[1], frozen_epochs=identity['epochs'],
        model_tensors_finite=True, optimizer_tensors_finite=True, sampler_and_rng_present=True,
        limits_vi='Checkpoint đang học dở, chưa phải model refit9epoch. Kiểm bằng CPU, không xác nhận trước tính tương đương số học trên thiết bị GPU khác.')
    with (HERE / f'a3-checkpoint-verified{args.attempt:02}.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
