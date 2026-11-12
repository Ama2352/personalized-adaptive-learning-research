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
assert RUN == 'modal-junyi-batch-utilization-t4-20261112-01'
OUTPUT = Path('/opt/kltn/experiments/akt/results') / (RUN+'-operation')
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
    try:
        value = json.loads((OUTPUT/'progress.json').read_text())
        return dict(packet_passes=len(value['passes']),optimizer_steps=value['total_steps'],
                    valid_targets=value['total_targets'],latest=value['passes'][-1])
    except (OSError, ValueError):
        return None


wait_started=time.monotonic()
while time.monotonic()-wait_started<110:
    progress=latest_progress()
    if progress and progress['packet_passes']>=2:
        break
    time.sleep(1)
else:
    raise TimeoutError('No stable batch32 training observed')

started = time.monotonic()
print(json.dumps(dict(kind='telemetry_header', run=RUN, samples_requested=12,
    interval_seconds=1, cpu_max=read_optional('/sys/fs/cgroup/cpu.max'),
    memory_max=read_optional('/sys/fs/cgroup/memory.max'),
    model_or_torch_imported=False)), flush=True)
previous_worker = None
previous_time = None
completed = 0
for index in range(12):
    if time.monotonic() - started > 30:
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
    if index < 11:
        time.sleep(max(0, 1 - (time.monotonic() - sample_time)))
print(json.dumps(dict(kind='telemetry_end', completed_samples=completed,
    elapsed_seconds=time.monotonic() - started)), flush=True)
