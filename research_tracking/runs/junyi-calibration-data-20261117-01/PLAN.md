# Chuẩn bị nguồn calibration10 Junyi thật

Ngày17/11/2026. User yêu cầu tiếp tục pipeline calibration thật, root phân công nguồn dữ liệu và xác nhận hai stageCPU trong ngân sách đã nêu. Đây là chuẩn bị Development đọc-only ở nguồn, không thay role, split, model weights hoặc hyperparameters.

## Nguồn và ranh giới

Nguồn canonical là `artifacts/bkt_baseline/derived/canonical/`,726Parquet tổng249.372.459byte. Assignments gốc ở `artifacts/bkt_baseline/splits/assignments.parquet`. Frozen roles là `artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json`. Chỉ lấy đúng15.847calibrationusers thuộc Developmentfold0–3. Train80, selection, outerfold4 và Holdout giữ tách khỏi output.

Refit90 vocabulary đã fit từ142.621train+selectionusers nằm tại `artifacts/akt/window-cache/full-refit90-20261114-01.encoding.json`,717exercise. Tiền xử lý chỉ dùng vocabulary này để đếm OOV. Không fit vocabulary từ calibration. Confidence/graphTRAIN80 vẫn theo artifact của các model đã refit.

## Hai stage và caps

1. `--mode count` đối chiếu role/assignment/encoding metadata, rồiJOIN đúngcalibrationusers để tính exacttargets/learners/positive–negative/OOV/uniquesource_rows/maxevents. Output nhỏ `COUNT.json`. Nguồn stats và metadatahash kiểm trước/sau.
2. `--mode prepare` kiểm hash726nguồn với inventory đã đóng, COPY mộtcalibration-onlyParquet theo `user_id,time_done,source_row`, tạoassignmentcache đúngDevelopment và đếm lại toàn bộ output. Hash nguồn trước/sau, manifest nguồn mới có pinParquet/assignments. Các model dùng chung nguồn này để tránh scan canonicalgốc nhiều lần.

Mỗi stage tối đa3.000.000targets,180giây,640MiBRSS,160MiBoutput. DuckDB256MB/1thread,512MBtemp. Watchdog riêng của chính process theoRSS/thời gian/output, giữ failure và dừng process khi chạm cap. Nguồn249MB được scan hữu hạn; runtime/thựcRAM báo bằngreceipt, đây chỉ là dự toán trước chạy. Temp và output đều ở vùngartifacts/akt sở hữu riêng.

Output dự kiến `artifacts/akt/junyi-cohorts/outer4-calibration-full-20261117-01/`. Không nén/copy cacheTRAIN90 hoặc tạo lại encoding/windows nếu chưa cần. Producer sau đó nhậnDataPaths mới và `prepare_calibration_population` để tạo exacttarget/prefix identity, với caps theo số liệuCOUNT thật.

## Bổ sung population sau hai stage đầu

COUNT và PREPARED đã kiểm đủ1.621.484targets/15.847learners/0OOV, maxlearner13.491events. Dùng chính API `prepare_calibration_population` để tạo population/prefix manifest độc lập model trên nguồn14,14MB đã chuẩn bị. Lượt đầu cap180s dừng đúng MAX_SECONDS, RSS368,3MB, giữ failure và chưa có populationcomplete.

Theo rootreview, đã đo kỹ thuật10.000targetđầu bằngcProfile với cap60s. Profile ghi7,46s, toànwrapper15,96s/RSS336,5MB, bao gồmsetup/query/profiling và contention hiện hành, không suy tuyến tính thành dự báo runtime chính xác. Guard cũ còn statoutputfoldermỗi0,1s ở stagechỉđọc; đã bỏ đooutputở count/population và chỉ đo1s ở prepare, giữ time/RSSsample0,1s. Source producer/prefix recipe giữ nguyên.

Root cho phép đúng một retry population với cap600s/RSS640MiB, exacttargets1.621.484 và maxlearner13.491. Lượt02 ghim preprocessor source/argv trước chạy, giữ các receipt180s vàprofile. Population đầy đủ được công bố khi API kiểm learner coverage và trả đúng tổngtargets.

## Nghiệm thu

Unit fixtures phải chứng minh filter chỉcalibration, giữ chronology/labels/source_rows/OOV, từ chối invalidvalues/duplicaterows và outputprotected/overwrite. Dữ liệu thật phải có đủ15.847learners,0source_rowduplicate,0invalidrows, cùngtarget/OOVcounts ở nguồn vàcache. Manifest công bốcomplete sau kiểm nguồn/output. Ghi rõ việc chuẩn bị nguồn chưa phải fit temperature hoặc evaluation thật.
