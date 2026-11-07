# Bằng chứng CPU refit recovery, Gate2 và pathway parity

Ngày07/11/2026. Đây là engineering gate và source-mechanism unit evidence, chưa là confirmatory research experiment.

- Refit/selection/training suite32passed26.17s. Actual AKT CPU dropout ngắt sau epoch1, khôi phục đủ3epoch, khớp weights/Adam/RNG/loss. Config, learner scope, selected epoch budget và vocabulary được khóa.
- Gate2 suite tests/akt tests/shared_kt đạt235passed89.93s, zero failures/errors/skips. Source/lock không đổi trong lần chạy, JUnit và log được lưu. Pointer trước được giữ tại artifacts/akt/preflight, pointer hiện hành được verify bằng require_gate2_evidence.
- GAM suite15passed15.34s. Prototype tách signal/parent-adaptation/local-adaptation đạt endpoint parity S=P=L=0 với graph-free và111 với full-package, kể cả struggling/forgotten states. Context/probability tolerance1e-15, theta/memory tolerance1e-12. Empty-edge fixture xác nhận local pathway vẫn đổi r_neg và decay.

## Dùng làm bằng chứng

Có thể trích kiểm correctness và cơ chế package. Không suy CUDA readiness, successful Task14, full training, causal edge benefit hoặc superiority từ các test này. Prototype chưa được nối vào benchmark/pilot runner. Thiết kế CPU09/10 tại reports/CPU09_CPU10_PROTOCOL_DRAFT.md còn chờ chốt trước run kết luận.

## Tái lập

Dùng .venv, PYTHONPATH=src;third_party và Git safe.directory đúng checkout upstream trong môi trường tiến trình. Command Gate2 được lưu trong report JSON. Refit tests tại tests/akt/test_refit_recovery.py, pathway tests tại tests/gam_kt/test_simulator_pathways.py. Log đã copy được kiểm SHA trước/sau trong copy_inventory.json. Source hashes tại manifest.json.

CLI/refit recovery chưa tích hợp qua watchdog, batch recovery chưa gộp vào selection/refit. Gate2 hiện tại không thay quyền execution hoặc ngân sách đã duyệt.
