# Xuất gọn A1 Junyi và đối chiếu A0

Đã xuất A1 epoch 9 sau selected-fit 12 epoch đến `experiments/akt/results/model-export-a1-batch128-20261113-01/`. Thư mục có bốn file cùng cấu trúc gói A0, gồm một checkpoint `A1_JUNYI_SELECTED.pt` 28.908.975 byte, `MODEL_INDEX.json`, `SUPPORT.zip` và `README.md`. Model/Adam/RNG giữ nguyên byte từ checkpoint nguồn. Gói support giữ source, encoding/receipt, graph, roles và provenance. Checkpoint/predictions/logs gốc giữ nguyên tại output run.

`export-plan.json` được ghi trước khi sao chép, ghim SHA nguồn/đích và input support. `export_selected.py` kiểm hợp đồng A0–A1 rồi stream file tạm, fsync, đối chiếu và publish trên D. `verify_export.py` đạt CPU torch.load(weights_only=True), trọng số hữu hạn, vocabulary 717, alpha A1, Adam/RNG, SHA nguồn/đích và mọi member SUPPORT.zip. Gói chưa kiểm API inference độc lập từ riêng thư mục export. Không training, không dùng Modal/GPU hoặc truy cập Holdout.

## Phạm vi so sánh

`comparison-audit.json` xác nhận cùng inputs/encoding, split outer-fold4 train80/selection10, train13.347.331 target, selection1.600.343 target, backbone khởi tạo, seed42, trainbatch128, optimizer, FP32, kiến trúc backbone và quy tắc min_delta0,0001/patience3/max20epoch. A1 thêm augmentation đồ thị theo thiết kế. Dùng cùng tập selection chưa đủ kết luận hơn kém trên tập đánh giá độc lập.

A0 chọn epoch bằng validation batch1, A1 bằng batch128. Checkpoint A0 epoch9 đã replay đủ selection với batch128 và Log Loss bằng bản cũ. Xác suất khác nhẹ về số học, ranking toàn12epoch A0 bằng batch128 còn chưa replay. Giới hạn này phải được công bố trong kết quả so sánh. Refit/calibration/đánh giá độc lập cùng protocol còn chờ. Giữ nguyên checkpoint và kết quả lịch sử A0.

## Nguồn

- A0 gọn tại `experiments/akt/results/model-export-a0-batch128-20261112-01/`.
- A1 gốc tại `experiments/akt/results/modal-junyi-a1-b128-h100-20261113-07/checkpoints/epoch-009/state.pt`.
- Hợp đồng/admission, replay A0 và nghiệm thu A1 tại hồ sơ đã đóng `research_tracking/runs/junyi-a1-selection-cache-20261113-01/`. Hồ sơ đó giữ nguyên.
