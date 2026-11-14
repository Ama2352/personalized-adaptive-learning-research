"""Xuất gọn checkpoint refit đã hoàn tất trên D, kiểm SHA trước/sau sao chép."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments/akt')]


def verify_completed(output, variant, plan):
    from knowledge_tracing.akt.checkpoint import load_training_snapshot
    from knowledge_tracing.akt.research_junyi_engineering import file_sha
    identity = json.loads((output / 'run-manifest.json').read_text())
    complete = json.loads((output / 'COMPLETE.json').read_text())
    epochs = plan['candidates'][variant]['epochs']
    checkpoint = output / 'checkpoints' / f'epoch-{epochs:03}' / 'state.pt'
    metadata = json.loads((checkpoint.parent / 'metadata.json').read_text())
    marker = json.loads((checkpoint.parent / 'COMPLETE.json').read_text())
    if (identity['phase'] != 'junyi_refit90' or identity['variant'] != variant
            or identity['plan_sha256'] != plan['identity']
            or complete['status'] != 'JUNYI_REFIT90_COMPLETE'
            or complete['complete_epochs'] != epochs or complete['frozen_epochs'] != epochs
            or complete['checkpoint'] != checkpoint.relative_to(output).as_posix()
            or complete['checkpoint_sha256'] != file_sha(checkpoint)
            or metadata['checkpoint_sha256'] != complete['checkpoint_sha256']
            or metadata['checkpoint_bytes'] != checkpoint.stat().st_size or metadata['identity'] != identity
            or marker['checkpoint_sha256'] != complete['checkpoint_sha256']
            or marker['metadata_sha256'] != file_sha(checkpoint.parent / 'metadata.json')):
        raise ValueError('Refit completion or checkpoint integrity differs')
    payload = load_training_snapshot(checkpoint, expected_identity=identity, device='cpu')
    history = payload['progress']['history']
    if (payload['progress'].get('role') != 'junyi_refit90' or payload['progress']['epoch'] != epochs
            or history != complete['history'] or len(history) != epochs
            or [row['epoch'] for row in history] != list(range(1, epochs + 1))
            or not {'model_state_dict', 'optimizer_state_dict', 'encoding', 'python_rng',
                    'numpy_rng', 'torch_rng', 'cuda_rng'} <= payload.keys()):
        raise ValueError('Final refit checkpoint lifecycle incomplete')
    import torch
    if not payload['model_state_dict'] or any(not torch.isfinite(value).all().item()
                                             for value in payload['model_state_dict'].values()):
        raise ValueError('Refit model contains nonfinite tensors')
    return checkpoint, identity, complete


def export(request, destination):
    from run_junyi_refit import pinned
    from junyi_staged_io import sha, write_new
    plan = json.loads(pinned(request['epoch_plan']).read_text())
    config = json.loads(pinned(request['config']).read_text())
    variant = request['variant']
    output = (ROOT / config['output_dir']).resolve()
    destination = destination.resolve()
    base = ROOT / 'experiments/akt/results'
    if (output.parent != base or output.name != config['run_id'] or destination.parent != base
            or destination.exists() or destination == output):
        raise ValueError('New owned compact export under experiments/akt/results required')
    checkpoint, identity, complete = verify_completed(output, variant, plan)
    support = {'run-manifest.json': output / 'run-manifest.json', 'COMPLETE.json': output / 'COMPLETE.json',
               'metadata.json': checkpoint.parent / 'metadata.json'}
    for name in ('config', 'cuda_profile', 'epoch_plan', 'selected_index', 'lock_file', 'graph', 'confidence'):
        if name in request:
            support['inputs/' + name + pinned(request[name]).suffix] = pinned(request[name])
    for name in ('roles', 'encoding90', 'encoding90_receipt', 'encoding80', 'encoding80_receipt'):
        support['inputs/' + name + '.json'] = pinned(request['inputs'][name])
    inventory = {name: dict(sha256=sha(path), bytes=path.stat().st_size) for name, path in support.items()}
    source_sha = sha(checkpoint)
    destination.mkdir()
    model = destination / (variant + '_JUNYI_REFIT.pt')
    with checkpoint.open('rb') as source, model.open('xb') as target:
        shutil.copyfileobj(source, target, 1024 * 1024)
    if sha(model) != source_sha:
        raise ValueError('Refit checkpoint changed during export')
    with zipfile.ZipFile(destination / 'SUPPORT.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, path in support.items():
            raw = path.read_bytes()
            import hashlib
            if hashlib.sha256(raw).hexdigest() != inventory[name]['sha256']:
                raise ValueError('Support input changed during export')
            archive.writestr(name, raw)
        archive.writestr('INVENTORY.json', json.dumps(inventory, indent=2))
    with zipfile.ZipFile(destination / 'SUPPORT.zip') as archive:
        import hashlib
        if any(hashlib.sha256(archive.read(name)).hexdigest() != pin['sha256']
               for name, pin in inventory.items()):
            raise ValueError('Support archive integrity mismatch')
    index = dict(model=variant + '_JUNYI_REFIT', phase='refit90', checkpoint_file=model.name,
        checkpoint_sha256=source_sha, checkpoint_bytes=model.stat().st_size, epochs=complete['frozen_epochs'],
        identity=identity, support_sha256=sha(destination / 'SUPPORT.zip'),
        calibration_completed=False, independent_evaluation_completed=False,
        source_output=output.relative_to(ROOT).as_posix())
    write_new(destination / 'MODEL_INDEX.json', index)
    (destination / 'README.md').write_text('# Model refit ' + variant + '\n\n'
        'Checkpoint neural TRAIN90, khởi tạo mới, epoch cố định theo selected-fit. '
        'SUPPORT.zip giữ cấu hình, encoding, split và graph/confidence để nạp lại. '
        'Chưa calibration hoặc đánh giá độc lập. Không dùng trực tiếp model Junyi trong Grade10.\n', encoding='utf-8')
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export(json.loads(args.request.read_text(encoding='utf-8')), args.output)))


if __name__ == '__main__':
    main()
