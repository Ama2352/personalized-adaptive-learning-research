# Tách CPU local và function GPU cho A2/A3 Junyi

Đợt bắt đầu ngày 13/11, nghiệm thu local ngày 14/11/2026. Đây là bằng chứng kỹ thuật. Chưa training A2/A3 Junyi, chưa cấp GPU, chi Modal trong đợt bằng 0 USD.

## Đã hoàn thành

1. `scripts/akt/prepare_junyi_gpu_stage.py` kiểm CPU local trước upload. Đối chiếu model A0/A1 thật, 27 trường cấu hình học, profile FP32, roles, encoding, cửa sổ và số target. Confidence phải có nguồn fit TRAIN80 đầy đủ, cùng recipe và lịch sử native-window. Thiếu confidence hoặc Gate đúng source sẽ bị từ chối.
2. `experiments/akt/junyi_staged_io.py` giải nén, kiểm SHA và tạo snapshot tại `artifacts/akt/` trên D. Upload hoàn tất trước gọi function GPU. Upload dở chỉ bổ sung file thiếu khi byte cũ khớp. Vùng dataset gốc, venv và credentials bị chặn.
3. `experiments/akt/modal_junyi_staged.py` điều phối function GPU có hạn mức tài nguyên/thời gian, một GPU, không tự retry. Worker `scripts/akt/run_junyi_gpu_stage.py` dùng snapshot có sẵn, chạy numerical producer hiện hành. Checkpoint, Adam, RNG và predictions vẫn theo producer. Checkpoint COMPLETE được commit lên Volume v2 và lập chỉ mục phục hồi.
4. Sau xác nhận App GPU dừng, CPU local mới download, kiểm SHA/bytes và nén. Archive COMPLETE ghi cuối. Mất kết nối sau checkpoint có thể thu các checkpoint đã đóng từ chỉ mục phục hồi. Lỗi vẫn giữ logs và partial để điều tra.

Checkpoint ghi trực tiếp lên Volume v2. Tài liệu Modal xác nhận v2 hỗ trợ hard link, phù hợp cách native producer công bố checkpoint. Commit độ bền checkpoint và đọc batch vẫn nằm trong vòng đời function. Chưa có số đo runtime mới để khẳng định giảm bao nhiêu chi phí. [Tài liệu Modal Volumes](https://modal.com/docs/guide/volumes)

## Đã kiểm và giới hạn

- `tests10.log` và `tests10.xml` ghi **71 ca đạt trong 14,32 giây**, gồm IO thực trên filesystem local, điều phối Modal giả lập, stop barrier, worker giả lập, checkpoint index, upload dở, artifact sai SHA, retry download, cấu hình lệch, ngân sách và source bundle. Các ca này không cấp container thật.
- `actual-baseline-audit.json` ghi đối chiếu A2/A3 với MODEL_INDEX và SHA model A0/A1 thật. Model gốc giữ nguyên.
- A0 lịch sử chọn epoch bằng validation batch 1. Chỉ checkpoint epoch 9 đã replay batch 128. Chưa replay ranking toàn 12 epoch. Kiểm metadata khớp không xóa giới hạn này.
- Numerical parity CPU compact A2/A3 đã có ở [đợt trước](../junyi-a2-a3-preparation-20261113-01/README.md). Chưa kiểm worker staged trên Linux/CUDA hoặc interrupt/resume thật trên Volume v2.
- `tests01.log`/`tests02.log` giữ lần kiểm bị treo trong môi trường Windows hạn chế. Lượt sau chạy venv với quyền thực thi phù hợp và Modal được giả lập. `tests03` và `tests07` giữ lỗi fixture đã sửa. Không cộng các lượt lặp thành số ca độc lập.

## Entry point và trình tự tiếp theo

Chạy từ `D:\Dev\KLTN` bằng `.venv\Scripts\python.exe -B`. Request chuẩn bị cần có `archives` source/data/cpu_gate với SHA, `local_files` ánh xạ đường dẫn đích sang path/bytes/SHA và `worker` theo validator. Không dùng template giả confidence để vượt kiểm.

```powershell
.\.venv\Scripts\python.exe -B scripts/akt/prepare_junyi_gpu_stage.py --request <cpu-request.json> --snapshot artifacts/akt/modal/<snapshot-id>
.\.venv\Scripts\python.exe -B experiments/akt/modal_junyi_staged.py --snapshot artifacts/akt/modal/<snapshot-id> --request <execution-request.json>
# Chỉ sau confidence thật, Gate mới, parity CUDA và dự toán đã nghiệm thu
.\.venv\Scripts\python.exe -B experiments/akt/modal_junyi_staged.py --snapshot artifacts/akt/modal/<snapshot-id> --request <execution-request.json> --run
```

Lệnh không có `--run` trả `NO_CLOUD_ACTION`. Execution request phải có execution_id mới, approval_reference, allocation_id hợp lệ trong ledger, image_id, GPU, child/function/watchdog timeout tăng dần và reserved_usd_per_run đủ cho cận chi phí. Resume cần checkpoint path, SHA và inventory cũ. Một allocation chỉ được dùng một lần, lỗi upload giữ reservation để đối soát trước phân bổ lại. Input snapshot không chứa token. Modal client dùng profile private hiện hành và temp trên D.

Output lớn về `experiments/akt/results/<execution-id>/`, gồm budget/dispatch/guard, remote-inventory, files, artifacts.zip và COMPLETE. Logical run giữ nguyên giữa các tranche để tiếp tục đúng checkpoint. Evidence nhỏ của đợt này ở thư mục hiện tại.

## Điều kiện trước training chính

1. Fit confidence thật trên TRAIN80 với spool/resume, đủ lineage và unsupported/reason.
2. Đóng source mới và Gate Linux mới, CPU_CHECK đúng snapshot. Gate cũ không đại diện source mới.
3. Kiểm CUDA ngắn A2/A3, graph on/off và checkpoint/resume, so cùng tensor/target/profile với đường tham chiếu của từng variant. Graph augmentation được phép đổi dự đoán so A0/A1, parity cần kiểm là giữa hai cách thực thi cùng variant.
4. Cập nhật dự toán cả fit/refit/evaluation trong tổng 30 USD, sau đó chạy từng tranche có cap và checkpoint. Chưa có allocation hoặc lượt GPU mới trong đợt này.

`STATE.json` là điểm tiếp tục. `MANIFEST.json` ghim source, bằng chứng và logs của nghiệm thu hiện tại.
