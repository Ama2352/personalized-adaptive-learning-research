# Đối chiếu deliverables và sáu sprint từ PDF thật

Lượt này chỉ đọc đề cương PDF5trang, metadata/artifact nhỏ, source và các báo cáo được tham chiếu. Không model load, real-data replay, Holdout, GPU/cloud hoặc preview/browser. Không stage/commit theo phân công root.

## Nguồn đã đọc trực tiếp

- `paper2/DC KLTN0127 23520355&23521338_LeVanTuan.pdf`145.844byte, SHA trùng inventory do user xác nhận08/11 và file Desktop hiện tại. Đọc bằng pypdf trong `.venv`, không dựa riêng bản trích hoặc status cũ. Trang3 xác nhận models, graph conditions và metrics; trang4 xác nhận demo/giới hạn; trang5 xác nhận deliverables/sprint/article.
- SAKT `experiments/sakt/results/sakt-selected-engineering10x84-20261110-03/selected-claim.json`, GKT `experiments/gkt/results/gkt-selected-engineering10x84-20261110-01/selected-claim.json` đều SELECTED_ONLY_COMPLETE,84supported selection targets,refit_started=false. Source research_runner thực có entrypoint selected fit cho từng model.
- Grade10 A0 verification và sáu graph fits trong bundles12/11 xác nhận7conditions,selected epoch4/5,refit/calibration chưa hoàn tất. Không dùng metrics selection đó làm kết luận generalization.
- Junyi bốn refit exports9epoch đã nghiệm thu, GPU calibration metadata17/11 đủ cùng cohort. STATE ghi CPU joins đang chạy, outer evaluation còn chờ. Không đọc prediction binaries.
- Demo evidence.py ghim các trace GAM/Paper2 đã lưu; chưa có nghiệm thu demo fitted AKT mới. Có bản thảo các phần THESIS_METHODS/THESIS_RQ12 trong reports, chưa tìm thấy bằng chứng nghiệm thu luận văn toàn văn/gói bảo vệ trong phạm vi đã rà.
- RQ12_EXISTING_EVIDENCE_20261117 do agent khác vừa tổng hợp giữ các phát hiện và giới hạn, không có thí nghiệm mới. Demo/selected-statistics code và chứng nhận kỹ thuật được dùng xác định implementation progress, không nâng thành kết luận nghiên cứu.

## Chỉnh hai báo cáo hiện hành

Bảng định nghĩa/chặng lifecycle tách selected-fit, neural refit, response calibration và independent evaluation cho Junyi/Grade10. Model table giữ A0–A3 và vai trò, tránh lặp cùng câu trạng thái4lần. Bảng sáu sprint ghi rõ deliverable đã có/còn phải nghiệm thu, kèm internal links tới phần có số liệu trong report. Phần metrics giải thích mục đích LL/Brier/AUC/ECE và outcomes vòng kín trước khi đề nghị hoàn tất.

Phân loại phạm vi giữ models/conditions/statistics/demo/repro/thesis theo đề cương. BKT tham chiếu được xác minh từ PDFtr3–4. Dataset/architecture bổ sung có thể hoãn. Lược bỏ SAKT/GKT hoặc đầu ra bắt buộc cần GVHD xác nhận. Bản thảo bài báo vẫn có trong deliverablesĐC, công bố sau KLTN và phạm vi nghiệm thu cần GVHD xác nhận. Không mở submission task, không tự đòi full5fold AKT vì đề cương cho kiểm ổn định qua nhiều split hoặc bootstrap.

HTML nhúng duy nhất approvedPDF thành link tải offline, decode kiểm SHA nguyên byte. HTML229KB trước khi ghi manifest, không chứa dataset/log/credentials; prose không thêm hash hoặc path inaccessible. Không thêm folder báo cáo mới. MD có link PDF thật và internal anchors tường minh, nguồn nghiên cứu hiện hành được trỏ đúng reportRQ12.

## Kiểm và giới hạn

`check_scope_update.py` đạt PASS, tạo PROPOSAL_PDF_RECHECK06 và QA06. Kiểm PDFactual, attachment nguyên byte, models/metrics/conditions/deliverables, lifecycle,selectedartifacts,tag/ID/anchorHTML. `check_calibration_update.py` vẫn PASS bốn GPU snapshots cùng inputs/budget. `git diff --check` trên ownedfiles đạt. Figure nguồn/SVG cũ không sửa, chưa có kiểm trực quan mới.

MANIFEST06 ghim nguồn và outputs. Bản báo cáo này tiếp tục giữ CPU fit/outer/results comparison còn chờ nghiệm thu. Những kết quả GPU và code mới hỗ trợ tiến độ chuẩn bị đánh giá, không đóng RQ1/RQ2/RQ3 hoặc tạo claim CG-AKT cải thiện.
