# Chuẩn bị checkpoint/restore CUDA — 10/11/2026

## Trạng thái

CHUẨN BỊ, CHƯA CHẠY. Hai script đã qua phân tích cú pháp và đối chiếu 11 lời gọi API với source hiện hành. Chưa có checkpoint GPU mới hoặc kết quả restore từ gói này.

Bằng chứng trước đã được nghiệm thu riêng tại `research_tracking/runs/akt-colab-t4-current-20261110-01/`. CPU Gate 1.993 ca và CUDA smoke A0–A3 vẫn giữ nguyên phạm vi cũ.

## Mục tiêu trực tiếp

Xác nhận AKT không đồ thị và CG-AKT có gate có thể lưu complete-epoch state trên CUDA và tiếp tục cùng quỹ đạo khi nạp trong process mới. Tái dùng `research_graph_checkpoint.py`, `ResearchGraphAKTAdapter`, `GraphAdamParticipation` và `train_epoch`. Không thay kiến trúc, numerical recipe hoặc thuật toán optimizer.

`checkpoint_worker.py` nhận `--variant A0|A3` và `--phase continuous|interrupted|resumed`. Với mỗi variant, nhánh continuous train E1–E2, interrupted train E1 và lưu checkpoint, resumed tạo model/Adam mới rồi khôi phục E1 và train E2. Đối chiếu chính xác model, optimizer, Python/NumPy/CPU/CUDA RNG, counters, participation và sáu dự báo. RNG được cố ý thay đổi trước restore để kiểm việc nạp thật.

Toàn bộ là fixture handmade 8 learner × 6 tương tác. Confidence được dựng sẵn, không phải artifact Method24 đã fit. Cấu hình backbone giữ 256d/8heads/1block cùng recipe26/28. Không dùng Junyi hoặc Holdout.

## Workload và bằng chứng cần nhận

`allocation.json` chốt sáu process, tối đa 16 optimizer updates/384 physical target exposures, 90 giây mỗi process và 360 giây tổng, CUDA allocator 2 GiB, output checkpoint 256 MiB và free disk tối thiểu 30 GiB. Dừng ở lỗi đầu, không tự retry.

Bốn checkpoint dự kiến nằm trong native output của run, đi kèm metadata, COMPLETE.json, events đã flush/fsync và checksum inventory. Mỗi checkpoint dự kiến khoảng 27 MB dựa trên engineering A0 hiện có, chưa đo bản CUDA của lượt này. Các checkpoint chỉ là complete-epoch model/optimizer/RNG state. Early stopping, sampler/lifecycle controller, global budget và cloud durability còn là điều kiện riêng.

Chỉ nghiệm thu sau khi sáu process kết thúc đúng, nhánh restored khớp continuous và artifact lớn đã được lưu về nơi bền vững rồi kiểm SHA. Không suy từ terminal exit0 hoặc chỉ đọc metadata.

## Trở ngại đang quan sát

MCP vẫn báo frontend kết nối nhưng `run_code_cell` mới hết thời gian chờ hoặc trả output cũ. Sau đổi source sang health, `get_cells` vẫn giữ output export trước. Chưa có bằng chứng lệnh health mới đã thực thi. Vì vậy chưa gửi lệnh chạy checkpoint.

Đã chuẩn bị canary tải một file nhỏ qua Colab, nhưng chưa xác nhận file ở local. Cần chốt đường tải checkpoint lớn trước lượt training dài. Không giả rằng checkpoint trong `/content` đã được lưu bền vững. Đã nhờ người dùng mở tab Colab và chạy cell đầu có `checkpoint_health`; không tự thay runtime hay lặp lại setup.

## Tiếp tục sau gián đoạn

1. Đọc `blocked-observations.json`, `allocation.json` và state tổng. Không lặp lại cài venv hoặc CUDA smoke đã nghiệm thu.
2. Xác nhận health có timestamp mới, root cũ còn tồn tại, T4 vẫn có và `.venv` 44 package còn nguyên. Nếu đổi runtime, điều tra trước mọi launch.
3. Chốt đường nhận checkpoint lớn. Với bản được tải thủ công, kiểm SHA/inventory trước khi nhận vào `experiments/akt/results/` theo run.
4. Request chỉ mới chuẩn bị tại `artifacts/akt/colab/requests/t4-checkpoint-stage-launch.json`. Dùng cell ID thực tế còn hợp lệ trước khi gửi. Request không phải bằng chứng đã chạy hoặc quyền Main training.
5. Sau kết quả đạt mới cập nhật hai file báo cáo GVHD. Hiện không có kết quả nghiên cứu mới để thêm vào báo cáo.
