# Calibration A2/A3 chuyển CPU local ngày17/11

Mốc mới nhất. A2 đã fit và được đọc lại độc lập từ Drive Sang, biên nhận `LOCAL_A2_FIT_ACCEPTANCE100.json` trong bundle thực thi. Calibration đạt3/4 ở phạm vi Junyi fold4. TemperatureA2=1,0295325171, LogLoss trên chínhcohortfit0,3584482535→0,3583105009. Phải chờ nhóm đánh giá độc lập để so sánh mô hình. LượtA2 cógiánđoạnhost, wall77,35phút không được dùng kết luận hiệu năngCPU. Các đoạn sau giữ diễn tiến kỹ thuật.

Theo yêu cầu sử dụng CPU máy cá nhân, cache tạm tối đa4GB đặt tại `artifacts/akt/local-calibration/20261117`. Kết quả chính tiếp tục lưu trên Drive Sang. Cache sau khôi phục đầu vào và snapshot A2 chiếm546.461.091byte.

## Đã xác nhận

- Đầu vào source/model, numeric A2/A3 và metadata window đã kiểm SHA. Biên nhận `research_tracking/runs/junyi-calibration-real-20261117-01/LOCAL_CALIBRATION_INPUTS01.json`.
- Snapshot A2 giữ1.278.474dự đoán của12.439người học, đã sao lưu và kiểm SHA trên Drive. Khôi phục12.440file gồm manifest và các shard vào cache, kiểm từng file. Biên nhận `LOCAL_A2_SNAPSHOT01.json` cùng bundle.
- Tiến trình Colab đã dừng, access token tạm đã xóa, runtime CPU đã trả. Biên nhận `COLAB_LOCAL_MIGRATION_STOP01.json` và `COLAB_RELEASE_AFTER_MIGRATION01.json`.
- Adapter fit SQLite giữ nguyên thuật toán temperature V1, thứ tự và digest target. Kiểm lại26ca tổng hợp đạt6,48giây tại `research_tracking/runs/local-calibration-migration-20261117-02/tests-root03.txt`. Có kiểm resume, target trùng/thiếu và parity toàn payload.

## Đang thực hiện và giới hạn

Lượt A2 local attempt100 tiếp tục join/audit từ snapshot đã đóng. Nguồn KT frozen được giữ nguyên trong cache riêng, relocation chỉ tạo metadata dẫn xuất. Log `research_tracking/runs/junyi-calibration-real-20261117-01/local-a2-join100.txt`.

Calibration được nghiệm thu vẫn2/4model, tương ứng A0/A1. A2/A3 chỉ được tính hoàn thành sau khi fit đầy đủ, đọc lại output trên Drive và đối chiếu binding, số target và SHA. Đánh giá outer độc lập vẫn0/4. Lượt này chưa tạo kết luận so sánh mới hoặc tiêu thụ Modal.

Sau nghiệm thu Drive sẽ ghi inventory và dọn cache theo quyền đã cấp. SQLite không được đưa vào gói kết quả chính.

## Khôi phục lỗi ghi manifest A3

Lượt A3 attempt100 gặp `WinError5` khi thay manifest. Phép kiểm `WINDOWS_SHARE_PROBE01.json` xác nhận reader thông thường đang mở file có thể gây đúng lỗi này, và thay file thành công ngay sau đóng reader. Vì vậy việc theo dõi đã chuyển sang log và metadata kích thước, tránh đọc manifest đang được ghi. Đây là cơ chế gây lỗi đã tái hiện, chưa xác định độc lập tiến trình giữ handle đúng thời điểm lỗi thật.

Adapter bổ sung retry có giới hạn0,05/0,1/0,2/0,4giây cho lỗi Windows5/32/33, theo lịch sẵn có trong `src/knowledge_tracing/akt/runner.py`. Serializer gốc và nguồn KT frozen giữ nguyên. Có31kiểm thử đạt10,37giây, gồm ca mở reader thật trên Windows rồi đóng để kiểm retry. Log `TESTS_LOCAL_RETRY_GREEN02.txt` giữ trong bundle thực thi. Lỗi quyền tồn tại sau năm lần gọi tiếp tục được trả ra.

Toàn bộ file của attempt100 được giữ. Snapshot phục hồi chỉ dùng shard được manifest liệt kê, kiểm SHA từng file. File chưa được manifest xác nhận được liệt kê riêng, tiếp tục giữ tại output lỗi. Metadata relocation phiên bản mới đặt theo SHA adapter để giữ hồ sơ phiên bản trước.

## Biểu diễn gọn đã kiểm trên toàn cohort A2

`COMPACT_A2_FULL_PARITY100.json` xác nhận1.621.484record giữ nguyên nội dung và thứ tự khi gom15.847Parquet thành50shard, mỗi shard tối đa32.768row. Thời gian552,52giây bao gồm đọc nguồn, dựng lại và kiểm publicreader. File nguồn giữ nguyên; bản compact dùng riêng sau khi cóCOMPLETE và lineage khớp. Fit lưu cả manifest compact và hồ sơ nguồn trong metadata trên Drive.

`THIN_LOGITS_A2_FULL_PARITY100.json` tái tính nguyên solver V1 trên bảng29.327.360byte từ database A2 đã đóng1.155.735.552byte, bằng attachread-only. Toàn payload và identity calibrator khớp exact kết quả đã nghiệm thu, gồm69lần tính mục tiêu. Lượt kiểm mất417,63giây, sampledpeak khoảng36,4MiB. Thời gian này đo bước kiểm solver với biểu diễn hẹp. Lượt fit A2 trước có gián đoạn host nên hai số không tạo phép so tốc độ end-to-end có kiểm soát.

Nguồn solver V1, quy tắcclip, bounds và thuật toán tìm hệ số được giữ. Chỉ bảng trung gian dùng đọc lặp được thu gọn.43kiểm thử fitter/join/compact/lineage đạt30,83giây trong `TESTS_THIN_COMPACT_LINEAGE_GREEN01.txt`. A3 được đưa qua cùng kiểm stream trước khi fit với biểu diễn mới.
