"""Lưu số đo CPU/T4 và hình độc lập theo quy ước màu figures4papers.

ChenLiu-1996, e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15, CC BY-NC 4.0.
Provenance tại research_tracking/runs/figures4papers-akt-20261112-01/.
"""
import csv
import json
import os
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/akt/runtime/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

gpu=json.loads((ROOT/'experiments/akt/results/colab-a1-compact-adapter-20261113-01/result.json').read_text())
cpu=json.loads((HERE/'context-component.json').read_text(encoding='utf-8'))
assert gpu['status']=='PASS_T4_COMPACT_ADAPTER_PARITY_AND_TIMING'
assert cpu['status']=='PASS_COMPACT_ADAPTER_CONTEXT_CPU_COMPONENT'
telemetry=[]
for sample in gpu['samples']:
    if sample['returncode']==0 and sample['values']:
        util,memory,power=[float(value.strip()) for value in sample['values'].split(',')]
        telemetry.append(dict(phase=sample['phase'],at=sample['at'],gpu_util_percent=util,
                              memory_used_mib=memory,power_watts=power))
summary=[]
for method in ('reference','compact'):
    runs=[row for row in gpu['training'] if row['method']==method]
    samples=[row for row in telemetry if row['phase'].startswith(method)]
    seconds=sum(row['seconds'] for row in runs)
    targets=sum(row['targets'] for row in runs)
    summary.append(dict(method=method,steps=sum(row['steps'] for row in runs),seconds=seconds,
        targets=targets,targets_per_second=targets/seconds,samples=len(samples),
        gpu_util_mean_percent=statistics.mean(row['gpu_util_percent'] for row in samples),
        peak_memory_mib=max(row['memory_used_mib'] for row in samples)))
for name,rows in [('gpu-telemetry.csv',telemetry),('gpu-blocks.csv',gpu['training']),
                  ('gpu-summary.csv',summary),('cpu-component-data.csv',cpu['timings'])]:
    with (HERE/name).open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
receipt=dict(status='PASS_CPU_AND_T4_COMPACT_ADAPTER',gpu=summary,
    gpu_speedup=summary[0]['seconds']/summary[1]['seconds'],cpu_component_speedup=cpu['component_speedup'],
    gpu_probe_seconds=gpu['elapsed_seconds'],gpu_parity=gpu['parity'],local_tests_passed=69,
    modal_spent_usd=0,real_junyi_epoch_benchmarked=False,source2_checkpoint_migrated=False,
    limits_vi='GPU fixture tổng hợp, 8 bước mỗi bản theo ABBA. Gồm collate/prefix/checksum và step. '
              'Chưa gồm SQL/cache I/O, checkpoint, validation, epoch Junyi hoặc H100. '
              'CPU component dùng 128 window thật từ shard đầu TRAIN80. GPU sample có tương quan.')
(HERE/'summary.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none',
                     'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,3,figsize=(13,4.7))
labels=['Reference','Compact']
colors=['#B74040','#134F95']
values=[[cpu['mean_seconds'][key] for key in ('reference','compact')],
        [row['seconds'] for row in summary],[row['gpu_util_mean_percent'] for row in summary]]
titles=['Chuẩn bị context trên CPU','Collate + training step trên T4','GPU-Util theo mẫu trên T4']
ylabels=['Giây / 128 window thật','Giây / 8 bước tổng hợp','GPU-Util trung bình (%)']
limits=[1.1,18,100]
for axis,heights,title,ylabel,limit in zip(axes,values,titles,ylabels,limits):
    bars=axis.bar(labels,heights,color=colors,width=.58)
    axis.bar_label(bars,fmt='%.2f',padding=5)
    axis.set_title(title,pad=18)
    axis.set_ylabel(ylabel)
    axis.set_ylim(0,limit)
axes[2].axhline(50,color='#555555',linestyle='--',linewidth=1)
axes[2].text(1.4,52,'Mục tiêu 50%',ha='right',fontsize=8)
fig.suptitle('A1 · cùng công thức, trọng số khởi tạo, batch và FP32',fontsize=14)
fig.text(.5,.04,'T4 batch128 × 200 · kiểm alpha0 và0,75 khớp · VRAM đỉnh5.305MiB\n'
    'Phép đo ngắn, chưa gồm I/O và toàn epoch Junyi/H100',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.15,1,.92))
for extension in ('svg','png','pdf'):
    path=HERE/f'compact-adapter-cpu-t4-v1.{extension}'
    assert not path.exists()
    fig.savefig(path,dpi=150)
plt.close(fig)
print(json.dumps(receipt,ensure_ascii=False))
