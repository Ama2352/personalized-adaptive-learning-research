# Publisher metadata của index main Gate05

Source chuẩn bị `publish_gate05_main_index01.py`, SHA0365e7850af024e3bf99ec87afeaf55e8087822e38c64c26a82e515f1c345414. Việc chạy chờ ROOT review, actual outer Gate05 ACCEPTED và report runtime schema2 thật.

Worker gọi `worker_gate()` ngay đầu `main()`, trước argparse và đọc metadata. ROOT có thể gọi qua helper0dc hiện có, với owned27giây gồm cleanup3 và outer30giây gồm final postchecks. Worker timer/acceptance là24giây. Input args giữ SHA do ROOT cấp, các paths được cố định theo lượt05. Mã được chuẩn bị bằng đọc nguồn và metadata filesystem.

Index duy nhất trong preflight có tên `gate2-main177-win-current-gate-20261109-05.json`. Output vận hành là `P/gate05-main-index-publication01`, gồm exact globalpointer trước/sau và result. Root-owned launch đặt output receipt riêng ngoài thư mục này. Publisher giữ index đã tạo khi postcheck bị từ chối để ROOT review failure. Globalpointer được đối chiếu exact bytes trước/sau.

Các tham số cần Root cung cấp

| Argument | Input cố định |
|---|---|
|`--outer-receipt-sha256`|`P/win-current-gate-20261109-05-outer/result.json`, phải actual ACCEPTED/0errors/RC0/Job0|
|`--report-sha256`|`artifacts/akt/preflight/gate2-evidence-win-current-gate-20261109-05.json`|
|`--log-sha256`|Merged native log cùng run|
|`--packet-sha256`|`P/windows_current_gate_packet05.ROOT.json`, actualeb2949554791e9b52c639e1b51d52dc82431be600e920083533869b179f031c4|
|`--worker-sha256`|Native worker02, actualb59becc9c2af31d10cf20a4afc17a05946a1e9acdd989114d30bcbfb3dc3b374|
|`--controller-sha256`|Full outer03, actual4722088dadf1dc3e45203bb29c242e22d5d54bd66b4141f46b2ab8df28f64f3e|
|`--runtime-report`|Absolute actual schema2 report có parent chính xác `artifacts/akt/preflight`, đề xuất `runtime-schema2-main177-20261109-01.json`|
|`--runtime-sha256`|SHA raw actual schema2 report do ROOT cung cấp|
|`--lock-sha256`|Actual `requirements-akt.lock.txt`|
|`--self-sha256`|Publisher sourceSHA phía trên|
|`--build-map-sha256`|SHA của `json.dumps(native_report['build_hashes'],sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()`|
|`--global-pointer-sha256`|SHA raw historical currentpointer trước lượt, hiện9e768aadcf084482a2eeb9be814fc399100dd1a507eaa89afbbae87100365cd6|
|`--approval-reference`|ROOT review cho đúng index publication này|

Publisher xác thực actual outer/source/controller/packet, hash lại toàn bộ output files được outer liệt kê, yêu cầu177native build paths và81test modules. Sau public preflight thật, nó tạo năm trường đúng format native và gọi public `require_gate2_evidence`. Toàn bộ input map và current build map được đối chiếu lại, reader được gọi lần cuối và environment phải nguyên giá trị.

Gate05 dùng runtime legacy259c. Báo cáo đó được giữ đúng SHA từ packet Gate. Report schema2 mới có nguồn/upstream/lock/venv được public preflight kiểm tra lại. `authorization.require_gate2_evidence` dòng126–175 không nhận runtime-reportSHA và native Gate report không bind runtime-reportSHA vào predicate của reader. Do đó có thể dùng report schema2 thật khác SHA khi cùng context được validator hiện hành chấp nhận. Receipt publisher ghi riêng `gate_original_runtime_reference` và `selected_runtime_report`. Main guard sau đó bind SHA schema2 mới trong `ResearchRuntimeEvidence`. Nếu report mới không hợp lệ, publisher dừng trước tạo index.

Process Git environment phải được caller chuẩn bị trước launch theo chính profile của `research_main_execution.MainGitProfile`, gồm `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=nul`, `GIT_CONFIG_COUNT=3`, lần lượt `core.fsmonitor=false`, exact `safe.directory=D:/Dev/KLTN/artifacts/akt/dependencies/upstream`, `core.autocrlf=true`, cùng `GIT_OPTIONAL_LOCKS=0`, `GIT_TERMINAL_PROMPT=0`, `GIT_ALLOW_PROTOCOL=__NO_TRANSPORT__`. Mã kiểm tra exact các biến GIT_/GH_ và giữ nguyên environment. Root không nên thêm config ngoài profile đó cho publisher.

Actual proof03 SHA cac0e916a29f81f8f716aad5d9df05ea5c9e13c591f000fee0a130d02a499361 và EOL proof a0307845fbd04ff1b7e52dea821ed9159462005876c4facfdd18be62c40ca6fd được bind trong source. Git origin/path/hash phải trùng actual binary đã review. Public preflight chạy một lần, bằng original `verify_upstream`, trong phase chỉ nhận đúng mười read-only Git commands theo thứ tự. Windows audit `executable=null` hoặc literal `git` được ghi đúng raw value. Các subprocess khác, network, imports framework và truy cập corpus/model inputs bị guard từ chối. Index có software-evidence identity để main guard tiêu thụ. Execution authorization tiếp tục được main public guard kiểm tra riêng.

Nếu Gate05/runtime/profile/source không còn phù hợp, publisher dừng và giữ output phục vụ review. Receipt của worker phải được ROOT đánh giá cùng owned cleanup, overall elapsed và absence của `postwrite-rejection.json`.
