"""Dựng chỉ mục bàn giao từ inventory đã kiểm và biên nhận Drive thực."""
from pathlib import Path
import html
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
B = Path(__file__).resolve().parent
REPORT = ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'

ROWS = [
    ('BKT · Junyi', 'CV5 gồm 3.537 lượt fit theo exercise/fold; refit cuối 720 exercise',
     '720 .pkl; hệ số CV trong cv.json; prediction Parquet; manifest, log, metric và Test lịch sử',
     'Giữ baseline lịch sử. Test đã được truy cập từ trước; không dùng để chọn model mới.'),
    ('GAM-KT · Junyi', 'CV5 hoàn tất; 5 bộ difficulty theo fold',
     'difficulty.parquet/json; prediction Parquet, coverage, bảng metric, log và so sánh BKT',
     'Chưa xác nhận refit cuối/Test. Fit matched theo protocol mới còn thiếu.'),
    ('Graph-GAM-KT · Paper2', 'Có source online và bảng kết quả đã đóng băng',
     'Gói Paper2 gốc, cấu hình, kết quả replay/vòng kín và thống kê đã lưu',
     'Chưa tìm thấy checkpoint offline độc lập. Cần lifecycle matched hiện hành.'),
    ('AKT · Junyi expert', 'A0–A3 đủ chọn epoch, refit, calibration và outer fold4',
     '4 checkpoint selected + 4 refit .pt; SUPPORT/config; 4 calibrator; dự đoán raw/calibrated, metric, bootstrap/Holm, telemetry và figure',
     'Mỗi model chạy 12 epoch selection, chọn epoch9 rồi refit9. Tổng84 epoch đã thực thi cho bốn điều kiện này. Một fold, một seed.'),
    ('AKT · Grade10', '7 checkpoint selected; epoch chọn 5/5/4/4/4/4/4',
     'A0; A1/A2/A3 × expert/learned, .pt + index + support/config',
     'Chưa refit/calibration/đánh giá vòng kín chính. Bảy refit sẽ dùng tổng30 epoch đã chọn, sau khi đủ gate chung.'),
    ('SAKT · Grade10 engineering', '6 epoch, chọn epoch1 trên cohort10 người học',
     'state.pt, selected-terminal, epoch logs, selection predictions và coverage',
     'Chưa là baseline nghiên cứu Main60 hoặc Junyi. Không tính lượt nhỏ này là đã xong model đối chứng.'),
    ('GKT · Grade10 engineering', '11 epoch, chọn epoch6 trên cùng cohort10 người học',
     'state.pt, selected-terminal, epoch logs, selection predictions và coverage',
     'Main60 và Junyi còn thiếu. Là biến thể theo phương trình gốc, chưa chứng nhận khớp code tác giả.'),
    ('Confidence cạnh · Junyi TRAIN80', 'Đã fit 976 cạnh; 708 có support, 268 thiếu support',
     'confidence.json, COMPLETE, identity, fit-manifest, phiên bản runtime, OOF, child fit ledger và log',
     'Score ổn định dự báo có điều kiện. OOF/fit ledger giữ để audit; SQLite đầu vào phái sinh giữ local và có manifest tái dựng.'),
    ('Paper1 · Grade10', 'Source mô phỏng và kết quả công bố làm nền RQ1/RQ2',
     'Notebook tiền kết quả và PDF chính thức; Elo cập nhật online',
     'PDF là nguồn chuẩn. Không tính đây là checkpoint neural offline.'),
]

SCOPE = '''## Phạm vi training còn lại theo protocol hiện hành

Đối chiếu Protocol21 đã adopt và bảng rà phạm vi15/11. Có **15/36 phase neural chính đã có bằng chứng** gồm8phase Junyi expert và7selected Grade10. Một phase là selected-fit hoặc refit; số này không đo phần trăm hoàn thành RQ hay toàn KLTN.

| Phần còn thiếu | Phase selected-fit/refit | Mục đích nghiên cứu |
|---|---:|---|
| Junyi learned-graph A1/A2/A3 |6|Kiểm kết luận có phụ thuộc cách xây đồ thị từ dữ liệu hay không; predictive evidence có giới hạn thứ tự luyện quan sát|
| Junyi SAKT/GKT |4|Đối chứng KT bổ sung theo đề cương, cùng ranh giới thông tin|
| Grade10 bảy điều kiện AKT đã chọn |7|Tạo bản refit cho calibration, quyết định lộ trình và vòng kín trên môi trường biết cạnh thật/nhiễu|
| Grade10 SAKT/GKT main |4|Hoàn tất đối chứng cùng cohort và gate đầy đủ trước refit/evaluation chính|
| Tổng |**21**|Chưa gồm matched GAM/Graph-GAM, ước lượng graph/confidence bổ sung, calibration và inference|

Đề xuất hoãn sáu phase Junyi learned-graph trong báo cáo15/11 **chưa được áp dụng**. Nhận định trước rằng chỉ còn Grade10 là hết AKT thiếu phần này. Giữ đầy đủ nghĩa vụ hiện hành trong bàn giao. Gate chọn chung chín ứng viên Grade10 còn cần SAKT/GKT main trên cohort phù hợp. Không tự lấy engineering10 thay main60.
'''


def main():
    catalog = json.loads((B/'TRAINING_OUTPUTS_CATALOG_DRAFT01.json').read_text(encoding='utf-8'))
    folder_file = B/'DRIVE_FOLDER01.json'
    folder = json.loads(folder_file.read_text(encoding='utf-8')) if folder_file.exists() else None
    receipt_file = B/'NEW_ARCHIVES_DRIVE01.json'
    receipt = json.loads(receipt_file.read_text(encoding='utf-8')) if receipt_file.exists() else {}
    extra=B/'CONFIDENCE_ARCHIVES_DRIVE01.json'
    if extra.exists():
        receipt.setdefault('files',[]).extend(json.loads(extra.read_text(encoding='utf-8'))['files'])
    base = 'https://drive.google.com/drive/folders/'
    md = '''# Bàn giao đầu ra training KLTN · 17/11/2026

## Đọc trước

Đã có model và kết quả đánh giá độc lập cho bốn điều kiện AKT Junyi expert. Kết quả này hỗ trợ phân tích dự báo của RQ1/RQ3. Hoàn thành RQ3 còn cần quyết định học và vòng kín Grade10. Các đối chứng còn lại vẫn được giữ theo protocol.

Kết quả hiện tại chưa phát hiện ưu thế rõ của các bản graph sau calibration trên Junyi outerfold4. Kết luận được giới hạn theo population và thiết kế đã kiểm, với độ bất định trình bày bên dưới.

Mở các ZIP từ thư mục gốc của bản checkout để giữ đường dẫn repository. Mỗi ZIP mới có HANDOFF_MEMBER_INVENTORY.json, ghi đường dẫn, dung lượng và SHA-256 từng file. Bộ nhận cần kiểm SHA trước sử dụng. Dùng .venv riêng, nạp .pt/.pkl chỉ khi tin cậy nguồn. Giữ nguyên outputs cũ và tạo run mới cho phần tiếp tục.

## Toàn bộ nhóm đầu ra đã định vị

| Nhóm | Đã thực hiện | File bàn giao | Giới hạn/phần tiếp tục |
|---|---|---|---|
'''
    for row in ROWS:
        md += '|'+ '|'.join(row)+'|\n'
    md += '\n## AKT hiện tại đóng góp gì cho ba RQ?\n\n'
    md += '''- **RQ1.** Junyi cho thấy lợi ích dự báo của đồ thị rất nhỏ. Sau calibration, ba bản graph so với A0 chưa có cải thiện Log Loss/Brier đáng tin cậy sau Holm. Cần tiếp chuỗi ngưỡng mastery → ready set → chọn bài → kết quả học để xác định nơi ảnh hưởng bị mất.
- **RQ2.** Các chẩn đoán Paper1/2 đã kiểm ba bẫy đánh giá. Bốn model expert hiện tại bổ sung benchmark một điều kiện graph; chưa bao phủ đủ chất lượng đồ thị, lịch sử, profile và thưa dữ liệu. Sensitivity/noise trên checkpoint cố định có thể thực hiện trước khi cân nhắc training thêm.
- **RQ3.** A0 không graph, A1 graph cố định, A2 confidence từng cạnh, A3 confidence+cổng đã so sánh dự báo độc lập. A3 so A0 sau calibration có ΔLogLoss≈−0,000020, CI95% chứa0; chưa kết luận tốt hơn. Chưa có kết luận chính về ổn định, quyết định lộ trình và vòng kín. Bằng chứng âm được giữ nguyên.

Các kết quả outer dùng39.616 người học/4.137.050 target,144 OOV giữ null, cùng population mỗi model. Phân tích thống kê được khóa family sau inference nhưng trước xem metric outer; báo exploratory, mộtfold/mộtseed. Không quy kết cải thiện học thực từ log quan sát.

'''
    md += SCOPE
    md += '''
## Ưu tiên tính đúng của kết quả

Rà phạm vi ngày18/11 xác nhận các hướng nghiên cứu chính tiếp tục bám baRQ. Mục tiêu nghiệm thu là phép so sánh đúng, đủ đối chứng và artifact để báo cáo. Kết quả âm hoặc bất định được giữ. Outer Junyi đã xem, mọi thiết kế thay đổi từ đây cần ghi thời điểm và địa vị hậu kiểm/thăm dò.

Mỗi RQ được kết luận theo mức độ bằng chứng, độ lớn hiệu ứng, bất định và điều kiện áp dụng. Có thể kết luận hỗ trợ một phần, chưa thấy khác biệt rõ hoặc cần thêm bằng chứng. P-value và dấu hiệu ứng là những phần của diễn giải cùng cơ chế và đối chứng.

Con số21phase là backlog theo ma trận triển khai nhóm đã adopt. Đề cương chưa bắt buộc tích đầy đủ mọi model×graph×environment. Nhánh learnedJunyi còn giữ trong backlog, đề xuất giảm phạm vi chưa áp dụng. Ưu tiên nghiên cứu là khép chuỗi mastery→chọn bài→vòng kín Grade10 và ba bẫy, cùng các đối chứng yêu cầu; các tối ưu tài nguyên bổ sung cần có lợi ích cụ thể đối với lượt thực nghiệm cần thiết.

Các giới hạn phải bàn giao gồm A0 validation batch1 lịch sử chưa replay ranking đủ12epoch, A3 refit mixed hardware, mộtfold/mộtseed và family thống kê khóa sau inference nhưng trước xem metric. Hồ sơ chi tiết nằm ở SCOPE_AND_RESULT_INTEGRITY_REVIEW_20261118.md trong gói bằng chứng. Kết quả hiện hành chưa chứng minh tương đương model, hiệu quả dạy học thực hoặc nguyên nhân duy nhất của việc graph chưa giúp.
'''
    md += '''
## Kết quả dự báo đã có

BKT/GAM là trung bìnhCV5 lịch sử; AKT là một outerfold4 với partition/refit hiện hành. Hai bảng phục vụ định vị bằng chứng; chưa dùng chênh lệch giữa hai protocol làm kết luận xếp hạng cùng điều kiện.

| Baseline lịch sử | AUC | Log Loss | Brier |
|---|---:|---:|---:|
|BKT CV5|0,783413|0,375607|0,115105|
|GAM-KT CV5 supported|0,774866|0,394881|0,120372|

| Junyi outer sau calibration | AUC | Log Loss | Brier |
|---|---:|---:|---:|
'''
    for model, value in catalog['groups']['AKT_JUNYI']['outer']['models'].items():
        m = value['calibrated']
        md += f"|{model}|{m['auc']:.6f}|{m['log_loss']:.6f}|{m['brier']:.6f}|\n"
    md += '\n## Tải đầu ra và bằng chứng\n\n'
    links = [
        ('Thư mục gốc KLTN trên Drive Sang', base+'1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7'),
        ('Model AKT selected/refit, Grade10, audit và helper nối các phần ZIP', base+'1--Q-yO2ja7q2RwWWfyv6nDtw80PDrnyZ'),
        ('Junyi outer A0–A3, raw/calibrated predictions, source đã pin, calibrator và figure', base+'1-GKHCBGtqFLiL-Zi84onLbLHl_iR0Fk-'),
        ('Lịch sử training/recovery đã sao lưu và kiểm SHA trước dọn local', base+'1V-H0estsyh2oQQ3qnfapU9qSpGZFoF3H'),
    ]
    if folder:
        links.insert(1, ('Gói bàn giao toàn bộ nhóm model bổ sung và chỉ mục hiện hành', folder['webViewLink']))
    for label, url in links:
        md += f'- [{label}]({url})\n'
    md += '\nCác ZIP AKT lớn đã chia phần. Dùng DRIVE_PARTS_MANIFEST.json và restore_drive_zips.py trong thư mục backup để nối và kiểm checksum trước giải nén. Bản A0_BEST_SO_FAR epoch5 là lịch sử bị thay thế, không chọn lại làm model chính. Dùng Junyi refit9 cho calibration/outer, selected9 để truy vết chọn epoch. Junyi và Grade10 có vocabulary khác nhau, cần checkpoint tương ứng.\n\n'
    md += '| Archive mới | File thành viên | Byte nguồn | Byte ZIP | Trạng thái |\n|---|---:|---:|---:|---|\n'
    for item in receipt.get('files', []):
        md += f"|[{item['name']}]({item['webViewLink']})|{item['member_count']}|{item['source_bytes']:,}|{int(item['size']):,}|SHA256 Drive khớp|\n"
    md += '''
## Những gì người tiếp tục cần chuẩn bị

1. Checkout source và đọc AGENTS.md, docs/REPOSITORY_MAP.md, Protocol21/Recipe26. Gói SOURCE_PROTOCOLS giữ source đang dùng, cấu hình và tests. Frozen-source trong gói outer giữ bản thực thi chính xác của outer; phải dùng source đó khi tái lập outer.
2. Giải nén model kèm SUPPORT.zip, MODEL_INDEX và calibration tương ứng. Các chỉ mục trong bộ hồ sơ định vị graph, encoding, roles và run nguồn. Không dùng .pt đơn lẻ rồi tự dựng vocabulary khác.
3. Muốn train tiếp phải có canonical Junyi, learner assignments và graph inputs đúng SHA theo manifests. Gói này bàn giao **đầu ra training**. Dataset gốc, SQLite/cache trung gian và môi trường .venv không được nhân bản trong đợt này; người nhận cần chuyển dữ liệu đầu vào hợp lệ riêng hoặc tái dựng theo pipeline rồi kiểm SHA. Không gọi gói này là bản sao toàn project có thể chạy ngay khi chưa nghiệm thu data dependencies.
4. Tài khoản Modal/OAuth, token và quyền Drive được cấp riêng cho người nhận. Chủ Drive cần chia sẻ thư mục gốc KLTN cho người tiếp tục để truy cập cả model backup, outer và gói mới. Các URL được kiểm bằng tài khoản chủ Sang; chưa kiểm quyền bằng tài khoản người nhận.
5. Ưu tiên hoàn tất gate/main comparator Grade10, refit/calibration rồi chạy chuỗi quyết định/vòng kín. Giữ matched GAM/Graph-GAM và nghĩa vụ learnedJunyi trong backlog. Mỗi lượt mới pin đầu vào/source/budget trước chạy; CPU local/miễn phí, GPU chỉ dùng khi cần.

## Nguồn đối chiếu

- docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md và26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md.
- docs/bkt-baseline-results.md; cv_cpp/cv/cv.json; final_cpp/final.json.
- experiments/gam_kt/results/wsl_cpp/cv/cv.json vàreport_vi.md.
- MODEL_INDEX các model-export; baseline-evaluation-readiness-20261117-01/EXISTING_ARTIFACTS.json.
- junyi-outer-real-20261117-01/OUTER_COMPARISON01.json, thống kê/Drive acceptance; TRAINING_SCOPE_RECONCILIATION_20261115.md.
- PACKAGE_INVENTORY01.json và NEW_ARCHIVES_DRIVE01.json là inventory/biên nhận của đợt này.
'''
    (B/'README.md').write_text(md, encoding='utf-8')
    # HTML tĩnh tự chứa, giữ bảng cuộn ngang trên điện thoại; không phụ thuộc CDN.
    lines = md.splitlines(); body=[]; table=False; listing=False
    for line in lines:
        if line.startswith('|'):
            if set(line.replace('|','').replace('-','').replace(':','').replace(' ',''))==set():
                continue
            cells=line.strip('|').split('|')
            if not table:
                body.append('<div class="scroll"><table>'); table=True
            body.append('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in cells)+'</tr>')
            continue
        if table:
            body.append('</table></div>'); table=False
        if not line:
            continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'))
            body.append(f'<h{level}>'+inline(line[level:].strip())+f'</h{level}>')
        else:
            body.append('<p>'+inline(line)+'</p>')
    if table:
        body.append('</table></div>')
    page='''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bàn giao kết quả training KLTN · 17/11</title><style>body{font:16px/1.65 system-ui,sans-serif;color:#172b3a;background:#f5f7fa;margin:0}main{max-width:1120px;margin:auto;background:white;padding:32px}h1{font-size:30px}h2{font-size:23px;margin-top:36px}table{border-collapse:collapse;width:100%;font-size:14px}td{padding:12px;border:1px solid #d9e1e8;vertical-align:top;min-width:100px}tr:first-child{font-weight:650;background:#edf3f6}.scroll{overflow-x:auto}a{color:#155a86}p{margin:12px 0}@media(max-width:600px){main{padding:18px}h1{font-size:25px}}</style><main>'''+''.join(body)+'</main></html>'
    (B/'BAN_GIAO_TRAINING.html').write_text(page, encoding='utf-8')
    if '--update-report' in sys.argv:
        update_report()
    print('HANDOFF_REPORT_WRITTEN', len(ROWS), 'groups', len(receipt.get('files', [])), 'archives')


def inline(value):
    import re
    text=html.escape(value)
    text=re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)', r'<a href="\2">\1</a>', text)
    return re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)


def update_report():
    marker='## 17/11 — Đối chiếu lại toàn bộ phần training còn lại'
    path=REPORT/'BAO_CAO.md'; text=path.read_text(encoding='utf-8')
    if marker not in text:
        text=text.replace('<a id="history"></a>', marker+'\n\n'+SCOPE.split('\n',1)[1]+'\n<a id="history"></a>', 1)
        path.write_text(text, encoding='utf-8')
    audit_marker='## 18/11 — Nghiệm thu theo tính đúng của bằng chứng'
    path=REPORT/'BAO_CAO.md'; text=path.read_text(encoding='utf-8')
    if audit_marker not in text:
        section='''## 18/11 — Nghiệm thu theo tính đúng của bằng chứng

Kết quả âm hoặc chưa rõ khác biệt được giữ làm kết quả nghiên cứu. Outer Junyi hiện tại chưa phát hiện ưu thế rõ của graph sau calibration trên các so sánh LogLoss/Brier đã hiệu chỉnh Holm. Kết luận còn có điều kiện mộtfold/mộtseed. Phần tiếp tục ưu tiên phép đo ngưỡng mastery, thay đổi lựa chọn và vòng kín Grade10 cùng ba bẫy đánh giá.

Con số21phase còn lại là ma trận triển khai của nhóm; đề cương chưa ấn định tích đầy đủ mọi model×graph×environment. Đề xuất hoãn learnedJunyi chưa áp dụng. SAKT/GKT và matched GAM/Graph-GAM tiếp tục là đối chứng cần theo dõi. Mỗi lượt bổ sung cần có câu hỏi còn thiếu và đầu ra sử dụng trong luận văn.

Giới hạn phương pháp gồm A0 selection theo validation batch1 lịch sử chưa replay ranking đủ12epoch, A3 refit mixed hardware và family thống kê khóa sau inference nhưng trước xem metric. Outer đã xem, thiết kế thay đổi từ đây cần ghi là hậu kiểm/thăm dò. Hồ sơ rà phạm vi và liêm chính kết quả ngày18/11 được lưu trong gói bàn giao.

'''
        text=text.replace('<a id="history"></a>',section+'<a id="history"></a>',1)
        path.write_text(text,encoding='utf-8')
    path=REPORT/'BAO_CAO_NGHIEN_CUU.html'; text=path.read_text(encoding='utf-8')
    marker='id="training-scope-reconciled-20261117"'
    if marker not in text:
        section='''<section id="training-scope-reconciled-20261117"><h2>17/11 — Đối chiếu phần training còn lại</h2><p>Đã khép8phase fit/refit Junyi expert A0–A3 và có7selected checkpoint Grade10, tổng15/36phase neural chính của protocol hiện hành. Mốc này chưa quy đổi thành phần trăm hoàn tất nghiên cứu.</p><div class="table-wrap"><table><thead><tr><th>Còn thiếu</th><th>Phase</th><th>Mục đích</th></tr></thead><tbody><tr><td>Junyi learned-graph A1–A3</td><td>6</td><td>Kiểm phụ thuộc vào cách xây đồ thị từ dữ liệu</td></tr><tr><td>Junyi SAKT/GKT</td><td>4</td><td>Đối chứng KT theo đề cương</td></tr><tr><td>Grade10 bảy refit AKT</td><td>7</td><td>Chuẩn bị quyết định lộ trình và vòng kín</td></tr><tr><td>Grade10 SAKT/GKT main</td><td>4</td><td>Đối chứng cùng cohort và gate chung</td></tr></tbody></table></div><p>Tổng còn21phase selected-fit/refit theo Protocol21. Chưa gồm matched GAM/Graph-GAM, calibration và inference. Nhánh learned-Junyi từng được đề xuất hoãn, đề xuất chưa áp dụng. Vì vậy nhận định trước rằng chỉ còn Grade10 là hết AKT đã thiếu phạm vi này. Engineering SAKT/GKT trên10người học chưa thay được baseline main60; gate đầy đủ chín ứng viên Grade10 còn phải hoàn tất.</p></section>'''
        text=text.replace('<h2>Quá trình nghiên cứu đến hiện tại</h2>', section+'<h2>Quá trình nghiên cứu đến hiện tại</h2>', 1)
        path.write_text(text, encoding='utf-8')
    path=REPORT/'BAO_CAO_NGHIEN_CUU.html'; text=path.read_text(encoding='utf-8')
    if 'id="result-integrity-review-20261118"' not in text:
        section='''<section id="result-integrity-review-20261118"><h2>18/11 — Nghiệm thu theo tính đúng của bằng chứng</h2><p>Kết quả âm hoặc chưa rõ khác biệt được giữ làm kết quả nghiên cứu. Outer Junyi hiện tại chưa phát hiện ưu thế rõ của graph sau calibration trên các so sánh LogLoss/Brier đã hiệu chỉnh Holm, trong giới hạn mộtfold/mộtseed. Phần tiếp tục ưu tiên ngưỡng mastery, thay đổi lựa chọn và vòng kín Grade10 cùng ba bẫy đánh giá.</p><p>Con số21phase là ma trận triển khai nhóm. Đề cương chưa ấn định tích đầy đủ mọi model×graph×environment. Đề xuất hoãn learnedJunyi chưa áp dụng; các đối chứng SAKT/GKT và matched GAM/Graph-GAM tiếp tục được theo dõi. Mỗi lượt bổ sung cần chỉ rõ câu hỏi còn thiếu và đầu ra sử dụng trong luận văn.</p><p>Giới hạn cần giữ gồm A0 selection dùng validation batch1 lịch sử chưa replay ranking đủ12epoch, A3 refit mixed hardware và family thống kê khóa sau inference nhưng trước xem metric. Outer đã xem; mọi thiết kế thay đổi từ đây cần ghi thời điểm và địa vị hậu kiểm/thăm dò.</p></section>'''
        text=text.replace('<h2>Quá trình nghiên cứu đến hiện tại</h2>',section+'<h2>Quá trình nghiên cứu đến hiện tại</h2>',1)
        path.write_text(text,encoding='utf-8')


if __name__=='__main__':
    main()
