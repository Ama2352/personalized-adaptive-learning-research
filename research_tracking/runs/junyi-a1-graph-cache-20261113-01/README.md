# Cache đồ thị A1 — tích hợp và kiểm T4

## Phạm vi

Tính trước message từ prefix quá khứ của từng window Junyi và giữ trong SQLite chỉ đọc. Không cache trọng số, alpha, logits hoặc gradient. Cache riêng theo dataset, window manifest, encoding, phase, graph và source. Không đổi phép chia learner, batch128 hoặc FP32. Chỉ kiểm kỹ thuật trên cohort T4 đã được phép chuyển ở đợt trước, không chọn mô hình và không dùng Holdout.

## Tiến trình

- Đã thêm builder CPU và reader cache có SHA ngoài, khóa đầy đủ input và digest từng context. Đổi input, graph, phase hoặc source phải tạo cache mới. Build chưa hoàn tất chỉ để lại `.partial`, không công bố cache.
- Đã nối cache tùy chọn vào adapter và selected-fit producer. Grant và recovery identity ghi cache. Đổi sang selection tự bỏ cache train. Định danh producer được sửa để khớp backend context và adapter thực.
- Lượt local đầu gặp thiếu PYTHONPATH rồi Git từ chối ownership của dependency và quyền hardlink trong vùng test mặc định. Lượt tiếp dùng venv, vùng test ổ D và safe.directory chỉ trong môi trường process. Không đổi cấu hình Git global. Hai assert so cả thời gian thực thi đã được sửa để so kết quả số học.
- `local-tests03.log` và XML xác nhận **62 ca đạt trong 98,07 giây**, gồm parity loss/gradient/Adam/RNG/prediction, shuffled/rebatched windows, đổi dữ liệu và cache hỏng, build thiếu coverage, resume cùng backend và orchestration producer.
- Colab xác nhận Tesla T4 15.360 MiB. Gói 159 file được kiểm SHA trước khi giải nén. Phép kiểm GPU hoàn tất trong 71,83 giây, tổng 100 bước optimizer trong workload kỹ thuật. Loss, gradient, Adam/RNG có drift0 ở alpha0 và0,75; 4.440 prediction selection và checkpoint reload cũng drift0. Prediction so sau reset về cùng weights, không so hai model đã được timing với số bước bất kỳ.

## Kết quả cache trên T4

| Đại lượng | A1 compact trực tiếp | A1 compact cache SQLite |
|---|---:|---:|
| Số bước tính trong đoạn timing | 44 | 44 |
| Tổng thời gian timing | 20,99 giây | 20,61 giây |
| Target/giây | 14.956,7 | 15.232,3 |
| GPU-Util trung bình | 67,3% | 70,8% |
| Số mẫu GPU | 74 | 73 |
| VRAM dùng cao nhất theo nvidia-smi | 5.305 MiB | 5.305 MiB |

Mỗi phương án có hai block khoảng10giây theo ABBA. Mẫu GPU gồm hai bước warm-up mỗi block. Hai adapter cùng tồn tại trên GPU, nên VRAM này chưa là yêu cầu full training của một model. Cache gồm256window/14.270target,260KiB, dựng trênCPU khoảng0,67giây trước tạo model CUDA.

Throughput tăng khoảng1,84%, nhỏ so với dao động giữa các block. **Đúng số học đã đạt trong phạm vi kiểm; lợi ích hiệu năng chưa được kết luận.** Cache giữ tùy chọn, chưa bật mặc định. Cần ưu tiên phần đọc/giải mã và selection theo [rà toàn epoch](CACHE_AUDIT.md), gồm14bước và điều kiện sử dụng lại dữ liệu.

## Artifact và kết thúc runtime

Đã tải toàn bộ ZIP26,4MB về `experiments/akt/results/colab-a1-graph-cache-t4-20261113-01/`, kiểm806chunk, SHA file/member và ZIP CRC. `BENCHMARK_STATE.pt`28,9MB có54tensor model và48parameter Adam, đã nạpCPU và kiểm finite. Đây là state benchmark, không phải model nghiên cứu được chọn hoặc checkpoint production được phép resume. Dữ liệu cache nằm dưới `artifacts/akt/graph-context-cache/t4-cohort-20261113-01.sqlite`.

`download-receipt.json`, `local-checkpoint-load.json` và `runtime-cleanup.json` giữ xác nhận. Colab trả `RUNTIME_UNASSIGN_RETURNED` sau khi tải/kiểm artifact, rồi bridge đã đóng. Đợt này dùng **0USD Modal**, không chạyH100. FigureSVG/PNG/PDF vàCSV nằm ngay trong bundle, dựng lại bằng `.venv/Scripts/python.exe -B research_tracking/runs/junyi-a1-graph-cache-20261113-01/build_figure.py`. Màu/quy ước tái dùng từ figures4papers đã ghim ở đợt trước.

## Entry points

Builder CPU dùng `.venv/Scripts/python.exe -B scripts/akt/build_junyi_graph_context_cache.py --request <request.json>`. Request ghi selected-cache/roles/encoding/receipt/graph/window-cache cùng SHA ngoài, output mới dưới `artifacts/akt/graph-context-cache/`, thời gian và RAM tối đa.

`run_junyi_selected` nhận `train_graph_context_cache` và `expected_train_graph_context_cache_sha256` cùng nhau. Grant phải chứa `prepared_inputs.train_graph_context_cache_sha256`. A0 từ chối cache đồ thị. Phải dùng window cache và encoding đã ghim. Cache không tự build khi GPU đang train.

## Điều kiện trước H100

Đối chiếu GPU và tải artifact đã đạt. Full TRAIN80 cache, source/runtime gate cho producer cuối và migration checkpoint A1 epoch1 source2 còn chờ. Checkpoint source2 được giữ nguyên. Kết quả kiểm cùng backend không tự cho phép dùng lại checkpoint khác source.

## Giới hạn

Mẫu 256 window train và 88 window selection là benchmark kỹ thuật, không đại diện toàn epoch. Tốc độ T4 không được quy trực tiếp sang H100. Cache áp dụng log cố định với prefix có sẵn. Vòng kín có đáp án tương lai chưa biết cần dựng context tuần tự.
