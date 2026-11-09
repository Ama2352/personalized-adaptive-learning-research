# Đề xuất02 cho Linux CPU provenance và actual Gate execution profile

Ngày09/11/2026. Revision source-only theo quyết định ROOT. Bản01 SHA b0f960940e17a90f51ec2b384d82c8bd9100013961a126433ff821c551663d38 được giữ nguyên. Bỏ yêu cầu external Linux Gate controller receipt trong bản01. Không sửa production/chạy import/tests/Git/Gate hoặc tạo actual proof ở bước này.

## Bốn file được đề nghị mở trong cùng batch

- src/knowledge_tracing/akt/research_main_execution.py.
- tests/akt/test_research_main_execution.py.
- scripts/akt/refresh_gate2.py.
- tests/akt/test_gate2_refresh.py.

Public authorization.py và provenance.py giữ nguyên. MainGitProfile Windows, fixed Windows constants và Windows Git environment/checks giữ semantics/body hiện hành. Không sửa model/config/runner/checkpoint hoặc các bằng chứng lịch sử.

## Gate wire additive, sáu trường chính xác

Writer thêm top-level execution_profile vào report hiện hành schema1. Object này chỉ có schema_version bằng integer1, platform_id bằng sys.platform, project_root bằng str(ROOT), python bằng sys.executable, python_prefix bằng sys.prefix, writer_sha256 bằng sha256_file(Path(__file__)). Tất cả lấy từ actual process, không CLI override, caller dict hoặc runtime report copy. Không thêm trường quyết định fit/training hay đổi PASS/count/timeout/partition/publication schema hiện có.

writer_sha256 phải đúng trước['scripts/akt/refresh_gate2.py'] từ current build map. Existing whole build-before/after check giữ nguyên. Như vậy report profile và native source population cùng bind writerbytes. Production kiểm thiếu hoặc mismatch build membership phải STOP; fixture map synthetic phải có real test-writer key và SHA phù hợp. Không bỏ comparison để fixtures cũ qua.

Legacy Windows schema1 reader authorization.require_gate2_evidence không đổi và tiếp tục đọc report cũ thiếu execution_profile theo hợp đồng của reader đó. Fresh writer trên Windows cũng ghi actual six fields. Nhánh Windows Main hiện có không tự thêm điều kiện profile khiến historical Windows proof đổi semantics. Source modification vẫn làm Gate05 cũ stale qua current build binding bình thường.

## Main Linux Git API riêng

Thêm frozen MainLinuxGitProfile với exact fields mode/executable/executable_sha256/source_root/proof_file/proof_sha256/upstream_files_sha256. Mode linux-cpu-lf-v1 duy nhất. Không default binary/profile/proof. Exact class union trong MainSelectedExecutionSpec thay vì làm MainGitProfile Windows nhận Linux mode. Pure path metadata dùng PurePosixPath để kiểm absolute/lexical . và ..; actual path kiểm ở actual Linux process.

_git_environment dispatch exact concrete class. Windows branch giữ mapping hiện hành. Linux branch yêu cầu platform_id linux, exact physical native source root, process-only GIT_CONFIG_NOSYSTEM=1, GIT_CONFIG_GLOBAL=/dev/null, GIT_CONFIG_COUNT=3, core.fsmonitor=false, safe.directory=exact source root, core.autocrlf=false, GIT_OPTIONAL_LOCKS=0, GIT_TERMINAL_PROMPT=0, GIT_ALLOW_PROTOCOL=__NO_TRANSPORT__. _validate_git_environment vẫn so sánh exact TOÀN BỘ GIT_/GH_ variables. Không strip biến, global Git config write hoặc auto-mutate caller env.

Spec metadata dispatch theo declared profile platform thay literal win32. Actual _main_native_evidence dispatch sys.platform thật và reject cross-host trước data/model. Linux kiểm physical Git path từ shutil.which('git'), exact profile binary SHA, no local shadow git, physical same-root upstream và .venv. Lexical .venv/bin/python và prefix giữ public runtime-interpreter semantics, không resolve venv-entry symlink thành quyền base Python.

## Source proof wire prospective, chưa có actual Linux proof

Proof JSON closed object với schema_version1; kind MAIN_LINUX_CPU_SOURCE_PROVENANCE_V1; platform_id linux; project_root/python/python_prefix/source_root; git object exact executable/executable_sha256; git_environment exact mapping; source exact original verify_upstream output commit/tree/remote/files; source_before/source_after raw-LF SHA maps; runtime_report_sha256; lock_sha256. Không còn gate_execution hoặc external Gate controller fields. Proof pin do ROOT lấy từ actual target và review, bind trong spec/auth, không suy proof SHA từ bản Windows.

Source expected LF giữ đúng bảng read-only normalization của bản01. LICENSE 50a2c2d2521182935c537a56220083c7a4194abdfbd459b6c682fae32cceb4cf/1069B; README.md bec19014f10f469002e46f53175a1599b1be9b2d3fc9fe184129e6da1efd442b/1391B; akt.py ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67/14396B. Chỉ expected CRLF→LF tính trong bộ nhớ từ ba raw Windows hashes đã pin, không phải actual Linux observation. Admission không normalize target để làm khớp.

Proof checks vẫn đi cùng ORIGINAL preflight/verify_upstream và require_gate2_evidence. Actual output commit/tree/remote/files phải bằng source proof, expected source commit và ba physical LF hashes. Actual schema2 CPU runtime phải platform linux, đúng ROOT/venv/interpreter/origins/lock, cuda_available false. Không fake report, đổi build_hashes_fn hoặc bỏ dirty/remote/blob checks.

## Linux Gate profile acceptance sau genuine public reader

_main_native_evidence lấy đúng gate['evidence_path'] mà public reader vừa trả, đọc bounded bằng old._read_json rồi đối chiếu digest lại với gate['report_sha256'] và external ResearchRuntimeEvidence.gate_report_sha256. Không dò glob/report khác hoặc sửa report/index.

Bắt buộc execution_profile là dict exact sáu keys kể trên, schema_version type int và bằng1, platform_id linux. project_root/python/python_prefix phải đúng actual process vars cùng runtime schema2. ROOT/prefix physical checks và lexical interpreter checks đã mandatory qua genuine preflight; profile equality bổ sung provenance của process writer. writer_sha256 phải đúng native build_hashes['scripts/akt/refresh_gate2.py'] và actual writerfile SHA. Hash-bound report build_hashes vẫn phải current qua genuine reader. Profile field thiếu/thừa, Windows platform, stale interpreter/prefix/root/writer hoặc sai digest đều STOP trước corpus/model.

Không cần external Linux Gate producer/normalized receipt/controller infrastructure mới. Một Windows Gate thiếu profile hoặc ghi win32 không được nhánh Linux nhận dù source/lock bytes vô tình cùng giá trị. Linux runtime/Gate mới vẫn chưa có nên batch code/pure fixtures không enabling actual fit. Future actual runtime/source/Gate/ROOT-owned authorization và dispatch tiếp tục cần riêng.

## Regression hữu hạn, không chạy ở proposal

Test_main giữ Windows environment regression hiện có; thêm Linux metadata positives và cross-OS/extra env/wrong root/binary/source proof/rawLF negatives. Mock public readers để kiểm exact hash-bound report sau genuine reader, legacy missing profile, six-key schema/types, Windows profile, wrong root/python/prefix/writer, stale report reread và failed runtime/Gate phải dừng trước corpus. Pure manufactured fixtures không tự tạo MainSelectedExecution grant.

Test_gate thêm meaningful actual refresh fixture assertion report execution_profile bằng actual vars + writer SHA trong current synthetic build map; simulated platform Linux/Windows kiểm nguồn fields. Đổi fixture build-map để chứa writer dependency, không chỉ mock payload mới. Existing legacy-reader fixture thiếu profile tiếp tục được public reader chấp nhận để giữ compatibility. Không đổi test groups/count/limits hoặc chạy real suite trong fixtures.

Exact added case count/pins và ROOT-owned bounded pure command chỉ đề xuất sau code freeze. Chưa có PASS, target runtime hoặc numerical CUDA claim.

## Pins tại revision02

research_main_execution.py 902018762fde6433a9bd9e33ce770df0057f6b0623327b8ff6b798e1faf4d881.
test_research_main_execution.py 9c102b3645528c5a2b7a4ca7830a68429f824ec0c3199b4d3ba587f88efcc0ce.
refresh_gate2.py 8689c5b4737f4eae00459f4a3bc85c22206f58974274304fa4411e36f9acc055.
test_gate2_refresh.py 268ace8716285c35db15caaae1efc819776795e3ef931f2e14f41b9cbe2a1e3c.

Gate writer anchor refresh235–241; current source freeze/recheck217/277; public Gate reader authorization126–175; actual runtime preflight178–197; Main native evidence105–135. Implementation chỉ bắt đầu sau ROOT release bốn file.