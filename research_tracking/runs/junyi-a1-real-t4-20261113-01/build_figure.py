"""Tổng hợp số đo thật và dựng SVG/PDF/PNG độc lập.

Màu/quy ước từ figures4papers e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15,
ChenLiu-1996, CC BY-NC 4.0. Provenance ở bundle figures4papers-akt-20261112-01.
"""
import csv
import json
import os
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUTPUT=ROOT/'experiments/akt/results/colab-a1-real-t4-20261113-attempt02'
os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/akt/runtime/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

short=json.loads((OUTPUT/'result.json').read_text(encoding='utf-8'))
long=json.loads((OUTPUT/'profile/result.json').read_text(encoding='utf-8'))
assert short['status']=='PASS_REAL_JUNYI_T4_BOUNDED_THROUGHPUT'
assert long['status']=='PASS_REAL_T4_STEADY_PIPELINE_PROFILE'
short_rows=[]
for method in ('reference','compact'):
    blocks=[row for row in short['training'] if row['method']==method]
    samples=[[float(value.strip()) for value in row['values'].split(',')]
             for row in short['samples'] if row['phase'].startswith(method) and row['returncode']==0]
    seconds=sum(row['seconds'] for row in blocks)
    targets=sum(row['targets'] for row in blocks)
    short_rows.append(dict(method=method,steps=sum(row['steps'] for row in blocks),seconds=seconds,
        targets=targets,targets_per_second=targets/seconds,gpu_samples=len(samples),
        gpu_util_mean_percent=statistics.mean(row[0] for row in samples),
        peak_memory_mib=max(row[1] for row in samples)))
steady=[]
telemetry=[]
for sample in long['samples']:
    if sample['returncode']==0 and sample['values']:
        util,memory,power,clock,temperature=[float(v.strip()) for v in sample['values'].split(',')]
        telemetry.append(dict(phase=sample['phase'],at=sample['at'],gpu_util_percent=util,
            memory_mib=memory,power_watts=power,sm_clock_mhz=clock,temperature_c=temperature,
            rss_bytes=sample['rss_bytes']))
for condition in long['conditions']:
    samples=[row for row in telemetry if row['phase']==condition['name']]
    steady.append(dict(name=condition['name'],seconds=condition['seconds'],steps=condition['steps'],
        targets=condition['targets'],targets_per_second=condition['targets_per_second'],
        gpu_samples=len(samples),gpu_util_mean_percent=statistics.mean(row['gpu_util_percent'] for row in samples),
        peak_memory_mib=max(row['memory_mib'] for row in samples),
        seconds_per_batch=condition['seconds']/condition['steps'],
        read_seconds_per_batch=condition['read_seconds']/condition['steps'],
        prepare_seconds_per_batch=condition['batch_prepare_seconds']/condition['steps'],
        step_seconds_per_batch=condition['adapter_step_seconds']/condition['steps'],
        conditional_train_epoch_minutes=13347331/condition['targets_per_second']/60))
cache_results=[json.loads((HERE/name).read_text(encoding='utf-8')) for name in
               ('graph-cache-prototype.json','graph-cache-validated-prototype.json')]
cache_rows=[dict(variant=name,direct_seconds=row['mean_seconds']['direct'],
    cached_seconds=row['mean_seconds']['cached'],warm_component_speedup=row['warm_component_speedup'],
    build_once_seconds=row['build_once_seconds']) for name,row in zip(('naive','validated_immutable'),cache_results)]
for name,rows in [('short-training.csv',short_rows),('steady-training.csv',steady),
                  ('steady-gpu-telemetry.csv',telemetry),('graph-cache-comparison.csv',cache_rows)]:
    with (HERE/name).open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
summary=dict(status='REAL_T4_BENCHMARK_PROFILE_AND_CACHE_PROTOTYPE_COMPLETE',population=short['population'],
    short=short_rows,short_speedup=short_rows[0]['seconds']/short_rows[1]['seconds'],
    validation=short['validation'],validation_probability_max_drift=short['validation_max_probability_drift'],
    steady=steady,preloaded_speedup=steady[2]['targets_per_second']/steady[1]['targets_per_second'],
    cache_prototypes=cache_rows,benchmark_state_downloaded_and_verified=True,modal_spent_usd=0,
    production_graph_cache=False,full_epoch_executed=False,h100_measured=False,
    limits_vi='Chuỗi dài gồm warmup2batch và≥15giây mỗiđiềukiện, thứtựcốđịnh, khởitạomới vàcohortlặp. '
              'Cache input preloaded và cache graph là hai phép thử khác nhau. '
              'Ngoại suy T4 theo target/giây chưa gồm full admission/checkpoint/validation và không áp cho H100.')
(HERE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none',
                     'axes.spines.top':False,'axes.spines.right':False})
colors=['#777777','#B74040','#134F95']
labels=['A0','A1 đọc mẫu','A1 sẵn input']
fig,axes=plt.subplots(1,2,figsize=(11,4.8))
bars=axes[0].bar(labels,[row['targets_per_second']/1000 for row in steady],color=colors,width=.58)
axes[0].bar_label(bars,fmt='%.2f',padding=5)
axes[0].set_ylim(0,22)
axes[0].set_ylabel('Nghìn target/giây')
axes[0].set_title('Thông lượng sau làm nóng',pad=18)
bars=axes[1].bar(labels,[row['gpu_util_mean_percent'] for row in steady],color=colors,width=.58)
axes[1].bar_label(bars,fmt='%.1f%%',padding=5)
axes[1].axhline(50,color='#555555',linestyle='--',linewidth=1)
axes[1].text(2.35,52,'Mục tiêu 50%',ha='right',fontsize=9)
axes[1].set_ylim(0,100)
axes[1].set_ylabel('GPU-Util trung bình theo mẫu (%)')
axes[1].set_title('Tesla T4 · cùng cohort Junyi thật',pad=18)
fig.suptitle('Đo pipeline trên T4 · FP32 · batch128 · ba điều kiện khoảng15giây',fontsize=13)
fig.text(.5,.04,'256 window train, lấy từ8shard · warmup2batch · giữ toàn bộ mẫu GPU từng phase\n'
    'A1 sẵn input dùng records đã giải mã trong RAM · chưa là cache graph production hoặc toàn epoch',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.15,1,.92))
for extension in ('svg','png','pdf'):
    target=HERE/f'junyi-real-t4-steady-v1.{extension}';assert not target.exists();fig.savefig(target,dpi=150)
plt.close(fig)
fig,axis=plt.subplots(figsize=(8,4.5))
bars=axis.bar(['Kiểm lặp từng entry','Bytes bất biến đã kiểm'],
    [row['warm_component_speedup'] for row in cache_rows],color=['#B74040','#134F95'],width=.55)
axis.bar_label(bars,fmt='%.2f×',padding=6)
axis.axhline(1,color='#555555',linestyle='--',linewidth=1)
axis.set_ylim(0,2.1)
axis.set_ylabel('Tăng tốc phần context khi cache đã có')
axis.set_title('Thử cache graph theo window trên CPU',pad=20)
fig.text(.5,.04,'Mỗi prototype đối chiếu với builder trực tiếp trong cùng lượt · 256 window\n'
    'Dữ liệu và digest khớp khi đổi nhóm/shuffle · chưa đo cache graph trên GPU hoặc toàn epoch',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.16,1,1))
for extension in ('svg','png','pdf'):
    target=HERE/f'graph-cache-cpu-v1.{extension}';assert not target.exists();fig.savefig(target,dpi=150)
plt.close(fig)
print(json.dumps({'short_speedup':summary['short_speedup'],'steady':steady,'preloaded_speedup':summary['preloaded_speedup'],'cache':cache_rows},ensure_ascii=False))
