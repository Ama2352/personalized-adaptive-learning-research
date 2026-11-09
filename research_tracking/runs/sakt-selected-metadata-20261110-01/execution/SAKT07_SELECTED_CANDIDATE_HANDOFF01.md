# Bàn giao SAKT07 selected-only candidate01

## Phạm vi hiện tại

Root đã chọn recipe30 trước fit. Doc30 ghi rõ d200/h5/head40/context100, dropout0,2, Adam0,001, batch128 terminal targets, seed42 với epoch42+e−1, tối đa50epoch, patience5 và delta0,0001. Đây là cấu hình đầu tiên của nhóm trên core hiện có. Không gán tương đương tác giả TensorFlow hoặc kết quả fitted.

Ba file dưới đây chỉ là bản nguồn riêng dưới P. Chưa áp dụng canonical execution/runner. Existing Main, Gate và research_selection không được sửa trong gói này.

| File | SHA-256 |
| --- | --- |
| sakt_research_execution_candidate01.py | 183d37545e1aa87144aaab2c21efef000bda658ecc2d707670f0f4c7b623ff57 |
| sakt_research_runner_candidate01.py | 2d6ec4f6f0be78013c610964479ee085d9effecace83259ba525bd066ae8de7f |
| test_sakt_selected_candidates01.py | 36b124bc5b5e5b2f7b2153d63224c6026fe9c89c212f0ccd2fc57a9a8c8fcecc |
| docs/thesis_recovery/30_SAKT_RESEARCH_NUMERICAL_RECIPE_V1.md | b1029ac40184c373d3396ec887e86877e8e3a1b14f72b14dc666133ed21b4777 |

## API và ranh giới

`SAKTSelectedExecutionSpec`, `SAKTSelectedRecipe`, `SAKTSelectedBudget` và `SAKTSelectedEvidence` đóng input. `prepare_sakt_selected_identity` chỉ đọc và kiểm file thật. `require_sakt_selected_authorization` yêu cầu file quyền SAKT riêng, exact scope và các SHA bên ngoài. Quyền A0 hoặc metadata stage không cấp quyền ở đây.

`run_sakt_selected_fit` là entry duy nhất. Entry kiểm quyền trước lazy Torch, dùng public reader canonical cho provenance cả ba role, tạo phase train80 và raw selection10 riêng. Callback tối ưu chỉ giữ phase cần dùng và metadata trong `_Run`. Calibration không tham gia tiêu chí chọn epoch.

Core/trainer/checkpoint/EarlyStopping và shared claim được tái dùng. Tiêu chí chọn epoch là native Torch BCE mean trên cùng float32 exported P/y được join theo identity. Báo cáo dùng evaluator `_metrics` hiện có. Epoch không lưu checkpoint có SHA null. Best checkpoint được kiểm SHA/size trước tạo container mới, khôi phục bằng đúng epoch spec, rồi kiểm lại toàn bộ raw selection prediction identity.

Artifact dự kiến nằm trong `experiments/sakt/results/<run_id>/`, gồm invocation, event journal, epoch receipts/checkpoint cải thiện, selection predictions và targets riêng, coverage, terminal, shared claim và COMPLETE cuối. Failure giữ counters reservation/body-returned/complete cùng nguồn lỗi. Outer được Root chuẩn bị sau sẽ cần hard deadline, owned Job-family RAM và kiểm terminal sau publication. Guard nội bộ chỉ đo worker RSS/free RAM.

Không có refit90, T-fit, system freeze, public resume hoặc Junyi/GPU trong candidate. Selected-only SAKT không thay thế bất kỳ condition nào của ma trận chín mô hình.

## Kiểm đã có và kiểm đang chờ

AST ba candidate đã đạt qua `.venv` với `ast.parse`. Không import candidate hoặc chạy test/model. Peer đã đọc đúng execution183d, runner2d6 và test36b cùng API primitive và actual epoch22/checkpoint33. Peer không tìm thấy blocker tĩnh trong phạm vi đó.

34 ca dự kiến đến từ9 hàm test và các tham số. Chúng kiểm recipe drift, worst-case work reserve, registry/geometry metadata, protected source paths,8 dạng quyền sai qua public entry trước reader/lazy model, full-null prediction join và10 sai lệch identity/labels, calibration origin và private token seal. Những SHA giả trong fixture chỉ là metadata. Không có mock guard thành công hoặc proof runtime/corpus giả được nghiệm thu.

Entry test để Root bọc trong owned controller sau review là `.venv/Scripts/python.exe -B -m pytest -q artifacts/akt/local-tests/akt-research-runner-20261108-01/test_sakt_selected_candidates01.py`. Đề xuất pure worker20s, whole30s, không Torch/NumPy/model và không mở corpus thật. Đây mới là lệnh đề xuất, chưa chạy. Native producer sau apply cần allocation riêng với model/update counts, RAM và wall quota cụ thể. Component22/33 lịch sử chỉ xác nhận primitive tiny fixture, chưa xác nhận producer d200/full corpus.

Execution từng có pin f881. Thay đổi cuối chỉ đưa kiểm vai trò source path lên trước `_path` trong vòng expected_sources để từ chối protected extra path trước khi kiểm filesystem. Runner và test giữ nguyên. Không sửa bằng chứng component cũ.