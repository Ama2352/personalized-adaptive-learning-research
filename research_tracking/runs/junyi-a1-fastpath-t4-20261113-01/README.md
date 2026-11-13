# A1 — giảm chuyển đổi Python và kiểm nhanh trên T4 ngày 13/11

## Kết quả đã xác nhận

Đã kiểm trên Tesla T4 miễn phí của Colab, Python 3.13.16, Torch 2.14.1+cu130. Phép kiểm GPU kéo dài 28,62 giây, dữ liệu tổng hợp, batch128 × 200 với 12.800 target mỗi bước. Hai điều kiện alpha 0 và 0,75 giữ nguyên khởi tạo, dropout/RNG, loss, gradient, một bước Adam và trạng thái optimizer. Sai lệch lớn nhất bằng 0 trong các đại lượng đã đối chiếu. Bộ kiểm helper trên Colab đạt 19 ca trong 1,75 giây.

| Đại lượng của chuỗi đo ngắn | Trước sửa | Sau sửa |
|---|---:|---:|
| Thời gian 6 bước training | 6,196 giây | 4,925 giây |
| Target/giây | 12.395 | 15.593 |
| GPU-Util trung bình theo mẫu | 26,53% | 37,75% |
| Số mẫu tài nguyên | 19 | 16 |
| VRAM sử dụng đỉnh theo nvidia-smi | 5.269 MiB | 5.269 MiB |

Thông lượng tăng 1,258 lần, thời gian giảm 20,51%. Mức GPU trung bình trong lượt này còn dưới mục tiêu 50%. Đợt này sử dụng 0 USD Modal.

## Thay đổi và cơ sở

Chỉ đổi cách chuyển evidence dataclass thành JSON phục vụ kiểm tính toàn vẹn. Encoder mở từng dataclass bằng `fields()` khi gặp nó, tránh dựng lại toàn bộ cây bằng `asdict()` trước khi JSON duyệt tiếp. Giữ kiểm tuple/dataclass, sắp thứ tự khóa, encoding mặc định, cấm NaN/Inf và tính lại digest mỗi lần. Kiểm mutation vẫn chạy, chưa thêm cache. Cơ sở shallow conversion được mô tả trong tài liệu Python. [Tài liệu Python](https://docs.python.org/3.13/library/dataclasses.html#dataclasses.asdict)

Helper local được tách từ AST để đo bằng stdlib khi máy thiếu RAM. Hai mẫu synthetic sparse/dense giữ digest cũ, tăng tốc riêng helper 1,21 và 1,92 lần. Đây là phạm vi của `local-helper-benchmark.json`. Phép kiểm model thật trên CUDA và bộ kiểm local riêng cung cấp bằng chứng ở cấp cao hơn.

## Giới hạn và quyết định tiếp theo

Đây là bằng chứng kỹ thuật hỗ trợ chuẩn bị AKT, chưa tăng mức hoàn tất thực nghiệm RQ1–RQ3. Chuỗi đo có một cặp sáu bước, chạy cũ rồi mới. Prefix evidence dựng trước vòng đo. Adapter ticket, sinh prefix theo batch, SQL/cache loading, validation và checkpoint production chưa nằm trong thông lượng này. Các mẫu nvidia-smi có cửa sổ đo tương quan và ranh giới phase xấp xỉ. Cần phép đo producer đại diện trước khi suy ra tốc độ toàn Junyi hoặc H100.

Source helper mới đã được sửa tại workspace. Gate đầy đủ và kiểm resume checkpoint lịch sử theo danh tính nguồn mới còn chờ. Checkpoint source2 epoch1 được giữ nguyên tại vị trí đã ghi trong bundle A1 trước, chưa áp dụng migration hoặc chạy lại training. Chưa có bằng chứng GPU trung bình toàn training đạt 50%. Bước ưu tiên tiếp là chuẩn bị representation hoặc cache của prefix/message cố định theo input và graph, giữ phần phụ thuộc trọng số học trong model, rồi kiểm full batch lifecycle trước lượt Modal tiếp theo.

## Bằng chứng và cách dựng lại

- `summary.json`, `training-summary.csv`, `gpu-telemetry.csv` giữ số liệu dùng trong bảng và hình.
- `a1-fastpath-t4-v1.svg/.png/.pdf` là hình độc lập đã kiểm trực quan. `build_figure.py` dựng lại từ raw result đã tải. Bảng màu/quy ước kế thừa figures4papers, provenance và giấy phép được dẫn trong script.
- `source-transfer-manifest.json` giữ inventory source trước upload. Gói chỉ có source và fixture tổng hợp, chưa chuyển log Junyi, checkpoint nghiên cứu hoặc thông tin đăng nhập.
- `probe_t4.py` giữ đúng script đã chạy, kế thừa bộ kiểm native trước. Hai trạng thái optimizer được so sánh sau một bước mỗi alpha. Chuỗi sáu bước phục vụ đo tốc độ, chưa kiểm quỹ đạo dài bằng checkpoint.
- `download-receipt.json` ghi kiểm SHA archive, CRC ZIP và từng member sau tải về ổ D. Raw result, log và ZIP nằm tại `experiments/akt/results/colab-a1-fastpath-t4-20261113-01/`.
- `verify_local.py` và `local-regression.json/.log` giữ lượt hồi quy có trần 120 giây và 1 GiB RSS. Đọc trạng thái receipt trước khi khẳng định số ca đạt.
- `runtime-release.json` ghi xác nhận tiến trình probe đã thoát, không còn compute process của lượt kiểm, cell gọi `runtime.unassign()` đã trả về và bridge local đã đóng. Tab Colab thuộc phiên làm việc được giữ để người dùng quản lý.

Các thao tác dựng lại dùng Python `.venv` của repository. `prepare_probe.py` tạo ZIP mới và request chuyển source, dừng nếu trùng tên archive. `probe_t4.py` chạy trong venv dự án trên Colab và cần upstream AKT tại commit đã ghim. Source cũ và candidate phải ở hai cây riêng như request setup. Giữ nguyên bằng chứng đã đóng, dùng run ID mới khi đo lại.
