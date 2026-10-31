# Đặc tả tích hợp AKT graph-free vào Junyi

**DRAFT — PENDING REVIEW**

Ngày khảo sát và revision: 31/10/2026. **PENDING APPROVAL:** người dùng đã nêu hướng ưu tiên original AKT + thin adapter + NonRasch exercise-level; đây chưa phải duyệt thiết kế cuối cùng. AKT chưa được triển khai trong repository. Các lựa chọn chi tiết ghi **PROPOSED** cần review trước implementation.

Quy ước trạng thái: **VERIFIED** = có output kiểm tra hoặc source inspection được dẫn; **PROPOSED** = quyết định thiết kế chưa thử; **BLOCKED** = thiếu điều kiện/bằng chứng; **PENDING APPROVAL** = cần duyệt trước chuyển bước. Source inspection không đồng nghĩa đã cài/import/test AKT tại repo.

## 1. Bài toán, động lực và phạm vi

KLTN cần một backbone attention có provenance rõ để đi theo lộ trình AKT graph-free → Fixed-graph AKT → Confidence-Gated AKT (CG-AKT). Mốc hiện tại thiết kế baseline dự đoán `correct` của exercise hiện tại từ lịch sử learner. Baseline này chưa trả lời RQ1–RQ3: predictive metrics không tự chứng minh graph cải thiện mastery, outcome hoặc policy học tập.

Phạm vi triển khai tương lai: adapter dữ liệu, model AKT đã kiểm chứng, huấn luyện Development, xuất prediction, kiểm tra nhân quả theo chuỗi và benchmark cùng dòng. Không thêm graph, KC suy diễn, wall-clock decay hay generic Transformer thay AKT. Không đổi BKT/GAM-KT, canonical data, assignments, CV/refit/Test artifacts. Holdout không được dùng trong discovery này hoặc các giai đoạn Development đề xuất.

Lần revision này chỉ đọc source, metadata, manifest và predictions/sidecar Development; chỉ cập nhật tài liệu này. Không cài package, tạo environment, clone/vendor, chạy test model/smoke/train hoặc commit. Không biến topic/area thành feature của NonRasch baseline.

## 2. Workflow và quy ước thực tế

Đã đọc `AGENTS.md`, các spec/plan hiện có dưới `docs/superpowers/` (BKT 13/10, tái cấu trúc/GAM-KT/public Git 18/10, shared KT 30/10), cùng các skill cài tại:

- `C:/Users/AmaDev/.codex/plugins/cache/openai-curated-remote/superpowers/7.0.1/skills/using-superpowers/SKILL.md` và `references/codex-tools.md`.
- `.../brainstorming/SKILL.md` cùng `builder-check-prompt.md`.
- `.../writing-plans/SKILL.md` để xác định cổng chuyển bước, không bắt đầu lập kế hoạch thực thi.

Skill brainstorming ghi: “After the design doc is approved, the next step is the plan”. Vì người dùng yêu cầu tôn trọng cổng này, **chưa tạo implementation plan**. Đây là draft để chọn approach và duyệt design; không phải plan đã được chấp thuận. Không dùng execution/implementation skills. Builder check chỉ review tài liệu.

Quy ước tên được giữ: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`; plan tương lai sẽ nằm ở `docs/superpowers/plans/`. `.gitignore` đang bỏ qua toàn bộ `docs/superpowers/`; tài liệu tồn tại cục bộ nhưng không hiện trong `git status` thông thường. Không đổi ignore hoặc force-add/commit trong task này.

**VERIFIED:** `git check-ignore -v docs/superpowers/specs/2026-10-31-akt-integration-design.md` trỏ đến `.gitignore:13:/docs/superpowers/`. **PROPOSED**, sau khi tài liệu được duyệt: cách hẹp nhất là force-add từng file spec/plan đã duyệt bằng đường dẫn cụ thể, không force-add cả thư mục. Nếu cần policy lâu dài, thay rule thư mục cha bằng ignore nội dung và allowlist đúng các file được duyệt; phải kiểm `git check-ignore -v` và `git diff --cached --name-only` để không kéo tài liệu nội bộ khác vào Git. Đây là hai lựa chọn tương lai, không sửa Git config, `.gitignore`, index hoặc commit ở task này.

## 3. Hiện trạng đã xác minh

### 3.1 Dữ liệu, split và benchmark

| Bằng chứng | Quan sát | Mức xác minh |
|---|---|---|
| Canonical manifest `artifacts/bkt_baseline/derived/manifest.json` | 25.924.553 canonical rows; bỏ 1.439 duplicate | Đọc manifest; không quét lại toàn bộ canonical/raw |
| Split manifest | 247.606 learner; Development 198.084; năm fold 39.617/39.617/39.617/39.617/39.616 | Đọc manifest; xác minh riêng assignments Development |
| GAM CV `fold=*/predictions/part-*.parquet` | 20.706.208 rows; 198.084 learner; 720 exercise; không trùng `source_row` | SQL aggregate trên toàn predictions Development |
| Prediction → assignment | 0 learner/fold mismatch hoặc learner ngoài Development | Left join với assignments đã lọc Development |
| Prediction → Development raw sidecar | 20.706.208 match, không thiếu/trùng identity user/exercise/correct/suggested | Join `source_row`; không dùng raw duplicate dư làm target |
| Timestamp trên cùng learner | VERIFIED: 0 tie sau canonical dedup, 0 tie xuyên exercise | Audit Development raw sidecar theo user/time rồi intersect canonical source rows trong predictions; chi tiết §3.5 |
| BKT/GAM CV JSON | Có 5 fold mỗi model; GAM đánh dấu `holdout_test_used=false` | Đọc CV JSON, không đọc kết quả Test |
| BKT–GAM report | BKT tốt hơn trên cả năm common-row metrics, CI bốn metric không chứa 0 | Kết quả được báo cáo; không tính lại metrics/bootstrap trong task này |

Canonical được partition theo exercise, manifest ghi thứ tự `(user_id, exercise, time_done, source_row)` cho BKT. AKT phải **sắp lại xuyên exercise theo `(user_id, time_done, source_row)`**; không lấy order file hay BKT `order_id` làm timeline AKT.

Prediction GAM đã lưu thiếu `time_done`; không được dùng riêng chúng làm input sequence. Sidecar `artifacts/gam_kt/derived/source_map/source_sidecar.parquet` có time, nhưng chứa 20.707.382 raw Development rows gồm duplicate; manifest scope là `development only`. Trong discovery, join với source rows prediction để nhận đúng 20.706.208 target. Production adapter tương lai vẫn phải đọc canonical + frozen Development assignments, không phụ thuộc vào việc một baseline có xuất prediction thành công hay không.

SHA-256 đo tại lần khảo sát:

| File | SHA-256 |
|---|---|
| `artifacts/bkt_baseline/derived/manifest.json` | `035fb113fcbbd0f433fcda210d43ef279f6eb8163e0b3b4b72c9d4f066a02fb7` |
| `artifacts/bkt_baseline/splits/manifest.json` | `a69c0b440ef7d206133470f13696e853cb237c35c56c2b9015c175edaa89f94c` |
| `artifacts/bkt_baseline/splits/assignments.parquet` | `ee588c5b72fc214295e6eef1839b5110c884f43ab52ab4a792ca82e35812be20` |

Hash manifest không thay cho inventory/hash của mọi canonical shard. Chưa lập lại inventory dataset vì không có di chuyển hay sửa dữ liệu.

### 3.2 Metadata, KC và graph

Đọc `dataset/junyi_Exercise_table.csv`: 837 rows, 835 `name` duy nhất. Các cột là `name`, `live`, `prerequisites`, vị trí hiển thị, ngày tạo, thời gian chuẩn, tên hiển thị, `topic`, `area`. Không có cột KC hoặc bảng exercise→KC độc lập trong các nguồn được kiểm tra. Topic/area không đủ cơ sở làm KC.

Parser tách prerequisites bằng dấu phẩy/chấm phẩy/`|`: 988 tham chiếu, 981 cặp duy nhất trước bỏ self-edge; 979 cạnh sau bỏ 2 self-edge; 835 nodes, 59 isolated, 0 endpoint ngoài catalog. Cả 720 exercise Development khớp nguyên dạng node `name`. Hướng là prerequisite→dependent. Đây là mapping exercise→graph node, **không phải** exercise→KC hay xác minh quan hệ nhân quả sư phạm. Graph không đi vào baseline.

### 3.2.1 Audit topic/area — VERIFIED

Đọc CSV với `dtype=str, keep_default_na=False` để không biến literal `N/A` thành null rồi mất dấu nguồn. Không trim/normalize/clean dataset. Metadata SHA-256: `13292cc2c809985abbacedaba434e39aeb02a7fcb2a32f17b60c4d3f4d769546`.

| Phạm vi | Exercise | Topic gồm N/A / có nội dung | Area gồm N/A / có nội dung | Exercise mang N/A |
|---|---:|---:|---:|---:|
| Catalog unique | 835 | 41 / 40 | 9 / 8 | 19 |
| Development | 720 | 40 / 39 | 9 / 8 | 1 |

Không có chuỗi rỗng ở `name/topic/area`, không có leading/trailing whitespace và không có collision khi chỉ kiểm `strip().casefold()`. Tuy nhiên literal `N/A` là **thiếu ngữ nghĩa**, không là một curriculum topic/area thật: có 20 catalog rows tương ứng 19 exercise unique. Trong Development, `matrix_mul_two` có topic=area=`N/A`: 8 interactions, 4 learners. Join ID đạt 720/720; coverage metadata có nội dung đạt 719/720 exercise và 20.706.200/20.706.208 interactions. Bốn learner này vẫn có thể xuất hiện ở nhóm metadata khác; không suy ra số learner hoàn toàn thiếu metadata.

Mapping trên giá trị raw: exercise→topic và exercise→area đều đúng một giá trị; topic→area cũng đúng một giá trị, kể cả `N/A`. Hai exercise có catalog record lặp là `matrix_mul_two` và `matrix_app_fruit_oil`; các record của từng tên đồng nhất ở topic/area/prerequisites. Không cần chọn một record mâu thuẫn để join. Tính nhất quán này chỉ xác nhận catalog hiện có, không chứng minh hierarchy đầy đủ hoặc đúng sư phạm.

Ví dụ trong yêu cầu cần giữ đúng token thực: `solving_quadratics_by_factoring` và `graphing_parabolas_1` có topic **`quadtratics`** (spelling hiện có), area=`algebra`; `parabola_intuition_1` có `conic-sections/algebra`. Không tự đổi `quadtratics` thành `quadratics`. Token `linear-equations-and-inequalitie` cũng được giữ nguyên; chưa đủ căn cứ gộp nó với `solving-linear-equations-and-inequalities`.

Có thể join đáng tin cậy theo `exercise=name` mà không đọc Holdout: catalog là metadata đã có, cohort lấy từ predictions Development đã đối chiếu assignments. Mọi thống kê dưới đây chỉ dùng Development; catalog-only counts không là phân bố Holdout. Nếu metadata được dùng fit một variant tương lai, vocabulary topic/PID và xử lý thiếu phải tiếp tục fit train-only.

### 3.2.2 Phân bố topic/area — VERIFIED

Các bảng sau dùng 20.706.208 canonical source rows trong predictions Development, join catalog unique theo exercise. Learner là distinct trong từng nhóm, **không cộng các learner counts để ra tổng** vì một learner có thể thuộc nhiều topic/area. Interactions/exercise counts là phân hoạch theo một raw topic/area mỗi exercise. Không tính topic/area làm feature baseline.

| Area | Interactions | Learners distinct | Exercises |
|---|---:|---:|---:|
| `arithmetic` | 14.101.034 | 150.540 | 250 |
| `algebra` | 3.018.400 | 62.438 | 239 |
| `geometry` | 2.334.089 | 46.044 | 146 |
| `analytic-geometry` | 580.628 | 28.650 | 29 |
| `probability-statistics` | 483.969 | 15.874 | 38 |
| `calculus` | 122.488 | 7.872 | 10 |
| `logics` | 42.071 | 4.313 | 5 |
| `biology` | 23.521 | 1.296 | 2 |
| `N/A` | 8 | 4 | 1 |

| Topic | Interactions | Learners distinct | Exercises |
|---|---:|---:|---:|
| `addition-subtraction` | 4.827.397 | 91.490 | 34 |
| `multiplication-division` | 2.640.939 | 47.811 | 26 |
| `telling-time` | 1.656.054 | 46.626 | 15 |
| `factors-multiples` | 1.296.307 | 30.121 | 16 |
| `fractions` | 1.290.104 | 35.070 | 51 |
| `absolute-value` | 1.237.928 | 30.823 | 19 |
| `decimals` | 1.217.250 | 36.292 | 42 |
| `basic-geometry` | 668.218 | 18.058 | 27 |
| `exponents-radicals` | 607.800 | 15.455 | 28 |
| `order-of-operations` | 559.909 | 23.296 | 12 |
| `segments-and-angles` | 548.709 | 26.724 | 18 |
| `solving-linear-equations-and-inequalities` | 482.928 | 15.922 | 52 |
| `area-perimeter-and-volume` | 445.658 | 18.581 | 33 |
| `statistics` | 396.144 | 12.737 | 29 |
| `transformations` | 327.937 | 5.709 | 4 |
| `rates-and-ratios` | 253.427 | 10.333 | 29 |
| `parallel-and-perpendicular-lines` | 245.320 | 6.224 | 15 |
| `unit-conversion` | 205.339 | 5.163 | 13 |
| `polynomials` | 204.458 | 6.421 | 28 |
| `triangle-properties` | 182.462 | 8.922 | 14 |
| `ratio-percentage` | 144.940 | 7.206 | 6 |
| `congruent-triangles` | 140.594 | 7.065 | 16 |
| `quadrilaterals-and-polygons` | 137.920 | 5.905 | 11 |
| `calculus` | 122.488 | 7.872 | 10 |
| `algebra-functions` | 102.709 | 5.462 | 18 |
| `similar-triangle` | 99.892 | 4.985 | 13 |
| `pythagorean-theorem` | 94.645 | 6.755 | 4 |
| `probability` | 87.825 | 4.960 | 9 |
| `linear-equations-and-inequalitie` | 87.636 | 3.242 | 24 |
| `circle-properties` | 86.088 | 8.406 | 13 |
| `systems-of-eq-and-ineq` | 65.505 | 4.237 | 16 |
| `quadtratics` | 60.287 | 4.318 | 17 |
| `logical-reasoning` | 42.071 | 4.313 | 5 |
| `complex-numbers` | 39.072 | 2.510 | 6 |
| `trigonometry` | 31.919 | 2.839 | 11 |
| `biology` | 23.521 | 1.296 | 2 |
| `vectors-matrix` | 19.644 | 1.631 | 19 |
| `conic-sections` | 15.788 | 1.442 | 8 |
| `sequence_and_series` | 9.368 | 688 | 6 |
| `N/A` | 8 | 4 | 1 |

### 3.2.3 So sánh representation — PROPOSED / PENDING APPROVAL

| Modeling option | Inputs / ý nghĩa | Hệ quả và khuyến nghị |
|---|---|---|
| 1. AKT-NonRasch-exercise | Exercise làm question token; n_pid=0; concept_ids=None | Hướng ưu tiên Sprint 2; không cần KC và không dùng topic/area/prerequisites |
| 2. AKT-Rasch-topic-proxy | Exercise làm PID/question riêng; raw topic làm c_t proxy; area chỉ audit | Có thể là sensitivity experiment về chia sẻ biểu diễn theo curriculum; **không** gọi topic là validated KC hoặc trộn kết quả vào baseline 1 |
| 3. AKT-Rasch validated KC | Exercise/PID + mapping KC được chuyên gia/nguồn độc lập biện minh | BLOCKED: chưa có mapping/validation phù hợp |

Option 2 đáng khảo sát **sau** baseline ổn định vì metadata phần lớn có coverage và topic→area raw đơn trị. Nó kiểm một giả thuyết khác: grouping curriculum có giúp Rasch representation không. Một topic có thể chứa nhiều kỹ năng, một exercise có thể cần nhiều KC; nhãn đơn trị catalog không phản ánh multi-KC, prerequisite, granularity hoặc prerequisite mastery. Các nhóm rất lệch tần suất và `N/A` không có nghĩa chung. Không gán tất cả N/A vào một KC giả. Quyết định thiếu topic (exclude/accounting riêng hoặc metadata-unknown được huấn luyện) cần design riêng; mọi so sánh option 1/2 phải cùng target rows và budget. Thêm Rasch vừa đổi representation vừa đổi tham số, nên cải thiện không tự quy cho “KC đúng”; cần ablation/capacity controls. Option 2 không thuộc implementation Sprint 2 này.

### 3.3 Phân bố lịch sử Development

Đếm trên toàn predictions Development đã đối chiếu assignment; một lịch sử là toàn bộ exercise của một learner:

| Thống kê | Số interaction/learner |
|---|---:|
| Min / Q25 / median / Q75 | 1 / 3 / 10 / 50 |
| P90 / P95 / P99 / max | 219 / 483 / 1.669 / 22.067 |
| Learner có đúng 1 interaction | 31.567 |
| Learner có ≤5 interaction | 62.373 |
| Learner có >200 interaction | 21.137 |
| Rows thuộc learner có >200 interaction | 16.202.446 (~78,25%) |
| Rows bị bỏ nếu chỉ giữ 200 dòng đầu mỗi learner | 11.975.046 (~57,83%) |

Không được lọc learner ngắn, bỏ interaction đầu hoặc cắt toàn bộ timeline còn một prefix/suffix. Các quantile và count trên có output SQL trực tiếp. Số learner có một interaction tương đương khoảng 15,94% learner, dù chỉ chiếm khoảng 0,15% rows; bỏ họ làm thay đổi learner population.

### 3.4 Hợp đồng và code tái sử dụng

`src/knowledge_tracing/shared_kt.py` có `StableVocabulary`, `CausalSequenceInputs`, `build_causal_sequence_inputs`, `SequenceKTModel`, `check_prediction_alignment`, `coverage_summary`, `validate_fold_isolation`. Các file này cùng tests và báo cáo benchmark đang là untracked work có trước task; cần bảo toàn.

- Vocabulary zero-based, sort token string; unknown token hiện gây lỗi, chưa có OOV policy.
- Builder giữ item hiện tại, `prior_responses[t]=r[t-1]`, `-1` đầu learner; trả current targets riêng. `sequence_offsets` đánh dấu learner, `user_ids` có một phần tử mỗi event.
- Builder default `exercise_id`, trong canonical/prediction là `exercise`: adapter truyền `item_key='exercise'` và alignment keys tường minh. Không đổi tên dữ liệu gốc.
- `causal_attention_mask` là tam giác dưới **gồm đường chéo**. Không đủ làm mask retriever AKT: response values cần mask **strict past**. Dùng hai mask khác nhau.
- `SequenceKTModel.predict(inputs)` không nhận target; có thể bọc một thư viện nội bộ nhận responses nhưng phải chứng minh tính nhân quả chức năng cho từng vị trí.
- Builder hiện sort/materialize toàn bộ rows; production cần streaming theo learner có giới hạn bộ nhớ, kiểm parity trên fixture với contract; không gọi builder một lần cho 20,7M Python dictionaries.

`gam_kt/splits.py` có validation assignments và ordering; `bkt_baseline/metrics.py`, `gam_kt/evaluation.py` định nghĩa metric; `paired_bootstrap.py` có thống kê paired theo learner. API BKT/GAM-KT không đổi.

### 3.5 Timestamp và thứ tự xuyên exercise — VERIFIED, với giới hạn precision

Audit chỉ dùng `artifacts/gam_kt/derived/source_map/source_sidecar.parquet` (manifest `development only`) và canonical source keys ở predictions Development. Chia raw sidecar thành 8 bucket `hash(user_id)%8`, group theo `(user_id,time_done)` để toàn lịch sử của một learner nằm cùng bucket; không chia theo source-row range vì có thể tách một tie ra hai nhóm.

| Chỉ tiêu | Kết quả |
|---|---:|
| Raw Development sidecar rows | 20.707.382 |
| Nhóm raw user/time có >1 row / số rows / excess | 1.174 / 2.348 / 1.174 |
| Nhóm raw timestamp tie có nhiều exercise | 0 |
| Canonical rows giữ lại trong 1.174 nhóm raw tie | 1.174 (đúng một mỗi nhóm) |
| Canonical user/time tie / cross-exercise tie / excess | 0 / 0 / 0 |
| time_done null trong raw Development | 0 |
| Min / max raw Development time_done | 1.350.003.835.131.230 / 1.421.000.065.650.430 |

Interpreted dưới Unix microseconds, range là `2012-10-12T01:03:55.131230Z` đến `2015-01-11T18:14:25.650430Z`. GAM CV manifest ghi unit=`us`; docs `docs/bkt-data-readiness-audit.md:36` dẫn mô tả trường microsecond (đó là evidence tài liệu cũ, không truy cập lại toàn raw/Holdout). Tất cả 20.707.382 raw Development timestamps chia hết cho 10; chỉ 207.432 chia hết cho 1.000 và 197 chia hết cho 1.000.000. Vì vậy không làm tròn sang milliseconds/seconds; đơn vị lưu microsecond nhưng quan sát trên lưới bội 10 microsecond. Chưa xác minh physical clock resolution hoặc độ chính xác đồng hồ; đơn vị lưu không tự là độ chính xác thực tế.

**PROPOSED:** giữ integer time_done và sort stable `(user_id,time_done,source_row)` xuyên exercise trong adapter. Source_row chỉ làm deterministic tie-break, không là bằng chứng thứ tự nhân quả. Hiện không có canonical tie trong cohort đã kiểm; nếu data version khác xuất hiện tie, log nhóm/cross-exercise counts và đánh giá sensitivity order trước claim chronological unambiguous. Không thay timestamp, thứ tự canonical vật lý hoặc frozen manifest. AKT nguyên bản dùng thứ tự/vị trí, không dùng khoảng cách wall-clock; đó là giới hạn diễn giải temporal và không biến learner-disjoint CV thành calendar-time validation.

## 4. Yêu cầu kiến trúc AKT và giới hạn ngữ nghĩa

### 4.1 Paper và biến thể

Nguồn chính là Ghosh, Heffernan & Lan (KDD 2020), DOI `10.1145/3394486.3403282`, §2.1, §3, Fig.1. Paper phân biệt exercise/question với concept; có encoder question, encoder interaction, knowledge retriever và prediction network. Nhánh Rasch chia sẻ embedding theo concept rồi điều chỉnh bằng difficulty của question. Mã tác giả có cả AKT-Rasch và AKT-NonRasch. [S1–S3]

Ký hiệu rút gọn của nhánh Rasch:

\[
x_t=c_{c_t}+\mu_{q_t}d_{c_t},\qquad
y_t=e_{(c_t,r_t)}+\mu_{q_t}f_{(c_t,r_t)}.
\]

Không được suy từ tên biến `n_question` rằng mọi đường code chỉ cần item ID: nhánh `pid` của tác giả và đường gọi AKT trong PyKT dùng một chuỗi concept cùng chuỗi problem ID. Nếu đặt concept=exercise và PID=exercise, hai mức phân cấp đồng nhất; đó là pseudo-concept assumption, mất chia sẻ giữa các exercise cùng KC, không tái lập Rasch trên KC đã xác minh. [S2, S5, S7]

**Đề xuất phương pháp:** `AKT-NR-exercise`, dùng exercise ID làm token question trong nhánh NonRasch (`n_pid=0`), `concept_ids=None`. Đây là lựa chọn question-level có công khai giới hạn, không tạo KC giả. Đủ để khảo sát backbone attention graph-free; **không gọi là tái lập đầy đủ AKT-Rasch**. Nếu yêu cầu bắt buộc Rasch/KC hierarchy gốc, thiếu mapping là blocker cần giải quyết trước triển khai.

### 4.2 Những chi tiết cần giữ và kiểm chứng

| Thành phần | Yêu cầu / quyết định thiết kế |
|---|---|
| Embedding | Giữ đúng tùy chọn upstream; đề xuất `separate_qa=False`: embedding item cộng embedding đáp án; không biến thành embedding learner |
| Encoder | Context question nhìn `j≤t`; context interaction ở vị trí j chỉ nhìn `≤j`; retriever response nhìn `j<t` |
| Retriever | Query/key từ question context, values từ encoded interactions; không thay bằng attention generic |
| Monotonic attention | Giữ decay học được và context-aware distance, clipping/detach/softmax như source đã pin |
| Thời gian | Thứ tự event và khoảng cách vị trí; không dùng elapsed seconds hoặc thêm positional embedding khi source forward không dùng |
| Prediction | Current question cộng retrieved representation, FFN, sigmoid; trả một p tại mỗi target hợp lệ |
| Loss | VERIFIED upstream sum BCE; giữ sum cho source parity. PROPOSED training adapter dùng mean masked BCE cho NonRasch, công khai là training adaptation (§9) |
| Optimizer | Adam, seed 42; config riêng của AKT, không kế thừa `tol/maxiter/num_fits` của BKT |

Phương trình attention cần kiểm theo source: với điểm tương đồng `a[t,j]`, trọng số dùng `softmax(exp(-theta*d[t,j])*a[t,j])`, `theta>0`. Không thay bằng trừ trực tiếp `theta*d` trước softmax. Khoảng cách contextual và decay không bảo đảm mọi attention weight giảm đơn điệu theo j vì similarity vẫn thay đổi. [S1–S2]

Forward upstream gốc nhận `(q_data, qa_data, target, pid_data=None)`; `target` chỉ dùng tính loss/mask, prediction lấy từ logits. Padding loader dùng token 0, valid q bắt đầu 1; `qa=q+r*N`, label padding -1. Loader cắt chunk không overlap, nhưng đây là convention preprocessing, không phải bắt buộc của kiến trúc. Upstream training có gradient clipping tùy config; checkpoint chứa state model/optimizer/epoch. [S2–S4]

PyKT tách forward p/regularizer khỏi loss nhưng runner thường lấy `y[:,1:]`, bỏ output đầu; dataset dựng shifted sequences và select masks. Dùng nguyên runner đó sẽ khác coverage Junyi. Embedding ID conventions cũng khác; không chuyển ID/mask giữa hai nguồn bằng giả định. [S5–S7]

### 4.3 Ranh giới fidelity — VERIFIED nguồn, PROPOSED tích hợp

| Lớp quyết định | Phải giữ / được phép thích ứng |
|---|---|
| Kiến trúc NonRasch đã chọn | Giữ embedding/response composition, hai encoder, retriever, decay/distance, masks, residual/norm/FFN và prediction head của source pin. Không thay monotonic attention bằng vanilla Transformer, thêm positional/time/graph signal hoặc nhánh Rasch rồi vẫn gọi baseline cũ |
| Biến thể | Chọn upstream NonRasch n_pid=0 là lựa chọn có tên; bỏ difficulty/Rasch không là phát hiện mới. Nếu sau này bật topic-proxy Rasch, đó là model/experiment riêng |
| Dataset adapter | Được mapping exercise IDs train-only, sequence ordering, windowing, right padding, masks loss/export và OOV policy đã duyệt; không đổi nhãn correct hoặc dùng suggested/topic/area làm feature baseline |
| Training | Được chọn batch/optimizer/lr, normalization/clipping, early-stop/refit trong protocol riêng có provenance. Thay training settings có thể đổi nghiệm học, phải công khai; không phải thay attention architecture |
| Benchmark | Chung frozen learner folds, targets/source_row, predict-before-update, metric definitions và common-row population. Không ép AKT dùng EM, một model mỗi exercise, difficulty-fit hoặc online state mechanism của BKT/GAM-KT |

**BLOCKED kiểm chứng thực thi:** chưa cài source AKT, chưa import/forward/backward/parity hoặc training trong repo này. “Faithful” hiện là mục tiêu và source-level assessment; chỉ được tuyên bố thực thi đạt sau tests. Sum loss/source-gradient parity và adapter mean-gradient relation là hai phép kiểm khác nhau; không đòi mean gradients bằng sum gradients khi N≠1.

## 5. Các phương án tích hợp và khuyến nghị

**PENDING APPROVAL:** người dùng ưu tiên A + NonRasch exercise-level. Bảng giữ lại các tradeoff để review; hướng ưu tiên chưa cấp phép triển khai hoặc ngầm chuyển sang B/C.

| Tiêu chí | A — AKT tác giả + adapter, upstream nguyên vẹn | B — PyKT AKT + adapter | C — Local adaptation/vendor tối thiểu |
|---|---|---|---|
| Nguồn | `arghosh/AKT`, commit `01b7e8d7d7c862cabc9467108e3e7f2555653a88` | Candidate `pykt-team/pykt-toolkit` commit `2fc4d64880956f21155a238d0b0302ac42cb5196`; setup version `0.0.38` | Bắt nguồn từ A hoặc B đã pin; không viết lại AKT |
| Fidelity | Tham chiếu trực tiếp paper tác giả; commit có softmax-mask bug fix | Giữ lõi AKT, có nhiều emb_type/nhánh tùy biến; phải khóa đường chuẩn | Phụ thuộc patch; phải parity logits, loss và gradients với parent |
| Provenance hiện tại | Đọc được `akt.py` tại đúng commit | Đọc được main AKT và pinned setup; fetch pinned AKT bị cache miss, chưa xác nhận file tại candidate SHA | Chưa có snapshot/patch; không thực hiện ở task này |
| License | MIT, copyright Aritra Ghosh; giữ notice | MIT, copyright pykt-team; giữ notice | Giữ license parent và ghi patch provenance |
| Bằng chứng hoạt động | History model hiển thị bug fix 04/12/2020; không có bằng chứng bảo trì gần đây | History repo hiển thị commits 31/08/2026; không suy ra AKT được test/bảo trì ở runtime này | Maintainer chính sẽ là dự án KLTN |
| Python/Torch | README Linux, PyTorch 1.2.0 và stack cũ; không coi “Python 3+” là chứng nhận 3.13 | setup khai `Python>=3.5`, `torch>=1.7`; lower bounds không là compatibility matrix | Có thể sửa tương thích tối thiểu; tăng trách nhiệm xác minh |
| Dependency | Model module trực tiếp chỉ Torch, NumPy và stdlib; runner cũ thêm sklearn | Cài toolkit thêm pandas/sklearn/wandb/entmax và nhiều model imports | Chỉ deps module đã chọn; phải audit dependency closure |
| Interface | Forward gộp loss, device global; cần wrapper, dummy targets khi infer | Forward p/reg thuận tiện; cần bypass runner/data conventions | Có thể tách logits/device tốt hơn nhưng là thay đổi local |
| Dataset | Viết Junyi streaming adapter, không dùng loader dataset benchmark gốc | Vẫn cần adapter preserving source rows; dùng preprocessing chuẩn PyKT sẽ tạo mismatch coverage | Adapter tương tự A/B |
| CPU/GPU | Source chọn cuda nếu có, có fallback CPU; wrapper phải đồng bộ module device và tensor device | Cũng có global device; chưa chạy ở máy này | Có thể sửa device factories theo input; phải kiểm parity |
| RAM/runtime | Attention O(B·heads·L²), chưa có số đo | Cùng độ phức tạp lõi; toolkit không tự làm training rẻ hơn | Tương tự nếu không đổi thuật toán |
| Reproducibility | Checkout read-only đúng SHA, wrapper hash, env lock, data/split hash | Khóa repo SHA và deps; chỉ version package không đủ | Parent SHA + file hash + unified patch + tests |
| Kiểm attention | Hàm attention riêng, có thể test/hook không đổi source | Hàm riêng nhưng nhiều emb_type; khóa `qid`, không `pdiff` hoặc nhánh thay thế | Dễ hook hơn, rủi ro drift cao hơn |
| Fixed graph/CG-AKT | Tốt cho baseline bất biến; graph variant cần module riêng về sau | Có scaffold toolkit nhưng custom modification dễ phụ thuộc nội bộ | Dễ sửa nghiên cứu, phải gánh regression upstream |
| Chi phí dài hạn | Adapter nhỏ; checkout có đường dẫn/import riêng vì upstream không có package API ổn định | Nhiều integration surface; phù hợp hơn nếu cần nhiều DLKT model từ toolkit | Ít dependency, nhiều công bảo trì fidelity |

**Khuyến nghị có điều kiện: A với NonRasch theo exercise.** Giữ nguồn tác giả bất biến, chỉ bọc dữ liệu/training/export. Đề xuất checkout tương lai tại `artifacts/akt/dependencies/upstream/`, pin SHA; không sao chép code thuật toán vào adapter và không gọi nguyên `main.py` (có logic dataset/checkpoint/Test riêng). Không clone trong discovery.

Wrapper có thể thiết lập `upstream_module.device` về device đã chọn trước forward và `.to(device)` cho model; phải test CPU, và GPU khi có, kể cả host có CUDA nhưng yêu cầu CPU. Mỗi process chỉ một device, không đổi global khi model khác đang forward; multi-device/thread sharing ngoài phạm vi baseline. Nếu cách này hoặc API cũ không đạt fidelity/compatibility, **dừng A**, trình patch tối thiểu theo C để duyệt. Không tự chuyển C hoặc âm thầm sửa source. B chưa được chọn vì vẫn phải thay runner/data path, thêm dependency và chưa giải quyết KC. Nếu roadmap chuyển sang nhiều backbone PyKT, cần đánh giá lại lợi ích B.

MIT cho phép sử dụng/redistribute với notice; repo gốc KLTN hiện chưa cung cấp license tổng thể ở root được kiểm tra. Trước phân phối source tương lai phải giữ license upstream và quyết định license dự án riêng; không diễn giải paper PDF có license giống code. [S8–S9]

## 6. Component và interface dự kiến

Các đường dẫn dưới đây là đề xuất thiết kế, chưa có file triển khai hay CLI tương ứng. Đặc tả đủ để lập plan sau duyệt, không phải các task đang được thực thi.

| Thành phần dự kiến | Trách nhiệm / interface |
|---|---|
| `src/knowledge_tracing/akt/config.py` | `AKTConfig`: variant, device, model/window/train budget, seeds, paths; reject graph và partition khác Development |
| `akt/provenance.py` | `verify_upstream(root, expected_commit) -> dict`; hash source/LICENSE, runtime, wrapper, manifests; fail on mismatch |
| `akt/data.py` | `iter_development_learners(canonical, assignments, outer_fold, role) -> Iterator[LearnerEvents]`; filter Development trước trả rows, validate identity/order/binary |
| `akt/encoding.py` | `fit_vocabulary(train_users)`, vocabulary sorted + train support; reserve PAD=0, encode known=shared_id+1; unknown là trạng thái riêng, không mở rộng vocab |
| `akt/windows.py` | `iter_windows(learner, context=100, target_block=100)`; trả inputs, source rows, valid/context/target masks |
| `akt/model.py` | `AKTAdapter.fit(inputs, targets)`, `.predict(inputs) -> ndarray`; nội bộ `forward_window`, model upstream tách khỏi data/runner |
| `akt/training.py` | Adam, masked loss, inner selection, checkpoint/resume; không tự chạy outer prediction khi chọn checkpoint |
| `akt/prediction.py` | `predict_fold(...)` và atomic Parquet export; uniqueness mỗi source_row, coverage và null policy |
| `akt/evaluation.py` | `score_shards(...)`, native/supported/common-row, tái dùng định nghĩa metric hiện có |
| `akt/cli.py` | Subcommands explicit preflight/smoke/pilot/fold sau này; không có lệnh mặc định chạy tất cả CV hoặc Test |
| `tests/akt/` | Behavioral, parity, window, split, checkpoint, export tests |
| `experiments/akt/configs/*.json` | Schema version + explicit defaults; JSON dùng stdlib, không thêm parser dependency |
| `docs/akt-provenance.md`, `experiments/akt/README.md` | Nguồn, patch nếu có, môi trường, commands đã kiểm chứng về sau |

`LearnerEvents` phải có `user_id`, `exercise`, `time_done`, `source_row`, `correct`, `suggested`, frozen fold. `correct` chỉ là target hoặc lịch sử đã quan sát; `suggested` chỉ nằm output/report. User ID không là feature embedding.

`CausalSequenceInputs` giữ vai trò ranh giới model-neutral. Adapter kiểm ordering/offsets/shift; không sửa shared contract hiện hữu để vừa một thư viện. Nếu streaming parity lộ thiếu contract, đề xuất thay đổi riêng để review trước.

## 7. Thiết kế sequence và cửa sổ

### 7.1 Một target cụ thể

Với `A:1`, `B:0`, current `C:?`, model-neutral input là item `[A,B,C]`, prior `[-1,1,0]`. Response hiện tại C chỉ có trong target khi train/score.

Để gọi upstream nguyên vẹn, wrapper khôi phục nội bộ response ở vị trí j từ `prior[j+1]` trong cùng cửa sổ; response cuối đặt dummy=0. Tạo `qa[j]=q[j]+N*r[j]`; với ví dụ này tương đương `(A,1),(B,0),(C,dummy)`. Đây là tensor aligned theo event, **không shift lần hai rồi dùng strict mask**. Output C chỉ retrieve interaction A/B. Dummy C không ảnh hưởng p(C). Khi train có thể dùng cùng cách dựng input từ prior, current targets chỉ dùng loss.

Batched tensor có thể chứa response t ở vị trí lịch sử phục vụ t+1; điều kiện đúng là p(t) bất biến với response t và tương lai, không phải mọi label đều vắng khỏi toàn bộ batch. Strict masks và behavioral tests chứng minh điều đó. Không đọc `prior[j+1]` của learner khác, ngoài window hoặc ngoài prefix khi infer online. Infer một current target chỉ cần lịch sử đã biết và dummy current.

### 7.2 Quy tắc cửa sổ đề xuất

**PROPOSED:** dùng `target_block=T=100`, `context_prefix=H=100`, `max_length=H+T=200`. Với user có n event đánh số 1..n, target block bắt đầu `s=1,101,201,...`; cửa sổ chứa từ `a=max(1,s-H)` đến `b=min(n,s+T-1)`. Chỉ suffix `[s,b]` có target/loss/export mask; prefix chỉ cung cấp context. Với target t trong block, item encoder thấy exercises `[a,t]`; retriever chỉ dùng response-bearing context `[a,t-1]`. Future items/responses t+1..b không có đường ảnh hưởng đến p_t. Contextual representation của một event được tính từ prefix có sẵn trong cùng window, không từ lịch sử đã bị cắt.

- Window đầu có tối đa 100 event; các window sau tối đa 200. Ví dụ target 101..200 dùng context 1..100, target 201..300 dùng context 101..200.
- Một row xuất hiện nhiều lần làm context nhưng đúng một lần làm loss target/export target mỗi epoch/evaluation. Tổng target count bằng tổng rows, không chỉ bằng số unique sau dedup output.
- Với target nằm giữa block, effective history có 100..199 event trước nó; window đầu có 0..99. Đây là **block-window protocol**, không tuyên bố mọi target dùng đúng rolling 199 event hoặc toàn bộ lịch sử.
- Re-encode context sau mỗi window; chưa dùng KV cache vì contextual encoder có thể đổi representation khi rút cửa sổ. Không dùng state từ user khác/batch trước.
- Cùng quy tắc cho train, inner validation, outer evaluation. Deterministic boundary theo event rank đầu user, không theo batch/shuffle. Shuffle windows chỉ trong train.
- Số windows toàn Development tính từ lengths là 362.172; số này mô tả I/O geometry, chưa là runtime estimate. Training nhiều epoch/fold lặp lại windows.

Ví dụ không có OOV; đánh số một-based, `C` là context-only, `T` là scored targets:

| Độ dài learner | Cửa sổ (C / T) | Số prediction targets |
|---:|---|---:|
| 1 | W1: C rỗng; T=1 | 1; question-only, không response history |
| 100 | W1: C rỗng; T=1..100 | 100; p_1 không có history, p_100 dùng 1..99 |
| 101 | W1 T=1..100; W2 C=1..100, T=101 | 101; p_101 dùng 1..100 |
| 200 | W1 T=1..100; W2 C=1..100, T=101..200 | 200; p_200 dùng 1..199 |
| 201 | Như n=200; W3 C=101..200, T=201 | 201; p_201 dùng 101..200, không dùng 1..100 |

Các target intervals rời nhau và hợp thành 1..n, nên mọi eligible target đúng một lần; context lặp không thêm direct loss/metric. Learner hàng nghìn event được chia hết timeline, không bỏ đầu/cuối hoặc các user ngắn. H và T là config preprocessing, không đổi kiến trúc AKT; phải kiểm H+T≤max_length và dùng cùng config cho fit/evaluate. H=100,T=100 là điểm khởi đầu có memory bound, chưa là optimum. Tăng H/L tăng attention memory/time theo L²; overlap còn tăng I/O và re-encoding. Giảm T để context đều hơn tạo nhiều cửa sổ.

Full-history inference giữ tất cả event trước t, có chi phí quadratic theo learner dài nhất và không trùng protocol truncation. Rolling-window-per-target giữ đúng 199 lịch sử gần nhất (khi có đủ) cho mỗi target, nhưng phải re-encode nhiều prefix chồng lấn và tốn tính toán hơn. Block-window có reset context ở ranh giới và history length biến thiên 100..199 sau block đầu. Chunk không overlap 200 rẻ hơn nhưng có target ở ranh giới thiếu toàn history trước chunk. Tất cả là phương án protocol, không phải kiến trúc mới. Khóa H/T/OOV và cách chọn context trước bất kỳ outer-fold metric nào để tránh tối ưu evaluation protocol theo kết quả; đổi sau đó tạo run/version mới và ảnh hưởng tính unbiased của CV cũ.

### 7.3 Padding, khởi đầu và unseen

Right-padding duy nhất, không left-padding/pack nhiều user thành một sequence. PAD q/qa=0, target=-1, valid=false, source_row sentinel riêng. Pad ở bên phải không thể ảnh hưởng prefix thực dưới causal mask; upstream không có key-padding mask đầy đủ nên phải kiểm bằng cách kéo dài padding và đổi nội dung padded positions. Không batch toàn padding. Prefix context có valid=true nhưng target/loss=false.

Tại đầu mỗi retained window/known segment, đặt prior sentinel=-1 trong input view của adapter; không đưa đáp án ngoài retained context vào tensor và không sửa correct/prior dữ liệu nguồn. Các prior còn lại phải đúng previous event trong segment. Tái dựng response dùng next-prior cùng segment, dummy cuối như §7.1.

Interaction đầu learner known exercise vẫn có output question-only với retriever attention row đầu bằng zero; giữ row này và báo nhóm history=0. Không áp dụng `[:,1:]` của PyKT. Learner dài/short đều được giữ.

### 7.4 OOV: bằng chứng và lựa chọn — VERIFIED / PROPOSED

**VERIFIED outer-train incidence:** exercise được xem OOV ở fold k nếu chỉ xuất hiện trong Development fold k, không xuất hiện trong bốn fold train. Tái dựng tập này từ `SELECT DISTINCT exercise,fold` trong toàn predictions Development; khớp các rows `train_support_students=0`. Không dùng outer outcomes để chọn representation, threshold hoặc model; nhãn chỉ được giữ trong row identity, không cần dùng để quyết định policy. Inner-train vocabulary có thể có thêm OOV; counts dưới đây không thay cho audit inner split sau này.

**PROPOSED default:** current unseen xuất null fitted prediction (`prediction_kind='unseen', is_fallback=false`). Known target dùng context sau unseen gần nhất nếu unseen còn trong cửa sổ lịch sử. Giữ nguyên các target-block mốc rank 1,101,201,... của timeline gốc; **không re-anchor block tại mỗi barrier** như draft trước, vì cách đó có thể làm đổi context/window phase vĩnh viễn dù OOV đã ra khỏi history horizon.

Định nghĩa zero-based cho audit: target rank i, base window start `a=max(0,floor(i/100)*100-100)`; last unseen rank trước i là u hoặc -1. Effective start `a'=max(a,u+1)`. Retriever dùng known response events a'..i-1. Nếu OOV ở giữa target block, tách thành các đoạn known liên tiếp, nhưng giữ mốc global block và prefix start này; mỗi đoạn encode riêng, OOV xuất row null riêng. Không pad OOV vào giữa sequence, không nối history qua barrier, không shift global rank sau khi bỏ OOV khỏi tensors.

| Fold | OOV exercises / rows / learners | Rows của affected learners | Known targets sau OOV đầu | Known targets bị giảm history | Known target mất sạch history do OOV |
|---:|---:|---:|---:|---:|---:|
| 0 | 5 / 34 / 5 | 7.134 | 2.749 | 746 | 6 |
| 1 | 4 / 16 / 2 | 3.019 | 115 | 115 | 2 |
| 2 | 0 / 0 / 0 | 0 | 0 | 0 | 0 |
| 3 | 0 / 0 / 0 | 0 | 0 | 0 | 0 |
| 4 | 3 / 144 / 2 | 3.432 | 792 | 614 | 18 |
| Tổng | 12 / 194 / 9 | 13.585 | 3.656 | 1.475 | 26 |

Audit impact chỉ đọc 13.585 rows của 9 affected users, join Development sidecar time theo source_row, sort user/time/source_row; đối chiếu join rows 13.585/13.585. “Giảm history” so với nominal block-window gồm cả unknown event, không phải so với full-history/rolling inference hay một model OOV có p hợp lệ. Có 129.485 context-event uses bị loại trên các targets này (60.702/12.612/56.171 ở folds 0/1/4), tối đa 199 event/target. Đó là số event-target pairs, không phải số unique interactions bị bỏ khỏi evaluation. Known targets vẫn được predicted, gồm 26 target question-only sau barrier. 1.475 tương đương ~0,0071% known targets; OOV current rows ~0,00094% toàn Development. Output accounting dự kiến 20.706.208 rows, finite known predictions 20.706.014 nếu không có lỗi khác; đây là **projection từ policy**, chưa có AKT inference.

| Strategy | Train/inference và embedding | History / coverage / shift | Common-row và quyết định |
|---|---|---|---|
| Context barrier + null current (default) | Không tạo embedding chưa học. Train vocab không có OOV nên reset là missing-history condition xuất hiện chủ yếu lúc eval; train đã có short/window starts nhưng không hoàn toàn match | Giữ known suffix, mất older known context trước barrier; known current vẫn có p, OOV current null; distribution shift bị giới hạn nhưng có thật | Fitted/common rows rõ ràng; quantified impact nhỏ, chọn để giữ source/representation đơn giản, không vì metric tốt |
| Train-fitted UNK token + response handling | Reserve UNK trong train vocab và **thực sự** cho gradient bằng corruption ID train-only, deterministic seed, independent labels. separate_qa=false: q_UNK + response embedding r=0/1 đã học; nếu separate_qa=true phải có QA_UNK-wrong/correct có train exposure | Giữ toàn history positions và responses, tăng prediction coverage tới current unseen nếu UNK được học; item identity đã mất. Synthetic random corruption không nhất thiết đại diện unseen exercise thật; phải log train support cả outcome và corruption rate | Có thể báo generic learned-UNK predictions riêng, không gắn fitted-exercise support hoặc trộn vào fitted common. Thêm augmentation/training-protocol choice, chỉ sensitivity tương lai sau design riêng; không triển khai trong revision |
| Chỉ giữ known history, bỏ OOV event | Không cần UNK, current unseen vẫn null; known histories đi xuyên OOV | Giữ older known context nhưng compact positions làm khoảng cách monotonic thay đổi; không còn full event chronology. Muốn giữ rank gaps/mask holes cần thêm khả năng không được source đảm bảo | Có thể làm variant disclosed với coverage tương tự default; không gọi semantics không đổi, chưa đề xuất thay default |
| Train-global correctness fallback cho current OOV | Scalar fit trên train, không phải AKT fitted probability | Có số p trên mọi row nhưng không giải quyết representation/history; context policy vẫn phải chọn | Chỉ report fallback riêng, exclude fitted/common; không dùng làm baseline default |

Không reserve random UNK chưa học, không dùng PAD=unknown, không mở vocabulary bằng catalog/union validation IDs. Train-fitted UNK khả thi bằng token vocabulary/augmentation, không cần đổi attention architecture, nhưng là thí nghiệm khác; không lấy outer OOV labels để fit token hoặc chọn corruption rate. Context-barrier default có thể làm mất useful history nên không suy từ incidence nhỏ rằng metric impact chắc chắn nhỏ. Nếu so default với UNK/skip, phải đăng ký inner-only comparison và cố định giao scored targets; không chọn từ outer score.

Nếu thử learned-UNK về sau, phải có training exposure cho **past UNK interaction của cả đáp án 0 và 1 trước một target sau đó có loss**, không chỉ UNK ở current target cuối sequence; response tại current target bị strict mask nên không tự dạy interaction pathway của chính nó. Giữ riêng UNK token với PAD và kiểm gradient/support bằng behavioral tests; frequency/augmentation rate là hyperparameter inner-only.

Window count 362.172 là trước OOV segmentation; phải log số windows sau tách, targets/context/pad counts và reset counts ở từng fit/eval scope. Null OOV row vẫn giữ nguyên source_row và rank metadata.

## 8. Output, coverage và benchmark

Xuất mọi outer target một lần: `source_row:int64`, `user_id:string`, `exercise:string`, `time_done:int64`, `correct:{0,1}`, `suggested:{0,1}`, `fold:int`, `prediction:nullable float64`, `prediction_kind:{fitted,unseen}`, `is_fallback:bool`, `train_support_students:int`, `history_available:int`, `history_used:int`, `context_reset:bool`, `window_id`, `checkpoint_id`.

Khi source_row trùng, identity mismatch, thiếu/dư target, p invalid/NaN cho known target hoặc fold sai, fail thay vì tự deduplicate. Trước common-row join kiểm `(user_id,exercise,time_done khi có,correct,suggested)` theo source row; dùng identity keys `exercise` tường minh với shared helper. Hai baseline cũ không có time trong mọi schema nên không bắt buộc cột không tồn tại, nhưng kiểm qua canonical identity nếu cần.

Coverage tách expected rows/users/exercises, rows xuất ra, finite model predictions, current-item unseen, context barriers, known targets bị giảm history, known-zero-history vì OOV, history=0, history bands, suggested và train-support bands. Native AKT fitted metrics trên known rows; không báo coverage=100% chỉ vì có một row null mỗi target. Nếu future variant có learned-UNK probability, thêm prediction_kind riêng và generic-UNK coverage, giữ primary fitted common-row intersection như policy đã khóa.

Common ba model = finite fitted AKT ∩ fitted BKT (`train_skill_students>0`) ∩ GAM nonfallback, cùng fold/source_row; tính lại **cả ba** trên cùng giao. Không đặt AKT metrics trên subset cạnh BKT/GAM bảng cũ full common mà gọi matched comparison. Báo mỗi pair riêng nếu giao khác; giữ mẫu số và attrition từng bước.

5 metric: AUC, Log Loss, Brier, ECE 15 equal-width bins (p=1 bin cuối), Accuracy p≥0,5; AUC null nhóm một lớp. Micro theo interaction trong fold; tổng hợp unweighted fold mean ± sample SD. Tái dùng metric functions đã kiểm tra, không sửa BKT scorer unseen semantics. Paired bootstrap giữ learner là cluster, lấy mẫu có hoàn lại trong fold, metric delta cùng rows; 1.000 replicates/seed có đăng ký trước. CI conditional trên fits/splits hiện có. Exact AUC bootstrap chưa khả thi thì báo BLOCKED, không thay estimand.

## 9. Split, early stopping và model selection

Outer fold k chỉ được đánh giá sau khi checkpoint đã khóa. Train candidates dùng Development folds khác k, không dùng labels/metrics fold k để chọn checkpoint, hyperparameter hoặc số epoch. Frozen GroupKFold theo learner không phải calendar-time split; chronological replay bên trong mỗi learner không biến nó thành temporal generalization theo thời điểm toàn cục.

Đề xuất inner split 90/10 learner trong outer-train bằng SHA-256 versioned tag `akt-inner-v1|42|k|user_id`, rank/tie-break ID; lưu danh sách/hash mới riêng, không sửa frozen assignments. Fit vocabulary/support và mọi fitted preprocessing **chỉ trên inner-train** khi chọn epoch. Early-stop inner Log Loss, min_delta=0,0001, patience=3, tối đa 20 epochs; chọn epoch sớm nhất khi tie. Selection metric chỉ trên inner known predictions, báo attrition. Seed=42, không thử seeds rồi chọn tốt nhất.

Sau chọn epoch E, refit model mới từ seed đã khóa trên toàn outer-train đúng E epochs, refit vocabulary trên outer-train; không early-stop outer, không mang inner checkpoint sang làm final fit. Outer được score một lần. Việc refit có thể thêm exercise/token so với inner train, nên không kỳ vọng inner-selected weights hay metric được giữ nguyên. E là selected **epoch**, không sao chép số optimizer steps từ dataset nhỏ sang dataset lớn; log cả steps/valid targets ở hai stage.

### 9.1 Loss normalization và optimizer

**VERIFIED source inspection:** `AKT.forward` trả summed BCE trên labels>-0,9 cộng regularizer nhánh PID; `run.py` gọi backward trực tiếp trên sum. `main.py` khai Adam, CLI default lr=1e-5, batch_size=24, maxgradnorm=-1 (tắt); dataset có thể override config. Đây là defaults của source, không phải bằng chứng tối ưu hay kết quả đã tái lập ở Junyi. [S2, S4]

Với N valid targets và mask m:

\[
L_{sum}=\sum_i m_i\,\operatorname{BCEWithLogits}(z_i,y_i),\qquad
L_{mean}=L_{sum}/N,\quad N=\sum_i m_i>0.
\]

Sum gradients tăng theo số valid targets; short histories, partial blocks, padding và OOV segmentation khiến N biến thiên. Mean bỏ hệ số N nhưng không làm gradient variance/Adam dynamics/batch sampling tự tương đương source. Adam có epsilon/momentum và clipping nên không thể coi đổi lr theo một hằng số là tái lập sum-training. Minibatch mean cũng không tự bảo đảm mỗi interaction có cùng effective epoch weighting khi N biến thiên; log N/distribution, shuffle windows deterministic, và báo metric/loss epoch bằng tổng BCE/tổng targets, không trung bình không trọng số batch means. Nếu cần cải thiện batch packing/token budgeting thì phải khóa algorithm trước outer, không âm thầm thay giữa folds.

**PROPOSED default:** giữ upstream sum cho parity reference, training adapter NonRasch lấy returned sum chia N trước backward. Vì n_pid=0 không có regularizer nên việc này đúng mean masked BCE; không dùng công thức này cho Rasch tương lai mà chưa quyết định regularizer normalization. Context-only/pad targets=-1 và N chỉ đếm scored targets; batch N=0 bị skip/không tạo optimizer step. Gradient clipping global norm=1,0 **sau** normalization, log pre-clip norm/fraction clipped. Đây là training adaptation công khai, không sửa source model/loss function và không claim giữ nguyên learning trajectory.

| Tham số đề xuất chưa thử | Giá trị / provenance |
|---|---|
| Variant / dimensions | NonRasch n_pid=0; d_model=256, heads=8, blocks=1, d_ff=1024, final_fc=512, dropout=0,05, kq_same=1, separate_qa=false; tham chiếu CLI source, không là optimum Junyi |
| Adam | lr=1e-4, betas=(0,9;0,999), eps=1e-8, weight_decay=0; lr là quyết định kỹ thuật provisional cho mean loss, **khác** source default 1e-5 sum loss, chưa có experimental provenance |
| Batch / precision | CPU initial B=4 windows, FP32, no accumulation; có thể pilot resource-only B=8 nếu được duyệt, sau đó khóa một B cho selection/refit/CV, không chọn B bằng outer metric |
| Clipping | max_grad_norm=1,0 sau mean; khác source tắt mặc định, cần review gradient measurements |
| Seed / scheduler | 42; không LR scheduler ban đầu, không best-of-seeds |
| Checkpoint selection | Inner Log Loss, min_delta=0,0001, patience=3, max 20 epochs; chọn epoch sớm khi tie; masks/OOV/coverage được log |

lr/clipping/batch vẫn **PROPOSED** cho bounded testing, không tối ưu được xác nhận. Smoke kiểm correctness/stability; nếu pilot dùng metric để chọn lr thì đó là inner tuning có registry/candidate budget, không còn chỉ feasibility pilot. Bất kỳ thay loss scale/lr/B/window/selection phải thành protocol version trước outer score. Không dùng BKT `num_fits/tol/maxiter` hoặc GAM difficulty mechanism để ép AKT training giống nhau.

### 9.2 Fixed-budget alternative — PROPOSED / PENDING APPROVAL

Nếu measured pilot cho thấy inner selection + refit quá đắt, có thể khóa **E_fixed=3 full epochs** làm candidate budget chung cho mọi outer fold, một fit mới trên toàn outer-train, final checkpoint sau epoch 3, không chọn best checkpoint bằng outer/inner metric. Định epoch là một lượt mọi eligible train target đúng một lần; giữ batch/window/lr/seed đã duyệt. Không có inner selection nên không cần double-training/refit stage; training reports vẫn có loss/grad/resources, outer chỉ score cuối. E=3 chưa có chất lượng được xác nhận và có thể underfit; số E cuối phải được duyệt sau resource measurements nhưng trước outer outcomes, dùng cùng rule cho mọi fold.

Wall-time/RAM safety cap dừng run như **incomplete**, không đổi checkpoint chạy dở thành result của fixed-epoch protocol. Nếu muốn fixed-step/token budget thay epoch thì cần spec amendment: step/token count, sampling và coverage train phải rõ, không trộn với complete-epoch results. Không tiết kiệm bằng cách chọn checkpoint trên outer labels hoặc giảm evaluation population.

Thiết kế mặc định không HPO. Nếu cần HPO, chỉ inner data với candidate list/budget khóa trước, lặp cùng procedure cho mỗi outer fold; không chọn một config từ 5 outer scores rồi gọi chính các scores đó là unbiased CV. Fold 0 sau khi đã xem results cũng không còn là tuning set cho báo cáo CV không thiên lệch nếu sửa model vì điểm đó.

## 10. Environment và dependency strategy

### 10.1 Quan sát chỉ đọc

| Kiểm tra | Kết quả xác minh / giới hạn |
|---|---|
| `Get-Command python,py,wsl` | Python ở `C:/Users/AmaDev/AppData/Local/Programs/Python/Python313/python.exe`; launcher và wsl.exe có tồn tại |
| Python hệ thống / `venv/Scripts/python.exe` | Cả hai 3.13.5; module discovery không tìm thấy torch/pykt; venv có duckdb/psutil |
| `py -0p` | Launcher báo không tìm thấy Python đã đăng ký; không phủ nhận interpreter chạy được qua absolute path |
| Environment trong root | Chỉ thấy `venv/`; không thấy `.venv/` hoặc env AKT tại root; không khẳng định toàn máy không có env khác |
| RAM qua psutil | 16.794.759.168 byte tổng (~15,64 GiB); 3.134.861.312 byte khả dụng (~2,92 GiB) tại thời điểm đo; 16 logical CPUs |
| Ổ D qua `shutil.disk_usage` | 99.004.059.648 byte trống (~92,20 GiB), snapshot tại thời điểm đo |
| GPU | Không tìm thấy `nvidia-smi` trên PATH/hai vị trí chuẩn đã thử; CIM video query bị Access denied. Chưa biết có GPU/VRAM/CUDA phù hợp |
| WSL | `wsl -l -q` và `wsl --status` trả `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`; chưa kiểm tra được distro, torch hay GPU bên trong |
| Cache/dependency local | `third_party/` chỉ có pyBKT; không thấy AKT/PyKT trong filename search repo. Pip cache tồn tại; wheel cache thấy antlr runtime, không thấy torch wheel có tên rõ. Không phân tích nội dung opaque HTTP cache, không kết luận offline install bất khả thi |
| Dependency convention | `requirements.txt` pin stack hiện tại và local pyBKT; pyproject Python≥3.11, hai CLI BKT/GAM, không khai deps; không thêm AKT vào requirements cũ |

Các lệnh CIM bị chặn, một probe Python ban đầu lỗi quoting và đã được chạy lại thành công bằng stdin script. Join toàn bộ sidecar tại DuckDB 512 MiB bị OutOfMemory; đã chuyển sang kiểm join theo khoảng 2.000.000 source rows, giữ nguyên memory limit. Không dùng lỗi này để suy ra Torch training sẽ OOM. Không nâng quyền, thay permission hoặc sửa WSL. Lỗi WSL không chứng minh distro bị hỏng/mất. Tài liệu cũ từng xác minh distro tồn tại bằng quyền khác; không coi đó là trạng thái runtime đã kiểm hôm nay.

### 10.2 Khuyến nghị

Ưu tiên **môi trường Windows riêng `.venv/`** cho parity/unit/smoke CPU sau duyệt; path này đã được ignore và tách `venv/` BKT. Candidate Python 3.13.5 đang có hoặc Python 3.12 riêng nếu wheel/source compatibility cần; chưa chọn exact Python/Torch pin. PyTorch docs có hướng dẫn Windows/CPU/CUDA nhưng không chứng nhận riêng AKT cũ; phiên bản wheel, Python ABI, NumPy và driver phải được đối chiếu rồi khóa trước install. [S10]

Tạo `requirements-akt.lock.txt` riêng với exact pins/hashes sau dependency resolution đã được phép, không kéo local pyBKT vào runtime AKT. Không gọi `pip install -r requirements.txt` của BKT để dựng AKT. Dùng absolute `.venv/Scripts/python.exe`, ghi `sys.executable`, Torch/NumPy/platform/device versions, deterministic settings và package lock hash. Chỉ dự kiến editable project install với `--no-deps` nếu cần và đã kiểm package không kéo BKT trong import path; có thể dùng `PYTHONPATH=src`.

**PROPOSED compatibility check trước installation:** đối chiếu exact CPython version/ABI/architecture với official PyTorch wheel tags trên Windows CPU index, supported Python range và dependency requirements NumPy; kiểm pinned AKT dùng API/dtype tương thích candidate Torch/NumPy. Ghi một compatibility matrix “source inspection / wheel có sẵn / import tested / parity tested”, không suy từ version bounds rằng tất cả đã pass. Chưa tạo env hoặc chạy resolver/install/dry-run package ở task này. Chỉ sau approval mới resolve/pin và download/install; không tự downgrade môi trường BKT. Nếu Python 3.13 không có bộ dependency thích hợp, đề xuất Python 3.12 riêng cần duyệt thay vì sửa venv cũ.

Sau install được phép mới kiểm `sys.executable`, module origins, import Torch/NumPy, device selection, pinned-source parity và tests; GPU test chỉ khi inspect được hardware/driver. CPU-only smoke quy mô §13 là **khả thi về mặt thiết kế**, chưa được xác nhận thực thi vì chưa có Torch. Nếu import/parity hoặc memory preflight fail, dừng trước Junyi train. RAM available là snapshot lượt discovery ban đầu, phải đo lại khi chạy; `.wsl/` có tồn tại nhưng WSL API bị chặn, không suy ra bên trong không có Python/Torch. Không cần WSL cho CPU baseline; nếu muốn dùng WSL/GPU thì kiểm chỉ đọc từ terminal có quyền thích hợp sau user approval, không đổi permission distro.

## 11. Leakage và kiểm chứng tương lai

Tất cả tests dưới đây là thiết kế, **chưa chạy**. Fixture nhỏ synthetic, không truy cập Holdout; sau khi triển khai chạy bằng Python AKT riêng. Test behavioral dùng eval mode, dropout tắt, weights cố định và tolerance rõ; train mode kiểm nhân quả với RNG reset cùng seed hoặc dropout=0.

| Invariant | Test có khả năng bắt lỗi |
|---|---|
| Current response | Đổi r_t ở target fixture, dựng lại shifted input; p_t giữ nguyên; nếu kiểm autograd thì gradient p_t theo **interaction activation riêng tại vị trí t** bằng zero, không đòi shared response-embedding parameter gradient bằng zero vì tham số đó còn dùng ở quá khứ |
| Future response | Đảo r_(t+1..end), p_(≤t) không đổi; chạy qua nhiều block/window boundaries |
| Future exercise | Đổi exercise tương lai không đổi p trước đó, kể cả contextual-distance code |
| History được dùng | Với weights/fixture nhạy đã định, đổi một past response phải đổi ít nhất một p sau đó; tránh model hằng làm test leakage pass rỗng |
| Masks | Hai encoder mask j≤t, retriever j<t; all-masked first row không NaN; attention forbidden mass bằng zero |
| Shift | A:1,B:0,C:? → prior[-1,1,0], aligned qa A1/B0/Cdummy; không double shift, không nối current item với đáp án sai event |
| Padding / loss | Prefix p/loss/grad không đổi khi thêm/đổi right pad; padded/context-only targets không góp direct loss/metric/export; valid N=0 không optimizer step; kiểm sum=N×mean và grad_mean=grad_sum/N cho NonRasch cùng tensors, dropout=0 |
| Window | n=1,99,100,101,200,201 và 22.067 theo ví dụ §7.2; mỗi target một lần, context overlap đúng, order/ties/source_row giữ nguyên; so single-target prefix với output cùng retained context; H/T config không đổi model topology |
| Learner | Đổi/permutate user khác/batch order không đổi p user đang xét; prior đầu user=-1, không carry memory/response |
| Fold và fit scope | Thay outer labels không đổi vocab/support/checkpoint selection; inner-train và inner-val không giao user; outer fold không được gọi trong fit callback |
| Deterministic encoding | Shuffle row input vẫn cùng vocabulary sorted; checkpoint load dùng saved vocabulary; thêm OOV eval không resize vocab |
| OOV | Current unseen null; global target-block boundaries không re-anchor sau barrier, prefix start=max(base,lastOOV+1); không encode OOV như PAD; count context-reduced/zero-history đúng; UNK nếu làm variant sau phải có train gradient/support và r=0/1 đúng |
| Alignment | Duplicate/extra/missing/wrong identity phải fail; context-only row không được export lần hai |
| Graph-free | Không graph arg/file read; config graph=true bị reject; thay catalog prerequisite values không đổi p/vocab |
| Architecture parity | Cùng upstream pin, weights, tensors: so logits/p, summed loss, gradients và masks; eval CPU FP32 atol/rtol=1e-6 ban đầu, GPU tolerance định trước khi chạy |
| Checkpoint | Save/load eval p giống trong tolerance; resume RNG/optimizer/order state cho next-step parity trên cùng runtime/device; reject config/vocab/hash mismatch |
| Numerical / mode | Forward/backward batch chứa đúng/sai, short/long; finite loss/p/grad, nonzero gradient; `.eval()` repeat ổn định, `.train()` dropout được kỳ vọng khác eval |

Không yêu cầu p train=eval khi dropout bật. Không so online full-history với window-truncated history rồi kết luận leak. Source fixes, nếu cần, phải được kiểm regression và ghi deviation; một failed fidelity/leakage test chặn smoke/training.

## 12. Checkpoint, reproducibility và extension

Checkpoint tương lai: `model_state_dict`, optimizer state, epoch/step, RNG Python/NumPy/Torch/CPU/CUDA khi có, sampler position/order, vocabulary và support, variant, config schema, window policy, inner/outer scope, source SHA, wrapper/lock/manifest/assignment hashes, device/runtime và selected-epoch record. Atomic write vào run ID mới, không overwrite completed run; resume chỉ khi identity khớp. CPU/device portability được test riêng, không hứa bitwise identical xuyên phần cứng/version.

Fixed-graph/CG-AKT sẽ ở module/variant riêng sau milestone, không sửa silent baseline checkpoint architecture. Extension dự kiến ở question representation hoặc retriever attention với interface graph conditioning riêng; chưa chốt công thức hay triển khai hook rỗng. Điều kiện research tương lai: node mapping exercise-level và hướng cạnh có audit; confidence/gate có provenance độc lập, không lấy outer labels; match protocol và đăng ký ablations. Kết quả predictive phải tách đánh giá learning path/outcome với protocol riêng.

**PROPOSED controlled comparison:** khóa canonical/source rows, folds/inner split, train-only vocab và OOV policy, window/targets, metric population, seeds, selection rule và optimizer-step/token budget. Dùng cùng backbone dimensions; giữ một immutable graph-free checkpoint/source version. Graph parameters có thể làm tăng capacity dù backbone không đổi: báo số trainable parameters/FLOPs, thêm capacity-matched non-graph control khi cần; không gọi comparison “same capacity” chỉ vì d_model bằng nhau. Dùng cùng HPO budget/candidate opportunity hoặc không HPO ở mọi variant. Báo native coverage rồi recompute các variants trên giao rows đã khóa; không để graph missing-node filtering loại âm thầm learner/items.

Graph-off **architectural equivalence** cần load cùng backbone weights/state, eval mode/dropout off, gate=0 hoặc graph contribution bypass **trước** bất kỳ normalization/graph-derived preprocessing nào có ảnh hưởng; cùng tensor inputs, p/logits baseline phải khớp tolerance. Extra graph parameters ở off mode không được ảnh hưởng outputs. Đây khác **training ablation**: model graph-on đã train rồi tắt gate có thể khác baseline vì backbone weights đã học khác. Muốn so learning effect cần fresh fits cùng init/seed/budget và graph-on/off ablations; không hứa independently trained models giống bitwise. Confidence-weighted edges và gate phải có tests riêng sau này, không đưa vào Sprint 2 baseline bây giờ.

## 13. Lộ trình thí nghiệm và feasibility

| Giai đoạn sau duyệt | Budget đề xuất / gate | Evidence phải có trước bước sau |
|---|---|---|
| 1. Environment + unit/architecture | Không Junyi training; pin nguồn/env, tests §11 | Import, upstream parity, leakage/coverage/checkpoint tests pass |
| 2. Smoke Development-only | ≤32 inner-train + 16 inner-val users, ≤4.096 targets mỗi phía, ≤20 optimizer steps, ≤120 giây train; CPU B=4,L≤200, nhỏ d=32/h=4 nhưng giữ kiến trúc | Finite loss/grad, save/load, coverage/alignment, nonconstant p; short/long/single-event fixtures; RAM/runtime đo thật |
| 3. Bounded pilot | Cohort hash-fixed ≤1.024 train + 256 inner-val users, ≤100.000 targets, ≤1 epoch hoặc 15 phút (điều kiện đến trước); architecture candidate thật | Throughput, peak RSS/VRAM, tokens/targets, validation finite, checkpoint và resource preflight |
| 4. One outer fold | Cổng phê duyệt riêng sau pilot; inner selection + outer-train refit, outer score khóa cuối | Không leak/model-selection contamination, complete predictions, common rows, measured cost |
| 5. Five-fold CV | Cổng tương lai riêng; không automatic chaining từ fold | Config/protocol đóng băng, output/resource/resume review |
| 6. Benchmark | Đọc predictions cùng fold | Native/coverage/common metrics và denominators ba model |
| 7. Paired uncertainty | Budget riêng, dùng common rows/learner | Conditional CI, single-class handling; AUC CI nếu exact feasible |

Smoke/pilot cohort thuộc outer-train của fold đang phát triển, tách inner-train/val bằng user; không lấy outer fold 0 làm smoke validation. Chọn sample bằng hash và giới hạn số event có log, không dùng labels/loss chọn sample. Development-only không đồng nghĩa không thể overfit: mọi lần chạy/retry/config change ghi run registry có lý do. Smoke chỉ correctness; không chọn model vì metric đẹp. Pilot chỉ feasibility; nếu dùng pilot metric để đổi hyperparameter thì phải khai đó là tuning và chuyển sang inner selection protocol, không che như smoke.

**PROPOSED measurements/gates:** pilot phải đo wall-clock load/train/val/export riêng; windows/s, valid-targets/s, processed-context/pad counts, optimizer steps, loss và gradient norm trước/sau clipping, p distribution/variance và coverage theo history/OOV, peak process RSS/available RAM và peak Torch allocated/reserved VRAM khi có GPU. Ghi hardware/device/threads/FP32/runtime, full-length candidate model khác tiny smoke, checkpoint I/O và lỗi/resume. Throughput từ tiny smoke không dùng ngoại suy full fold.

Proceed **one fold** chỉ sau environment/provenance/parity/leakage/loss/window/OOV/checkpoint tests pass, complete bounded smoke/pilot có finite nonconstant p và aligned coverage, không swap/memory failure; đề xuất RAM headroom≥1 GiB sau measured peak, disk preflight đủ cho checkpoint/predictions/logs, estimated selection+refit+infer nằm trong ngân sách được user duyệt. Nếu không đáp ứng thì BLOCKED hoặc duyệt fixed-budget §9.2, không tự giảm scored targets. Proceed **five-fold** cần một fold hoàn tất không protocol violation, denominator/common-row verified, resource/time/resume plan dựa số đo fold thật, config khóa và **phê duyệt riêng**. Nếu dùng outer fold đầu để sửa model/protocol vì metric, không coi 5-fold với fold đó là unbiased confirmatory CV; phải khai exploratory và thiết kế lại evaluation. Không có gate nào là auto-trigger training.

Tính toán được hỗ trợ: một tensor attention FP32 B=4,heads=8,L=200 cần 5.120.000 byte (~4,88 MiB). Đây chỉ **một** tensor, chưa gồm distance/cumulative/softmax intermediates, nhiều block, activations, gradients, optimizer và data loader. Không coi là peak memory. B=24 cần ~29,30 MiB mỗi tensor tương tự. Với 2,92 GiB RAM available hiện tại, không materialize dataset/full windows; dùng Arrow/streaming, DuckDB memory≤512 MiB, threads≤2, loader workers=0 ban đầu. Cần kiểm import Torch overhead trước quyết định B và RAM ceiling; chưa biết có chạy full fold hợp lý trên máy này hay không.

Chưa có measured AKT throughput nên không ước lượng giờ full CV. Ngoại suy sau pilot theo số target/window/batch thực tế và phân bố chiều dài; tách inner-selection, refit, outer-infer, I/O. Năm outer-train datasets tổng cộng khoảng 4 lần Development interactions mỗi epoch trước inner split/context expansion, khác với một lượt replay validation BKT/GAM. Nếu CPU quá chậm: GPU riêng/remote được duyệt (cần quyết định chuyển dữ liệu), fixed-budget được duyệt, hoặc giới hạn pilot và giữ full CV BLOCKED. Không giảm âm thầm population evaluation.

## 14. Rủi ro, quyết định và điều kiện chấp nhận

### Quyết định cần người dùng duyệt

1. **PENDING APPROVAL:** chốt hướng ưu tiên A + **AKT-NonRasch-exercise**, pin upstream; KC validated hiện BLOCKED, topic-proxy Rasch chỉ một sensitivity experiment tương lai, không feature của baseline.
2. **PENDING APPROVAL:** chấp nhận block-window H=100/T=100 có config, giữ global target-block anchors khi OOV; current unseen null + context barrier làm default, biết rằng 1.475 known targets bị rút history theo outer vocab hiện tại. Learned-UNK augmentation chỉ review sau, không tự bật.
3. **PENDING APPROVAL:** training adapter mean masked BCE, lr=1e-4, Adam, clip=1,0, B=4 CPU provisional; architecture/source parity vẫn theo upstream sum. Đây là revision training protocol, không cùng training defaults upstream hoặc draft cũ.
4. **PENDING APPROVAL / BLOCKED runtime:** môi trường riêng, exact Python/Torch/NumPy pin sau compatibility review; GPU chưa biết và WSL API bị chặn. Không cài vào `venv/` hoặc WSL BKT.
5. **PENDING APPROVAL:** inner 90/10 + select/refit, hoặc fixed-epoch alternative E_fixed=3 sau budget review; full fold/full CV cần phê duyệt riêng, không auto-run sau smoke/pilot.
6. **PENDING APPROVAL sau design:** cách tracking tài liệu được duyệt trong Git (force-add từng file hoặc policy allowlist); task này chỉ ghi khuyến nghị, không sửa ignore/index/config hay commit.

Rủi ro cần giữ trong interpretation: curriculum topic không là KC validation dù mapping đơn trị; N/A/spelling không được tự clean; OOV barrier đổi context distribution dù incidence nhỏ; block history khác rolling/full history; mean/clip/lr/B đổi learning dynamics; epoch refit có vocabulary lớn hơn inner; precision lưu timestamp không là clock accuracy; graph branch thêm capacity và graph-off sau training không tự khôi phục fitted baseline.

### Readiness hiện tại

| Hạng mục | Trạng thái | Lý do |
|---|---|---|
| Frozen Development evidence và ID alignment | VERIFIED | SQL counts/joins và manifest hash có output |
| Topic/area raw hierarchy và coverage | VERIFIED | 41 topics/9 areas gồm N/A, 720/720 ID join, 719/720 có metadata nội dung; không là KC validation |
| Timestamp ties và unit | VERIFIED, clock accuracy chưa biết | 0 canonical Dev tie, 0 cross-exercise tie; lưu us, quan sát bội 10 us |
| Outer OOV/context impact | VERIFIED audit / PROPOSED policy | 194 OOV rows, 9 learners; 1.475 known targets reduced history theo global anchors; inner-scope counts chưa có |
| Question-level NonRasch khả thi về metadata | PROPOSED / PENDING APPROVAL | Hướng ưu tiên người dùng, không cần KC giả; chưa final approval |
| Faithful Rasch/KC hierarchy | BLOCKED | Không có exercise→KC độc lập |
| Nguồn A candidate | VERIFIED inspection, execution BLOCKED | Exact commit model đọc được; chưa cài/import/test trong repo |
| Nguồn B pinned model | BLOCKED một phần | Candidate SHA/setup có; pinned akt.py chưa fetch được |
| Python/Torch runtime compatibility | BLOCKED | Chưa có torch và không được install/test ở task này |
| GPU/WSL availability | BLOCKED xác minh runtime | Quyền query bị chặn; thư mục .wsl tồn tại, không suy đoán hardware |
| Mean loss/lr/clipping/batch | PROPOSED / PENDING APPROVAL | Chưa bounded test; tách khỏi architecture fidelity |
| AKT implementation/tests/smoke | BLOCKED bởi design gate | Chưa bắt đầu, không được phép thực hiện ở giai đoạn này |
| Implementation plan | PENDING APPROVAL design | Không invoke writing-plans trước approval rõ ràng |
| One fold / full CV | PENDING APPROVAL riêng | Cần implementation + tests + pilot + approval mới |

Acceptance triển khai tương lai: provenance/lock chính xác; exercise-only NonRasch không nhận topic/area/graph; giữ lõi AKT với deviations minh bạch; source-sum parity và adapter-mean gradient relation đều pass; contract/window/causality/barrier-global-anchor tests pass; bounded train/val/predict smoke có measurements/checkpoint/alignment; toàn evaluation population gồm short/first/OOV được accounting; đúng inner selection/refit hoặc fixed-budget đã duyệt; full-fold/CV readiness theo §13 và approval riêng; không sửa benchmark cũ hoặc dùng Holdout. Acceptance **revision hiện tại**: audit topic/area/timestamps/OOV có output Development-only, loss/window/OOV/fidelity/compute được phân biệt VERIFIED–PROPOSED–BLOCKED–PENDING APPROVAL, một spec được sửa tại chỗ, không plan hoặc implementation.

## 15. Nguồn và nhật ký discovery

### Nguồn ngoài đọc qua web, không tải repository về workspace

- **S1:** [Paper AKT, KDD 2020](https://people.umass.edu/~andrewlan/papers/20kdd-akt.pdf), §2.1, §3, Fig.1; [arXiv](https://arxiv.org/abs/2007.12324).
- **S2:** [AKT model tại commit 01b7e8d](https://raw.githubusercontent.com/arghosh/AKT/01b7e8d7d7c862cabc9467108e3e7f2555653a88/akt.py); [softmax bug fix](https://github.com/arghosh/AKT/commit/01b7e8d7d7c862cabc9467108e3e7f2555653a88).
- **S3:** [README tác giả](https://github.com/arghosh/AKT/blob/master/README.md): Rasch/NonRasch và stack tham chiếu cũ.
- **S4:** [Loader gốc](https://raw.githubusercontent.com/arghosh/AKT/master/load_data.py), [run.py](https://raw.githubusercontent.com/arghosh/AKT/master/run.py), [main.py](https://raw.githubusercontent.com/arghosh/AKT/master/main.py). Các URL branch dùng cho discovery, phải hash lại snapshot pinned khi triển khai.
- **S5:** [PyKT AKT main](https://raw.githubusercontent.com/pykt-team/pykt-toolkit/main/pykt/models/akt.py). Chưa xác minh nội dung tại pinned SHA candidate.
- **S6:** [PyKT data loader](https://raw.githubusercontent.com/pykt-team/pykt-toolkit/main/pykt/datasets/data_loader.py).
- **S7:** [PyKT training](https://raw.githubusercontent.com/pykt-team/pykt-toolkit/main/pykt/models/train_model.py): đường AKT dùng cc/cr/cq, y[:,1:] và masked BCE.
- **S8:** [AKT MIT license](https://raw.githubusercontent.com/arghosh/AKT/master/LICENSE).
- **S9:** [PyKT MIT license](https://raw.githubusercontent.com/pykt-team/pykt-toolkit/main/LICENSE), [pinned setup](https://raw.githubusercontent.com/pykt-team/pykt-toolkit/2fc4d64880956f21155a238d0b0302ac42cb5196/setup.py), [commit history](https://github.com/pykt-team/pykt-toolkit/commits/main/), [candidate commit](https://github.com/pykt-team/pykt-toolkit/commit/2fc4d64880956f21155a238d0b0302ac42cb5196).
- **S10:** [PyTorch installation guide](https://pytorch.org/get-started/locally/). Không coi trang selector là chứng nhận compatibility cho code AKT cũ.

GitHub API commit URLs không truy cập được qua công cụ; xác minh SHA bằng commit links từ history. Một số pinned raw URLs cache miss; ghi rõ phần chưa xác minh thay vì gán branch main vào commit đó. Không dựa số stars vào đánh giá fidelity/maintenance.

### Nguồn nội bộ

`docs/research/bkt-gam-kt-baseline-benchmark-report.md`, `docs/bkt-gam-kt-benchmark.md`, `docs/kt-data-semantics.md`; source `shared_kt.py`, `gam_kt/{runner,splits,evaluation}.py`, `bkt_baseline/metrics.py`; `scripts/bootstrap_bkt_gam_cv.py`; manifests/data paths §3; `requirements.txt`, `pyproject.toml`, `.gitignore`; các spec/plan lịch sử §2. Facts thesis theo yêu cầu người dùng, không khẳng định đã đối chiếu bản đăng ký đề tài chính thức.

### Các phép kiểm đã thực hiện

Discovery ban đầu: PowerShell `Get-Content`, `rg --files`, `rg -n`, `git status --short`, `Get-Command`, `py -0p`, `wsl -l -q`, `wsl --status`, CIM RAM/video (Access denied). Python hệ thống/venv qua stdin: `sys.version`, `sys.executable`, `importlib.util.find_spec`, `psutil.virtual_memory/cpu_count`, `shutil.disk_usage`, listing cache. SQL DuckDB in-memory, memory_limit=512MB/threads≤2 trên prediction Development/sidecar và assignments đã lọc Development; không tạo persistent table/file. Aggregate count/unique, quantile lengths, identity join chia khoảng source_row; phép join lớn thất bại được ghi ở §10. SHA-256 ba file §3. Không chạy pytest hoặc model smoke.

Revision trước approval: chỉ Python stdin chạy bằng `venv/Scripts/python.exe` để đọc dữ liệu, không cài hoặc ghi environment. Đã chạy:

- `pd.read_csv(..., dtype=str, keep_default_na=False)`, nunique/raw-empty/strip-casefold-collision/cardinality checks và duplicate-name metadata comparison; hash catalog; DuckDB register catalog unique trong RAM, join Development p theo exercise để group count rows/distinct user/exercise cho mọi topic/area.
- Tái dựng outer OOV từ set `(exercise,fold)`, đối chiếu `train_support_students=0`; lấy users affected, đọc 13.585 prediction rows của họ rồi join sidecar time bằng source_row, sort user/time/source_row; lặp ranks tính a/a' theo §7.4. Không fit model/vocab vào outer labels hoặc đọc Holdout.
- Group raw Development sidecar theo `(user_id,time_done)` trong 8 bucket user-hash; lấy 1.174 tie groups/2.348 rows rồi intersect canonical source rows từ Development predictions; kết quả 1.174 retained rows/0 canonical ties. Các query memory≤512MB, threads=1, insertion-order preservation=false, timestamp audit tắt spill bằng temp_directory rỗng. Timestamp min/max/null/modulo và GAM CV unit đọc riêng. Không quét raw ProblemLog hoặc canonical toàn bộ chứa Holdout.
- Một câu CREATE VIEW dùng bound parameter không được DuckDB hỗ trợ đã fail BinderException trước khi đọc; chạy lại bằng fixed literal path thì thành công. Không sửa code production để giải quyết lỗi audit.
- `git check-ignore -v` xác nhận `.gitignore:13`; `git status`, whitespace/content checks chỉ đọc để kiểm bàn giao. Không stage/commit/đổi Git config hoặc `.gitignore`.

SQL mẫu audit metadata (metadata là DataFrame catalog unique đã register; p chỉ trỏ GAM CV Development):

```sql
SELECT m.topic, count(*) AS interactions,
       count(DISTINCT p.user_id) AS learners,
       count(DISTINCT p.exercise) AS exercises
FROM p LEFT JOIN metadata m ON p.exercise=m.name
GROUP BY m.topic ORDER BY interactions DESC, m.topic;
-- Lặp cùng query cho area; giữ N/A thành nhóm được gắn thiếu ngữ nghĩa.
```

SQL tie discovery chạy cho mỗi bucket b=0..7:

```sql
SELECT user_id,time_done,count(*) AS n,count(DISTINCT exercise) AS exercises
FROM read_parquet('artifacts/gam_kt/derived/source_map/source_sidecar.parquet')
WHERE hash(user_id)%8 = $b
GROUP BY user_id,time_done HAVING count(*)>1;
-- Register kết quả nhỏ; join sidecar để lấy source_row rồi intersect p.
-- Group retained rows lại theo user_id,time_done để tính canonical ties.
```

Evidence paths của revision: `dataset/junyi_Exercise_table.csv`; `artifacts/gam_kt/derived/source_map/{source_sidecar.parquet,sidecar_manifest.json}`; `experiments/gam_kt/results/wsl_cpp/cv/fold=*/predictions/part-*.parquet` và `cv.json`; `.gitignore:13`; source timestamp heuristic `src/knowledge_tracing/gam_kt/runner.py:_timestamp_unit`; `docs/bkt-data-readiness-audit.md:36`. Không sửa những nguồn này.

Builder check độc lập của draft ban đầu đã đối chiếu `shared_kt.py`. Một reviewer độc lập khác đã đọc revision và shared contract: kết luận “nothing important left” để lập plan sau approval; xác nhận global anchors/known segments/prior reconstruction, metadata N/A, sum/mean training separation, selection/refit/fixed-budget và graph-off controls đủ rõ. Đây là review mức tài liệu, không phải evidence model leakage tests đã pass. Các lựa chọn §14 vẫn PENDING APPROVAL.

Để tái lập phân bố lengths (chỉ đọc Development artifacts):

```sql
WITH lengths AS (
 SELECT user_id, count(*) AS n
 FROM read_parquet('experiments/gam_kt/results/wsl_cpp/cv/fold=*/predictions/part-*.parquet')
 GROUP BY user_id
)
SELECT min(n), quantile_cont(n,[0.25,0.5,0.75,0.9,0.95,0.99]), max(n),
 count(*) FILTER (WHERE n=1), count(*) FILTER (WHERE n>200),
 sum(n) FILTER (WHERE n>200), sum(greatest(n-200,0)), sum(ceil(n/100.0))
FROM lengths;
```

**Điểm dừng:** chờ review và chấp thuận đặc tả. Chỉ sau đó dùng `writing-plans` để tạo implementation plan; việc duyệt design/plan không tự cấp phép chạy full fold/CV/Holdout.
