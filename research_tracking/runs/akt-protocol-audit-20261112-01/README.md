# Audit cấu hình và độ đầy đủ benchmark AKT — 12/11/2026

## Kết quả đã kiểm

`audit-result.json` nghiệm thu lại cả bảy selected fits bằng archive thực, không importTorch hoặc gọi cloud. Đã kiểm recipe, shared initialization, phase, learner/seed separation, fit vocabulary/support từTRAIN48, chronology,1260target mỗi model, labels so với corpus, history geometry vàepochselection. AUC, LogLoss, Brier, ECE15 vàaccuracy đã được tính lại độc lập. Bảy selectedcheckpoints dùng tiếp được cho đúng phạm vi đã ghi.

Đã kiểm train/selection/calibration không trùng người học. Plan có60người development và150người final dự kiến, tổng210seedfamily riêng cùng630streamseed riêng. Audit chỉ đọc metadata của plan, dữ liệu train/selection và hash calibration. Không đọc final events hoặc Junyi Holdout events.

`junyi-role-audit.json` đã tái dựng toàn bộ role memberships từ frozen Development assignments. Kết quả giữ nguyên126774/15847/15847/39616, identity khớp bản trước. Đã sửa lỗi phòng ngừa ở bước chuẩn hóa kiểu dữ liệu. CLI cũ épstr/int trước kiểm, có thể làmNone hoặc fold số thực thành giá trị nhìn hợp lệ. Hiện helper kiểm kiểu gốc rồi mới chuẩn hóa ID nguyên sangstring, phát hiện cả duplicate int/string ID. Đây là lỗi có thể gây sai dữ liệu đầu vào khác, chưa thấy xảy ra trên assignments đang dùng.

## Những phần chưa đạt acceptance cho benchmark đầy đủ

- Junyi có role manifest nhưng chưa có producer nghiên cứu nối80/10/10 vàCUDA. Legacyfullfold dùng90/10 rồirefit toànoutertrain, không tương đương protocol mới.
- Selected phase của Grade10 chưa là independent evaluation. Thiếu comparatorSAKT/GKT của Main vàexternalfreeze/refit/calibration.
- Prediction wrapper hiện luôn enabled=True. Core graph-off đã có kiểm, còn fitted-checkpoint graph-off/noise/gate telemetry chưa nối trọn luồng.
- BKT/GAM5fold lịch sử và protocol dành riêng calibration có phạm vi train khác nhau. Historicalreference vàmatchedfinal cần bảng riêng.
- Full Gate1994 nghiệm thu imageGrade10 đãfreeze. Những sourceJunyi mới cần nghiệm thu tương ứng trước training.

Các điểm trên là trạng thái triển khai hoặc giới hạn diễn giải. Chưa có bằng chứng buộc chạy lại bảy selectedfits vì sai split hoặc recipe.

## Các lượt kiểm và lỗi đã giữ

- `data-contract-tests.log/xml` giữ lỗi collect đầu do PYTHONPATH thiếu src, trước khi chạy test. Lượt02 dùng PYTHONPATH đúng repository.
- `data-contract-tests02.log/xml` đạt173tests và6subtests trên geometry, rolewindows, graphcontext/condition vàbộ chiaJunyi bản trước sửa kiểu.
- `junyi-type-safety-tests.log/xml` đạt9tests và11subtests sau sửa kiểu.
- `audit-fault-tests.log` đạt7tests gài lỗi recipe, epochselection, wrongrole/label/history vàmetricknownexample.
- `combined-tests.log/xml` giữ lượt cuối trên source hiện hành của các nhóm nêu trên. Không cộng số của các lượt chồng nhau thành số ca độc lập.
- `artifact-audit.log` và`audit_contracts_attempt01.py` giữ phép audit đầu nhầm tổng plan là60. Plan thực có150finalmetadatabổsung. Lượt02 đã kiểm đúng210family vàkhông đọc finalevents.

## Cách dựng lại

Mã audit thực là `audit_contracts.py`, chỉ đọc artifact và ghi báo cáo vào chính bundle. Output độc quyền không ghi đè kết quả cũ. Khi tái dựng phải dùng bản sao script/output trong một bundle hoặc local-test mới theo quy tắc repo.

Các lệnh kiểm dùng `.venv\Scripts\python.exe -B`, PYTHONPATH trỏ `src`, pytest pluginautoload tắt vàcacheprovider tắt. Lượt audit này không cấpGPU hoặc trainingNN, không sửa dataset, assignments hoặc nativeartifacts.

## Kế hoạch cấu hình và figure

[Hợp đồng benchmark KLTN](../../reports/AKT_BENCHMARK_CONTRACT_20261112.md) chốt các trường phải lưu cho predictive metrics, calibration, graph-off/noise/gate, decisiontrace vàclosedloop. Các metric response có thể tính lại từ rawp/labels đã giữ. Những metric quyết định vàlearning cần inference/evaluator riêng. Thiếu metricexport không tự có nghĩa cầntrainlại.

Người dùng xác nhận ngày12/11 rằng Junyi là phần training quan trọng và yêu cầu tiếp tục hoàn thiện toàn bộ AKT. Bước tiếp theo là nối phaseviewsJunyi đúngroles vàkiểm trước producerCUDA, rồi benchmark có boundedallocation riêng. Ưu tiên KLTN.
