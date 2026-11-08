# Source delta01 và Linux Gate24 — offline preparation

**Chưa apply delta hoặc chạy Gate từ nhánh này.** Parent phải review nguồn trước dispatch. Pure metadata/AST checks:8PASS, controller0,226122giây,0operation-main/filesystem-delta/Git/model/network calls; receipt `source-delta-gate24-offline-tests02/run.json`. Trial01 giữ6PASS/2harness errors, log và old test snapshot; sửa test harness, operation sources không đổi. Không chạy thêm tests.

## Thứ tự bắt buộc

1. **Loader04 trước:** actual accepted receipt đã nhận tại `received-loader-evidence02-transfer03/upstream-loader-transfer03/result.json`; remote path `upstream-loader-transfer03/result.json`. Source loader04 bound `6aff88a7abc9620d6372ee934391d2079bccd253330e7a1e4f0ddcaa436b41b2`. Đọc SHA từ **nguyên bytes actual local file**, không chép terminal hash hoặc tự dựng JSON. Loader03/transfer02 failed trước đó giữ nguyên.
2. **Delta01 source-only30s:** `apply_source_delta01.py` yêu cầu actual loader path/SHA đã accepted, base ZIP/receipt và toàn161files còn đúng baseline. Backup old exact16086bytes vào exclusive `ROOT/source-delta01/test_graph_prototype.before.py`, giữ new17214bytes, thay đúng `tests/akt/test_graph_prototype.py`, kiểm161after/160không đổi. Old SHA5e2aae…→new7a198d…; không sửa production/native model hoặc assertions để nới tolerance.
3. **Nhận actual delta evidence:** giữ `source-delta01/result.json`, before/after inventories, backups và `ROOT/gpu09-worker-kit-materialization-02.json` nguyên bytes. Parent verify raw receipt hashes trước tạo Gate request. Partial delta STOP, không tự rollback/retry/delete.
4. **Gate24:** `linux_cpu_gate24_driver01.py`, runID `20261108-linux-native-24`, exclusive stage `linux-cpu-validation-gate-20261108-03`. Mandatory actual new-materialization SHA, delta-result SHA và accepted loader receipt path/SHA. Native `refresh_gate2.py` toàn suite, expected771PASS/0fail/error/skip, native600s/outer630s/MCP660s. Không deselect/skip, không rerun runtime.

Base ZIP SHA `b6707cfd0139898a22dd04db9095d01622c1df9b7061f05f8579ecb4ab30d233` và base materialization SHA `debb7590e8fd1247bcbdf7a479c2ea204b7d8625414c989b0a4bab5c1e831c3b` giữ nguyên. New receipt dùng **base_archive_sha256 + delta provenance + new161manifest**, `base_archive_contains_delta=false`, `new_archive_created=false`; không gán bytes mới cho ZIP cũ. Gate23 FAILED result/output-manifest pins c7cf0a…/4edfac… được kiểm trước/sau, không relabel thành PASS.

## Runtime tái dùng đúng identity cũ

Native runtime report02 SHA `31974cac738a28ae6db6b609f75d596b43e993f2e51a2d5c946ed8ed65675cd6`, phase receipt SHA `874336b8923c67edb44f638adc740b7928c152683006bb62c0300c3e56a1fc81`, accepted **prior driver105a2388…**. New Gate driver không đòi prior receipt mang SHA của chính driver mới. Reuse chỉ hợp lệ vì lineage chứng minh duy nhất test fixture đổi, check_runtime/production/native3GitLF và44profile/lock60dad… không đổi; loader source mới cũng được pin riêng. Không có runtime command trong Gate24 driver.

Cleanup/Git/env guards được giữ như reviewed driver02: own process group một lần, cleanup error chặn PASS, CPU-hidden và OMP/MKL/OpenBLAS2, Git transports/config/auth isolation, cooperative20GiB/min30GiB free. Full software suite có optimizer fixtures sẵn có: **không claim0optimizer của actual Gate**. Prep/mock stage ở đây mới0execution/model.

## Cách chuẩn bị Delta request sau parent review

Tại repository root, PowerShell; đây chỉ là command mẫu, chưa được chạy trong nhánh này:

```powershell
$work = 'artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01'
$proof = Get-Content -LiteralPath "$work/source-delta-gate24-offline-tests02/run.json" -Raw | ConvertFrom-Json
$loader = "$work/received-loader-evidence02-transfer03/upstream-loader-transfer03/result.json"
$loaderHash = (Get-FileHash -LiteralPath $loader -Algorithm SHA256).Hash.ToLowerInvariant()
.\.venv\Scripts\python.exe -B "$work/prepare_source_delta_gate24_request01.py" --operation delta --expected-source-sha256 $proof.source_sha256_before_after.'apply_source_delta01.py' --loader-remediation-receipt $loader --loader-remediation-relative-path 'upstream-loader-transfer03/result.json' --expected-loader-remediation-sha256 $loaderHash --approval-reference 'USER_REVIEWED_CPU_SOURCE_DELTA_ONLY_AFTER_LOADER04'
```

Producer tạo exclusive `artifacts/akt/colab/requests/gpu09-add-source-delta01.json` và `source-delta01-request-contract.json`; **không dispatch**. Kiểm current source hashes với proof trước dùng. Gate request dùng cùng producer `--operation gate24`, expected source lấy key `linux_cpu_gate24_driver01.py`, thêm `--materialization-receipt`, `--expected-materialization-sha256`, `--delta-result-receipt`, `--expected-delta-result-sha256` từ actual received bytes. Producer fail-closed nếu thiếu/mismatch; không có placeholder receipts hoặc request được chuẩn bị trước actual delta.

Gate output request `gpu09-add-linux-gate24-01.json`, contract `linux-gate24-request01-contract.json`. Parent kiểm bridge remaining>=660s trước dispatch riêng. Chưa có Gate24 actual acceptance, worker/trainer/GPU/realdata/Modal từ những tệp offline này.
