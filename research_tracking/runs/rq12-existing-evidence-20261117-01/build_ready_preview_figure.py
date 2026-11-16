"""Dựng bảng chéo ready/gợi ý từ CSV đã kiểm, giữ SVG và PNG độc lập."""
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR'] = str(ROOT/'artifacts/figure_runtime/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def main():
    prefix = HERE/'rq1-ready-preview-v01'
    assert not prefix.with_suffix('.svg').exists() and not prefix.with_suffix('.png').exists()
    source = HERE/'rq1_conditionals.csv'
    with source.open(encoding='utf-8',newline='') as stream:
        rows = {r['changed']:r for r in csv.DictReader(stream) if r['variable']=='ready_set'}
    assert rows['True']['preview_changed']=='5' and rows['False']['preview_changed']=='17'
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none',
                         'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    figure, axis = plt.subplots(figsize=(8.8,4.9))
    try:
        figure.subplots_adjust(left=.02,right=.98,bottom=.06,top=.88)
        axis.set(xlim=(0,1),ylim=(0,1));axis.axis('off')
        figure.suptitle('Đổi tập đủ điều kiện có đi cùng đổi gợi ý?',fontsize=16,x=.5,y=.96)
        axis.text(.45,.88,'Gợi ý đổi',ha='center',va='center',fontsize=13,color='#0F4D92')
        axis.text(.79,.88,'Gợi ý giữ',ha='center',va='center',fontsize=13,color='#394B59')
        for row_index, flag in enumerate(('True','False')):
            row=rows[flag];y=.55-row_index*.30
            label='Tập đủ điều kiện đổi' if flag=='True' else 'Tập đủ điều kiện giữ'
            denominator=int(row['snapshots'])
            axis.text(.265,y+.125,f'{label}\n{denominator:,} cặp'.replace(',','.'),
                      ha='right',va='center',fontsize=11.5,linespacing=1.7)
            for column,field in enumerate(('preview_changed','preview_unchanged')):
                x=.30+column*.34;count=int(row[field])
                axis.add_patch(Rectangle((x,y),.30,.25,facecolor='#E9F2F7' if column==0 else '#F0F2F4',
                                         edgecolor='#B8C6D0',linewidth=1))
                axis.text(x+.15,y+.155,f'{count:,}'.replace(',','.'),ha='center',va='center',
                          fontsize=24,color='#0F4D92' if column==0 else '#394B59')
                percentage=f'{100*count/denominator:.1f}'.replace('.',',')
                axis.text(x+.15,y+.065,percentage+'% trong hàng',ha='center',va='center',fontsize=10.5)
        axis.text(.30,.105,'1.080 cặp snapshot pilot · 9 cụm seed–hồ sơ',fontsize=10,ha='left')
        axis.text(.30,.035,'Các ô mô tả đồng biến cùng thời điểm.',fontsize=10,ha='left')
        figure.savefig(prefix.with_suffix('.svg'),metadata={'Creator':'KLTN, quy ước figures4papers của Chen Liu'})
        figure.savefig(prefix.with_suffix('.png'),dpi=180)
    finally:
        plt.close(figure)
    metadata=dict(source=source.relative_to(ROOT).as_posix(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        values=[[5,55],[17,1003]],row_denominators=[60,1020],snapshots=1080,clusters=9,
        caption_vi='Bảng chéo của pilot graph package và baseline GAM trên cùng snapshot; gợi ý là concept preview trong replay.',
        limitations_vi='Đồng biến mô tả, chưa phải trung gian nhân quả hoặc kết quả học vòng kín.',
        rebuild=' .venv/Scripts/python.exe -B research_tracking/runs/rq12-existing-evidence-20261117-01/build_ready_preview_figure.py',
        style_reference='research_tracking/runs/figures4papers-akt-20261112-01/upstream-reference.json',
        style_upstream_commit='e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15',license='CC BY-NC 4.0',
        style_implementation_vi='Dựng bằng Matplotlib với quy ước SVG text/font và bố cục của figures4papers như các figure AKT hiện hành.')
    prefix.with_suffix('.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='FIGURE_CREATED',svg=str(prefix.with_suffix('.svg')),png=str(prefix.with_suffix('.png')))))


if __name__=='__main__':
    main()
