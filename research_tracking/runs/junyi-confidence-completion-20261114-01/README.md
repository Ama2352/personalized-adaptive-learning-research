# Confidence TRAIN80 và A2 Junyi — đã hoàn tất selected-fit ngày 14/11

## Kết quả đã nghiệm thu

A2 đã học 12 epoch trên đủ 13.347.331 target TRAIN80 mỗi epoch, chọn checkpoint epoch 9 và xuất đúng 1.600.343 dự đoán của 15.847 người học selection. Đã kiểm target/order, xác suất, checkpoint, Adam và RNG. Hai lượt H100 đã dừng trước khi thu artifact. Lượt cuối có 210 file, 2.925.030.322 byte, archive đã đối chiếu. Gói model bốn file giữ một checkpoint .pt tại `experiments/akt/results/model-export-a2-batch128-20261114-01/`.

- `a2-final-acceptance.json` và `a2-export-result.json` là điểm kiểm A2 và model.
- `a2-selection-metrics.json` giữ AUC 0,805993, Log Loss chuẩn 0,353567, Brier 0,107698 và ECE 0,004138 từ hàm chấm dùng cho GAM-KT.
- `a2-comparison-audit.json` giữ cùng quần thể/cấu hình học A0–A2 và giới hạn A0 chưa replay đầy đủ ranking epoch bằng batch128.
- `a2-final-performance.json` ghi 47 phút 19 giây trong hai function GPU, trung bình train 3 phút 03 giây/epoch, 1.320 mẫu NVML trung bình 32,23%, VRAM đỉnh 5.789 MiB. Mục tiêu GPU trên 50% chưa đạt.
- `figures/` giữ SVG, PNG, CSV và manifest. `build_a2_selection_figure.py` dựng lại sang prefix/thư mục mới, theo quy ước figures4papers đã lưu.
- `a2-report-verification.json` giữ kiểm HTML/ID và quan sát PNG. Hai báo cáo GVHD tại `research_tracking/supervisor_reports/2026-11-10/01_tien_do/` đã cập nhật.

## Phạm vi kết luận và bước sau

Đã hoàn tất selected-fit của A2 trên Development outer fold 4, một seed. Điểm chọn checkpoint A0/A1/A2 lần lượt 0,35358018/0,35356185/0,35356694, là quan sát mô tả trên selection. A3, refit/calibration, đánh giá độc lập, kiểm quanh ngưỡng và mô phỏng vòng kín còn chờ. Không suy ra lợi ích đồ thị hoặc RQ3 đã hoàn tất từ các điểm này.

CPU chuẩn bị và tải/nén đã tách khỏi thời gian thuê GPU. Tăng mức CPU bảo đảm lên 2 vCPU ở lượt tiếp tục chưa có đối chứng xác nhận tăng tốc. Billing sau training ghi 19,09665620 USD metered toàn workspace, billed bằng 0. Ledger giữ cận lịch sử 25,22710605 USD và dự phòng 3 USD. Phải đối soát cận cũ trước một allocation A3 2,60 USD, giữ trần toàn KLTN 30 USD.

Hồ sơ này đã niêm phong. Dùng STATE để đọc điểm tiếp tục, tạo bundle mới khi phát sinh công việc mới. Giữ nguyên các log lỗi, source và checkpoint lịch sử.

## Lịch sử triển khai được giữ nguyên bên dưới


## Phạm vi

Tiếp tục theo yêu cầu người dùng sau đợt kiểm T4. Corpus đầu vào ở `artifacts/akt/confidence/full-train80-20261114-02/`, dùng đúng request và source identity của lượt trước. Đợt trước đã lưu đủ 232.662 record và 13.347.331 target nhưng chưa niêm phong. Các artifact cũ được giữ để truy vết.

Bước hiện hành gồm kiểm/niêm phong corpus, crossfit confidence theo người học TRAIN80, build cache CPU train/selection, kiểm đối chiếu dữ liệu/cấu hình A0/A1 và chuẩn bị Gate cho training A2/A3. Dùng `.venv` trong repository. Models, corpus, cache và OOF lớn nằm trên ổ D.

## Nguồn và ranh giới dữ liệu

Request gốc ở `../junyi-confidence-train80-20261114-01/request.json`. Đã đối chiếu toàn bộ source pin trong `IDENTITY.json` và đều khớp khi tiếp tục. Confidence chỉ fit TRAIN80 của Development outer fold 4. Selection10, calibration10, outer validation và Holdout nằm ngoài fit confidence. Method24, seed42, ba fold người học và 200 bootstrap giữ theo recipe đã chốt.

Độ tin cậy đo mức ổn định của lợi ích dự báo có điều kiện theo cạnh. Cần kiểm bằng thực nghiệm độc lập để diễn giải hiệu quả đồ thị. Mọi lý do thiếu hỗ trợ thống kê và lỗi tài nguyên phải được ghi riêng.

## Log và phục hồi

`spool-resume01.log` giữ lượt tiếp tục corpus. Output gốc giữ SQLite, IDENTITY, SPOOL_COMPLETE, controller telemetry và checkpoint COMPLETE theo từng child. `STATE.json` của bundle này giữ trạng thái tiếp tục. Các bước fit tiếp theo có log riêng. Chỉ finalize khi đủ child và toàn SHA/lineage khớp.

## Kết quả và phần còn thiếu

Corpus đã niêm phong, cache selection đã kiểm đầy đủ và source mới đạt 2.614 ca Linux. Confidence đã fit đủ 736 child và hoàn tất kiểm toàn vẹn. Đọc `STATE.json` để biết tiến độ thật. Confidence hoàn chỉnh và cache graph thật còn cần hoàn tất trước training chính A2/A3.

## Cập nhật lúc tiếp tục

Corpus đã niêm phong, đủ13.347.331target và232.662record. Xem `spool-acceptance.json`. CLI batch mới gọi nguyên hàm main của CLI cũ trong cùng process, giữ source pin thống kê. Pilot4child đạt và6marker cũ giữ nguyênSHA, xem `batch-pilot-acceptance.json`. Resource cap350.000row/child bao phủ mức lớn nhất301.489row; RAM tối đa768MiB có giám sát toàn cây process. `progress.jsonl` và STATE giữ tiến độ thật.

Cache selection mới ở `artifacts/akt/window-cache/full-selection10-staged-20261114-02/`, được xây bằng reader Parquet của `inputs.paths`, có1.600.343target và populationSHA khớpA0. `selection-cache-acceptance.json` và `selection-admission-acceptance.json` giữ kiểm đầy đủ. Lượt01 bị chặn vì truyền cache đầy đủ vào reader chỉ nhận cohort kỹ thuật nhỏ; output dở được giữ. Đã sửa cùng lỗi tại `prepare_junyi_staged_caches.py`.

Gate Linux CPU01 giữ2613ca đạt và1ca lỗi so sánh loss tuyệt đối của CLI recovery, chênh1,78813934e-7, source nguyên byte. App đã dừng, ZIP đã tải và kiểm. `linux-cpu-settlement01.json` đóng cap0,15USD theo cận bảo thủ. Cấu hình CPU của fixture trước đó chưa ghim deterministic/luồng. Kiểm local source cũ một ca đạt, nên nguyên nhân nền tảng vẫn là giả thuyết cần kiểm trên Linux. Fixture mới ghimCPU1luồng và deterministic, giữ nguyên phép so sánh bitwise và code training thực nghiệm.

## Gate Linux đã đạt

Lượt02 với fixture CPU một luồng và deterministic giữ nguyên so sánh bitwise đã đạt 2.614 ca, 0 lỗi hoặc skip trong 183,737 giây worker. Giữ failure01, kết quả local nguồn cũ và kiểm local fixture mới. `linux02/` ghim source ZIP cùng báo cáo, settlement và controller của lượt02. Hai App đã dừng, artifact ZIP đã tải và đối chiếu. Tổng cap hai lượt CPU 0,30 USD được cộng theo cận bảo thủ vào ledger, chi phí riêng thực tế chưa tách được. Confidence tiếp tục local, chưa training chính A2/A3.

## Dependency và request để chuẩn bị snapshot

`runtime-lock-verification.json` đối chiếu cùng SHA lock giữa T4, Gate Linux và file local trên D. `upstream-portable-inventory.json` ghi checkout AKT sạch, đúng commit và file LF, chuẩn bị riêng vì mount artifacts của worker sẽ che bản dependency sẵn trong image. Git objects được sao chép/đối chiếu trước checkout, không thay source upstream gốc. Checkout khoảng 94 MB gồm các tệp công khai kèm repo để Git xác minh sạch.

`prepare_worker_inputs.py` chỉ tạo request khi COMPLETE confidence thật hiện diện và khớp SHA. `assemble_stage_requests.py` chỉ ghép khi có cache đầy đủ, kèm upstream và các SHA nguồn/đích. Reflog và hooks của Git được loại khỏi gói chuyển. Hai helper này còn chờ chạy trên artifact hoàn chỉnh. Sau tạo snapshot phải kiểm lại checkout ngay trong snapshot trước khi cấp GPU.

## Confidence thật đã hoàn tất

`confidence-acceptance.json` và `CONFIDENCE_MANIFEST.json` ghim artifact cuối. Toàn bộ 736 child, 976 cạnh, 11.807.185 row có child được fit từ corpus đã duyệt đủ 13.347.331 target. Có 708 cạnh supported, 268 unsupported; 700 trọng số dương và 276 bằng 0. Không có solver exception. Supported chưa đồng nghĩa trọng số dương hoặc cạnh tiên quyết thật. `confidence-weight-summary.json` giữ thống kê mô tả; artifact chưa chứng minh A2/A3 cải thiện kết quả nghiên cứu.

Lượt batch02 dừng đúng cap 3.600 giây sau 455 child. Lượt batch03 hoàn tất 281 child còn lại trong 1.896,390 giây, tái dùng checkpoint cũ. `child-audit-final01.log` kiểm đủ mọi SHA/lineage/coverage. `finalize01.log` ghi công bố confidence thành công. Artifact lớn, summary và OOF được giữ nguyên tại output trên D. Hiện chạy `prepare_junyi_staged_caches.py` trên confidence thật, output `artifacts/akt/graph-context-cache/full-train80-staged-20261114-01/`; cache còn cần nghiệm thu.

## Nghiệm thu snapshot A2 và bắt đầu lượt chạy có giới hạn

Bốn cache CPU thật đã hoàn tất, gồm 13.347.331 target train và 1.600.343 target selection cho mỗi biến thể. Snapshot A2 phiên bản02 đã kiểm đủ 1.491 file, đúng checkout AKT upstream và inventory giữ nguyên sau kiểm Git. Lượt01 giữ bằng chứng lỗi thiếu thư mục Git refs trong gói file-only. Lượt02 bổ sung một ref công khai trỏ đúng commit đã ghim.

`a2-snapshot-dependency-verification02.json` giữ nghiệm thu. `a2-training-request01.json` dành tối đa 2,60 USD cho một H100, watchdog 1.860 giây, tối đa một container và không retry tự động. Ledger giữ cận tổng dự kiến 25,8794 USD gồm dự phòng 3 USD. Runner đọc billing thật trước cấp GPU. Đã gọi entrypoint upload rồi training, chưa xác nhận GPU bắt đầu tại mốc ghi này. Log ở `a2-training01.log`, output dự kiến `experiments/akt/results/modal-junyi-a2-staged-h100-20261114-01/`.

## Điều chỉnh triển khai Modal trước epoch đầu

Lượt01 bị SDK chặn vì một Volume gắn nhiều mount. Lượt02 bị chặn do copy layer sau local runtime mount. Lượt03 không mount được vào thư mục artifacts còn file. Lượt04/05 giữ lỗi dựng image CPU do rename trên overlay và cú pháp multiline của run_commands. Lượt06 kiểm CPU bắt thiếu configs trong source image. Lượt07 kiểm toàn SHA trên Volume quá180giây, H100 chưa được gọi. Mọi App cũ đã có xác nhận dừng. Các lượt02–07 giữ settlement riêng trong ledger; số tiền đóng là cận bảo thủ, chưa phải chi thực tế.

Đường thực thi sửa dùng một image chứa toàn bộ snapshot, dựng trên CPU, rồi kiểm đủ1.491file và dependency trên CPU provider trước gọi H100. GPU đọc cache từ image local, chỉ gắn Volume output. Source numerical, dữ liệu, confidence, cấu hình học và Gate trong snapshot giữ nguyên byte. Controller local sửa riêng, các kiểm hợp đồng mới nhất đạt39ca. `provider-preparation-manifest01.json` ghim source controller, tests và các log đã kết thúc. Lượt08 đang chuẩn bị image, chưa có kết quả epoch tại mốc này.

## A2 đã bắt đầu training thật

Source03 sửa đường dẫn runtime đạt Gate Linux 2.615 ca. Snapshot03 giữ cùng worker request, confidence, data và numeric profile, qua nghiệm thu CPU và checkout. Lượt09 CPU provider đạt 9,5268 giây, gồm 4,6607 giây SHA. Đã xác nhận CUDA và 600 bước epoch1 bằng telemetry, xem `a2-remote-progress.jsonl`. Một H100 với cap2,60USD; chờ kết thúc, stop acknowledgement và thu đủ artifact trước khi đóng lượt.

## Nghiệm thu lượt09 và tiếp tục lượt10

Lượt09 hoàn tất7epoch trên toàn TRAIN80, mỗi epoch13.347.331target và1.600.343target selection,0OOV. `a2-tranche09-acceptance.json` xác nhận125artifact/1.215.327.363byte đã tải và đối chiếu, checkpoint epoch007 nạp CPU được, tensor hữu hạn, Adam và Python/NumPy/Torch/CUDA RNG đầy đủ. Chưa đạt điều kiện dừng selected-fit. Đã tiếp tục từ epoch8 bằng cùng snapshot03 và checkpoint epoch007, không lặp lại7epoch cũ.

`a2-tranche09-performance.json` ghi21phút26giây train gồm checkpoint định kỳ,4phút59giây selection,41giây khác trong function,768mẫuNVML trung bình32,4375%, VRAM đỉnh5.789MiB. Lượt này chưa đạt mục tiêuGPU trên50%. Cache đúng về số học trong kiểm T4 trước đó, nhưng chưa có đối chứng full-epoch chứng minh tăng tốc mạnh. Chuẩn bị và tải/nén artifact ở ngoài thời gian thuê GPU đã hoạt động thực tế.

Lượt10 dành2vCPU thay mức bảo đảm0,25vCPU, giới hạn vẫn4vCPU, cùng2luồngTorch và numeric recipe. Đây là quyết định tài nguyên của agent dựa trên mẫuCPU115,5% một lõi, chưa có đối chứng xác nhận lợi ích. `a2-resume-resource-choice10.json` ghim controller và lý do. Giới hạn2,60USD/lượt và cận toàn dự án29,0542USD gồm3USD dự phòng vẫn dưới30USD. Billing trước lượt10 ghi17,59665434USD metered, khác cận dự phòng bảo thủ.

Collector local mới giữ file tạm ở root đợt tải để tránh đường dẫn recovery dài trên Windows. Các file của lượt trước có cùng SHA/bytes được sao chép từ bản đã nghiệm thu trênD, tránh tải lại qua mạng.41ca local đạt, gồm đường dẫn dài và không gọi remote reader cho file trùng. Source numerical trong image/Gate giữ nguyên. Checkpoint/predictions/logs lớn giữ tại output theo run; đọc STATE để biết lượt hiện hành.
