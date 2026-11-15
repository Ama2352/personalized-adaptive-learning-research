"""Nghiệm thu A3 cuối, chép output theo inventory rồi xuất model gọn trên D."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / 'scripts/akt'), str(ROOT / 'src')]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_new(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    import torch
    from export_junyi_refit_model import export, verify_completed
    from knowledge_tracing.akt.checkpoint import load_training_snapshot

    operation = ROOT / 'experiments/akt/results/modal-junyi-a3-refit-h100-ws2016-20261115-02'
    receipt = read(operation / 'remote-inventory.json')
    assert read(operation / 'app-budget-guard.json')['stop_acknowledged'] is True
    assert read(operation / 'COMPLETE.json')['status'] == 'LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
    assert receipt['status'] == 'JUNYI_REFIT90_COMPLETE'
    logical = 'junyi-a3-refit-20261114-01'
    prefix = 'outputs/' + logical + '/'
    inventory = {name[len(prefix):]: pin for name, pin in receipt['files'].items()
                 if name.startswith(prefix)}
    assert inventory and 'COMPLETE.json' in inventory and 'run-manifest.json' in inventory
    source = operation / 'files/outputs' / logical
    destination = ROOT / 'experiments/akt/results' / logical
    for name, pin in inventory.items():
        path = source / name
        assert path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256']
    inventory_path = HERE / 'a3-final-copy-inventory01.json'
    evidence = dict(source=source.relative_to(ROOT).as_posix(),
                    destination=destination.relative_to(ROOT).as_posix(), files=inventory)
    if inventory_path.exists():
        assert read(inventory_path) == evidence
    else:
        write_new(inventory_path, evidence)
    for name, pin in inventory.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.stat().st_size == pin['bytes'] and sha(target) == pin['sha256']
        else:
            with (source / name).open('rb') as incoming, target.open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing, 1024 * 1024)
        assert target.stat().st_size == pin['bytes'] and sha(target) == pin['sha256']
    plan = read(HERE / 'epoch-plan.json')
    checkpoint, identity, complete = verify_completed(destination, 'A3', plan)
    payload = load_training_snapshot(checkpoint, expected_identity=identity, device='cpu')
    history = payload['progress']['history']
    assert len(history) == 9 and all(row['valid_targets'] == 14947674
                                    and row['optimizer_steps'] == 2040 for row in history)

    def finite(value):
        if isinstance(value, torch.Tensor):
            return bool(torch.isfinite(value).all())
        if isinstance(value, dict):
            return all(finite(item) for item in value.values())
        if isinstance(value, (tuple, list)):
            return all(finite(item) for item in value)
        return True

    assert payload['optimizer_state_dict']['state'] and finite(payload['optimizer_state_dict'])
    assert all(key in payload for key in ('python_rng', 'numpy_rng', 'torch_rng', 'cuda_rng'))
    compact = ROOT / 'experiments/akt/results/model-export-a3-refit-20261114-01'
    if compact.exists():
        index = read(compact / 'MODEL_INDEX.json')
        assert index['checkpoint_sha256'] == sha(checkpoint)
    else:
        index = export(read(HERE / 'refit-request-a3.json'), compact)
    proof = dict(status='PASS_A3_REFIT90_FINAL', operation=operation.relative_to(ROOT).as_posix(),
                 inventory=inventory_path.name, files=len(inventory), checkpoint_sha256=sha(checkpoint),
                 model_export=compact.relative_to(ROOT).as_posix(), epochs=9,
                 targets_per_epoch=14947674, steps_per_epoch=2040,
                 total_target_uses=134529066, total_optimizer_steps=18360,
                 model_optimizer_finite=True, rng_present=True, stop_acknowledged=True,
                 limits_vi='Chuỗi nối H100/L4/T4/H100. Chưa chứng minh bitwise-equivalence xuyên GPU. '
                           'Chưa hiệu chỉnh hoặc đánh giá độc lập. Checkpoint giữa các epoch lịch sử '
                           'trên Drive có file không còn trong bundle023, history và checkpoint cuối đã kiểm.')
    proof_path = HERE / 'a3-final-acceptance01.json'
    if proof_path.exists():
        assert read(proof_path) == proof
    else:
        write_new(proof_path, proof)
    print(json.dumps(proof, ensure_ascii=False))


if __name__ == '__main__':
    main()
