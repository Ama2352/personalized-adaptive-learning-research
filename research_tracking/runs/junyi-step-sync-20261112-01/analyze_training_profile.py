"""Đọc riêng phần training đã hoàn tất, giữ nguyên thất bại của toàn job."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--execution', choices=('01', '02', '03'), required=True)
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
NATIVE = ROOT/'experiments/akt/results'/('modal-junyi-step-sync-t4-20261112-'+args.execution)
prefix = {'01':'sync', '02':'attention', '03':'attention-cache'}[args.execution]
receipt = json.loads((NATIVE/'receipt.json').read_text())
assert receipt['download_inventory_verified'] is True
assert json.loads((NATIVE/'app-budget-guard.json').read_text())['stop_acknowledged'] is True
if receipt['status'] != 'JUNYI_STEP_SYNC_PROFILE_COMPLETE':
    assert args.execution == '01' and receipt['status'] == 'FAILED'
    assert receipt['worker_result']['error'] == 'Prediction batch numerical tolerance exceeded'
with (NATIVE/'artifacts.zip').open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == receipt['archive_sha256']
with zipfile.ZipFile(NATIVE/'artifacts.zip') as archive:
    assert archive.testzip() is None
    inventory = json.loads(archive.read('SHA256.json'))
    assert set(archive.namelist()) == set(inventory) | {'SHA256.json'}
    for name, entry in inventory.items():
        with archive.open(name) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256']
    def read_json(suffix):
        matches = [name for name in inventory if name.endswith('-operation/'+suffix)]
        assert len(matches) == 1
        return json.loads(archive.read(matches[0]))
    cases = [read_json(f'{variant}-{repeat:02d}.json') for repeat in range(3)
             for variant in ('reference', 'candidate')]
    exact = [read_json(f'pair-{repeat:02d}-exact.json') for repeat in range(3)]
    assert all(row['status'] == 'PASS_EXACT_CUDA_PACKET_STATE' and row['model_optimizer_and_rng_exact']
               for row in exact)
    assert read_json('cuda-equivalence.json')['status'] == 'PASS_EXACT_SYNTHETIC_EQUIVALENCE'
    telemetry_name = next(name for name in inventory if name.endswith('-operation/gpu-telemetry.jsonl'))
    raw = archive.read(telemetry_name)
    (BUNDLE/(prefix+'-gpu-telemetry.jsonl')).write_bytes(raw)
samples = [json.loads(line) for line in raw.splitlines() if line.strip()]
assert len({row['initial_backbone_sha256'] for row in cases}) == 1
assert len(receipt['checkpoint_transfers']) == 6
assert len({row['checkpoint_sha256'] for row in receipt['checkpoint_transfers'].values()}) == 1
rows = []
for case in cases:
    assert case['status'] == 'COMPLETE_ENGINEERING_CASE'
    assert case['targets'] == 56332 and case['optimizer_steps'] == 256
    assert case['actual_benchmark_batch_size'] == 4 and case['fresh_reload_first_window_exact']
    selected = [sample for sample in samples if sample['phase']['variant'] == case['variant']
                and sample['phase']['repeat'] == case['repeat']]
    assert len(selected) >= 3 and all(sample['exit_code'] == 0 for sample in selected)
    readings = [list(map(float, sample['gpu'].split(','))) for sample in selected]
    rows.append(dict(variant=case['variant'], repeat=case['repeat'],
                     full_seconds=case['full_training_wall_seconds'],
                     exclude_first_seconds=case['exclude_first_batch_seconds'],
                     exclude_first_targets=case['exclude_first_batch_targets'],
                     targets_per_second=case['exclude_first_batch_targets_per_second'],
                     gpu_utilization_mean=statistics.mean(row[0] for row in readings),
                     vram_mib_mean=statistics.mean(row[1] for row in readings),
                     power_w_mean=statistics.mean(row[3] for row in readings), gpu_samples=len(selected)))
pairs = []
for repeat in range(3):
    reference = next(row for row in rows if row['repeat'] == repeat and row['variant'] == 'reference')
    candidate = next(row for row in rows if row['repeat'] == repeat and row['variant'] == 'candidate')
    assert reference['exclude_first_targets'] == candidate['exclude_first_targets']
    ratio = reference['exclude_first_seconds']/candidate['exclude_first_seconds']
    pairs.append(dict(repeat=repeat, speedup=ratio, time_reduction_fraction=1-1/ratio))
median = statistics.median(row['time_reduction_fraction'] for row in pairs)
accepted = median >= .05 and all(row['speedup'] > 1 for row in pairs)
summary = dict(status='ACCEPT_PACKET_OPTIMIZATION' if accepted else 'DO_NOT_ADOPT_FROM_PACKET',
               original_job_status=receipt['status'], original_job_error=receipt['worker_result'].get('error'),
               scope='completed_training_subexperiment_only', exact_cuda_state_pairs=3,
               checkpoint_files_byte_identical=True, rows=rows, pairs=pairs,
               median_time_reduction_fraction=median, full_epoch_benchmark=False,
               next_requirement='Ghim nguồn, kiểm resume và pipeline trước áp dụng vào lượt chính.')
(BUNDLE/(prefix+'-analysis.json')).write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
with (BUNDLE/(prefix+'-figure-data.csv')).open('x', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(json.dumps(dict(status=summary['status'], original_job_status=receipt['status'], pairs=pairs,
                      median_time_reduction_fraction=median)), flush=True)
