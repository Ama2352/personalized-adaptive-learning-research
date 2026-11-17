# Stream numeric A2/A3 từ Volume sang Drive

## Đã xác minh

- Bộ kiểm tổng hợp có 12 ca đạt. Nội dung ZIP đọc lại đúng byte, kích thước bằng công thức đã pin và không đổi khi thay kích thước block. Các ca đổi SHA, đổi số byte, đổi binding, count hoặc manifest nguồn đều bị từ chối.
- Hủy phía consumer đóng reader và thread producer. Queue có tối đa hai block, mỗi member nguồn tối đa 2 MiB, block phát tối đa 8 MiB. Giới hạn payload đang sống được suy ra từ các cap này, chưa có đo peak RSS riêng của lượt upload đầy đủ.
- Probe API thật trước đó đọc một NPZ A2 106.090 byte vào RAM, SHA đúng. Hồ sơ nằm tại `../junyi-calibration-real-20261117-01/A2_NUMERIC_API_SOURCE_PROBE01.json`. Không ghi binary xuống ổ đĩa và không tạo compute Modal.

## Cách nối

`scripts/akt/modal_volume_archive.py` cung cấp ba bước. `build_numeric_plan` đọc receipt đã pin từ GPU result, directory metadata và manifest shard. Hàm kiểm binding, số cửa sổ/target và SHA từng manifest. `zip_size` tính kích thước archive chính xác. `iter_zip_bytes` đọc nguồn qua API, kiểm SHA/bytes từng member rồi tạo ZIP_STORED trực tiếp cho uploader.

Plan có `entries`, `total_bytes` là tổng byte nguồn và `source_plan_sha256` là SHA256 JSON canonical của hai trường đó. Uploader phải dùng kết quả `zip_size(plan)` làm tổng byte ZIP. Factory phải tạo iterator mới khi khôi phục và đóng iterator trong `finally`.

Archive giữ RECEIPT cùng các cặp JSON/NPZ. Config GPU đã có trong hồ sơ operation/request được publish riêng trên Drive, không nhân bản vào numeric archive này. Hàm builder chỉ hỗ trợ hai numeric run A2/A3 hiện hành. Không dùng như công cụ archive tùy ý.

## Giới hạn

Chưa chạy upload archive thật trong gói này. Probe không chứng minh mọi NPZ đều đọc được. Mỗi nguồn phải được đọc và kiểm lại trong lượt upload. Không xóa nguồn Volume sau upload. Không chạy calibration, suy luận, training hoặc bất kỳ CPU function trả phí nào.

Lượt pytest cần quyền thực thi ngoài giới hạn socket của môi trường kiểm vì asyncio Windows tạo socket pair nội bộ. Không có lệnh gọi compute cloud trong tests. Các lượt thử đầu bị chờ ở socketpair đã ngắt, sau khi đổi quyền thực thi bộ kiểm đạt.

Lệnh kiểm được ghi tại tests01.txt và tests01.xml. Không có dependency mới.
