"""Kiểm model refit đã xuất trên D bằng manifest, không tải tensor vào RAM."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
COMMON_KEYS = (
    'phase', 'plan_sha256', 'inputs', 'encoding', 'window_identity',
    'gate_sha256', 'epochs', 'profile', 'confidence_policy',
    'initial_backbone_sha256',
)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    models = {}
    reference = None
    for variant in ('a0', 'a1', 'a2', 'a3'):
        export = ROOT / f'experiments/akt/results/model-export-{variant}-refit-20261114-01'
        if not (export / 'MODEL_INDEX.json').exists():
            continue
        index = read(export / 'MODEL_INDEX.json')
        checkpoint = export / index['checkpoint_file']
        assert index['phase'] == 'refit90' and index['epochs'] == 9
        assert index['identity']['variant'] == variant.upper()
        assert checkpoint.stat().st_size == index['checkpoint_bytes']
        assert sha(checkpoint) == index['checkpoint_sha256']
        assert sha(export / 'SUPPORT.zip') == index['support_sha256']
        assert not index['calibration_completed']
        assert not index['independent_evaluation_completed']
        common = {key: index['identity'][key] for key in COMMON_KEYS}
        if reference is None:
            reference = common
        assert common == reference, 'Các model khác hợp đồng refit chung'
        complete_path = ROOT / index['source_output'] / 'COMPLETE.json'
        complete = read(complete_path)
        history = complete['history']
        assert len(history) == 9
        assert [row['epoch'] for row in history] == list(range(1, 10))
        assert all(row['valid_targets'] == 14947674 for row in history)
        assert all(row['optimizer_steps'] == 2040 for row in history)
        seconds = [row['resource']['wall_seconds'] for row in history]
        models[variant] = {
            'checkpoint_sha256': index['checkpoint_sha256'],
            'complete_sha256': sha(complete_path),
            'export': export.relative_to(ROOT).as_posix(),
            'epochs': 9,
            'total_optimizer_steps': 18360,
            'total_target_uses': 134529066,
            'epoch_seconds': seconds,
            'mean_epoch_seconds': sum(seconds) / len(seconds),
        }
    assert models, 'Chưa có model refit để kiểm'
    evidence = {
        'status': 'PASS_EXISTING_REFIT_EXPORTS',
        'models': models,
        'shared_identity': reference,
        'missing_exports': [v for v in ('a0', 'a1', 'a2', 'a3') if v not in models],
        'limits_vi': 'Kiểm file, số target/step và identity. Chưa hiệu chỉnh hay đánh giá độc lập; không suy ra hiệu quả đồ thị từ việc refit thành công.',
    }
    output = HERE / ('exports-verified-' + '-'.join(models) + '.json')
    if output.exists():
        assert read(output) == evidence, 'Bằng chứng cũ thay đổi'
    else:
        with output.open('x', encoding='utf-8') as stream:
            json.dump(evidence, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps({'status': evidence['status'], 'models': list(models), 'evidence': output.name}))


if __name__ == '__main__':
    main()
