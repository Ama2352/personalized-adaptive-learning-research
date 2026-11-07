# Sẵn sàng kiểm recovery AKT trên Colab — 07/11/2026

## Phạm vi và kết luận

Gói này hoàn thiện kiểm kỹ thuật local và chuẩn bị notebook GPU miễn phí. Không đọc lại Junyi/Holdout, không đổi kiến trúc nghiên cứu hoặc hyperparameters đã phê duyệt, không khởi tạo compute/image/Volume Modal và không dùng credits. Fixture d32 là cấu hình kiểm riêng, không thay training config d256. Các kết quả dưới đây không chứng minh graph có ích và không đóng RQ1–RQ3.

## Lỗi được xác định và sửa

`torch.load(map_location='cuda')` có thể đưa cả RNG ByteTensor trong checkpoint lên CUDA. CUDA generator yêu cầu RNG state trên CPU. `_restore_payload` trước đây chuyển `torch_rng` về CPU nhưng chưa chuyển danh sách `cuda_rng`. Sửa tại `src/knowledge_tracing/akt/checkpoint.py`: chuyển từng RNG state về CPU trước `set_rng_state_all`; không thay model/Adam weights hoặc dữ liệu.

Nguồn đối chiếu: [PyTorch torch.load](https://docs.pytorch.org/docs/2.7/generated/torch.load.html), [CUDAGeneratorImpl v2.7.1](https://github.com/pytorch/pytorch/blob/v2.7.1/aten/src/ATen/cuda/CUDAGeneratorImpl.cpp#L315-L326). Đây là kết luận từ source và regression CPU mô phỏng remapped state, chưa là lỗi được tái hiện trên GPU thật.

Trial đầu bị Git ownership guard chặn, không dùng làm bằng chứng lỗi CUDA. Sau khi cấu hình safe.directory riêng cho process đúng upstream, regression mới thất bại trên đường restore cũ; sau sửa, checkpoint/recovery suite đạt **12 tests**, unit checkpoint/probe đạt **10 tests**. Giữ cả source cũ và logs với SHA để kiểm lại, không sửa snapshot lịch sử.

## Recovery qua tiến trình mới — đã chạy CPU

`scripts/akt/synthetic_recovery_probe.py` dùng đúng `train_epoch` và checkpoint/replay cursor của pipeline, không viết trainer thay thế. Fixture17targets/3exercises/H2T2/batch2, d32/dropout0.2:

| Nhánh | Workload thực tế | Nghiệm thu |
|---|---|---|
| Continuous | 5 optimizer updates,17targets | Hoàn tất epoch nhỏ |
| Interrupted | 2 updates,7targets | Ngắt có chủ đích sau checkpoint đã publish |
| Resumed, process mới | 3 updates,10targets | Hoàn tất cùng epoch, khôi phục Adam/RNG/cursor |

Tổng10updates qua3tiến trình; không phải10epochs hoặc training thật. Run `experiments/akt/results/cpu-colab-recovery-20261107-02` đạt trong19.99giây: model/Adam/RNG/predictions exact, max delta0; thứ tự optimized row ledger khớp, đủ17targets mỗi nhánh, không trùng/bỏ sót; sampler9windows khớp; checkpoint/phase files nguồn không đổi. Run01 thất bại do probe chưa gán checkpoint identity trước export; đã sửa probe và giữ log/source trước sửa.

Giới hạn: ngắt tại optimizer boundary có chủ đích, không hard-kill giữa ghi file, không preemption/Volume durability, không full data/epoch selection/refit/throughput. `gate4_pass=false`; `cuda_mid_epoch_resume_verified=false` trên CPU.

## Notebook và nguồn chuyển Colab

Notebook hiện có7cells. GPU lifecycle d256/400targets/1update được giữ riêng; recovery d32/17targets được thêm sau đó. Recovery bị chặn nếu CPU hoặc lifecycle chưa đạt, source đổi, report sai device/workload/scope/ledger hoặc checksum outputs sai. AST6codecells và **19 trường hợp guard giả lập** đã đạt local; đây không phải19 thí nghiệm GPU.

Kitv11 có137files, SHA256 `0d4d59a973b4909b26837f795ead499f3b0da6375db3dd6f58096c57530a9f09`; chỉ allowlist source/fixtures. Không có interactions thật, credentials hoặc checkpoint. Bản notebook chạy ở ngoài ZIP và cần dùng cùng v11; v10 không chứa recovery script.

Actual Colab/Linux/CUDA vẫn **CHƯA CHẠY**. Phiên local không có kênh thực thi runtime Colab; notebook được chuẩn bị để chạy tương tác qua giao diện chuẩn. [Runbook](../../docs/akt-colab-synthetic-runbook.md) hướng dẫn thao tác và tải artifacts. Colab không sẵn GPU/quota thì tiếp tục local; không tự tiêu Modal credits. Sau Colab đạt vẫn cần kiểm riêng môi trường Modal nhỏ, có allocation rõ.

## Bằng chứng và việc còn lại

- Bundle [cpu-colab-recovery-20261107-01](../runs/cpu-colab-recovery-20261107-01/README.md): regression trước/sau, trial thất bại, CPU recovery3processes, guard harness, notebook snapshot và bundle inventory.
- [Gate archive](../runs/cpu-colab-recovery-gate-20261107-01/README.md): **407passed,0fail/error/skip**,169.05giây pytest, cap540giây CPU; nguồn/lock/upstream ổn định, pointer đã kiểm lại. Report SHA `4ed716224778b069816e0ba22370bfc4ad5c60326a89cfc5d7b832133716d961`. Snapshot401 cũ được giữ; số test không được dùng thay nghiệm thu CUDA hoặc kết quả RQ.
- Tiếp theo: thực thi notebook trên GPU Colab khi runtime sẵn sàng, giữ cả output thất bại/thành công; không tự retry training, không chạy Modal từ việc token còn hiệu lực.

## Cập nhật handoff VS Code — cùng ngày07/11

Notebook hiện8cells, nhúng nguyên kitv11 cóSHA cố định và không còn gọi browser upload/download. Cell01 chỉ kiểm kết nối, cellcuối xuất ZIP+SHA tải quaColabContents; source/model/tests trong kit khôngđổi.20checks local đạt: actual137file extraction và failure ZIP export/hash/no-overwrite, các guard GPU/setup/CPU làmocks. Initialharness false-positive vì comment chứa google.colab đã sửa bằng ASTimportcheck; giữ log/source cũ. Bằng chứng ở runs/cpu-vscode-colab-notebook-20261107-01, khôngactualColab/CUDA. Nội dung7cells/19guards ở phần trước mô tả bảnnotebook lịch sử. Mở runbook hiện tại cho thao tác mới.
