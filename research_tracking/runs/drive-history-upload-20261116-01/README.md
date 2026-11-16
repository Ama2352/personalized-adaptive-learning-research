# Upload lịch sử AKT có phục hồi tiến độ

## Cập nhật sau đăng nhập và kiểm Drive thật

Đã đăng nhập đúng Sang, kiểm thư mục đích và quota Drive. Probe thật dùng file tổng hợp 1.048.593 byte, dừng process sau server ack 262.144 byte rồi chạy process khác. Lượt phục hồi gửi tiếp từ `bytes 262144-524287/1048593`, checksum server khớp nguồn. [Nghiệm thu probe](real-probe/RECOVERY_ACCEPTANCE.json) và `real-probe/NETWORK.jsonl` giữ bằng chứng. Đây là ngắt client có chủ ý, chưa cắt mạng vật lý.

Người dùng xác nhận đã dừng upload thư mục history trên trình duyệt. Uploader chính đang gửi 37 file / 35,15 GB theo inventory; `EXECUTION_STATE.json` và `events.jsonl` giữ diễn tiến, `RECEIPTS.json` chỉ ghi những file đã kiểm xong. Các đoạn chuẩn bị bên dưới phản ánh thời điểm chưa đăng nhập. Probe giữ hai file tổng hợp nhỏ trong thư mục Drive riêng `KLTN_UPLOAD_RECOVERY_CHECK_20261116`. Không dùng probe làm bằng chứng hoàn tất sao lưu 35 GB.

## Hiện trạng

Đã chuẩn bị uploader và kế hoạch 37 file, gồm 35 ZIP cùng hai file hướng dẫn/manifest, tổng 35.154.236.922 byte. Nguồn là `experiments/akt/results/drive-offload-history-20261116-01/`. Đích là thư mục cùng tên bên trong [Drive KLTN](https://drive.google.com/drive/folders/1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7), bằng tài khoản Sang `honguyenminhsang2005@gmail.com`.

Đã đạt 29 kiểm thử offline trên dữ liệu tổng hợp và Drive giả lập. `tests02.txt` giữ output pytest mới nhất, `tests01.txt` giữ lượt trước. Chưa kết nối hoặc upload thật bằng script, còn thiếu OAuth Desktop client. Kết quả test xác nhận cơ chế phần mềm trong mô phỏng HTTP, chưa chứng minh hành vi trên mạng/Google Drive thật.

## Một lần chuẩn bị đăng nhập

1. Mở [Google Cloud Console](https://console.cloud.google.com/), chọn hoặc tạo project riêng cho uploader, bật **Google Drive API**.
2. Trong **Google Auth platform**, khai báo thông tin ứng dụng. Với Gmail cá nhân chọn audience **External**, để trạng thái **Testing** và thêm `honguyenminhsang2005@gmail.com` vào test users.
3. Vào **Clients**, tạo client loại **Desktop app**, tải file JSON.
4. Lưu JSON tại `D:\Dev\KLTN\artifacts\akt\private\drive-upload\client_secret.json`. Giữ nội dung JSON trong máy.
5. Chạy lệnh bên dưới. Trình duyệt sẽ mở để chọn tài khoản Sang và cấp quyền Drive. Script kiểm email qua API trước thao tác tạo thư mục hoặc gửi file.

Uploader dùng quyền `https://www.googleapis.com/auth/drive` để truy cập thư mục có sẵn và đối chiếu những file đã upload bằng trình duyệt. Quyền này cho phép quản lý Drive, nên cần đọc màn hình đồng ý của Google. Phạm vi thao tác của script là đích đã chốt trong `UPLOAD_PLAN.json`.

## Lệnh Windows

Mở PowerShell tại `D:\Dev\KLTN` và chạy bằng `.venv` hiện có.

```powershell
.\.venv\Scripts\python.exe -B scripts\akt\drive_resumable_upload.py --prepare
.\.venv\Scripts\python.exe -B scripts\akt\drive_resumable_upload.py --login-only
.\.venv\Scripts\python.exe -B scripts\akt\drive_resumable_upload.py
```

Lệnh đầu chỉ kiểm inventory local. Lệnh thứ hai đăng nhập và kiểm tài khoản/đích. Lệnh thứ ba upload tuần tự với chunk 32 MiB sau bước kiểm thật được nêu phía cuối. Các thư viện cần thiết đã có trong `.venv`, phiên bản giữ tại `ENVIRONMENT.json`.

Khi chuyển từ upload trình duyệt sang script, dừng lượt gửi cùng thư mục lịch sử trên trình duyệt để script đối chiếu ổn định các file đã hoàn tất. File có cùng tên, thư mục cha, kích thước và checksum được tái sử dụng. Tiến độ của file trình duyệt đang gửi dở thuộc phiên riêng, script chỉ tiếp tục được các phiên do nó lưu. Thư mục duplicates là lượt upload khác.

Chạy lại cùng lệnh sau khi đóng terminal hoặc khởi động lại máy. Ctrl+C lưu trạng thái gần nhất. Khi nhận phản hồi chưa chắc chắn, script hỏi Drive phần byte đã nhận rồi mới gửi tiếp. Sau 20 lần lỗi liên tiếp sẽ dừng và giữ state. Phiên Drive hết hạn có thể buộc gửi lại file đang dở, giới hạn phiên theo Google khoảng một tuần. File đã hoàn tất được đối chiếu checksum ở lần chạy tiếp.

Nguồn phải giữ nguyên khi upload. Script kiểm size/mtime, hash SHA-256 và MD5 trước gửi từng file, đối chiếu SHA với inventory archive đã có. Cache hash gắn với size/mtime trong state để giảm đọc lại. Nếu người khác cố tình thay byte đồng thời giữ nguyên size/mtime thì cơ chế cache không phát hiện được, vì vậy nguồn cần được giữ ổn định. File rỗng bị từ chối rõ ràng trong bản này, thư mục hiện tại đã kiểm không có file rỗng.

## Nơi lưu tiến độ và bằng chứng

| Vị trí | Nội dung |
|---|---|
| `artifacts/akt/private/drive-upload/` | OAuth client, token, URI phiên, offset và khóa một tiến trình. Được Git ignore, giữ riêng trên D |
| `UPLOAD_PLAN.json` | Nguồn, đích, đường dẫn, size/mtime và SHA từ inventory |
| `events.jsonl` | Các sự kiện hoàn tất file, hết hạn phiên và hoàn tất đợt, tạo khi chạy thật |
| `RECEIPTS.json` | ID Drive, SHA nguồn, MD5 server, SHA server nếu được trả về, tạo khi nghiệm thu file |
| `ACCEPTANCE.json` | Nghiệm thu toàn đợt, tạo sau khi đủ 37 file được kiểm |

State dùng ghi tạm, flush/fsync và thay thế atomic. Khóa tiến trình hạn chế hai uploader ghi chung state. ID Drive được xin và lưu trước khi tạo file để retry cùng ID sau mất phản hồi. URI phiên chỉ nhận HTTPS tại endpoint upload của Google, được giữ riêng. Luồng upload đọc trực tiếp file trên D với chunk trong RAM. Không tạo thêm ZIP hoặc bản sao lớn.

Checksum nghiệm thu là MD5 do Drive trả về so với MD5 nguồn, cùng kích thước/đích/tên. Khi Drive có `sha256Checksum`, script kiểm thêm SHA-256. Đây là kiểm bằng metadata checksum server, không có lượt tải xuống toàn bộ 35 GB để xác minh độc lập. Bản nguồn và hardlink tiếp tục tồn tại sau upload, việc dọn cần nghiệm thu và quyết định riêng.

## Các ca đã kiểm

Upload nhiều chunk, mất mạng sau khi server đã nhận chunk, mất phản hồi cuối file, process dừng rồi phục hồi theo offset server, bỏ qua file đã hoàn tất, tái sử dụng file trình duyệt đã hoàn tất, phiên hết hạn, checksum sai, thay nguồn/plan, tài khoản sai, lỗi quyền, giới hạn retry, HTTP 429, offset trên 32 GB, range lỗi, URI ngoài Google, khóa hai tiến trình, file rỗng và bảo toàn manifest nguồn. Các kết quả này đều dùng fake HTTP.

Lượt kiểm thật đầu tiên nên giới hạn bằng bản dữ liệu tổng hợp nhỏ và thư mục đích phụ, xác minh cắt/kết nối lại trước khi gửi archive lớn. Giữ log riêng để phân biệt test kỹ thuật với tiến độ sao lưu nghiên cứu.

## Nguồn thiết kế

- [Drive resumable uploads](https://developers.google.com/workspace/drive/api/guides/manage-uploads) quy định session URI, `308`, `Range` và xử lý hết hạn.
- [Google Python OAuth quickstart](https://developers.google.com/workspace/drive/api/quickstart/python) hướng dẫn Desktop client và lưu refresh token.
- [Pre-generated IDs](https://developers.google.com/workspace/drive/api/guides/create-file#generate-ids-to-use-with-your-files) giải thích retry cùng ID tránh tạo file trùng.

## Bước tiếp theo

Nhận client JSON qua file local, mở đăng nhập để người dùng xác nhận Sang. Kiểm thật một file tổng hợp nhỏ cùng việc dừng/mở lại. Sau đó thực hiện lịch sử 35 ZIP theo kế hoạch đã tạo. Chưa có file nào trong nguồn bị đổi hoặc xóa bởi uploader.


## Nghiệm thu hoàn tất ngày 17/11/2026

Đã hoàn tất đủ 37 file, gồm 35 ZIP và hai file hỗ trợ, tổng 35.154.236.922 byte. Đọc lại metadata của toàn bộ file và năm thư mục bằng một lượt xác minh riêng sau khi process upload thoát mã 0. Cả 37 SHA-256 server và MD5 khớp pin local, tên/thư mục cha khớp kế hoạch, size/mtime của 37 nguồn còn khớp snapshot. Biên nhận [READBACK_ACCEPTANCE.json](READBACK_ACCEPTANCE.json) giữ ID/link/checksum từng file cùng giới hạn.

[Mở thư mục lịch sử đã sao lưu](https://drive.google.com/drive/folders/1V-H0estsyh2oQQ3qnfapU9qSpGZFoF3H). `EXECUTION_STATE.json` đã chuyển COMPLETE_READBACK_VERIFIED. Lượt này kết thúc lúc 2026-11-17T00:22:16.294571+07:00. Bản local còn nguyên, chưa có thao tác dọn 35 GB trong lượt upload này. Đây là nghiệm thu bằng checksum server sau upload, không có lượt tải lại toàn bộ file về máy.
