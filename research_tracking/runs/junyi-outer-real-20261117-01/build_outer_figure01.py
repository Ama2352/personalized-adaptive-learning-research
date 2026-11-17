"""Figure từ kết quả outer thật, palette/quy ước figures4papers đã lưu giấy phép.

ChenLiu-1996/figures4papers e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15,
CC BY-NC4.0. Nguồn giấy phép trong bundle figures4papers-akt-20261112-01.
"""
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/akt/runtime/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    result=json.loads((B/'OUTER_COMPARISON01.json').read_text())
    models=('A0','A1','A2','A3')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
        'axes.spines.right':False,'svg.fonttype':'none','axes.formatter.useoffset':False})
    fig,axes=plt.subplots(1,2,figsize=(12.5,5.3))
    x=np.arange(4)
    for state,offset,color,label in [('raw',-.18,'#B74040','Trước hiệu chỉnh'),
            ('calibrated',.18,'#134F95','Sau hiệu chỉnh')]:
        values=[result['models'][model][state]['ece'] for model in models]
        bars=axes[0].bar(x+offset,values,width=.34,color=color,label=label)
        axes[0].bar_label(bars,fmt='%.4f',padding=4,fontsize=9)
    axes[0].set_xticks(x,models)
    axes[0].set_ylabel('ECE · độ lệch xác suất theo15nhóm')
    axes[0].set_ylim(0,max(result['models'][m]['raw']['ece'] for m in models)*1.3)
    axes[0].set_title('Xác suất sau hiệu chỉnh trên người học mới',pad=18)
    axes[0].legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.13),ncol=2,fontsize=9)
    selected=[row for row in result['comparisons'] if row['reference']=='A0'
        and row['metric']=='log_loss' and row['probabilities']=='calibrated']
    assert len(selected)==3
    for y,row in enumerate(selected):
        low,high=row['ci95']
        axes[1].hlines(y,low,high,color='#134F95',linewidth=2)
        axes[1].plot(row['estimate'],y,'o',color='#134F95',markersize=6)
    axes[1].axvline(0,color='#777777',linewidth=1,linestyle='--')
    axes[1].set_yticks(range(3),[row['candidate']+' − A0' for row in selected])
    axes[1].invert_yaxis();axes[1].set_ylim(2.6,-.6)
    axes[1].ticklabel_format(axis='x',style='sci',scilimits=(-3,3))
    axes[1].set_xlabel('Chênh lệch Log Loss sau hiệu chỉnh')
    axes[1].set_title('So sánh đồ thị với AKT không đồ thị',pad=18)
    fig.suptitle('Junyi · đánh giá độc lập A0–A3 trên cùng Development fold4',fontsize=13,y=.97)
    fig.subplots_adjust(left=.08,right=.97,top=.79,bottom=.29,wspace=.45)
    fig.text(.08,.12,'Cùng4.136.906target có dự đoán;144OOV được báo riêng. CI95% bootstrap ghép cặp theo người học,2.000lượt.',fontsize=9)
    fig.text(.08,.065,'Giá trị âm ở hình phải ứng với Log Loss thấp hơn A0. CI là khoảng biên; Holm24 và giới hạn quy trình nằm trong báo cáo.',fontsize=9)
    pins={}
    for extension in ('svg','png','pdf'):
        path=B/('outer-comparison-v01.'+extension)
        assert not path.exists()
        fig.savefig(path,dpi=150)
        pins[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    plt.close(fig)
    (B/'FIGURE_MANIFEST01.json').write_text(json.dumps(dict(
        source='OUTER_COMPARISON01.json',source_sha256=hashlib.sha256((B/'OUTER_COMPARISON01.json').read_bytes()).hexdigest(),
        figures=pins,recipe='build_outer_figure01.py; .venv Python; Matplotlib Agg; figures4papers palette/style'),indent=2)+'\n')
    print('OUTER_FIGURE_SVG_PNG_PDF_WITH_SOURCE_CREATED')

if __name__=='__main__':
    main()
