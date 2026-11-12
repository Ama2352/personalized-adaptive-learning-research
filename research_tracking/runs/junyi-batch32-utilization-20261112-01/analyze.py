"""Đối chiếu artifact, tổng hợp usage và xuất dữ liệu hình."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
NATIVE = ROOT/'experiments/akt/results/modal-junyi-batch-utilization-t4-20261112-01'
receipt = json.loads((NATIVE/'receipt.json').read_text())
assert receipt['status'] == 'JUNYI_BATCH_UTILIZATION_COMPLETE'
assert receipt['download_inventory_verified'] is True
assert json.loads((NATIVE/'app-budget-guard.json').read_text())['stop_acknowledged'] is True
with (NATIVE/'artifacts.zip').open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == receipt['archive_sha256']
with zipfile.ZipFile(NATIVE/'artifacts.zip') as archive:
    assert archive.testzip() is None
    inventory = json.loads(archive.read('SHA256.json'))
    assert set(archive.namelist()) == set(inventory) | {'SHA256.json'}
    for name, entry in inventory.items():
        with archive.open(name) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256']
    name = next(name for name in inventory if name.endswith('/gpu-telemetry.jsonl'))
    raw = archive.read(name)
    (BUNDLE/'gpu-telemetry.jsonl').write_bytes(raw)
    name = next(name for name in inventory if name.endswith('/resume-verification.json'))
    resume = json.loads(archive.read(name))
    assert resume['status'] == 'PASS_EXACT_NEXT_UPDATE'
    (BUNDLE/'resume-verification.json').write_text(json.dumps(resume, indent=2)+'\n')
result = receipt['worker_result']
assert result['actual_completed_optimizer_steps'] == 770
assert result['trained_target_exposures'] == 24*56332
assert result['total_target_exposures_including_resume_check'] <= 1358368
assert result['checkpoint_reload_and_next_update_exact'] is True
passes = result['passes']
assert len(passes) == 24 and all(row['scored_targets'] == 56332 and row['optimizer_steps'] == 32
                               for row in passes)
stable_passes = passes[1:]
samples = [json.loads(line) for line in raw.splitlines()]
stable = [row for row in samples if row['phase']['name'] == 'stable_training']
assert len(stable) >= 30
metrics = {}
for key in ('gpu_utilization', 'vram_used_mib', 'vram_total_mib', 'power_w', 'sm_clock_mhz'):
    values = [row[key] for row in stable]
    metrics[key] = dict(mean=statistics.mean(values), minimum=min(values), maximum=max(values))
elapsed = stable[-1]['at_monotonic']-stable[0]['at_monotonic']
assert elapsed >= 30
summary = dict(status='VERIFIED_BATCH32_RESOURCE_TEST', gpu='T4', batch_size=32,
               gpu_goal_above50_percent=metrics['gpu_utilization']['mean'] > 50,
               metrics=metrics, stable_sample_count=len(stable), sampled_seconds=elapsed,
               stable_targets_per_second=sum(row['scored_targets'] for row in stable_passes)
                   /sum(row['seconds'] for row in stable_passes),
               cuda_resource=result['cuda_resource'], checkpoint_reload_and_resume_exact=True,
               actual_optimizer_steps=770, training_packet_passes=24,
               unique_packet_targets=56332, target_exposures=24*56332,
               total_remote_seconds=receipt['total_remote_seconds'],
               main_training_protocol_changed=False, independent_quality_evaluation=False,
               cpu_ram_sample_status='Observer reached container after task completed, no usable process samples',
               limits_vi='Lặp packet TRAIN80 để đo tải GPU. Chưa đo cả epoch hoặc chất lượng selection. '
                         'So tốc độ với batch4 cũ là tham khảo lịch sử, chưa phải đối chứng đồng thời.')
(BUNDLE/'usage-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
with (BUNDLE/'resource-data.csv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=['seconds', 'gpu_utilization', 'vram_used_mib',
        'vram_total_mib', 'power_w', 'sm_clock_mhz'])
    writer.writeheader()
    for row in stable:
        writer.writerow(dict(seconds=row['at_monotonic']-stable[0]['at_monotonic'],
                             **{key:row[key] for key in writer.fieldnames if key != 'seconds'}))
print(json.dumps(summary, ensure_ascii=False), flush=True)
