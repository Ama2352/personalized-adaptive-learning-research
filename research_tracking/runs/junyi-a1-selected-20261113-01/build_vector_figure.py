"""Vẽ số đo H100 thực, dùng bảng màu/quy ước figures4papers đã lưu giấy phép.

Nguồn figures4papers e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15,
ChenLiu-1996, CC BY-NC 4.0. Hồ sơ tại bundle figures4papers-akt-20261112-01.
"""
import csv
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/akt/runtime/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

result=json.loads((BUNDLE/'vector-gpu-result03-from-stdout.json').read_text(encoding='utf-8'))
assert result['status']=='PASS_H100_A1_SCALAR_VECTOR_PARITY'
rows=[]
for record in result['alphas']:
    for mode in ('old','new'):
        rows.append(dict(alpha=record['alpha'],mode=mode,total_seconds=record[mode]['staged_seconds'],
            **record[mode]['stages_seconds']))
with (BUNDLE/'a1-vector-h100-data.csv').open('x',encoding='utf-8',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
    'axes.spines.right':False,'svg.fonttype':'none'})
fig,axes=plt.subplots(1,2,figsize=(12,4.6))
colors=['#B74040','#134F95']
labels=['Bản cũ','Theo batch']
for i,mode in enumerate(('old','new')):
    values=[record[mode]['staged_seconds'] for record in result['alphas']]
    bars=axes[0].bar([x+(i-.5)*.34 for x in (0,1)],values,width=.32,color=colors[i],label=labels[i])
    axes[0].bar_label(bars,fmt='%.3f',padding=5)
axes[0].set_xticks([0,1],['Alpha = 0','Alpha = 0,75'])
axes[0].set_ylim(0,3.5)
axes[0].set_title('Tổng các giai đoạn đã đo')
axes[0].set_ylabel('Giây')
axes[0].legend(frameon=False)
stages=('bind','forward','backward')
record=result['alphas'][1]
for i,mode in enumerate(('old','new')):
    bars=axes[1].bar([x+(i-.5)*.34 for x in range(3)],
        [record[mode]['stages_seconds'][stage] for stage in stages],width=.32,color=colors[i])
    axes[1].bar_label(bars,fmt='%.3f',padding=5)
axes[1].set_xticks(range(3),['Gắn dữ liệu đồ thị','Forward','Backward'])
axes[1].set_ylim(0,.72)
axes[1].set_ylabel('Giây')
axes[1].set_title('Chi tiết ở alpha = 0,75')
fig.suptitle('A1 trên H100 · cùng batch128 × 200 · 12.800 target tổng hợp',fontsize=14)
fig.text(.5,.035,'Mỗi alpha đo một cặp, đảo thứ tự cũ/mới · GPU dùng chung với training\n'
    'Tổng không gồm sao chép snapshot so sánh · Chưa phải tốc độ toàn Junyi',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.12,1,.94))
for extension in ('svg','png','pdf'):
    destination=BUNDLE/('a1-vector-h100-v1.'+extension)
    assert not destination.exists()
    fig.savefig(destination,dpi=150)
plt.close(fig)
print('Đã lưu SVG/PDF/PNG/CSV từ số đo H100, giữ giới hạn phép đo trên hình.')
