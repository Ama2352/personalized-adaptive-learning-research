# Kiểm mức sử dụng GPU của AKT ngày 12/11/2026

## Cập nhật12/11 lúc22giờ13 — kiểm chạy hai model dùng chungGPU

Sau khi batch32 đạt mức sử dụngGPU trên50%, đã kiểm ý tưởng chạy hai tiến trình cùng mộtT4 để rút ngắn thời gian hoàn thành hai model. Giữ cùng dữ liệu, batch32 mỗi model, hai seed và số lần cập nhật. Hai model chạy lần lượt mất45.49giây, đồng thời mất45.74giây cho cùng901.312target đo. GPU-Util tăng từ87,9% lên99,9%, tổng thông lượng gần như ngang nhau. Chưa có bằng chứng để tiếp nhận chạy đồng thời làm phương án tăng tốcT4.

Bốn checkpoint đã tải vềD, nạp lại và update tiếp theo khớp. Hai cách chạy khớp model, optimizer, RNG và loss theo seed. Đây là phép kiểm kỹ thuật trên packet lặp. Chưa đánh giá hội tụ, chưa chạyH100 và chưa đổi batch củaA0 chính. Source vàlog lỗi output ban đầu được giữ trongbundle. [Bằng chứng vàfigure](../runs/junyi-concurrent-gpu-20261112-01/README.md).


## Cập nhật20giờ59 — lượt batch32 đã nghiệm thu

Đã hoàn tất lượt kiểm batch32 trên T4 bằng source AKT hiện có. Trong 115 mẫu nvidia-smi qua khoảng65giây training ổn định, GPU-Util trung bình87,5%, thấp nhất76% và cao nhất90%. VRAM đang dùng1.541/15.360MiB, công suất trung bình67,7W và tốc độ khoảng19.792target/giây. Mục tiêu sử dụng GPU trên50% đã đạt trong khoảng đo.

Checkpoint đã tải về, kiểm toàn vẹn, nạp lại và cập nhật Adam tiếp theo khớp model, optimizer, RNG và metric. Lượt kiểm lặp một packet TRAIN80 để đo tài nguyên. Chất lượng trên toàn Junyi và thời gian hội tụ còn cần đánh giá trước khi tiếp nhận batch32 cho các so sánh nghiên cứu. A0 chính vẫn giữ6epoch batch4 đã lưu, chưa thay cấu hình giữa lượt.

Lượt remote gồm kiểm/đóng gói85,06giây, snapshot billing tăng khoảng0,02USD so ngay trước lượt. [Bằng chứng đầy đủ](../runs/junyi-batch32-utilization-20261112-01/README.md). Hai phương án tối ưu nhỏ phía dưới vẫn giữ quyết định cũ. Người dùng yêu cầu chờ H100, chưa chạy H100.


## Đối soát cuối đợt lúc 20 giờ 07

API Modal ghi nhận 3,24858233USD tài nguyên được đo, trong đó 3,24USD đã trừ credits, các khoản miễn trừ được ghi riêng. `billed_cost` hiện bằng0USD. Quy đổi từ30USD credits ban đầu còn khoảng26,76USD. Đây là snapshot lúc20giờ07, chưa phải hóa đơn phân bổ cuối cùng cho từng App. Danh sách container lúc kiểm cuối rỗng.

Giữa snapshot trước A0 execution06 và trước phép đo01, tổng ghi nhận tăng khoảng0,60USD. Giữa trước phép đo01 và cuối đợt tăng khoảng0,04USD. Lượt A0 đã hoàn tất sáu epoch train/selection, archive2.339.280.485byte đã tải và kiểm SHA/CRC/inventory. Không quy toàn bộ3,24USD cho việc kiểm thử tối ưu.

| Phương án | Kết quả thực đo | Quyết định |
|---|---|---|
| Gộp kiểm tra và chẩn đoán của step | Ba cặp CUDA khớp tuyệt đối. Trung vị giảm0,13% thời gian, có một cặp chậm hơn | Loại, trả step chính về bản gốc |
| Giữ cast ma trận khoảng cách trên GPU | Ba cặp CUDA khớp tuyệt đối. Giảm0,91%,3,53%,3,43% thời gian | Chưa đạt ngưỡng tiếp nhận5% đã đặt, giữ ở bundle thử nghiệm |
| Tăng batch dự báo4→32 | Vượt ngưỡng sai lệch xác suất1e-6 trước khi hoàn tất bộ đo | Không tiếp nhận. Chưa lưu được độ lệch cực đại nên chưa kết luận mức sai khác |
| Cache khoảng cách và causal mask theo độ dài/device | Đã khớp CPU. Lượt cloud chạm giới hạn400giây và App đã dừng, thiếu artifact GPU dùng được | Chưa xác nhận CUDA hoặc mức tăng tốc. Giữ code và log, không tự retry |

Hai phép đo training đầu cùng batch4, seed42, thứ tự shuffle43 và packet1.024window/56.332target. Mỗi phương án có ba cặp đảo thứ tự. Sáu checkpoint mỗi phương án giống nhau từng byte, cùng model/Adam/RNG. Worker của lượt01 có trạng thái FAILED do phần dự báo chạy sau training. Phần training đã hoàn tất có sáu hồ sơ case và ba hồ sơ đối chiếu riêng, được phân tích đúng phạm vi. Giữ nguyên lỗi của toàn job.

Bản chính chưa có thay đổi tăng tốc nào được tiếp nhận từ đợt này. Số sử dụng GPU cao hơn chưa đủ làm tiêu chí tiếp nhận. Cần giảm thời gian xử lý cùng workload, giữ tính đúng và đối chiếu pipeline trước khi tiếp tục training dài.

## Hệ quả cho dự toán30USD

Giá kiểm ngày12/11 là0,000164USD/giây cho T4,0,0000131USD/core/giây và0,00000222USD/GiB/giây. Với trần2core/8GiB, cận tài nguyên là0,00020796USD/giây, chưa cộng lưu trữ. [Bảng giá Modal](https://modal.com/pricing).

Để kiểm độ nhạy ngân sách, giả sử A0 còn2epoch selected và5epoch refit, sáu điều kiện graph mỗi điều kiện8epoch selected và5epoch refit. Lấy1.640giây train và250giây selection mỗi epoch từ khoảng số đo A0, workload tương lai là151.900giây. Nhân cận đơn giá trên được khoảng31,59USD, cộng3,24USD đã dùng thành khoảng34,83USD. Đây là kịch bản minh họa có điều kiện, chưa phải dự báo chính xác. Graph chưa có thông lượng đo và số epoch cuối còn chưa biết. Phép tính chưa gồm startup, checkpoint, calibration hoặc các mô hình khác.

Ước lượng18–28giờ trước đây giả định chỉ1–2epoch refit đã không còn phù hợp với diễn tiến A0. Cần lập lại dự toán toàn ma trận và chọn phương án tăng tốc có bằng chứng trước lượt training dài mới. Không bỏ baseline bắt buộc hoặc đổi split để khớp ngân sách.

Nguồn đối soát, dữ liệu từng cặp, log nvidia-smi, code candidate và hình SVG/PDF/PNG ở [bundle tối ưu GPU](../runs/junyi-step-sync-20261112-01/README.md). Các file `sync-analysis.json` và `attention-analysis.json` giữ quyết định loại. `billing-final.json` và `containers-final.json` giữ snapshot cuối. Figure bảnv2 sửa nhãn bị cắt, bảnv1 và nguồn được giữ nguyên.

## Kết luận hiện tại

Cách gọi trước đây rằng GPU đã được tối ưu là quá sớm. Cache, dự báo theo batch và phục hồi checkpoint đã có kiểm kỹ thuật. Mức khai thác GPU trong training chính cần được đo riêng. Đợt đo này xác nhận cấu hình batch4 còn dư VRAM và còn thời gian GPU không chạy kernel. Chưa xác định nguyên nhân nghẽn hoặc chứng minh chi phí thấp nhất để đạt chất lượng yêu cầu.

## Quan sát trực tiếp trong training

Lấy 30 mẫu cách nhau khoảng hai giây, từ 18 giờ 52 phút 30 giây đến 18 giờ 53 phút 29 giây ngày 12/11. Cùng process, cùng epoch5 của execution06, không chuyển sang validation hoặc đóng gói trong khoảng đo.

| Đại lượng | Giá trị đo |
|---|---|
| GPU | NVIDIA T4 |
| GPU-Util trung bình | 43,9%, thấp nhất39%, cao nhất49% |
| VRAM cấp cho context | 459/15.360MiB, khoảng2,99% |
| Điện năng trung bình | 50,95W, giới hạn70W |
| CPU process training | Trung bình tương đương1,28core |
| RAM thường trú process training | Trung bình4,34GiB |
| Tiến độ giữa hai mốc ghi nhận | 2.100 bước optimizer, 496.651target |
| Thông lượng giữa hai mốc | 8.519target/giây trong58,30giây |
| Padding trong phần cửa sổ vừa xử lý | 42,50% số token |

GPU-Util phản ánh phần thời gian có kernel đang thực thi. Chỉ số này chưa mô tả mức sử dụng FLOPS hoặc mức chiếm dụng từng SM. VRAM được cấp và mức hoạt động bộ nhớ là hai đại lượng khác nhau. [Định nghĩa NVIDIA](https://nvidia.custhelp.com/app/answers/detail/a_id/3751/~/useful-nvidia-smi-queries).

Đây là một khoảng quan sát gần một phút. Số CPU/RAM thuộc process training, chưa phải toàn container. Chưa đọc được cgroup quota. Chưa đo toàn epoch hoặc chi phí để đạt cùng chất lượng dự báo.

## Phân biệt các pha thực thi

Mẫu cuối execution04 gồm bốn thời điểm còn worker và26thời điểm worker đã kết thúc, GPU về0% khi đóng gói. Gộp các mẫu này sẽ làm sai trung bình mức sử dụng trong training. Giữ nguyên cả hai bộ log để kiểm chứng.

Batch lớn hơn đã cho thông lượng cao hơn trong benchmark trước, nhưng số bước Adam mỗi epoch cũng thay đổi. Chưa có bằng chứng thời gian đạt cùng chất lượng hoặc tổng chi phí thấp hơn. Cấu hình chính hiện hành tiếp tục batch4 với cùng checkpoint. Các giả thuyết cần kiểm tiếp gồm chi phí đồng bộ CPU–GPU, nhiều kernel nhỏ và kích thước batch. Tăng GPU-Util đơn thuần chưa đủ làm tiêu chí chọn cấu hình.

## Phục hồi lỗi startup

Execution05 hết35giây khi kiểm runtime, trước mọi bước training. Archive lỗi đã tải về và kiểm inventory, App đã dừng. Giữ bản worker cũ, tăng riêng thời gian chờ kiểm runtime lên120giây, kiểm AST xác nhận phần khác giữ nguyên. Execution06 tiếp tục từ checkpoint đã kiểm của execution04 tại epoch5 bước39.488. Khoảng đo trên xác nhận training đã tiến đến bước43.800. Chưa xác định nguyên nhân sâu hơn của sự chậm startup.

## Tiến độ mô hình đã đối chiếu

Execution04 đã hoàn tất epoch4. Log Loss selection lần lượt là0,359648,0,356651,0,355651 và0,356488. Epoch4 kém epoch3. Checkpoint tốt nhất tạm thời ở epoch3. Chưa chốt epoch cuối, refit, calibration hoặc đánh giá độc lập.

## Bằng chứng và cách dựng lại

Các file nằm trong [bundle A0 đang mở](../runs/junyi-main-selected-20261112-01/README.md).

- `gpu-telemetry06.log` giữ mẫu nvidia-smi, process và tiến độ gốc.
- `gpu-telemetry06-data.csv` giữ dữ liệu dạng bảng.
- `gpu-telemetry06-summary.json` giữ thống kê và giới hạn.
- `collect_gpu_telemetry06.py` và `observe_stable_gpu06.py` giữ cách lấy mẫu trên container hiện có.
- `summarize_gpu_telemetry.py` dựng lại CSV và JSON bằng Python trong `.venv`, không cần Torch.
- `gpu-telemetry04.log` giữ pha chuyển từ training sang đóng gói.
- `execution04-verification.json` và `verify_execution04.py` kiểm archive và bốn epoch.
- `runtime-timeout05-remediation.json` giữ đối chiếu sửa startup cùng nguồn checkpoint.

Việc quan sát dùng container training đang chạy. Không cấp thêm GPU cho bộ lấy mẫu. Đợt đo không tăng bằng chứng trả lời RQ hoặc xác lập mô hình cuối cùng.
