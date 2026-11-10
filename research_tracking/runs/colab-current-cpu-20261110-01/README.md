# AKT trên Colab CPU ngày 10/11/2026

## Kết quả đã xác nhận

Đã điều khiển Colab qua cầu nối MCP chính thức từ terminal của dự án. Người dùng xác nhận kết nối CPU và cho phép tải gói nguồn khoảng 1 MB để kiểm. Phiên có khoảng 11,7 GiB RAM khả dụng lúc khám phá môi trường.

| Lượt kiểm | Phạm vi | Kết quả |
|---|---|---|
| Local | Bộ đóng gói nguồn, đủ tám tài liệu phụ thuộc và dừng khi thiếu tài liệu | 11 đạt |
| Colab baseline | Bảy module về model, checkpoint, parity upstream, training, online, windows và encoding | 67 đạt, 0 lỗi, 0 bỏ qua |
| Colab research core | Bốn module về model đồ thị, optimizer, checkpoint và online observables | 113 đạt, 0 lỗi, 0 bỏ qua |

Lượt baseline mất 20,263 giây cả tiến trình, lượt research core mất 41,936 giây. Đây là thời gian kiểm fixtures, không phải tốc độ huấn luyện corpus. Hai lượt đều kiểm lại toàn bộ SHA nguồn trước–sau và giữ nguyên nguồn.

## Tìm bằng chứng

- `remote/baseline-tests.xml` và `remote/research-core-tests.xml` ghi từng ca kiểm. Các file `.log`, `*-command.json` và `*-status.json` đi kèm giữ lệnh, output và trạng thái.
- `remote/runtime.json`, `setup-venv-target.log`, `setup-freeze.log` và `install-report.json` ghi môi trường thực tế. Python 3.13.18, Torch 2.14.1+cpu, NumPy 2.4.6, pandas 2.2.3, DuckDB 1.5.6 và pytest 8.4.2.
- `remote/transfer.json` và `bundle-manifest.json` ghi gói nguồn gồm 275 file. ZIP giữ tại `artifacts/akt/colab/sourcekit-cpu-current-20261110-01.zip`, SHA `c7c0fbb160e2ef5f62c6a5f002242bdb36528c4994e3edf17d4c314bf65d2707`.
- `verification.json` ghi kiểm độc lập sau tải về. Archive 31.922 byte được kiểm CRC và SHA từng file trước khi lưu 21 file bằng chứng remote. `manifest.json` liên kết nguồn và đầu ra của bundle này.

## Diễn tiến và giới hạn

Gói cũ thiếu recipe 28/29/30 mà source hiện hành cần. Đã bổ sung ba tài liệu vào allowlist cố định, kiểm trường hợp thiếu từng tài liệu và giữ nguyên notebook Paper 1/2 gốc. Chỉ bản sao đóng gói được xóa outputs và metadata.

Bộ duyệt tự động ban đầu chặn truyền nguồn ra Google Colab. Sau khi người dùng cho phép rõ payload và đích, đã truyền đủ 30 phần nhỏ và kiểm archive cùng SHA toàn bộ thành viên trên Colab. Không truyền Junyi, credentials hoặc checkpoint lịch sử.

Một số lệnh `run_code_cell` trả outputs rỗng. Trạng thái này không được dùng làm bằng chứng thành công. Đã đọc lại cell và quan sát trạng thái trong kernel để phân biệt chưa có kết quả với bước đã hoàn tất. Tách giải nén khỏi chuẩn bị môi trường giúp xác nhận từng bước. Hai lượt kiểm chỉ được chấp nhận sau khi lấy JUnit và kiểm lại archive trên máy local. Các kết quả cầu nối thô giữ tại `artifacts/akt/private/colab-bridge/session-7b319172d1ee4b068afd33de8b74beab/`, không đưa thông tin kết nối riêng vào báo cáo.

Venv trên Colab dùng `--system-site-packages` để tái dùng runtime sẵn có. Chỉ DuckDB 1.5.6 được cài bổ sung trong venv dự án. Đây là bằng chứng chạy được trên một môi trường Linux CPU cụ thể, chưa thay thế bộ nghiệm thu toàn nguồn, môi trường khóa dependency, CUDA, phục hồi lỗi bất ngờ hoặc durability trên Modal. Các fixtures có những bước cập nhật trọng số nhỏ theo test, chưa chạy nghiên cứu Main60 hoặc Junyi. Chưa có kết luận CG-AKT tốt hơn baseline và chưa dùng credit Modal.

## Bước kế tiếp

Tiếp tục hoàn thiện cầu nối checkpoint nghiên cứu A0 sang backend dự báo tuần tự, rồi kiểm parity trên fixtures ở Colab. Lượt nạp checkpoint lịch sử hoặc truyền checkpoint sang Colab cần phạm vi riêng được xác nhận. Bộ kiểm toàn nguồn và profile CUDA vẫn là điều kiện riêng trước huấn luyện lớn.
