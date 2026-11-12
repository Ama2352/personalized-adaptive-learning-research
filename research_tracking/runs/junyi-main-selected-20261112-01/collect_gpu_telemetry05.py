"""Đọc telemetry container hiện hành bằng stdlib, không nạp model/Torch."""
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

RUN = sys.argv[1]
assert RUN == 'modal-junyi-main-selected-t4-20261112-05'
OUTPUT = Path('/opt/kltn/experiments/akt/results/modal-junyi-main-selected-t4-20261112-01')
FIELDS = ('timestamp', 'name', 'utilization.gpu', 'utilization.memory',
          'memory.used', 'memory.total', 'power.draw', 'power.limit',
          'clocks.sm', 'clocks.mem', 'pstate', 'temperature.gpu', 'clocks.max.sm')


def read_optional(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def worker_stats():
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit() or int(directory.name) == os.getpid():
            continue
        try:
            arguments = (directory / 'cmdline').read_bytes().split(b'\0')
            if b'/opt/junyi-numerical-worker.py' not in arguments:
                continue
            raw = (directory / 'stat').read_text()
            values = raw[raw.rfind(')') + 2:].split()
            return dict(pid=int(directory.name),
                        cpu_seconds=(int(values[11]) + int(values[12])) / os.sysconf('SC_CLK_TCK'),
                        rss_bytes=int(values[21]) * os.sysconf('SC_PAGE_SIZE'))
        except (OSError, ValueError, IndexError):
            continue
    return None


def latest_progress():
    files = list(OUTPUT.glob('epoch-*-progress.jsonl'))
    if not files:
        return None
    path = max(files, key=lambda candidate: candidate.stat().st_mtime)
    with path.open('rb') as stream:
        size = path.stat().st_size
        stream.seek(max(0, size - 32768))
        lines = stream.read().splitlines()
    for line in reversed(lines):
        try:
            value = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue
        training = value['training']
        return dict(file=path.name, epoch=value['epoch'],
                    complete_epoch=value['complete_epoch'],
                    optimizer_steps=training['optimizer_steps'],
                    valid_targets=training['valid_targets'],
                    epoch_wall_seconds=training['resource']['wall_seconds'],
                    valid_tokens=training.get('valid_tokens'),
                    padding_tokens=training.get('padding_tokens'))
    return dict(file=path.name, progress_pending=True)


started = time.monotonic()
print(json.dumps(dict(kind='telemetry_header', run=RUN, samples_requested=30,
    interval_seconds=2, cpu_max=read_optional('/sys/fs/cgroup/cpu.max'),
    memory_max=read_optional('/sys/fs/cgroup/memory.max'),
    model_or_torch_imported=False)), flush=True)
previous_worker = None
previous_time = None
completed = 0
for index in range(30):
    if time.monotonic() - started > 75:
        break
    sample_time = time.monotonic()
    result = subprocess.run(['nvidia-smi', '--query-gpu=' + ','.join(FIELDS),
                             '--format=csv,noheader,nounits'],
                            capture_output=True, text=True, check=True, timeout=4)
    values = next(csv.reader(result.stdout.splitlines()))
    gpu = dict(zip(FIELDS, (value.strip() for value in values)))
    worker = worker_stats()
    cpu_cores = None
    if worker and previous_worker and worker['pid'] == previous_worker['pid']:
        cpu_cores = (worker['cpu_seconds'] - previous_worker['cpu_seconds']) / (sample_time - previous_time)
    print(json.dumps(dict(kind='telemetry_sample', index=index,
        observed_at_utc=datetime.now(timezone.utc).isoformat(),
        elapsed_seconds=sample_time - started, gpu=gpu, worker=worker,
        worker_cpu_core_equivalents=cpu_cores,
        cgroup_memory_current=read_optional('/sys/fs/cgroup/memory.current'),
        progress=latest_progress())), flush=True)
    completed += 1
    previous_worker, previous_time = worker, sample_time
    if index < 29:
        time.sleep(max(0, 2 - (time.monotonic() - sample_time)))
print(json.dumps(dict(kind='telemetry_end', completed_samples=completed,
    elapsed_seconds=time.monotonic() - started)), flush=True)
