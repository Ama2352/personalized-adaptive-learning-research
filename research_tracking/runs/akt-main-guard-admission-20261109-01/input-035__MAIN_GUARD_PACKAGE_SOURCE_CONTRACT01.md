# Chuẩn bị package cho actual Main A0 guard — nguồn chưa chạy

## Phạm vi hữu hạn

Hai file mới `prepare_main_selected_guard_package01.py` và `run_prepare_main_selected_guard_package01.py` chỉ chuẩn bị metadata cho bước guard admission. Bản này chưa chạy/import/test, chưa tạo native config, authorization, request hoặc dry payload. Các nguồn production đã được Gate05 kiểm vẫn giữ nguyên. Actual guard và actual selected fit đều chưa được thực hiện bởi hai file này.

Stage tiếp theo sử dụng corpus canonical60 đã có, audit đủ48train/6selection/6calibration và10.080/1.260/1.260events. Reader được phép kiểm cả ba public roles theo Protocol22. Không dùng calibration để tối ưu, chọn epoch/candidate, hoặc fit temperature ở bước này. Không mở oracle/final, không sinh learner/response/world, không import model/trainer.

## Các bước tách biệt

1. `--prepare-dry` phải qua genuine owned GO trước domain imports hoặc corpus reads. Worker audit exact public10 bytes rồi dùng public `read_public_research_corpus`, tạo typed specs và A0 empty condition qua `GraphTrain80Binding`/`prepare_research_graph_condition`. Không tạo corpus object giả. Gọi **hàm thật** `research_main_execution._metadata(spec,evidence)` để có identity, gồm genuine native preflight/Gate/source/corpus metadata checks. Đây là private dependency cần giữ rõ, không thay API production hoặc monkeypatch validators. Kết quả chỉ là một wrapped proposal có `execution_authority=false` tại `P/main_guard_package01_dry.json`, cùng receipts/logs trong P.
2. ROOT đọc dry rồi mới có thể cho phép `--materialize` với exact dry SHA và review reference. Mode này có namespace owned/output riêng, tái audit cùng inputs và so toàn bộ wrapped proposal với dry. Ba đường dẫn final phải đồng thời chưa tồn tại trước khi ghi. Chỉ ghi exclusive native config, authorization và request, giữ phần ghi dở nếu lỗi, không retry/overwrite. Materialization chưa chứng minh guard được chấp nhận.
3. Actual guard admission sau đó dùng worker/outer cũ `check_main_selected_guard01.py`/`run_main_selected_guard01.py`, với requestSHA và ROOT operation reference riêng. Hai builder không gọi guard factory hoặc `run_main_selected_candidate`. Lifecycle fit/export/checkpoint cần allocation khác sau review, không được suy từ bước metadata.

## Typed contracts và bindings

Builder dùng nguyên lớp `AKTConfig`, `ResearchResourceBudget`, `SimulatorResearchSpec`, `ResearchRuntimeEvidence`, `MainSelectionContext`, `MainSelectedStageSpec`, `MainSelectedExecutionSpec`, `MainGraphInput`, `MainGitProfile`, `CorpusReadLimits`. A0 stage có external graph condition `None`, còn implementation condition là empty A0 tính thật từ public corpus. Stage source identity dùng đúng map177 trong accepted native Gate report, không thêm scratch builder vào map177. Request source pins bổ sung builders, guard controllers, helper và5tài liệu để kiểm prep/admission.

Runtime schema2 là `artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json`, SHA `3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b`. Index riêng là `artifacts/akt/preflight/gate2-main177-win-current-gate-20261109-05.json`, SHA `e8162f6efce3ca0a443f6c40f69308b06b610e95d5a02504ba146e92b6f87366`. Giữ nguyên globalpointer. Genuine `_metadata` vẫn phải xác nhận mọi runtime/Gate/protocol/source/data identity; tên file hoặc SHA-shaped claim không cấp quyền.

Native config giữ seed42, context100/target100, batch4, architecture256/8/1/1024/512, dropout.05,20epochs/patience3 và optimizer recipe frozen. Chỉ resource allocation cho guard được chốt1optimizer step/1optimized target/1training second,45s main wall/RSS1GiB/free2GiB. Source validators hiện chỉ yêu cầu các caps dương/đúng đối chiếu, không thấy minimum bắt buộc nhiều hơn1. Chưa có actual admission proof cho bộ caps này. Nếu actual guard từ chối, giữ failure và review, không tăng cap tự động.

## Resource, process và I/O

Mỗi metadata mode là một operation mới, whole60s gồm cleanup3/finalization2, worker50s. Không gộp thời gian của prepare và materialize thành một lượt. Worker monitor RSS1GiB/free2GiB, clock không reset; owned Job cung cấp hard cleanup bên ngoài checks hợp tác. Root phải review packet/caps trước dispatch. Không dự báo runtime từ các giới hạn này.

ROOT phải cung cấp đúng process Git profile Windows native03. Wrapper so khớp toàn bộ `GIT_`/`GH_`, không strip hoặc sửa profile không phù hợp. Child dùng actual Git binary/PIN/EOL kiểm bởi production `_metadata`; chỉ cho phép đúng10read-only provenance commands, không network/transport. Actual `platform.uname`/`platform.processor` được warm trong phase giới hạn trước domain imports; chỉ cho exactSystemRoot `cmd /c "ver"` tối đa3lần, không fake OS fields. Phase đóng bằng `finally`. TEMP/TMP/TMPDIR trỏ owned/runtime-temp trước các domain imports. Parent environment được restore.

Không blanket-claim sandbox toàn filesystem. Python audit chặn neural/solver/teacher imports, network, children ngoài whitelist, protected data và mọi corpus path ngoài exact public10. Source chỉ có các thao tác ghi exclusive tường minh. Các field zero model/optimizer/teacher phản ánh phạm vi bị cấm và source path, không neural efficacy. Mọi denied attempt, kể cả bị bắt exception, làm verdict không accepted.

## Root command sau source review

Wrapper nhận `--worker-sha256`, `--outer-sha256`, `--approval-reference` và đúng một mode `--prepare-dry` hoặc `--materialize`. Mode materialize cần thêm `--expected-dry-sha256` và `--review-reference`. Chưa có các command được thực thi trong nhánh này. Actual producer vẫn mới hỗ trợ Grade10 A0–A3, không dùng MainStage metadata của Junyi để bỏ qua adapter chưa có. Chín candidates và hai môi trường vẫn là yêu cầu nghiên cứu.
