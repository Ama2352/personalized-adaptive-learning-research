# Regression RNG và recovery AKT tổng hợp — 07/11/2026

Chỉ kỹ thuật CPU và chuẩn bị Colab, không có Junyi/Holdout/GPU/Modal compute.
`cuda-rng-before.log/xml` bị Git ownership guard; `before2` mới là regression expected-fail
trên restore cũ. `after`12pass và unit01 10pass. Source trước sửa giữ nguyên SHA.
Probe01 lỗi identity trước prediction export; probe02 đã sửa và chạy3processes thật:
continuous5updates/17targets = interrupted2/7 + resumed3/10. Model/Adam/RNG/sampler/
predictions exact, nguồn interrupted bất biến,19.99s. Đây là ngắt có chủ đích tại
committed optimizer boundary, không hard-kill/preemption/Volume durability.
Các `.pt` ở experiments/akt/results theo run, không sao binary vào Git; inventories
được đối chiếu trước archive. Báo cáo/harness guard là19mockcases, không actualCUDA.
Kitv11 CRC/source SHA parity đã kiểm; chưa chạy suite trong extracted Linux runtime.
Notebook snapshot và manifest đi cùng source bundle; Gate4 luôn false.
