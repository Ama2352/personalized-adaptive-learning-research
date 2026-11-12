"""Tổng hợp đoạn đo training ổn định, giữ riêng đoạn chuyển pha của04."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

BUNDLE = Path(__file__).resolve().parent


def read_records(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()
            if line.startswith('{')]


def describe(values):
    return dict(min=min(values), mean=statistics.mean(values),
                median=statistics.median(values), max=max(values))


raw = BUNDLE / 'gpu-telemetry06.log'
records = read_records(raw)
samples = [row for row in records if row['kind'] == 'telemetry_sample']
end = next(row for row in records if row['kind'] == 'telemetry_end')
assert len(samples) == end['completed_samples'] == 30
assert all(row['worker'] is not None and row['progress']['epoch'] == 5
           and row['progress']['complete_epoch'] is False for row in samples)
assert len({row['worker']['pid'] for row in samples}) == 1
assert len({row['progress']['file'] for row in samples}) == 1
first, last = samples[0]['progress'], samples[-1]['progress']
steps = last['optimizer_steps'] - first['optimizer_steps']
targets = last['valid_targets'] - first['valid_targets']
progress_seconds = last['epoch_wall_seconds'] - first['epoch_wall_seconds']
assert steps > 0 and targets > 0 and progress_seconds > 0
assert first['optimizer_steps'] > 39488
gpu = {key: describe([float(row['gpu'][key]) for row in samples])
       for key in ('utilization.gpu', 'utilization.memory', 'memory.used', 'memory.total',
                   'power.draw', 'power.limit', 'clocks.sm', 'clocks.max.sm', 'temperature.gpu')}
cores = [row['worker_cpu_core_equivalents'] for row in samples
         if row['worker_cpu_core_equivalents'] is not None]
assert len(cores) == 29 and all(value >= 0 for value in cores)
valid = last['valid_tokens'] - first['valid_tokens']
padding = last['padding_tokens'] - first['padding_tokens']
assert valid > 0 and padding >= 0
tail = [row for row in read_records(BUNDLE / 'gpu-telemetry04.log')
        if row['kind'] == 'telemetry_sample']
summary = dict(status='VERIFIED_STABLE_TRAINING_TELEMETRY', run='execution06',
    source_raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
    samples=len(samples), elapsed_seconds=end['elapsed_seconds'],
    start_utc=samples[0]['observed_at_utc'], end_utc=samples[-1]['observed_at_utc'],
    model_batch_size=4, epoch=5, same_worker_and_phase=True,
    gpu=gpu, cpu_core_equivalents=describe(cores),
    worker_rss_bytes=describe([row['worker']['rss_bytes'] for row in samples]),
    progress_delta=dict(optimizer_steps=steps, scored_targets=targets,
        seconds=progress_seconds, targets_per_second=targets / progress_seconds,
        valid_tokens=valid, padding_tokens=padding,
        padded_token_fraction=padding / (valid + padding)),
    vram_used_fraction=gpu['memory.used']['mean'] / gpu['memory.total']['mean'],
    device_states=sorted({row['gpu']['pstate'] for row in samples}),
    previous_tail04=dict(samples=len(tail), worker_present=sum(row['worker'] is not None for row in tail),
        worker_absent=sum(row['worker'] is None for row in tail),
        interpretation_vi='Chuyển từ cuối training sang đóng gói, không dùng làm trung bình training ổn định.'),
    interpretation_vi='Cấu hình hiện hành còn thời gian GPU không chạy kernel và còn dư VRAM. '
                      'Chưa nhận dạng bottleneck hoặc chứng minh tối ưu toàn bộ training.',
    limitations_vi=['Một khoảng gần60giây, không đại diện mọi epoch hoặc validation.',
                    'GPU-Util đo thời gian có kernel, không phải phần trăm FLOPS/SM occupancy.',
                    'Không đọc được cgroup quota, CPU/RAM là số đo process.',
                    'Thông lượng dựa hai mốc progress trong cùng epoch, chưa đo time-to-quality.'],
    metric_definition_source='https://nvidia.custhelp.com/app/answers/detail/a_id/3751/~/useful-nvidia-smi-queries')
with (BUNDLE / 'gpu-telemetry06-summary.json').open('x', encoding='utf-8') as stream:
    json.dump(summary, stream, ensure_ascii=False, indent=2)
with (BUNDLE / 'gpu-telemetry06-data.csv').open('x', newline='', encoding='utf-8') as stream:
    writer = csv.writer(stream)
    writer.writerow(['index', 'utc', 'gpu_util_percent', 'vram_mib', 'power_w',
                     'cpu_core_equivalents', 'worker_rss_bytes', 'optimizer_steps', 'targets'])
    for row in samples:
        writer.writerow([row['index'], row['observed_at_utc'], row['gpu']['utilization.gpu'],
                         row['gpu']['memory.used'], row['gpu']['power.draw'],
                         row['worker_cpu_core_equivalents'], row['worker']['rss_bytes'],
                         row['progress']['optimizer_steps'], row['progress']['valid_targets']])
print(json.dumps(dict(status=summary['status'], gpu_mean=gpu['utilization.gpu']['mean'],
    vram_fraction=summary['vram_used_fraction'], cpu_cores=summary['cpu_core_equivalents']['mean'],
    rss_gib=summary['worker_rss_bytes']['mean'] / 1024**3,
    targets_per_second=summary['progress_delta']['targets_per_second']), ensure_ascii=False))
