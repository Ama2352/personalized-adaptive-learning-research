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
