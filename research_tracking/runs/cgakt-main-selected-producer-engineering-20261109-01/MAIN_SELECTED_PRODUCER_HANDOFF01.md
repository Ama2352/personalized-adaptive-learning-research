# Main selected-only A0–A3: bàn giao nguồn01

Ngày09/11/2026. SOURCE-ONLY: agent chưa import, compile, chạy test, đọc corpus, tạo authorization hoặc chạy model.16 hàm test là số đếm tĩnh, **chưa có verdict PASS**. Bản kế hoạch trước code `MAIN_SELECTED_PRODUCER_PATCH_PLAN01.md` (998a771f…) giữ nguyên; ghi chú này giải thích các refinement sau review của ROOT.

## Bốn tệp mới, không thay pilot

- `src/knowledge_tracing/akt/research_main_execution.py`: spec/profile/input cụ thể; factory kiểm actual authorization, nguồn/runtime/Gate và public corpus trước model. Không CLI/tạo authorization.
- `src/knowledge_tracing/akt/research_selected_runner.py`: actual selected-fit80 → epoch raw-selection10 → complete-epoch checkpoint → fresh best reload → raw-best-selection10/claims. Tái sử dụng trainer, prediction/export primitives, context index, condition factory và checkpoint hiện có; không sao chép training loop.
- Hai tệp test cùng tên trong `tests/akt/`:10 kiểm guard/metadata/file-mock và6 kiểm orchestration. Không test nào là bằng chứng actual preflight/Gate, model fit hoặc corpus thật.

Entry hiện là `run_main_selected_candidate(spec, evidence, *, authorization_file, expected_authorization_sha256)`. **Factory actual guard chỉ chạy một lần bên trong entry**; caller không được đưa execution token/callable/MainStageNOAUTH thay grant. Đây là refinement có chủ ý so với chữ ký dự kiến ở plan01, ngăn việc tin token giả hoặc bắt đầu lại đồng hồ từ một caller-supplied guard.

Scope đầu tiên chỉ Grade10 simulator CPU A0/A1/A2/A3. Junyi, SAKT và GKT bị từ chối trước source/data/model allocation. Điều này không miễn ba phần còn thiếu trong required9/two-environment allocation. A0 dùng một model độc lập, internal empty condition có identity riêng; external estimator graph vẫn `None`. Không dùng A3-off làm A0. Không chạy system selector, external freeze, refit90, calibration hoặc lifecycle resume.

## Authorization và provenance đóng

Auth phải là file thật ở vùng AKT được phép, schema1 exact fields:
`schema_version, scope, decision, run_id, config_sha256, execution_spec_sha256, stage_spec_sha256, identity, caps, requested_phases, approval_reference`.

Scope `simulator-research-main-selected-only-v1`, decision `AUTHORIZE_BOUNDED_MAIN_SELECTED_ONLY`; phases duy nhất `select_train80, raw_selection10`. Caps gồm exact research budget/read/context/checkpoint/input/output/CPU-thread/Git-profile. Identity bind actual21/22/23/26/allocation, source build hashes, runtime/lock/Gate pointer/report/log, corpus public manifests/bytes/domain/bank/plan/audited train+selection role, topology/Method24 request. SHA hoặc claim không tự cấp quyền; agent không tạo file auth để chạy.

Actual public reader vẫn audit cả ba role như Protocol22 cho phép; chỉ typed train và selection đi vào model. Không oracle/final/Holdout. Bank phải có đủ84reference items; các role/count/support đối chiếu từ public reader thật. Graph A2/A3 hoặc learned topology cần actual Method24 loader; TRAIN80 lineage và declared/learned topology được condition factory đối chiếu. Không tạo fake Loaded/Verified object hoặc tự điền confidence.

## Windows Git profile: validation thật, không bypass

Old pilot `_native_evidence` không chấp nhận process-only safe.directory/core.autocrlf profile đã dùng thực sự trong native03. ROOT cho phép validator riêng **chỉ trong module mới**. `MainGitProfile` pin Git executable SHA, actual EOL probe, ba physical upstream file SHA, source root chính xác dưới project, và đúng3process config entries: fsmonitor=false, safe.directory=source_root, autocrlf=true. Reject mọi extra/missing `GIT_`/`GH_` setting, transport, root khác, shadow Git, symlink/junction đường dẫn nguồn. Không sửa/strip/restore environment trong validator; launcher phải cung cấp profile được review.

Sau admission profile, mã vẫn gọi nguyên bản `native_auth.preflight` và `native_auth.require_gate2_evidence`: genuine Git/PIN/remote/source/runtime/lock/source-build/elapsed checks còn bắt buộc. Matching Git profile không cứu stale Gate. EOL probe là bằng chứng Windows đã có; không gán nó thành Linux LF hoặc cross-host PASS. Profile metadata fixtures không chạy Git và không tạo runtime certificate.

## Training/ledger và terminal

Giữ nguyên config/maxepochs20/dropout.05/patience3/min_delta.0001/native BCE. `phase_inputs()` cấp train-only; `epoch_validation_inputs()` cấp raw selection read-only khi đang fit; final best export dùng phase riêng. Không tối ưu bằng calibration, không đổi reporting LL thành epoch objective.

GraphAdam tracker là observer thực của Adam. Durable event reserve trước actual body; body-returned và committed có bộ đếm/targets riêng, đối chiếu actual tracker cumulative counters. Final progress không pending không tính thêm step. Budget bước/targets/train-time/wall/RSS/free-RAM/output tính chung qua mọi epoch và hai fresh model/Adam constructors, không reset ở best reload. Adam/trainer nằm trong explicit CPU device context, giữ nguyên numerical config.

Save best sau complete full train epoch bằng checkpoint f40; restore index train trước save vì receipt bind train index. Reload vào fresh owned containers, initial backbone match; inspect/restore thật; đóng tracker sau restore trước inference. CP `fitted_research_model=False` giữ nguyên nghĩa state-container, actual authorized complete-fit terminal riêng mới ghi sự kiện đã xảy ra. Đây không là resume hoặc certificate nghiên cứu.

Raw prediction primitive dự đoán mọi target trước khi join nhãn scoring; OOV vẫn null/có reason, full denominator được giữ. CSV giữ chronology native; sortedK downstream chỉ là statistical view. Best-reload raw rows phải semantic-exact so với raw epoch đã chọn. Terminal/artifact SHA+size lấy từ file thật; MainStage completion vẫn NO_EXECUTION_AUTHORITY. Lỗi/incomplete/source/resource có failure receipt, không auto-retry hay tự fallback A0. Cleanup thread trước publication; failure sau COMPLETE vẫn ghi failure override khi writer còn hoạt động. Owned outer/Job phải bảo vệ hard timeout và yêu cầu terminal **không có** failure trong actual integration sau này; cooperative source guard không phải sandbox.

## Điều ROOT cần kiểm tiếp

Đề xuất targeted pure command sau source review: `.venv\Scripts\python.exe -B -m pytest tests/akt/test_research_main_execution.py tests/akt/test_research_selected_runner.py -q --junitxml=<exclusive-owned-path>`; dự kiến16 logical cases,0NN/optimizer/corpus thật. ROOT chọn outer cap/cold-canary/owned cleanup; agent chưa chạy.

Sau khi nguồn freeze, actual source Gate hiện tại phải được refresh trước bất kỳ main fit. Chưa có actual main authorization, topology request, resource allocation hoặc actual selected-only terminal cho nguồn mới. Required9 file-admission/external freeze, SAKT/GKT/Junyi producers và refit/calibration driver vẫn là các dependency riêng; không chuyển typed metadata completion thành quyền dùng chúng.

`main_selected_producer_source01.json` ghi exact source SHA/size của batch và các dependency đọc đối chiếu. Những test/mocks mới chỉ hỗ trợ review orchestration; không thay actual native fitting acceptance.
