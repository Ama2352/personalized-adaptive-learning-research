# Duyệt kiểm CPU compatibility của batch CUDA core

Ngày 09/11/2026. Root và reviewer độc lập đã đọc batchA bốn source/test files. 13 kiểm metadata đã đạt trong0,4977573giây và xác nhận Torch/NumPy/Pandas chưa được import ở lượt đó.

Cho phép chạy một lượt CPU04 gồm26testcases, một backbone/wrapper/gate,8forward và5logical backward,0Adam constructor/step. Geometry tối đa2×6, dữ liệu dựng tay. Worker `275df4b3e0571235de6d7c8602bc77e20d83a1c599a1f226e21f9d99f8100ee3`, outer `1dac7e1ee2303d03a03a5b0446888921faa417f942b0140d512cbaf92c8290c6`, allocation `909f3da95e64bdbbfc715f16ff45b12e2a1ece4f19d2dfdb7407db9ad6c2eb1d`.

Allocation riêng có trần90giây tổng, owned87, worker80 và cleanup reserve3. RSS không quá1GiB, RAM khả dụng tối thiểu1536MiB. Quyết định floor của lượt unit nhỏ này dựa trên bằng chứng CPU03 trước đó có peak277712896bytes trong6,838giây với cùng geometry và số phép NN. Monitor vẫn kiểm floor/cap và dừng khi vượt. Các allocation cũ giữ giới hạn đã ghi.

Nghiệm thu cần đủ26JUnitidentities, các bộ đếm body thật, genuine upstream source/Git/EOL, source-before/after, khôi phục methods/runtime/environment, Job0 và thời gian toàn outer. Lượt này kiểm đường CPU sau thay đổi source. ActualCUDA/checkpointCUDA/MainCUDA là các bước tiếp theo trong ladder.
