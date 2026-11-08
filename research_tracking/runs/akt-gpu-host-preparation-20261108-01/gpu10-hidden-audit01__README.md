# GPU-host hidden audit: source/test đã freeze, chưa remote

08/11/2026. **Warm-existing44 only; không full GPU setup readiness.** Chưa có fresh GPU-host discovery sau manual T4 selection nên chưa có request audit hợp lệ để dispatch. Không chạy normal startup, Torch, GPU, installer hoặc model trong batch này.

## Implementation và bằng chứng local

Source trước hardening PathFinder có SHA **`f9ef5e56caf1b59222b323aa23164878c6cff3ff7f7522c183adfdaeee5735a9`**; test SHA **`b58890366619e23b05db70ac87e041dc85914ab3eef0a4e99bea92c669eae1fb`**. Old auditor source `dd7738...`, CHILD template exact `a2b6bf03cb1c0a546a4d437525a80e869edfc6ed1abaca11fdc177b2c3991d98` và CPU-v3 `578181...` giữ nguyên. Chỉ old CHILD được reuse; không gọi old CPU-only main.

Một invocation local bằng `.venv\Scripts\python.exe -I -S -B .../test_hidden_audit01.py`, outer controller timeout30s. **13 unittest methods PASS**,0failure/error, unittest0.295s/controller **0.8874478s≤30s cumulative mới**. `trial01/` có exact command/log/run.json và năm source/template/manifest snapshots SHA trước/sau bằng nhau. Tests chỉ synthetic metadata/AST/CLI/copy filesystem; không controller main/Popen, target, normal startup, dependency imports hay device/network/install/model. Cleanup ordering được kiểm static và failure verdict được mock, không giả actual kill/reap proof. Construction receipt `source-template-copy01.json` ghi initial derived controller trước hardening; frozen tested source là SHA trên/run.json, không nhầm initial hash là final source.

Root review sau trial01 tìm P2: scan `.py`/package/ZIP bằng tay có thể bỏ qua actual import precedence/extension/.pyc/virtual origin. Giữ nguyên sourcef9ef... +13PASS trong snapshots; đây là static finding, không fabricate RED. **Current source đã freeze `b1925a620787d9feaf846e81917f2d074c7918eed85562c0d5232361f0bb0e68`** thêm stdlib `PathFinder.find_spec` trên đúng no-site sys.path+purelib, chỉ ADD actual resolved origin; unknown binary/bytecode/virtual/missing origin failclosed trước child. Không import/execute hook. Knownempty system-symlink exception giữ nguyên.

Focused `test_startup_origin02.py` SHA `33f7cd4026b7d7c7f525f7449d29f4c75bc623bf80ee38511fb1818f93dcbf92`: **3methods PASS**, controller0.6234439s. Positive source sentinel được locate mà không execute; .so/.pyc/virtual/relative bị reject; exact explicit search và absent customizers được kiểm. Current cumulative **1.5108917s≤30s**,0actual target/model/GPU/normalstartup. Không rerun13/broad, không gộp13+3 thành fullsuite16PASS trên cùng source; `trial02/` giữ actual focused scope và SHA trước/sau.

Sau đó root cho phép đúng một combined regression trên current source để kiểm coupled guards. `current-combined03/` chạy cả hai test modules: **16 unittest methods PASS trên cùng sourceb192...**,0failure/error; child1.0704401s, post-hash controller1.0941311s, cumulative **2.6050228s≤30s**. Sáu source/test/manifest/original-auditor/v3 inputs SHA trước/sau bằng nhau. Không sửa source/tests, không rerun các run cũ hoặc reset cap. Đây là current-source mock regression, không actual target/normalstartup/GPU acceptance; lịch sử13+3 riêng ở trên vẫn giữ đúng scope tại thời điểm từng run.

Root full review tiếp phát hiện P1 reserve: chỉ deadline90 có thể để child chạy tới90 rồi mới cleanup/posthash, dù late rejection đã có. Sourceb192/16PASS được giữ riêng, không fake RED. `reserve-focused04/` bổ sung prechild/whilechild deadline80 và 4focusedPASS; own static review thấy thêm zero-RC vừa qua80 có thể skip whilebody, nên giữ sourceb173/4PASS rồi thêm guard **sau observed exit trước finallycleanup**. `reserve-postexit-focused05/` current source **`21da29e8575aa6e5b4dc00f37b684b8a713c6749592e4dc3681c083fd66fa282`**, test SHA300c6570..., **4focusedPASS**, posthash0.2551422s; cumulative **3.0785155s≤same30s**. Không full16rerun/không gộp counts thành fullsuite hiện tại. Guards80/90 được check bằng pure boundary+AST/static ordering; không actual child/sleep/GPU. Exact oldCHILD và guards khác không đổi.

Actual CPU startup facts02/03 được root thu riêng bằng no-site, không do tests tạo: exactly1PTH151bytes SHA2638..., setuptools RECORD SHA0d3d... bind entry; `/usr/lib/python3.13/sitecustomize.py` system symlink tới exact empty `/etc/python3.13/sitecustomize.py`; usercustomize/apport helper absent. Manifest `reviewed_startup_manifest01.json` SHA **`fcd1175ddc46bb51a64d677d124e682545c32200b48cd9f589dfe64f00feb929`** được tạo từ raw JSON facts SHA100155.../c060..., không Windows/memory. Chỉ optional exact manifest này cho phép PTH đã review + `SETUPTOOLS_USE_DISTUTILS=stdlib` và exception hẹp system symlink→empty target; fresh preflight phải match lại. Không nới global source/input/output symlink guard. Unknown/changed/missing hooks STOP trước child.

## CLI đề nghị, không execute

Metadata-copy preparer riêng sẽ tạo exact-byte relocated inputs tại `ROOT/artifacts/akt/gpu10-hidden-inputs/<id>/`, không auto phase. `copy-inventory.json` schema1/role `EXACT_BYTE_DISCOVERY_RELOCATION_NOT_EXECUTION`, copy_root, phase_auto_execution=false, copies mỗi label có original_locator/origin_kind/destination/bytes/SHA before-after. Labels: baseline, fresh, launcher, acceptance, profile; optional startup_manifest. Destination `<label>.json`; original locator giữ nguồn ngoàiROOT/local đúng thực tế. Acceptance phải `LOCAL_DERIVED_RECEIPT_FROM_VERIFIED_RPC`, fresh phải `REMOTE_DISCOVERY_ARTIFACT`.

CLI dùng một pinned relocation inventory thay năm cặp receipt path/SHA rời, để ràng buộc toàn bộ packet:

```text
/usr/bin/python3 -I -S -B ROOT/artifacts/akt/gpu10/hidden_audit01.py
  --mode GPU_HOST_CUDA_HIDDEN_AUDIT_ONLY
  --expected-source-sha256 21da29e8575aa6e5b4dc00f37b684b8a713c6749592e4dc3681c083fd66fa282
  --attempt-id <NEW_ID> --approval-reference <EXPLICIT_PARENT_APPROVAL>
  --input-directory artifacts/akt/gpu10-hidden-inputs/<id>
  --input-inventory-sha256 <ACTUAL_COPY_INVENTORY_SHA>
```

Actual future fresh wrapper must use generic attempt `gpu-host-*`, source02/profile0944 exact, new GPU_HOST approval, phase `GPU_HOST_READONLY_DISCOVERY`, launcher status `COMPLETED_GPU_HOST_READONLY_DISCOVERY_NOT_GPU_READY`. Derived acceptance status `VERIFIED_ACTUAL_WARM_GPU_HOST_DISCOVERY_NOT_GPU_READY` cần raw RPC SHA, exact result+launcher SHA, parent_review_reference, both cleanup true, source_files165. Source checks exact fresh argv flags/new stage locator; không relabel old CPU raw `b003...` hoặc launcher/acceptance cũ. CPU baseline vẫn pre-switch metadata only. ABI/source/44metadata/RECORD/eight discovery entrypoint fingerprints phải khớp; fresh GPU indication không là T4/capability proof.

## Khi thực sự được duyệt chạy

Warm phase≤90s total, đúng1target child `TARGET -I -B audit-child.py` chỉ sau strict bindings/startup gate. Child env CUDA/NVIDIA hidden, owned HOME/TMP/cache, no inherited PIP/PYTHON/CONDA; old8imports có pytest, discovery8 có packaging, hai tập được phân biệt. CHILD checks normal prefix/origins44/full RECORD paths, CPU scalar và CUDA uninitialized. Không gọi check_runtime (vì nó gọi CUDA availability), pip, network, GPU availability/count/name/arch, model hoặc optimizer.

Deadline target là **controller start+80s**, check prechild, hai lần mỗi vòng quanh resource scan và ngay sau observed exit (kể cả RC0). Chừa10s cho ownedcleanup/reap3s+posthash/receipt trong overall90s; wait timeout không vượt remaining80budget. Cleanup_once đặt handled trước signal, reap/RC/resource/hash/postexit-budget failure chặn accepted và giữ failed child receipt.20GiBworkspace/min30GiBfree là cooperative; không whole-host/OS quota hoặc hard deadline khi OS/filesystem block. Source/input/startup files hash trước/sau, exception duy nhất cho exact reviewed empty system startup symlink. Accepted status chỉ `GPU_HOST_CUDA_HIDDEN_CPU_AUDIT_ACCEPTED_NOT_CUDA_READY`.0explicit GPU-query calls là source ledger, không full dependency syscall attestation. Outer controller bị hard-kill có thể không tới finally; chưa global failure-recovery proof.

**Cold là blocker riêng:** CPU→T4 persistence chưa được chứng minh. Missing/partial/mismatched ROOT/venv không được repair/install từ controller này. Cần bootstrap descriptor/probe và explicit hidden empty-install source khác; không copy `venv.json` cũ làm fresh evidence, không bỏ CPU-v3 guard. Xem note cold contract riêng trước hardware switch.
