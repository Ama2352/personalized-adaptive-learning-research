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
