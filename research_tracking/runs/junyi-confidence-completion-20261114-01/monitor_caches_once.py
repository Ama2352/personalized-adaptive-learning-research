"""Theo dõi marker cache CPU, giữ file partial khi chưa công bố hoàn tất."""
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CACHE = ROOT/'artifacts/akt/graph-context-cache/full-train80-staged-20261114-01'
receipts = []
for path in sorted(CACHE.glob('*.receipt.json')):
    value = json.loads(path.read_text())
    receipts.append(dict(name=path.name, status=value['status'], windows=value['windows'],
        targets=value['targets'], bytes=value['bytes'], seconds=value['wall_seconds'],
        sha256=value['cache_sha256'], peak_rss_mib=value['peak_rss_bytes']/1024**2))
partial = [dict(name=path.name, bytes=path.stat().st_size) for path in CACHE.glob('*.partial')]
snapshot = dict(observed_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat(),
                completed_caches=len(receipts), expected_caches=4, receipts=receipts, partial=partial)
state = json.loads((HERE/'STATE.json').read_text())
state['cache_progress'] = snapshot
(HERE/'STATE.json').write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
with (HERE/'cache-progress.jsonl').open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(snapshot)+'\n')
print(json.dumps(snapshot))
