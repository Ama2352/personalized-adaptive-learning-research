"""Kiểm file A1 xuất trên CPU, không training hoặc cấp GPU."""
import hashlib
import json
from pathlib import Path
import zipfile

import torch

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / 'experiments/akt/results/model-export-a1-batch128-20261113-01'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    index = json.loads((OUTPUT / 'MODEL_INDEX.json').read_text(encoding='utf-8'))
    path = OUTPUT / index['checkpoint_file']
    assert len(list(OUTPUT.glob('*.pt'))) == 1
    assert sha(path) == index['checkpoint_sha256']
    payload = torch.load(path, map_location='cpu', weights_only=True)
    assert payload['identity'] == index['metadata']['identity']
    assert payload['progress']['epoch'] == 9 and payload['progress']['validation_complete'] is True
    weights = payload['model_state_dict']
    assert weights and payload['optimizer_state_dict']['state']
    for key in ('python_rng', 'numpy_rng', 'torch_rng', 'cuda_rng'):
        assert key in payload
    assert all(value.device.type == 'cpu' and torch.isfinite(value).all() for value in weights.values())
    assert weights['backbone.q_embed.weight'].shape == (718, 256)
    assert 'alpha' in weights and 'gate.weight' not in weights
    assert sha(OUTPUT / 'SUPPORT.zip') == index['support_sha256']
    with zipfile.ZipFile(OUTPUT / 'SUPPORT.zip') as saved:
        assert saved.testzip() is None
        for name, pin in index['support_inventory'].items():
            with saved.open(name) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == pin['sha256']
    source = ROOT / index['source_checkpoint']
    assert sha(source) == index['checkpoint_sha256']
    result = {'status': 'PASS_A1_EXPORT_CPU_LOAD_AND_INTEGRITY', 'all_outputs_on_d': True,
              'selected_epoch': 9, 'tensors': len(weights),
              'parameters': sum(value.numel() for value in weights.values()),
              'alpha': float(weights['alpha']), 'optimizer_and_rng_preserved': True,
              'checkpoint_bytes': path.stat().st_size, 'source_unchanged': True,
              'source_checkpoint_sha256': index['checkpoint_sha256'],
              'standalone_inference_tested': False,
              'output_inventory': {item.name: {'bytes': item.stat().st_size, 'sha256': sha(item)}
                                   for item in sorted(OUTPUT.iterdir()) if item.is_file()}}
    (HERE / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'selected_epoch', 'checkpoint_bytes', 'alpha')}))


if __name__ == '__main__':
    main()
