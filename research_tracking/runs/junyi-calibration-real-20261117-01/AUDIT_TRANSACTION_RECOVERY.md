# Recovery audit CPU bằng transaction — 17/11/2026

## Bottleneck đã xác minh ở mức synthetic

Hàm prediction._expected_insert gốc tạo expected table rồi gọi executemany theo learner, chưa có transaction bao ngoài. Trên DuckDB file local,400rows cùng dữ liệu mất0,510giây với autocommit và0,102giây khi bao BEGIN/COMMIT, nhanh khoảng5,00lần. SHA các hàng logical giống hệt, WAL lần lượt91.517 và17.690bytes. Tổng801rows synthetic bao gồm warmup. Đây là đo localdisk, chưa phải hệ số tăng tốc ModalVolume/fullcohort.

A0/A1 thực đã ghi đầy đủ1.621.484rows và15.847Parquet/learners theo RAW_RECOVERY_ADMISSION01.json lúc12:02:27. Audit vẫn ghi WAL. Probe riêng chỉ sao chép DB/WAL vào /tmp CPU để đếm expected table đã gặp tail checksum đang ghi, nên không có expected-row-count đáng tin từ probe đó. Không có bằng chứng DB gốc bị hỏng.

## Helper và ranh giới

`scripts/akt/calibration_audit_transaction.py` nằm ngoài package KT. `transactional_expected_insert` bọc đúng helper gốc trong BEGIN/COMMIT và restore hook trong finally. Khi helper lỗi, transaction rollback. Root dùng context này trong CPU worker riêng cho các lượt mới.

`resume_completed_raw_audit` tiếp tục export_predictions với iterator prediction rỗng và completed_users của raw manifest. Chỉ prepare-output hook cho đúng một physical raw directory đã pin. Audit SQL, metadata validation và original helper vẫn được tái sử dụng. Source KT trên disk và inference binding đã frozen được giữ riêng với source SHA của CPU wrapper.

Trước recovery, writer phải có FAILED/COMPLETE của đúng attempt hoặc external receipt kind MODAL_CPU_WRITER_STOPPED_V1, APP_STOPPED và tasks0. External receipt đối chiếu operation config SHA, allocation/request SHA, run, variant và operation tranche. Root tạo receipt từ trạng thái Modal đã xác minh. Helper từ chối marker của attempt khác.

Raw manifest và SHA mọi Parquet được lưu trước thao tác. Mọi unlisted part/pending file khiến helper từ chối, tránh cleanup ngoài inventory. Hai scratch DB/WAL cũ được rename sang receipt/before-audit sau khi writer-stop được xác nhận, giữ bytes/SHA. Parquet được kiểm SHA lại sau audit. Raw đã complete có thể dùng lại cho attempt fit/upload mới, không ghi lại closed manifest.

## Public recovery pipeline

`recover_cpu_calibration(request, root, *, gpu_result, raw_source_pin, closed_marker_pin, attempt_id, publish, volume_commit)` dùng load_inputs metadata hiện hành, kiểm source identity, old raw config, NumericBinding, PredictionBinding, source/cache/population và graph identity với receipt GPU gốc. Không dựng model.

Pipeline audit/reuse raw, commit Volume, đóng numeric archive bằng helper hiện hành, đóng raw ZIP thành tranche mới, commit/publish cả hai rồi gọi fit_volume_calibration V1 với fit tranche mới. Hàm trả calibration_identity và ba publication receipts. Caller cấp callback CPU Drive và Volume commit. `cpu-recover` gọi thẳng pipeline này vì resume đã tự bao transaction, tránh BEGIN lồng nhau.

## Kiểm chứng

Lượt cuối audit-recovery-tests05 đạt12/12 trong38,13giây. Bao gồm giữ nguyên Parquet, restore hooks, rollback primary-key failure, từ chối running/mismatched writer, external-stop tasks0/request binding, giữ scratch WAL, từ chối unlisted files, A1 toy end-to-end archive→V1→publish, mismatch old checkpoint và retry raw đã complete. Metadata loader được thay bằng fixture synthetic trong hai tests full pipeline; audit/export/ZIP/fitter V1 thực được gọi.

Trong nhánh này chưa chạy recovery trên Junyi thật, chưa dừng A0/A1 app và chưa gọi GPU. Probe metadata CPU đã tự dừng, dữ liệu lớn tiếp tục ở Volume. Root quyết định writer-stop và launch worker thực từ receipts/pins đã lưu.
