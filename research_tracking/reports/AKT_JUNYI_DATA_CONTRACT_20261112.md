# Hợp đồng dữ liệu AKT cho Junyi và Grade 10 — 12/11/2026

## Hai môi trường và kết quả đang có

Lượt A0 trên Modal đã nghiệm thu và đợt A1/A2/A3 đang thực hiện dùng corpus mô phỏng Grade 10. Corpus có84item/28khái niệm,48học viên train,6selection,6calibration,210tương tác mỗi học viên. Các checkpoint này phục vụ đối chứng có kiểm soát cho RQ3. Chúng chưa là benchmark Junyi.

Junyi dùng dữ liệu bài tập thực với vocabulary riêng. Cần huấn luyện A0 và các biến thể đồ thị bằng dữ liệu Junyi riêng. Không đưa numeric embedding từ84item sang exerciseIDs Junyi. Hai môi trường cùng đánh giá phương pháp tích hợp đồ thị, có checkpoint và quần thể độc lập.

## Số lượng đã xác nhận bằng metadata

Chỉ đọc manifest preprocessing/split có sẵn, chưa truy vấn sự kiện, correctness hoặc dự báo Holdout trong lượt này.

| Thành phần | Số lượng / trạng thái |
|---|---|
| Canonical Junyi | 25.924.553 tương tác sau loại1.439dòng trùng |
| Tổng người học | 247.606 |
| Development | 198.084 người học |
| Development outer fold4 | 39.616 người học dành riêng đánh giá |
| Outer-train của fold4 | 158.468 người học |
| Inner train / selection / calibration | 126.774 / 15.847 / 15.847 người học, derivative metadata đã tạo |
| Target counts theo train/selection/calibration | Cần inventory Development theo role trước dự toán training |

Nguồn ở `artifacts/bkt_baseline/derived/manifest.json` và `artifacts/bkt_baseline/splits/manifest.json`. Không sửa chúng. Số158.468 là phép trừ198.084−39.616 từ metadata, chưa là kết quả chạy training hoặc đếm target theo role.

## Cách dùng dữ liệu đã adopt

Protocol21 chọn Development outer fold4 trong đợt staged, một trainingseed42. Bên trong outer-train cần tách người học thành train80%, selection10% và calibration10%, có quy tắc làm tròn, hash-rank và danh sách được ghim trước khi fit. Đây là inner-role derivative, giữ nguyên Development/Holdout và outer fold assignments lịch sử.

Vocabulary, graph learned và estimator confidence của lượt selected chỉ được fit từ TRAIN80. Selection dùng chọn epoch và selector bằng dự báo raw ở checkpoint tốt nhất trước refit. Sau freeze, refit neural từ khởi tạo được quy định trên train+selection90% tại số epoch đã chọn. Graph/confidence vẫn giữ bản fitTRAIN80 theo Recipe26. Temperature chỉ fit bằng calibration10% sau refit. Outer-validation không tham gia chọn epoch, graph hoặc hyperparameter. Holdout tiếp tục giữ riêng khỏi lựa chọn.

Full5fold và refit trên toànDevelopment là những lượt khác, cần dự toán và quyền chạy riêng. Chưa gọi staged fold4 là kết quả5fold. Việc dùng mọi người học để train chung sẽ làm mất ranh giới đánh giá đã chọn.

## Biểu diễn cho AKT

- Mỗi exercise là một ID ổn định. Nhãn là `correct`. `suggested` chỉ dùng phân nhóm kết quả.
- Trình đọc tạo một chuỗi xuyên bài tập cho mỗi người học, sắp theo `time_done, source_row`. Canonical lưu vật lý theo cảexercise, nên không dùng thứ tự file làm thứ tự chuỗi AKT.
- Vocabulary fit train-only, lưu ánh xạ và số người học hỗ trợ từng bài. Bài chưa có trong train cần được ghi OOV/unsupported theo pipeline, cùng full/common-supported target counts.
- Window dùng100context và100target, tổng tối đa200token. Context chỉ cung cấp lịch sử, targetmask xác định phần tính loss/scoring, không đếm lại target vì cửa sổ chồng nhau.
- Causal masking và prior responses phải giữ dự đoán trước khi nhận đáp án hiện tại. Tương tác tương lai và nhãn của câu đang hỏi không được vào dự báo.
- Mọi model trong cùng so sánh phải có learner roles, targetkeys và điều kiện graph/confidence tương ứng. Cách tối ưu có thể riêng theo model nhưng ranh giới thông tin cần khớp.

Nguồn triển khai được đọc trong lượt audit là `src/knowledge_tracing/akt/data.py`, `encoding.py`, `windows.py` và `splits.py`.

## Khoảng trống kỹ thuật đã xác nhận

`splits.py::make_inner_split` hiện giữ baseline inner split90/10. Đã bổ sung module thuần metadata `research_junyi_roles.py` và CLI chuẩn bị derivative80/10/10. Bảy unit tests đạt, gồm disjoint/exhaustive, giữ outerfold, ổn định thứ tự, làm tròn và từ chối sai partition. CLI đã tạo role manifest thực từ metadata Development, không đọc events/correctness. Chưa nối role views này vào trainer Junyi. `research_main_execution.py::MainSelectedExecutionSpec` hiện giới hạn environmentGrade10 và từ chối Junyi. Vì vậy việc đổi `device` hoặc thay đường dẫn input trong worker Grade10 chưa tạo được một lượt Junyi đúng protocol.

Các bước tiếp theo cần làm theo thứ tự sau.

1. Đã tạo derivative learner-role manifest trên outer-train fold4 ở `artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/`. Mỗi nhóm10% làm tròn lên, train lấy phần còn lại. SHA-rank dùng seed42/fold4 và nhãn phiên bản riêng. Không sửa assignments cũ.
2. Nối reader Junyi vào phase views80/10/10. Kiểm vocabulary, OOV, chronology, target identity và không vượt learner boundary.
3. Nối typed graph/confidence condition cho vocabulary Junyi. Không dùng graph84item của Grade10.
4. Tạo bounded CUDA producer và artifact contract Junyi, gồm selected checkpoint, dự báo, target coverage, telemetry và recovery. Giữ pipeline BKT/GAM lịch sử.
5. Đếm target và cache size bằng Development được phép. Chạy benchmark giới hạn trên GPU sau allocation riêng, đo cả training, validation, checkpoint và dataloading.
6. Dự toán selected+refit của toàn bộ allocation từ phép đo Junyi. Chỉ mở lượt đầy đủ khi chi phí nằm trong phần free credits được duyệt còn lại.

Không dùng throughput Grade10 làm thời gian Junyi đã được xác nhận. Hiện chưa có cơ sở khẳng định30USD đủ cho toàn bộ modern matrix Junyi. Budget2,50USD vừa duyệt áp dụng sáu điều kiện Grade10 của đợt hiện tại.

## Nguồn phương pháp

- `docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md`.
- `docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md`.
- `docs/thesis_recovery/27_MAIN_CANDIDATE_LIFECYCLE_PLAN.md`.
- `research_tracking/runs/modal-akt-graph-selected-20261112-01/README.md`.


## Giới hạn Gate sau bước chuẩn bị roles

Bộ1994ca trên Modal chứng nhận image nguồn đã frozen cho đợt Grade10. Module/CLI/test Junyi mới có7ca local đạt, chưa được nối vào image hoặc full Gate mới. Cần nghiệm thu source/runtime mới trước lượt training Junyi.
