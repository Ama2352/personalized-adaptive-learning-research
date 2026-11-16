# Sink artifact trực tiếp từ cloud sang Drive

## Kết quả đã kiểm

Đã bổ sung `scripts/akt/drive_artifact_sink.py` để CPU worker gửi danh sách file rõ ràng từ Modal Volume hoặc cloud scratch sang Google Drive. Bộ kiểm offline cuối đạt **22/22** trong 16,31 giây ở `tests04.txt`. Các lượt trước đạt 16/16, 19/19 và 21/21 được giữ để truy vết diễn tiến.

Đây là bằng chứng kỹ thuật với Drive giả và callback Volume giả. Gói này chưa có bằng chứng chạy Modal hoặc xác nhận checksum từ Google Drive thật. Root phụ trách phép kiểm CPU thực tế và chỉ cho phép chuyển sang GPU sau khi đạt.

## Đích và ranh giới

- Tài khoản Drive phải là `honguyenminhsang2005@gmail.com`, thư mục cha `1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7`.
- Mỗi snapshot đi vào `KLTN/<run_id>/<tranche_id>/`, giữ đường dẫn tương đối của từng file.
- Entrypoint công khai yêu cầu Linux và Volume `/artifacts`. Source nằm trong Volume hoặc `/tmp` của cloud worker.
- OAuth chỉ đọc từ biến môi trường `KLTN_DRIVE_OAUTH_JSON` do Modal Secret cấp. Worker CPU giữ Secret. Không gửi thông tin xác thực vào GPU worker.
- Callback `volume_commit` phải lưu bền vững Volume. Root dùng Volume `kltn-junyi-calibration-artifacts-v1`, mount `/artifacts`.
- Root điều phối duy nhất một CPU writer cho mỗi run/tranche. Khóa `/tmp/kltn-drive-locks/` chỉ bảo vệ process trong cùng container. Modal Volume không cung cấp khóa phân tán. Khi dùng lại container, root reload Volume trước khi mở file của snapshot.
- PC chỉ nhận kết quả nhỏ chứa Drive ID, kích thước và SHA. Artifact lớn, URI phiên upload và bằng chứng upload giữ trên cloud.

## Cách tích hợp

CPU worker gọi API sau khi nhận snapshot bất biến, đã đóng toàn bộ file đang ghi.

```python
from scripts.akt.drive_artifact_sink import publish_from_environment

receipt = publish_from_environment(
    source_root="/artifacts/junyi-a2/calibration-001/payloads",
    files=["config.json", "predictions.parquet", "model.pt"],
    run_id="junyi-a2",
    tranche_id="calibration-001",
    volume_commit=artifact_volume.commit,
    max_total_bytes=512 * 1024**2,
)
```

Danh sách file phải tường minh. Worker cần đưa cấu hình, manifest nguồn và đầu ra nghiên cứu cần lưu vào danh sách này. Helper không tự quét thư mục. File rỗng bị từ chối rõ ràng, có thể mô tả log rỗng trong một manifest JSON có nội dung. Các tên private phổ biến, đường dẫn vượt thư mục, symlink và junction bị chặn.

## Độ bền và nghiệm thu

1. Hash SHA-256/MD5 nguồn và giới hạn tổng byte trước khi gọi Drive. `ARTIFACT_PLAN.json` bất biến theo nội dung, source và đích.
2. Commit payload và plan lên Volume trước yêu cầu Drive đầu tiên. Đối chiếu email và thư mục cha trước khi tạo file.
3. Mỗi lần cập nhật state hoặc log sự kiện đều gọi `Volume.commit`. URI resumable được lưu vào `.drive-state/state.json` và commit trước chunk đầu.
4. Khi worker ngắt sau khi Drive nhận chunk nhưng trước khi lưu offset, lượt kế tiếp hỏi offset từ cùng URI và tiếp tục phần còn thiếu.
5. Mỗi file cần đủ kích thước, MD5, **SHA-256 do Drive trả**, tên và parent. Cờ `strict_verified` riêng được đặt trước khi core ghi trạng thái hoàn tất. Kết quả MD5 cũ phải kiểm SHA lại.
6. Đọc metadata lại toàn batch trước khi đặt `strict_batch_verified` và ghi `drive-evidence/STRICT_ACCEPTANCE.json`. Commit receipt trước khi trả kết quả nhỏ.
7. Nếu cùng byte được restage với mtime mới, hash lại toàn bộ nội dung rồi mới cập nhật fingerprint riêng trong state. Giữ URI/offset cũ. Plan công khai giữ nguyên. Thay đổi byte hoặc source/đích cần tranche mới.

Root cần kiểm CPU thực tế với một file nhỏ, gây ngắt có kiểm soát, khởi động CPU worker mới từ Volume, xác nhận offset/session tiếp tục và đối chiếu SHA server. Một lượt chỉ thoát mã 0 chưa đủ nghiệm thu. Khi lỗi, giữ Volume/state để tiếp tục. Entrypoint chỉ trả loại lỗi được kiểm soát, loại bỏ nội dung ngoại lệ có thể chứa OAuth hoặc URI.

## Phạm vi các ca kiểm

22 ca bao gồm namespace, commit trước chunk, ngắt sau server ACK, tiếp tục cùng phiên, thiếu/sai SHA, cờ MD5 cũ, lỗi ở lần readback cuối, sai tài khoản, lỗi commit ban đầu, lỗi commit receipt cuối không trả thành công và được kiểm lại ở lượt kế, thay đổi snapshot, mtime-only restage, nội dung thay đổi nhưng kích thước/mtime giữ nguyên, đường dẫn private/traversal, giới hạn byte, file rỗng, tách tên folder payload khỏi namespace, Secret không được lưu ra JSON và lỗi có URI bị che.

Lệnh dựng lại, dùng `.venv` của repository, chỉ tạo fixture tổng hợp nhỏ.

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/akt/test_drive_artifact_sink.py -q -p no:cacheprovider --basetemp=artifacts/akt/runtime/drive-cloud-sink-tests-20261117-04
```

Mã lõi tái sử dụng là `scripts/akt/drive_resumable_upload.py`. Nhánh này giữ nguyên core CLI và không tạo Modal resource. SHA nguồn và log nằm trong `MANIFEST.json`. Các quy tắc commit/reload và giới hạn đồng thời được đối chiếu tài liệu Modal Volume. [Tài liệu Modal Volume](https://modal.com/docs/guide/volumes)
