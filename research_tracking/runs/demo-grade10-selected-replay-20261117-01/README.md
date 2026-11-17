# Demo dự báo Grade10 từ bảy mô hình đã học

## Mục tiêu và phạm vi nghiệm thu

Đề cương yêu cầu demo nghiên cứu thể hiện người học, trạng thái kiến thức, đồ thị và lựa chọn lộ trình. Gói này bổ sung một phần còn thiếu trong demo hiện hành, cho phép xem dự báo thật đã lưu của AKT/CG-AKT trên cùng lịch sử Grade10. Chế độ GAM-KT hiện có tiếp tục cung cấp trạng thái và quyết định mô phỏng đã ghi.

Nguồn là bảy mô hình selected-fit đã nghiệm thu ngày 12/11, gồm A0 không đồ thị và A1/A2/A3 với đồ thị chuyên gia hoặc học từ TRAIN. Sáu người học mô phỏng có cùng 210 tương tác mỗi người, tổng 1.260 dự báo cho từng mô hình. Miền này có 28 khái niệm và 84 bài. Các mô hình Junyi có từ vựng riêng.

Người xem có thể chọn mô hình, nguồn đồ thị, người học và bước lịch sử. Demo hiển thị dự báo trước đáp án hiện tại, dự báo A0 ở cùng câu hỏi, số lần quan sát theo khái niệm, chuỗi bài đã ghi, 31 trọng số cạnh khi có đồ thị và bảng Log Loss/AUC/Brier/ECE dùng chọn vòng. Các giá trị cổng theo từng bước chưa được archive nên trường đó giữ `null` và giao diện ghi rõ tình trạng này.

Đây là replay trên tập development đã dùng chọn vòng. Gói không tạo thêm dự đoán hay mẫu nghiên cứu. Trạng thái thành thạo đã hiệu chỉnh và hành động của bộ chọn bài AKT vòng kín vẫn là hạng mục mở của E11.

## Nguồn và kiểm tra đối chiếu

- `REPLAY_MANIFEST.json` ghi các input, checkpoint identity, nguồn chấp thuận và SHA của projection nhỏ. `build_projection.py` kiểm lại toàn bộ 1.260 khóa tương tác, nhãn, lịch sử và phase giữa bảy mô hình. Bốn metric được tính lại bằng evaluator GAM-KT dùng chung rồi đối chiếu số đã nghiệm thu với sai số tối đa `1e-10`.
- `selected-replay.json.gz` là projection 94.985 byte cho demo. Loader kiểm manifest/file và giới hạn giải nén trước khi dùng. Chỉ alias sáu người học mô phỏng được đưa vào API.
- Hai archive A0 và A1 chuyên gia đã chuyển lên Drive. Hai lần lấy lại đúng `predictions.csv`, `targets.csv`, `SHA256.json` dùng Range, kiểm SHA archive qua metadata và SHA từng member theo manifest bên trong. Tổng response 336.832 byte, thấp hơn giới hạn 4 MiB được duyệt. Các receipt `A0_RANGE_RECEIPT.json` và `A1_EXPERT_RANGE_RECEIPT.json` lưu đối chiếu. Không tải archive hay weights đầy đủ.
- Lần dựng projection đầu gặp thiếu archive A1 chuyên gia tại vị trí local cũ. Sau khi truy vết relocation và lấy ba member nhỏ từ Drive, lần dựng hoàn chỉnh đạt `SEVEN_SELECTED_REPLAYS_VERIFIED`. Không thay nội dung nguồn lịch sử.

## Chạy demo

Tại repository, chạy bằng môi trường dự án.

```powershell
.\.venv\Scripts\python.exe -m src.research_demo --port 8765
```

Mở `http://127.0.0.1:8765`, chọn mục AKT/CG-AKT đã học. `Ctrl+C` đóng máy chủ khi xem xong. API mới chỉ có `/api/selected-replay` với ba tham số allowlist `model`, `learner`, `step`.

## Tiêu chí kiểm và kết quả

| Tiêu chí | Kết quả |
|---|---|
| Đủ bảy mô hình, sáu người học, 1.260 tương tác mỗi mô hình | Đạt, builder kiểm khóa/nhãn/lịch sử và metric gốc |
| Dự báo trước cập nhật, API chỉ hiện đáp án ở bước trước | Đạt, kiểm riêng thay đáp án hiện tại và tương lai |
| Đúng trọng số cạnh đã lưu, không dựng giá trị cổng | Đạt, A0 có 0 cạnh, sáu cấu hình có 31 cạnh, cổng từng bước `null` |
| Không tải model hoặc import Torch khi mở demo | Đạt, kiểm tiến trình Python riêng |
| API allowlist, Origin, chống đọc file tùy ý và mutation | Đạt, bộ kiểm cũ và mới chạy chung |
| Bản cũ tiếp tục hoạt động | Đạt, tổng 143 ca trong `TESTS03.txt` |
| Cú pháp hai tệp JavaScript | Đạt với `node --check`, ghi ở `STATIC_QA.json` |
| Hiển thị trực quan desktop/mobile | Chưa kiểm trong gói này, tránh mở preview khi RAM hạn chế |

`TESTS01.txt` ghi 30 ca mới đạt. `TESTS02.txt` giữ lượt chạy đầu với 36 lỗi kết nối localhost do quyền mạng của tiến trình, 107 ca còn lại đạt. Chạy lại với quyền localhost đã duyệt cho ra `TESTS03.txt`, 143 ca đạt trong 10,81 giây. Fixture HTTP luôn shutdown, server-close và join thread trong teardown. Không mở browser hoặc máy chủ preview riêng.

## Còn thiếu để hoàn thành demo trong đề cương

1. Nghiệm thu checkpoint Grade10 refit và phép chuyển dự báo sang mastery đã hiệu chỉnh trước khi nối bộ chọn bài hiện đại.
2. Ghi trạng thái cổng theo từng bước và chạy vòng kín được duyệt để trình bày hành động thật cùng kết quả học.
3. Kiểm giao diện trực quan khi đủ RAM, giữ bằng chứng rồi đóng phiên kiểm.

Các điểm trên giữ mở. Thành quả của gói hiện tại là demo xem lại mô hình đã học và bằng chứng development có nguồn kiểm chứng.
