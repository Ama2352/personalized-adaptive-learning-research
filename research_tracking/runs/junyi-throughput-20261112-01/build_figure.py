"""Dựng histogram đã đo, dùng palette/quy ước figures4papers đã lưu trong repo."""
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

source = ROOT/'research_tracking/runs/junyi-lifecycle-20261112-01/representative-packet-selection.json'
data = json.loads(source.read_text())
labels = ['1–10','11–50','51–100','101–199','200']
counts = ([64576,30592,31606,21304,84584],[290,146,151,104,333])
bins = ((1,11),(11,51),(51,101),(101,200),(200,201))
for observed,key in zip(counts,('full_geometry','packet_geometry')):
    histogram = data[key]['length_histogram']
    assert observed==[sum(histogram[begin:end]) for begin,end in bins]
assert sum(counts[0])==data['full_geometry']['windows']==232662
assert sum(counts[1])==data['packet_geometry']['windows']==1024
rows = []
for index,label in enumerate(labels):
    rows.append(dict(window_length=label,full_count=counts[0][index],packet_count=counts[1][index],
                     full_percent=100*counts[0][index]/232662,packet_percent=100*counts[1][index]/1024))
with (BUNDLE/'figure-data.csv').open('x',newline='',encoding='utf-8') as stream:
    writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none',
                     'axes.spines.top':False,'axes.spines.right':False})
figure,axis = plt.subplots(figsize=(9,4.8),layout='constrained')
positions = range(len(labels))
axis.bar([x-.19 for x in positions],[r['full_percent'] for r in rows],width=.36,
         color='#3c6e82',label='TRAIN80 đầy đủ (232.662 cửa sổ)')
axis.bar([x+.19 for x in positions],[r['packet_percent'] for r in rows],width=.36,
         color='#8f3d3d',label='Mẫu đo T4 (1.024 cửa sổ)')
axis.set_xticks(list(positions),labels)
axis.set_ylabel('Tỷ lệ cửa sổ (%)')
axis.set_xlabel('Số bước trong cửa sổ')
axis.set_ylim(0,47)
axis.legend(frameon=False,loc='upper left',fontsize=10)
axis.set_title('Junyi — hình học dữ liệu dùng đo tốc độ',loc='left',pad=18)
for index,row in enumerate(rows):
    axis.text(index-.19,row['full_percent']+.65,f"{row['full_percent']:.1f}",ha='center',fontsize=9)
    axis.text(index+.19,row['packet_percent']+.65,f"{row['packet_percent']:.1f}",ha='center',fontsize=9)
for extension in ('svg','pdf','png'):
    target=BUNDLE/('junyi-throughput-geometry.'+extension)
    if target.exists():
        raise FileExistsError(target)
    figure.savefig(target,dpi=160)
plt.close(figure)
print('Saved SVG/PDF/PNG and CSV, geometry only')
