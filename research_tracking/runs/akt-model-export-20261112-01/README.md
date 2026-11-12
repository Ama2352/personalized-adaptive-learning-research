# Xuất gọn model AKT trên ổD

Đã xuất8checkpoint đại diện đến `D:/Dev/KLTN/experiments/akt/results/model-export-20261112-01/`, gồm7điều kiện Grade10 và1A0 Junyi best-so-far epoch5. Tổng checkpoint217.690.536byte, toàn gói khoảng221MB. Mỗi cấu hình có một file.pt. Cấu hình, vocabulary, graph/confidence và metadata gốc tập trung trong MODEL_INDEX.json. SUPPORT.zip giữ source/runtime/item bank.

`export-plan.json` được ghi trước khi sao chép model, gồm archive/member/destination/SHA. `export_models.py` chỉ đọc nguồn, stream sang file tạm trênD, đối chiếu rồi publish trong thư mục export. Model gốc giữ nguyên byte. `verify_export.py` đã kiểm8/8SHA, torch.load(weights_only=True,map_location=cpu), model_state_dict/Adam, trọng số hữu hạn, vocabulary và tensor gate đúng variant. Có log và verification.json.

Đây là checkpoint nghiên cứu, Grade10 còn refit/calibration/đánh giá độc lập. Junyi đang chọn epoch, checkpoint5 là best-so-far theo min_delta. Source và mapping đi kèm phục vụ sử dụng qua pipeline KLTN, chưa kiểm API inference độc lập. Lịch sử checkpoint đầy đủ nằm trong các archive cũ, batch32 kỹ thuật có bundle riêng. H100 đang chờ theo yêu cầu, không có run H100 trong đợt này.

Các file.pt nằm trong vùng output theo run trênD. Git lưu script/chỉ mục/bằng chứng nhỏ. Không có upload Hugging Face trong bước xuất local này.
