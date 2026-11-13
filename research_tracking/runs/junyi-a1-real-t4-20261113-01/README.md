# A1 — đo Junyi thật trên T4 và kiểm khả năng cache

## Kết quả đã đạt ngày 13/11/2026

Đã đo cả đọc/kiểm cache mẫu, chuẩn bị batch, forward, backward và Adam trên T4 miễn phí. Dữ liệu gồm 256 window từ 204 learner TRAIN80, lấy 32 window từ mỗi tám shard đã chọn bằng seed43. Selection gồm 88 window, 4.440 target từ 64 learner, mỗi learner giữ tối đa 300 sự kiện đầu. Vocabulary717 và graph976 cạnh theo nguồn hiện hành. Membership learner giữ nguyên phép chia frozen, ID được đổi mã theo role và thứ tự đã có, không chia lại trên ID mới.

### Đối chiếu ngắn trên dữ liệu thật

| Đại lượng | A1 reference | A1 compact |
|---|---:|---:|
| Đọc mẫu và 8 bước học | 9,4048 giây | 4,3990 giây |
| Target/giây | 6.069 | 12.975 |
| GPU-Util trung bình theo mẫu | 23,0% | 48,5% |
| Số mẫu GPU | 31 | 13 |
| Dự đoán 4.440 target selection | 0,6869 giây | 0,2006 giây |

Training nhanh hơn khoảng 2,14 lần, prediction nhanh hơn 3,42 lần. Loss, gradient, tham số sau Adam, optimizer và RNG khớp ở hai mức alpha đã kiểm. Sai lệch xác suất selection lớn nhất bằng 0, population hash khớp. Các model được khởi tạo mới seed42 để kiểm thực thi. Chưa dùng checkpoint A1 nghiên cứu để đo.

### Chuỗi dài hơn sau làm nóng

Sau nhận xét GPU48,5%, đo riêng mỗi điều kiện tối thiểu15giây sau hai bước làm nóng, tối đa64bước/điều kiện. Các bước liên tục giữ optimizer đã khởi tạo, khác phép đo ngắn khởi tạo lại optimizer ở mỗi block. Thời gian và số bước riêng được lưu đầy đủ, không dùng phần profiler để tính throughput.

| Điều kiện kỹ thuật | Bước | Target/giây | GPU-Util trung bình | Mẫu GPU |
|---|---:|---:|---:|---:|
| A0, đọc mẫu mỗi lượt | 38 | 17.747 | 80,0% | 27 |
| A1 compact, đọc mẫu mỗi lượt | 32 | 14.842 | 69,7% | 27 |
| A1 compact, tái dùng records đã giải mã | 36 | 16.314 | 75,4% | 28 |

A1 hiện vượt mục tiêu50% trong chuỗi đo này. Tái dùng input tăng thêm khoảng9,9% throughput so với đọc/kiểm NPZ lặp. Đây là thử nghiệm in-memory trên mẫu đã có, chưa triển khai prefetch hoặc cache graph production. A0 dùng cùng vocabulary, dữ liệu, batch128, FP32, optimizer và khởi tạo backbone theo seed42, giữ vai trò đối chiếu chi phí tính toán. Bảng này không so chất lượng dự báo của A0/A1.

GPU-Util đo thời gian có kernel hoạt động trong cửa sổ lấy mẫu, độ dài cửa sổ tùy sản phẩm. Các mẫu liên tiếp có tương quan và ranh giới phase xấp xỉ. Báo cáo giữ cả kết quả ngắn và dài. Kết quả dài có thêm warm-up, optimizer chạy liên tục và thời lượng lấy mẫu lớn hơn, vì vậy mức69,7% chưa được quy cho một thay đổi code mới sau phép đo48,5%. [Định nghĩa NVIDIA NVML](https://docs.nvidia.com/deploy/nvml-api/620/api/structnvmlUtilization__t.html)

## Profiler và phần còn có thể giảm

Giữ trace CPU/CUDA của bốn bước A1 riêng. Mỗi batch có khoảng36ms dựng graph context và khoảng43ms đọc/kiểm dữ liệu mẫu theo vùng profiler. Đây là thời gian có instrumentation, chỉ dùng để xác định hướng điều tra. `cudaStreamSynchronize` tích lũy khoảng955ms trong bốn bước bao gồm chờ GPU thực sự tính toán, không được cộng toàn bộ vào phần CPU có thể loại bỏ. Thời gian `backward_launch_seconds` là thời gian phát lệnh, một phần thực thi GPU có thể được chờ ở gradient clipping. Không kết luận clipping chậm chỉ từ đồng hồ host.

Các nhóm CUDA được ghi gồm nhân tensor, nhân ma trận, cumsum và softmax/attention. Trace, bảng CPU/device và danh sách operation được giữ tại thư mục `profile/` trong output native. Wrappers chỉ thêm vùng đánh dấu và gọi nguyên các hàm integrity/model; source production được giữ ở phiên bản ade1754 trong đợt này.

## Có thể cache gì trước khi GPU chạy

Đối với Junyi fixed-stream, có thể tính trước parent lookup, support, mean correctness quá khứ, message A1, mặt nạ áp dụng và metadata window. Với confidence cố định theo artifact, có thể tính trước phép tổng hợp tương ứng và feature cố định cho gate. Alpha, gate output phụ thuộc trọng số đang học, logits, loss và gradient vẫn tính trong model. Với mô phỏng vòng kín, cache chỉ dùng graph tĩnh và lịch sử đã quan sát, không tính trước đáp án hoặc hành động tương lai.

Đã thử hai prototype CPU trên cùng256window và giữ cả kết quả âm.

| Prototype cache theo window | Dựng trực tiếp / 256 window | Lookup + ghép batch | Tăng tốc phần context |
|---|---:|---:|---:|
| Kiểm semantic toàn bộ từng entry ở mỗi lookup | 0,1381 giây | 0,1489 giây | 0,93 lần |
| Kiểm semantic khi fill, kiểm SHA bytes bất biến mỗi lookup | 0,0890 giây | 0,0539 giây | 1,65 lần |

Các cặp được đo riêng trong từng lượt, tải máy có biến động, không so thời gian tuyệt đối giữa hai lượt như một đối chiếu được kiểm soát. Prototype thứ hai giữ digest context khớp builder hiện hành theo từng batch, kể cả đổi thứ tự và nhóm97window. Đổi prior response hoặc phase gây cache miss. Sửa bytes context bị từ chối. Đây mới là bằng chứng CPU, chưa có số tăng tốc CUDA từ cache graph và chưa có cache đĩa toàn TRAIN80.

Khóa cache production cần dataset/source manifest, roles/fold/phase, encoding, graph/confidence và phiên bản công thức/builder. Từng entry còn gắn hash typed arrays của window, bao gồm prior responses và geometry. Refit90, encoding khác, graph nhiễu khác hoặc confidence khác phải được phân biệt bằng key. Cache được ghép theo window để dùng qua các thứ tự shuffle khác nhau. Cache cả batch cố định sẽ mất khả năng tái dùng khi nhóm window thay đổi.

Thiết kế tiếp theo phù hợp là sidecar theo shard trong vùng `artifacts/akt/`, build trên CPU trước khi cấp GPU, kiểm đầy đủ nguồn/target coverage khi đóng cache, rồi đọc trước số shard hữu hạn. Giữ source window cache hiện có. Native vẫn kiểm context và batch sau ghép. Nghiệm thu cần so toàn tensor context, loss/gradient/Adam/RNG, prediction, sampler/resume và đo cả I/O của cache. Chỉ đưa vào pipeline khi chi phí lookup, kiểm và đọc artifact thực sự nhỏ hơn phần tính lại.

## Ước lượng thời gian

Quy đổi riêng thông lượng chuỗi dài A1 cho13.347.331target train cho khoảng15phút/epoch T4 ở điều kiện giống mẫu; dùng input đã giải mã cho khoảng13,6phút. Đây là ngoại suy kỹ thuật, chưa chạy toàn epoch. Full cache admission, phân bố window đuôi dài, toàn I/O, checkpoint và validation chưa được nghiệm thu. Số17phút đã trao đổi trước dựa vào lượt đo ngắn. Không dùng tỷ lệ T4 để khẳng định thời gian H100 hoặc hứa22phút còn2phút.

Ưu tiên triển khai vẫn là nghiệm thu source cuối và chuyển tiếp checkpoint A1 source2 epoch1 thật có manifest riêng, sau đó đo workload đại diện trên H100 có trần chi phí. Cache chỉ tạo đóng góp kỹ thuật giúp chạy thí nghiệm, chưa hoàn thành các so sánh khoa học RQ3.

## Bằng chứng và sự cố đã giữ

- `cohort-receipt.json`, `prepare_cohort.py` giữ lấy mẫu, nguồn, giới hạn và biến đổi ID. Data phái sinh ở `artifacts/akt/colab/junyi-real-t4-cohort-20261113-01/`, không đưa vào Git.
- `egress-authorization.json` ghi lần bộ duyệt tự động chặn egress và chấp thuận rõ ràng tiếp theo của người dùng cho gói1,37MB tới Colab. `transfer-manifest.json` giữ inventory trước upload, không token/Holdout/checkpoint nghiên cứu.
- Lượt đầu bị chặn do output folder khác run ID trước khi model training. `probe_real_t4_attempt01.py`, `failed-attempt01.json` và `configuration-fix.json` giữ lỗi và kiểm cấu hình sửa đúng trước lượt02. Gói source đầu chứa scriptv1, scriptv2 được chuyển riêng và kiểm SHA. Không bỏ qua validate_config.
- `probe_real_t4.py` là script đã thành công. `profile_pipeline_t4.py`, `profile-config-check.json` giữ phép đo dài hơn và profiler.
- `graph-cache-prototype.json` và `graph-cache-validated-prototype.json` cùng hai script benchmark cache giữ cả phép đo chậm hơn và bản kiểm dữ liệu bất biến. Cache graph production chưa được nối.
- `checkpoint-download-receipt.json` ghi đủ799chunk, CRC ZIP và SHA model. `local-state-load.json` xác nhận54tensor model hữu hạn và48parameter có Adam state, optimizer step4. Trạng thái benchmark28,9MB ở `experiments/akt/results/colab-a1-real-t4-20261113-attempt02/BENCHMARK_STATE.pt`, không là selected-fit và không hỗ trợ resume production.
- `download-plan.json`, `profile-download-plan.json`, `profile-download-receipt.json` giữ kiểm tải về D. Logs/results/trace nằm trong output native trên, với profiler tại `profile/`. Các bản model tạm của profiler được phục hồi khởi tạo sau từng điều kiện.
- `summary.json`, CSV và figure SVG/PDF/PNG độc lập được dựng từ số đo thực. `build_figure.py` giữ cách dựng và provenance màu từ figures4papers. Kết quả mới được nối vào cặp báo cáo hiện hành.

Đợt này dùng0USD Modal. Thông tin dọn runtime và bridge được ghi riêng trong `runtime-cleanup.json` theo đúng trạng thái quan sát được, không suy ra runtime đã trả chỉ từ bridge đóng.
