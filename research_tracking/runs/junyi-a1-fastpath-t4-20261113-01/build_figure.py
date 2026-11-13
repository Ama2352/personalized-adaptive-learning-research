"""Vẽ phép kiểm ngắn T4 từ artifact đã tải và kiểm inventory.

Bảng màu/quy ước từ figures4papers commit
e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15, ChenLiu-1996, CC BY-NC 4.0.
Hồ sơ nguồn tại research_tracking/runs/figures4papers-akt-20261112-01/.
"""
import csv
import json
import os
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.environ['MPLCONFIGDIR'] = str(ROOT/'artifacts/akt/runtime/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

result = json.loads((ROOT/'experiments/akt/results/colab-a1-fastpath-t4-20261113-01/result.json').read_text())
assert result['status'] == 'PASS_T4_A1_EVIDENCE_JSON_PARITY'
summary = []
telemetry = []
for row in result['gpu_samples']:
    if row['returncode'] == 0 and row['values']:
        gpu, memory, power = [float(value.strip()) for value in row['values'].split(',')]
        telemetry.append(dict(phase=row['phase'],monotonic=row['monotonic'],
                              gpu_util_percent=gpu,memory_used_mib=memory,power_watts=power))
for record in result['short_training']:
    samples = [row for row in telemetry if row['phase']==record['method']]
    summary.append(dict(**record,samples=len(samples),
        gpu_util_mean_percent=statistics.mean(row['gpu_util_percent'] for row in samples),
        peak_memory_mib=max(row['memory_used_mib'] for row in samples)))
for filename,rows in [('training-summary.csv',summary),('gpu-telemetry.csv',telemetry)]:
    with (HERE/filename).open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
receipt=dict(status=result['status'],elapsed_seconds=result['elapsed_seconds'],
    training=summary,speedup=summary[0]['seconds']/summary[1]['seconds'],
    time_reduction_percent=100*(1-summary[1]['seconds']/summary[0]['seconds']),
    all_parity_drifts_zero=all(all(value==0 for value in row['max_absolute_drift'].values())
                              for row in result['alphas']),modal_spent_usd=0,
    limits_vi='Một cặp sáu bước, cũ rồi mới, mẫu tổng hợp và prefix dựng sẵn. '
              'GPU-Util nvidia-smi có cửa sổ lấy mẫu và ranh giới phase xấp xỉ. '
              'Chưa đo toàn producer, toàn epoch hoặc hiệu năng H100.')
(HERE/'summary.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
                     'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
fig,axes=plt.subplots(1,2,figsize=(10,4.7))
colors=['#B74040','#134F95']
labels=['Trước sửa','Sau sửa']
bars=axes[0].bar(labels,[row['seconds'] for row in summary],color=colors,width=.55)
axes[0].bar_label(bars,fmt='%.2f s',padding=5)
axes[0].set_ylim(0,8)
axes[0].set_ylabel('Giây cho 6 bước training')
axes[0].set_title('Thông lượng tăng 1,26 lần')
bars=axes[1].bar(labels,[row['gpu_util_mean_percent'] for row in summary],color=colors,width=.55)
axes[1].bar_label(bars,fmt='%.1f%%',padding=5)
axes[1].axhline(50,color='#555555',linestyle='--',linewidth=1)
axes[1].text(1.45,52,'Mục tiêu 50%',ha='right',fontsize=9)
axes[1].set_ylim(0,65)
axes[1].set_ylabel('GPU-Util trung bình theo mẫu (%)')
axes[1].set_title('Mẫu ngắn trên Tesla T4')
fig.suptitle('A1 giữ nguyên công thức · batch128 × 200 · dữ liệu tổng hợp',fontsize=13)
fig.text(.5,.04,'Prefix dựng sẵn · một lượt đối chiếu, 6 bước mỗi bản · VRAM đỉnh 5.269 MiB\n'
         'Loss, gradient và trọng số sau bước kiểm khớp · Chưa đo toàn epoch Junyi/H100',
         ha='center',fontsize=9)
fig.tight_layout(rect=(0,.14,1,.93))
for extension in ('svg','png','pdf'):
    target=HERE/f'a1-fastpath-t4-v1.{extension}'
    assert not target.exists()
    fig.savefig(target,dpi=150)
plt.close(fig)
print(json.dumps(receipt,ensure_ascii=False))
