# AKT — chạy và phê duyệt

Các cấu hình trong thư mục `configs/` là cấu hình bị giới hạn cho những bước sau này. Mọi tài liệu ở đây chỉ mô tả tích hợp AKT trên dữ liệu Development; không dùng Holdout/Test.

## Trạng thái hiện tại

- Mã AKT gốc được ghim theo `docs/akt-provenance.md`; thuật toán upstream giữ nguyên.
- Gate 1 (source và môi trường) đã qua kiểm tra.
- Smoke, pilot và full fold **chưa được chạy**. Cả `smoke.json`, `pilot.json` và `fold0.json` đều đặt `execution_enabled=false`.
- Kết quả “PASS” của gate chỉ là evidence kỹ thuật; không phải quyền chạy thí nghiệm.
- Không có lệnh CV hoặc Holdout trong CLI.

## Lệnh chỉ đọc

```powershell
& .\.venv\Scripts\python.exe -B -m knowledge_tracing.akt.cli --help
& .\.venv\Scripts\python.exe -B -m knowledge_tracing.akt.cli preflight --config experiments/akt/configs/smoke.json
```

`preflight` chỉ kiểm cấu hình, source đã ghim, lock và báo cáo runtime; lệnh không mở dataset.

## Các bước bị chặn

`smoke` và `pilot` yêu cầu một authorization riêng, khớp `phase`, `run_id`, source commit, hash cấu hình và các giới hạn đã duyệt. File gate PASS không thể thay authorization. Full fold vẫn bị chặn ở milestone này; `fold-readiness` chỉ đọc kết quả pilot được chỉ định và luôn trả `full_fold=false`, `five_fold=false`.

Trước khi đọc cohort, runner kiểm tra evidence Gate 2 theo commit nguồn, lock, hash mã/test và log kiểm thử; thay đổi các file này sau kiểm thử làm evidence mất hiệu lực. Giới hạn trong authorization được áp dụng cho cả lựa chọn cohort lẫn training, kể cả khi thấp hơn config. Cohort được xếp hạng theo SHA-256 với tag trong plan, và prefix target giữ đúng thứ tự xếp hạng đó.

## Smoke Task 13

`configs/smoke.json` vẫn là template an toàn với `execution_enabled=false`. Mỗi smoke cần config riêng, run ID mới và file authorization riêng. Authorization khớp phase, run ID, hash chính xác của config, source/runtime/data manifest identity và resource caps; không thể chuyển sang pilot, full fold, CV hoặc config khác. Không thêm `--run-id` vào CLI: run ID nằm trong file config.

Run `smoke-task13-20261031-01` kết thúc `incomplete` do thứ tự learner groups ở export. Run `smoke-task13-20261031-02` dừng trước khi nạp cohort vì available RAM dưới floor 1 GiB. Cả hai run cũ được giữ nguyên. Bản sửa ordering và watchdog được kiểm tra ở Gate 2 với 146 synthetic tests pass.

Một authorization riêng đã cho phép chạy bounded smoke `smoke-task13-20261101-03`:

```powershell
& .\.venv\Scripts\python.exe -B -m knowledge_tracing.akt.cli smoke --config experiments/akt/configs/smoke-task13-20261101-03.json --authorization experiments/akt/authorizations/smoke-task13-20261101-03.json
```

Kết quả: `completed`; 11 learner train thực nạp với 4.096 target, 16 validation learner với 549 target; 12 optimizer steps và 48 windows; prediction export 549/549 hàng, gồm 441 fitted và 108 unseen null. Worker peak RSS `475,430,912` bytes; watchdog wall time `27.53s`; RAM khả dụng thấp nhất trong log boundary `3,799,662,592` bytes. Guard giữ nguyên floor 1 GiB và kiểm tra trước/sau mỗi batch; số nhỏ nhất trong các check batch không được lưu riêng, nên giá trị trên là mức thấp nhất có log cụ thể. Smoke này chỉ xác nhận bounded pipeline trên Development, không phải kết quả benchmark/CV. Tỷ lệ unseen 19,67% chịu ảnh hưởng cohort train smoke nhỏ, không ngoại suy sang Development CV đầy đủ.

Trên Windows, runner kiểm tra peak working set trước và sau batch; nếu vượt ngưỡng, run không được đánh dấu hoàn tất. Đây là kiểm tra giữa các bước, chưa phải giới hạn bộ nhớ cưỡng chế của hệ điều hành: một phép cấp phát có thể tạm vượt ngưỡng hoặc gây OOM trước khi kiểm tra kết thúc. Watchdog CLI giới hạn thời gian của tiến trình con. Cần xem lại các giới hạn này trước khi cho phép smoke/pilot dùng dữ liệu thật.

Cấu hình smoke giữ CPU, batch 4, d32/4 heads, H/T=100, tối đa 32 learner train, 16 validation, 4.096 targets mỗi phía, 20 optimizer steps, 120 giây train và 300 giây toàn tiến trình. Pilot dùng d256/8 heads/d_ff1024, tối đa 1.024 train, 256 validation, 100.000 targets, 900 giây train và 1.200 giây tổng. Đây là các mức chặn dự kiến, chưa được đo thực nghiệm.

Không đổi cấu hình hoặc tạo output trong baseline/dataset. Mỗi run cần `run_id` mới và output riêng; implementation không stage hay commit artifact tự động.
