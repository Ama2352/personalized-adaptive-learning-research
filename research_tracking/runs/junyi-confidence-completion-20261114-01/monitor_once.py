"""Ghi tiến độ thật từ marker child, giữ bằng chứng lớn trong output trên D."""
import json
from pathlib import Path
import time
import psutil

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT/'artifacts/akt/confidence/full-train80-20261114-02'

state = json.loads((HERE/'STATE.json').read_text())
complete = list((OUTPUT/'children').glob('*/COMPLETE.json'))
snapshot = dict(observed_at_unix=time.time(), completed_children=len(complete), total_children=736)
journals = sorted(OUTPUT.glob('batch-stages-*.jsonl'), key=lambda path:path.stat().st_mtime_ns)
journals = [path for path in journals if '.telemetry.' not in path.name]
if journals:
    lines = journals[-1].read_text().splitlines()
    if lines:
        snapshot['current_child'] = json.loads(lines[-1])['child']
    telemetry = journals[-1].with_suffix('.telemetry.jsonl')
    if telemetry.exists():
        rows = telemetry.read_text().splitlines()
        if rows:
            last = json.loads(rows[-1])
            snapshot.update(worker_elapsed_seconds=last['seconds'], rss_mib=last['rss']/1024**2,
                            available_ram_mib=last['available_ram']/1024**2)
state.update(snapshot)
active = []
for process in psutil.process_iter(['pid', 'name']):
    if 'python' not in (process.info['name'] or '').lower():
        continue
    try:
        command = process.cmdline()
        if (not any(Path(value).name == 'fit_junyi_confidence_batch.py' for value in command)
                or '--output' not in command):
            continue
        if Path(command[command.index('--output')+1]).resolve() != OUTPUT:
            continue
        active.append(dict(pid=process.pid, created_at_unix=process.create_time(),
                           worker='--worker' in command))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue
state['active_processes'] = active
(HERE/'STATE.json').write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n')
with (HERE/'progress.jsonl').open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(snapshot)+'\n')
print(json.dumps(snapshot))
