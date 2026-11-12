"""Figure kiểm kỹ thuật Junyi, chuyển thể style figures4papers đã ghim.

Quy ước trục, palette và vector export kế thừa commit
e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15, CC BY-NC4.0.
Nguồn/LICENSE giữ ở bundle figures4papers-akt-20261112-01.
"""
import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).parent
os.environ['MPLCONFIGDIR'] = str(ROOT/'artifacts/figure_runtime/figures4papers-20261112-01/matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

output = BUNDLE/'figure-junyi'
output.mkdir(exist_ok=False)
events = [json.loads(row) for row in (BUNDLE/'training-events.jsonl').read_text().splitlines()]
by_step = {event['training']['optimizer_steps']: event['training'] for event in events}
records = [dict(step=step, trained_targets=row['valid_targets'],
                cumulative_train_loss=row['loss_sum']/row['valid_targets'])
           for step,row in sorted(by_step.items()) if row['valid_targets']]
with (output/'training-data.csv').open('x', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
with (output/'coverage-data.csv').open('x', encoding='utf-8', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['population','targets'])
    writer.writerows([['supported',1405],['oov',125]])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,
    'axes.spines.right':False,'axes.spines.top':False,'axes.linewidth':1.3,
    'svg.fonttype':'none','pdf.fonttype':42})
fig,axes = plt.subplots(1,2,figsize=(12,4.8),gridspec_kw=dict(width_ratios=[1.4,1]))
axes[0].plot([row['step'] for row in records], [row['cumulative_train_loss'] for row in records],
             color='#0F4D92',linewidth=2)
axes[0].set(title='Một epoch đã hoàn tất',xlabel='Lần cập nhật trọng số',
            ylabel='Sai số train trung bình tích lũy',xlim=(1,79))
axes[0].grid(axis='y',alpha=.2)
axes[1].barh(['Có dự đoán','Ngoài vocabulary'],[1405,125],color=['#42949E','#9A4D8E'],height=.48)
axes[1].invert_yaxis()
axes[1].set(title='Giữ đủ 1.530 target selection',xlabel='Số tương tác',xlim=(0,1700))
for y,n in enumerate([1405,125]):
    axes[1].text(n+40,y,f'{n:,}'.replace(',','.'),va='center',fontsize=12)
fig.subplots_adjust(left=.08,right=.98,bottom=.21,top=.86,wspace=.4)
fig.text(.08,.045,'Cohort kỹ thuật 256 train / 32 selection. Chưa chọn epoch hoặc đánh giá độc lập.',fontsize=10)
try:
    for extension in ('svg','pdf','png'):
        fig.savefig(output/('junyi-lifecycle.'+extension),dpi=250,bbox_inches='tight',facecolor='white')
finally:
    plt.close(fig)
