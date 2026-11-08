# Windows owned Job launcher: actual pure-process proof

08/11/2026. Đã thêm helper [windows_owned_worker.py](../../scripts/research/windows_owned_worker.py) cho history/reader/corpus worker được root review riêng. **Chỉ chạy tiến trình tổng hợp ngủ/ghi metadata**,0native Paper2/collector/model/Torch/GPU/remote. Không sửa science worker/outer/reader của agent khác. Đây là nghiệm thu process ownership/cleanup local, không research result, CUDA hoặc complete training readiness.

## Gap đã xử lý và API

Probe trước ghi nhận `.venv` redirector giữa outer và actual Python: `Popen.pid` khác actual worker PID. Timeout/reap chỉ Popen handle không đủ để tự suy descendant cleanup. [Bundle failure/probe trước](../runs/rq1-history-availability-20261108-01/manifest.json), manifest SHA `e34307cbf499b8639412cb4c0375e36d8a6f996ad46aa6d075e5c6d8dc24ac77`, commit root đã kiểm `d7d7ec8`, giữ cả native-attempt01 **FAILED_PRE_NATIVE** và probe **UNKNOWN/rejected**. Không copy lại bundle đó hoặc đổi outcome thành PASS.

`run_owned(worker_path, worker_args, attempt_dir, *, expected_worker_sha256, approval_reference, max_seconds, cleanup_reserve_seconds, max_output_bytes)` dùng đúng repository `.venv/Scripts/python.exe`, không trực tiếp launch base Python. Caller phải truyền cap và approval reference/source pin; helper không cấp research authorization. Không retry hoặc ghi đè attempt cũ. Worker owner gọi **`worker_gate()` trước knowledge_tracing/NumPy/pandas/Torch**; launch metadata qua hai env names `KLTN_WINDOWS_LAUNCH_MANIFEST` và `KLTN_WINDOWS_LAUNCH_NONCE`, không thay CLI khoa học.

Parent bắt đầu monotonic/wall timing trước setup, ghi nonce/source/argv/parent token vào manifest; worker ghi READY rồi đợi GO. Parent dùng owned process handles, `GetProcessTimes` exact FILETIME và `QueryFullProcessImageNameW` full image path, kiểm PID/create-time/topology/entry/prefix/source/command trước đăng ký lease. Handle provisional sai identity/ancestry chỉ được close, **không** terminate; ready PID phải nằm trong cây đã xác minh, không mở arbitrary ready PID chỉ vì có image Python.

Job kill-on-close dựa trên existing Gate25 Job code, nhưng **assign cả actual waiting worker và root shim**, kiểm `IsProcessInJob` trước GO; worker cũng query exact named Job trước khi trả gate receipt. Không suy already-created child thuộc Job chỉ vì parent đã assign shim. Cleanup luôn terminate owned Job ngay cả shimRC0, reap Popen, query Jobactive0, close extra handles và borrowed Popen handle; lỗi/unknown không được accepted. Chỉ scoped owned handles, không taskkill/name-wide hoặc user apps.

DETACHED_PROCESS với stdio redirected được chọn vì không cần console tương tác. **Actual vẫn có conhost**, nên không gọi flag đó là bằng chứng không tạo console host. Receipt normal/descendant/timeout đều ghi owned conhost token được adopt; cleanup Job đảm bảo empty trong các ca đã đo.

## Một lượt actual synthetic, không rerun

Root review exact sources rồi trực tiếp chạy controller một lần:

```powershell
.venv\Scripts\python.exe -B artifacts/akt/local-tests/windows-owned-launcher-20261108-01/run_tests.py
```

**6test methods PASS,0fail/error/skip**, unittest1,849s; controller **2,145356699998956s≤20s cumulative**; tool terminal wall2,6589773s là timing riêng parent ghi, không thay controller timing. Ba source SHA trước=sau. Suite dùng unittest trong actual `.venv` process với timer của chính process, không nested testlauncher hoặc cài thư viện. Timer/cooperative checks không là hard OS quota attestation.

| Actual process mode | Outcome helper | Cleanup proof | Helper elapsed |
|---|---|---|---:|
| Normal |accepted launch; shimRC0 |actualworker inJob trước GO; Jobactive1 trước cleanup→0, handlesclosed |0,4124937057s/5s |
| Sleeping descendant rồi rootRC0 |accepted launch; shimRC0 |worker báo descendant in exactJob; Jobactive4 trước cleanup→0, handlesclosed |0,3730299473s/5s |
| Post-GO timeout |**rejected như thiết kế**, returncode1 |GO đã release, actualworker inJob; timeout giữ1s cleanup reserve; Jobactive0, handlesclosed, không body result |1,0166609287s/2s |

Normal actual Popen shim8484 (`D:\Dev\KLTN\.venv\Scripts\python.exe`) và worker44584 (base imageC:) khác PID nhưng worker entry/prefix vẫn `.venv`. WinAPI trả full image paths; không dùng drive-less PSutil `.exe` để suy full image. Descendant shim25428/worker28816 đã nhận GO trước spawn pure sleeping child45676; child được xác minh inJob. Các PID chỉ mô tả run này, không dùng lại để kill sau archive.

Năm pure methods kiểm ready nonce/schema/source/argv/entry/token/preGO imports, unknown/recycled provisional handle close-only, changed ancestry không becomeowned, lexical `..`/outside/root alias, source drift trước bất kỳ Kernel/Popen. Test source-negative dùng cap120 nhưng không launch process, chỉ xác minh API không chặn caller cap120. Không fake một actual120s hoặc600s run. Actual process method tuần tự dừng ngay nếu normal Job setup fail; không retry platform restriction.

Source helper SHA `0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1`; tests `57cda05a6d990d5b90a8b2f4ad06a2a506ec6028d8d9c70e2b81a7c8aa4c501f`; controller `0e4fa1c4dafceee20903ed03e41441225a66252bc416ef1486b4d25136546ae0`. Full raw actual manifests/READY/GO/body/stdout/stderr và receipts giữ trong [bundle helper](../runs/windows-owned-worker-engineering-20261108-01/manifest.json), kèm copy inventory SHA trước/sau. Timeout rejected và các negative controls được giữ, không biến chúng thành accepted worker execution.

## Phạm vi còn phải giữ

Generic API cho caller≤600s, startup gate≤10s; **chỉ các synthetic calls ngắn ở trên được kiểm thực tế**. Không tự launch120/600 hoặc mở cap khoa học. Caller vẫn phải kiểm final total sau khi persist/đọc outputs, nguồn/plan/case ledgers/semantic acceptance, runtime/Gate/resource/authorization và budget riêng trước native/model. Existing history cumulative60 vẫn giữ lịch sử0,845393699943088s trước integration mới; allowance20 ở đây là engineering batch được root cấp riêng, không reset scientific counter hay native60 cap.

Job proof này không là chữ ký/capability chống caller cùng workspace giả metadata; worker source phải review và gọi gate đúng phase. Không attestation toàn syscall hoặc ảnh runtime khác, không portability guarantee trên Windows Job restrictions khác. Root phải review integration mới của science worker/reader trước native retry; module này không sửa old source, old attempts hoặc claim RQ hoàn tất. Root giữ Git/shared tracking; tiểu tác vụ không tự commit/push hoặc gửi ra ngoài.
