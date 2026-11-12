"""Đọc lại selected checkpoints từ Volume, hash streaming và đối chiếu chỉ mục."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
import modal

index = json.loads((BUNDLE / 'checkpoint-index.json').read_text(encoding='utf-8'))
records = []
for entry in index['entries']:
    selected = entry['selected_checkpoint']
    volume = modal.Volume.from_name(selected['volume_name'])
    files = []
    for name, expected, cap in (
        ('state.pt', selected['state_sha256'], 64*1024**2),
        ('metadata.json', selected['metadata_sha256'], 1024**2),
        ('COMPLETE.json', selected['complete_sha256'], 1024**2),
    ):
        digest, size = hashlib.sha256(), 0
        for block in volume.read_file(selected['volume_directory'] + '/' + name):
            size += len(block)
            assert size <= cap
            digest.update(block)
        assert digest.hexdigest() == expected
        files.append(dict(name=name, bytes=size, sha256=digest.hexdigest()))
    records.append(dict(candidate_id=entry['candidate_id'], selected_epoch=entry['selected_epoch'],
                        volume_name=selected['volume_name'], files=files))
    print(entry['candidate_id'], 'selected checkpoint durable PASS', flush=True)
with (BUNDLE / 'selected-durable-verification.json').open('x', encoding='utf-8') as stream:
    json.dump(dict(status='ALL_SEVEN_SELECTED_CHECKPOINTS_REREAD_VERIFIED',
                   checkpoint_count=len(records), gpu_allocated=False, records=records), stream, indent=2)
    stream.write('\n')
