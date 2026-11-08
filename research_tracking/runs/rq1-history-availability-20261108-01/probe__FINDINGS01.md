# Windows .venv redirector: một pure process probe

08/11/2026. Source worker `28b2b60f…` và outer `65fca33a…` giữ nguyên. Attempt khoa học01 dừng ở assert worker_parent_pid==os.getppid tại workerline44, trước imports knowledge_tracing/NumPy/pandas/native và trước model cases. Đây là failure vận hành, không kết quả native replay hoặc scientific counterexample. Không bỏ PID guard, không chạy base Python, không thử lại worker.

## Thực chạy duy nhất và phạm vi kết luận

Command `.venv\Scripts\python.exe -B artifacts/akt/local-tests/retention-metric-separation-20261108-01/windows-launch-probe01/run_probe.py`. Outer source SHA `1a2cb14774829c1a27def7f0683cdd89096f310c4678028dbfbea513e70f4492`; child source SHA `947bb6bbe14dbd5f9910378925cd4b1393ff2ca62d8fd9f3560d25a5b636495a`. Giữ launch flags của worker `sys.executable -B`; child chỉ stdlib/psutil7.2.2, không import Torch/NumPy/pandas/knowledge_tracing, không spawn tiếp hoặc gọi native/collector/model/GPU/remote.

Receipt `probe-attempt01/probe.json`, SHA `1f2508c7f89b58c005efd91393b724c5ccb70efdf7d8a147a504e011e475b504` lưu chain được đối chiếu PID/PPID/create_time/exe với process sống khi child đợi release:

| Vai trò | PID | PPID | Create time |
|---|---:|---:|---:|
| Outer Python thực |25364|4844|1794136375.019984|
| Popen .venv redirector |22140|25364|1794136375.2312033|
| Python thực chạy child |36656|22140|1794136375.269227|

Child `sys.executable=D:\Dev\KLTN\.venv\Scripts\python.exe`, `sys.prefix=D:\Dev\KLTN\.venv`; `os.getppid()==22140`, khác PID outer25364. `Popen.pid==22140` là redirector. Quan sát này hỗ trợ đúng giả thuyết một tầng trung gian khi dùng `.venv` trên Windows, trong **một** launch được đo; không suy mọi runtime đều có hình dạng này.

PSutil trả `.exe` raw dạng thiếu drive: shim `\Dev\KLTN\.venv\Scripts\python.exe`, actualPython `\Users\AmaDev\AppData\Local\Programs\Python\Python313\python.exe`. Probe lưu raw values; shim normalize theo current drive khớp lexical entry D:, hai actualPython images bằng nhau trong PSutil. Không tự gán full drive C: cho raw `.exe` của actual image; `sys._base_executable` được lưu riêng, không được thực thi.

**Overall probe UNKNOWN/rejected**, không PASS: child và Popen đều thoátRC0, error=null nhưng tracked owned `conhost.exe` PID18612/create_time1794136375.245793 còn sống ở snapshot cuối tức thời. Không kill process nào. Điều này không chứng minh conhost còn tồn tại lâu dài hoặc một native worker đã orphan. Chưa có hậu kiểm/cleanup/reprobe thứhai được chạy; không sửa receipt thành accepted.

Thời gian probe0.4560244999593124s≤10s; prior attempt01 thực0.3893691999837756s, tổng availability ledger mới **0.845393699943088s/60s**. Đây là charge bổ sung, không reset budget. Năm source/input SHA trước=sau. Stdout child≤16KiB, stderr rỗng; nguồn khoa học/plan/oldreceipt không đổi.

## Đề xuất sửa nhỏ để owner/root review trước native retry

1. Giữ guard ancestry có ý nghĩa: direct-child mode kiểm PID+create_time outer; Windows shim mode kiểm **đúng** Popen PID/create_time và `.venv` entry, shim.parent=outer PID/create_time, actual worker PID/create_time cùng prefix/entry/source/command. Không nhận arbitrary ancestor sâu tùy ý hoặc thay expected parent bằng observedparent chỉ để assert xanh. Dispatch/launch handshake mới có nonce và exact source/plan bindings; giữ old attempt/source bất biến.
2. `subprocess.run(timeout)` ở outer hiện chỉ sở hữu Popen handle của shim; không có bằng chứng nó sẽ reap Python descendant trên timeout. Không mô phỏng orphan bằng native. Reuse WindowsJob/cleanup_once trong `artifacts/akt/local-tests/graph-lifecycle-engineering-20261108-01/gate-planning/windows_gate25_outer01.py`, SHA `240d52cbd833632313b6b3d594a93e49acf43c2289acb027791baf7da2abd1d9`, thay vì thêm daemon/framework hoặc broad taskkill.
3. **Không copy nguyên trình tự assign rồi mặc định đủ:** wrapper hiện gọi Popen trước, rồi assign Popen._handle vào Job. Với redirector thực đo, Python child có thể đã xuất hiện trước bước assign shim. Source hiện không kiểm Job membership của child đó. Giữ pre-native GO barrier và xác minh/assign actual waiting worker vào đúng owned Job trước GO (handle/create_time-bound), hoặc source launch-suspended→assign→resume được review riêng. Chưa thử nghiệm race này, chưa chứng minh wrapper hiện có đảm bảo descendant containment trên runtime này.
4. Cleanup bằng owned Job ngay cả khi shim đãRC0; reap Popen handle, kiểm Job empty và observed owned tokens trong reserved cleanup time. Không broad PID/name kill, không thao tác user apps. Conhost tức thời phải được xử lý trong chính bounded cleanup verdict, không lờ đi hoặc gọi đó là persistent leak khi chưa có chứng cứ. Native retry chỉ sau root review source mới/caps/receipt và remaining cumulative budget, không chạy tự động từ probe.

Đây là evidence và proposal vận hành; source science chỉ owner sửa.0new native cases/observations/independentN,0Torch/NN/optimizer/remote/Git. Không cập nhật shared ledger/index trực tiếp: root/owner consume số thời gian và receipt đã lưu.
