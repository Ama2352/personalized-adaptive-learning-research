# GRAPH29 — audit candidate01 và wire sửa candidate02

Ngày09/11/2026. SOURCE-ONLY. Không import/AST/test/native/Git, không sửa canonical hoặc candidate01 đã freeze. Candidate01 inventory `8942a568db520fe4a63f82644d3aff4d4060c19f0c085c257d482578df682e21`, handoff `c5d9f5261ff3c65bcd96072914a758dbc862394c5da4a2d13e655e647d690e44`; plan02 `05e135f998f4b28a803844a303f6fd43450c65a0a5053f8a0c163166930b664c`.

## Hai defects ROOT đã đồng ý sửa trước apply

**Owned launch crosswire.** `research_selected_resume.py::seal_pause_terminal` kiểm accepted receipt/worker SHA/Job0 và marker nhưng không nối worker result với actual worker token/job/request của chính receipt. Hai lượt cùng generic worker source có thể bị trộn artifact do wiring sai. Worker resultB + clean receiptA vẫn thỏa các predicates hiện tại. `inspect_parent` lặp lại khoảng trống đó. Source equality không chứng minh hai files đến từ cùng process operation. Phải bind actual helper launch/ready/GO/token với returned result và parent request trước khi cho child sử dụng.

**Retained quota.** `control_binding` cho policy/request max_retained_bytes nhỏ hơn spec.max_output_bytes; parent inventory bị kiểm theo cap nhỏ, nhưng `_Run` và các write helpers của child chỉ dùng spec.max_output_bytes. Child có thể vượt declared lineage cap nhỏ. ROOT chọn một quota duy nhất. Candidate02 sẽ yêu cầu cả policy và request `max_retained_bytes == spec.max_output_bytes`, vẫn cộng parent retained bytes vào child usage. Không thêm quota plumbing thứ hai.

Điểm nhỏ cùng closed-wire validation là cần kiểm `policy.after_epoch == state.epoch == marker.epoch`. Actual publisher đã ép equality khi tạo pause, consumer cần giữ nó khi đọc metadata; không suy lịch pause mới từ một marker khác.

## Các semantics đã kiểm

* `semantic_spec` bỏ đúng native run_id/output_dir và derived stage.config_sha256. Giữ nguồn/runtime/Gate/corpus/graph/encoding/budget/recipe/hyperparameters và mọi field khác. CP identity hiện có cũng bỏ run/output, nên reuse CP không cần sửa low-level checkpoint.
* Parent latestE và bestB được phân biệt. History liên tục1..E, cumulative targets và exact objective được kiểm; actual EarlyStopping replay diễn ra trước constructor. Runner kiểm replayed best_epoch trùng state best_epoch. Tie/min_delta/patience giữ helper hiện có.
* Genuine CP inspect diễn ra trước constructor; fresh initial hashes kiểm trước restore. CP restore đặt CPU Python/NumPy/Torch RNG cuối. Sau restore chỉ có byte/metadata/guard operations trước train_epoch; shuffle là private Random(seed+epoch), không reseed thêm hoặc tạo loader RNG giả. Cần witness native mới để chứng minh actual equality.
* Cumulative prefix steps/targets/training/wall/retained bytes được giữ; optimizer restore event có schema riêng và không tăng counters. Parent1+child2 physical constructors là trần3. Exact before/after-body counters giữ nguyên. Monotonic epochs khác process không bị trừ trực tiếp.
* `check_parent_refs` là cheap terminal/marker/receipt audit ở batch boundaries. Full parent inventory được kiểm khi admit, mỗi epoch và trước finalization. Không là filesystem isolation hoặc phát hiện tức thời mutation của mọi unselected parent file. CP restore/copy tự có source/copy/source-after checks. Concurrent external writers chưa có quyền từ API này.
* Sealer nhận elapsed từ ROOT outer. Outer tương lai phải kiểm actual whole elapsed sau seal/hash/write và giữ failure override nếu trễ, không lấy một prehash elapsed làm final acceptance.

## Wire candidate02 cần ROOT review trước code

Chỉ derivative sáu paths của candidate01 dưới thư mục `cgakt-selected-resume-candidate02`. Candidate01/before inventory giữ nguyên. Không thêm launch framework hoặc sửa helper0dc.

### Worker result

Future ROOT-reviewed pause worker ghi đúng chín keys.

```text
schema_version = 1
status = PAUSED_MAIN_SELECTED_COMPLETE_EPOCH
execution_spec_sha256
authorization_file
authorization_sha256
request_file
request_sha256
ownership
pause_reference
```

`ownership` chính là actual dict trả từ `windows_owned_worker.worker_gate()` ở đầu worker, không caller boolean. Exact tám fields hiện có là `status, worker, parent_owner, os_parent_pid, nonce, ready_sha256, job_name, preGO_forbidden_imports`. `pause_reference` giữ bốn fields đã có. `execution_spec_sha256` lấy actual typed parent spec.identity sau closed request parsing; authorization fields là actual file được genuine parent factory tiêu thụ.

Request file vẫn do actual worker/ROOT driver có closed schema riêng kiểm. Resume module chỉ hash/read bounded actual request bytes và bind exact argv, không viết lại parser main hoặc gọi một callback được caller đánh dấu verified. Convention worker argv cho phase1 cố định sáu strings `--request, relative_request, --request-sha256, digest, --approval-reference, actual_reference`. Future worker/outer phải được review riêng theo convention này trước execution.

### Terminal và typed child request

Terminal giữ12 fields cũ và thêm đúng một subrecord `launch_proof` có chín fields.

```text
worker_result_file, worker_result_sha256,
request_file, request_sha256,
execution_spec_sha256,
authorization_file, authorization_sha256,
protocol_sha256,
ownership
```

`protocol_sha256` exact map ba names `launch.json, ready.json, GO.json`. Các file này nằm cùng directory với accepted helper receipt. Receipt có existing path/SHA fields ở terminal. `ownership` là exact actual worker_gate dict, kiểm trùng raw worker result và launch protocol.

`SelectedResumeRequest` thêm hai SHA bắt buộc `expected_parent_request_sha256` và `expected_parent_execution_spec_sha256`. Chúng nằm trong closed resume auth subrecord đã được ROOT SHA-bind. Existing expected_parent_worker_sha256 giữ nguyên. Factory fresh/public original authorization schema không đổi. Parent spec SHA khác child vì run paths khác; consumer dùng actual parent invocation.spec để kiểm exact parent SHA, sau đó semantic projection so với child.

`seal_pause_terminal` thêm keyword bắt buộc `expected_request_file`, `expected_request_sha256`. Parent typed spec đã là argument của sealer; không thêm trusted flag hoặc resolver callback. Parent invocation.json đã có full spec metadata và actual authorization SHA từ genuine guard. Sealer/consumer kiểm chúng với worker result và bounded authorization bytes. Có thể thêm authorization_file vào invocation chỉ trong controlled branch để kiểm path trực tiếp, giữ fresh default wire.

### Những so sánh bắt buộc

1. Đọc bounded bytes một lần cho mỗi JSON rồi parse chính bytes đã hash. Kiểm actual worker result SHA, request SHA, authorization SHA và protocol map. Alias/path protections giữ nguyên. External Root request SHA và parent spec SHA phải bằng expected fields, không chỉ bằng hai strings trong cùng một JSON.
2. Exact launch/ready/GO schemas theo helper0dc. `manifest.nonce == ownership.nonce == ready.nonce == GO.nonce`; job_name bằng manifest/GO/ownership và accepted receipt.job_name. Hash ready bytes bằng GO.ready_sha256 và ownership.ready_sha256. GO dict phải bằng exact `{nonce,ready_sha256,worker,job_name}`.
3. Exact worker token dict bằng ownership.worker, ready.worker, GO.worker và receipt.actual_worker. Parent owner bằng manifest.parent và receipt.parent. Ready.parent_pid bằng ownership.os_parent_pid và receipt.popen.pid. Không reopen/reclassify dead PID, không coi same executable là same launch.
4. Actual receipt accepted/GO_released/worker_returncode_before_cleanup/returncode/cleanup_accepted/popen_handle_closed phải đúng; Job0, cleanup/errors rỗng, helperSHA0dc, worker SHA bằng external expected pin. Không accept chỉ từ status text. WorkerResult ownership.status/preGO_forbidden_imports cũng exact helper values.
5. Manifest.worker_args bằng sáu strings theo actual request file/SHA/review reference. Hash canonical argv phải bằng ready.argv_sha256. Receipt.command bằng exact entry/-B/worker path/argv từ manifest. Manifest worker SHA/helper SHA bằng ready và receipt. Entry/prefix thuộc fixed physical repository .venv, giữ genuine helper semantics. Không normalize một wrong drive thành đúng drive.
6. Worker result spec SHA bằng sealer parent spec.identity và hash parent invocation.spec. Authorization SHA bằng invocation.authorization_sha256 và bytes actual authorization; decision/closed resume subrecord vẫn do genuine factory kiểm. Consumer xác nhận parent invocation semantic projection bằng child spec, không bỏ nguồn/runtime/Gate khỏi comparison.
7. Marker/state/history/accounting/output inventory và original quota checks như candidate01; thêm exact retained cap và pause epoch. Toàn bộ launch proof bytes phải được kiểm lại trước child admission. Cheap boundary audit giữ thêm worker result/request/protocol/authorization immutable pins, còn full parent-output audit giữ các epoch boundaries.

Giữ max directory/file/byte caps và outer deadline. Metadata receipt equality chỉ là consistency dưới cooperative pinned-source contract. Actual ROOT worker/outer/fresh-process evidence vẫn bắt buộc; manufactured fixtures không biến thành ownership proof.

## Regression derivative dự kiến

Giữ30ca cũ nhưng sửa manufactured fixtures theo schema mới, không gọi chúng actual. Thêm same-source crosswire negative với hai job/token/nonce/request khác nhau; workerSHA giống hệt. Thêm wrong expected request/spec SHA, wrong token/GO/ready SHA, stale worker-result bytes và thấp retained cap. Exact physical IDs/count chốt từ source derivative sau ROOT review wire, không gọi dự kiến này là collection/PASS. Actual helper processes và NN vẫn0 trong metadata tests; hai genuine EarlyStopping tests tiếp tục có Torch library import riêng như đã công bố.

Phase1 intentional pause-only giữ nguyên. Phase2 durable crash/partial-epoch physical-cost recovery, persistence và benchmark vẫn là blocker trước Stage7 long paid; metadata corrections này không đóng blocker đó.
