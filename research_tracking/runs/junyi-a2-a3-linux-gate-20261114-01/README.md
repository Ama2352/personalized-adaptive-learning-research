# Kiểm nguồn A2/A3 trên Linux CPU ngày 14/11

Đã chạy một lượt CPU-only trên image runtime ghim hiện hành, tối đa600giây và reservation0,15USD theo quyền duyệt tranche nhỏ trong tổng30USD. Source ZIP1.242.250byte gồm345file, giữ riêng tại `artifacts/akt/modal/junyi-a2-a3-20261114-01/source.zip`. Không chuyển thêm dữ liệu Junyi và không cấp GPU.

Gate đạt **2.590 ca, 0 lỗi**, worker139,59giây. App `ap-8V9yRANyzLja7cOczYWOjX` đã dừng, có stop_acknowledged. ZIP kết quả105.466byte đã tải và kiểm inventory từng file.

Output chuẩn tại `experiments/akt/results/modal-junyi-a2-a3-cpu-20261114-01/`, gồm `receipt.json`, `artifacts.zip`, `app-budget-guard.json`, billing và reservation. `source-gate-preparation.json` giữ source/build inventory. Runner kế thừa CPU Gate A1 đã có, các tên input nội bộ của runner giữ để giảm thay đổi.

`settlement.json` giữ cận chi phí bảo thủ0,15USD. Billing tổng sau lượt đọc là15,54801318USD, không đủ để suy ra chi phí riêng vì số liệu tổng khác các snapshot lịch sử. Không dùng hiệu số âm làm bằng chứng lượt chạy miễn phí. Ledger đã đóng allocation và cộng toàn cap vào historical upper, tổng cận bảo thủ19,9793610043USD, giữ thêm3USD dự phòng.

Sau khi Gate chạy, người dùng yêu cầu xác minh sâu hơn việc tách CPU/GPU. Source cache graph/selection đã tiếp tục sửa. **Gate này chỉ đại diện source trong ZIP đã ghim, cần Gate cuối sau các sửa đổi mới trước training A2/A3.** Chưa có CUDA parity hoặc training A2/A3 trong đợt này.

Tạm dừng theo yêu cầu người dùng. Theo dõi tiếp ở [STATE confidence](../junyi-confidence-train80-20261114-01/STATE.json).
