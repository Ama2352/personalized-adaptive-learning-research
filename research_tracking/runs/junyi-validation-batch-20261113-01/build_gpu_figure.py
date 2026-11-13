"""Dựng hình từ phép đo T4, dùng quy ước figures4papers đã lưu trong repo.

Tham khảo Chen Liu, figures4papers, e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15,
CC BY-NC4.0. Nguồn/giấy phép ở bundle figures4papers-akt-20261112-01.
"""
import csv
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/figure_runtime/figures4papers-20261112-01/matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

report=json.loads((BUNDLE/'positive-result.json').read_text(encoding='utf-8'))
assert report['status']=='PASS_SYNTHETIC_VALIDATION_BATCH128_PARITY' and report['fixture_signal']=='positive'
rows=[]
for result in report['results']:
    for index,(legacy,batched) in enumerate(zip(result['legacy_seconds'],result['batch128_seconds'])):
        rows.append(dict(variant=result['variant'],repeat=index+1,legacy_seconds=legacy,
            batch128_seconds=batched,legacy_peak_vram_gib=result['legacy_peak_vram_bytes']/1024**3,
            batch128_peak_vram_gib=result['batch128_peak_vram_bytes']/1024**3))
with (BUNDLE/'validation-batch-data-v2.csv').open('x',encoding='utf-8',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none',
    'axes.spines.top':False,'axes.spines.right':False})
figure,axes=plt.subplots(1,2,figsize=(11,4.8),layout='constrained')
positions=np.arange(2)
colors=('#B64342','#0F4D92')
labels=('Từng cửa sổ','Batch128')
for axis,fields,title,ylabel in [
    (axes[0],('legacy_mean_seconds','batch128_mean_seconds'),'Thời gian validation','Giây'),
    (axes[1],('legacy_peak_vram_bytes','batch128_peak_vram_bytes'),'VRAM cấp phát cao nhất','GiB')]:
    for mode,field in enumerate(fields):
        values=[result[field]/(1024**3 if axis is axes[1] else 1) for result in report['results']]
        centers=positions+(-.2 if mode==0 else .2)
        bars=axis.bar(centers,values,width=.36,color=colors[mode],label=labels[mode])
        for bar,value in zip(bars,values):
            axis.annotate(f'{value:.2f}',(bar.get_x()+bar.get_width()/2,bar.get_height()),
                xytext=(0,14),textcoords='offset points',ha='center',fontsize=10)
        if axis is axes[0]:
            key='legacy_seconds' if mode==0 else 'batch128_seconds'
            for center,result in zip(centers,report['results']):
                axis.scatter(center+np.linspace(-.045,.045,3),result[key],color='#23343b',s=14,zorder=3)
    maximum=max(result[field]/(1024**3 if axis is axes[1] else 1)
        for field in fields for result in report['results'])
    if axis is axes[0]:
        maximum=max(max(result[key]) for result in report['results'] for key in ('legacy_seconds','batch128_seconds'))
    axis.set_ylim(0,maximum*1.45)
    axis.set_xticks(positions,[result['variant'] for result in report['results']])
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    axis.legend(frameon=False,loc='upper left',fontsize=9)
figure.suptitle('Validation trên T4 · cùng 12.800 target tổng hợp',fontsize=14)
figure.text(.5,-.035,'Cột là trung bình, chấm là từng lượt · ba cặp đo/model · dữ liệu ở RAM, chưa gồm SQL Junyi',
    ha='center',fontsize=9)
for extension in ('svg','pdf','png'):
    path=BUNDLE/f'validation-batch-t4-v2.{extension}'
    assert not path.exists()
    figure.savefig(path,bbox_inches='tight',dpi=180)
plt.close(figure)
print('Đã dựng SVG/PDF/PNG và CSV từ kết quả T4.')
