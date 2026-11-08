# Chuẩn bị GPU-host: các bộ kiểm tra local đã freeze, chưa chạy GPU

08/11/2026. **Bản trình root review trước đóng bundle.** Hồ sơ này ghi source-preparation cho nhánh warm và cold sau khi người dùng chọn GPU thủ công. Bốn phần dưới đây chỉ được kiểm bằng local mocks/AST/metadata; chưa có actual fresh GPU-host discovery, bootstrap, hidden audit hoặc installer. Không đổi hardware, không chạy model, GPU/Modal, cài gói hay dùng dữ liệu nghiên cứu trong gói chuẩn bị này.

## Phạm vi bằng chứng

Working root: `artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/`. Bundle dự kiến: `research_tracking/runs/akt-gpu-host-preparation-20261108-01/`; chưa được tạo khi lập dry inventory. Các receipt lưu command, elapsed, hash trước/sau và scope; logs unittest được giữ nguyên, không tạo JUnit giả.

| Phần/source hiện tại | Kiểm tra cuối trên đúng source | Budget cumulative của riêng phần | Điều đã chứng minh |
|---|---|---|---|
| `gpu10-hidden-audit01/hidden_audit01.py`, SHA `21da29e8575aa6e5b4dc00f37b684b8a713c6749592e4dc3681c083fd66fa282` | `current-combined06`: **20 methods PASS**,0fail/error |3.552282299962826/30s|Pure guards cho bindings/startup origins/payload và reserve80+10s. Không chạy normal-target child.|
| `gpu10-host-discovery01/host_discovery.py`, SHA `4c41381fe00069cf888addfa89865abcba98c711b2a1462294dbaf136b5cde03` | `trial02`: **9 methods PASS**,0fail/error |0.5567243999976199/15s|CLI/source rendering và receiver consistency bằng synthetic RPC objects. Không tạo actual request/receipt GPU.|
| `gpu10-cold-bootstrap01/gpu10_cold_bootstrap02.py`, SHA `037d5aafc1490afb0ae36c0abb216552625a52993f2dfffee1aa4d6d1a5c5883` | `mock-trial03`: **24 methods PASS**,0fail/error |0.6092078000074252/15s|Owned-PG/time/resource/finalization/customize AST fragments với virtual mocks.0actual venv/Popen/pip.|
| `gpu10-cold-installer01/packet_validator01.py`, SHA `197820549124e8b09047b23939d9c5e9d52412633663bd725e92bb7b698a3c78` | `pure-trial03`: **41 methods PASS**,0fail/error |5.5143692000128794/30s, gồm cả pure metadata analysis|Pure byte/receipt consistency và public packaging compatibility semantics. Không installer/launcher/runtime authority.|

Counts ở bảng là bốn scopes có fixture và kiểm tra dùng chung; không phải số quan sát độc lập hoặc full software Gate. Commands/repeated historical methods nằm trong từng run receipt; không cộng các lượt thành một bộ test độc lập.

## Warm và cold là hai trường hợp khác nhau

Generic discovery giữ discovery02/profile hiện có, nhưng bắt buộc attempt/approval/mode mới `GPU_HOST_READONLY_DISCOVERY`. ROOT absent phải trả `COLD_ROOT_ABSENT`, không tạo ROOT/target child/venv và không cấp install authority. ROOT partial hoặc ABI/source mismatch STOP, không repair. Warm chỉ có thể xét sau actual fresh GPU-host labels, nguồn/profile,165source hashes trước/sau, kết quả/launcher hash và cleanup của **cả native child lẫn launcher**. Host indication chưa xác nhận T4/driver hoặc CUDA usability. Reply giới hạn48k; oversized RPC phải ghi prefix hash đúng nghĩa, không gọi prefix là hash toàn response.

Warm hidden auditor có explicit mode `GPU_HOST_CUDA_HIDDEN_AUDIT_ONLY`, chỉ tái dùng existing44 nếu fresh provenance/ABI/metadata/source matches. Nó tái dùng nguyên old post-audit `CHILD` SHA `a2b6bf03cb1c0a546a4d437525a80e869edfc6ed1abaca11fdc177b2c3991d98`, không sửa old CPU-v3 main/guard. Old eight CPU imports gồm pytest; discovery eight origins gồm packaging thay pytest. Target normal child chỉ có thể chạy sau reviewed startup guards, CUDA/NVIDIA hidden, không gọi `check_runtime` hoặc `cuda.is_available` trong child. Ledger0explicit device API không là attestation mọi syscall của imported dependencies. Bounded postchecks/cooperative limits không là hard OS quota; không chứng minh recovery orphan cho mọi outer interruption.

Cold bootstrap chỉ chấp nhận ROOT **thực sự absent**, source/packet stage ngoài ROOT. Nó tạo isolated `.venv --without-pip`, đo actual ABI/cfg/lexical executable và no-site emptiness; descriptor chỉ mang status `FRESH_EMPTY_VENV_DISCOVERY_PENDING_STARTUP_AND_PIP_REVIEW`. ROOT present kể cả missing/empty venv STOP; không lấy old `venv.json` làm fresh creation. Cfg có thể cùng hash nếu fresh creation thực sự cùng môi trường; không dùng hash inequality giả freshness. `--owned-child` là orchestration nội bộ hợp tác, không independent authorization boundary. Source02 dành24s cho child/6s cleanup+posthash trong tổng30s; outer actual postwall vẫn phải kiểm sau final small publication.

## Actual CPU startup facts chỉ là baseline để kiểm lại

Nguồn actual đọc trước đó: `actual-startup-facts02.json` SHA `10015564bade7735038ded84d88973028e89801b6a1fde8960f1bb6cc97787dc`, và `actual-startup-facts03.json` SHA `c06098c2ae42994fdf50119b8238570f0c292d00b5d52e311a004149b58dda7a`. Chúng là no-site stdlib source reads trên **CPU host hiện hữu**, không normal startup/GPU audit.

Có đúng một `distutils-precedence.pth`,151B, SHA `2638ce9e2500e572a5e0de7faed6661eb569d1b696fcba07b0dd223da5f5d224`; entry được bind vào actual setuptools84.2.1 RECORD SHA `0d3d398cf0c3a9df7726ff7565a78a7f187e73fed033c647b4e45cecffb0d114`. Body chỉ gọi `_distutils_hack.add_shim` khi `SETUPTOOLS_USE_DISTUTILS=local`; reviewed policy dùng `stdlib` và chỉ hợp lệ nếu actual fresh preflight match lại. `sitecustomize.py` tại `/usr/lib/python3.13/` là system symlink tới `/etc/python3.13/sitecustomize.py`, target actual empty0B/SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; usercustomize/apport_helper không có trong facts. Exception giới hạn đúng empty system target này, không nới source/input/output no-symlink guards. Unknown/changed hooks STOP.

Normalized public facts và original safe JSON/provenance được chọn vào inventory. Raw startup01 traceback/private RPC không copy; normalized record giữ actual failure do guard từ chối nonregular symlink cùng hash nguồn, không biến failure thành package/GPU mismatch. CPU discovery02 actual warm candidate trước đây được lưu riêng tại [báo cáo discovery CPU](akt_t4_discovery_readiness_20261108.md); hồ sơ mới không relabel CPU result thành fresh GPU evidence và không nhân đôi toàn bundle cũ.

## Pure44/478 metadata analysis

Selected report SHA `92a2bbae1cdf285491bac1d67082d16c824aeb2ca9447d841a8182807be671dd` và direct-wheel lock SHA `60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a` giữ nguyên từ Linux resolver lịch sử. Bộ kiểm mới dùng **public packaging26.3**, không custom resolver:44wheel filename/name/version/URL/hash/tag checks,41Requires-Python declared thỏa/3unspecified,29requested roots,14NVIDIA. Full478Requires-Dist rows đã ghi raw/index/marker/provider/reason: **46active satisfied,432inactive**.

Đây là engineering regression dùng **marker environment của historical CPU resolver**, và **synthetic union of selected wheel tags**, không actual target tags của máy GPU. Full output `gpu10-cold-installer01/compatibility-engineering-summary01.json`134509B SHA `e4a71f75f75737e57bc8ad063aa87d73729402bd3184c76c8755a6e4f9b35f07`; canonical dependency ledger SHA `116e49c1e6ee80f408dd1ac933808fbb10b515d6b09f1c5871f31f8d7a6e986d`. Không suy wheel-byte verification/install success từ metadata/hash advertised.

Validator nhận đủ11artifact byte copies và `trusted_review` **ngoài packet**; strict pinned cold02/source/policy/cfg/ABI/result/approval/config/origin fields, old CPU role/pending/nonempty/mismatch reject. Future startup/basepip/empty-normal-probe/compatibility receipt schemas chưa có actual fresh GPU producers. Trusted-review role là declared cooperative input, không chữ ký hoặc chứng thực freshness. Output luôn execution_authorized=false, runtime_or_install_verified=false; live origins/filesystem/hook inspection và approval/authentication vẫn phải có riêng. Chưa có installer process launcher. Plan600s/20GiB/min30GiB và install deadline480+120reserve mới là proposal, không actual throughput/cost proof.

## Failure và các revision được giữ

- Cold mock01:17methods gồm16PASS/1FAIL, do Windows fixture path expectation; sửa fixture sang PurePosixPath, production source01 không đổi; mock02 actual17PASS. Cold02 hardening theo static review rồi mock03 actual24PASS; không fabricate RED cho static findings.
- Packet pure01:39methods gồm28PASS/7FAIL/4ERROR. Allowlist thiếu hostname official **đã có** trong pinned lock `download-r2.pytorch.org`; không phải dependency/runtime failure. Narrow source fix và negative assertion cụ thể dẫn pure02 actual39PASS. Final consistency fix bind cfg.version/ABI, bootstrap approval/cap30 dẫn pure03 actual41PASS. Tất cả source snapshots/logs/receipts giữ nguyên.
- Warm: historical13PASS, origin-focused3PASS, combined16PASS, reserve4PASS, post-exit4PASS và final current20PASS; PathFinder/cleanup-reserve fixes bắt nguồn static review, không giả test đỏ. Generic01 và02 đều9PASS; revision cuối sửa nhãn prefix-vs-whole-response hash, không nhận receipt mới là actual.

## Điều còn thiếu trước bất kỳ chạy GPU nào

Người dùng chưa chọn GPU trong gói này; warm persistence sau hardware switch chưa được chứng minh. Cần actual fresh generic discovery. Warm cần fresh source/ABI/package/startup binding và actual hidden audit; cold cần actual bootstrap rồi **cả base+target startup review**, normal-empty prefix/origins, reviewed actual basepip/effectiveconfig, full target tags/11markerfields và active dependency evaluation. Missing/unknown inputs STOP, không tự cài/downgrade/repair/resolve.

Actual CUDA runtime report, Linux software Gate acceptance theo native source/lock validators, public bounded cuda-smoke/context/authorization, VRAM/time limits và resume là các phase chưa được thực hiện bởi nguồn chuẩn bị này. Existing [Linux CPU worker proof](akt_linux_worker_readiness_20261108.md) là historical CPU evidence, không new-host GPU PASS. Không có CUDA model updates, trainer throughput/cost estimate, refit/research/Holdout hoặc paid cloud allocation từ mocks.

Dry packager chỉ snapshot text nguồn/receipt/log/public facts và hash inventory trước/sau; loại private RPC/request encoded payload/ZIP/wheels/venv/models/data. `record_evidence_run`/`verify_evidence_bundle` chỉ được gọi để đóng sau root duyệt exact report+dry inventory; SHA integrity không thay scientific/runtime review. Root xử lý index/Git; báo cáo và old closed bundles không bị sửa bởi việc lập inventory.
