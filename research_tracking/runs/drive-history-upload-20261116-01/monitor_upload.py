"""Đọc tiến độ đã lưu, chỉ xuất số liệu và tên file, giữ URI/token riêng."""
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
state = json.loads((ROOT / 'artifacts/akt/private/drive-upload/state.json').read_text(encoding='utf-8'))
plan = state['plan']
verified_bytes = 0
acknowledged_bytes = 0
verified_files = 0
current_file = None
for row in plan['files']:
    entry = state['files'].get(row['path'], {})
    if entry.get('complete'):
        verified_files += 1
        verified_bytes += row['bytes']
        acknowledged_bytes += row['bytes']
    else:
        acknowledged_bytes += entry.get('offset') or 0
        if entry:
            current_file = row['path']
progress = dict(at=datetime.now(timezone.utc).isoformat(), verified_files=verified_files,
                total_files=len(plan['files']), verified_bytes=verified_bytes,
                acknowledged_bytes=acknowledged_bytes, total_bytes=plan['bytes'],
                percent=round(acknowledged_bytes * 100 / plan['bytes'], 2), current_file=current_file)
with (HERE / 'PROGRESS.jsonl').open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(progress, ensure_ascii=False) + '\n')
print(json.dumps(progress, ensure_ascii=False))
