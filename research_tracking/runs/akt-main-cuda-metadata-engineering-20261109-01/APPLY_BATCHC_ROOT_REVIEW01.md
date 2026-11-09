# Thứ tự tích hợp Main CUDA sau review nguồn

Root và reviewer độc lập đã đọc bốn production diffs cùng contract BatchC, kiểm tám candidate hashes và17đầu vào gốc. Root đã compile cả tám file, chưa import hoặc chạy chúng. Nhánh CPU giữ serialization và API mặc định. Nhánh CUDA có profile, recipe28, runtime/source/Gate đúng thiết bị, Linux proof riêng và checkpoint schema2.

Root chọn cập nhật thứ tự engineering. Áp dụng tám file ứng viên để kiểm metadata qua entrypoints chuẩn, trong khi lượt hồi quy native checkpoint chờ tài nguyên và chẩn đoán môi trường. Checkpoint04 chưa dispatch, source/packet trước đó được giữ. Sau khi nguồn Main ổn định, chuẩn bị lại packet hồi quy CPU với đúng source hashes. Không dùng packet04 cũ để chạy nguồn mới.

Checkpoint BatchB giữ sourcee17e và metadata38 đã kiểm. Việc áp dụng C không xác nhận hồi quy native hoặc actual CUDA. Source Gate lịch sử vẫn stale và cần nghiệm thu mới trước nghiên cứu. Không thêm quyền chạy, thay phương pháp khoa học, hyperparameters, splits, Holdout hoặc chi Modal.

Kiểm local tiếp theo gồm collection metadata của bốn test modules qua source canonical. Trường hợp `tests/akt/test_runtime.py::test_native_akt_import_cpu` dùng framework thật được giữ cho allocation native riêng. Các test còn lại cần được kiểm scope từ source, xác nhận collected IDs và chạy bounded sau khi Root review controller. Không dùng số test dự kiến thay actual collection.
