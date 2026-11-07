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

## Review cuối — Hai góc cần đóng

Gate2 CLI-recovery07 phát hiện lỗi file tạm checkpoint khi pytest run path sâu trên Windows: destination239ký tự nhưng tên tạm thêm basename+UUID vượt giới hạn đường dẫn thông thường. Đây là lỗi portability thực, sẽ rút ngắn tên tạm trong cùng thư mục; không đổi registry/global settings hoặc bỏ guard. Giữ logs/JUnit của lần thất bại.

Adversarial review còn chỉ ra attempt thất bại trước checkpoint mới phải kế thừa recovery pointer từ source để cumulative wall time không mất dấu. Dự kiến reserve recovery attempt trước loader, copy byte-identical các dependency đã kiểm SHA và ghi pointer trước training. Source run giữ nguyên; next attempt vẫn kiểm checkpoint/model/cohort identity. Cần test early-loading failure và budget chain trước Gate2 cuối.

Hai sửa đổi đã thực hiện: tên tạm checkpoint/copy ngắn trong cùng directory; recovery attempt reserve trước loader và kế thừa verified checkpoint dependencies/pointer. Test early-loader-failure kiểm chain12.5s+7s=19.5s, attempt2, source hashes giữ nguyên. Targeted parent/runner suite51passed14.68s, log `evidence/20261107-recovery-parent-01.log`. Worker stdout/stderr được parent lưu riêng, không overwrite; hard kill vẫn có envelope dựa committed pointer. Gate2 CLI-recovery07 giữ kết quả271pass2fail (Windows path), không publish. Gate2 CLI-recovery08 đang kiểm source đã sửa, không được ghi PASS trước output.

Kit Colab v7 build120files, SHA018888bbee3718f0c9ce9222ae079315aefca67d176e4d2be8ec49d78f69c9cc. Đây là source package mới; chưa kiểm thực tế trên Colab/Linux/CUDA. V6 là snapshot đã có local isolated-suite proof trước gói recovery. Không dùng results cũ để tuyên bố toàn bộ v7 đã chạy Colab.

## Nghiệm thu cuối gói

Gate2 CLI-recovery08: **274passed,0failed,0errors,0skipped**,217.71s pytest. Report SHA256 `51e5367ab41724e01336943df207b1fc6364f5db826b3d5bb65447c0e1984e9f`, current pointer được publish và `require_gate2_evidence` kiểm PASS. Build/lock/upstream hash trước–sau không đổi. Gói `research_tracking/runs/cpu-akt-recovery-20261107-01` archive24outputs kèm source SHA, cả failure07 và success08.

Đã kiểm lại artifact CLI của chính Gate2-08:2cases, model/Adam/Python/NumPy/Torch/CUDA-state-container equality exact,9prediction rows/case giống hệt continuous,85train targets,3updates,selected epoch1,attempt2. CUDA container rỗng trong CPU fixture, không là CUDA test. `lifecycle_proof.json` giữ predictions tổng hợp và inventory hashes, không chép model/data thật. Bundle integrity verified; đây là nghiệm thu kỹ thuật CPU cho REC01–REC06, không là Gate4 hoặc RQ3 result.
