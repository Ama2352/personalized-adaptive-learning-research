# Sửa hẹp discovery02: Debian no-site sysconfig scheme

08/11/2026. Source01, profile01 và lịch sử40PASS/trial01timeout được giữ nguyên. Không dùng suite40PASS làm chứng nhận actual Linux probe đã chạy thành công.

## Failure01 thực tế và giả thuyết

Parent đã chạy CPU discovery01 và giữ verdict failed/result SHA `23bd580d91c1efd3cbd1d604760bbedd0ade519cc711f118b59b93ab2ebf1650`. `actual-cpu-discovery01-existing-logs.json` giữ exact target stderr470byte SHA `f06ff63598a0476ce9b1a371e9ad7e77f7b39684a1b6a995c9e18050c1a7864e`: `pure.iterdir()` gặp FileNotFound tại `.venv/local/lib/python3.13/dist-packages`.

Đây là chọn **default Debian posix_local scheme dưới -I -S**, không là bằng chứng installed44 packages mất/sai hoặc venv cần repair. Source01 bỏ child receipt khi target thất bại; inner cleanup ở result01 là null/unknown, không suy launcher cleanup chứng minh global cleanup.

## Source02 và kiểm focused

`discovery02.py` là bản sao source01 SHA `c176c85ad5e93c6daf229f9f7f884b277aa11c1ae99a259389059292784d0b75`; chỉ thay một dòng gộp bằng ba dòng: lấy venv path; reject nếu không có scheme `venv`; lấy `purelib` bằng `sysconfig.get_path(...,scheme='venv',vars={'base':...,'platbase':...})`. Không đổi prefix/site/origin guard, package, venv hoặc cài đặt. Không fallback scheme tự đoán. Source02 SHA **`51c4b98053ba4eaac42b8c8be51ac29645c0b5fdcdf243b19d07c760a8a9db5f`**; `source02-copy-inventory.json` có exact source01 before/after, source02 pre/postwrite SHA, bytes và unified diff. Profile vẫn exact **`0944dc50b1840c35d6085e5faa888b3d3370849e59077ea68e9a2397009b8228`** bind ABI Linux actual02; không tạo lại profile để né failure.

Các lệnh đã chạy local bằng repository `.venv`:

- `python -I -S -B .../prepare_correction02.py`: derive exclusive source02 + inventory, không chạy probe.
- `python -I -S -B .../run_scheme_checks02.py`: hai invocation stdlib AST-prefix tests, **OLD2FAIL → NEW2PASS**, tổng controller **0.6605037s≤10s**. Log/source snapshots và before/after SHA ở `scheme-checks02/`. Hai case phân biệt Debian default scheme với explicit venv và reject missing-venv scheme. Không chạy lại suite40; old ledger117.7979959s giữ nguyên, cap10s là authorization mới riêng cho focused regression.0model/optimizer/probe/install/GPU.

Kiểm này là synthetic sysconfig stub trên exact PROBE prefix, chưa là actual Linux success của source02. Parent phải review rồi dispatch once và đọc actual result. Không auto rerun nếu bridge timeout.

## Request02 đã chuẩn bị, chưa dispatch

`derive_request02.py` giữ producer01 nguyên bytes và tạo producer02; `request-producer02-copy-inventory.json` ghi delta/pins. `prepare_request02.py` AST-parse source/cell, validate profile và parse **exact generated argv bằng parser source02**, không gọi operation main. Lệnh local: `.venv\Scripts\python.exe -I -S -B .../prepare_request02.py`.

`request-add-cpu-discovery02.json`: **26.796byte**, SHA **`d33db0ccdb6ea659a06883ba5a2ba7074d46ce914b6ccd983ae29d1e21c65cb6`**. Source/profile SHA như trên, stage mới `/content/KLTN_GPU10_DISCOVERY_20261108_01/cpu-readonly02[-inputs]`; không project writes/overwrite. Cell code/file LF SHA `2e80cb7485bc2130d9b0f7496f5478c5b1638bee26bf8c56a0ea7989fb581bed`. Request01/history không sửa.

Wrapper02 thêm hash/size metadata cho target logs và inline exact text khi≤4096byte, toàn JSON reply≤48000byte; failure nguyên nhân được thấy mà không xuất huge payload. Giữ source stage/launcher cap30s, cleanup reap grace2s và pending normal-startup/site-hook/RECORD/CUDA audits. Khi accept actual warm CPU discovery, parent phải kiểm **cả inner child và launcher cleanup/RC**; wrapper chưa chứng minh global orphan cleanup khi outerkill xảy ra trước innerfinally. Không dùng cho model/GPU/paid phase.
