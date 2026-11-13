"""Vẽ số đo CPU component, dùng quy ước màu figures4papers đã lưu provenance.

ChenLiu-1996, e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15, CC BY-NC 4.0.
Hồ sơ ở research_tracking/runs/figures4papers-akt-20261112-01/.
"""
import csv
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/akt/runtime/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

result=json.loads((HERE/'result.json').read_text(encoding='utf-8'))
assert result['status']=='PASS_COMPACT_A1_CONTEXT_CPU_PROTOTYPE'
with (HERE/'component-data.csv').open('x',encoding='utf-8',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=['method','seconds'])
    writer.writeheader()
    writer.writerows(result['timings'])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none',
                     'axes.spines.top':False,'axes.spines.right':False})
fig,axis=plt.subplots(figsize=(8,4.7))
bars=axis.bar(['Evidence hiện hành','Mảng gọn thử nghiệm'],
    [result['mean_seconds'][name] for name in ('reference','compact')],
    color=['#B74040','#134F95'],width=.55)
axis.bar_label(bars,fmt='%.3f s',padding=6)
axis.set_ylim(0,1.05)
axis.set_ylabel('Giây chuẩn bị context và 4 checksum')
axis.set_title('A1 trên CPU · cùng 128 cửa sổ Junyi TRAIN80',pad=20)
fig.text(.5,.04,'5.527 target · message FP32 và mask khớp · hai lượt mỗi bản\n'
    'Chỉ đo thành phần CPU · chưa nối trainer, chưa đo tốc độ toàn epoch/GPU',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.13,1,1))
for extension in ('svg','png','pdf'):
    target=HERE/f'compact-context-cpu-v1.{extension}'
    assert not target.exists()
    fig.savefig(target,dpi=150)
plt.close(fig)
print('Đã dựng hình và CSV từ số đo component CPU.')
