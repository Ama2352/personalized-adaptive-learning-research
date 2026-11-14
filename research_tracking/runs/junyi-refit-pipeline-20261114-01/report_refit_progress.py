"""Cập nhật hai file GVHD theo model refit đã xuất; giữ figure/CSV/provenance riêng."""
import csv
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
from statistics import mean

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
REPORT=ROOT/'research_tracking/supervisor_reports/2026-11-15/01_tien_do'
BASE=ROOT/'research_tracking/supervisor_reports/2026-11-14/01_tien_do'

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    models={}
    for variant in ('a0','a1','a2','a3'):
        path=ROOT/f'experiments/akt/results/model-export-{variant}-refit-20261114-01/MODEL_INDEX.json'
        if path.exists():
            index=read(path);assert index['phase']=='refit90' and index['epochs']==9
            checkpoint=path.parent/index['checkpoint_file'];assert sha(checkpoint)==index['checkpoint_sha256']
            models[variant]=index
    assert 'a0' in models
    complete=read(ROOT/'experiments/akt/results/junyi-a0-refit-20261114-01/COMPLETE.json')
    rows=[dict(epoch=r['epoch'],seconds=r['resource']['wall_seconds'],optimizer_steps=r['optimizer_steps'],targets=r['valid_targets']) for r in complete['history']]
    assert len(rows)==9 and all(r['targets']==14947674 and r['optimizer_steps']==2040 for r in rows)
    figures=HERE/'figures';figures.mkdir(exist_ok=True)
    prefix=figures/'a0-refit-training-time-v01'
    if not prefix.with_suffix('.svg').exists():
        with prefix.with_suffix('.csv').open('x',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/figure_runtime/matplotlib')
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
        fig,ax=plt.subplots(figsize=(8.4,4.1));fig.subplots_adjust(left=.12,right=.97,bottom=.17,top=.84)
        bars=ax.bar([r['epoch'] for r in rows],[r['seconds'] for r in rows],color='#3e7184',width=.64)
        ax.bar_label(bars,labels=[str(round(r['seconds'])) for r in rows],padding=4,fontsize=10)
        ax.set_xticks(range(1,10));ax.set_ylim(0,165);ax.set_xlabel('Epoch');ax.set_ylabel('Thời gian học (giây)')
        ax.set_title('A0 refit trên H100 — thời gian học từng epoch',loc='left',pad=18)
        ax.set_axisbelow(True);ax.grid(axis='y',alpha=.18)
        fig.savefig(prefix.with_suffix('.svg'));fig.savefig(prefix.with_suffix('.png'),dpi=170);plt.close(fig)
        source=ROOT/'experiments/akt/results/junyi-a0-refit-20261114-01/COMPLETE.json'
        prefix.with_suffix('.json').write_text(json.dumps(dict(source=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),phase='refit90',population_targets_per_epoch=14947674,style_reference='research_tracking/runs/figures4papers-akt-20261112-01/upstream-reference.json',style_upstream_commit='e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15',license='CC BY-NC 4.0',generation_script=(HERE/'report_refit_progress.py').relative_to(ROOT).as_posix(),files={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in [prefix.with_suffix('.svg'),prefix.with_suffix('.png'),prefix.with_suffix('.csv')]}),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    labels=dict(a0='AKT không đồ thị',a1='Đồ thị cố định',a2='Độ tin cậy cạnh',a3='Độ tin cậy cạnh và cổng')
    active=read(ROOT/'research_tracking/COMPUTE_BUDGET.json')['new_allocations']
    progress=read(HERE/'refit-loop-progress.json')
    table=[]
    for variant,label in labels.items():
        record=progress.get('models',{}).get(variant,{})
        completed=record.get('complete_epochs',0)
        state='Đã chuẩn bị đầu vào; chờ thực thi'
        if completed:
            state=f'Đã lưu checkpoint sau {completed}/9 epoch; chờ tiếp tục'
        if any(variant in allocation['id'] for allocation in active):
            state=f'Đang refit; {completed}/9 epoch đã nghiệm thu trên D'
        if variant in models:
            state='Đã refit 9/9 epoch, model đã xuất trên D'
        table.append([variant.upper(),label,state,'Còn chờ'])
    summary=f'Bước refit khởi tạo mô hình mới và học lại trên hợp nhóm huấn luyện với nhóm đã dùng chọn số epoch. Nhóm hiệu chỉnh xác suất và nhóm đánh giá độc lập tiếp tục được giữ riêng. Đến đợt cập nhật ngày 15/11, đã nghiệm thu và xuất model refit cho {len(models)}/4 phiên bản. A0 hoàn tất 9 epoch trên TRAIN90, tổng cộng 134.529.066 lượt tương tác được dùng làm mục tiêu dự báo qua 9 vòng học, với 18.360 bước cập nhật trọng số. Mỗi tương tác được dùng một lần làm mục tiêu trong mỗi epoch.'
    timing=f'Thời gian học A0 trung bình {mean(r["seconds"] for r in rows):.1f} giây/epoch, dao động {min(r["seconds"] for r in rows):.1f}–{max(r["seconds"] for r in rows):.1f} giây. Hai đợt H100 đã hoàn tất, có nối lại từ checkpoint. Toàn bộ artifact đã tải về D và kiểm inventory; gói xuất gọn có checkpoint 9, optimizer, nguồn ngẫu nhiên, cấu hình và mã hóa bài tập.'
    additional_times=[]
    for variant,index in models.items():
        if variant=='a0':
            continue
        history=read(ROOT/index['source_output']/'COMPLETE.json')['history']
        assert len(history)==9
        assert all(row['valid_targets']==14947674 and row['optimizer_steps']==2040 for row in history)
        additional_times.append(f'{variant.upper()} trung bình {mean(row["resource"]["wall_seconds"] for row in history):.1f} giây/epoch')
    if additional_times:
        timing+=' Các phiên bản refit tiếp theo đã nghiệm thu trên cùng quần thể và số bước cập nhật. '+ '. '.join(additional_times)+'.'
    limit='Đây là hoàn tất bước học lại mô hình theo số epoch đã chọn. Hiệu chỉnh xác suất, xuất dự đoán trên nhóm đánh giá độc lập và kết luận hiệu quả đồ thị còn chờ. Thời gian trong biểu đồ là thời gian học từng epoch, gồm phần tích lũy khi nối lại; thời gian chuẩn bị, tải artifact và tổng thời gian sử dụng function được theo dõi riêng.'
    if progress['status']=='STOPPED_REQUIRES_ROOT_REVIEW' and not active:
        if 'BUDGET_ENVELOPE_REQUIRES_RECONCILIATION' in progress.get('error',''):
            limit+=' Lượt tiếp theo đang dừng để đối soát ngân sách còn lại. Checkpoint đã lưu cho phép tiếp tục từ vị trí gần nhất; chưa nghiệm thu các phiên bản còn thiếu.'
        else:
            limit+=' Tiến trình đã dừng để kiểm tra lỗi vận hành trước lượt tiếp theo. Chỉ các model đã xuất và kiểm đầy đủ mới được tính hoàn tất.'
    svg=prefix.with_suffix('.svg').read_text();svg=svg[svg.index('<svg'):svg.rindex('</svg>')+6]
    for identifier in sorted(set(re.findall(r'\bid="([^"]+)"',svg)),key=len,reverse=True):
        new='a0refit_'+identifier
        svg=svg.replace('id="'+identifier+'"','id="'+new+'"').replace('#'+identifier+'"','#'+new+'"').replace('url(#'+identifier+')','url(#'+new+')')
    completed_names=', '.join(v.upper() for v in models)
    heading='15/11 — '+completed_names+' hoàn tất refit'+('; tiếp tục các phiên bản còn lại' if len(models)<4 else '')
    section='<section id="refit-update-20261115"><h2>'+heading+'</h2>'+''.join('<p>'+escape(p)+'</p>' for p in [summary,timing])
    section+='<div class="table-scroll"><table><thead><tr>'+''.join('<th scope="col">'+c+'</th>' for c in ['Phiên bản','Thành phần','Refit TRAIN90','Hiệu chỉnh và đánh giá độc lập'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(c)+'</td>' for c in row)+'</tr>' for row in table)+'</tbody></table></div>'
    section+='<figure><div class="svg-frame">'+svg+'</div><figcaption>Mỗi epoch dùng cùng 142.621 người học, 14.947.674 tương tác và 2.040 bước optimizer. FP32, batch 128, seed 42. Số liệu từ lịch sử refit A0 đã nghiệm thu.</figcaption></figure><p>'+escape(limit)+'</p></section>\n'
    html=(BASE/'BAO_CAO_NGHIEN_CUU.html').read_text();html=html.replace('chốt ngày 14/11/2026','cập nhật ngày 15/11/2026').replace('ngày 14/11/2026</title>','ngày 15/11/2026</title>')
    anchor='<section id="ngan-gon">';assert anchor in html;html=html.replace(anchor,section+anchor,1)
    html=html.replace('Tiến độ chốt ngày 14/11/2026','Tiến độ đến ngày 15/11/2026').replace('2.660','2.667')
    html=html.replace('Bản chốt tiến độ ngày 14/11/2026','Bản cập nhật tiến độ ngày 15/11/2026')
    html=html.replace('Kiểm CUDA có giới hạn, dự toán chi phí còn lại rồi chạy 36 epoch refit.','A0 đã refit đủ 9 epoch; tiếp tục A1–A3 trong trần ngân sách, sau đó hiệu chỉnh và đánh giá độc lập.')
    html=html.replace('Refit dữ liệu thật vẫn chưa bắt đầu. Bước kế tiếp là kiểm tính toán CUDA có giới hạn bằng đường refit mới, rồi đối soát dự toán cho toàn bộ phần còn lại.','Tại bản chốt ngày 14/11, refit dữ liệu thật còn chờ. Trong đợt tiếp tục ngày 15/11, đã sửa và kiểm hai lỗi tích hợp ở guard đường dẫn Volume và allocator CUDA, sau đó hoàn tất refit A0 trên H100. Phần tiếp theo là học lại A1–A3 và tiếp tục đối soát ngân sách.')
    html=html.replace('Refit thật, hiệu chỉnh xác suất, so sánh độc lập và kết quả vòng kín của mô hình mới.','Hoàn tất refit A1–A3, hiệu chỉnh xác suất, so sánh độc lập và kết quả vòng kín của mô hình mới.')
    html=html.replace('<nav aria-label="Mục lục">','<nav aria-label="Mục lục"><a href="#refit-update-20261115">Refit mới nhất</a>',1)
    old_intro='Bước mới nhất là chuẩn bị xong dữ liệu và cài đặt đường học lại mô hình sau khi chọn số epoch.'
    html=html.replace(old_intro,'Bước mới nhất là hoàn tất refit A0 trên TRAIN90 và tiếp tục các biến thể đồ thị theo cùng protocol.')
    md=(BASE/'BAO_CAO.md').read_text().replace('ngày 14/11/2026','ngày 15/11/2026').replace('2.660','2.667')
    additions='## '+heading+'\n\n'+summary+'\n\n'+timing+'\n\n| Phiên bản | Thành phần | Refit TRAIN90 | Hiệu chỉnh và đánh giá độc lập |\n|---|---|---|---|\n'+'\n'.join('| '+' | '.join(row)+' |' for row in table)+'\n\n![Thời gian học A0 refit](../../../runs/junyi-refit-pipeline-20261114-01/figures/a0-refit-training-time-v01.svg)\n\n'+limit+'\n\n'
    first=md.index('\n');md=md[:first+1]+'\n'+additions+md[first+1:]
    md=md.replace('Refit dữ liệu thật vẫn chưa bắt đầu. Bước kế tiếp là kiểm tính toán CUDA có giới hạn bằng đường refit mới, rồi đối soát dự toán cho toàn bộ phần còn lại.','Tại bản chốt ngày 14/11, refit dữ liệu thật còn chờ. Ngày 15/11 đã sửa/kiểm guard Volume và allocator CUDA, hoàn tất refit A0 trên H100. Tiếp tục A1–A3 và đối soát ngân sách.')
    md=md.replace('Kiểm CUDA có giới hạn, dự toán chi phí còn lại rồi chạy 36 epoch refit.','A0 đã refit đủ 9 epoch; tiếp tục A1–A3 và đánh giá độc lập.').replace('Refit thật, hiệu chỉnh xác suất, so sánh độc lập và kết quả vòng kín của mô hình mới.','Hoàn tất refit A1–A3, hiệu chỉnh xác suất, so sánh độc lập và kết quả vòng kín của mô hình mới.')
    md=md.replace('Tiến độ chốt ngày 15/11/2026','Tiến độ đến ngày 15/11/2026').replace(old_intro,'Bước mới nhất là hoàn tất refit A0 trên TRAIN90 và tiếp tục các biến thể đồ thị theo cùng protocol.')
    remaining=', '.join(variant.upper() for variant in labels if variant not in models)
    if remaining:
        html=html.replace('tiếp tục A1–A3',f'tiếp tục {remaining}').replace('Tiếp tục A1–A3',f'Tiếp tục {remaining}').replace('Hoàn tất refit A1–A3',f'Hoàn tất refit {remaining}').replace('học lại A1–A3',f'học lại {remaining}')
        md=md.replace('tiếp tục A1–A3',f'tiếp tục {remaining}').replace('Tiếp tục A1–A3',f'Tiếp tục {remaining}').replace('Hoàn tất refit A1–A3',f'Hoàn tất refit {remaining}')
    (REPORT/'BAO_CAO_NGHIEN_CUU.html').write_bytes(html.encode())
    (REPORT/'BAO_CAO.md').write_bytes(md.encode())
    evidence=dict(status='REFIT_EXPORTED_ARTIFACTS_VERIFIED',epochs=9,targets_per_epoch=14947674,total_targets=134529066,total_steps=18360,mean_epoch_seconds=mean(r['seconds'] for r in rows),models_exported=list(models),loop_status=progress['status'],reports=REPORT.relative_to(ROOT).as_posix(),source_complete_sha256=sha(ROOT/'experiments/akt/results/junyi-a0-refit-20261114-01/COMPLETE.json'))
    (HERE/'refit-report-20261115-state.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence,ensure_ascii=False))

if __name__=='__main__':main()
