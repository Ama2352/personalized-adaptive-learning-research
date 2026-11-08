# Kiểm tích hợp reference pipeline — local08/11

**151 PASS**, không lỗi hoặc skip; controller1,1700695s trong cap30s. Dùng .venv, tắt plugin ngoài và CUDA. Không NN optimizer/model fit, dữ liệu Junyi/Holdout, remote hoặc chi phí cloud. Bộ test dùng observables tổng hợp và deterministic backend, có fit scalar temperature trên nhãn tổng hợp; không phải151 quan sát nghiên cứu.

Gồm76 kiểm research-data+legacy-data,39 calibration (có luồng fit scalar→84 reference probes→controller→served prediction ticket→observe→stale snapshot reject),36 controller+legacy-bridge. Tổng151 là một lượt kiểm chung, không cộng tiếp với các targeted suites để báo số independent tests/experiments.

Receipt lưu11source/test/protocol SHA trước=sau; gồm controller hiện hành sau guard recent/count/chapter. Các bundle targeted trước giữ nguồn tương ứng của chúng. Các file code đang tracked trong Git, source bindings nằm trong receipt; module này không tự tạo research corpus, research-fitted checkpoint hoặc kết quả RQ.

Bước tiếp theo: role-aware research collector riêng, trainer selected-fit/refit90/calibration10 và outer simulator runner. Giữ graph/environment/controller identities, full-target coverage và predict-before-observe. Không dùng PASS này thay full software Gate hoặc CUDA readiness.
