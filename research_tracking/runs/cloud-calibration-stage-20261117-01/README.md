# Worker CPU stage input calibration từ Drive

`scripts/akt/modal_calibration_input_stage.py` định nghĩa worker, không tự chạy cloud. API `create_app()` trả app và hàm `stage`. Root duyệt lượt chạy riêng và gọi tuần tự trong app.run. Worker chỉ dùng CPU, 1 CPU/1 GiB, timeout 600 giây, startup 180 giây, một container mỗi lúc, không tự retry cả function, trả container sau hai giây và dùng container mới cho lần gọi sau.

## Input cố định

- Drive Sang `honguyenminhsang2005@gmail.com`, thư mục cha `1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7`.
- File ZIP `1GlPhrWOLwFNeUiv1unYaEATypWmV9_Vy`, 134.525.060 byte.
- ZIP SHA-256 `a34cee8e961baf7056e8f16159d2b9a25afcca72f3c19b3a37bd0d711aab2d6a`.
- Plan nằm trong ZIP, SHA-256 `a552518a231ee5d432e88080220e22ab161c196150b42addea08f0f94aed64dc`, tương ứng INPUT_PLAN04 đã được root chuẩn bị.

Secret OAuth chỉ gắn CPU worker. Module không ghi token hoặc resumable URL ra state/log. Worker che nội dung ngoại lệ, chỉ trả loại lỗi. Account, parent, byte và SHA do Drive trả cần khớp trước khi tải media. OAuth endpoint cần đúng endpoint Google đã chốt.

## Lưu bền vững và nghiệm thu

Volume `kltn-junyi-calibration-artifacts-v1` v2 được reload trước khi mở file. Root vật lý lấy từ `/artifacts`. Input nằm dưới `calibration-inputs-20261117-01/`, source giữ nguyên cây đường dẫn trong repository.

Tải vào INPUT.zip.part, flush/fsync và commit sau mỗi chunk tối đa 8 MiB. Khi mất mạng, hỏi lại bằng HTTP Range từ kích thước part đã commit. Có hai lần thử lại cho lỗi mạng/HTTP tạm thời. Phản hồi Range sai bị chặn. File tải xong phải đúng SHA mới đổi tên INPUT.zip và commit.

Giải nén kiểm SHA ZIP và SHA plan, tối đa 256 payload member cộng plan, 160 MiB tổng giải nén và 64 MiB mỗi file. Không cho member trùng, traversal, drive path Windows, private/Holdout path, symlink, directory entry hoặc member mã hóa. Mọi file phải khớp byte và SHA trong plan. Dữ liệu được ghi vào staging directory riêng, chỉ đổi tên thành source sau khi đủ tất cả file. Lỗi giữ staging chưa nghiệm thu trên Volume để root điều tra.

Lượt sau có thể kiểm lại source đã stage. Thiếu file, thêm file hoặc khác SHA đều bị từ chối. STAGED.json giữ đầy đủ file pins trên Volume. Kết quả trả về PC chỉ có root nguồn, đường dẫn/SHA receipt, số file, byte và pins ZIP/plan. Không trả payload/model.

## Kiểm đã chạy

`tests03.txt` đạt **14/14** trong 0,39 giây. Bao gồm mất mạng sau chunk đầu và tiếp tục từ byte 128 trên Drive giả, sai account, sai Range, archive exact/idempotent, traversal, private path, symlink, member ngoài plan, SHA sai, member trùng, vượt trần giải nén và source đã stage có file thừa. Lượt tests01 đạt 11/11 và tests02 đạt 12/12 được giữ.

SDK local xác nhận decorator Modal có tham số `serialized`, phù hợp nested worker. Chưa chạy Modal, chưa tải ZIP thật, chưa chứng nhận tốc độ/chi phí CPU. Root cần kiểm thực tế trong hạn mức đã dự kiến trước khi chuyển sang GPU.

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/akt/test_modal_calibration_input_stage.py -q -p no:cacheprovider --basetemp=artifacts/akt/runtime/calibration-stage-tests-20261117-03
```
