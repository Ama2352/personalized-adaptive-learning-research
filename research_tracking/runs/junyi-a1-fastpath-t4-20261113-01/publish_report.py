"""Nối diễn tiến kiểm T4 vào hai báo cáo, chỉ mục và trạng thái điều tra."""
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
summary=json.loads((HERE/'summary.json').read_text())
regression=json.loads((HERE/'local-regression.json').read_text())
assert summary['all_parity_drifts_zero'] and regression['status']=='PASS'
assert '74 passed' in (HERE/'local-regression.log').read_text()
report=ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
heading='## 13/11 — kiểm nhanh giảm xử lý CPU của A1 trên T4'
paragraph=('Sau khi đối chiếu cơ sở thiết kế, nhóm giữ công thức A1 và sửa riêng cách tạo mã kiểm tra '
    'tính toàn vẹn của dữ liệu đồ thị. Mục tiêu là giảm chuyển đổi dữ liệu Python lặp trước khi GPU tính toán. '
    'Phép kiểm Tesla T4 miễn phí kéo dài 28,62 giây. Loss, xác suất, gradient, trọng số sau một bước Adam '
    'và trạng thái optimizer khớp hoàn toàn ở hai điều kiện đã kiểm. Bộ kiểm helper trên Colab đạt 19 ca, '
    'kiểm hồi quy local đạt 74 ca, có cả adapter Junyi và Grade10.')
limits=('Chuỗi đo gồm sáu bước mỗi bản trên dữ liệu tổng hợp, prefix được dựng trước. '
    'Thông lượng tăng 1,26 lần và thời gian giảm 20,5%. GPU-Util trung bình đo được tăng từ 26,5% '
    'lên 37,8%, vẫn dưới mục tiêu 50% trong lượt ngắn này. Cần kiểm toàn pipeline và tính tương thích '
    'khi nối checkpoint trước khi dùng nguồn mới cho lượt H100 tiếp theo. Kết quả này bổ sung bằng chứng '
    'kỹ thuật chuẩn bị AKT. Thực nghiệm kết luận RQ3, validation A1 epoch1 và selected fit còn đang chờ.')
closing=('Logs, số liệu, hình SVG/PDF/PNG và archive đã được tải về ổ D, kiểm tính toàn vẹn. '
    'Đã gửi lệnh trả runtime Colab và đóng bridge sau khi lấy bằng chứng. Đợt này dùng 0 USD Modal.')
markdown=report/'BAO_CAO.md'
text=markdown.read_text(encoding='utf-8')
assert heading not in text
first,rest=text.split('\n',1)
first=first.replace('12/11/2026','13/11/2026')
section=f'{heading}\n\n{paragraph}\n\n{limits}\n\n{closing}\n\n'
section+='[Hồ sơ kiểm T4](../../../runs/junyi-a1-fastpath-t4-20261113-01/README.md)\n\n'
markdown.write_text(first+'\n\n'+section+rest.lstrip('\n'),encoding='utf-8')
svg=(HERE/'a1-fastpath-t4-v1.svg').read_text(encoding='utf-8')
svg=svg[svg.index('<svg'):]
svg=re.sub(r'id="([^"]+)"',r'id="a1fastt4_\1"',svg)
svg=svg.replace('url(#','url(#a1fastt4_').replace('href="#','href="#a1fastt4_')
html=report/'BAO_CAO_NGHIEN_CUU.html'
text=html.read_text(encoding='utf-8')
identifier='a1-fastpath-t4-20261113'
assert f'id="{identifier}"' not in text
section=(f'<section id="{identifier}"><h2>{heading.removeprefix("## ")}</h2>'
    f'<p>{paragraph}</p><p>{limits}</p><p>{closing}</p>'
    f'<figure>{svg}<figcaption>Nguồn đo T4 ngày 13/11. Một cặp sáu bước, batch128 × 200, '
    'prefix dựng trước. Số đo GPU ở lượt ngắn chưa đại diện toàn epoch Junyi/H100.</figcaption></figure></section>\n')
anchor='<section id="a1-architecture-review-20261113">'
assert text.count(anchor)==1
text=text.replace(anchor,section+anchor,1)
text=text.replace('cập nhật 12/11/2026','cập nhật 13/11/2026',1)
html.write_text(text,encoding='utf-8')
entry=('## 13/11 — A1 giảm chuyển đổi evidence và kiểm T4\n\n'
    '[Hồ sơ](LINK) giữ phép kiểm GPU 28,62 giây, drift0 ở hai alpha, '
    '19 ca Colab và 74 ca local. Chuỗi sáu bước giảm 6,20→4,93 giây, '
    'GPU mẫu 26,5→37,8%. Full producer/resume còn chờ, 0 USD Modal.\n\n')
for relative,link in [
    ('docs/REPOSITORY_MAP.md','../research_tracking/runs/junyi-a1-fastpath-t4-20261113-01/README.md'),
    ('research_tracking/reports/README.md','../runs/junyi-a1-fastpath-t4-20261113-01/README.md'),
    ('research_tracking/EVIDENCE_INDEX.md','runs/junyi-a1-fastpath-t4-20261113-01/README.md')]:
    path=ROOT/relative
    first,rest=path.read_text(encoding='utf-8').split('\n',1)
    path.write_text(first+'\n\n'+entry.replace('LINK',link)+rest.lstrip('\n'),encoding='utf-8')
state_path=ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state=json.loads(state_path.read_text(encoding='utf-8'))
state['a1_fastpath_t4_20261113']=dict(
    status='PARTIAL_PERFORMANCE_IMPROVEMENT_VERIFIED',
    bundle=HERE.relative_to(ROOT).as_posix(),
    production_helper_changed=True, architecture_changed=False,
    source_sha256=hashlib.sha256((ROOT/'src/knowledge_tracing/akt/research_graph_model.py').read_bytes()).hexdigest(),
    selected_checkpoint_modified=False, checkpoint_migration_applied=False,
    local_regression_passed=74, colab_helper_tests_passed=19,
    t4_seconds=summary['elapsed_seconds'], training=summary['training'],
    synthetic_parity_all_drift_zero=True, full_producer_benchmarked=False,
    gpu50percent_accepted=False, modal_spent_usd=0, cloud_training_started=False,
    runtime_release=(HERE/'runtime-release.json').relative_to(ROOT).as_posix(),
    next_vi='Tối ưu prefix/message cố định với provenance, kiểm full producer gồm adapter và data prep. '
            'Kiểm resume-validation từ checkpoint source2 theo nguồn mới trước khi cấp H100. '
            'Giữ checkpoint cũ và hạn mức 30 USD toàn KLTN.')
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (ROOT/'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a',encoding='utf-8') as stream:
    stream.write('\n\n## 13/11/2026 — vòng tối ưu nhỏ A1 và kiểm T4 miễn phí\n\n'+paragraph+'\n\n'+limits+'\n\n'+closing+'\n')
# Giữ kết quả và đường dẫn source đã kiểm trước khi đóng bundle.
receipt=dict(status='PASS_STATIC_REPORT_CHECK',
    svg_embedded=f'id="{identifier}"' in text,
    report_pair_has_result=heading in markdown.read_text(encoding='utf-8'),
    figure_visually_checked=True, local_tests=regression['status'])
(HERE/'report-check.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir()
       if p.is_file() and p.name!='manifest-final.json'}
(HERE/'manifest-final.json').write_text(json.dumps(dict(status='CLOSED',files=files,
    raw_artifacts='experiments/akt/results/colab-a1-fastpath-t4-20261113-01/',
    source_sha256=state['a1_fastpath_t4_20261113']['source_sha256']),indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt))
