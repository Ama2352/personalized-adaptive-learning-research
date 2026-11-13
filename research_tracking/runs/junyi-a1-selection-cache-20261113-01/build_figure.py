"""Dựng figure độc lập từ lịch sử/checkpoint đã kiểm, không suy kết quả Holdout.

Màu và quy ước tái dùng figures4papers đã ghim tại bundle
figures4papers-akt-20261112-01, ChenLiu-1996, CC BY-NC 4.0.
"""
import argparse
import csv
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',required=True)
    parser.add_argument('--history',default='live-history.json')
    args=parser.parse_args()
    assert args.version.isalnum()
    history=json.loads((HERE/args.history).read_text())
    records=[json.loads(line) for line in (HERE/'monitor.jsonl').read_text().splitlines()]
    measured=next(row['train_epochs'] for row in reversed(records) if row.get('train_epochs'))
    epochs={row['epoch']:row for row in measured if row['complete']}
    selected=[epochs[i] for i in (1,2,3) if i in epochs]
    assert len(selected)==3 and all(row['targets']==13347331 for row in selected)
    rows=[dict(epoch=row['epoch'],seconds=row['wall_seconds'],targets=row['targets'],
               targets_per_second=row['targets']/row['wall_seconds']) for row in selected]
    with (HERE/('training-time-'+args.version+'.csv')).open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    validation=[dict(epoch=row['epoch'],selection_logloss=row['validation']['native_bce'],
                     targets=row['validation']['targets'],seconds=row['validation_seconds']) for row in history['history']]
    with (HERE/('selection-curve-'+args.version+'.csv')).open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(validation[0]));writer.writeheader();writer.writerows(validation)
    os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/akt/runtime/matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none',
        'svg.hashsalt':'a1-resume-'+args.version,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11.2,5.2))
    bars=axes[0].bar(['Source2\nepoch1','Compact + đọc trước\nepoch2','Compact + đọc trước\nepoch3'],
        [row['seconds']/60 for row in rows],color=['#777777','#134F95','#134F95'],width=.57)
    axes[0].bar_label(bars,fmt='%.2f',padding=5)
    axes[0].set_ylabel('Phút training / epoch')
    axes[0].set_ylim(0,27)
    axes[0].set_title('Cùng 13.347.331 target / epoch',fontsize=12,pad=20)
    axes[0].tick_params(axis='x',labelsize=9)
    x=[row['epoch'] for row in validation];y=[row['selection_logloss'] for row in validation]
    axes[1].plot(x,y,marker='o',color='#134F95')
    for a,b in zip(x,y):axes[1].annotate(f'{b:.5f}',(a,b),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9)
    axes[1].set_xticks(x)
    axes[1].set_xlabel('Epoch đã hoàn tất validation')
    axes[1].set_ylabel('Log Loss trên selection (thấp hơn tốt hơn)')
    axes[1].set_title('1.600.343 target selection, 0 OOV',fontsize=12,pad=20)
    axes[1].set_ylim(min(y)-.0015,max(y)+.0025)
    fig.suptitle('A1 đã nối checkpoint epoch1 và tiếp tục trên H100',fontsize=14)
    fig.text(.5,.035,'H100 · FP32 · batch128 · thời gian ở các epoch khác nhau, chưa là benchmark lặp ghép cặp\n'
        'Selection dùng chọn checkpoint · chưa refit/calibration/đánh giá độc lập',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.16,1,.92))
    for suffix in ('svg','png','pdf'):
        path=HERE/('a1-resume-h100-'+args.version+'.'+suffix)
        assert not path.exists()
        fig.savefig(path,dpi=180,metadata={'Date':'2026-11-13'} if suffix=='svg' else None)
        if suffix=='svg':path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
    plt.close(fig)
    print(json.dumps(dict(version=args.version,epochs=[row['epoch'] for row in validation],
        observed_training_speedup=rows[0]['seconds']/rows[1]['seconds'])))


if __name__=='__main__':main()
