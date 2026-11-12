"""Dựng figure tiến độ từ snapshot checkpoint, giữ từng phiên bản hình."""
import argparse
import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
font_cache = ROOT/'artifacts/figure_runtime/matplotlib'
font_cache.mkdir(parents=True,exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(font_cache)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BUNDLE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--snapshot',required=True)
parser.add_argument('--version',required=True)
args = parser.parse_args()
assert Path(args.snapshot).name==args.snapshot and args.version.isalnum()
snapshot = json.loads((BUNDLE/args.snapshot).read_text())
history = snapshot['progress']['history']
training = snapshot['training']
assert len(history)==len(training)
rows = []
for measured,train in zip(history,training):
    assert train['complete'] and train['valid_targets']==13347331
    assert train['optimizer_steps']==1818
    rows.append(dict(epoch=measured['epoch'],training_seconds=train['resource']['wall_seconds'],
        validation_seconds=measured['validation_seconds'],
        selection_log_loss=measured['validation']['native_bce'],
        training_targets=train['valid_targets'],selection_targets=measured['validation']['targets']))
stem = BUNDLE/('a0-h100-progress-'+args.version)
assert not stem.with_suffix('.csv').exists()
with stem.with_suffix('.csv').open('x',newline='',encoding='utf-8') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
fig,axes=plt.subplots(1,2,figsize=(10,4.5),layout='constrained')
epochs=[row['epoch'] for row in rows]
axes[0].plot(epochs,[row['selection_log_loss'] for row in rows],marker='o',color='#3b7085')
axes[0].set_xticks(epochs)
axes[0].set_xlim(min(epochs)-.4,max(epochs)+.4)
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Log Loss trên tập chọn epoch')
axes[0].set_ylim(.345,.365)
for row in rows:
    axes[0].annotate(f"{row['selection_log_loss']:.4f}",
        (row['epoch'],row['selection_log_loss']),xytext=(0,9),textcoords='offset points',ha='center')
train=[row['training_seconds']/60 for row in rows]
validation=[row['validation_seconds']/60 for row in rows]
axes[1].bar(epochs,train,label='Training',color='#3b7085',width=.55)
axes[1].bar(epochs,validation,bottom=train,label='Validation',color='#a87743',width=.55)
axes[1].set_xticks(epochs)
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Thời gian (phút)')
axes[1].set_ylim(0,7)
axes[1].legend(loc='upper right',frameon=False)
for epoch,t,v in zip(epochs,train,validation):
    axes[1].text(epoch,t/2,f'{t:.2f}',ha='center',va='center',color='white')
    axes[1].text(epoch,t+v/2,f'{v:.2f}',ha='center',va='center',color='white')
fig.suptitle('A0 không đồ thị trên Junyi — H100, batch128',fontsize=13)
fig.supxlabel('13,35 triệu lượt train và 1,60 triệu lượt selection mỗi epoch · chưa đánh giá độc lập',fontsize=9)
for extension in ('svg','pdf','png'):
    assert not stem.with_suffix('.'+extension).exists()
    fig.savefig(stem.with_suffix('.'+extension),dpi=150)
plt.close(fig)
print(stem)
