"""Tổng hợp số đo cache thật, giữ CSV và figure SVG/PNG/PDF độc lập.

Tái dùng màu và quy ước figures4papers đã ghim tại bundle
figures4papers-akt-20261112-01, ChenLiu-1996, CC BY-NC 4.0.
"""
import csv
import json
import os
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUTPUT=ROOT/'experiments/akt/results/colab-a1-graph-cache-t4-20261113-01'
result=json.loads((OUTPUT/'result.json').read_text(encoding='utf-8'))
assert result['status']=='PASS_REAL_JUNYI_T4_GRAPH_CACHE'
assert all(row['max_absolute_drift']==0 for row in result['parity'])
assert result['validation_max_probability_drift']==result['checkpoint_reload_max_drift']==0
rows=[]
telemetry=[]
for sample in result['samples']:
    if sample['returncode']==0 and sample['values']:
        gpu,memory,power=map(float,sample['values'].split(','))
        telemetry.append(dict(phase=sample['phase'],at=sample['at'],gpu_util_percent=gpu,
                              memory_mib=memory,power_watts=power))
for name in ('reference','compact'):
    blocks=[row for row in result['training'] if row['method']==name]
    samples=[row for row in telemetry if row['phase'].startswith(name+'-')]
    seconds=sum(row['seconds'] for row in blocks)
    targets=sum(row['targets'] for row in blocks)
    rows.append(dict(method=result['methods'][name],steps=sum(row['steps'] for row in blocks),
        seconds=seconds,targets=targets,targets_per_second=targets/seconds,
        gpu_mean_percent=statistics.mean(row['gpu_util_percent'] for row in samples),
        gpu_samples=len(samples),peak_memory_mib=max(row['memory_mib'] for row in samples),
        min_block_targets_per_second=min(row['targets_per_second'] for row in blocks),
        max_block_targets_per_second=max(row['targets_per_second'] for row in blocks)))
for name,data in [('comparison.csv',rows),('gpu-telemetry.csv',telemetry)]:
    with (HERE/name).open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
speedup=rows[1]['targets_per_second']/rows[0]['targets_per_second']
summary=dict(status='PASS_CACHE_PARITY_PERFORMANCE_NOT_CONCLUSIVE',methods=rows,speedup=speedup,
    throughput_change_percent=(speedup-1)*100,cache_build_seconds=result['graph_cache']['wall_seconds'],
    cache_bytes=result['graph_cache']['bytes'],cache_windows=result['graph_cache']['windows'],
    population=result['population'],parity=result['parity'],prediction_drift=0,checkpoint_reload_drift=0,
    optimizer_steps=result['workload']['optimizer_steps'],local_tests_passed=62,
    elapsed_gpu_probe_seconds=result['elapsed_seconds'],modal_spent_usd=0,
    benchmark_checkpoint_downloaded=True,full_train_cache_built=False,h100_measured=False,
    cache_default_enabled=False,
    limits_vi='Hai block10giây mỗi phương án theo ABBA, lặp cohort nhỏ. GPU sample gồm warmup2step mỗi block. '
              'Hai model cùng tồn tại trên GPU. Prediction so sau reset về cùng weights. '
              'Checkpoint terminal giữ state train trước reset. Chưa đo cả epoch, source2migration hoặc fullproducer CUDA.')
(HERE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/akt/runtime/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none',
                     'svg.hashsalt':'junyi-a1-graph-cache-20261113-01',
                     'axes.spines.top':False,'axes.spines.right':False})
labels=['Dựng context\ntrực tiếp','Cache graph\nSQLite']
colors=['#777777','#134F95']
fig,axes=plt.subplots(1,2,figsize=(10.8,5))
values=[row['targets_per_second']/1000 for row in rows]
errors=[[value-row['min_block_targets_per_second']/1000 for value,row in zip(values,rows)],
        [row['max_block_targets_per_second']/1000-value for value,row in zip(values,rows)]]
bars=axes[0].bar(labels,values,color=colors,width=.52,yerr=errors,capsize=5)
axes[0].bar_label(bars,fmt='%.2f',padding=16)
axes[0].set_ylim(0,20)
axes[0].set_ylabel('Nghìn target/giây')
axes[0].set_title('Cả đọc dữ liệu, collate và bước học',fontsize=12,pad=20)
bars=axes[1].bar(labels,[row['gpu_mean_percent'] for row in rows],color=colors,width=.52)
axes[1].bar_label(bars,fmt='%.1f%%',padding=5)
axes[1].set_ylim(0,100)
axes[1].set_ylabel('GPU-Util trung bình theo mẫu (%)')
axes[1].set_title('T4 · FP32 · batch128',fontsize=12,pad=20)
fig.suptitle('Cache graph A1 khớp kết quả · mức tăng tốc tổng còn nhỏ',fontsize=14)
fig.text(.5,.035,'256 window Junyi train · 2 block × 10 giây mỗi phương án, thứ tự ABBA\n'
    'Vạch sai số là min–max giữa block · chưa là khoảng tin cậy hoặc toàn epoch',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.14,1,.92))
for suffix in ('svg','png','pdf'):
    path=HERE/('a1-graph-cache-t4-v1.'+suffix)
    metadata={'Date':'2026-11-13'} if suffix=='svg' else None
    fig.savefig(path,dpi=180,metadata=metadata)
    if suffix=='svg':
        path.write_text('\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
plt.close(fig)
print(json.dumps(summary,ensure_ascii=False))
