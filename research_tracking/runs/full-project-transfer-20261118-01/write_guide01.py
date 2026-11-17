"""Hướng dẫn một cửa cho người tiếp tục KLTN, từ registry đã nghiệm thu."""
from pathlib import Path
import csv
import html
import json
import re

B=Path(__file__).resolve().parent


def main():
    master=json.loads((B/'MANIFEST_BAN_GIAO.json').read_text(encoding='utf-8'))
    totals=master['totals']
    text=f'''# BẮT ĐẦU TẠI ĐÂY · Bàn giao toàn bộ phần việc KLTN còn lại

Cập nhật18/11/2026. Hạn nộp29/12/2026. Chủ bộ dữ liệu bàn giao là Sang. Thư mục này giữ source hiện hành, đầu vào chuẩn, cache, model, kết quả, bằng chứng và lịch sử cần để tiếp tục KLTN. Mọi bản gốc local/Drive được giữ nguyên.

## 1. Hiểu đúng trạng thái nghiên cứu

KLTN giải thích vì sao đồ thị tiên quyết chưa giúp ổn định, tìm điều kiện hiệu lực và đánh giá CG-AKT tối giản. Kết luận theo độ lớn hiệu ứng, bất định và điều kiện kiểm nghiệm; kết quả âm hoặc chưa rõ khác biệt được chấp nhận.

| Phần | Đã có | Cần tiếp tục |
|---|---|---|
| RQ1 | Chẩn đoán cơ chế của Paper1/2; benchmark dự báo Junyi expert | Khép dự báo→mastery→ready set→lựa chọn→outcome trên checkpoint fitted |
| RQ2 | Bằng chứng chẩn đoán ba bẫy: giả định simulator, năng lực chung, thứ tự luyện Junyi | Đối chứng/coverage graph noise, lịch sử, profile và khái niệm thưa dữ liệu còn thiếu |
| RQ3 | A0/A1/A2/A3 Junyi expert đủ selection/refit/calibration/outer; Grade10 có7selectedcheckpoint | SAKT/GKT main, matched GAM/Graph-GAM, Grade10 refit/calibration/closed-loop và các ablation |

Junyi sau calibration chưa phát hiện ưu thế rõ của ba graphvariants soA0 trên LogLoss/Brier sau Holm trong outerfold4 đã kiểm. Mộtfold/mộtseed; family thống kê khóa sau inference nhưng trước xem metric nên diễn giải thăm dò. Giữ nguyên số liệu và các giới hạn này.

## 2. Bố cục bộ bàn giao

```
BAT_DAU_TAI_DAY.html / .md       hướng dẫn và thứ tự tiếp tục
MANIFEST_BAN_GIAO.json           fileID, SHA, vị trí và quy tắc restore
khoi_phuc_ban_giao.py            download tiếp tục, kiểm SHA, ghép ZIPpart, restore
01_SOURCE/                     source/hồ sơ, AKT upstream Gitbundle, runtime locks
02_DU_LIEU/                    CSV gốc, canonical, split, corpus và metadata graph
03_ARTIFACTS_VA_KET_QUA/        cache chuẩn, model, calibration, outer, traces
04_LICH_SU_AUDIT/               lịch sử training/recovery đã giữ cho audit sâu
```

Tổng dữ liệu được chỉ mục là **{totals['files']}file / {totals['bytes']/1e9:.2f}GB**. Nhóm ready khoảng**{totals['ready_bytes']/1e9:.2f}GB** để tải và chạy tiếp, nhóm archive giữ lịch sử bổ sung. Mọi assets dùng fileID trong chính thư mục bàn giao này. Các URL trong manifest cũ tiếp tục giữ provenance; dùng RELOCATION_DRIVE.json để tra bản copy mới.

Source snapshot giữ bytes hiện hành tại commit gốcf016c4cd, gồm thay đổi notebook CPU đã có trên workingtree. Các wrapper/protocol được bảo toàn, source theo run và SUPPORT.zip tiếp tục đi cùng model. Môi trường Python/WSL và thông tin đăng nhập được dựng/cấp riêng cho người nhận. Một bộ cache chuẩn mỗi phase đã được giữ thay cho nhiều staged snapshot lặp.

## 3. Nhận file và khôi phục

Chủ thư mục cấp quyền đọc thư mục bàn giao mới cho tài khoản người nhận. Tải bốn file hướng dẫn này cùng requirements-tai-goi.txt, requirements-local-bo-sung.txt và SHA256SUMS.txt. Dành một thư mục download và một thư mục project mới; khôi phục lần đầu cần project trống, có thể có .venv.

### Cách tải

- Trình duyệt/Drive desktop có thể tải các folder theo nhóm, giữ cấu trúc01_SOURCE/02_DU_LIEU/03_ARTIFACTS_VA_KET_QUA/04_LICH_SU_AUDIT trong thư mục download.
- Tool hỗ trợ OAuth của người nhận và tiếp tục file.part sau gián đoạn. Access/refresh token được giữ tại auth-dir riêng, ngoài source. Dùng OAuth Desktop client riêng khi chọn cách này.

Ví dụ dưới đây dùng D:/Nhan_KLTN chứa các file hướng dẫn và D:/Dev/KLTN_tiep_quan là project mới. Chạy PowerShell, Python3.13 và Git đã có trên máy.

```powershell
py -3.13 -m venv D:\\Dev\\KLTN_tiep_quan\\.venv
D:\\Dev\\KLTN_tiep_quan\\.venv\\Scripts\\python.exe D:\\Nhan_KLTN\\khoi_phuc_ban_giao.py --manifest D:\\Nhan_KLTN\\MANIFEST_BAN_GIAO.json --downloads D:\\Nhan_KLTN\\goi --tier ready --extract --root D:\\Dev\\KLTN_tiep_quan
```

Lệnh trên dùng các file đã tải qua trình duyệt. Nếu dùng downloader OAuth, cài thư viện trong chính .venv rồi thêm --download.

```powershell
D:\\Dev\\KLTN_tiep_quan\\.venv\\Scripts\\python.exe -m pip install -r D:\\Nhan_KLTN\\requirements-tai-goi.txt
D:\\Dev\\KLTN_tiep_quan\\.venv\\Scripts\\python.exe D:\\Nhan_KLTN\\khoi_phuc_ban_giao.py --manifest D:\\Nhan_KLTN\\MANIFEST_BAN_GIAO.json --downloads D:\\Nhan_KLTN\\goi --tier ready --download --client-secret D:\\Nhan_KLTN\\private\\client_secret.json --auth-dir D:\\Nhan_KLTN\\private --extract --root D:\\Dev\\KLTN_tiep_quan
```

Khi gián đoạn, chạy lại cùng lệnh. File hoàn tất được kiểm SHA và giữ, file.part tiếp tục từ byte đã nhận. File đích khác nội dung sẽ dừng để rà. Tool ghép ba model ZIPmultipart, lưu manifest/hướng dẫn riêng theo archive, phục hồi Grade10bestcheckpoint về đường dẫn gốc và tạo AKT upstream checkout đúng commit từ Gitbundle.

Các mức tải có mục đích riêng.

| Mức | Dùng khi |
|---|---|
| core | Bắt đầu đọc kết quả/hoàn thiện Grade10; lấy source, canonical, model và outputs, chuẩn bị cache Junyi thêm khi cần |
| ready | Tiếp tục cả Junyi với cache train/selection/refit, graphcontext và confidence spool đã có; nên dành ít nhất40GB trống cho download, giải nén, .venv và output mới |
| archive | Audit sâu các lần training/recovery; tải thêm lịch sử khoảng35GB |

Thêm --extract khi muốn phục hồi cây project. Dùng cùng lệnh bỏ --extract để chỉ kiểm các file tải về. Sau restore, .handoff-restore.json giữ biên nhận và trạng thái khôi phục.

## 4. Dựng môi trường và kiểm trước khi chạy nghiên cứu

1. Vào project mới, đọc AGENTS.md, docs/REPOSITORY_MAP.md và các protocol đã adopt21/26. Source, fileCSV và split được kiểm SHA trước mọi execution.
2. WindowsCPU/Python3.13 dùng requirements-akt.lock.txt cho AKT; bổ sung requirements-local-bo-sung.txt của bộ bàn giao cho Parquet/figure/downloader, rồi cài project bằng pip install -e . trong .venv. requirements-akt.lock.txt chứa wheelWindows; LinuxGPU dùng artifacts/akt/runtime/modal-linux-cuda.lock.txt và source/runtime của run tương ứng.
3. BKT lịch sử dùng pyBKT vendored/patch theo docs/pybkt-provenance.md và runbookWSL. Giữ kết quả frozen khi đối chứng; mô tả convergence và selectionbias đã ghi. Khôi phục kết quả cached trước khi cân nhắc chạy EM lại.
4. Chạy import/preflight và kiểm tổng hợp phù hợp. Kiểm nạp checkpoint và prediction export trên workload nhỏ trước khi cấp GPU dài. Kiểm mới phải có runID/config/source/runtime/input/caps/output riêng.
5. Chỉ cài thư viện trong .venv của project. Người nhận tự đăng nhập Drive/Modal được cấp quyền. Bước bàn giao này dùng CPU/API lưu trữ, chưa chạy training hay GPU.

Lượt kiểm khôi phục của bên bàn giao được ghi tại COLD_RESTORE_ACCEPTANCE01.json và nhật ký kèm theo. Nó kiểm source/input/model layout trong thư mục mới với dependency .venv đang có. Người nhận cần nghiệm thu môi trường riêng và CUDA trước execution.

## 5. Định vị model và bằng chứng

| Nhóm | Nơi dùng sau restore |
|---|---|
| JunyiA0–A3 refit9 | experiments/akt/results/model-export-a0-refit-20261114-01 đến a3; dùng .pt + MODEL_INDEX + SUPPORT.zip |
| JunyiA0–A3 selected | model-export-a0-batch128-20261112-01, a1-batch128-20261113-01, a2/a3-batch128-20261114-01 |
| Grade10selected7 | experiments/akt/results/model-export-20261112-01/Grade10; A0 vàA1/A2/A3 × expert/learned |
| Grade10selected normal layout | experiments/akt/results/modal-main60-*; archive gốc, selected-terminal, predictions và bestcheckpoint đã có đường phục hồi |
| Confidence/learnedGrade10 | artifacts/akt/local-tests/akt-research-runner-20261108-01/method24-native01 và main60-graph-conditions02; đây là đầu vào nghiên cứu thật |
| Junyi confidence | artifacts/akt/confidence/full-train80-20261114-02; confidence.json/OOF/fitledger/SQLite theo manifest |
| BKT/GAM | experiments/bkt_baseline/results/wsl_cpp và experiments/gam_kt/results; giữ CV5/final/Test lịch sử đúng role |
| SAKT/GKT | experiments/sakt/results và experiments/gkt/results; hiện chỉ engineering10learners, main research còn thiếu |
| Outer/calibration đã chạy | experiments/akt/results/handoff-outer-20261117 và handoff-calibration; đường dẫn mới có trong manifest/relocation |
| Nguồn outer frozen | handoff-reference/frozen-outer-source-and-figures; tái lập exactsource dùng packet này và compatibility receipts |
| RQ1/RQ2 traces và figures | experiments/simulator/results, experiments/gam_kt/results/rq1-*, research_tracking/runs và reports |

Junyi và Grade10 có vocabulary khác nhau; dùng checkpoint/encoding đúng miền. Mỗi Junyi expert selected-fit thực thi12epoch, chọn9; refit9. Bảy Grade10 đã chọn5/5/4/4/4/4/4, bảy refit tương ứng tổng30epoch sau gate. Các model còn lại chọn epoch theo protocol của chúng.

A3graph-off là ablation của backboneA3. Fallback hệ thống dùng checkpointA0 độc lập. Confidence hiện hành là độ ổn định dự báo surrogate TRAIN, oracle edge truth chỉ dùng control mô phỏng có nhãn riêng.

## 6. Thứ tự tiếp tục để hoàn thành toàn KLTN

| Ưu tiên | Việc cụ thể | Bằng chứng nghiệm thu |
|---|---|---|
| H01 | Khôi phục/source/import/checkpoint/input preflight, đọc nhật ký đang mở | SHA đúng, roles/coverage và source/runtime được chốt cho run tiếp theo |
| H02 | Hoàn tất SAKT/GKT selected main trên cùng Main60; chuẩn bị matched GAM/Graph-GAM | Đủ đối chứng cùng cohort, predictions/targets/coverage và selection receipts |
| H03 | Hoàn tất candidate gate/system-selector Grade10; freeze trước mainrefit | Chín ứng viên đúng scope, selector/bootstrap theo protocol, quyết định ghi trước refit |
| H04 | Refit Grade10 theo epoch đã chọn, calibration riêng và commonreference84items | Checkpoint/optimizer/RNG/counters; raw/calibrated predictions và binding |
| H05 | Nối KT→mastery→readyset→action→outcome, controller chung | Trace đo khác biệt tại từng mắt xích, gồm trường hợp prediction đổi mà action giữ nguyên |
| H06 | Khép ba bẫy RQ1/RQ2 với control còn thiếu | Simulator version rõ, can thiệp ability/prerequisite có cặp, order/degree/chapter/support controls Junyi |
| H07 | Đánh giá vòng kín/noise/history/profile/sparseconcept theo ma trận hữu hạn đã freeze | Đơn vị suy luận đúng, effect/CI/negativecontrol, ablation confidence/gate/graph-off |
| H08 | Hoàn tất baselineJunyi và nhánh learnedJunyi theo quyết định scope đã ghi | Matched informationboundary, epochs tự chọn đúng development và artifact contract |
| H09 | Tổng hợp thống kê/figure và demo kết nối model đã nghiệm thu | SVG+CSV/source, bảng so sánh có denominator/OOV, demo phản ánh đúng mức bằng chứng |
| H10 | Viết kết quả/thảo luận/giới hạn, đối chiếu đề cương và chuẩn bị bảo vệ | Mỗi claim có nguồn, đủ deliverables/RQ và nêu rõ điều kiện kết luận |

Theo ma trận nhóm đã adopt còn21phase neural gồm6learnedJunyi,4SAKT/GKTJunyi,7refitAKTGrade10 và4SAKT/GKTGrade10. Đây là ma trận triển khai nhóm; đề cương chưa ấn định mọi tích model×graph×environment. Đề xuất hoãn learnedJunyi trước đây chưa áp dụng. Giữ nhiệm vụ trong backlog và chốt mọi điều chỉnh phạm vi trước thực thi, ưu tiên bằng chứng quyết định/vòng kín. Matched GAM/Graph-GAM, graph/confidence bổ sung, calibration và inference được hạch toán riêng.

Protocol21 giữ Hdev30; horizon final/historical500 và coveragehistory>50 cần quyết định/version rõ trước chạy. Tái dùng bằng chứng Paper1/2 và các pilot có ghi giới hạn; source/PDFPaper1 lấy PDF chính thức làm chuẩn. Những nhận định historical ở `_context` hoặc report cũ được đọc theo ngày và scope của chúng.

## 7. Ranh giới khoa học và ngân sách

- Giữ learner-disjoint splits/roles, predict-before-update, OOV/null/coverage và effective causal history. Graph/confidence dùng TRAIN80, frozen qua neural refit90 theo recipe hiện hành.
- Holdout/Test lịch sử BKT đã xem. Giữ nó ngoài modelselection, confidence, ngưỡng và simulator design. OuterJunyi hiện đã xem; sửa thiết kế từ đây cần ghi thời điểm/địa vị hậu kiểm.
- BKT/GAMCV5 là bảng lịch sử, AKTouterfold4 là protocol khác. Matched comparisons cần cùng population và giới hạn thông tin; phép tối ưu/stopping có thể khác khi được giải thích.
- Bootstrap theo learner/seedblock phù hợp; dòng tương tác trong cùng learner có phụ thuộc. Holm dùng family đã chỉ định. Bất định và kết quả âm được giữ.
- Giữ giới hạn A0 validationbatch1 lịch sử chưa replay ranking đủ12epoch bằng batch128, A3refit mixedhardware, mộtfold/mộtseed và latefamilyfreeze. ArchiveA0 đủ12epoch được bàn giao để audit khi cần.
- Modal dùng GPUH100 theo chính sách hiện hành, CPUlocal/Colab miễn phí. Mọi nguồn tiền và token được cấp riêng cho người nhận. Kiểm balance/budget ledger mới trước chạy, một GPU mỗi lúc, cap thời gian/chi phí, checkpoint và upload có xác nhận.
- Giá trị utilizationGPU hoặc p-value quan sát riêng lẻ chưa là tiêu chí hoàn thành RQ. Nghiệm thu dựa trên thiết kế đúng và bằng chứng đủ cho kết luận có giới hạn.

## 8. Tài liệu đọc theo thứ tự

1. Đề cươngPDF trong paper2, baRQ và góp ý GVHD đã ghi trong docs/thesis_recovery.
2. docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md và26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md.
3. research_tracking/supervisor_reports/2026-11-16/01_tien_do/BAO_CAO_NGHIEN_CUU.html, bản cập nhật17–18/11.
4. research_tracking/reports/SCOPE_AND_RESULT_INTEGRITY_REVIEW_20261118.md và RQ12_EXISTING_EVIDENCE_20261117.md.
5. junyi-outer-real-20261117-01/STATE.json/README.md, training-handoff-20261117-01 và full-project-handoff-audit-20261118-01.
6. docs/thesis_recovery/TASKS.json, research_tracking/CLAIM_EVIDENCE_MATRIX.md và các decision/run log; đối chiếu với trạng thái nghiệm thu mới nhất.

Các binary lớn nằm theo run trong experiments và artifacts, hồ sơ nhỏ theo run trong research_tracking. Giữ file gốc/manifest cũ, dùng relocation khi đổi vị trí. Figure cần SVG độc lập, CSV/source và cách dựng lại. Khi có kết quả mới đáng kể, cập nhật hai file báo cáo hiện hành và giữ diễn tiến nghiên cứu.
'''
    (B/'BAT_DAU_TAI_DAY.md').write_text(text,encoding='utf-8')
    body=[];table=False;code=False
    for line in text.splitlines():
        if line.startswith('```'):
            if table:body.append('</table></div>');table=False
            body.append('</code></pre>' if code else '<pre><code>');code=not code;continue
        if code:
            body.append(html.escape(line)+'\n');continue
        if line.startswith('|'):
            if not line.strip('|-: '):continue
            if not table:body.append('<div class="scroll"><table>');table=True
            body.append('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in line.strip('|').split('|'))+'</tr>');continue
        if table:body.append('</table></div>');table=False
        if not line:continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'));body.append(f'<h{level}>'+inline(line[level:].strip())+f'</h{level}>')
        else:body.append('<p>'+inline(line)+'</p>')
    page='''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bàn giao toàn KLTN · 18/11/2026</title><style>body{font:16px/1.65 Inter,system-ui,sans-serif;color:#173044;background:#f3f6f8;margin:0}main{max-width:1120px;margin:auto;padding:30px;background:#fff}h1{font-size:30px;line-height:1.3}h2{font-size:23px;margin-top:36px}h3{font-size:18px}table{border-collapse:collapse;width:100%;font-size:14px}td{padding:12px;border:1px solid #d6e0e6;vertical-align:top;min-width:110px}tr:first-child{background:#edf4f7;font-weight:650}.scroll{overflow:auto}pre{padding:18px;background:#edf3f6;overflow:auto;font-size:13px}a{color:#155b8a}@media(max-width:600px){main{padding:16px}h1{font-size:25px}}</style><main>'''+''.join(body)+'</main></html>'
    (B/'BAT_DAU_TAI_DAY.html').write_text(page,encoding='utf-8')
    relocation=[dict(original_file_id=a['source_file_id'],handoff_file_id=a['file_id'],drive_path=a['drive_path'],sha256=a['sha256']) for a in master['assets'] if 'source_file_id' in a]
    (B/'RELOCATION_DRIVE.json').write_text(json.dumps(dict(originals_preserved=True,files=relocation),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (B/'DANH_MUC_FILE.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['drive_path','role','tier','bytes','sha256','file_id','url']);writer.writeheader()
        for asset in master['assets']:writer.writerow({k:asset[k] for k in writer.fieldnames})
    print('GUIDE_AND_FILE_INDEX_WRITTEN',len(master['assets']),flush=True)


def inline(value):
    value=html.escape(value)
    value=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',value)
    return re.sub(r'`([^`]+)`',r'<code>\1</code>',value)


if __name__=='__main__':
    main()
