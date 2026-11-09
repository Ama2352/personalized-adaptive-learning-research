# Rà độc lập replay native mastery CPU09

Ngày09/11/2026. Chỉ đọc source, JSON notebook và contract. Chưa import, chạy fixture/native, decode gzip hoặc tính kết quả mới. Verdict là **scoped static PASS về ngữ nghĩa replay/evaluator**. Actual parity và resource acceptance cần receipts của lượt chạy sau review.

## Nguồn đã đối chiếu

| File | SHA256 |
|---|---|
|`replay_rq1_cpu09_native_mastery01.py`|`337677c160f56da0d1454785cb18cbe5eae6ac9019db76a6b59a9eb187e0ebad`|
|`test_rq1_cpu09_native_mastery01.py`|`8b97ef21a0e3f53d9f367d8c8c22078e01dc8ef9503bc8ef07437d8732cacf1d`|
|`worker_rq1_cpu09_native_mastery01.py`|`03c46f237cacd25998da7466052ac063a2a389f3439b3dff4f865b61d4751158`|
|`rq1_cpu09_native_mastery_contract01.json`|`6e867619eb5ae4203e3e3294f72274eead04295d1635ded6bb7b7f6e8a3045cc`|
|Notebook Paper2|`353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f`|
|`src/knowledge_tracing/paper2_reference.py`|`a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1`|
|`src/knowledge_tracing/gam_kt/simulator_pathways.py`|`33ad34140f7b08eb22f86e6cc3caf7b0e7c98f09e4fd74945a6f7e9718b07560`|
|`scripts/research/run_approved_cpu_pilots.py`|`55e8e3c74c8daa92d572c809353da5546fa435b55e18b8ab30fdcf46e8413e8e`|

Tên bốn file đầu là trong prep `artifacts/akt/local-tests/akt-research-runner-20261108-01/`. Notebook anchors dùng số cell và dòng nội bộ trong code cell.

## Trình tự và đầu vào estimator

CPU09 runner bắt đầu mỗi world ở UTC2026-01-01 và tăng timestamp trước select. Step0 tăng6giờ, step dương chia hết cho28 tăng72giờ, các step khác tăng6giờ. Replay có cùng offsets6/168/240/402/474/708 tại các mốc0/27/28/55/56/84. Worker kiểm28nodes trước khi dùng recurrence. Clock được đặt tên source-derived đúng với nguồn, vì trace không chứa logged timestamps.

Notebook cell11 dòng45–81 cho thấy selector cập nhật selection/question counters, recent concepts và current chapter. Replay gọi real `policy.select()` một lần mỗi event, yêu cầu cid/qid/difficulty khớp rồi mới `predict`. Nó không thay select bằng một lookup logged query. Factory giữ cùng pathway của CPU09, với S=P=graph_on và L=false. Profile, mechanism strength, seed và latent theta không được truyền vào factory. Khác biệt histories đi qua các observable y trước đó.

Trình tự là native select → exact query/difficulty parity → native predict → exact binary64 P parity → capture native state → update bằng current y và chính P vừa dự báo. Callback source revalidation chỉ được gọi sau đủ120streams/14.400events và native counters hoàn tất. Truth threshold join nằm sau callback đó. Nếu stream cuối mismatch, helper không gọi attach_truth, và worker có failure path giữ attempt.

## Native M và criterion của world

Cell13 dòng50–52 định nghĩa M bằng stored theta_est≥1250 và stored pi_task≤0,55. Cell13 dòng92–102 trả pi đã decay cho P và update. Hàm này cùng pathway `_context` chỉ tính giá trị từ state hiện có. Lần capture bổ sung không mutate state và không dùng RNG. Do đó readout lưu stored pi và decayed pi riêng là đúng ngữ nghĩa nguồn. Predict/capture/update tạo3lần `_decayed_pi` mỗi event, phù hợp cap43.200.

Cell3 dòng33 đặt threshold1250. Cell9 dòng45 lấy world theta_at trước response/learning và dòng74 lưu theta_before. Cell19 dòng26/61/83 dùng cùng predicate≥MASTERY_ELO cho mastery của world. Replay dùng ngưỡng đó trên queried concept tại pre-update timestamp. Quần thể và thời điểm này khác bảng mastery-rate toàn28concept sau update của notebook, và đã được đặt target riêng trong contract.

`p_true`, `theta_before` và các world-mechanism diagnostics không vào estimator. Projection chỉ giữ step/concept/question/P/y. Current y nằm trong observable row để orchestration chuyển cho update, sau khi P và state capture đã xong. Worker tái dùng real reference loader/namespace và pathway adapter. Nó giữ environment/controller graph advanced fixed và hai pathway S/P, phù hợp treatment CPU09.

## Population và confusion counts

Đủ120worlds, mỗi world120queried events. Mỗi persona-arm có10×120=1.200rows. Mỗi arm có10×3×120=3.600rows. Có120world groups,12persona-arm groups và4arm groups, tổng136groups. Ba tầng dùng lại cùng14.400events nên tổng repeated row uses43.200. Seed clusters vẫn10.

TP/FP/FN/TN được cộng trên queried events của chính served histories từng arm, giữ cả zero cells. `theta_gate_true_pi_blocked` chỉ tính theta-pass nhưng pi-block. `oracle_true_pi_blocked` còn yêu cầu world truth=true, nên đây là số miss mà theta đã đạt và pi là gate còn lại, không phải toàn bộ FN. Mọi tỷ lệ downstream cần dùng row/support denominator tương ứng và giữ trường hợp unsupported lớp.

Own-served population chịu tác động selection và closed-loop divergence. Các arm có thể hỏi concept khác nhau sau histories khác nhau. Không nên diễn giải khác biệt confusion như cải thiện causal hoặc so predictor trên common query set. Native stored M và V1 calibrated/reference-item criterion cần giữ tên và target riêng.

## Một điểm cần viết chính xác

Worker gọi generic `cache.validate_trace` trước replay. Validator đọc các trường world để kiểm finite/schema/range. Vì vậy, whole worker có đọc và type-validation dữ liệu theta_before/p_true trước parity. Điều được bảo đảm trong orchestration là **diễn giải threshold/confusion sau full parity**, cùng việc world fields không vào estimator. Các truth-trap fixtures kiểm projection/join boundary của helper, chưa là bằng chứng whole-worker không đọc bất kỳ truth field trước parity.

Mười hai unittest methods là số tĩnh trong source đã đọc. Chúng kiểm clock, select side effects, predict/capture/update order, stored-vs-decayed pi, graph-only factory, projection và truth-join gating, last-stream mismatch, source drift, grid ordering và confusion zeros. Chưa có output kiểm thử hoặc replay để nâng verdict nguồn thành actual numerical parity. Không thấy deterministic correction bắt buộc trong ngữ nghĩa source hiện tại.
