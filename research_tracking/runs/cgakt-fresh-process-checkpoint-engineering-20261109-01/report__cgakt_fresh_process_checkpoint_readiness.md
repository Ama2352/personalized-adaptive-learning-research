# CG-AKT: training state qua process mới — nghiệm thu CPU09/11/2026

GRAPH19 đã xác nhận producer và consumer là **hai OS processes khác nhau**. Sau
khi producer hoàn tất E1, lưu checkpoint và chạy tiếp đủ E2, consumer mới được
khởi chạy, restore E1 rồi chạy lại **toàn bộ E2**. Full model/Adam state, RNG,
module modes, sample order, numerical batch inputs và readout khớp exact.
Đây là nghiệm thu fresh-process training-state/epoch-boundary sample parity trên
fixture CPU, không phải lifecycle/main training hoặc fitted research baseline.

## Thiết kế và kết quả thực tế

Dữ liệu handmade giữ nguyên helper5793/test332 và production checkpoint f40.
Chỉ8learner, mỗi người6events; full epoch có8windows/48targets và2batches4×6.
E1 dùng declared sampler seed43; E2 dùng44 trên **cùng full factory8windows** ở
cả hai processes. Không seed search, không corpus/teacher/oracle/Junyi/Holdout.

| Vai trò | Training thực hiện | Forward | Adam bodies | Save/load |
|---|---|---:|---:|---:|
|Producer|E1đủ2batches + E2đủ2batches; readout1lần|5|4|1/0|
|Consumer mới|Restore E1, E2đủ2batches; readout1lần|3|2|0/1|
|Tổng physical|2model/2Adam constructors;6backward/6clip|8|6|1/1|

Tổng144training target exposures, không144learner hoặc144target độc lập: population
là48targets được dùng ở E1producer, E2producer và E2consumer. Hai readouts mỗi
lần24targets là kiểm parity, không thêm optimizer update. Tracker cumulative ở
cả hai bên cùng4 vì consumer kế thừa E1history2; không cộng4+4 thành8updates.

Producer actualPID25260/creationFILETIME`134386548214640266`; consumer actualPID46564/
`134386548447362484`. Đây là actual Python worker tokens từ Windows kernel,
không venv shimPID. Producer terminal0, Job0 và handle đóng trước khi consumer
được tạo; hai Jobs đều cleanup accepted. Parent không import Torch/NumPy/domain.

Parent stream-hash checkpoint26,705,057bytes cùng metadata/COMPLETE và producer
result trước consumerGO. Handoff có externalSHA, source/profile/phase bindings
và cleanup receipt. Consumer tái tạo typed case, inspect trước model constructor,
restore vào fresh adapter/owned Adam; không cache model hoặc copy tensors giữa
processes. Profile dùng byte21/26 thực, runtime/allocation bindings có nghĩa;
handmade provenance vẫn không phải training attestation.

Trước restore, consumer cố ý đổi Python/NumPy/Torch CPU RNG và module modes.
Ngay sau restore, cả3RNG và mọi mode khớp E1producer, rồi mới bắt đầu E2. RNG
trước/sau producer save cũng bằng nhau. E2cả hai bên đủ8/48/2, ordered-batch SHA,
target/window population SHA và actual q/qa/loss-target inputSHA từng batch khớp.
Đây là bằng chứng tránh drop/dup của **full next epoch này**, không serialized
mid-epoch iterator/cursor hoặc recovery sau hard kill.

ModelSHA cuối hai bên:
`b058b5ad5055e407261d9f3ef57690e79a6be003453251ffc2a574a407772aac`.
AdamSHA:
`b5dc73a630282bacf6edffe0f7423f0c59150fc55dc36a5edadb1e7060542995`.
Readout24probabilities float32 so bằng nguyên bit; native loss/count và input
signature cũng exact. Không dùng allclose thay exact, không đòi loss giảm hoặc
graph có hiệu ứng thuận lợi.

## Thời gian và tài nguyên

| Phần | Worker elapsed(s) | Native interval(s) | Peak RSS(bytes) | Min available RAM(bytes) |
|---|---:|---:|---:|---:|
|Producer|21.7925313|13.2959745|473,210,880|4,625,072,128|
|Consumer|18.1061938|9.8255357|410,038,272|4,623,114,240|

Whole supervisor stored43.7231702s/150; terminal observation43.7307322s giữ riêng.
Mỗi owned call≤60s gồm3s cleanup, worker53/native45, RSS1GiB/free2GiB đồng nhất
giữa explicit train_epoch budget, monitor và preflight. Không fixed-canary charge
trong lượt này. Bookkeeping/source/RNG/serialization nằm trong thời gian đo;
timing body/pre/post/state-audit giữ nguyên trong raw artifacts, có lồng nhau nên
không cộng như các phần độc lập. Không suy full-corpus/GPU throughput hoặc so
speedup với workload CP119 có6negative payloads khác lượt này.

## Điều đã đóng và phần chưa chứng minh

Fresh OS process + full-next-epoch state/sample parity đã được kiểm thực tế trong
fixture CPU; bổ sung đúng giới hạn same-process của CP119. Không thay đổi
production f40/test332, baseline upstream, architecture/hyperparameters hoặc
protocol. Source-only proposal4updates/partialE2 cũ chưa bao giờ thực thi; được
snapshot trước khi tăng acceptance thành full E2/6updates.

Chưa có selected-fit/main system-freeze/refit/calibration/EarlyStopping/global
budget lifecycle resume; không mid-epoch cursor, hard-kill, cross-platform,
actual research corpus, fitted CG-AKT hay GPU readiness/efficacy. History chỉ6events,
không kiểm runtime rollover100. Confidence trong handmade case không phải actual
Method24estimator fit/P(edge true). Independent trained A0fallback vẫn là hợp đồng
khác. Không có thí nghiệm research/p-value/learning-gain mới trong gói này.

Bundle giữ raw hai child/owned/supervisor, handoff, nguồn đã chạy, lịch sử source
chưa chạy và metadata/COMPLETE. Một binary giữ nguyên trong experiments, chỉ
reference SHA/size và kiểm byte trước/sau copy. CP119 được tham chiếu bằng manifest,
không nhân đôi bundle/historical checkpoint references.

Nguồn sau đóng gói: [cross-process proof](../runs/cgakt-fresh-process-checkpoint-engineering-20261109-01/parent__cross_process_proof.json),
[handoff](../runs/cgakt-fresh-process-checkpoint-engineering-20261109-01/parent__handoff.json),
[binary reference](../runs/cgakt-fresh-process-checkpoint-engineering-20261109-01/binary_reference.json),
[CP119](../runs/cgakt-research-checkpoint-engineering-20261109-01/manifest.json).
Manifest quyết định integrity/trạng thái đóng gói; report không thay raw receipts.
