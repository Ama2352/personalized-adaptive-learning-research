# Nhật ký tích hợp recovery AKT

Ngày 07/11/2026. Phạm vi: engineering CPU synthetic; không train Junyi, không mở Holdout, không GPU/cloud. Python dùng `.venv` trong repository.

## Gói 1 — Schema và hợp đồng nguồn

Thêm `RecoveryOptions`, mặc định tắt. Config JSON chỉ nhận trường đã khai báo; source envelope và SHA-256 phải đi đôi, source thuộc một run khác trong `experiments/akt/results/`. Semantic hash giữ toàn bộ cấu hình, chỉ loại `run_id`, `output_dir`, recovery request/cadence. Authorization vẫn khóa toàn bộ config của attempt mới và kiểm envelope trước learner load.

Module `recovery.py` không import Torch. Envelope kết thúc do parent công bố, tham chiếu SHA của manifest, watchdog và các checkpoint đã commit. Không tìm checkpoint bằng filename mới nhất. Kiểm bytes, path traversal, build/data identity và cumulative wall budget. Envelope không ghi đè. Chưa kết nối training/CLI trong gói này.

Bằng chứng: `evidence/20261107-recovery-contract-01.log`: 21 passed; `evidence/20261107-recovery-schema-02.log`: 48 passed, 13.41s, gồm runner regression. Fixtures hoàn toàn synthetic, không unpickle checkpoint. Đây là chứng cứ kỹ thuật chuẩn bị RQ3, chưa là kết quả trả lời RQ.

Gate2 trước đó có 241 test PASS cho build cũ. Source mới làm evidence đó stale; sẽ refresh sau gói tích hợp ổn định. Kit Colab v6 vẫn là snapshot cũ, chưa chứa recovery mới.
