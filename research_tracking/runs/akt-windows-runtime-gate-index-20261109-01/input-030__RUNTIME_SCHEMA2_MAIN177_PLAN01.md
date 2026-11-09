# Chuẩn bị kiểm runtime schema2 CPU bằng native CLI

Thực thi chờ ROOT sau khi Gate05 terminal và admission RAM mới. Source plan này dùng public `scripts/akt/check_runtime.py::main/inspect_runtime`, không thay nội dung legacy `runtime-v2.json`.

Lệnh native cần chạy trong repository .venv, output absolute và chưa tồn tại

```powershell
& D:/Dev/KLTN/.venv/Scripts/python.exe -B D:/Dev/KLTN/scripts/akt/check_runtime.py --upstream D:/Dev/KLTN/artifacts/akt/dependencies/upstream --device cpu --lock-file D:/Dev/KLTN/requirements-akt.lock.txt --output D:/Dev/KLTN/artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json
```

ROOT có thể dùng worker mỏng để chạy CLI này qua `runpy.run_path` với nguyên argv trên sau `worker_gate()`. Helper0dc giữ actual worker và toàn process tree trong owned Job trước GO. Việc gọi native CLI cần preserved environment, source và defaultdevice semantics. Allocation đề xuất60whole/57owned gồm cleanup3/54worker, RSS≤1GiB và available≥2GiB được quan sát trước Torch và trong lượt. Đây là hypothesis tài nguyên cho một runtime check, cần đọc actual receipt sau chạy. Nếu setup/ownership/source/resource/time sai thì dừng và giữ failure/output đã sinh.

## Workload và guards

Native `inspect_runtime` dòng97–132 kiểm interpreter/prefix, gọi original `verify_upstream`, import NumPy/psutil/Torch thật, kiểm origins trong cùng .venv, rồi exec module upstream để xác nhận class AKT tồn tại và đặt module.device=CPU. Nó không gọi constructor AKT hoặc optimizer. Source runtime return ghi schema2, platform/prefix/root/lock, versions/origins, RAM/disk và actual CUDA availability.

Guard đề xuất đo model constructor/forward/backward/optimizer/solver/teacher đều0. Cho phép imports runtime thực và source module upstream. CPU framework metadata tensors khi import cần scope riêng với các operation model. Chặn CUDA init/_lazy_init/tensor.cuda/module.cuda, không sửa giá trị availability. Source CPU branch có hai callsites `cuda.is_available`, gồm upstream module device selection và cuối runtime report. Ghi actual calls/path/values và yêu cầu false, `torch.version.cuda is None`, `cuda.is_initialized() is False`. Nếu imports phát sinh callsite khác thì lưu observed scope để ROOT review.

Giữ exact process Git profile đã review cho MainGitProfile. Original `verify_upstream` thực hiện10read-only commands và đọc3upstream files, không fetch. Windows audit có raw executable null hoặc literal `git`, commandline phải đúng list2cmdline và thứ tự source. Real Windows platform metadata có thể gọi literal System32/cmd.exe `/c "ver"`, tối đa3lần trong phase metadata đã review. Guard vẫn chặn mọi child khác và network. Parent/helper cleanup và PID/Filetime/Job0 acceptance đi cùng native runtime result.

TEMP/TMP/TMPDIR trỏ owned runtime-temp trong lượt, cache tempfile được lưu/khôi phục. stdout/stderr và JSON report giữ nguyên bytes. Không cần pytest nên không có pytestlogging/basetemp. Các vùng dataset/BKT artifacts/actual corpus/experiments/Holdout được audit chặn. Source CSV/notebook chỉ có thể cần opaque hash nếu kiểm current Gate build thêm, không parse dữ liệu tại runtime check này.

## Source và evidence pins cần ROOT khóa trước lệnh

| File | SHA256 |
|---|---|
|`scripts/akt/check_runtime.py`|`4f5be1c58db40cd8875865275bb50f0b8171dc781615d4ce9f862ca598c1f795`|
|`src/knowledge_tracing/akt/authorization.py`|`bd6be914e3b5049927ba6358ee4872097a46469fede9ad1b71ee63df951ac7f0`|
|`src/knowledge_tracing/akt/config.py`|`beb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f`|
|`src/knowledge_tracing/akt/provenance.py`|`493d82af749baefcacec9ece0a7abe3297e64398eb4cd93c1d639ca41752cb59`|
|`scripts/research/windows_owned_worker.py`|`0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1`|
|`requirements-akt.lock.txt`|`3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a`|
|Actual Win03 verify proof|`cac0e916a29f81f8f716aad5d9df05ea5c9e13c591f000fee0a130d02a499361`|
|Installed EOL policy proof|`a0307845fbd04ff1b7e52dea821ed9159462005876c4facfdd18be62c40ca6fd`|

Upstream commit01b7e8d7d7c862cabc9467108e3e7f2555653a88 và tree904863502337ef2eefd1769d14836b62e3c3804a phải qua original verification. Rawfiles giữ actual akt.py be2788c20cac602e86ef3a51e5294b37dd7b200f818be4e173dbd69069a3ec6d, README df8eea9919dcdb343f3a841540af18e2039b8b0c33af449ca9c752d11f56ee8b, LICENSE891133edce0d8693f5b916d4257ce70b71a02aa110cb02cc5d47326544ea4522.

Sau runtime check, ROOT xác minh raw report schema2/prefix/root/lock/device/origins, genuine source equality, exact before/after source/legacy/currentpointer bytes, ownership/resources/time, rồi cung cấp path/SHA thật cho publisher0365. `require_gate2_evidence` không yêu cầu runtimeSHA bằng legacy259c của Gate05. Public preflight xác nhận schema2 mới dùng cùng source/lock/venv. Giữ hai runtime identities riêng trong receipts để truy vết.
