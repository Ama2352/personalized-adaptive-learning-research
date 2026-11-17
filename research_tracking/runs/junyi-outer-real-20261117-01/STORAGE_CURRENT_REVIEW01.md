# Dung lượng AKT còn lại sau đợt chuyển Drive

Kiểm metadata ngày17/11 bằng `storage_top01.py`, `storage_fast02.py` và `review_unused_metadata01.py`. Hai lượt quét đo cùng cấu trúc, lượt sau dùng directory entry nhẹ hơn. Không xóa dữ liệu trong các lượt kiểm kê này. `STORAGE_TOPLEVEL01.json` và `STORAGE_TOPLEVEL02.json` giữ số liệu tại hai thời điểm khi CPU A3 còn ghi Parquet.

## Vì sao vẫn lớn

Đợt đã dọn chỉ áp dụng35ZIP lịch sử,35.154.218.914byte, theo `research_tracking/runs/history-cleanup-20261117-01/ACCEPTANCE.json`. Danh mục55.784.079.663byte bản trùng là một nhóm khác. Cả21.604source trong danh mục bản trùng vẫn còn, keeper cũng còn với cùng kích thước và mtime nguồn chưa đổi. Đây là đối chiếu metadata với catalog đã hash trước đó, chưa thay bước hash lại trước xóa.

| Vùng | GiB logic | Vai trò và cách xử lý tiếp |
|---|---:|---|
| artifacts/akt/staged |38,67|Snapshot input/cache cũ. Ưu tiên đối chiếu với keeper và inventory trước khi thu gọn từng bản trùng.|
| artifacts/akt/window-cache |3,93|Cache các cohort/giai đoạn. Giữ bộ còn được request hoặc replay dùng.|
| artifacts/akt/confidence |3,88|Nguồn fit confidence và audit. Giữ confidence cuối cùng, lineage/OOF và dữ liệu cần cho phần còn thiếu.|
| artifacts/akt/local-tests |3,56|Nguồn/fixture/log kiểm. Phân biệt binary dựng lại được với log thất bại quan trọng.|
| artifacts/akt/local-calibration |khoảng2,5|Cache tạm được duyệt4GB, gồm đầu vào và output CPU outer đang hoàn tất. Kết quả chính đã lưu Drive.|
| experiments/akt/results/drive-offload-duplicates-20261116-01 |10,13|Payload duy nhất theo hash cùng các hardlink để upload. Xóa riêng tên gom có thể không trả dung lượng khi tên khác còn giữ cùng file.|
| Các results khác |khoảng31,28|Lịch sử fit/refit, checkpoints và exports. Giữ compact export cuối cùng và checkpoint cần resume/audit.|

Tổng theo đường dẫn là59,83GiB trong artifacts/akt và41,41GiB trong experiments/akt. Khử hardlink theo fileID trên hai vùng còn81,85GiB logical unique, nên khoảng19,4GiB bị cộng lặp khi cộng tổng folder. Chưa đo NTFS allocation/compression. D trống khoảng61,6GiB ở lượt kiểm.

## Thứ tự thu gọn có căn cứ

1. Dùng lại `UNUSED.csv` làm catalog gốc. Chỉ nhận row duplicate còn đúng source/keeper, hash lại cả hai và kiểm fileID/hardlink. Metadata hiện đã xác nhận21.604row cùng size/mtime.
2. Ghi allowlist cụ thể, inventory SHA và relocation từ snapshot cũ sang keeper hoặc Drive đã nghiệm thu. Loại toàn bộ input/output đang dùng của outer và các model/baseline còn thiếu.
3. Giữ model.pt, MODEL_INDEX.json, SUPPORT.zip của model cuối cùng, calibrator, dự đoán/nhãn, log và figure nghiên cứu. Dọn các tên bản sao đúng allowlist sau khi đủ điều kiện lưu giữ.
4. Xử lý cache/fixture có thể dựng lại trong đợt riêng. Vùng private chứa credentials và state upload, cần phân loại từng file khi thu gọn.

Chưa tuyên bố55,78GB sẽ được giải phóng nguyên vẹn. Dung lượng trả lại cần tính trên fileID cuối cùng được unlink và đo free space sau thao tác. Các thông tin đăng nhập giữ trong vùng private, ngoài gói bàn giao nghiên cứu.
