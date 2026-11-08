# Theo dõi bằng chứng nghiên cứu KLTN

**Báo cáo tiến độ để trao đổi GVHD:** mở [bản tóm tắt08/11 — đợt01](supervisor_reports/2026-11-08/01_tien_do/BAO_CAO.md) và [notebook đầy đủ kết quả nghiên cứu](supervisor_reports/2026-11-08/01_tien_do/KET_QUA_NGHIEN_CUU.ipynb). Theo yêu cầu người dùng, thư mục hiện hành chỉ giữ đúng2file này. Gói26artifacts cũ và các bản đọc/receipts đã loại khỏi layout vẫn bảo toàn ở Git commit `2e63cd9`; không dùng hash/cellcount cũ chứng nhận bản notebook đang chỉnh. [Bản kỹ thuật revision6](reports/BAO_CAO_TIEN_DO_GVHD_20261108.md) giữ làm nguồn nền. ROOT chốt currentpins sau kiểm; không tự gửi ra ngoài.

**Protocol Development hiện hành:** [S04-A/S05-B V1](../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md) đã được nhóm chọn theo quyền user giao ngày08/11. Các snapshot chờ S04/S05 cũ được giữ làm lịch sử; việc chọn phương pháp không cấp quyền chi Modal, fullCV hoặc Holdout.

**Điểm bắt đầu cho người viết báo cáo:** [Bản đồ repository](../docs/REPOSITORY_MAP.md) và [mục lục báo cáo](reports/README.md). `reports/` là nơi thống nhất bản phân tích/số liệu tổng hợp; `runs/` là bundles bằng chứng theo run. Hai phần phục vụ diễn giải và kiểm chứng, chưa phải bản luận văn hoàn chỉnh. Output bootstrap baseline đã chuyển từ root `reports/` vào đây, có [hồ sơ relocation](reports/report_relocation_20261107.json).

**Collector/KT simulator mới:** [báo cáo DATA05–07](reports/simulator_collection_runner_20261107.md) phân biệt collector fixture, adapter, domain portability fix và corpus/trainer chưa hoàn thành. Registry được bổ sung từ các terminal run manifests đã tồn tại; đó là cập nhật chỉ mục, không là số thí nghiệm mới. Current source-bound software gate xem investigation state, không lấy số tests trong các snapshot lịch sử bên dưới.

Nội dung theo run có thể là pilot nghiên cứu, kiểm phần mềm hoặc archive một lần kiểm; không dùng số thư mục hay số tests để tính số thí nghiệm trả lời RQ. Với run đã đóng gói, đọc README và manifest trước kết quả. Các mục phân công/audit ban đầu bên dưới được giữ để truy lịch sử; trạng thái triển khai mới xem [progress](RESEARCH_PROGRESS.md) và [investigation state](../docs/thesis_recovery/INVESTIGATION_STATE.json).

## Mục đích và phạm vi

Thư mục này giữ dấu vết độc lập về tiến độ nghiên cứu Knowledge Tracing/adaptive learning. Đây là chỉ mục và bản diễn giải; artifact gốc vẫn ở vị trí ban đầu, kể cả khi Git ignore. Không chép dataset, predictions, checkpoints hay log lớn vào đây.

## Cấu trúc

- RESEARCH_PROGRESS.md: dashboard theo RQ, sprint và mô hình.
- EXPERIMENT_LEDGER.md: chronology các lần chạy, phân biệt trạng thái và mức xác minh.
- EVIDENCE_INDEX.md: đường dẫn, Git class, loại artifact và mức xác minh.
- VALIDITY_AUDIT.md: verdict giao thức, so sánh, leakage, reproducibility và thống kê.
- RESEARCH_GAPS.md: thiếu hụt theo mức ưu tiên.
- DECISION_LOG.md: quyết định có bằng chứng, không tự gán ngày lịch sử.
- CLAIM_EVIDENCE_MATRIX.md: RQ/claim → experiment → artifact.
- experiment_registry.json: registry theo schema 1.0.0.
- reports/initial_audit.md: báo cáo ban đầu; kỳ sau tạo báo cáo mới, không ghi đè.
- KE_HOACH_KIEM_TOAN.md: trình tự và giới hạn audit ban đầu.

## Phân công và nguyên tắc

- Agent triển khai mô hình chịu trách nhiệm code, cấu hình và thực thi đã được duyệt.
- Auditor độc lập chỉ đọc bằng chứng và chỉ cập nhật file trong thư mục này; không chạy model/test hoặc sửa artifact.
- Nhóm nghiên cứu quyết định thiết kế RQ, điều kiện thí nghiệm, mastery threshold và đánh giá chính sách.
- ID evidence/experiment/claim ổn định; không đổi ID khi cập nhật ghi chú.
- Git class: tracked, untracked, ignored, outside-repo, unknown. Git ignored không làm mất giá trị khoa học, nhưng hạn chế tính portable.

## Mức bằng chứng

- VERIFIED: artifact gốc đã được mở/đối chiếu trực tiếp.
- REPORTED: chỉ thấy trong báo cáo/ghi chú, chưa đối chiếu artifact gốc.
- INFERRED: suy ra gián tiếp, chưa đủ chứng minh.
- MISSING: không tìm thấy trong phạm vi đã kiểm tra.
- CONFLICTING: nguồn mâu thuẫn.
- NOT APPLICABLE: không liên quan.

Mức này áp dụng cho từng claim. Execution status độc lập với validity: run COMPLETED có thể chưa đủ hợp lệ/tái lập.

## Vòng đời và cập nhật

Vòng đời run: PLANNED, RUNNING, COMPLETED, FAILED, INTERRUPTED, UNKNOWN. Không suy ra completion từ tên thư mục. Ở lượt sau: đọc registry/report cũ; tìm artifact mới bằng filesystem cộng Git; đối chiếu manifest/config/hash/log/metrics; cập nhật cùng ID nếu cùng run, tạo ID mới nếu execution mới; giữ báo cáo lịch sử và ghi run superseding cùng khác biệt.

Artifact ignored được tham chiếu bằng repo-relative path và metadata cần thiết. Không đổi .gitignore, force-add, di chuyển hoặc sao chép dữ liệu nhạy cảm. Timestamp chỉ là gợi ý. Với thư mục đang ghi, hoãn đọc đến khi manifest/log ổn định.

## Registry

experiment_registry.json có schema_version, updated_on, scope_note, evidence_levels, execution_lifecycle và experiments[]. Mỗi record lưu ID, model/variant, objective, RQ, sprint, dataset/protocol, execution/verification status, refs config/code/metrics/evidence, kết quả, giới hạn và liên hệ run. Không nhúng log/prediction.

## Cập nhật CPU07/11/2026

User cho phép engineering CPU và lưu evidence ngày07/11. Quy tắc auditor-only ở trên mô tả lượt audit cũ. runs/ giữ diagnostic bounded, simulated traces và README/manifest mỗi run. Historical artifacts giữ vị trí.
