# Chuẩn bị A2/A3 Junyi và tách CPU trước GPU

## Đã đạt

Bộ kiểm tests06 có 299 ca đạt. Đã nối confidence TRAIN80 vào A2/A3 expert, giữ đủ cạnh và null/reason cho cạnh unsupported (trọng số vận hành 0). A2 dùng confidence, A3 thêm gate đã có ở ResearchGraphNative. Đường graph-off và zero-confidence về backbone đã kiểm bằng model CPU thật. Producer dùng cùng state machine checkpoint/early stopping/reload/export và hợp đồng A0. Chưa fit confidence Junyi thật hoặc training A2/A3.

Đã thêm handoff CPU cho train cache. Script `scripts/akt/prepare_junyi_cpu_admission.py` duyệt strict toàn232.662window/13.347.331target trong347,65giây, không GPU. Receipt tại `artifacts/akt/window-cache/full-train80-cpu-admission-20261113-01.json`, SHA trong full-cpu-admission01.log. Session nhận lại kiểm key, source validator chuẩn LF, manifest và SHA/bytes từng shard, mất3,82giây trênWindows; đối chiếu5window input/target/mask khớp. Receipt chỉ tái dùng kiểm geometry trên đúng byte nguồn, không cấp quyền training. Guard và SHA mỗi epoch vẫn giữ. Kiểm Linux/CUDA của nguồn mới còn chờ.

## Cấu hình so sánh

A2/A3-preparation.json giữ nguyên các trường học từ A1, cùng data pins A0/A1, batch128, seed42, optimizer, FP32, min_delta0,0001/patience3/max20. Đây là template chuẩn bị, chưa là grant thực thi. Mỗi variant phải khởi tạo backbone cùng seed, chia sẻ artifact confidence TRAIN80. Checkpoint A0/A1 đã học không dùng khởi tạo A2/A3. A0 chọn epoch bằng validation batch1, chỉ epoch9 đã replay batch128; giới hạn ranking toàn12epoch tiếp tục giữ.

## Diễn tiến kiểm

- tests01 có4ca mới sai phase fixture; sửa fixture rồi tests02 đạt67ca.
- tests03 có lỗi thiếu import trong test handoff và hardlink bị Windows hạn chế; tests04 còn riêng hardlink. tests05 chạy đúng quyền file trênD đạt ca đó. tests06 cùng toàn bộ nhóm đạt299ca.
- Các ca synthetic có mock admission CUDA rõ phạm vi. Model/gradient/Adam CPU dùng code thật; tests state machine dùng TinyAdapter như suite trước. Không suy CUDA readiness từ các ca này.

## Còn tiếp tục

Compact A2/A3 cần tính weighted message và gate theo batch, đối chiếu reference để tránh lặp bottleneck A1 cũ. Compact A1 và cache A1 hiện từ chối A2/A3 rõ ràng. Full confidence CPU cần spool/resume/fit và provenance theo native-window recipe đã có. Orchestration Modal cần CPU prepare → GPU train/validate/checkpoint → CPU đóng gói, có stop acknowledgment trước postprocess. Đợt này chưa dùng credit mới, chưa sửa historical checkpoint/source bundle đã đóng.


## Gói compact tiếp nối

Sau commit23bd552 đã bổ sung CompactConfidenceContext cho A2/A3. Weighted message và bốn gate features dựng CPU từ đúng prefix, chuyển GPU theo mảng; gate và residual thực hiện theo batch. Đường tham chiếu được giữ để đối chiếu. Compact A1 giữ định dạng và phép tính riêng. Disk graph cache A1 tiếp tục từ chối A2/A3 để tránh đọc nhầm format.

Tests07 đạt87ca ở nhóm tập trung; tests08 gộp339ca đạt, có overlap nên không cộng số ca. Probability đối chiếu reference với atol1e-7/rtol1e-6; model/gradient/Adam với atol1e-6/rtol1e-5. Bao gồm alpha0/khác0, confidence0/khác0 và gate có weight khác0. A2/A3 checkpoint/resume CPU cho cùng trạng thái với continuous, graph on/off. Có kiểm message weighted nhiều parent, gate features và current/future label không làm đổi prefix. Các ca CUDA admission được mock rõ như suite gốc; chưa là CUDA/GPU throughput proof.

Template A2/A3 đã đặt run/output riêng, execution_enabled=false; không trỏ output A1 cũ. Mọi trường học khoa học khớp A1, checkpoint khởi tạo cùng seed thay vì dùng model đã học. Hai template chưa là quyền thực thi.

## Quy trình cloud cần nối trước trả phí

1. CPU App chuẩn bị source/data, fit confidence TRAIN80, strict admission, context và manifest. Snapshot immutable/receipt ghim source và mọi byte dữ liệu. Kiểm runtime CPU, chuẩn bị image sẵn; GPU thực hiện riêng phát hiện CUDA.
2. GPU App chỉ nạp đúng snapshot, xác minh SHA, train/validation, checkpoint và predictions cần GPU. Model/Adam/RNG/sampler giữ trong cùng logical run, checkpoint có COMPLETE được đồng bộ lên Volume. Một GPU, timeout/cap/retries0, resume từ checkpoint đã kiểm. Ghi số giây từng giai đoạn.
3. Sau khi GPU trả kết quả bền vững, controller phải xác nhận App GPU đã dừng. CPU App mới đóng gói, tải và kiểm archive, tổng hợp metrics/figures/report. Kiểm mất kết nối và lỗi từng stage bằng bounded synthetic runs trước full data. Source/runtime mount phải giữ interpreter hoạt động, không che venv bằng volume data.

Hiện receipt CPU trước GPU đã nối producer/CLI và được kiểm toàn cache trênWindows. Toàn bộ orchestration Modal ba App/stop barrier chưa được triển khai. Chưa fit confidence Junyi thật. GPU timing, numerical parity và độ bền resume của source mới còn chờ. Giá hiện hành lưu pricing-and-budget.json; GPU choice phải dựa chi phí/target đo thật và dự toán cả fit/refit/calibration/evaluation trong30USD. Đợt này0USDModal.


## Chốt kiểm CPU của đợt hiện tại

Đã siết nguồn validator trước/sau full strict admission và trước ghi handoff. tests09 đạt41ca cache, gồm phát hiện source thay đổi trong/sau CPU pass; suite này có overlap với339ca tests08 nên không cộng tổng. Receipt01 giữ làm lịch sử, dùng cùng source tại commit23bd552. Source hiện tại dùng receipt02 mới, strict toàn232.662record/13.347.331target trong285,31giây CPU. Nhận lại với source/key/manifest/shard SHA khớp mất3,13giây CPU,5window prefix khớp. `full-cpu-admission02.log` và `full-handoff-verification02.json` giữ số liệu. Chưa đo trên Linux/GPU. Hai lượt có tải máy khác nhau.

STATE.json giữ bốn taskA23–A26 và acceptance cụ thể. Learned topology/điều kiện learned chưa triển khai trong nhánh này, tiếp tục nằm trong phạm vi KLTN. Gói hiện tại đã hoàn tất kiểm local; chuẩn bị Modal chưa READY vì confidence thật, staged orchestration, Gate Linux/CUDA và dự toán toàn matrix còn chờ. Không mở GPU trong đợt này. Checkpoint A0/A1, export, prediction và closed bundles giữ nguyên.


## Tiếp nối 14/11 — controller staged đã có kiểm local

A24 đã triển khai CPU local chuẩn bị/upload → function GPU → xác nhận dừng → CPU local download/nén. 71 ca local đạt, gồm lỗi và checkpoint recovery bằng Modal giả lập. Chưa kiểm cloud/CUDA thật, chưa fit confidence thật và chưa training A2/A3. [Hồ sơ tiếp nối](../junyi-local-gpu-separation-20261113-01/README.md). Kế hoạch ba CPU/GPU App ở trên được thay bằng CPU local ở hai đầu theo yêu cầu mới.
