"""Kiểm archive, checkpoint, đối chiếu serial/parallel và dựng figure độc lập."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
REQUEST = json.loads((BUNDLE/'request04.json').read_text(encoding='utf-8'))
NATIVE = ROOT/'experiments/akt/results'/REQUEST['run_id']


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


receipt = json.loads((NATIVE/'receipt.json').read_text())
assert receipt['status']=='JUNYI_CONCURRENT_GPU_COMPLETE',receipt
assert receipt['download_inventory_verified'] is True
assert json.loads((NATIVE/'app-budget-guard.json').read_text())['stop_acknowledged'] is True
assert sha(NATIVE/'artifacts.zip')==receipt['archive_sha256']
result = receipt['worker_result']
assert result['measured_total_optimizer_steps']==1160
assert result['training_protocol_changed'] is False and result['h100_tested'] is False
assert all(row['serial_parallel_exact'] and row['checkpoint_resume_exact']
           for row in result['equivalence'].values())
with zipfile.ZipFile(NATIVE/'artifacts.zip') as archive:
    inventory = json.loads(archive.read('SHA256.json'))
    assert archive.testzip() is None
    assert set(archive.namelist())==set(inventory)|{'SHA256.json'}
    for name,pin in inventory.items():
        with archive.open(name) as stream:
            assert hashlib.file_digest(stream,'sha256').hexdigest()==pin['sha256']
        assert archive.getinfo(name).file_size==pin['bytes']
    telemetry_name = next(name for name in inventory if name.endswith('-operation/gpu-telemetry.jsonl'))
    telemetry = archive.read(telemetry_name)
    (BUNDLE/'gpu-telemetry.jsonl').write_bytes(telemetry)
    samples = [json.loads(line) for line in telemetry.splitlines()]
    checkpoints = {name:pin for name,pin in inventory.items()
                   if '/checkpoints/' in name and name.endswith('/state.pt')}
    assert len(checkpoints)==4
    for label in ('solo-a','solo-b','parallel-a','parallel-b'):
        prefix = f"experiments/akt/results/{REQUEST['run_id']}-{label}/operation/"
        child = json.loads(archive.read(prefix+'result.json'))
        assert child['actual_completed_optimizer_steps']==290
        assert child['trained_target_exposures']==9*56332
        assert child['total_target_exposures_including_resume_check']<=509758
        assert child['checkpoint_reload_and_next_update_exact'] is True
        write_json(BUNDLE/(label+'-result.json'),child)
        resume = json.loads(archive.read(prefix+'resume-verification.json'))
        assert resume['status']=='PASS_EXACT_NEXT_UPDATE'
    write_json(BUNDLE/'checkpoint-inventory.json',checkpoints)

rows = []
for case in result['cases']:
    selected = [sample for sample in samples
                if sample['phase']['name']==case['name']
                and case['measurement_started_monotonic']+1<=sample['at_monotonic']
                <=case['measurement_finished_monotonic']-1]
    assert len(selected)>=10,(case['name'],len(selected))
    row = dict(case)
    row['telemetry_samples'] = len(selected)
    for key in ('gpu_utilization','vram_used_mib','power_w'):
        row[key+'_mean'] = statistics.mean(sample[key] for sample in selected)
        row[key+'_max'] = max(sample[key] for sample in selected)
    rows.append(row)
serial_seconds = sum(row['seconds'] for row in rows[:2])
assert sum(row['targets'] for row in rows[:2])==rows[2]['targets']==901312
speedup = serial_seconds/rows[2]['seconds']
assert abs(speedup-result['aggregate_speedup'])<1e-12
summary = dict(status='VERIFIED_CONCURRENT_SMALL_GPU_ENGINEERING',gpu=result['actual_gpu_name'],cases=rows,
    serial_combined_seconds=serial_seconds,parallel_seconds=rows[2]['seconds'],
    serial_targets_per_second=901312/serial_seconds,
    parallel_targets_per_second=901312/rows[2]['seconds'],aggregate_speedup=speedup,
    time_reduction_percent=(1-1/speedup)*100,
    correctness_exact=True,checkpoint_resume_exact=True,
    decision='CANDIDATE_SMALL_GPU_ONLY_REQUIRES_REPLICATION' if speedup>=1.10 else 'DO_NOT_ADOPT_NO_CLEAR_THROUGHPUT_GAIN',
    h100_generalization_verified=False,main_training_changed=False,
    limitations_vi='Một đối chiếu ngắn, hai seed, packet lặp đã cache. Mỗi cách xử lý cùng dữ liệu và batch32 mỗi model. Chưa đo hội tụ, full epoch hoặc H100. Telemetry mỗi child làm overhead hai cách khác nhau. Thời gian bảng chỉ gồm training đo, chưa gồm warmup/khởi động/checkpoint.')
write_json(BUNDLE/'comparison.json',summary)
with (BUNDLE/'comparison.csv').open('w',newline='',encoding='utf-8') as stream:
    fields=['name','concurrent_processes','seconds','targets','targets_per_second',
            'gpu_utilization_mean','vram_used_mib_mean','power_w_mean','telemetry_samples']
    writer = csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

labels = ['Hai model\nchạy lần lượt','Hai model\nchạy đồng thời']
times = [serial_seconds,rows[2]['seconds']]
fig,axes = plt.subplots(1,2,figsize=(10,4.8),layout='constrained')
bars = axes[0].bar(labels,times,color=['#3b7085','#8c4143'],width=.55)
axes[0].set_ylabel('Thời gian training đo (giây)')
axes[0].set_ylim(0,max(times)*1.3)
axes[0].bar_label(bars,labels=[f'{value:.2f} s' for value in times],padding=6)
gpu = [statistics.mean(row['gpu_utilization_mean'] for row in rows[:2]),rows[2]['gpu_utilization_mean']]
bars = axes[1].bar(labels,gpu,color=['#3b7085','#8c4143'],width=.55)
axes[1].set_ylabel('GPU-Util trung bình (%)')
axes[1].set_ylim(0,115)
axes[1].bar_label(bars,labels=[f'{value:.1f}%' for value in gpu],padding=6)
fig.suptitle(f"AKT trên một {result['actual_gpu_name']} — cùng 901.312 target đo mỗi cách",fontsize=13)
fig.supxlabel('Batch32 mỗi model · cùng seed42/43 · chưa kiểm H100 hoặc chất lượng độc lập',fontsize=9)
for extension in ('svg','pdf','png'):
    fig.savefig(BUNDLE/('concurrency-comparison.'+extension),dpi=160)
plt.close(fig)
print(json.dumps(summary,ensure_ascii=False,indent=2))
