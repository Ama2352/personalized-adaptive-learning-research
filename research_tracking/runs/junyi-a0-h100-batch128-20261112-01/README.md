# A0 Junyi batch128 trênH100

Người dùng yêu cầu chạyH100 choA0 và chọnbatch128 trực tiếp, không benchmark batch riêng. Lượt mới từseed42, protocol akt-nr-exercise-v2-batch128. Giữ optimizer/lr/split/window/FP32/early stopping như cũ, chỉ batch và hardware đổi theo yêu cầu. Sáu epochbatch4 giữ làm lịch sử riêng. Không coi lịch sử batch4 là epoch của lượtbatch128. Các model so sánh sau cần cùng công thức batch128.

TRAIN80 126.774learner/13.347.331target, selection10 15.847learner/1.600.343target, 717exercise, không calibration/outer-validation/Holdout. Tối đa20epoch, patience3,min_delta0,0001. Batch128 tạo1.818update/epoch trên232.662window, tối đa36.360update.

Kiểm nguồn và cấu hình trênCPU trướcGPU. Không có lượt benchmarkGPU riêng. Training thật theo dõi GPU/VRAM/throughput/loss và checkpoint. NếuOOM hoặc sai input dừng, giữ log. Đặt trầnA0selected đợt đầu3USD trong trần toànKLTN30USD và vẫn chừa ngân sách cho phần còn lại. Phầnrefit/calibration cần đầu vào cùng công thức đã đóng băng và được theo dõi riêng.

Người dùng bổ sung yêu cầu lưu rồi ngắt ngay khi lượt training thành công. Controller kết thúcApp vàguard dừng đúngApp trước bước tảiarchive vềlocal. Checkpoint đãsync theo COMPLETE marker trong lúc train. Cuối lượt kiểm SHA và0container, không giữGPU để đọc báo cáo hoặc tải file.

Đã chuẩn bị prepare_resume.py vàresume_worker.py cho cùng logicalrun nếu tranche đầu hết giới hạn trước early stopping. Chỉ nối sau receipt/archive/SHA và stopack đã đạt, dùng source/data/config/profile giống hệt, giữ toàn checkpoint epoch và checkpoint mới nhất. Không thay batch giữa lượt và không tự khởi động lại từđầu. Tối đa hai lần nối sau lượt đầu, mỗi lần phải cóallocation riêng trong trần toànKLTN30USD. Hiện chưa dispatch lần nối.

## Snapshot hai epoch đầu

A0 không đồ thị đã được đưa lên H100 với batch128, khởi tạo từ seed42 và dùng toàn bộ tập train Junyi đã chốt. Hai epoch đầu đã hoàn tất training, validation và lưu checkpoint. Mỗi epoch học 13,35 triệu lượt và kiểm dự báo trên 1,60 triệu lượt selection, đủ toàn bộ đối tượng dự kiến và 0 OOV.

Để chọn thời điểm dừng, theo dõi mức sai lệch giữa xác suất dự báo và đáp án trên tập selection. Log Loss giảm từ0,3600 xuống0,3569 sau hai epoch, cho thấy mô hình đang học được trên cấu hình mới. Kết quả này phục vụ chọn checkpoint. Đánh giá độc lập, refit và calibration còn ở các bước tiếp theo.

Training mất khoảng2phút mỗi epoch, validation thêm khoảng3phút12giây. So với lịch sửT4 batch4 khoảng31phút cho cả chu kỳ, lượtH100 batch128 hiện khoảng5phút10giây. Đây là thay đổi đồng thời phần cứng vàbatch. Lịch sử sáu epoch batch4 được lưu riêng, bảng mới đếm từ epoch1 của lượtbatch128. GPU tiếp tục chạy các epoch theo early stopping và được dừng sau khi xuất bằng chứng bền vững.

Nguồn epoch01-snapshot.json vàepoch02-snapshot.json đọc CPU từcheckpoint đãcomplete trongcontainer. Figurea0-h100-progress-epoch002v2 cóSVG/PDF/PNG/CSV, dựng bằngbuild_progress_figure.py. Bản đầu của hình được giữ, v2 nới khoảngtrụcX để tránh nhãn đè. Chưa đóngbundle vìGPU còntrain.

## Đợt1 đã nghiệm thu, tiếp tụcđợt2

Đã hoàn tất5epoch/9.090updates/66.736.655targetexposures. Có20checkpoint, archive531.888.179byte SHA361b76fb3f242455fcc4767a6450a96be7bfa2b903ad130205b9c10198e39589 trênD. H100 đãdừng,0container được xác nhận độc lập. Credits snapshot còn24,74USD, tăng1,98USD so trướcH100. LogLoss selection1–5 là0,360011/0,356920/0,355758/0,355607/0,354815. Besttạm5,stale0, chưachốtselected. Đợt2 giữsource/data/config/profile/identity, phục hồi đúngepoch5 rồi bắtđầu6. DùngH100! đểgiữ kiếntrúcGPU, tránh auto-upgrade ảnhhưởng kiểm probability SHA giữa cácđợt. Trần3USD đợt2, không benchmark.

## Đợt2 đã nghiệm thu, tiếp tụcđợt3

Đã hoàn tất10epoch/18.180updates/133.473.310targetexposures,25checkpoint trongarchive664.386.641byte SHA5416e45fe827bf45787a678694029da539aeaa92c1032202c3a914d8eb8f4cf4 trênD. App02đãstopped và0container được xác nhận. Tổngcredits snapshot7,45USD, còn22,55USD. Epoch7 tăngloss nhưng8/9 lại giảm, besttheomin_deltaở9/LL0,353580;10LL0,353560 chỉgiảm0,000020nênstale1. Đợt3nối10vàbắtđầu11, trần3USD, chưađổiđiềukiệndừng.

Giới hạn kế hoạch nối được cập nhật theo số đo thực tế5epoch/tranche. Đểbao hết trần20epochcần tốiđa4execution thaycho dự tính3banđầu. Chỉnối khi chưaearlystop, archive/stop đãkiểm vàledger trong30USDchophép. Không mở sẵn cácGPUtiếp theo. Đây là sửa dự tính vận hành, không đổi20/patience3/min_delta hay dữliệu.


## Nghiệm thu cuối và báo cáo riêng ngày 13/11

A0 không đồ thị trên Junyi đã hoàn tất 12 epoch H100 batch128 và chọn checkpoint epoch 9 theo patience 3, min_delta 0,0001. Mỗi epoch có 13.347.331 target train và 1.600.343 target selection, 0 OOV. Đã tải và kiểm ba archive, nạp lại checkpoint được chọn, xuất đủ dự báo và model chính về D. Cả ba App đã dừng, snapshot server ghi 0 container.

Log Loss selection của checkpoint được chọn là 0,353580, AUC 0,805990, Brier 0,107700 và ECE 0,004270. Đây là tập dùng chọn epoch, đánh giá độc lập và so sánh chính thức với BKT/GAM-KT còn ở bước tiếp theo. Refit90 và calibration chưa thực hiện. Training trung bình 2 phút 03 giây và validation 3 phút 18 giây/epoch. Telemetry toàn quá trình xử lý ghi GPU trung bình 26,49%, cao nhất 74%, VRAM cao nhất 5.793 MiB. Còn dư địa tối ưu validation.

Ba phiên H100 ghi credits tăng khoảng 5,39 USD, tổng KLTN đã dùng 8,67 USD và còn 21,33 USD tại snapshot cuối, billed 0 USD. Mọi lần tiếp tục cần dự toán trong phần ngân sách còn lại.

Model chính ở `experiments/akt/results/model-export-a0-batch128-20261112-01/`, có một `.pt` cùng SUPPORT, MODEL_INDEX và README. Báo cáo tự chứa ở `research_tracking/supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html`. Dựng lại bằng `build_training_report.py`, số liệu từ epoch12-analysis-input/selection-metrics/resource-summary và các verification/billing/stop-confirmation. Figure cuối final012v2 giữ SVG/PDF/PNG/CSV cùng script.

Đối soát ledger giữ bản trước thay đổi và toàn bộ reservation lịch sử trong closed_reservations, giải phóng cap đã đóng để tránh tính trùng với metered usage. Không thay đổi trần 30 USD, cấm trả thêm và dự phòng 3 USD. Cận trên kế toán 9,002 USD giữ lớn hơn snapshot meter 8,679 USD. Không cấp job mới trong gói làm báo cáo.


## Kiểm báo cáo và đóng bundle

Đã kiểm tự động số liệu, model SHA, số dự báo, 12 epoch, App stopped và bố cục ngữ cảnh trước cập nhật. Đã xem figure cuối cùng, screenshot desktop 1440px và khung hẹp 600px. Chrome kiểm thử đã kết thúc, không tạo preview server. Lượt Chrome đầu trong môi trường hạn chế lỗi Crashpad; chạy lại với quyền mở Chrome cục bộ thành công. Screenshot 390px bị giới hạn viewport tối thiểu của Chrome headless nên không dùng làm kiểm mobile đạt, ảnh gốc vẫn giữ. Không xác nhận kiểm thiết bị di động thực. report-check.json ghi hai viewport đã nghiệm thu. Các script Python trong bundle đã parse cú pháp. Không chạy thêm training hoặc đọc Holdout.

Bundle đóng sau FINAL_MANIFEST.json. Mọi cập nhật tiếp theo dùng bundle mới và tham chiếu hồ sơ này, không sửa bằng chứng đã đóng.
