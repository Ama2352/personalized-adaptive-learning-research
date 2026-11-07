# Nhật ký tích hợp recovery AKT

Ngày 07/11/2026. Phạm vi: engineering CPU synthetic; không train Junyi, không mở Holdout, không GPU/cloud. Python dùng `.venv` trong repository.

## Gói 1 — Schema và hợp đồng nguồn

Thêm `RecoveryOptions`, mặc định tắt. Config JSON chỉ nhận trường đã khai báo; source envelope và SHA-256 phải đi đôi, source thuộc một run khác trong `experiments/akt/results/`. Semantic hash giữ toàn bộ cấu hình, chỉ loại `run_id`, `output_dir`, recovery request/cadence. Authorization vẫn khóa toàn bộ config của attempt mới và kiểm envelope trước learner load.

Module `recovery.py` không import Torch. Envelope kết thúc do parent công bố, tham chiếu SHA của manifest, watchdog và các checkpoint đã commit. Không tìm checkpoint bằng filename mới nhất. Kiểm bytes, path traversal, build/data identity và cumulative wall budget. Envelope không ghi đè. Chưa kết nối training/CLI trong gói này.

Bằng chứng: `evidence/20261107-recovery-contract-01.log`: 21 passed; `evidence/20261107-recovery-schema-02.log`: 48 passed, 13.41s, gồm runner regression. Fixtures hoàn toàn synthetic, không unpickle checkpoint. Đây là chứng cứ kỹ thuật chuẩn bị RQ3, chưa là kết quả trả lời RQ.

Gate2 trước đó có 241 test PASS cho build cũ. Source mới làm evidence đó stale; sẽ refresh sau gói tích hợp ổn định. Kit Colab v6 vẫn là snapshot cũ, chưa chứa recovery mới.

## Gói 2 — Training, fork và CLI

Nối snapshot vào chính `train_epoch`, dùng cùng optimizer step và telemetry; không tạo một train loop thứ ba. Checkpoint chỉ chứa prefix đã optimizer-update. Batch đã đọc nhưng bị target/step cap chặn không được commit vào cursor. Restore gồm model, Adam, RNG, shuffle cursor, loss/count/token/gradient accounting và history selection/refit. Replay chạy trước restore RNG của model. Epoch/step/target caps không tăng khi fork; parent watchdog trừ cumulative worker wall time của các attempt trước.

Selection giữ early stopping, earliest best epoch và validation history. Refit vẫn khởi tạo/train trên scope riêng, không nhận weights inner selection. Best checkpoint được copy byte-identical sang attempt mới, không sửa identity hoặc source artifact. Snapshot trước validation giúp phục hồi khi validation/export thất bại mà không train lại epoch. Orphan best checkpoint cũ được giữ.

Public smoke/pilot CLI nhận recovery qua config; vẫn cần authorization mới theo exact config/build/Gate2. Terminal envelope do watchdog công bố sau worker exit/kill, không tự cấp quyền retry. Loader timings được giữ ở telemetry; recovery training identity dùng semantic config, frozen manifests/build và hash nội dung cohort thực sự tải.

Bằng chứng đã có: `20261107-recovery-integration-01.log` 38 passed; `20261107-recovery-cli-04.log` 2 passed/83.91s; `20261107-recovery-regression-02.log` 94 passed/36.54s. CLI tests tạo parent/worker subprocess thật, abrupt `os._exit(23)` sau committed batch và lỗi export sau selection; predictions/trọng số/counts khớp chính xác lượt continuous. External provenance, RAM và learner loader trong fixture được thay bằng dữ liệu tổng hợp, không phải successful real-data pilot hoặc real-host RAM acceptance.

Giữ các lần thất bại: CLI01 mất relative PYTHONPATH khi worker đổi cwd; CLI02 test launcher intercept cả Git subprocess; CLI03 prediction fixture chưa đổi trusted test root. Sửa harness, không nới production path guards. Regression01 có 90pass/4fail vì nhánh default-off vẫn truy identity của fixture authorization tối giản; sửa để không kiểm source khi recovery tắt. Regression02 đã pass toàn bộ gói đó. Mỗi retry dùng log mới.

Review bổ sung phát hiện phân loại checkpoint bằng hai lần Torch load giữ thừa model/Adam tensors; đổi sang một loader phân loại có identity validation và giải phóng payload sau restore. Chưa đo VRAM hoặc tuyên bố CUDA readiness. Test lại snapshot và Gate2 sau thay đổi này là điều kiện đóng gói.

Giới hạn: source/runtime/device/config semantics phải khớp; không tự migrate CPU→CUDA/Windows→Colab. Không resume lịch sử không có envelope. O(prefix) replay, dung lượng snapshot và cadence phải benchmark trước full training. Committed optimizer count có thể rollback phần chưa publish khi hard kill; tổng worker wall time vẫn cộng đủ. CPU exact equality không phải tolerance CUDA đã xác minh. Full-fold command vẫn bị vô hiệu hóa.
