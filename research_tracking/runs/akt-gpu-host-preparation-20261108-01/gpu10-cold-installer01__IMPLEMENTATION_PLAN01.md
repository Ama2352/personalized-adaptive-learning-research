# Plan trước implementation: hidden cold install vào empty venv

08/11/2026. **Chưa có installer mới, mock, target process, pip/network/install, hardware hoặc GPU action.** Đây là input contract/source plan, không runnable config/authorization và không full T4 readiness. Giữ old CPU-v3 main/guards/venv.json/cfg/proofs nguyên bytes. Reference: `../COLD_GPU_HOST_PREPARATION_CONTRACT01.md`.

## Entrypoint nhỏ nhất

Một source artifact mới `gpu10_hidden_install_empty01.py`, explicit mode **`GPU_HOST_CUDA_HIDDEN_INSTALL_EMPTY`**, trusted ROOT cố định, output stage mới độc quyền, exact source SHA/packet SHA/approval reference. Chỉ từ **fresh actual empty-venv creation descriptor** của cold-bootstrap02 đã được review; audit warm-existing44 không là đường vào installer. No repair/reuse/auto retry/auto nextphase.

Reuse có provenance từ v3: bounded `read_owned`, strict PIP `verify_effective_config`, top-level METADATA selector+ALL RECORD origins, exact selectedURL/hash parser, sequential owned-PG cleanup ledger và cooperative resource checks. **Không gọi old `main` hoặc old `parse_inputs` nguyên hardcodedPINS**: chúng bound CPU venvidentity5dc/cfg0b, Python3.13.18/glibc2.39/basepip26.2.2 và CPU-host guard. Chỉ reuse algorithm, thay input-binding bằng actualfresh descriptor/profile được review. Old source không sửa.

CLI dự kiến: `BASE -I -S -B NEW_SOURCE --mode GPU_HOST_CUDA_HIDDEN_INSTALL_EMPTY --expected-source-sha256 HEX --input-packet PATH --input-packet-sha256 HEX --attempt-id NEW --approval-reference ACTUAL`. Base controller no-site; mọi normal-startup subprocess chỉ sau cả base+target startup gate. Child env allowlist, CUDA/NVIDIAhidden, owned HOME/TMP/config/cache, PIP_CONFIG_FILE=/dev/null, no inherited PIP/UV/PYTHONPATH/CONDA/LD settings.

## Packet chính xác và vai trò receipts

Schema machine-readable ở `input-packet-schema01.json`. Các artifact được copy exact bytes vào `ROOT/artifacts/akt/gpu10-cold-install-inputs/<id>/`, trước/sauSHA+original locator/origin kind và parent-review ref. Không rewrite raw descriptor hoặc đổi local-derived receipt thành remote-produced. Receipt path ở STAGING ngoàiROOT giữ original provenance khi copy. Packet là prerequisite evidence, không tự cấp quyền execute.

| Artifact bắt buộc | Nội dung phải kiểm ở actual target trước install |
|---|---|
| fresh_bootstrap_descriptor + bootstrap_result + bootstrap_policy | Source02/packet pins, ROOT absent→newcreation, `.venv --without-pip`, command/PG cleanup/≤30s accepted; fresh actual ABI/executable/lexical entry/currentbase/cfg. Status descriptor vẫn pending startup/pip review. Không dùng copied oldvenv.json. CfgSHA có thể trùng0b nếu actualfreshcreation thật; không yêu cầu hash khác để giả freshness. |
| actual_cfg | Exact cfg bytes từ venv đang tồn tại; system-site-packages false, no symlink venv/root, lexical venvPython resolve đúng approved currentbase. Hash đo lại ngay trước child. |
| fresh_empty_probe | Current target normal-prefix/sys.path/user-site sau reviewed startup, zero distributions/targetpip/Torch/NumPy specs; source/descriptor/cfgSHA và actual ABI bind. Không fake prefix từ no-site `/usr`. Partial/nonempty/mismatch STOP, không uninstall/repair. |
| startup_review | Actual current **BOTH base+target** startup facts+review; PTH/RECORD/helper/systemlink exceptions exact và explicitenv nếu cần. OldCPUfacts/FCD không tự là fresh acceptance; phải đo match lại. Unknown/changed hooks STOP trước basepip hoặc normal target. |
| base_pip_review | Actual runtime pipversion/origin/source hashes và effectiveconfig flat/nested exactdevnull được review; Python-isolated khác pip--isolated. Current implementation hỗ trợ reviewed26.2.2 policy, không giả oldversion còn tồn tại; khác thì STOP source/tooling review, không global install/downgrade pip. |
| linux_lock + selected_report + resolution_provenance | Lock60dad giữ exact44 officialdirectURLs/hashes, selected44/14NVIDIA/source92a2 report. Đây là historical Linux resolver metadata, không freshhost/install proof. Root requirements29/no-requested-extras source pinned; không dùng Windows lock/resolution. |
| target_compatibility | Actual targettags/completePEP508 environment +all44RequiresPython/activeRequiresDist fixed-closure evaluation; details dưới đây. Receipt mustbind descriptor/ABI/cfg/startup/basepip/lock/selectedmetadata/tool source+version/origins. |

## All44 compatibility không được suy từ tên Torch

Stored `gpu08.../received/resolution-attempt01/pip-report.json` có44packages,29requestedroots, không requested_extras fields; **41Requires-Python declarations**,22packages cóRequires-Dist/tổng**478rawrows**, đa số extra-dependent. Ba Requires-Python absent phải được ghi `unspecified`, không gọi là ba case bỏ kiểm. Chưa tính active count cho target mới.

Preflight riêng cần dùng **public packaging tooling có actual version/origin/hash được review**, không tự viết resolver/PEP508 parser, không `pip --platform` Windows để giả Linux markers. Preferred base publicpackaging chỉ dùng nếu thực sự có và đã qua base startup review; chưa có proof thì STOP, không tự fallback pip-privateAPI/install thư viện. Không coi tooling đó là runtime dependency đã có trong empty target.

Actual target tag receipt có thể lấy bằng public basepip `--python TARGET debug --verbose`, sau BOTH startup gates; source/parser/toolversion phải pinned và output bounded. Phải đối chiếu từng44 wheel filename (URL-decode basename, normalized name/version, complete tagset intersection), không chỉ cp313Torch. Descriptor hiện tại chưa có targettags; CPython/glibc strings không thay fulltag coverage.

Require-Python và Requires-Dist validator chỉ **kiểm fixed selected44**, không chọn version/graph/config. Dùng exact full target PEP508 environment11fields (implementation_name/version, os_name, platform_machine/release/system/version, python_full_version, platform_python_implementation, python_version, sys_platform), không copy resolverCPUenvironment. Public Requirement/SpecifierSet/Version/Marker semantics; record rawclause, marker context, active/inactive, selectedprovider/version and satisfaction cho toàn478rows. Currentroots không yêu cầu extras: prove that from pinned roots/report; nếu active clause yêu cầu extras/directURL/grammar ngoài reviewed validator policy thì STOP/review, không silently drop/auto resolve. Inactive extra clauses có reason, không bị tính là missingcoredependencies. Active requirement thiếuprovider hoặc version conflict →STOP trước download.

Preflight receipts dựa stored resolver metadata, không wheel-byte attestation. Installation `--require-hashes` mới kiểm downloaded wheel bytes. Sau install phải compare report44URLs/hashes+metadata, chạy actualtarget pip-check0, và đối chiếu actual METADATA requirement fields/active closure với preflight để không coi report metadata là toàn bộ binary proof.

## Execution sketch sau khi đủ actual receipts và root approve source

1. Validate strictpacket/schema/roles/types/SHA/actualcurrentGPU-host indication/TPUabsent; allfreshbindings; remeasure actualemptytarget/cfg/ABI/startup. Receipt missing/pending không được defaultTrue. Đây chưa xác minh actualT4/driver/CUDA.
2. Một attempt, direct exact44 command: `BASE -I -B -m pip --python TARGET install --require-hashes --no-deps --no-index --only-binary=:all: --no-cache-dir --no-compile --no-input --disable-pip-version-check --progress-bar off --retries 0 --timeout 20 --report NEW_REPORT -r LOCK`. Không sdist/buildfallback/upgrade/globaldependencies. Actualcfgdescriptor mới thay oldCPU PINS, không dùng hashinequality làm proof.
3. New installreport phải equal44selectedURLs/hash/name/version,14NVIDIA. Post pip-check dùng basecontrols-target, exact44 top-levelMETADATA+ALLRECORDorigins, actual current ABI/prefix/moduleorigins, eightCPUimports/scalar/cuda-uninitialized. Oldimport8 cópytest; discovery8 cópackaging. New audit không hardcode oldPythonpatch/glibc như identity: freshapprovedfacts+tag/requirementsreceipt là expectedvalues, packagebehavior vẫn phải actualpass.
4. Accepted chỉ **`HIDDEN_EMPTY_INSTALL_CPU_AUDIT_ACCEPTED_NOT_CUDA_READY`**; no check_runtime/CUDAavailability/devicequeries/model/optimizer. CUDA runtime/context/auth/worker/resume là phase khác.0explicitAPIqueryledger không wholedependency/hostsyscall attestation.

Overall600s, workspace20GiB/min30GiBfree, bounded logs; cooperative, không network/hardquota claim. Proposed installchild deadline controllerstart+480s, reserve120 cho pip-check/audit/cleanup/posthash; eachstage uses remainingoverall and explicitcleanup reserve, checks observedRC0deadline too. No stalePGIDdoublekill; allhandled groups cleanup_once/reap/failureblocksaccepted. Hash bounded outputs trước operativepostelapsedverdict; smallfinalpublication/outerpostelapsed cần được kiểm. Failure partialvenv/logs giữ nguyên, không retry/repair. Các timeallocations là **engineering proposal chờreview**, không actualthroughput/price forecast.

## Gaps hiện tại — chưa có runnable install packet

- Người dùng vẫn CPU; chưa actualpostmanual GPU cold descriptor/cfg/result, currentbase/target startup receipts hoặc normal-emptyprobe.
- Cold02descriptor hiện ghi pipruntime/effectiveconfig/targettags=None và normalprefixfalse; chưa có complete fresh PEP508environment/compatibility receipt.
- Chưa actual reviewed publicpackaging tooling onnewbase hoặc all44tag/41+3RequiresPython/478marker evaluation; không được biến oldresolverCPUreport thành target mới.
- Source/newinputrelocation preparer/newemptyinstaller chưa implemented/tested/approved. Warm20mocks/cold24mocks không thay các gaps này. Next source-prep nhỏ hợp lý là validator/schema-bound entrypoint failclosed khi thiếu receipts; actualmetadata/tooling phases cần nguồn/approval/budget riêng. Không run network/install/target để viết plan này.
