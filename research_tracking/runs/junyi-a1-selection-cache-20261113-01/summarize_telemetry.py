"""Tổng hợp mẫu nvidia-smi theo cả phiên, tách khỏi trung bình cửa sổ đang train."""
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    records = []
    for attempt in ('07', '09'):
        run = 'modal-junyi-a1-b128-h100-20261113-' + attempt
        path = ROOT / 'experiments/akt/results' / (run + '-operation') / 'gpu-telemetry.jsonl'
        raw = path.read_bytes()
        rows = [json.loads(line) for line in raw.splitlines()]
        assert len(rows) > 1
        assert all(b['at_monotonic'] > a['at_monotonic'] for a, b in zip(rows, rows[1:]))
        intervals = [b['at_monotonic'] - a['at_monotonic'] for a, b in zip(rows, rows[1:])]
        duration = sum(intervals)
        weighted = sum(row['gpu_utilization'] * dt for row, dt in zip(rows, intervals)) / duration
        records.append({'run_id': run, 'source': path.relative_to(ROOT).as_posix(),
                        'source_sha256': hashlib.sha256(raw).hexdigest(), 'samples': len(rows),
                        'observed_seconds': duration,
                        'gpu_util_sample_mean_percent': statistics.mean(row['gpu_utilization'] for row in rows),
                        'gpu_util_time_weighted_percent': weighted,
                        'zero_util_samples': sum(row['gpu_utilization'] == 0 for row in rows),
                        'over_50_percent_samples': sum(row['gpu_utilization'] > 50 for row in rows),
                        'peak_vram_used_mib': max(row['vram_used_mib'] for row in rows),
                        'vram_total_mib': rows[0]['vram_total_mib'],
                        'mean_power_w': statistics.mean(row['power_w'] for row in rows)})
    result = {'status': 'VERIFIED_TELEMETRY_SUMMARY', 'runs': records,
              'note_vi': 'Trung bình toàn khoảng có lấy mẫu, gồm admission/train/validation/export; '
                         'không bao mọi giây startup/packaging. GPU-Util là chỉ số nvidia-smi, '
                         'chưa đo riêng tỷ trọng chờ CPU hay hiệu suất phần cứng.'}
    (HERE / 'telemetry-summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
