# Review độc lập trước GPU Junyi

Subagent rà soát reader/cache, train_epoch, model, checkpoint và prediction. Chưa phát hiện blocker API hoặc chia dữ liệu trong scope pilot. Yêu cầu seed riêng Python/NumPy/CUDA ngoài CPU Torch đã đưa vào gpu_worker.py. Checkpoint/reload chứng minh khôi phục state và dự đoán ở cuối epoch. Phục hồi sampler/workflow giữa epoch còn chưa nghiệm thu.

Lượt CPU01 lỗi trước test vì thiếu thư mục runtime trong image mới. Đã giữ archive và traceback tại experiments/akt/results/modal-junyi-cpu-gate-20261112-01/. Lượt02 thêm mkdir cho đúng vị trí runtime, nguồn model và tests giữ nguyên. Chưa dùng GPU trong hai lượt này.
