# Kiểm kê và chuẩn bị lưu trữ checkpoint/artifact

## Rà lại nhu cầu audit — kết luận hiện hành

`REVIEW02.json` và `RETENTION_REVIEW02.csv` bổ sung rà soát giá trị audit theo yêu cầu người dùng. Các kết luận UNUSED trước đây được giữ để truy vết thay đổi. Checkpoint A3 epoch 4/bước 584 duy nhất đã chuyển sang giữ audit. Bản trùng cần giữ nội dung và metadata gắn với run, còn các phần upload cần có ZIP/manifest để dựng lại. Chưa có quyền xóa file từ lượt rà này.

`review_audit_retention.py` hash lại các bản giữ, đối chiếu manifest snapshot và tham chiếu SHA trong metadata. Kiểm phần chia bằng đọc ZIP đầy đủ theo đúng kích thước mỗi phần. Gói 06 giữ checkpoint cần bảo toàn, metadata và danh mục mới. Các gói 01–05 giữ nguyên. `tests-review02.log` có kết quả kiểm hồi quy.

## Chuẩn bị upload Drive

`DRIVE_UPLOAD_STATE.json` ghi đợt đầu gồm sáu ZIP có sẵn, tổng 471.339.551 byte. Đã hash lại cả sáu ZIP và ghi manifest `FIRST_DRIVE_UPLOAD_BATCH.json` trong thư mục output. Phương án là upload trực tiếp từ D, giữ tên và cấu trúc theo đợt. Các ZIP lịch sử lớn được xét sau theo danh mục đã có, tránh tạo thêm bản nén khi dung lượng local thấp. Đợt đầu chỉ sao lưu model/hồ sơ cốt lõi, chưa thay thế mọi snapshot lịch sử. Kết nối Drive hiện tại khác tài khoản cá nhân người dùng từng dùng nên đang chờ xác nhận nơi lưu. Chưa upload và chưa cấp quyền xóa local.

Người dùng đã cung cấp thư mục đích `1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7` trên Drive cá nhân. Kiểm metadata qua connector hiện tại trả HTTP 404. Lệnh liệt kê trả danh sách rỗng nên chưa đủ kết luận thư mục trống. Đang chờ cấp quyền chỉnh sửa hoặc đổi kết nối sang tài khoản cá nhân. `DRIVE_UPLOAD_LOCAL_PINS.json` giữ SHA-256 và MD5 đã tính lại cho cả sáu ZIP để đối chiếu metadata sau upload. Chưa có file nào được upload. Upload cũng chưa giải phóng dung lượng local.

Ngày16/11/2026. Đây là hồ sơ vận hành lưu trữ, không phải kết quả dự báo hay bằng chứng cải thiện RQ.

## Mở các tài liệu sau

1. [Báo cáo tổng hợp](../../reports/ARTIFACT_RETENTION_20261116.md) giải thích các nhóm cần giữ, lưu trữ lạnh và unused.
2. [UNUSED.csv](../../../experiments/akt/results/artifact-offload-20261116-01/UNUSED.csv) có từng file, dung lượng, SHA, lý do và đường dẫn bản giữ.
3. [Thư mục upload](../../../experiments/akt/results/artifact-offload-20261116-01/) giữ các gói đã kiểm SHA.

## Kết quả

- Bản trùng cùng kích thước/SHA thực tế có21.604file, khoảng55,78GB. Mỗi bản được gán unused có một bản giữ ở ngoài danh mục unused.
- Hai bộ chia file upload A3 có9phần, khoảng1,37GB, ghép đúngSHA của ZIP đầy đủ đang giữ.
- Một checkpoint phục hồi29MB đã hết nhiệm vụ sau refit. Nhu cầu giữ binary lịch sử cho audit được ghi riêng ở cộtreason/action.
- Tổng UNUSED có21.614file, khoảng57,18GB. Đây là ứng viên thu gọn theo từng file và điều kiện, chưa thay đổi đường dẫn hoặc nội dung bản gốc.
- Model cuối, selected checkpoint, các epochA0 cần kiểm ranking, source canonical và input/cache nền vẫn ở nhóm giữ. Các bundle đã đóng cần lineage khi xử lý các file trùng bên trong.
- Các gói model/audit01–04 tổng430,6MB; gói catalog05 thêm12,2MB. Tổng năm gói khoảng442,8MB.
- Có35ZIP lịch sử lớn sẵn để upload nguyên file, tổng35,15GB, được định vị riêng. Đây là danh sách lưu trữ lạnh, chưa khẳng định mọi ZIP chứa dữ liệu duy nhất.

## Phương pháp và các pass

1. Đọc bản đồ repo, protocol nhóm hiện hành, STATE và chứng cứ nghiệm thu bốn model refit. Chỉ kiểm metadata ở các vùng bảo vệ. Bỏ qua private/Holdout/Test trong hash và đóng gói.
2. `audit_retention.py` kiểm kê252.427file đọc được và hash24.765binary, tổng khoảng116GB, bằng hai luồng streaming. File được kiểmsize/mtime trước và sau hash. HASHES.jsonl giữ kết quả có thể dùng lại.
3. Rà độc lập bằng `finalize_classification.py`: giữ baseline GAM, metadata phục hồi và một bản chứng của mỗi nhóm trùng; kiểm mọi keeper nằm ngoài unused. SUMMARY_PASS01 giữ kết luận trước sửa, SUMMARY là kết luận hiện hành.
4. `package_for_offload.py` kiểm pin các export, đóng gói và kiểm từngmemberZIP, hash nguồn trước/sau và hashZIP. Model/support gốc giữ nguyên.
5. `write_report.py` dựng báo cáo và nén catalog05, kiểm từngmember cùngsource. Kiểm regression của classifier có8ca đạt. Kiểm cuối giữ riêng trong ACCEPTANCE.json.

Lượt audit01 trong môi trường mặc định đã được ngắt khi chưa có output; audit02 ở điều kiện thực thi phù hợp hoàn tất. Các log được giữ. Không chạy training, truy cập Holdout hoặc dùng GPU trong task này.

## Giới hạn

- .pytest_cache bịWindows từ chối quyền đọc; vẫn là chưa kiểm.
- File nhỏ chưa được kiểm trùng toàn bộ. REVIEW khoảng10,57GB cần thêm bằng chứng phụ thuộc.
- Các ZIP khácSHA có thể chứa member chồng lặp; chưa suy rằng ZIP dư hoàn toàn từ tên hoặcCRC.
- Tất cả số dung lượng là dung lượnglogic. Không cộng đồng thời bảng theo nhóm và bảng theo đuôi file.
- Gói upload có metadata learnerIDs và thông tin vận hành; nên chọn phạm vi lưu trữ riêng phù hợp. File gốc và cả gói mới hiện nằm trênD, chưa upload ra dịch vụ.

## Cách chạy lại

Dùng `.venv/Scripts/python.exe -B` với các script trong thư mục này. Script đóng gói dùng output mới và từ chối ghi đè gói đã tạo. Khi cần tái kiểm gói hiện có, dùng pin trong PACKAGES/CATALOG_PACKAGE và manifest bên trongZIP. Các bản summary/catalog là kết quả phân loại theo thời điểm, cần cập nhật bằng run mới nếu phạm vi nghiên cứu thay đổi.

Các file nặng và CSV đầy đủ nằm trong `experiments/akt/results/artifact-offload-20261116-01/`. Git chỉ giữ script, chỉ mục, summary, test log và manifest nhỏ.
