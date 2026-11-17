# Bàn giao đầu ra training KLTN · 17/11/2026

## Đọc trước

Đã có model và kết quả đánh giá độc lập cho bốn điều kiện AKT Junyi expert. Kết quả này hỗ trợ phân tích dự báo của RQ1/RQ3. Hoàn thành RQ3 còn cần quyết định học và vòng kín Grade10. Các đối chứng còn lại vẫn được giữ theo protocol.

Kết quả hiện tại chưa phát hiện ưu thế rõ của các bản graph sau calibration trên Junyi outerfold4. Kết luận được giới hạn theo population và thiết kế đã kiểm, với độ bất định trình bày bên dưới.

Mở các ZIP từ thư mục gốc của bản checkout để giữ đường dẫn repository. Mỗi ZIP mới có HANDOFF_MEMBER_INVENTORY.json, ghi đường dẫn, dung lượng và SHA-256 từng file. Bộ nhận cần kiểm SHA trước sử dụng. Dùng .venv riêng, nạp .pt/.pkl chỉ khi tin cậy nguồn. Giữ nguyên outputs cũ và tạo run mới cho phần tiếp tục.

## Toàn bộ nhóm đầu ra đã định vị

| Nhóm | Đã thực hiện | File bàn giao | Giới hạn/phần tiếp tục |
|---|---|---|---|
|BKT · Junyi|CV5 gồm 3.537 lượt fit theo exercise/fold; refit cuối 720 exercise|720 .pkl; hệ số CV trong cv.json; prediction Parquet; manifest, log, metric và Test lịch sử|Giữ baseline lịch sử. Test đã được truy cập từ trước; không dùng để chọn model mới.|
|GAM-KT · Junyi|CV5 hoàn tất; 5 bộ difficulty theo fold|difficulty.parquet/json; prediction Parquet, coverage, bảng metric, log và so sánh BKT|Chưa xác nhận refit cuối/Test. Fit matched theo protocol mới còn thiếu.|
|Graph-GAM-KT · Paper2|Có source online và bảng kết quả đã đóng băng|Gói Paper2 gốc, cấu hình, kết quả replay/vòng kín và thống kê đã lưu|Chưa tìm thấy checkpoint offline độc lập. Cần lifecycle matched hiện hành.|
|AKT · Junyi expert|A0–A3 đủ chọn epoch, refit, calibration và outer fold4|4 checkpoint selected + 4 refit .pt; SUPPORT/config; 4 calibrator; dự đoán raw/calibrated, metric, bootstrap/Holm, telemetry và figure|Mỗi model chạy 12 epoch selection, chọn epoch9 rồi refit9. Tổng84 epoch đã thực thi cho bốn điều kiện này. Một fold, một seed.|
|AKT · Grade10|7 checkpoint selected; epoch chọn 5/5/4/4/4/4/4|A0; A1/A2/A3 × expert/learned, .pt + index + support/config|Chưa refit/calibration/đánh giá vòng kín chính. Bảy refit sẽ dùng tổng30 epoch đã chọn, sau khi đủ gate chung.|
|SAKT · Grade10 engineering|6 epoch, chọn epoch1 trên cohort10 người học|state.pt, selected-terminal, epoch logs, selection predictions và coverage|Chưa là baseline nghiên cứu Main60 hoặc Junyi. Không tính lượt nhỏ này là đã xong model đối chứng.|
|GKT · Grade10 engineering|11 epoch, chọn epoch6 trên cùng cohort10 người học|state.pt, selected-terminal, epoch logs, selection predictions và coverage|Main60 và Junyi còn thiếu. Là biến thể theo phương trình gốc, chưa chứng nhận khớp code tác giả.|
|Confidence cạnh · Junyi TRAIN80|Đã fit 976 cạnh; 708 có support, 268 thiếu support|confidence.json, COMPLETE, identity, fit-manifest, phiên bản runtime, OOF, child fit ledger và log|Score ổn định dự báo có điều kiện. OOF/fit ledger giữ để audit; SQLite đầu vào phái sinh giữ local và có manifest tái dựng.|
|Paper1 · Grade10|Source mô phỏng và kết quả công bố làm nền RQ1/RQ2|Notebook tiền kết quả và PDF chính thức; Elo cập nhật online|PDF là nguồn chuẩn. Không tính đây là checkpoint neural offline.|

## AKT hiện tại đóng góp gì cho ba RQ?

- **RQ1.** Junyi cho thấy lợi ích dự báo của đồ thị rất nhỏ. Sau calibration, ba bản graph so với A0 chưa có cải thiện Log Loss/Brier đáng tin cậy sau Holm. Cần tiếp chuỗi ngưỡng mastery → ready set → chọn bài → kết quả học để xác định nơi ảnh hưởng bị mất.
- **RQ2.** Các chẩn đoán Paper1/2 đã kiểm ba bẫy đánh giá. Bốn model expert hiện tại bổ sung benchmark một điều kiện graph; chưa bao phủ đủ chất lượng đồ thị, lịch sử, profile và thưa dữ liệu. Sensitivity/noise trên checkpoint cố định có thể thực hiện trước khi cân nhắc training thêm.
- **RQ3.** A0 không graph, A1 graph cố định, A2 confidence từng cạnh, A3 confidence+cổng đã so sánh dự báo độc lập. A3 so A0 sau calibration có ΔLogLoss≈−0,000020, CI95% chứa0; chưa kết luận tốt hơn. Chưa có kết luận chính về ổn định, quyết định lộ trình và vòng kín. Bằng chứng âm được giữ nguyên.

Các kết quả outer dùng39.616 người học/4.137.050 target,144 OOV giữ null, cùng population mỗi model. Phân tích thống kê được khóa family sau inference nhưng trước xem metric outer; báo exploratory, mộtfold/mộtseed. Không quy kết cải thiện học thực từ log quan sát.

## Phạm vi training còn lại theo protocol hiện hành

Đối chiếu Protocol21 đã adopt và bảng rà phạm vi15/11. Có **15/36 phase neural chính đã có bằng chứng** gồm8phase Junyi expert và7selected Grade10. Một phase là selected-fit hoặc refit; số này không đo phần trăm hoàn thành RQ hay toàn KLTN.

| Phần còn thiếu | Phase selected-fit/refit | Mục đích nghiên cứu |
|---|---:|---|
| Junyi learned-graph A1/A2/A3 |6|Kiểm kết luận có phụ thuộc cách xây đồ thị từ dữ liệu hay không; predictive evidence có giới hạn thứ tự luyện quan sát|
| Junyi SAKT/GKT |4|Đối chứng KT bổ sung theo đề cương, cùng ranh giới thông tin|
| Grade10 bảy điều kiện AKT đã chọn |7|Tạo bản refit cho calibration, quyết định lộ trình và vòng kín trên môi trường biết cạnh thật/nhiễu|
| Grade10 SAKT/GKT main |4|Hoàn tất đối chứng cùng cohort và gate đầy đủ trước refit/evaluation chính|
| Tổng |**21**|Chưa gồm matched GAM/Graph-GAM, ước lượng graph/confidence bổ sung, calibration và inference|

Đề xuất hoãn sáu phase Junyi learned-graph trong báo cáo15/11 **chưa được áp dụng**. Nhận định trước rằng chỉ còn Grade10 là hết AKT thiếu phần này. Giữ đầy đủ nghĩa vụ hiện hành trong bàn giao. Gate chọn chung chín ứng viên Grade10 còn cần SAKT/GKT main trên cohort phù hợp. Không tự lấy engineering10 thay main60.

## Ưu tiên tính đúng của kết quả

Rà phạm vi ngày18/11 xác nhận các hướng nghiên cứu chính tiếp tục bám baRQ. Mục tiêu nghiệm thu là phép so sánh đúng, đủ đối chứng và artifact để báo cáo. Kết quả âm hoặc bất định được giữ. Outer Junyi đã xem, mọi thiết kế thay đổi từ đây cần ghi thời điểm và địa vị hậu kiểm/thăm dò.

Mỗi RQ được kết luận theo mức độ bằng chứng, độ lớn hiệu ứng, bất định và điều kiện áp dụng. Có thể kết luận hỗ trợ một phần, chưa thấy khác biệt rõ hoặc cần thêm bằng chứng. P-value và dấu hiệu ứng là những phần của diễn giải cùng cơ chế và đối chứng.

Con số21phase là backlog theo ma trận triển khai nhóm đã adopt. Đề cương chưa bắt buộc tích đầy đủ mọi model×graph×environment. Nhánh learnedJunyi còn giữ trong backlog, đề xuất giảm phạm vi chưa áp dụng. Ưu tiên nghiên cứu là khép chuỗi mastery→chọn bài→vòng kín Grade10 và ba bẫy, cùng các đối chứng yêu cầu; các tối ưu tài nguyên bổ sung cần có lợi ích cụ thể đối với lượt thực nghiệm cần thiết.

Các giới hạn phải bàn giao gồm A0 validation batch1 lịch sử chưa replay ranking đủ12epoch, A3 refit mixed hardware, mộtfold/mộtseed và family thống kê khóa sau inference nhưng trước xem metric. Hồ sơ chi tiết nằm ở SCOPE_AND_RESULT_INTEGRITY_REVIEW_20261118.md trong gói bằng chứng. Kết quả hiện hành chưa chứng minh tương đương model, hiệu quả dạy học thực hoặc nguyên nhân duy nhất của việc graph chưa giúp.

## Kết quả dự báo đã có

BKT/GAM là trung bìnhCV5 lịch sử; AKT là một outerfold4 với partition/refit hiện hành. Hai bảng phục vụ định vị bằng chứng; chưa dùng chênh lệch giữa hai protocol làm kết luận xếp hạng cùng điều kiện.

| Baseline lịch sử | AUC | Log Loss | Brier |
|---|---:|---:|---:|
|BKT CV5|0,783413|0,375607|0,115105|
|GAM-KT CV5 supported|0,774866|0,394881|0,120372|

| Junyi outer sau calibration | AUC | Log Loss | Brier |
|---|---:|---:|---:|
|A0|0.804765|0.360453|0.110202|
|A1|0.804778|0.360444|0.110199|
|A2|0.804769|0.360453|0.110201|
|A3|0.804775|0.360433|0.110192|

## Tải đầu ra và bằng chứng

- [Thư mục gốc KLTN trên Drive Sang](https://drive.google.com/drive/folders/1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7)
- [Gói bàn giao toàn bộ nhóm model bổ sung và chỉ mục hiện hành](https://drive.google.com/drive/folders/1P4if7AujsuG3ujRFro4BVl5ozO_eRQMb)
- [Model AKT selected/refit, Grade10, audit và helper nối các phần ZIP](https://drive.google.com/drive/folders/1--Q-yO2ja7q2RwWWfyv6nDtw80PDrnyZ)
- [Junyi outer A0–A3, raw/calibrated predictions, source đã pin, calibrator và figure](https://drive.google.com/drive/folders/1-GKHCBGtqFLiL-Zi84onLbLHl_iR0Fk-)
- [Lịch sử training/recovery đã sao lưu và kiểm SHA trước dọn local](https://drive.google.com/drive/folders/1V-H0estsyh2oQQ3qnfapU9qSpGZFoF3H)

Các ZIP AKT lớn đã chia phần. Dùng DRIVE_PARTS_MANIFEST.json và restore_drive_zips.py trong thư mục backup để nối và kiểm checksum trước giải nén. Bản A0_BEST_SO_FAR epoch5 là lịch sử bị thay thế, không chọn lại làm model chính. Dùng Junyi refit9 cho calibration/outer, selected9 để truy vết chọn epoch. Junyi và Grade10 có vocabulary khác nhau, cần checkpoint tương ứng.

| Archive mới | File thành viên | Byte nguồn | Byte ZIP | Trạng thái |
|---|---:|---:|---:|---|
|[BKT_cv_cpp_01.zip](https://drive.google.com/file/d/1kIOozhPXpwATkKOumKK9yJNsZnc6CkTk/view?usp=drivesdk)|3547|158,983,718|154,083,657|SHA256 Drive khớp|
|[BKT_final_cpp_01.zip](https://drive.google.com/file/d/1VTW6A4h09_p_wzNRVTGCrAASVk3PjkDm/view?usp=drivesdk)|723|6,464,166|3,131,273|SHA256 Drive khớp|
|[BKT_test_cpp_01.zip](https://drive.google.com/file/d/1IXWGWNKbzTZf-0EObzVQfJ4U42EhI2jX/view?usp=drivesdk)|1449|91,637,967|90,846,568|SHA256 Drive khớp|
|[BKT_benchmark_01.zip](https://drive.google.com/file/d/1hmmFcUMWrjgG79fYn03mKdqrU2dJa-Pr/view?usp=drivesdk)|55|44,264,000|9,658,478|SHA256 Drive khớp|
|[BKT_cv_cpp_smoke_01.zip](https://drive.google.com/file/d/156bLEcSmllF92ATVCEqp7skeHnepCWSe/view?usp=drivesdk)|9|297,936|268,126|SHA256 Drive khớp|
|[GAM_KT_CV5_01.zip](https://drive.google.com/file/d/1NuS3NG6OlGzuTnch_m1Njo5WRzjHurqh/view?usp=drivesdk)|389|188,658,896|182,237,414|SHA256 Drive khớp|
|[GAM_KT_CV5_02.zip](https://drive.google.com/file/d/1G67C6A_E8T1F7XhFYHL0pOB4zHw54PIm/view?usp=drivesdk)|73|35,591,471|35,566,927|SHA256 Drive khớp|
|[SAKT_ENGINEERING_ONLY_01.zip](https://drive.google.com/file/d/1tgoXazwTvLeZCgQwtPjXYsnax0Sdt95M/view?usp=drivesdk)|38|7,810,857|6,956,848|SHA256 Drive khớp|
|[GKT_ENGINEERING_ONLY_01.zip](https://drive.google.com/file/d/1qdGkZ4d3erw34XITkblH35WSNd-2XOBb/view?usp=drivesdk)|38|2,355,491|1,874,040|SHA256 Drive khớp|
|[PAPER2_LEGACY_01.zip](https://drive.google.com/file/d/1-ANin7qn4BD7hQBVVyDKiO7YLaC09W2W/view?usp=drivesdk)|1|3,835,888|3,826,974|SHA256 Drive khớp|
|[PAPER1_LEGACY_01.zip](https://drive.google.com/file/d/1Mw_lpuCiMlbTLVTTaM9yYl8AroKqmq9r/view?usp=drivesdk)|2|972,220|626,458|SHA256 Drive khớp|
|[JUNYI_TRAIN80_CONFIDENCE_AUDIT_01.zip](https://drive.google.com/file/d/1daTmQ0I-Xw8mlx206UJBdtkKetFhw7kx/view?usp=drivesdk)|25|1,039,089|256,559|SHA256 Drive khớp|
|[SOURCE_PROTOCOLS_01.zip](https://drive.google.com/file/d/1f0refT7gxZAv_457JQEEVoeyjoyEbV0O/view?usp=drivesdk)|708|7,968,723|2,820,976|SHA256 Drive khớp|
|[CONFIDENCE_OOF_FIT_LEDGER_01.zip](https://drive.google.com/file/d/1C-J2C8S0yd1U7VZR1IsQfuYaV-T_UJQ9/view?usp=drivesdk)|666|167,054,640|164,378,389|SHA256 Drive khớp|
|[CONFIDENCE_OOF_FIT_LEDGER_02.zip](https://drive.google.com/file/d/1Ux-vv70HGaQgJSH5oJ2nPeKf_QWP1-SR/view?usp=drivesdk)|465|149,005,416|146,545,165|SHA256 Drive khớp|
|[CONFIDENCE_OOF_FIT_LEDGER_03.zip](https://drive.google.com/file/d/1_LTEGZPSdf7awcMq3w7KiCJQrYxiPHsu/view?usp=drivesdk)|696|167,449,351|164,198,561|SHA256 Drive khớp|
|[CONFIDENCE_OOF_FIT_LEDGER_04.zip](https://drive.google.com/file/d/1F63y81KzLuPPZQW_cg5acuBQfrHmQMqJ/view?usp=drivesdk)|381|99,497,475|97,145,830|SHA256 Drive khớp|

## Những gì người tiếp tục cần chuẩn bị

1. Checkout source và đọc AGENTS.md, docs/REPOSITORY_MAP.md, Protocol21/Recipe26. Gói SOURCE_PROTOCOLS giữ source đang dùng, cấu hình và tests. Frozen-source trong gói outer giữ bản thực thi chính xác của outer; phải dùng source đó khi tái lập outer.
2. Giải nén model kèm SUPPORT.zip, MODEL_INDEX và calibration tương ứng. Các chỉ mục trong bộ hồ sơ định vị graph, encoding, roles và run nguồn. Không dùng .pt đơn lẻ rồi tự dựng vocabulary khác.
3. Muốn train tiếp phải có canonical Junyi, learner assignments và graph inputs đúng SHA theo manifests. Gói này bàn giao **đầu ra training**. Dataset gốc, SQLite/cache trung gian và môi trường .venv không được nhân bản trong đợt này; người nhận cần chuyển dữ liệu đầu vào hợp lệ riêng hoặc tái dựng theo pipeline rồi kiểm SHA. Không gọi gói này là bản sao toàn project có thể chạy ngay khi chưa nghiệm thu data dependencies.
4. Tài khoản Modal/OAuth, token và quyền Drive được cấp riêng cho người nhận. Chủ Drive cần chia sẻ thư mục gốc KLTN cho người tiếp tục để truy cập cả model backup, outer và gói mới. Các URL được kiểm bằng tài khoản chủ Sang; chưa kiểm quyền bằng tài khoản người nhận.
5. Ưu tiên hoàn tất gate/main comparator Grade10, refit/calibration rồi chạy chuỗi quyết định/vòng kín. Giữ matched GAM/Graph-GAM và nghĩa vụ learnedJunyi trong backlog. Mỗi lượt mới pin đầu vào/source/budget trước chạy; CPU local/miễn phí, GPU chỉ dùng khi cần.

## Nguồn đối chiếu

- docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md và26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md.
- docs/bkt-baseline-results.md; cv_cpp/cv/cv.json; final_cpp/final.json.
- experiments/gam_kt/results/wsl_cpp/cv/cv.json vàreport_vi.md.
- MODEL_INDEX các model-export; baseline-evaluation-readiness-20261117-01/EXISTING_ARTIFACTS.json.
- junyi-outer-real-20261117-01/OUTER_COMPARISON01.json, thống kê/Drive acceptance; TRAINING_SCOPE_RECONCILIATION_20261115.md.
- PACKAGE_INVENTORY01.json và NEW_ARCHIVES_DRIVE01.json là inventory/biên nhận của đợt này.
