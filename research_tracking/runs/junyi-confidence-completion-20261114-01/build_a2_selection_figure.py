"""Dựng đường chọn epoch A2 từ kết quả GPU, giữ SVG/PNG/CSV và nguồn.

Áp dụng palette và quy ước Matplotlib của Chen Liu, figures4papers,
commit e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15, CC BY-NC 4.0.
Hồ sơ tham khảo đã lưu tại runs/figures4papers-akt-20261112-01/.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/figure_runtime/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=HERE/'figures')
    parser.add_argument('--prefix',default='a2-junyi-selection-v01')
    args=parser.parse_args()
    source=ROOT/'experiments/akt/results/modal-junyi-a2-staged-h100-20261114-10/remote-inventory.json'
    receipt=json.loads(source.read_text())
    terminal=receipt['worker_result']['terminal']
    assert terminal['status']=='JUNYI_A2_SELECTED_ONLY_COMPLETE'
    assert terminal['complete_epochs']==12 and terminal['selected_epoch']==9
    assert all(row['validation']['targets']==1600343 for row in terminal['history'])
    output=args.output_dir
    output.mkdir(parents=True,exist_ok=True)
    paths={extension:output/(args.prefix+'.'+extension) for extension in ('svg','png','csv','json')}
    assert not any(path.exists() for path in paths.values())
    records=[dict(epoch=row['epoch'],native_selection_bce=row['validation']['native_bce'],
        selected=row['epoch']==terminal['selected_epoch'],selection_seconds=row['validation_seconds'],
        targets=row['validation']['targets']) for row in terminal['history']]
    with paths['csv'].open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
        'axes.spines.top':False,'axes.spines.right':False,
        'svg.fonttype':'none','pdf.fonttype':42,'axes.linewidth':1.1})
    fig,ax=plt.subplots(figsize=(8.2,4.8))
    fig.subplots_adjust(left=.13,right=.97,bottom=.22,top=.86)
    ax.plot([row['epoch'] for row in records],[row['native_selection_bce'] for row in records],
        color='#0F4D92',marker='o',markersize=5,linewidth=2)
    chosen=records[terminal['selected_epoch']-1]
    ax.scatter([chosen['epoch']],[chosen['native_selection_bce']],color='#B64342',s=100,zorder=4)
    ax.annotate('Checkpoint đã chọn\nepoch 9 · Log Loss 0,35356694',
        xy=(chosen['epoch'],chosen['native_selection_bce']),xycoords='data',
        xytext=(.48,.82),textcoords='axes fraction',fontsize=11,
        bbox=dict(boxstyle='round,pad=.45',facecolor='white',edgecolor='#d5dee6'),
        arrowprops=dict(arrowstyle='->',color='#B64342',linewidth=1.3))
    ax.set(title='Diễn biến chọn checkpoint A2 trên Junyi',xlabel='Epoch',ylabel='Log Loss trên tập chọn checkpoint')
    ax.set_xticks(range(1,13))
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
    ax.grid(axis='y',alpha=.2)
    ax.margins(x=.04,y=.12)
    fig.text(.13,.08,'Selection cố định · 15.847 người học · 1.600.343 tương tác · seed 42',fontsize=10)
    fig.text(.13,.035,'Checkpoint được chọn theo cải thiện tối thiểu 0,0001 và patience 3.',fontsize=9.5,color='#465466')
    fig.savefig(paths['svg'],metadata={'Creator':'KLTN, áp dụng quy ước figures4papers của Chen Liu',
        'Description':'Lịch sử selected-fit A2 Junyi. Dữ liệu Development dùng chọn epoch.'})
    fig.savefig(paths['png'],dpi=200)
    plt.close(fig)
    manifest=dict(source=source.relative_to(ROOT).as_posix(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        model='A2_EXPERT',phase='selected_fit80',selected_epoch=9,complete_epochs=12,
        style_reference='research_tracking/runs/figures4papers-akt-20261112-01/upstream-reference.json',
        license_reference='research_tracking/runs/figures4papers-akt-20261112-01/upstream__LICENSE',
        interpretation_vi='Theo dõi chọn checkpoint trên selection. Đánh giá độc lập còn chờ.',
        files={path.name:dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
               for extension,path in paths.items() if extension!='json'})
    with paths['json'].open('x',encoding='utf-8') as stream:
        json.dump(manifest,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(status='A2_SELECTION_FIGURE_SAVED',output=str(output))))


if __name__=='__main__':
    main()
