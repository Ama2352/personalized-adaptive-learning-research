# Calibration A2/A3 chuyển CPU local ngày17/11

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
