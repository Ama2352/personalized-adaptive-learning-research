# GKT frozen engineering adapter: pipeline inference, chưa fitted baseline — 08/11/2026

**32 portable unit tests PASS và một integration riêng load checkpoint GKT04 thật đã đạt;0optimizer updates mới.** Hai loại bằng chứng được tách rõ: unit container có role `unverified_fixture`, không phải trained model; integration giữ role `synthetic_trained_engineering_only`, không nâng thành research fitted. Không realdata/Holdout, corpus/training, GPU/cloud, network/install hoặc broad88/45/40-case rerun.

## Hành vi đã implement

Chỉ hai tệp mới: [adapter.py](../../src/knowledge_tracing/gkt/adapter.py) và [test_adapter.py](../../tests/gkt/test_adapter.py). Không sửa GKT checkpoint/training/recurrent/core/config/exports, shared KT hoặc AKT. Public `load_frozen_engineering_gkt` dùng nguyên GKT04 strict loader, kiểm expected checkpoint/inference identity trước load và kiểm returned trained role; private unit assembly không phải public authorization boundary. Model đóng băng eval/requires_gradFalse, source/weights/graph/recipe/binding được kiểm trước/sau inference.

Inference binding chứa bank, item vocabulary, ordered GKT node IDs/unit, explicit one-item→one-existing-node mapping, graph/recipe/domain/source/checkpoint SHA. Mapping multi-tag, foreign node/item, cross-domain hoặc concept mapping trái bank bị reject; không fit/map ngầm, không transfer Junyi→Grade10. **Mapping provenance là `caller_declared_inference_mapping_NOT_training_attested`**: GKT04 receipt bind toy node-domain/weights, chưa chứa chứng nhận item-bank/mapping đã dùng trong training. Bank-domain string equality và checksum không thay scientific training-domain certificate.

`predict_details(CausalSequenceInputs)` dùng shifted prior responses và original source-row/learner segmentation; score current target trước khi observe response đó. `query/query_many(GKTHistory, ItemQuery)` chỉ nhận past observations và current item/time/source row, không current answer/latent oracle. Cả hai đi qua cùng full-prefix predict/observe path, không cache state theo learner, không implicit context truncation hoặc fake practice từ probes. Item→node là readout theo node: hai item cùng node có cùng score trên cùng history; không bịa item-difficulty correction. `score_kind='uncalibrated_node_response_probability'`, không latent mastery hoặc calibrated item success.

Spec bắt buộc khai báo `history_policy='full_prefix'`, `oov_policy='unsupported_history'`, cold `query_only` hoặc `unsupported`, CPU/dtype và≤12events. Engineering bounds≤2learners/4nodes/8items, widths≤8. Unknown active query không vào embedding−1; bank-known item ngoài declared vocabulary là `oov_item`, vocabulary item chưa mapping là `unmapped_item`. Nếu real past event bất kỳ không map được thì later known targets trả `unsupported_history`; không skip/reset history ngầm. Global rank/history_available đếm mọi real event; history_used=0 cho unsupported và context_reset=False vì không có reset nội bộ. Cold-unsupported chỉ bỏ score đầu, vẫn observe real past event để target sau có history.

Mọi original target giữ một output, kể cả unsupported: probability=None cùng support reason và source identity, không finite0 sentinel hoặc silent row intersection. `predict` ndarray từ chối nếu có unsupported; `population_summary` yêu cầu exact original row order và ghi `research_fitted_targets=0`. Private/mock outputs giữ unverified role. `fit` và `as_online_backend` từ chối; shared `OnlineScore` vẫn chỉ nhận fitted/unseen_item, không sửa contract để đưa engineering score vào fitted `OnlineSession`.

## Bằng chứng và target population

| Lượt | Kết quả | Phạm vi |
|---|---|---|
| `parallel-gkt-adapter-20261108-unit01` |**32PASS/0fail/error/skip**, pytest23,79s/controller33,578948s | Portable mocks + explicitly unverified random container, no default untracked binary dependency. Kiểm offline/query/manual parity, masks/OOV/cold, learner/probe isolation, current/future-label invariance, source/weights/map drift, guards/role rejection, CPU/default-meta/RNG/immutability |
| `parallel-gkt-adapter-20261108-integration01` |**1 actual weights_only CPU checkpoint load**,0mock loads; controller10,083794s≤remaining18s | Exact stored GKT04 `.pt` được bind immutable metadata/COMPLETE/bundle SHA trước load; genuine stored trained toy weights, không train lại. Kiểm offline/query parity, same-node aliases, immutable probes, trained-engineering role và fitted route rejection |

Cumulative conservative **51,662743/60s**: lấy max monotonic/wall mỗi controller, cộng8s static-preflight reserve.0optimizer updates ở cả hai; Adam.step bị chặn trong fixtures/controller. Không có failed test/integration trial hoặc retry trong batch. Đề xuất ban đầu dùng stored binary trong default unit fixture được parent yêu cầu đổi **trước tests**, không mô tả nó như actual RED/failure.

Actual integration dùng6 handmade targets của1 learner, không nghiên cứu sample hoặc simulator run mới:

| Source row / global rank | Support reason | Scored? / history_used |
|---|---|---|
|101 /0|cold_query_only|Có /0|
|102 /1|known_history|Có /1|
|103 /2|unmapped_item|Không /0|
|104 /3|unsupported_history|Không /0|
|105 /4|oov_item|Không /0|
|106 /5|unsupported_history|Không /0|

**6expected=2scored+4unsupported,0research_fitted.** Sự từ chối sau OOV không làm mất global rank hoặc biến partial coverage thành full fitted population. Cold inclusion ở đây chỉ explicit engineering fixture, chưa benchmark denominator adoption.

[Actual result](../../artifacts/akt/local-tests/parallel-gkt-adapter-20261108-integration01/result.json) chứa từng score/role/source identity, coverage, exact input hashes và inference binding. Input weights `346807fdb44f9e9a37861073d593d523d9006f788f753c98016820179dfb909c` giữ ở artifact GKT04; metadata `01912938f358d667d42972faa0adbe56f8f287166c32284a3bfad5977c62e466`, COMPLETE `6aaf8cac5c084c82669c463a93f9ae8fa0992ef26ee184ba4b8902f53334c890`, [GKT04 manifest](../runs/gkt-checkpoint-engineering-20261108-01/manifest.json) `0e0f0a19e466fd9c334e7fc279a1ebe4669babd0c2b8dd000542c009207b4cac`. Không copy model binary vào GKT05 bundle hoặc embed base64 vào test source.

| Frozen source/evidence | SHA-256 |
|---|---|
|Adapter source|`2e6c4ed64433dac63f54344710303cf0908b0c66cc63735a71f3f6d23f42c0f4`|
|Portable test source|`08b7dccd4b66278d47bf5508768d2bdb9cc3cacb92290c0acbbbffd56c947ba7`|
|Unit JUnit|`338025c372dc334812139e15f4d9822095c275904952be1f173e9b786defbad0`|
|Actual integration result|`28f6c8e4dcd8d7476c9c131ad3e0ec40bd338de798c365843790556e3db466cc`|
|Frozen acceptance|`9f585832e32dc31950db7aeeddfa691158434d019499ca84c2bad6f5a3a95ccf`|

Ten implementation/test dependency hashes trước/sau cả hai lượt khớp, giữ40source snapshots. Integration helpers được tạo một lần và giữ source/current fingerprints; không dựng preexecution snapshot certificate riêng cho helper nếu chưa có. Actual reader instrumentation đếm1call và gọi nguyên weights_only Torch loader trên verified BytesIO, không fake data/model/result. Các source checks/bindings là cooperative consistency, không hostile-caller attestation hoặc nonresettable data authorization.

Parent source/actual receipt review và report/inventory approval là bước trước closure; không dựng independent-reviewer-agent PASS. [Bundle dự kiến](../runs/gkt-inference-adapter-engineering-20261108-01/README.md) lưu raw logs/JUnit/result, source snapshots, controllers, exact input lineage và raw parent review; packager không rerun model/tests.

## Chưa hoàn tất baseline

Adapter làm usable frozen inference và population accounting, chưa epoch/corpus trainer, selected-fit/refit/calibration, common research comparator hoặc closed-loop fitted session. Existing `OnlineSession` không nhận engineering score role; role-aware shared interface cần được duyệt riêng, không thêm parallel ticket/session framework ở đây. Proposal vẫn yêu cầu GKT comparator. Full-prefix, cold/OOV, graph variant/provenance, item/node/multi-tag mapping, information/capacity matching và S04/S05 chưa scientific adoption. GKT04 không restore optimizer/RNG/hidden state; GKT05 không thêm resume hoặc biến stored toy weights thành fitted research model. Không suy efficacy/RQ completion/learning benefit từ test counts hay2scored targets.
