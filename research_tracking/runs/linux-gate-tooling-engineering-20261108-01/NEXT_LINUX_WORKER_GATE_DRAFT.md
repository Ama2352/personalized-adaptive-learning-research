# Draft handoff Linux worker/Gate2 — 08/11/2026

Chỉ điều tra nguồn; không remote/install/model/GPU/test execution trong lượt đọc. Dòng tham chiếu dưới đây là source **trước batch tooling**. Install attempt01 dừng preflight trước pip-install theo handoff; sửa installer không tự là install PASS. Phải đọc receipt cài đặt thực tế trước bước worker. Parent sau đó cho phép batch tooling local nhỏ; chưa cấp quyền full Linux Gate hoặc GPU09 từ draft này.

## Kết luận cần dùng

**Không dùng lại Gate21 Windows cho Linux lock mới.** Windows lock SHA`3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a` khác candidate Linux SHA`60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a`. `context.py:174–178` truyền cùng `context.lock_file` cho runtime và Gate2; `authorization.py:163` so exact hash. Kit còn strip notebook bytes (`build_colab_bundle.py:30–44`), trong khi Gate2 hash notebook thực tế (`authorization.py:96–113`): source21 của Windows cũng không được gán lại cho copy đã transform.

Reader hiện không chứng thực OS của Gate2 riêng; vì vậy syntactic acceptance không tự là actual Linux execution. Không sửa report cũ/rehash thành lock khác, khai lock Windows cho runtime Linux để qua guard, mock validator hoặc dùng subset rồi gọi full Gate. Cần **actual CPU software Gate trên Linux isolated profile và exact frozen kit**, cùng source/lock mới.

## Call sites và hai blocker nhỏ

| Vị trí trước tooling | Hiện trạng/ý nghĩa |
|---|---|
| `scripts/akt/build_colab_bundle.py:13–26,30–44,60–69` | Kit gồm source/tests/config và Windows hashlock fixture; không gồm installed venv, Linux lock, runtime/Gate/context hoặc upstream Git checkout. Linux lock/installed receipts và pinned upstream phải được materialize/verify riêng. Không cài Windows wheels lên Linux. |
| `scripts/akt/refresh_gate2.py:41,61,76,121,128–134` | Producer chỉ dùng root `requirements-akt.lock.txt`, chưa có lock argument; final reader cũng dùng default. Đây là blocker explicit Linux lock, không cần thay reader contract. |
| `scripts/akt/check_runtime.py:42–44`; `tests/akt/test_runtime.py:40,60` | Dùng `pip._vendor.packaging`; isolated target cố ý `--without-pip`, và44packages không có pip. Full Gate sẽ thiếu dependency tooling dù install44 thành công. Standalone `packaging` đã được pin trong44, nên ưu tiên dùng public API của package này. Không thêm base site-packages vào target hoặc tự cài pip global. |
| `check_runtime.py:94–140,143–160` | CLI đã có `--lock-file`, schema2 bind executable/prefix/platform/source/lock/device và origins Torch/NumPy. `inspect_runtime` **chỉ hash lock, không parse== hoặc đối chiếu toàn44installed versions**. Windows hashlock thực tế cũng `name @ URL --hash=...`, cùng grammar Linux; không có format incompatibility cần manifest thứ hai. |
| `context.py:76–124,169–184`; `prepare_synthetic_context.py:103–118,187–215,224–242` | Context nhận lock riêng dưới `artifacts/akt` hoặc root `requirements-akt*.txt`; runtime/Gate pointer dưới preflight. Builder dummy chỉ kiểm path/input, không chứng nhận contents runtime/Gate hoặc tạo authorization. |
| `watchdog.py:109–147,179–185`; `runner.py:318–336` | Public CLI `python -m knowledge_tracing.akt.cli`; context SHA đi từ parent sang child; cả hai kiểm authorization/context identity, rồi worker kiểm Gate. Không gọi `_execute` trực tiếp hoặc bỏ context để né prerequisites. |

## Thay đổi tooling tối thiểu được đề xuất

1. Chỉ đổi `pip._vendor.packaging` sang `packaging` trong runtime helper và hai fixture imports. Giữ cùng parsing/ABI/hash checks. Alternative thêm pinned pip vào target sẽ đổi closure/install budget, nên không ưu tiên.
2. `refresh(..., lock_file=None)` và CLI `--lock-file`: default Windows path giữ nguyên. Lock chọn explicit phải là file hiện hữu, root-bound trong allowlist AKT; từ chối outside/protected/private/missing. Dùng cùng selected path/SHA ở before/after, payload provenance và final `require_gate2_evidence(..., lock_file=selected)`. Giữ schema1, source/upstream checks, zero fail/error/skip, strict elapsed1..600/default300 và threadenv2.
3. Không cần sửa config dataclass/model/hyper/split/context để xử lý việc này. Không thay Windows lock hoặc bundle lịch sử. Source tooling/tests đổi thì Gate21 thành historical; freeze, targeted tests có receipts, tạo kit mới rồi actual Linux Gate riêng. Không monkeypatch production globals hoặc dựng report PASS từ test chưa chạy.

## Dependency order nhỏ nhất, chưa thực thi

1. **Install/profile proof:** nhận đủ success/failure receipts; isolated `.venv` nằm ngay trong ROOT của kit. Cài44URL/hash theo allocation riêng; `pip check`, exact versions và origins phải có bằng chứng. Runtime JSON hash lock không thay kiểm44installed distributions. Root không đổi sau khi tạo reports/context. Giữ original Windows lock như fixture.
2. **Freeze source/kit:** hoàn tất tooling local, source/ZIP inventory; extract exact kit vào ROOT đã có venv. Materialize candidate Linux lock byte-exact riêng và pinned clean upstream Git/source. Không mang dataset/realdata/Holdout. Không sửa notebooks sau khi hash. Kit hiện không phải installed-runtime image.
3. **Actual Linux CPU runtime:** dùng `.venv/bin/python scripts/akt/check_runtime.py --device cpu --lock-file <Linux lock> --upstream <pinned source> --output <new preflight JSON>`. Schema2 phải có platform Linux, exact prefix/executable, source/lock/origins; không kế thừa system packages. Đây là bước tương lai cần success receipt, không lệnh đã chạy.
4. **Actual Linux full Gate2:** fresh subprocess, CUDA hidden và OMP/MKL/OpenBLAS2; suite chính xác `tests/akt tests/shared_kt`. Không chạy `tests/gam_kt` (test thực frozen assignments nằm ở đó), không tái dùng hai `-k` exclusions của notebook cũ. `test_native_akt_import_cpu` chỉ đòi device CPU/nonempty torch version và origins, không đòi build `+cpu`; CUDA wheel có thể được kiểm trên CPU với devices ẩn. Counts thật/JUnit/log/source/selected-lock pre/post và elapsed guard phải đạt. Windows757 là historical count, không ép count của source mới. Ngân sách phải được chốt trước trong1..600; runtime Colab chưa đo nên có rủi ro vượt cap, không auto retry hoặc nới max.
5. **CPU public worker trước:** tạo dummy context mới với runtime CPU, selected Linux lock và actual Linux Gate pointer; bind config/contextSHA/inputSHA/caps vào authorization. Public watchdog smoke bounded2steps theo existing builder contract; kiểm checkpoint/reload/export/recovery theo stage được cấp phép. Không thay default data bằng Junyi/BKT artifacts.
6. **GPU09 riêng:** fresh CUDA runtime schema2 trên hardware được cho phép, đúng isolated profile/source/lock; context `cuda-smoke` có allocator limits và authorization riêng. CPU runtime report không cấp CUDA và kitv12 proof không thay new worker. Nếu đổi runtime/install/source/lock phải kiểm lại provenance/Gate suitability, không copy PASS labels. GPU lifecycle/VRAM/recovery có allocation và receipts riêng; không Modal/full research từ draft này.

Đã đọc các source/table trên cùng `config.py`, `provenance.py`, `tests/akt/test_colab_bundle.py`, `tests/shared_kt/test_evidence.py`, contract20 và actual lock headers. Không đọc raw learner/Test hoặc thực thi source được điều tra. Các options ở đây là engineering dependency map, không lựa chọn S04/S05 hay research hyperparameters.

## Addendum sau tooling local freeze — chưa chạy các lệnh Linux sau

Batch local đã kiểm118targeted PASS; nguồn mới bỏ phụ thuộc target pip và thêm explicit lock, không thay default Windows. Gate21 chỉ còn historical source. **Path remote hiện tại `resolution-attempt01/candidate-linux-cuda.lock.txt` không nằm trong allowlist lock của CLI mới.** Trước full kit/Gate, cần copy byte-exact có inventory SHA trước/sau từ path đó sang, ví dụ, `artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt` trong cùng ROOT; cả hai phải khớp `60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a`. Giữ source cũ, tạo destination độc quyền, không overwrite/rename âm thầm; canonical copy chưa được thực hiện bởi draft này.

Sau khi copy và allocation riêng được xác nhận, entrypoints dự kiến:

```bash
# Chỉ là mẫu tương lai; ROOT, source, lock copy và installed profile phải đã verified.
# Hai biến sau phải do stage owner khai báo explicit, không auto tăng/retry cap.
.venv/bin/python scripts/akt/check_runtime.py --device cpu \
  --upstream artifacts/akt/dependencies/upstream \
  --lock-file artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt \
  --output artifacts/akt/preflight/runtime-linux-cpu-fresh.json
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
  .venv/bin/python scripts/akt/refresh_gate2.py --run-id "$FRESH_GATE_RUN_ID" \
  --lock-file artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt \
  --timeout-seconds "$APPROVED_GATE_SECONDS" --publish-current
```

`FRESH_GATE_RUN_ID` phải mới, `APPROVED_GATE_SECONDS` nằm1..600; không gán approval bằng việc hiện diện trong mẫu. Actual Linux Gate và worker vẫn chưa được chạy ở batch tooling local này.
