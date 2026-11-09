# Đề xuất triển khai nhỏ cho Linux CPU provenance của Main

Ngày09/11/2026. Chỉ đọc source, JSON và hash bằng PowerShell. Chưa import/chạy Python, Git, tests, model hoặc sửa production. Đề xuất này chờ ROOT duyệt trước release hai file. Linux runtime/Gate của batch hiện tại chưa có.

## API và hai file được chạm sau khi duyệt

1. `src/knowledge_tracing/akt/research_main_execution.py` thêm dataclass frozen `MainLinuxGitProfile`. Giữ nguyên `MainGitProfile` Windows, các constants, mapping environment và nhánh kiểm EOL Windows. `MainSelectedExecutionSpec.git_profile` nhận union chính xác của hai concrete classes, không subclass/duck typing.
2. `tests/akt/test_research_main_execution.py` thêm fixtures metadata và negatives riêng cho Linux. Không sửa config/model/runner/checkpoint/authorization/provenance, các source upstream hoặc reports cũ.

API mới được đề nghị có các trường `mode`, `executable`, `executable_sha256`, `source_root`, `proof_file`, `proof_sha256`, `upstream_files_sha256`. Mode duy nhất `linux-cpu-lf-v1`. `proof_file` là đường dẫn relative được old._path kiểm dưới ROOT/artifacts/akt. Source root vẫn đúng physical ROOT/artifacts/akt/dependencies/upstream. Executable là absolute POSIX physical path, không lexical symlink, không tự mặc định /usr/bin/git. Binary SHA và proof SHA do ROOT lấy từ actual target rồi pin trong config/auth, không có giá trị mặc định.

`_git_environment(profile, source_root, platform_name)` dispatch theo exact class. Nhánh Windows hiện hành giữ nguyên. Nhánh Linux chỉ nhận platform_name linux và exact source root. Spec kiểm metadata theo platform của class thay cho literal win32 hiện ở182. Actual `_main_native_evidence` vẫn dùng sys.platform thật và reject cross-host trước data/model. Kiểm lexical POSIX bằng PurePosixPath ở pure metadata để tests Windows không giả làm filesystem Linux.

Nhánh Linux trả đúng process environment với GIT_CONFIG_NOSYSTEM=1, GIT_CONFIG_GLOBAL=/dev/null, GIT_CONFIG_COUNT=3, key0 core.fsmonitor=false, key1 safe.directory=exact physical source root, key2 core.autocrlf=false, GIT_OPTIONAL_LOCKS=0, GIT_TERMINAL_PROMPT=0, GIT_ALLOW_PROTOCOL=__NO_TRANSPORT__. Validator vẫn so sánh TOÀN BỘ GIT_/GH_ variables, không strip biến thừa hoặc tự cấu hình môi trường. Việc caller chọn profile này phải minh bạch trong dispatch sau này.

Actual executable dùng shutil.which('git'), đối chiếu physical resolve với profile, hash đúng binary, reject shadow `git` trong ROOT/venv entry/base entry; không áp Windows executable names thay cho tên Linux. Exact Linux Git environment được kiểm trước original preflight. Các symlink interpreter .venv/bin/python tiếp tục theo public authorization.validate_runtime_interpreter, không mở ngoại lệ symlink source/proof/output.

## Proof wire được đề nghị, chưa có actual instance

Một JSON bounded, closed schema_version1, external proof_sha256 do ROOT review là input bắt buộc. Top-level đúng các trường sau.

- `schema_version`, `kind` với kind MAIN_LINUX_CPU_PROVENANCE_V1.
- `platform_id` bằng linux, `project_root`, `python`, `python_prefix`, `source_root` là actual lexical/physical bindings.
- `git` có exact executable và executable_sha256.
- `git_environment` đúng mapping Linux ở trên.
- `source` đúng output original verify_upstream gồm commit/tree/remote/files, không kết quả hand-built hash-object thay thế validator.
- `source_before`, `source_after` là exact ba raw-LF SHA maps, bằng source.files và expected LF; không normalize actual target khi admission.
- `runtime_report_sha256` và `lock_sha256` đúng external ResearchRuntimeEvidence.
- `gate_execution` chứa `receipt_file`, `receipt_sha256`, `controller_file`, `controller_sha256`, `platform_id`, `report_sha256`, `log_sha256`, `pointer_sha256`, `runtime_report_sha256`, `lock_sha256`, `build_hashes_sha256`. Các đường dẫn ROOT-bound. Controller/receipt là actual ROOT-reviewed Linux owned Gate run, không Windows Gate đổi nhãn.

Trường gate_execution bắt buộc vì public Gate schema1 hiện không lưu platform. Admission cần đọc SHA-bound actual Linux outer receipt và kiểm accepted status, actual platform/command interpreter/root, RC0, cleanup accepted, source before/after, current native outputs/runtime/lock/build bindings theo ĐÚNG schema controller mà ROOT chọn. Không chấp nhận một boolean verified hoặc SHA-shaped string tự đủ quyền.

Đây là một integration gap phải chốt trước implementation Linux actual path. Linux controller hiện tại của batch cũ không tự thành schema cho batch mới. Nếu chưa có agreed controller receipt schema và actual receipt, Linux `_main_native_evidence` phải dừng với lỗi provenance chưa đủ trước public corpus. Không thêm producer/normalizer/fake receipt vào batch hai file này. ROOT có thể duyệt phần metadata/source validation trước, giữ actual admission unavailable cho đến khi chốt proof reader.

Sau proof checks vẫn gọi nguyên `old.native_auth.preflight` và `require_gate2_evidence`, đối chiếu source trả về, schema2 runtime platform_id linux/device cpu/cuda_available false, lexical .venv/bin/python và prefix/ROOT/origins, exact lock, current build, Gate index/report/log SHA như nhánh hiện hành. Không thay build_hashes_fn, source verification, timeout/count conditions hoặc Gate report. Các kiểm CPU hidden/config và authorization closed schema vẫn giữ. Profile đã nằm trong asdict(spec), caps/auth identity nên khác profile làm stale auth.

## LF expected từ ba bytes Windows đang pin

Tính read-only CRLF→LF trong bộ nhớ, không viết checkout/ZIP. Chưa quan sát raw bytes trên Linux. Cả ba có bare CR bằng0.

| File | SHA Windows actual hiện tại | Bytes CRLF | Cặp CRLF | SHA LF prospective | Bytes LF |
|---|---|---|---|---|---|
| LICENSE |891133edce0d8693f5b916d4257ce70b71a02aa110cb02cc5d47326544ea4522|1090|21|50a2c2d2521182935c537a56220083c7a4194abdfbd459b6c682fae32cceb4cf|1069|
| README.md |df8eea9919dcdb343f3a841540af18e2039b8b0c33af449ca9c752d11f56ee8b|1443|52|bec19014f10f469002e46f53175a1599b1be9b2d3fc9fe184129e6da1efd442b|1391|
| akt.py |be2788c20cac602e86ef3a51e5294b37dd7b200f818be4e173dbd69069a3ec6d|14756|360|ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67|14396|

Original verifier vẫn phải nhận commit01b7e8d7d7c862cabc9467108e3e7f2555653a88/tree904863502337ef2eefd1769d14836b62e3c3804a/remotehttps://github.com/arghosh/AKT.git. Đối chiếu tree với actual output cùng source/proof, không lấy raw-LF prospective làm bằng chứng thực thi Git Linux.

## Regression hữu hạn dự kiến

Giữ nguyên Windows positives/negatives hiện có. Thêm Linux concrete profile/env positive thuần metadata, cross-platform và unknown mode, extra credential/transport/config variable, wrong source root/executable/hash, CRLF actual thay expected LF, missing/closed-schema/stale proof, missing actual Linux Gate proof, Windows runtime/Gate receipt không thay Linux proof, public validators thất bại phải dừng trước corpus, và mocked genuine validator readback đúng mà không tạo MainSelectedExecution grant. Các tests dùng manufactured tmpFS/metadata; không gọi Git, Torch, corpus hoặc solver. Exact test count/pins/ROOT-owned bounded controller chỉ chốt sau code và review, chưa có PASS hoặc feasibility runtime.

## Source anchors và pins

- research_main_execution.py59–93 Windows metadata/env,105–135 actual provenance/public validators,182 literal win32,191 CPU config. SHA902018762fde6433a9bd9e33ce770df0057f6b0623327b8ff6b798e1faf4d881.
- tests/akt/test_research_main_execution.py SHA9c102b3645528c5a2b7a4ca7830a68429f824ec0c3199b4d3ba587f88efcc0ce.
- authorization.py25–38 lexical interpreter,49–92 schema2 platform/ROOT/origins,126–175 Gate reader,178–197 original preflight. SHAbd6be914e3b5049927ba6358ee4872097a46469fede9ad1b71ee63df951ac7f0.
- provenance.py28–48 original10 Git commands, actual HEAD/tree/remote/dirty/blob/source checks. SHA493d82af749baefcacec9ece0a7abe3297e64398eb4cd93c1d639ca41752cb59.
- config.py SHAbeb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f.
- Read-only Windows original-verifier receipt upstream_verify_process_eol03.json SHAcac0e916a29f81f8f716aad5d9df05ea5c9e13c591f000fee0a130d02a499361, chỉ dùng đối chiếu pinned commit/tree, không Linux acceptance.

Không enabling fit, CUDA, promotion Windows Gate hoặc cấp chi phí trong đề xuất. Owned Linux launcher và actual target discovery/runtime/Gate là các bước riêng cần review sau này.