# Kiểm kê checkpoint/artifact và gói lưu trữ ngày16/11/2026

## Các nhóm lịch sử có thể upload thêm

Đã gom 35 ZIP có sẵn vào [drive-offload-history-20261116-01](<D:/Dev/KLTN/experiments/akt/results/drive-offload-history-20261116-01/>), tổng35,15GB, chia A3 recovery2,73GB, refit history14,86GB, T4 history8,94GB và pilot history8,62GB. Dùng hardlink cùng volume, lượt gom phát sinh khoảng49KB metadata trước khi thêm hướng dẫn. Nguồn ZIP giữ nguyên. `MANIFEST.json` giữ ánh xạ tên upload và SHA từ audit trước; lượt gom xác nhận size/mtime cùng file identity, chưa hash lại toàn bộ35GB. `COLD_ARCHIVE_FOLDER_STATE.json` giữ trạng thái.

Các ZIP có thể chứa nội dung chồng lặp với gói dedup10,88GB. Việc chọn lưu toàn bộ cần cân nhắc dung lượng Drive. Nhóm nào được người dùng upload và nghiệm thu thì mới duyệt dọn tương ứng. Dung lượng trống D quan sát đầu lượt gom còn2,67GB. Không có thao tác dọn trong lượt chuẩn bị này.

## Thư mục gom cho người dùng upload trực tiếp

[drive-offload-duplicates-20261116-01](<D:/Dev/KLTN/experiments/akt/results/drive-offload-duplicates-20261116-01/>) đã gom 2.219 nội dung duy nhất đại diện cho 21.604 đường dẫn trùng, tổng logic 55,78 GB. Cần upload nguyên thư mục khoảng 10,88 GB bằng Drive trên trình duyệt. `CONTENT` dùng hardlink tới các bản giữ trên D, nên dữ liệu nhị phân tiếp tục dùng chung với nguồn. Các file được giữ nguyên trong lúc chờ xác nhận upload. `MANIFEST.json` giữ ánh xạ đầy đủ, `AUDIT_METADATA.zip` giữ 869 metadata gồm 21 manifest snapshot, helper và hướng dẫn nằm cùng thư mục.

Đã chạy helper kiểm đủ SHA 2.219 nội dung và toàn bộ 21.604 ánh xạ, kiểm metadata ZIP và 9 ca tổng hợp. [MANUAL_OFFLOAD_STATE.json](<D:/Dev/KLTN/research_tracking/runs/artifact-retention-audit-20261116-01/MANUAL_OFFLOAD_STATE.json>) giữ nghiệm thu. Chưa phục hồi toàn bộ đường dẫn lịch sử vào thư mục độc lập. Sau khi người dùng báo upload xong sẽ kiểm bản Drive và điều kiện phục hồi trước dọn đúng danh mục.

Kiểm file identity cho thấy 55,78 GB logic gồm các bản đã dùng chung dữ liệu qua hardlink. Nhóm có thể hết liên kết sau dọn tương ứng khoảng 46,00 GB logic. Dung lượng thực giải phóng phải đo sau thao tác. Thư mục gom làm thay đổi số link filesystem của các bản giữ, nội dung và đường dẫn nguồn được bảo toàn. Bản gốc tiếp tục còn trên D.

## Đã sao lưu đợt đầu lên Drive

Sáu gói model/audit đã được sao lưu vào [thư mục KLTN](https://drive.google.com/drive/folders/1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7). Tổng dữ liệu gốc 471,34 MB. Ba ZIP nhỏ được upload trực tiếp, ba ZIP lớn chia thành bảy phần theo giới hạn 100 MiB của công cụ. `00_DOC_TRUOC.md`, `DRIVE_PARTS_MANIFEST.json` và `restore_drive_zips.py` trong thư mục hướng dẫn ghép lại đúng ZIP gốc. Đã đối chiếu dung lượng, thư mục và SHA-256 đọc lại từ Drive cho đủ 13 file. [Biên nhận](<D:/Dev/KLTN/research_tracking/runs/artifact-retention-audit-20261116-01/DRIVE_UPLOAD_RECEIPT01.json>) giữ ID và pin từng file.

File gốc trên D vẫn khớp SHA. Các phần chia thêm khoảng 423,90 MB local. Dung lượng được giải phóng trong lượt upload là 0 byte. Các snapshot lịch sử và danh mục 55,78 GB bản trùng ứng viên gộp còn cần xử lý tiếp theo điều kiện audit bên dưới. Helper đạt 12 ca tổng hợp trên Windows. Đã kiểm phép nối các phần local bằng SHA, còn việc chạy helper phục hồi ZIP nghiên cứu và kiểm Linux chưa được thực hiện.

## Kết luận cập nhật sau rà lại giá trị audit

Nhãn `UNUSED` ở lượt đầu quá rộng khi diễn giải nhu cầu audit lâu dài. Hoàn tất training chỉ kết thúc nhiệm vụ chạy tiếp của checkpoint. Checkpoint trung gian vẫn lưu trạng thái model, optimizer, RNG và vị trí xử lý tại một thời điểm cụ thể. Model cuối và log không thay thế được toàn bộ trạng thái đó. Căn cứ ở `src/knowledge_tracing/akt/checkpoint.py` và `_run_epochs` trong `src/knowledge_tracing/akt/research_junyi_refit.py`.

Danh mục hiện hành là [RETENTION_REVIEW02.csv](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/RETENTION_REVIEW02.csv>). `UNUSED.csv` và gói catalog 05 được giữ như lịch sử phân loại ban đầu. Bảng dung lượng ở các phần sau vẫn mô tả lượt kiểm đầu.

| Nhóm ban đầu | Kết luận sau rà lại | Điều kiện giữ bằng chứng |
|---|---|---|
| 55,78 GB bản trùng | Có thể gộp bản lưu vật lý, có điều kiện | Giữ một bản nội dung đúng SHA, metadata nguồn, ánh xạ đường dẫn và khả năng dựng lại snapshot |
| 1,37 GB phần chia upload | Có thể dựng lại từ ZIP đầy đủ, có điều kiện | Giữ ZIP đầy đủ và manifest chia phần. Kiểm từng phần dựng lại đúng SHA |
| 28,94 MB checkpoint trung gian duy nhất | Chuyển sang **giữ audit** | Giữ `state.pt`, `metadata.json` và `COMPLETE.json` cùng nhau |

Checkpoint cần giữ là A3 refit tại epoch 4, bước 584 trong `colab-junyi-a3-refit-20261115-001`. File có SHA riêng và metadata phục hồi tương ứng. Việc refit 9 epoch đã xong không đủ làm căn cứ bỏ trạng thái duy nhất này. Gói [06_AUDIT_RETENTION_REVIEW.zip](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/06_AUDIT_RETENTION_REVIEW.zip>) giữ bản sao checkpoint này cùng metadata và danh mục rà lại.

Các gói 01–05 chỉ giữ model chính, một phần hồ sơ training và catalog. Chúng chưa sao lưu toàn bộ nội dung 57,18 GB trong danh mục cũ. Khi gộp bản trùng, bản giữ có thể là cache dữ liệu, checkpoint lịch sử hoặc thành phần snapshot vẫn cần để audit. Cần bảo toàn cả nội dung lẫn bằng chứng nó thuộc run nào. Có thể phải tải lại bản lưu lạnh nếu kiểm tra lịch sử sau này.

Chưa cho phép dọn file nào qua lượt rà này. Các file gốc, bundle và gói cũ được giữ nguyên. [REVIEW02.json](<D:/Dev/KLTN/research_tracking/runs/artifact-retention-audit-20261116-01/REVIEW02.json>) ghi phạm vi, kết quả kiểm lại và giới hạn.

Lượt rà bổ sung đã kiểm lại đủ 21.614 dòng. Đã hash lại 2.220 bản giữ, tổng 11,54 GB, đối chiếu được 21.004 file snapshot với `INPUTS.json`, quét 8.403 file JSON metadata và dựng lại đủ 9 phần upload từ ZIP theo đúng SHA. Checkpoint A3 duy nhất được tham chiếu trong `a3-t4-first-tranche-acceptance01.json` và các manifest của run Colab đầu. Kết quả kiểm hồi quy đạt 11 ca. Các tham chiếu SHA xác nhận mối liên hệ với hồ sơ lịch sử, còn việc dựng lại toàn bộ mọi snapshot vẫn chưa được thực hiện.

[REVIEW02_KEEPERS.csv](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/REVIEW02_KEEPERS.csv>) định vị 2.220 bản nội dung phải được bảo toàn nếu muốn gộp bản trùng. Danh mục này chưa bao gồm toàn bộ metadata và các file KEEP khác của KLTN. Trong CSV rà lại, cột `review_status` và `required_before_cleanup_vi` là quyết định hiện hành. Các cột phân loại cũ được giữ để thấy vì sao kết luận thay đổi. Gói 06 có dung lượng 28,5 MB, chưa upload. [REVIEW02_ACCEPTANCE.json](<D:/Dev/KLTN/research_tracking/runs/artifact-retention-audit-20261116-01/REVIEW02_ACCEPTANCE.json>) ghi nghiệm thu cuối.

## Kết quả chính

Đã kiểm kê metadata 252,427 file trong các vùng đọc được và hash thực tế khoảng116,00GB binary. Danh mục UNUSED có 21,614 file, tổng 57.18GB. Các con sốGB trong báo cáo dùng10^9byte. File gốc giữ nguyên. Gói nén mới là bản sao để người dùng chọn nơi upload.

| Nhóm UNUSED | File | Dung lượng | Căn cứ |
|---|---:|---:|---|
| Bản local trùng nội dung | 21,604 | 55.78GB | Cùng size/SHA thực tế; mỗi dòng chỉ rõ bản giữ ngoài UNUSED |
| Phần chia upload cũ | 9 | 1.37GB | Ghép tuần tự khớpSHA ZIP đầy đủ; A3 đã refit xong |
| Checkpoint phục hồi đã hết nhiệm vụ | 1 | 0.03GB | Đợt refit tương ứng đã nghiệm thu; binary lịch sử vẫn có thể giữ lạnh theo nhu cầu audit |

## Vị trí các bản dư lớn

| Vùng | File trong UNUSED | Tổng |
|---|---:|---:|
| [artifacts/akt/staged](<D:/Dev/KLTN/artifacts/akt/staged>) | 21,004 | 38.90GB |
| [experiments/akt/results](<D:/Dev/KLTN/experiments/akt/results>) | 594 | 18.26GB |
| [artifacts/akt/modal](<D:/Dev/KLTN/artifacts/akt/modal>) | 16 | 0.02GB |

Chi tiết từng file, SHA, đường dẫn bản giữ, phân loại nguồn và điều kiện xử lý tại [UNUSED.csv](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/UNUSED.csv>). Các snapshot/bundle đã đóng cần giữ lineage khi thu gọn, dùng relocation hoặc hướng dẫn dựng lại đúngSHA. Danh mục này phục vụ duyệt từng nhóm; các bản gốc trong thư mục hiện vẫn tồn tại.

## Các file phải giữ cho công việc tiếp theo

- Bốn model refit JunyiA0–A3, MODEL_INDEX và SUPPORT.zip để calibration/đánh giá độc lập.
- Bốn checkpoint selected-fit được chọn và các bản epochA0 còn cần đối chiếu ranking validationbatch1/128.
- Bảy checkpointGrade10 cùngsource/mapping để hoàn thiện refit và vòng kín. Gói export gốc có thêm một A0Junyi best-so-far lịch sử.
- Encoding, learner roles, cohort và cache nền, graph/confidence TRAIN80, source/dependency và baseline lịch sử.
- Log, prediction và figure phục vụ các kết luận nghiên cứu; metadata của các run lỗi quan trọng.

Danh sách chi tiết tại [KEEP_ACTIVE.csv](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/KEEP_ACTIVE.csv>).

## Lưu trữ lạnh

11,139 file khoảng48.84GB thuộc ARCHIVE_ONLY. Đây là artifact lịch sử hoặc input snapshot, vẫn có giá trị truy vết và tái lập. Khi cần kiểm lại run cũ có thể phải tải chúng về. Các rawcheckpoint trùng đã tách khỏi nhóm này.

Đã định vị35 ZIP lớn có thể upload nguyên file, tổng35.15GB. Chúng đã có SHA thực tế, giúp tránh tạo thêm một bản nén hàng chụcGB trênD. Danh sách tại [EXISTING_ARCHIVES_READY.json](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/EXISTING_ARCHIVES_READY.json>).

## Gói upload đã tạo và kiểm

| Gói | Dung lượng | Nội dung |
|---|---:|---|
| [01_JUNYI_REFIT_A0_A3.zip](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/01_JUNYI_REFIT_A0_A3.zip>) | 108.4MB | Bốn model refit chính để calibration và đánh giá tiếp theo. |
| [02_JUNYI_SELECTED_A0_A3.zip](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/02_JUNYI_SELECTED_A0_A3.zip>) | 113.1MB | Bốn checkpoint selected-fit được chọn, phục vụ audit lựa chọn epoch. |
| [03_GRADE10_SELECTED_AND_LEGACY.zip](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/03_GRADE10_SELECTED_AND_LEGACY.zip>) | 202.3MB | Bảy checkpoint Grade10 đã chọn và một A0Junyi lịch sử trong gói export gốc. |
| [04_CORE_TRAINING_AUDIT.zip](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/04_CORE_TRAINING_AUDIT.zip>) | 6.7MB | Log, cấu hình, nghiệm thu, figure và báo cáo của các đợt training chính. |

Tổng bốn gói 430.6MB. Đã đối chiếuSHA nguồn trước/sau, từng member trongZIP và SHA cảZIP. Giữ cấu trúc đường dẫn khi giải nén. Các model.pt dùng loaderKLTN cùng cấu hình vàmapping; SUPPORT.zip đi kèm mỗi export. Metadata có learnerIDs và thông tin vận hành, phù hợp kho lưu trữ riêng. Gói model không chứa file tương tácJunyi gốc. Các ZIP lịch sử có thể chứa prediction/labels hoặc cohort nên cần xem nội dung khi chọn phạm vi chia sẻ.

## Phần cần rà thêm và giới hạn

Gói thứ năm [05_RETENTION_CATALOGS.zip](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/05_RETENTION_CATALOGS.zip>) dung lượng 12,2 MB giữ danh mục phân loại, inventory và kết quả hash. Tổng cả năm gói là 442,8 MB. [UPLOAD_INDEX.json](<D:/Dev/KLTN/experiments/akt/results/artifact-offload-20261116-01/UPLOAD_INDEX.json>) là chỉ mục upload hiện hành. Gói catalog giữ bản báo cáo tại thời điểm đóng gói, trước đoạn nghiệm thu bổ sung này.

Kiểm cuối đạt đối với SHA của cả năm ZIP, SHA các catalog, 21.604 liên kết bản trùng/bản giữ và model nguồn. Tám ca kiểm classifier đạt. Xem [ACCEPTANCE.json](<D:/Dev/KLTN/research_tracking/runs/artifact-retention-audit-20261116-01/ACCEPTANCE.json>).

- 127,966 file khoảng10.57GB ở REVIEW, phần lớn runtime/localtests; chưa đủ căn cứ kết luận unused.
- .pytest_cache bịWindows từ chối quyền đọc trong lượt kiểm. Nó được ghi riêng trong SUMMARY, không được gán unused.
- Vùngprivate/credentials, Holdout/Test được bỏ qua. Vùng bảo vệBKT/dataset/venv/WSL giữ nguyên.
- SHA tập trung binary>=1MiB có cùng kích thước, model/cache đang dùng và ZIP>=100MiB. Chưa kiểm trùng toàn bộ file nhỏ.
- ZIP khácSHA có thể chứa các member chồng lặp. Chưa suy bảnZIP nào dư hoàn toàn chỉ từ tên hoặc CRC.
- KEEP_ACTIVE là danh mục bảo thủ cho workflow hiện hành; việc mở thí nghiệm mới có thể thay đổi phụ thuộc.

## Cách sử dụng

1. Giữ model refit chính và các input đang dùng trênD trong giai đoạn calibration/đánh giá.
2. Chọn các gói model/audit ở trên để uploadDrive hoặcHuggingFace. Sau upload cần tải kiểm đúng phiên bản/SHA trước khi đổi vị trí bản local.
3. Với lịch sử lớn, upload từngZIP đã có theo danh mục lưu trữ lạnh.
4. Duyệt từng nhóm UNUSED khi cần thu gọn, đối chiếu bản giữ và giữ đường dẫn manifest có thể truy vết.

Nguồn kiểm tại [research_tracking/runs/artifact-retention-audit-20261116-01/SUMMARY.json](<D:/Dev/KLTN/research_tracking/runs/artifact-retention-audit-20261116-01/SUMMARY.json>) và [research_tracking/runs/artifact-retention-audit-20261116-01/CLASSIFICATION_REVIEW.json](<D:/Dev/KLTN/research_tracking/runs/artifact-retention-audit-20261116-01/CLASSIFICATION_REVIEW.json>).


## Rà bổ sung trong lúc upload hai thư mục lớn

Đã kiểm riêng 416 file, tổng 3,56 GB có thể đề xuất dọn. Gồm 16 phần truyền tạm 1,79 GB có ZIP/Drive đối chiếu và 400 checkpoint pytest tổng hợp 1,77 GB. Đã lưu hồ sơ nhỏ lên Drive và đọc lại SHA khớp. Chưa xóa, đang chờ duyệt danh sách cụ thể. Hai thư mục upload cùng các inode liên quan được loại khỏi danh sách. [Chi tiết, giới hạn và nguồn kiểm](../runs/artifact-retention-audit-20261116-01/STORAGE_REVIEW02.md).


## Cập nhật sau duyệt dọn

Đã xóa đúng 416 file / 3,56 GB theo xác nhận người dùng. Kiểm sau xóa đạt, bốn ZIP giữ lại vẫn khớp SHA. D trống khoảng 34,25 GB tại thời điểm kết thúc. Hai thư mục upload lớn tiếp tục giữ nguyên. [Nhật ký và giới hạn kiểm](../runs/artifact-retention-audit-20261116-01/STORAGE_REVIEW02.md).


## Upload lịch sử đã nghiệm thu ngày 17/11

Thư mục `drive-offload-history-20261116-01` đã sao lưu đủ 35 ZIP cùng hai file hỗ trợ, tổng 35,15 GB. [Thư mục Drive](https://drive.google.com/drive/folders/1V-H0estsyh2oQQ3qnfapU9qSpGZFoF3H) giữ dữ liệu, [biên nhận đọc lại](../runs/drive-history-upload-20261116-01/READBACK_ACCEPTANCE.json) xác nhận SHA-256 server của 37/37 file khớp nguồn, tên/parent/size đúng kế hoạch. Bản local còn trên D; việc dọn các đường dẫn archive và hardlink vẫn cần đúng inventory và điều kiện riêng. Thư mục duplicates là lượt khác, chưa được gán hoàn tất từ kết quả này.
