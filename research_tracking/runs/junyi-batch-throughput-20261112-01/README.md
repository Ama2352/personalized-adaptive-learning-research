# Đo thông lượng theo kích thước batch trên T4

## Trạng thái

Đã chuẩn bị chương trình và kiểm hợp đồng đầu vào bằng CPU. Chưa gửi job cloud trong gói chuẩn bị này. `cpu-contract-check.json` xác nhận đủ 1.024 cửa sổ, 56.332 target và 100.032 token hợp lệ cho từng điều kiện, không import Torch và không thực hiện training.

Đây là phép đo kỹ thuật phục vụ quyết định chi phí. Việc dùng batch mới trong nghiên cứu cần một quyết định protocol riêng vì số lần cập nhật và quỹ đạo tối ưu hóa thay đổi. Lượt A0 chính đang giữ batch 4.

## Đầu vào và đối chiếu công bằng

- Dùng nguyên source04, bằng chứng Gate04, encoding 717 exercise và packet đã kiểm tại `../junyi-throughput-20261112-01/`.
- Packet gồm 1.024 cửa sổ từ 755 learner TRAIN80. Đây là tập con để đo kỹ thuật. Các vai trò và danh tính của pha đầy đủ vẫn được giữ nguyên.
- Mỗi điều kiện dùng cùng thứ tự shuffle seed 43, cùng target, mask, nhãn và lịch sử nhân quả. Từng điều kiện khởi tạo lại trên CPU với seed 42 và phải có cùng mã kiểm backbone ban đầu.
- Cấu hình tham chiếu vẫn ghi batch 4. Trường `actual_benchmark_batch_size` ghi riêng cách nhóm thực tế 4, 8, 16 hoặc 32 qua API `collate_windows` và `AKTAdapter.step`.
- Giữ FP32 và các thiết lập Adam minh bạch. Không sửa validator hay cổng nghiệm thu của pipeline nghiên cứu.

| Batch thực tế | Cập nhật | Target | Token kể cả padding |
| --- | --- | --- | --- |
| 4 | 256 | 56.332 | 186.128 |
| 8 | 128 | 56.332 | 201.888 |
| 16 | 64 | 56.332 | 204.800 |
| 32 | 32 | 56.332 | 204.800 |

Nếu hoàn tất cả bốn điều kiện, tổng workload là 480 cập nhật và 225.328 lượt target. Mỗi điều kiện chỉ đi qua packet một lần.

## Số đo và bằng chứng phải thu

Thời gian một lượt bao gồm dựng batch, bước tối ưu hóa, đồng bộ CUDA và kiểm RAM. Xuất cả thời gian toàn lượt và thời gian sau khi bỏ batch đầu. Việc nạp và kiểm packet, lưu checkpoint và kiểm reload nằm ngoài thời gian thông lượng nhưng vẫn thuộc thời gian và chi phí job.

Mỗi điều kiện hoàn tất lưu số target, cập nhật, gradient hữu hạn, mức sử dụng VRAM/RAM, thời gian, checkpoint model/Adam/RNG và phép kiểm dự đoán cửa sổ đầu sau khi reload chính xác. Chương trình giữ giới hạn VRAM 2 GiB. Khi OOM, dừng các điều kiện còn lại, lưu kết quả từng điều kiện đã hoàn tất và trả trạng thái `PARTIAL_JUNYI_BATCH_PROFILE_OOM`. Không coi trạng thái này là nghiệm thu đủ bốn điều kiện.

Chưa có số đo GPU trong gói này. Chỉ lựa chọn phương án theo thông lượng và chi phí đo được. Phép đo không xác định mô hình dự báo tốt hơn. Ngoại suy sang training đầy đủ còn cần tính thời gian kiểm cache, sampler, validation, checkpoint và xuất dự đoán của producer chính.

## Giới hạn thực thi

- Một T4, dự phòng tối đa 0,20 USD trong ngân sách dự án 30 USD.
- Watchdog phía client 400 giây, tiến trình remote 380 giây, timeout function 420 giây. Workload worker có giới hạn riêng 320 giây.
- Nhánh chính phải xác nhận A0 hiện hành đã dừng, bổ sung allocation trong sổ ngân sách và kiểm lại request trước khi dispatch.
- Checkpoint từng điều kiện được đồng bộ về Volume. Archive tải về phải đạt kiểm SHA-256, CRC và inventory.
- Chạy mặc định của controller chỉ hiển thị kế hoạch. Việc dispatch cần `--run` cùng kiểm ngân sách và các pin đầu vào.

## Thành phần

- `gpu_worker.py` thực hiện bốn điều kiện và lưu kết quả.
- `request.json` ghi giới hạn, nguồn và pin packet/reader.
- `cpu-contract-check.json` giữ kiểm CPU thực tế về thứ tự, target và hình học batch.
- `../../../experiments/akt/modal_junyi_batch_probe.py` là controller. Đường dẫn từ root repository là `experiments/akt/modal_junyi_batch_probe.py`.
- `source-manifest.json` ghi inventory các file chuẩn bị. Manifest cần cập nhật nếu nhánh chính sửa chương trình trước dispatch.

Giữ bundle mở cho kết quả và rà soát của nhánh chính. Các checkpoint và archive lớn sẽ được lưu trong output theo run của pipeline.

## Kết quả thực thi đã nghiệm thu ngày12/11

Cả bốn trường hợp hoàn tất, tổng480updates/225.328target exposures. Mỗi trường hợp dùng56.332target/100.032validtokens, cùng backbone khởi tạo, có gradient hữu hạn và checkpoint reload khớp. Đã tải archive104.738.285byte, đối chiếuSHA/CRC/inventory và nhận stop acknowledgment. Worker mất35,30giây, remote cả đóng archive42,41giây. Đây là thời gian remote, không thay toàn bộ elapsed startup/download.

| Batch | Updates | Giây train packet | Target/giây | Peak allocated VRAM | Speedup sau bỏ batch đầu |
|---|---:|---:|---:|---:|---:|
|4|256|7,687|7.328|241,7MiB|1,00×|
|8|128|4,127|13.649|396,6MiB|1,68×|
|16|64|3,309|17.025|694,9MiB|2,11×|
|32|32|3,001|18.769|1.301,4MiB|2,43×|

Batch4 chịu khởi động CUDA đầu tiên. Đã giữ cả thời gian có và bỏ batch đầu để người đọc thấy ảnh hưởng. Mỗi batch chỉ có một lượt đo, chưa là benchmark time-to-quality hoặc số epoch cần hội tụ. Main A0 vẫn batch4, không áp batch mới âm thầm.

Lượt local01 bị chờ mạng trước reservation/dispatch. Đã xác minh đúng PID và dừng, giữlog. Lượt02 dùng quyền kết nối phù hợp và thực thi thành công. Hồ sơ ở `local-network-attempt01.json`, `root-review.json`, `gpu-execution02.log`, native receipt vàguard. `source-manifest.json` là inventory bản chuẩn bị ban đầu. Request được cập nhật sau root review, inventory cuối giữ ở `manifest.json`.

Figure đọc là `batch-throughput-v2.svg`, cóPDF/PNG/CSV và `build_figure_v2.py`. Bản đầu cùng nguồn vẫn giữ vì chú thích chân hình bị gần nhãn trục. Đã xem trực tiếp PNGv2, chữ và chú thích tách rõ. Chuyển thể quy ước figures4papers tại commit đã ghim trong `../figures4papers-akt-20261112-01/`, CC BY-NC4.0.
