"""Figure từ bảng thống kê đã đối chiếu, p-value/CI kế thừa Paper2 frozen."""
import csv
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    cache = ROOT/'artifacts/akt/runtime/figure-cache'
    cache.mkdir(parents=True,exist_ok=True)
    os.environ['MPLCONFIGDIR'] = str(cache)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    with (HERE/'PRIMARY_PACKAGE_CONTRAST.csv').open(encoding='utf-8',newline='') as stream:
        rows = list(csv.DictReader(stream))
    panels = [('fixed_replay','log_loss','Dự báo cùng luồng','Δ Log Loss · âm có lợi'),
              ('closed_loop','mean_learning_gain','Gain học thật','Δ gain · dương có lợi'),
              ('closed_loop','retention_theta_gain','Gain giữ lại sau 14 ngày','Δ gain · dương có lợi')]
    selected = []
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
    figure,axes = plt.subplots(1,3,figsize=(12.3,4.6),layout='constrained',sharey=True)
    for axis,(protocol,metric,title,label) in zip(axes,panels):
        group = [next(row for row in rows if row['protocol']==protocol and row['metric']==metric
                      and row['persona']==persona) for persona in ('PG','PY','PYH')]
        for position,row in enumerate(group):
            delta,lower,upper = map(float,(row['recomputed_raw_delta'],row['bootstrap_ci_low'],row['bootstrap_ci_high']))
            rejected = row['reject_holm_05']=='True'
            axis.errorbar(delta,position,xerr=[[delta-lower],[upper-delta]],fmt='o',markersize=7,
                capsize=4,color='#356c80',markerfacecolor='#356c80' if rejected else 'white',
                markeredgewidth=1.5,elinewidth=1.4)
            selected.append(row)
        axis.axvline(0,color='#8c949c',linewidth=1)
        axis.set_title(title,pad=15,fontsize=12)
        axis.set_xlabel(label,labelpad=10)
        axis.spines[['top','right']].set_visible(False)
        axis.grid(axis='y',alpha=.15)
        axis.margins(x=.2)
        axis.set_yticks(range(3),['Năng lực cao','Năng lực thấp','Yếu hàm số'])
    axes[0].invert_yaxis()
    figure.suptitle('Paper2 · Graph-GAM-KT trừ GAM-KT',fontsize=15)
    figure.supxlabel('Mỗi hồ sơ có 50 seed ghép cặp. Khoảng bootstrap 95% kế thừa 3.000 draws, chưa hiệu chỉnh đa kiểm định.\n'
        'Điểm tô là contrast qua Holm trong toàn family 45 hoặc 72. Cả gói context/adaptation được so sánh.\n'
        'Mean/delta/Holm đã tính lại; Wilcoxon p-value và khoảng bootstrap được giữ từ artifact lịch sử.',fontsize=9.5)
    for suffix in ('svg','png'):
        path = HERE/f'paper2-prediction-outcome-v01.{suffix}'
        if path.exists():
            raise FileExistsError(path.name)
        figure.savefig(path,dpi=160)
    plt.close(figure)
    with (HERE/'FIGURE_DATA.csv').open('x',encoding='utf-8',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(selected[0]))
        writer.writeheader();writer.writerows(selected)
    with (HERE/'FIGURE_METADATA.json').open('x',encoding='utf-8') as stream:
        json.dump(dict(source='PRIMARY_PACKAGE_CONTRAST.csv',figure_rows=9,
            inference_unit='50 paired seeds per persona',ci='frozen95percent3000bootstrapdraws',
            multiplicity='Holm across45 replay /72 closed-loop hypotheses',
            limits_vi='Khoảng CI không phải khoảng simultaneous. Đây là kế thừa kết quả Paper2, '
            'không phải outcome checkpoint AKT hiện hành hoặc riêng tác động cạnh.'),stream,ensure_ascii=False,indent=2)


if __name__ == '__main__':
    main()
