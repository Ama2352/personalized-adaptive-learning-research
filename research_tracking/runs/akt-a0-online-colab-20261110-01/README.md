# Checkpoint A0 nghiên cứu sang dự báo tuần tự

## Phần đã hoàn thiện

`src/knowledge_tracing/akt/research_a0_online.py` cung cấp `load_research_a0_online`. Hàm nhận checkpoint complete-epoch A0 đã ghim SHA, encoding nghiên cứu và ngân hàng bài cùng miền. Hàm tái dùng bộ kiểm checkpoint, AKTAdapter và AKTOnlineBackend hiện có để dự báo trước cập nhật. Không tạo optimizer hoặc khôi phục RNG huấn luyện trong lúc nạp suy luận.

Loader kiểm recipe, nguồn, đồ thị đã tắt, encoding, vocabulary, miền mô phỏng, phase và freeze lineage. State chỉ được chứa các trọng số `backbone.*`; tên được ánh xạ sang backbone gốc và nạp strict. Metadata, state digest, giới hạn byte và checkpoint được kiểm lại. Mô hình suy luận chạy CPU, kể cả khi đọc tensor CPU đã serialize từ producer CUDA. Trường hợp CUDA producer chưa được kiểm thực tế ở gói này.

Đây là đường nạp trọng số để đánh giá. Nó không tạo chứng nhận final fitted, chọn epoch, chọn hệ thống thắng, refit hoặc hiệu chỉnh. Đánh giá vòng kín chính vẫn cần các artifact lựa chọn/refit/calibration và quyền thực thi theo protocol.

## Kiểm thực tế trên Colab CPU

| Lượt | Kết quả | Diễn giải |
|---|---|---|
| attempt01 | 10 đạt, 12 lỗi thiết lập fixture | Fixture thu nhỏ kiến trúc bị frozen research policy chặn. Giữ nguyên lỗi và nguồn đầu vào. |
| attempt02 | 22 đạt, 0 lỗi, 0 bỏ qua | 12 ca mới và 10 ca hồi quy online hiện có. |

Lượt sửa dùng đúng kiến trúc nghiên cứu đã chốt, 8 learner giả × 6 tương tác, tổng 48 training targets và 2 Adam updates. Checkpoint được tạo bằng producer checkpoint thật rồi nạp bằng loader mới. Sáu dự báo tuần tự được đối chiếu với wrapper nghiên cứu ở sai số tuyệt đối 1e-6. Kiểm thêm OOV, RNG không đổi, không tạo optimizer, từ chối miền/cấu hình/encoding/phase/SHA sai và năm dạng payload không nhất quán dù đã cập nhật SHA archive.

Thời gian toàn tiến trình attempt02 là 20,461 giây, pytest ghi 17,74 giây. Nguồn giữ nguyên trước–sau. Đây là kiểm fixtures trên runtime Colab CPU kế thừa qua venv đã ghi trong `remote/runtime.json`. Không cộng 22 ca vào tổng kiểm cũ như thể tất cả là ca mới.

## Bằng chứng và cách lần lại

- `remote/attempt01/` giữ lệnh, log, JUnit, trạng thái và manifest nguồn của lượt lỗi. Payload nguồn ban đầu còn tại `artifacts/akt/colab/a0-online-overlay.json`, được ghim trong `overlay.json`.
- `remote/attempt02/` giữ các file tương ứng của lượt đạt. SHA trong manifest được đối chiếu với ba file local sau tải về.
- `verification.json` ghi archive 41.989 byte, CRC, SHA từng file và kiểm JUnit độc lập. `receive.py` là bước nghiệm thu nhỏ đã chạy.
- `historical-a0-metadata-check.json` xác nhận chỉ đọc epoch 4 của lượt engineering A0 đã có, khớp nguồn hiện hành và SHA state/metadata/COMPLETE. Lượt này không import Torch, không giải mã tensor hoặc dự báo bằng checkpoint lịch sử.
- `current-source-inventory.json` ghi đúng API production có 197 file nguồn/fixture và 92 module kiểm. Đây là inventory tĩnh, chưa là Gate mới.
- `manifest.json` liên kết input/output của bundle. Checkpoint fixture và các payload âm lớn giữ ở vùng kết quả của phiên Colab, chỉ tải log nhỏ về repository.

## Phần còn thiếu

Chưa có nghiệm thu toàn nguồn 197 file, CUDA, nạp tensor checkpoint lịch sử qua loader mới hoặc final refit/calibration. A1–A3 cần backend riêng giữ cơ chế đồ thị và gate, không được nạp qua đường A0. Main matrix, kết quả vòng kín, demo mô hình đã fit và kết luận RQ3 còn chờ. Không đọc Junyi/Holdout, không chạy full CV và không dùng Modal.
