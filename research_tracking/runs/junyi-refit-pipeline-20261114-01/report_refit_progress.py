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
    budget_review_path=HERE/'refit-remaining-budget-review.json'
    budget_review=read(budget_review_path) if budget_review_path.exists() else {}
    table=[]
    for variant,label in labels.items():
        record=progress.get('models',{}).get(variant,{})
        completed=record.get('complete_epochs',0)
        state='Đã chuẩn bị đầu vào; chờ thực thi'
        if completed:
            state=f'Đã lưu checkpoint sau {completed}/9 epoch; chờ tiếp tục'
        if record.get('partial_epoch'):
            state=f'Đã học đủ {completed}/9 epoch. Checkpoint mới nhất ở epoch {record["partial_epoch"]}, bước {record["partial_optimizer_step"]}'
        if any(variant in allocation['id'] for allocation in active):
            state=f'Đang refit; {completed}/9 epoch đã nghiệm thu trên D'
        if variant in models:
            state='Đã refit 9/9 epoch, model đã xuất trên D'
        if variant=='a3' and budget_review.get('status')=='A3_REFIT_PENDING_BUDGET':
            state='Chờ nguồn GPU phù hợp ngân sách, chưa refit'
        table.append([variant.upper(),label,state,'Còn chờ'])
    summary=f'Bước refit khởi tạo mô hình mới và học lại trên hợp nhóm huấn luyện với nhóm đã dùng chọn số epoch. Nhóm hiệu chỉnh xác suất và nhóm đánh giá độc lập tiếp tục được giữ riêng. Đến đợt cập nhật ngày 15/11, đã nghiệm thu và xuất model refit cho {len(models)}/4 phiên bản. Mỗi phiên bản đã nghiệm thu hoàn tất 9 epoch trên TRAIN90, tổng cộng 134.529.066 lượt tương tác được dùng làm mục tiêu dự báo qua 9 vòng học, với 18.360 bước cập nhật trọng số. Mỗi tương tác được dùng một lần làm mục tiêu trong mỗi epoch.'
    timing=f'Thời gian học A0 trung bình {mean(r["seconds"] for r in rows):.1f} giây/epoch, dao động {min(r["seconds"] for r in rows):.1f}–{max(r["seconds"] for r in rows):.1f} giây. Hai đợt H100 đã hoàn tất, có nối lại từ checkpoint. Các model và nhật ký đã được lưu, kiểm tra tính toàn vẹn và có checkpoint để tiếp tục khi cần.'
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
    if budget_review.get('status')=='A3_REFIT_PENDING_BUDGET':
        limit+=' A3 còn chờ bước refit vì cận cấp phát tiếp theo vượt phần ngân sách còn lại. Đã giữ đầu vào, cache và cấu hình để tiếp tục khi có nguồn GPU phù hợp.'
    elif progress['status']=='STOPPED_REQUIRES_ROOT_REVIEW' and not active:
        if 'BUDGET_ENVELOPE_REQUIRES_RECONCILIATION' in progress.get('error',''):
            limit+=' Lượt tiếp theo đang dừng để đối soát ngân sách còn lại. Checkpoint đã lưu cho phép tiếp tục từ vị trí gần nhất; chưa nghiệm thu các phiên bản còn thiếu.'
        else:
            limit+=' Tiến trình đã dừng để kiểm tra lỗi vận hành trước lượt tiếp theo. Chỉ các model đã xuất và kiểm đầy đủ mới được tính hoàn tất.'
    if progress['status']=='A3_COLAB_T4_TRANSFER_PENDING':
        limit+=' A3 đã học đủ 2 epoch và lưu thêm checkpoint ở epoch 3, bước 1.254/2.040. Credit Modal quan sát còn 0,32 USD. Hai lượt H100 đã dừng, checkpoint đã tải và kiểm trên D. Đã xác nhận Tesla T4 miễn phí trên Colab; đang chuyển gói phục hồi để tiếp tục. Chưa có epoch A3 nào được nghiệm thu trên T4. Thời gian toàn epoch trên T4 còn cần đo thực tế.'
    if progress['status']=='COLAB_RUNTIME_RECOVERY_REQUIRED':
        limit+=' Lượt Modal L4 tiếp tục từ checkpoint H100, giữ nguyên cấu hình học và tiến đến epoch 3, bước 1.883/2.040. GPU đã dừng, 70 artifact đã tải và kiểm trên D. Số dư Modal quan sát còn 0,28 USD, chưa có khoản trả thêm. Colab đã nhận đủ gói và kiểm đạt source/runtime, sau đó phiên đang nhận lệnh trong lúc chuyển checkpoint mới không còn source, cache và venv. Đang phân biệt runtime bị thay với MCP chuyển sang phiên T4 khác; chưa xác nhận file ở phiên cũ đã mất. Chưa chạy training A3 trên Colab. Checkpoint mới nhất trên D vẫn dùng được để tiếp tục, thời gian giữa H100/L4 phải diễn giải theo từng thiết bị.'
    if progress['status']=='A3_MODAL_L4_BOUNDED_EXECUTION_ACTIVE':
        limit+=' A3 đã nghiệm thu đủ 3/9 epoch, checkpoint trên D có model, optimizer và RNG để tiếp tục epoch 4. Một lượt L4 đang được thực hiện trong phần credit còn lại. Lượt trước bị watchdog dừng sau thời gian chờ cấp máy lớn, đã phục hồi và kiểm đủ checkpoint epoch 3. Controller hiện giới hạn thời gian function GPU/CPU và ngân sách riêng, đồng thời dành thời gian chờ cấp máy. Giữ nguyên source model, split, số epoch và cấu hình số học. Hướng Colab đã dừng theo yêu cầu. A3 chưa hoàn tất refit.'
    if progress['status']=='A3_H100_BUDGET_BLOCKED':
        limit+=' A3 đã nghiệm thu đủ 3/9 epoch và lưu checkpoint trên D, còn 6 epoch. Các lượt L4 đã dừng, artifact phục hồi đã kiểm. Chưa có checkpoint mới của epoch 4. Billing gần nhất còn khoảng 0,18 USD credit, chưa phát sinh khoản trả thêm; số liệu còn có điều chỉnh nên giữ cận ngân sách cũ. Theo yêu cầu, GPU tiếp theo sẽ là H100 khi có nguồn credit được cấp thêm. Lượt H100 đã có kiểm soát cần cận chi phí khoảng 0,63 USD, vượt số dư hiện tại. Checkpoint giữa epoch lưu mỗi 1.000 bước, tắt quá sớm có thể mất phần học sau checkpoint gần nhất. Hướng Colab đã dừng. Chưa hoàn tất refit A3 và chưa có kết luận đánh giá độc lập.'
    if progress['status'] in ('COLAB_DRIVE_ACCOUNT_PENDING','COLAB_PERSONAL_DRIVE_UPLOAD_PENDING',
                             'COLAB_DRIVE_INPUTS_VERIFIED_WAITING_T4'):
        limit+=' A3 đã nghiệm thu đủ 3/9 epoch, còn 6 epoch. Đang chuẩn bị Colab để tiếp tục bằng GPU miễn phí và lưu checkpoint trên Drive. Gói phục hồi gồm source, cache và checkpoint đã kiểm trên D. Cơ chế sao lưu và phục hồi đã kiểm bằng dữ liệu tổng hợp; kiểm trên Drive thật và training tiếp còn chờ. Giữ nguyên cấu hình số học, chia tập và confidence TRAIN80. Chưa có kết quả đánh giá độc lập mới.'
    if progress['status']=='COLAB_A3_SEQUENCE_RUNNING':
        a3=progress['models']['a3']
        limit+=f' A3 đang tiếp tục trên Tesla T4 miễn phí của Colab. Drive đã lưu và kiểm checkpoint sau {a3["complete_epochs"]}/9 epoch hoàn chỉnh'
        if a3.get('partial_epoch'):
            limit+=f', cùng phần đang học ở epoch {a3["partial_epoch"]}, bước {a3["partial_optimizer_step"]}/2.040'
        limit+='. Checkpoint T4 đầu tiên và 11 file nhật ký, cấu hình, metadata đã tải về ổ D và kiểm toàn vẹn. Chuỗi chạy có giới hạn thời gian, dừng khi lỗi hoặc không tiến triển, kiểm bản sao Drive sau mỗi lượt. Giữ cấu hình FP32, batch 128, seed 42, chia tập và confidence TRAIN80 như trước. A3 dùng nhiều loại GPU khi nối lại nên thời gian của nó cần báo cáo riêng. Phần này xác nhận tiến độ huấn luyện và khả năng phục hồi; kết luận hiệu quả của cơ chế đồ thị còn cần hiệu chỉnh và đánh giá độc lập.'
    figure_caption='Mỗi epoch dùng cùng 142.621 người học, 14.947.674 tương tác và 2.040 bước optimizer. FP32, batch 128, seed 42. Số liệu từ lịch sử refit A0 đã nghiệm thu.'
    if len(models)>1:
        prefix=figures/('refit-epoch-time-'+'-'.join(models)+'-v01')
        if not prefix.with_suffix('.svg').exists():
            comparison=[]
            sources={}
            for variant,index in models.items():
                source=ROOT/index['source_output']/'COMPLETE.json'
                durations=[row['resource']['wall_seconds'] for row in read(source)['history']]
                comparison.append(dict(model=variant.upper(),epochs=9,mean_epoch_seconds=mean(durations)))
                sources[variant]=dict(path=source.relative_to(ROOT).as_posix(),sha256=sha(source))
            with prefix.with_suffix('.csv').open('x',encoding='utf-8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(comparison[0]));writer.writeheader();writer.writerows(comparison)
            os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/figure_runtime/matplotlib')
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
            fig,ax=plt.subplots(figsize=(8.4,4.1));fig.subplots_adjust(left=.12,right=.97,bottom=.16,top=.82)
            bars=ax.bar([row['model'] for row in comparison],[row['mean_epoch_seconds'] for row in comparison],color='#3e7184',width=.55)
            ax.bar_label(bars,labels=[f'{row["mean_epoch_seconds"]:.1f}' for row in comparison],padding=6)
            ax.set_ylim(0,max(row['mean_epoch_seconds'] for row in comparison)*1.3)
            ax.set_ylabel('Giây / epoch');ax.set_title('Refit trên H100 — thời gian học trung bình',loc='left',pad=18)
            ax.set_axisbelow(True);ax.grid(axis='y',alpha=.18)
            fig.savefig(prefix.with_suffix('.svg'));fig.savefig(prefix.with_suffix('.png'),dpi=170);plt.close(fig)
            prefix.with_suffix('.json').write_text(json.dumps(dict(sources=sources,phase='refit90',aggregation='Trung bình đủ 9 epoch của từng model, cộng phần trước/sau resume. Không bao gồm chuẩn bị và tải artifact.',generation_script=(HERE/'report_refit_progress.py').relative_to(ROOT).as_posix(),style_reference='research_tracking/runs/figures4papers-akt-20261112-01/upstream-reference.json',files={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in [prefix.with_suffix('.svg'),prefix.with_suffix('.png'),prefix.with_suffix('.csv')]}),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        figure_caption='Trung bình đủ 9 epoch của từng model đã nghiệm thu, cùng TRAIN90 với 142.621 người học, 14.947.674 mục tiêu mỗi epoch, FP32, batch 128 và seed 42. Đây là thời gian học, các bước chuẩn bị và thu artifact được theo dõi riêng.'
    svg=prefix.with_suffix('.svg').read_text();svg=svg[svg.index('<svg'):svg.rindex('</svg>')+6]
    for identifier in sorted(set(re.findall(r'\bid="([^"]+)"',svg)),key=len,reverse=True):
        new='a0refit_'+identifier
        svg=svg.replace('id="'+identifier+'"','id="'+new+'"').replace('#'+identifier+'"','#'+new+'"').replace('url(#'+identifier+')','url(#'+new+')')
    completed_names=', '.join(v.upper() for v in models)
    heading='15/11 — '+completed_names+' hoàn tất refit'+('; tiếp tục các phiên bản còn lại' if len(models)<4 else '')
    if budget_review.get('status')=='A3_REFIT_PENDING_BUDGET':
        heading='15/11 — '+completed_names+' hoàn tất refit, A3 chờ nguồn GPU'
    section='<section id="refit-update-20261115"><h2>'+heading+'</h2>'+''.join('<p>'+escape(p)+'</p>' for p in [summary,timing])
    section+='<div class="table-scroll"><table><thead><tr>'+''.join('<th scope="col">'+c+'</th>' for c in ['Phiên bản','Thành phần','Refit TRAIN90','Hiệu chỉnh và đánh giá độc lập'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(c)+'</td>' for c in row)+'</tr>' for row in table)+'</tbody></table></div>'
    section+='<figure><div class="svg-frame">'+svg+'</div><figcaption>'+escape(figure_caption)+'</figcaption></figure><p>'+escape(limit)+'</p></section>\n'
    html=(BASE/'BAO_CAO_NGHIEN_CUU.html').read_text();html=html.replace('chốt ngày 14/11/2026','cập nhật ngày 15/11/2026').replace('ngày 14/11/2026</title>','ngày 15/11/2026</title>')
    anchor='<section id="ngan-gon">';assert anchor in html;html=html.replace(anchor,section+anchor,1)
    html=html.replace('Tiến độ chốt ngày 14/11/2026','Tiến độ đến ngày 15/11/2026').replace('2.660','2.667')
    html=html.replace('Bản chốt tiến độ ngày 14/11/2026','Bản cập nhật tiến độ ngày 15/11/2026')
    html=html.replace('Kiểm CUDA có giới hạn, dự toán chi phí còn lại rồi chạy 36 epoch refit.','A0 đã refit đủ 9 epoch; tiếp tục A1–A3 trong trần ngân sách, sau đó hiệu chỉnh và đánh giá độc lập.')
    html=html.replace('Refit dữ liệu thật vẫn chưa bắt đầu. Bước kế tiếp là kiểm tính toán CUDA có giới hạn bằng đường refit mới, rồi đối soát dự toán cho toàn bộ phần còn lại.','Tại bản chốt ngày 14/11, refit dữ liệu thật còn chờ. Trong đợt tiếp tục ngày 15/11, đã sửa và kiểm hai lỗi tích hợp ở guard đường dẫn Volume và allocator CUDA, sau đó hoàn tất refit A0 trên H100. Phần tiếp theo là học lại A1–A3 và tiếp tục đối soát ngân sách.')
    html=html.replace('Refit thật, hiệu chỉnh xác suất, so sánh độc lập và kết quả vòng kín của mô hình mới.','Hoàn tất refit A1–A3, hiệu chỉnh xác suất, so sánh độc lập và kết quả vòng kín của mô hình mới.')
    html=html.replace('<nav aria-label="Mục lục">','<nav aria-label="Mục lục"><a href="#refit-update-20261115">Refit mới nhất</a>',1)
    old_intro='Bước mới nhất là chuẩn bị xong dữ liệu và cài đặt đường học lại mô hình sau khi chọn số epoch.'
    html=html.replace(old_intro,f'Bước mới nhất là hoàn tất refit {completed_names} trên TRAIN90.')
    md=(BASE/'BAO_CAO.md').read_text().replace('ngày 14/11/2026','ngày 15/11/2026').replace('2.660','2.667')
    additions='## '+heading+'\n\n'+summary+'\n\n'+timing+'\n\n| Phiên bản | Thành phần | Refit TRAIN90 | Hiệu chỉnh và đánh giá độc lập |\n|---|---|---|---|\n'+'\n'.join('| '+' | '.join(row)+' |' for row in table)+'\n\n![Thời gian học refit](../../../runs/junyi-refit-pipeline-20261114-01/figures/'+prefix.name+'.svg)\n\n'+figure_caption+'\n\n'+limit+'\n\n'
    first=md.index('\n');md=md[:first+1]+'\n'+additions+md[first+1:]
    md=md.replace('Refit dữ liệu thật vẫn chưa bắt đầu. Bước kế tiếp là kiểm tính toán CUDA có giới hạn bằng đường refit mới, rồi đối soát dự toán cho toàn bộ phần còn lại.','Tại bản chốt ngày 14/11, refit dữ liệu thật còn chờ. Ngày 15/11 đã sửa/kiểm guard Volume và allocator CUDA, hoàn tất refit A0 trên H100. Tiếp tục A1–A3 và đối soát ngân sách.')
    md=md.replace('Kiểm CUDA có giới hạn, dự toán chi phí còn lại rồi chạy 36 epoch refit.','A0 đã refit đủ 9 epoch; tiếp tục A1–A3 và đánh giá độc lập.').replace('Refit thật, hiệu chỉnh xác suất, so sánh độc lập và kết quả vòng kín của mô hình mới.','Hoàn tất refit A1–A3, hiệu chỉnh xác suất, so sánh độc lập và kết quả vòng kín của mô hình mới.')
    md=md.replace('Tiến độ chốt ngày 15/11/2026','Tiến độ đến ngày 15/11/2026').replace(old_intro,f'Bước mới nhất là hoàn tất refit {completed_names} trên TRAIN90.')
    remaining=', '.join(variant.upper() for variant in labels if variant not in models)
    if remaining:
        html=html.replace('tiếp tục A1–A3',f'tiếp tục {remaining}').replace('Tiếp tục A1–A3',f'Tiếp tục {remaining}').replace('Hoàn tất refit A1–A3',f'Hoàn tất refit {remaining}').replace('học lại A1–A3',f'học lại {remaining}')
        md=md.replace('tiếp tục A1–A3',f'tiếp tục {remaining}').replace('Tiếp tục A1–A3',f'Tiếp tục {remaining}').replace('Hoàn tất refit A1–A3',f'Hoàn tất refit {remaining}')
    html=html.replace('bước chuẩn bị refit vừa hoàn tất',f'{len(models)} mô hình đã hoàn tất refit')
    (REPORT/'BAO_CAO_NGHIEN_CUU.html').write_bytes(html.encode())
    (REPORT/'BAO_CAO.md').write_bytes(md.encode())
    evidence=dict(status='REFIT_EXPORTED_ARTIFACTS_VERIFIED',epochs=9,targets_per_epoch=14947674,total_targets=134529066,total_steps=18360,mean_epoch_seconds=mean(r['seconds'] for r in rows),models_exported=list(models),loop_status=progress['status'],reports=REPORT.relative_to(ROOT).as_posix(),source_complete_sha256=sha(ROOT/'experiments/akt/results/junyi-a0-refit-20261114-01/COMPLETE.json'))
    (HERE/'refit-report-20261115-state.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence,ensure_ascii=False))

if __name__=='__main__':main()
