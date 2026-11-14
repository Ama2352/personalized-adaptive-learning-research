# Hoàn tất confidence TRAIN80 và chuẩn bị A2/A3 — 14/11/2026

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
