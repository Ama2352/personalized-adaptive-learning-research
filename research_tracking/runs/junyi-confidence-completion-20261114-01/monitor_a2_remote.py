"""Đọc tiến độ và telemetry A2 qua Volume, không gọi thêm function GPU."""
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
os.environ.update(MODAL_CONFIG_PATH=str(ROOT / 'artifacts/akt/private/modal.toml'), MODAL_PROFILE='kltn')
import modal

attempt = sys.argv[1] if len(sys.argv)>1 else '03'
assert attempt.isdigit() and len(attempt)==2
execution = 'modal-junyi-a2-staged-h100-20261114-' + attempt
output = ROOT / 'experiments/akt/results' / execution
dispatch = json.loads((output / 'dispatch.json').read_text())
volume = modal.Volume.from_name(dispatch['volume_name'], version=2)
operation = 'outputs/' + execution + '-operation/'
logical = 'outputs/junyi-a2-expert-selected-20261114-01/'


def read(name):
    try:
        return b''.join(volume.read_file(name)).decode('utf-8', errors='replace')
    except FileNotFoundError:
        return None


result = dict(observed_at_unix=time.time(), execution_id=execution)
for name in ('runtime.json', 'result.json', 'failure.log', 'controller-failure.log'):
    raw = read(operation + name)
    if raw is not None:
        result[name] = json.loads(raw) if name.endswith('.json') else raw[-4000:]
raw=read(operation+'checkpoint-index.json')
if raw:
    result['checkpoint_index']=json.loads(raw)
raw = read(operation + 'gpu-telemetry.jsonl')
if raw:
    samples = []
    for line in raw.splitlines():
        try:
            samples.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    if samples:
        tail = samples[-30:]
        result['gpu'] = dict(last=samples[-1], samples=len(samples),
            recent_mean_utilization=sum(row['gpu_utilization'] for row in tail)/len(tail),
            peak_vram_mib=max(row['vram_used_mib'] for row in samples))
entries = list(volume.iterdir(logical, recursive=False))
for entry in entries:
    name = entry.path.rsplit('/', 1)[-1]
    if name.endswith('-training.json') or name == 'selected-terminal.json' or name.startswith('partial-terminal-'):
        raw = read(logical + name)
        if raw:
            result[name] = json.loads(raw)
progress_names = sorted(entry.path for entry in entries if entry.path.endswith('-progress.jsonl'))
if progress_names:
    raw = read(progress_names[-1].lstrip('/'))
    if raw:
        lines = raw.splitlines()
        for line in reversed(lines):
            try:
                result['progress'] = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
raw = read(operation + 'worker.log')
if raw:
    result['worker_log_tail'] = raw[-2500:]
with (HERE / 'a2-remote-progress.jsonl').open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(result, ensure_ascii=False) + '\n')
summary=dict(execution_id=execution,gpu=result.get('gpu'),error=result.get('failure.log'))
event=result.get('progress',{})
summary.update(epoch=event.get('epoch'),steps=event.get('training',{}).get('optimizer_steps'),
    targets=event.get('training',{}).get('valid_targets'),
    train_seconds=event.get('training',{}).get('resource',{}).get('wall_seconds'))
summary['completed_training']={name:dict(complete=value.get('complete'),targets=value.get('valid_targets'),
    seconds=value.get('resource',{}).get('wall_seconds')) for name,value in result.items()
    if name.endswith('-training.json')}
summary['durable_checkpoint_count']=sum(name.endswith('/state.pt')
    for name in result.get('checkpoint_index',{}).get('files',{}))
if 'result.json' in result:
    summary['result']=result['result.json']
print(json.dumps(summary, ensure_ascii=False))
