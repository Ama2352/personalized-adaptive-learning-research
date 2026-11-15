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
    parser.add_argument('--execution-id', help='Run tải artifact đã có, mặc định giữ tên H100 lịch sử')
    parser.add_argument('--recovery', action='store_true', help='Kiểm index phục hồi sau watchdog, giữ nguyên hồ sơ lỗi')
    parser.add_argument('--evidence-suffix', default='', help='Hậu tố khi cần bổ sung bằng chứng phiên bản mới')
    args = parser.parse_args()
    execution_id = args.execution_id or f'modal-junyi-a3-refit-h100-20261115-{args.attempt:02}'
    if re.fullmatch(r'modal-junyi-a3-refit-(h100|l4|t4)-20261115-\d{2}', execution_id) is None:
        raise ValueError('Run A3 không hợp lệ')
    output = ROOT / 'experiments/akt/results' / execution_id
    guard = output / 'app-budget-guard.json'
    if args.recovery:
        output = output / 'recovery'
    receipt = json.loads((output / 'remote-inventory.json').read_text())
    assert json.loads((output / 'COMPLETE.json').read_text())['status'] == 'LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
    assert json.loads(guard.read_text())['stop_acknowledged']
    prefix = 'outputs/junyi-a3-refit-20261114-01/'
    candidates = []
    for name, pin in receipt['files'].items():
        match = re.fullmatch(prefix + r'checkpoints/refit-batch-epoch-(\d+)-step-(\d+)-[a-f0-9]+/state.pt', name)
        if match:
            candidates.append(((int(match[1]), int(match[2]), 0), name, pin))
        full = re.fullmatch(prefix + r'checkpoints/epoch-(\d{3})/state.pt', name)
        if full:
            candidates.append(((int(full[1]), 2040, 1), name, pin))
    position, name, pin = max(candidates)
    checkpoint = output / 'files' / name
    with checkpoint.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert digest == pin['sha256'] and checkpoint.stat().st_size == pin['bytes']
    identity = json.loads((checkpoint.parent / 'metadata.json').read_text())['identity']
    manifest = output / 'files' / prefix / 'run-manifest.json'
    if manifest.exists():
        assert json.loads(manifest.read_text()) == identity
    from knowledge_tracing.akt.checkpoint import load_training_snapshot
    import torch
    payload = load_training_snapshot(checkpoint, expected_identity=identity, device='cpu')
    full_epoch = position[2] == 1
    state = payload['progress'] if full_epoch else payload['resume_state']
    assert state['epoch'] == position[0]
    if full_epoch:
        assert state['complete'] is True
    else:
        assert state['optimizer_steps'] == position[1]
    for tensor in payload['model_state_dict'].values():
        assert torch.isfinite(tensor).all().item()
    optimizer_tensors = 0
    for values in payload['optimizer_state_dict']['state'].values():
        for tensor in values.values():
            if isinstance(tensor, torch.Tensor):
                assert torch.isfinite(tensor).all().item()
                optimizer_tensors += 1
    assert optimizer_tensors
    if not full_epoch:
        assert state['sampler_state'] and state['trainer_state']
    for key in ('python_rng', 'numpy_rng', 'torch_rng', 'cuda_rng'):
        assert key in payload
    assert payload['cuda_rng']
    history = state['history'] if full_epoch else state['trainer_state']['selection_state']['history']
    assert len(history) == position[0] - (0 if full_epoch else 1)
    assert all(row['valid_targets'] == 14947674 and row['optimizer_steps'] == 2040 for row in history)
    result = dict(status='PASS_A3_LOCAL_RECOVERY_CHECKPOINT',
        source_receipt=(output / 'remote-inventory.json').relative_to(ROOT).as_posix(),
        checkpoint=checkpoint.relative_to(ROOT).as_posix(), remote_checkpoint='experiments/akt/results/' + name[len('outputs/'):],
        checkpoint_sha256=digest, checkpoint_bytes=pin['bytes'], complete_epochs=len(history),
        partial_epoch=None if full_epoch else position[0],
        partial_optimizer_step=None if full_epoch else position[1], frozen_epochs=identity['epochs'],
        model_tensors_finite=True, optimizer_tensors_finite=True,
        sampler_and_rng_present=not full_epoch, rng_present=True, epoch_boundary_resume=full_epoch,
        limits_vi='Checkpoint đang học dở, chưa phải model refit9epoch. Kiểm bằng CPU, không xác nhận trước tính tương đương số học trên thiết bị GPU khác.')
    if re.fullmatch(r'(?:-[a-z0-9-]+)?',args.evidence_suffix) is None:
        raise ValueError('Hậu tố bằng chứng không hợp lệ')
    with (HERE / f'a3-checkpoint-verified{args.attempt:02}{args.evidence_suffix}.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
