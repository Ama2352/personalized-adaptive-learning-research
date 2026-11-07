# Mục lục báo cáo và phân tích KLTN

Đây là nơi thống nhất cho báo cáo/phân tích tổng hợp. Bằng chứng theo run nằm ở [../runs](../runs/); dữ liệu/models/predictions lớn giữ ở artifacts/experiments theo [bản đồ repository](../../docs/REPOSITORY_MAP.md). Các file dưới đây có vai trò khác nhau, không phải tất cả đều là kết luận nghiên cứu hoặc chương luận văn.

## Baseline đã có kết quả

| Nội dung | Báo cáo đọc được | Số liệu tổng hợp |
|---|---|---|
| BKT Junyi | [BKT results](../../docs/bkt-baseline-results.md) | Nguồn CV/refit lịch sử trong experiments, xem báo cáo |
| BKT–GAM-KT Development CV | [Bản ngắn](../../docs/bkt-gam-kt-benchmark.md), [bản chi tiết](../../docs/research/bkt-gam-kt-baseline-benchmark-report.md) | [Paired bootstrap JSON](paired_cluster_bootstrap_bkt_gam.json) |

JSON bootstrap chuyển từ root `reports/` với bytes/SHA giữ nguyên. [Hồ sơ relocation](report_relocation_20261107.json) lưu vị trí cũ/mới và hashes; số liệu không được tính lại. Bootstrap hai baseline graph-free không chứng minh graph hoặc chính sách học có ích.

## RQ1/RQ2 — Chẩn đoán và pilot

- [cpu_rq12_20261107.md](cpu_rq12_20261107.md): chuỗi prediction→decision, graph package, retention/re-entry và giới hạn nguồn.
- [cpu_pilots_20261107.md](cpu_pilots_20261107.md): approved bounded factorial và Junyi order pilots.
- [cpu_matched_controls_20261107.md](cpu_matched_controls_20261107.md): graph controls và độ phủ của thay đổi cạnh.
- [cpu_common_population_20261107.md](cpu_common_population_20261107.md): so sánh trên cùng learner/child opportunities, missingness và weak exposure.

Đọc run IDs/manifests được mỗi báo cáo chỉ ra. Pilot không tự trở thành confirmatory result; không suy lợi ích nhân quả từ logged Junyi order.

## Kỹ thuật và tính tái lập

- [simulator_kt_interface_20261107.md](simulator_kt_interface_20261107.md): typed session/query/checkpoint bridge, export fix, frozen inference và independent batching. Đây là engineering evidence, không là CG-AKT efficacy.
- `git_evidence_verification_*.json`: đối chiếu output hashes với bytes trong Git.
- `colab_bundle_*_verification_*.json`, `colab_upstream_*_inventory_*.json`: kiểm bundle/dependency/portability; không tự chứng minh đã chạy Colab/CUDA.
- Các JSON có tên `coverage`, `followup`, `diagnostics_verification`: số liệu kiểm tra hỗ trợ; đọc scope trong file và báo cáo tương ứng, không lấy tên file làm verdict nghiên cứu.

## Draft, lịch sử và hồ sơ vận hành

- [CPU09_CPU10_PROTOCOL_DRAFT.md](CPU09_CPU10_PROTOCOL_DRAFT.md): protocol pilot/draft; phạm vi được duyệt và confirmatory design là hai việc riêng.
- [initial_audit.md](initial_audit.md): snapshot audit ban đầu; không dùng inventory cũ thay trạng thái mới.
- [report_relocation_20261107.json](report_relocation_20261107.json), `temporary_relocation_*.json`, `uncommitted_inventory_*.json`: hồ sơ sắp xếp workspace, không phải kết quả mô hình.

## Quy ước duy trì

1. Bản diễn giải theo chủ đề có tên rõ và ngày; thêm vào đúng mục ở đây. JSON tổng hợp đi cùng báo cáo hoặc bundle có provenance.
2. Một execution mới dùng run ID mới trong `research_tracking/runs/`; không tạo thêm một root `reports/` hay thư mục tên chung chung để chứa cùng loại file.
3. Không đổi số liệu, seed hoặc protocol khi di chuyển file. Ghi inventory trước, so SHA sau và cập nhật chỉ mục; manifests/models/predictions/bundles lịch sử giữ nguyên.
4. Bản luận văn sau này trích nhận định có scope, bảng/số liệu và run ID; không đưa toàn bộ debug logs vào thân báo cáo.
