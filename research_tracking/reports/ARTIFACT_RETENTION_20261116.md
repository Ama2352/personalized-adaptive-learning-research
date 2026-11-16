# Kiểm kê checkpoint/artifact và gói lưu trữ ngày16/11/2026

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
