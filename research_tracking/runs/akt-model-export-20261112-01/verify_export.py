"""Kiểm SHA và schema checkpoint xuất trên CPU, không chạy training."""
import gc
import hashlib
import json
from pathlib import Path
import zipfile

import torch

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
OUTPUT = ROOT/'experiments/akt/results/model-export-20261112-01'
index = json.loads((OUTPUT/'MODEL_INDEX.json').read_text(encoding='utf-8'))
assert len(index['entries']) == 8
assert len(list(OUTPUT.rglob('*.pt'))) == 8
rows = []
for entry in index['entries']:
    path = (OUTPUT/entry['destination']).resolve()
    assert path.drive.upper() == 'D:' and path.is_relative_to(OUTPUT.resolve())
    with path.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256']
    payload = torch.load(path, map_location='cpu', weights_only=True)
    assert payload['identity'] == entry['checkpoint_metadata']['identity']
    weights = payload['model_state_dict']
    assert weights and payload['optimizer_state_dict']['state']
    assert all(value.device.type == 'cpu' and torch.isfinite(value).all() for value in weights.values())
    prefix = 'backbone.' if entry['dataset'] == 'Grade10' else ''
    assert weights[prefix+'q_embed.weight'].shape[0] == len(entry['vocabulary']['values'])+1
    assert weights[prefix+'q_embed.weight'].shape[1] == entry['architecture']['d_model'] == 256
    assert ('gate.weight' in weights) == entry['model'].startswith('A3')
    rows.append(dict(model=entry['model'], dataset=entry['dataset'], vocabulary=len(entry['vocabulary']['values']),
                     tensors=len(weights), parameters=sum(value.numel() for value in weights.values()),
                     torch_weights_only_load=True, hash_verified=True, device='cpu'))
    del payload, weights
    gc.collect()
with (OUTPUT/'SUPPORT.zip').open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == index['support_sha256']
with zipfile.ZipFile(OUTPUT/'SUPPORT.zip') as support:
    assert support.testzip() is None
    assert {'grade10_source.zip', 'junyi_source.zip', 'runtime.lock.txt', 'grade10_item_bank.json'} <= set(support.namelist())
result = dict(status='PASS_EIGHT_EXPORTS_CPU_LOAD_AND_INTEGRITY', models=rows,
              all_outputs_on_D=True, H100_started=False,
              standalone_inference_tested=False,
              limits='Kiểm schema, trọng số hữu hạn và vocabulary. Inference đầy đủ sử dụng source/pipeline gốc.')
(BUNDLE/'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(status=result['status'], models=len(rows), all_outputs_on_D=True)), flush=True)
