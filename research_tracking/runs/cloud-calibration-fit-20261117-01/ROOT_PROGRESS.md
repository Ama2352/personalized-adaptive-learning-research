# Tích hợp calibration cloud ngày 17/11

## Đã hoàn thành tại local

Đã nối typed Volume root cho raw Parquet và CPU fit V1. API mặc định giữ đường ghi local của các caller cũ. Root cloud resolve mount `/artifacts` một lần, rồi kiểm path vật lý và alias bên dưới. CPU helper kiểm calibration10 đầy đủ, binding nguồn, roles, encoding, manifest và shard SHA trước fit. Kết quả có config, temperature, manifest, tài nguyên và completion, trả filelist rõ ràng cho CPU uploader.

Rà soát độc lập phát hiện đổi phase có thể làm mất graph context cache đã gắn. Producer hiện truyền context_cache qua set_phase. Regression mới giữ đúng object cache. Tổng kiểm tích hợp mới nhất tại `../junyi-cuda-inference-20261117-01/tests04.txt` đạt70ca,1skip trênWindows. Skip thuộc phép tạo symlink. Manifest nhánh MANIFEST.json ghi thời điểm trước sửa cache; ROOT_MANIFEST02.json ghim source sau sửa và các log cloud.

## Diễn tiến Linux CPU

Image đầu thiếu sklearn theo import evaluation, được phát hiện trong log collection. Lượt gửi input đầu còn gặp timeout kết nối trước khi gửi tác vụ. Lượt CPU thực tiếp theo đã lưu kết quả trên Volume/Drive nhưng hết180giây lúc upload log. Recovery dùng worker CPU đồng bộ để gửi tiếp đúng các file đã có, SHA server đạt. Hai file nhỏ đã đọc qua Drive và khớp SHA, cho biết lỗi dependency image. Đã ghim scikit-learn/scipy như local và chạy tranche mới cpu-tests02 với hạn900giây để tách failure collection khỏi failure truyền tải. Log/receipt sau đó phát hiện thiếu PyArrow ở image; đã bổ sung đúng26.0.1 và chuyển routing ap-south sau lỗi input-plane mặc định. Tranche cpu-tests03 đạt98/98ca trong5,97giây, gồm trusted-mount symlink và numeric bridge. Drive xác nhận SHA ba file config/result/log, App đã kết thúc. Cấu hình cloud giữ SHA các source/tests và phiên bản thư viện. Xem LINUX_ACCEPTANCE.json và LINUX_CPU_GATE03.json.

## Trình tự tiếp theo

1. Nghiệm thu Linux CPU gate và lưu receipt Drive.
2. Chuẩn bị windows dùng chung cùng ba context cache trên CPU. Cache phải khóa calibration_predict, encoding90, đúng target/prefix; dùng WindowCache/GraphContextCache hiện có.
3. GPU nhận đầu vào đã chuẩn bị, chấm batch128, xuất numeric probabilities có window ID. CPU bridge nối lại record/labels và kiểm coverage trước xuất raw Parquet.
4. Trả GPU rồi CPU12–16GiB fit scalarV1, commit Volume và đồng bộ Drive Sang. Toàn bộ model refit giữ nguyên, không chọn lại epoch bằng calibration.

Input plan03 gồm177file,134.424.893byte ở bundle cloud-calibration-inputs, gồm model refit hiện có và cache calibration14MB. Mỗi thay đổi source sau freeze cần plan mới. Kiểm kỹ thuật được giữ riêng với kết quả trả lời RQ.
