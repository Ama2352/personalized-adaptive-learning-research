# Collection chuẩn bị cho ROOT, chưa thực thi

Chỉ chuẩn bị `gate_collection_worker01.py`, `run_gate_collection01.py` và
`gate_collection01_packet.template.json`. Chưa chạy Python/AST/pytest/import,
chưa đo số node, chưa có Gate PASS. Không sửa production/source kit/pointer,
không Git, remote hoặc đổi nguồn đã đóng.

## Lệnh ROOT có thể review sau sourcefreeze

ROOT tạo **file packet mới** từ template, điền `root_freeze_reference`, kết quả
canonical `gate2_build_hashes()` và `test_partition(ROOT)`, SHA mọi test module,
lock Windows và bốn file upstream actual local. Giữ template nguyên; không
dùng count cũ hoặc tự suy expected count từ test PASS. Packet chưa điền bị từ chối.

```powershell
& .\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_gate_collection01.py --packet D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/gate_collection01_packet.ROOT.json --packet-sha256 <ROOT_FINAL_PACKET_SHA256> --worker-sha256 <REVIEWED_WORKER_SHA256> --approval-reference <ROOT_EXACT_REVIEW_REFERENCE>
```

Các placeholder phải thay bằng giá trị ROOT kiểm tra. Đây không là lệnh đã chạy.
Không capture final native source inventory trước khi ROOT xác nhận loader và
các nguồn khác đã freeze. Outer, worker và helper SHA cần được ROOT review/pin
trước invocation. `--help` cũng chưa được agent chạy.

## Phạm vi và admission

- Một ngân sách **60s toàn invocation**, bắt đầu trước setup. Ba fresh Jobs
  theo canonical `stdlib`, `no-torch`, `remaining`, không retry. Mỗi lần phân
  bổ lấy thời gian còn của cùng đồng hồ; giữ 3s posthash và 3s owned cleanup.
  Worker timer hết trước active deadline của helper; mọi late receipt bị reject.
- Giữ **4GiB admission**, **1GiB available floor**, **3GiB mỗi owned process**.
  Worker poll0.1s cây shim/worker đã xác minh PID+ctime; Job chịu trách nhiệm
  cleanup, không kill PID ngoài scope. RAM là quan sát cooperative, không hard quota.
- Reuse `windows_owned_worker.py` nguyên byte, GO trước domain/native import.
  Không sửa guard của pure fixture cũ hoặc guard BEFORE GO.
- Sau GO, stdlib-group từ chối NumPy/Pandas/Torch/sklearn/scipy/DuckDB;
  no-torch-group cho NumPy/Pandas nhưng từ chối Torch; remaining cho CPU Torch
  và sklearn.metrics. Không solver.fit, NN constructors, backward, optimizer
  step, teacher collection, data parsers, test bodies hoặc runtest protocol.
  Guard Python profile dừng process trước body bị cấm; outer kiểm Job cleanup.
- Native Windows metadata chỉ tối đa3 lệnh literal system `cmd /c "ver"`
  trước khi đóng metadata phase. Không fake OS, subprocess phụ hoặc network.
- CUDA/NVIDIA hidden, thread2 do helper; pytest plugins auto-load bị tắt,
  addopts rỗng, không `-k`/deselect. Collection imports **có thực thi module tops**.

## Nội dung phải review trước ROOT dispatch

Worker gọi canonical partition/hash functions nhưng không `refresh()`/`main()`
và không Git. Outer có membership mirror để bắt file nguồn thêm/xóa; mỗi child
vẫn đối chiếu canonical function trước/sau. Các simulator CSV trong native
hash population chỉ được opaque stream-hash; parser/data/actual corpus bị chặn.
`tests/shared_kt/test_rq1_cross_ready.py` và `test_rq1_transitions.py` có
`exec_module` top-level để load analysis definitions, không gọi analysis main.
`test_graph_lifecycle.py` import bare `test_graph_training`; collection giữ đúng
canonical ordering/prepend mode, không namespace giả để làm import xanh.

Worker lưu AST potential-import-call inventory trước pytest, actual imported
repository source SHA bổ sung và origin/version CPU Torch nếu có. AST inventory
không là chứng cứ syscall, runtime site-package bytes hay toàn bộ native side
effects; cached bytecode không được chứng nhận bởi SHA source này. Chính guard
cũng chưa được thực thi hoặc kiểm thử ở đợt chuẩn bị này.

## Điều kiện nhận và outputs

`gate-collection01/<group>/`: log collection, inventory, `result.json` hoặc
failure markers. `gate-collection01-outer/<group>-owned/`: exact command/owner/
GO/cleanup/stdout/stderr/receipt. `before.json`, `final.json` chứa input hashes,
union node IDs, group counts, observed resources và supplemental imports.
Chỉ nhận khi đủ3group RC0, không skipped/error/foreign/duplicate/empty modules,
không forbidden counters, source/lock/upstream/packet byte và membership nguyên,
Job0/Popen handle đóng, environment restored và posthash vẫn trong60s.

Kết quả nhận là `ACCEPTED_COLLECTION_ONLY_NOT_GATE_PASS`, **không** fullGate.
ROOT dùng inventory này chốt một recipe fullGate riêng với count độc lập đã
review; không tự cập nhật old836/124 hay pointer. Nếu60s không đủ, giữ raw partial
và rejection, không chạy lại bằng cap mới khi chưa được ROOT review.

Diễn giải trước đây về “local import denial” đã được rút lại: không có actual
auto-review rejection nào được tìm thấy cho collection local. Old pure-controller
Popen guard chỉ thuộc process fixture của nó. Rejection source-export Colab lịch
sử vẫn giữ nguyên; không có remote/upload trong preparation này.
