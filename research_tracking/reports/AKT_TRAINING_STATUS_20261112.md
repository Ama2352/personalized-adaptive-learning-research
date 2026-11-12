# Thống kê triển khai và training AKT — 12/11/2026

## Lượt batch128 mới trênH100

A0 không đồ thị đã được đưa lên H100 với batch128, khởi tạo từ seed42 và dùng toàn bộ tập train Junyi đã chốt. Hai epoch đầu đã hoàn tất training, validation và lưu checkpoint. Mỗi epoch học 13,35 triệu lượt và kiểm dự báo trên 1,60 triệu lượt selection, đủ toàn bộ đối tượng dự kiến và 0 OOV.

Để chọn thời điểm dừng, theo dõi mức sai lệch giữa xác suất dự báo và đáp án trên tập selection. Log Loss giảm từ0,3600 xuống0,3569 sau hai epoch, cho thấy mô hình đang học được trên cấu hình mới. Kết quả này phục vụ chọn checkpoint. Đánh giá độc lập, refit và calibration còn ở các bước tiếp theo.

Training mất khoảng2phút mỗi epoch, validation thêm khoảng3phút12giây. So với lịch sửT4 batch4 khoảng31phút cho cả chu kỳ, lượtH100 batch128 hiện khoảng5phút10giây. Đây là thay đổi đồng thời phần cứng vàbatch. Lịch sử sáu epoch batch4 được lưu riêng, bảng mới đếm từ epoch1 của lượtbatch128. GPU tiếp tục chạy các epoch theo early stopping và được dừng sau khi xuất bằng chứng bền vững.

[Bằng chứng](../runs/junyi-a0-h100-batch128-20261112-01/README.md).


## Cập nhật20giờ07 ngày12/11

A0 Junyi hoàn tất6epoch train/selection,348.996updates và80.083.986lượt target. Hai epoch mới có Log Loss selection0,354982644 và0,354906797. Với min_delta0,0001, best tạm thời ở5 và stale1. Chưa chốt selected cuối, refit hoặc calibration. Archive execution06 đã tải/kiểm, bản guard lỗi dừng được giữ và có xác nhận server độc lập. Không có job GPU chạy ở snapshot cuối.

Các ước lượng cũ18–28giờ dựa trên1–2epoch refit chưa phù hợp với diễn tiến A0. Đợt thử tối ưu chưa có phương án được tiếp nhận. Chưa mở training dài mới trước khi cập nhật dự toán cả ma trận. [Đối soát chi tiết](AKT_GPU_UTILIZATION_AUDIT_20261112.md).


## Phạm vi và cách đọc

Bảng này chốt theo artifact đã tải về ngày 12/11. A0 là AKT không đồ thị, A1 dùng đồ thị cố định, A2 dùng confidence theo cạnh, A3 thêm gate điều tiết ảnh hưởng đồ thị. Expert và learned là hai nguồn đồ thị riêng, thành bảy điều kiện cho mỗi môi trường. Grade10 và Junyi có vocabulary riêng và train checkpoint riêng.

Một epoch là một lượt qua toàn bộ tập train đã cố định. Sau mỗi epoch, selection được dùng theo dõi chất lượng xác suất và chọn checkpoint. Chạy refit dùng mô hình và optimizer khởi tạo mới, trên train90 và đúng số epoch đã chọn. Các candidate phải hoàn tất selection và khóa quyết định chọn hệ thống trước bước refit chính. Graph/confidence tiếp tục giữ nguồn train80 theo Recipe26.

Các bảng chưa bao gồm full 5-fold CV, thêm seed, SAKT/GKT, các perturbation mở rộng hoặc thời gian nghiên cứu closed-loop. Các yêu cầu đó vẫn nằm trong backlog chung. Không dùng Holdout để chọn epoch.

## Các bước kỹ thuật đã hoàn tất

| Bước | Khối lượng hoặc thời gian đã xác nhận | Kết quả và ý nghĩa |
|---|---|---|
| Kiểm nguồn A0 và pipeline | Gate nguồn A0 đạt 2.218 ca | Ghim source04 cho lượt Junyi đang học |
| Kiểm producer A1 Junyi | Gate nguồn A1 đạt 2.226 ca trên CPU | Có kiểm selected-only, identity và phục hồi, còn nghiệm thu CUDA và fit thật |
| Kiểm cache Junyi đầy đủ | 87,08 giây CPU local | Đọc 232.662 cửa sổ, đủ 13.347.331 target của 126.774 người học |
| Đo tốc độ T4 trên packet đại diện | 256 cập nhật, 56.332 target trong 7,85 giây train | Có checkpoint và reload khớp. Phép đo toàn epoch bên dưới là cơ sở dự toán mới hơn |
| Phục hồi A0 sau Modal preemption | Giữ checkpoint epoch1 bước46.000 và tiếp tục cùng logical run | Trọng số, Adam, RNG và sampler lấy từ checkpoint. Hai file metadata khởi tạo được tái dựng từ nguồn ghim và checkpoint, có ghi rõ giới hạn |
| Lưu artifact execution02 | Archive 2.080.202.385 byte đã đối chiếu SHA, App có stop acknowledgment | Giữ epoch1, epoch2 và trạng thái epoch3 dở dang |
| Lưu artifact execution03 | Archive 2.129.675.285 byte đã kiểm toàn vẹn, App có stop acknowledgment | Đã hoàn tất epoch3 và giữ epoch4 bước15.016, tiếp tục bằng execution04 |

Nguồn kỹ thuật ở các bundle `junyi-throughput-20261112-01`, `junyi-a1-selection-20261112-01` và `junyi-main-selected-20261112-01`. Tất cả là kiểm kỹ thuật hoặc tiến độ fit, chưa thay thế bằng chứng so sánh độc lập cho RQ3.

## Grade10 — bảy điều kiện đã xong chọn epoch

Corpus Main60 có48 người học train,6 selection,6 calibration. Mỗi điều kiện xuất1.260 dự báo selection. Cột thời gian là thời gian controller remote trọn lượt được ghi trong nghiệm thu, gồm các bước vận hành, không phải thời gian train thuần. Các lượt dùng T4/A10 nên không dùng bảng này để xếp hạng tốc độ mô hình.

| Điều kiện | Epoch đã chạy | Epoch tốt nhất | Lý do kết thúc | Thời gian trọn lượt | Log Loss selection | Phần còn thiếu |
|---|---:|---:|---|---:|---:|---|
| A0 | 8 | 5 | Ba epoch sau epoch tốt nhất không cải thiện đủ | 3 phút20 giây | 0,599310 | Refit5 epoch, calibration, đánh giá độc lập |
| A1 expert | 8 | 5 | Cùng quy tắc dừng sớm | 3 phút52 giây | 0,599344 | Refit5 epoch và đánh giá |
| A1 learned | 7 | 4 | Cùng quy tắc dừng sớm | 4 phút34 giây | 0,599393 | Refit4 epoch và đánh giá |
| A2 expert | 7 | 4 | Cùng quy tắc dừng sớm | 4 phút39 giây | 0,599334 | Refit4 epoch và đánh giá |
| A2 learned | 7 | 4 | Cùng quy tắc dừng sớm | 4 phút31 giây | 0,599310 | Refit4 epoch và đánh giá |
| A3 expert | 7 | 4 | Cùng quy tắc dừng sớm | 4 phút58 giây | 0,599395 | Refit4 epoch và đánh giá |
| A3 learned | 7 | 4 | Cùng quy tắc dừng sớm | 3 phút35 giây | 0,599497 | Refit4 epoch và đánh giá |

Tổng đã chạy51 epoch selection, giữ30 checkpoint qua bảy lượt. Tổng thời gian controller khoảng30 phút. Refit theo các epoch đã chọn tương ứng30 epoch trên train90. Chưa dispatch refit. Dự phòng khoảng0,5–1,5 giờ GPU/vận hành cho đợt refit, calibration và export của corpus nhỏ này, cần nghiệm thu producer trước khi chốt. Thời gian hoàn thiện mã và closed-loop tách riêng.

Sai khác trên selection rất nhỏ. Đây là tập đã dùng chọn epoch, vì vậy chưa thể kết luận đồ thị hoặc CG-AKT tốt hơn trên dữ liệu độc lập.

Nguồn gồm [nghiệm thu A0](../runs/modal-akt-recovery-20261112-01/main60-a0-verification.json), [tổng hợp sáu graph fits](../runs/modal-akt-graph-selected-20261112-01/batch-summary.json) và [chỉ mục checkpoint](../runs/modal-akt-graph-selected-20261112-01/checkpoint-index.json).

## Junyi — thời gian và kết quả thực tế của A0

Train80 có126.774 người học,13.347.331 target. Selection10 có15.847 người học,1.600.343 target,0 OOV. Calibration10 và outer-validation tách riêng khỏi lượt này. Tất cả epoch dùng cùng split, cùng vocabulary717 bài và batch4.

| Epoch A0 | Train đã xử lý | Cập nhật Adam | Train thuần | Validation | Log Loss selection | Trạng thái |
|---|---:|---:|---:|---:|---:|---|
| 1 | 13.347.331 target | 58.166 | 26 phút47,6 giây | 4 phút08,4 giây | 0,359648 | Hoàn tất, có checkpoint |
| 2 | 13.347.331 target | 58.166 | 26 phút35,8 giây | 4 phút23,4 giây | 0,356651 | Hoàn tất, tốt hơn epoch1 |
| 3 | 13.347.331 target | 58.166 | 29 phút13,7 giây | 4 phút26,0 giây | 0,355651 | Hoàn tất, tốt hơn epoch2 |
| 4 | 3.431.632 target ở cuối execution03 | 15.016 | 7 phút34,4 giây | Chưa chạy | Chưa có | Đã giữ checkpoint, execution04 đang tiếp tục |

Mỗi epoch hoàn tất gồm232.662 cửa sổ. Ba epoch cộng validation mất khoảng95 phút35 giây theo bộ đếm pha. Thời gian khởi động, gián đoạn, tải artifact và vận hành nằm ngoài con số này. Thời gian epoch1 được ghép từ các đoạn phục hồi đã ghi nhận. Không cộng lại các counter cumulative của hai execution.

Log Loss lần lượt0,359648→0,356651→0,355651. Epoch3 cải thiện khoảng0,001000 so epoch2. Chưa có checkpoint cuối quá trình hoặc kết quả đánh giá độc lập. Epoch4 dở dang không được tính là một epoch hoàn tất.

Bổ sung [nghiệm thu execution03](../runs/junyi-main-selected-20261112-01/execution03-verification.json) và [mã kiểm](../runs/junyi-main-selected-20261112-01/verify_execution03.py). Snapshot trước execution03 được giữ nguyên tại [snapshot tiến độ](../runs/junyi-main-selected-20261112-01/training-status-20261112.json). Mã [đối chiếu artifact](../runs/junyi-main-selected-20261112-01/build_training_status.py) kiểm SHA archive, số target, history validation và stop acknowledgment.

## Vì sao chưa chốt số epoch còn lại

Giới hạn hiện hành là20 epoch, patience3 và min_delta0,0001. Số20 là trần an toàn. Sau mỗi epoch, mô hình được theo dõi trên selection và dừng khi ba epoch liên tiếp không cải thiện đủ. Nếu epoch tiếp tục tốt lên thì điểm dừng lùi lại.

A0 vừa cải thiện ở epoch3. Vì vậy thời điểm dừng sớm nhất hiện tại là sau epoch6, nếu epoch4–6 đều không cải thiện đủ. Trong trường hợp đó chọn epoch3 và refit đúng3 epoch. Từ mốc hiện tại còn phần còn lại của epoch4, epoch5–6 và3 epoch refit, dự phòng khoảng3–4 giờ GPU/vận hành theo tốc độ đã đo. Refit train90 lớn hơn train80 khoảng12,5% theo tỷ lệ người học, số target thực tế cần đếm trước khi dự báo chính xác.

Nếu epoch4 hoặc các epoch sau cải thiện, cần nhiều thời gian hơn và refit cũng có thể dài hơn. Không cố định trước7 epoch còn lại hoặc áp epoch tốt nhất Grade10 sang Junyi.

## Ước lượng còn lại theo từng phiên bản Junyi

Các khoảng dưới đây là kịch bản lập ngân sách. Sáu bản đồ thị chưa có số đo training toàn Junyi. Tạm giả định tốc độ gần A0, selected dừng sau4–5 epoch và refit1–2 epoch. Giả định này phải cập nhật sau benchmark graph và kết quả selection. A0 có cận dừng sớm riêng từ history đã quan sát.

| Điều kiện | Đã hoàn tất trên toàn Junyi | Epoch còn lại trong kịch bản thuận lợi | GPU còn lại ước lượng | Việc cần trước training |
|---|---|---|---:|---|
| A0 | 3 epoch selected, một phần epoch4 | Gần3 selected +3 refit nếu best giữ ở3 | 3–4 giờ | Tiếp tục checkpoint, hoàn tất selection, chờ freeze trước refit |
| A1 expert | 0 epoch | 4–5 selected +1–2 refit | 2,5–4 giờ | Admission graph và kiểm CUDA producer |
| A1 learned | 0 epoch | 4–5 selected +1–2 refit | 2,5–4 giờ | Hoàn tất topology learned train-only, admission và CUDA |
| A2 expert | 0 epoch | 4–5 selected +1–2 refit | 2,5–4 giờ | Confidence train-only, nối producer và kiểm CUDA |
| A2 learned | 0 epoch | 4–5 selected +1–2 refit | 2,5–4 giờ | Topology/confidence train-only, producer và kiểm CUDA |
| A3 expert | 0 epoch | 4–5 selected +1–2 refit | 2,5–4 giờ | Cùng confidence A2, thêm gate, kiểm fallback và CUDA |
| A3 learned | 0 epoch | 4–5 selected +1–2 refit | 2,5–4 giờ | Cùng topology/confidence A2, thêm gate và kiểm CUDA |

Tổng Junyi còn lại làm tròn khoảng18–28 giờ GPU trong kịch bản thuận lợi, bao gồm khoảng dự phòng nhỏ. Đây là bản cập nhật khoảng18–24 giờ đã trao đổi, có xét A0 vẫn cải thiện ở epoch3 và refit train90. Dự phòng24–48 giờ khi cần thêm epoch hoặc graph chậm hơn. Nếu phải chạm20 epoch ở nhiều điều kiện thì có thể vượt cả khoảng dự phòng, phải dự toán lại trước khi chạy tiếp.

Khoảng2–3 ngày hoàn tất toàn bộ là mục tiêu thuận lợi, phụ thuộc mã Junyi A2/A3, confidence/topology và producer refit sẵn sàng song song. Đây chưa là cam kết tiến độ. Calibration, xuất dự báo và đánh giá cuối cần thêm thời gian đo riêng. Full5-fold, thêmseed và closed-loop không nằm trong tổng giờ này.

## Việc tiếp theo để giảm thời gian và bảo vệ30USD

1. Đã đo batch4/8/16/32 trên cùng packet đã được duyệt. Bốn trường hợp đều được nghiệm thu, số đo và figure ở bundle `junyi-batch-throughput-20261112-01`. Giữ kết quả theo target/giây, padding, VRAM và chi phí, kèm kiểm checkpoint.
2. Nếu tăng batch, cập nhật quyết định protocol và kiểm tính so sánh trước khi áp dụng. Batch lớn hơn làm thay đổi số cập nhật Adam mỗi epoch, nên tốc độ cao hơn chưa xác định được tổng số epoch cần học.
3. Hoàn tất confidence/topology Junyi và producer A2/A3 trong lúc A0 tiếp tục. Reuse cache và phần lifecycle đã nghiệm thu.
4. Hoàn tất toàn bộ selected candidates, freeze quyết định, sau đó refit theo epoch đã chọn. Giữ tập calibration và independent evaluation đúng vai trò.
5. Chỉ dispatch trong ngân sách dự án30USD còn khả dụng theo ledger. Chưa có bảo đảm toàn ma trận vừa ngân sách với tốc độ batch4 hiện tại.

Các artifact lớn giữ tại `experiments/akt/results/<run-id>/`, bằng chứng và chỉ mục nhỏ tại `research_tracking/runs/`. App execution03 đã dừng, archive2.129.675.285byte đã được kiểm. Execution04 tiếp tục cùng A0 từ checkpoint epoch4 bước15.016. Bộ điều khiển hữu hạn có thể nối05/06, mỗi lượttrần0,85USD, tổngba lượt04–06tốiđa2,55USD đã preallocate trongtrần30USD. Lần nối04đầu dừng local do nhãnreview sai trướcbilling/GPU, đã giữfailurelog/request và sửa đúng hợpđồng, cóASTcontractcheck. Khôngrefit, graphfit hoặcHoldout trongbộđiềukhiển này.
