# Chuẩn bị đánh giá Junyi độc lập sau refit và calibration

Ngày17/11/2026. Trạng thái **CHƯA ĐỦ ĐIỀU KIỆN KHỞI CHẠY**. Đây là kế hoạch thực thi và kiểm phần mềm trên dữ liệu tổng hợp. Chưa có kết quả so sánh outer A0–A3. Phạm vi thuộc đánh giá mô hình và thống kê của KLTN, không thêm một lượt training hoặc một RQ mới.

## 1. Phép đánh giá cần trả lời điều gì

Bốn model đã refit cần được dự báo trên cùng những người học chưa dùng để tối ưu weights, chọn epoch hoặc fit temperature. So sánh này kiểm tra chất lượng dự báo ngoài tập fit của AKT không đồ thị A0, đồ thị cố định A1, trọng số tin cậy A2 và cổng đồ thị A3. Nó hỗ trợ RQ1/RQ2 về dự báo và RQ3 về phương pháp. Một benchmark Junyi chưa chứng minh tác động lên kết quả học vòng kín.

Nguồn điều hành là [Protocol21](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md). Role/split lấy từ [ROLE_LINEAGE](../runs/calibration-eval-readiness-20261117-01/ROLE_LINEAGE.json). Quyền hiện hành chỉ cho Modal H100, phần CPU dùng local `.venv` hoặc Colab miễn phí. Đầu ra nghiên cứu đi Drive Sang, local chỉ giữ chỉ mục và biên nhận nhỏ.

## 2. Dữ liệu, model và số lượng phải khóa trước khi đọc kết quả

| Thành phần | Nguồn và giá trị hiện có | Điều kiện nghiệm thu |
|---|---|---|
| Development | `artifacts/bkt_baseline/splits/manifest.json`,198.084người học trong5fold | Chỉ `partition=development`; tuyệt đối không dùng HoldoutTest49.522người học |
| Outer độc lập | fold4,39.616người học | View `outer_evaluation`,allowed_folds=(4,), đủ toàn bộ danh sách role |
| TRAIN80 |126.774người học | Không tiếp tục fit hoặc chọn cấu hình bằng outer |
| Selection10 |15.847người học | Epoch9 đã chọn trước, giữ nguyên |
| Refit90 |142.621người học,14.947.674target | Dùng weights refit cuối, không dùng weights TRAIN80 thay thế |
| Calibration10 |15.847người học,1.621.484target | Temperature chỉ fit ở role này |
| Outer target dự kiến |4.137.050row theo `experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json`,folds[4].overall.total_rows | **Ứng viên**, phải kiểm lại coverage neural/all-target/warm-up trước khi freeze target contract |
| Vocabulary | Encoding refit90 có717exercise | Dùng đúng cùng encoding A0–A3, OOV giữ null+reason |
| OOV lịch sử BKT |144row/3skill theo cùng metadata CV | Chỉ là OOV của model BKT outer-train; chưa xác nhận bằng OOV của refit90 neural |

Canonical có726file Parquet,25.924.553row theo derivedmanifest. Năm partition không thuộc vocabulary refit90 chỉ có7.381byte. Tuy nhiên hai lần đếm metadata đã dừng nên chưa thể đưa ra số OOV outer neural đã xác minh. Không lấy144của BKT làm số neural. Không có cột correctness nào được yêu cầu trong các truy vấn đếm.

Các export dùng `experiments/akt/results/model-export-a{i}-refit-20261114-01/MODEL_INDEX.json`,i=0..3. Encoding identity `4b8eb3e6bc5be9abd1419cf4e818b2e75dc86b82e59a0fe94e837c5f3299734f`; roles identity `7c9a8102e399bdbc6569fc5a929faae525480c86fe0c60d2d805244a80b8e45a`; outer view identity `b33db239bb2bed5b2666ad454b37d949a2724a131e76db33d180ed536390e669`.

## 3. Các kiểm đã thực hiện và giới hạn cụ thể

### Đường không dùng window cache hỗ trợ OOV fold4

`iter_junyi_phase_learners` nhận outer view và raw Development fold4. `windows.iter_windows` xuất `UnseenTarget` riêng. `prediction_batch.iter_predictions_batched` giữ đủ vị trí, xuất OOV null và chỉ gửi cửa sổ known vào model. Kiểm tổng hợp trong `tests/akt/test_outer_frozen_cache_readiness.py` xác nhận3row known/OOV/known fold4 thành xác suất/null/xác suất, đúng source_row, và model chỉ nhận2cửa sổ known. Đây là kiểm giao diện với predictor giả, chưa là kiểm CUDA hoặc suy luận model nghiên cứu thật.

**Đề xuất ưu tiên** dùng các hàm native công khai nêu trên trong launcher outer riêng, tránh sửa nguồn KT frozen chỉ để khởi chạy đánh giá. CPU cần chuẩn bị dữ liệu/cửa sổ và graph context ngoài thời gian thuê GPU. Đường native nếu nối reader trực tiếp trong H100 vẫn có chi phí chờ CPU, nên chưa được coi là phương án tối ưu đã đo. Chỉ chấp nhận launcher sau phép kiểm nhỏ trên cùng weights và nguồn dữ liệu, có receipt đủ coverage và đo wall-time.

### Window cache hiện tại có lỗi điều kiện với outer OOV

`research_junyi_window_cache._parts` nhận `UnseenTarget` chỉ khi `event.fold in (0,1,2,3)`, trong khi outer view hợp lệ có allowed_folds=(4,). Known windows vẫn qua nhánh riêng. Vì vậy đây là lỗi nhánh OOV của cache, chưa phải bằng chứng toàn bộ inference outer không được hỗ trợ. Test mong đợi outer OOV được nhận đang **XFAIL strict**, giữ bằng chứng của giới hạn hiện hành. Không đổi fold, bỏ row OOV hay đưa xác suất giả để vượt guard. Nếu chọn đường cached numeric, root cần điều phối source release và kiểm tương thích calibrator trước khi sửa frozen source.

### Hai phép đếm đã dừng, không lặp lại

1. Quét metadata fullcanonical, DuckDB1thread/128MiBengine, parentRSS256MiB, mục tiêu timeout90s. Monitor/termination có độ trễ, thực tế367,90s, peakRSS152.567.808byte. Không xuất counts. Sự vượt thời gian này được giữ trong `COUNT_RESOURCES01.json`, không coi guard đã đạt.
2. Chỉ5partition OOV/7.381byte, Windows Job128MiB,subprocess timeout60s. Dừng sau6,06s, returncode3221225477. Log ghi OpenBLAS không cấp được bộ nhớ. Job được terminate,activeprocess=0. Chưa xuất footerinventory/counts. Không retry theo yêu cầu điều hành.

Bằng chứng và log ở [bundle outer readiness](../runs/junyi-outer-readiness-20261117-01/README.md). Lượt pytest đầu thiếu PYTHONPATH được giữ, lượt cuối `PYTHONPATH=src` đạt3PASS/1XFAIL trong0,29s.

## 4. Calibration và ranh giới domain phải giữ nguyên

[Nghiệm thu metadata hiện có](../runs/junyi-calibration-real-20261117-01/POSTSTOP_CALIBRATION_METADATA_ACCEPTANCE01.json) xác nhận A0/A1 fit và đọc lại Drive. A0T=1,0301834528611808; A1T=1,026353620316833. A2/A3 phải có biên nhận tương đương trước khi đánh giá bốn model calibrated. Không suy hoàn tất fit từ việc GPU numeric đã xong.

`PredictionBinding.domain_sha256` của calibrator là nguồn calibration10 (`7c8540d820578751f5675ec8c777aa87a6918b15a345bfa55f35ae6833b18692`). Outer raw export phải ghi domain riêng của outer. `_validate_calibration` so toàn bộ binding, vì vậy truyền trực tiếp binding outer vào consumer của calibrator sẽ bị từ chối. `evaluation.iter_calibrated_predictions` có thiết kế caller tự kiểm population/role, dùng binding đã fit và kiểm checkpoint trên mỗi record. Cần một hợp đồng application bên ngoài nguồn frozen xác nhận checkpoint/vocab/roles/bank/reference/model-source trùng nhau, domain calibration giữ nguyên, domain outer được ghim riêng và cohort disjoint. Sau đó mới gọi consumer với binding đã fit. Không sửa binding cũ hoặc fit lại bằng outer.

`inspect_cpu_refit_export` và `_build_refit_predictor` hiện dựng assets calibration view; exporter `export_refit_calibration_predictions` nối qua calibration observation guard. Không gọi launcher calibration nguyên trạng cho outer hoặc sửa tên phase trên receipt. Outer cần launcher riêng dùng native inference + generic export, cùng metadata admission rõ ràng. `runner.run_full_fold` cũ gọi selection/refit nên không phù hợp tái dùng nguyên entrypoint khi đã có refit90 và calibration10.

Source inference đang ghim `d22f6d2e3d6bb4a6c2d7f72da748e55c5c647ce8b41a7ab46b25c82290a4c96c`; implementation temperature `a1e71c1da957199437bd42f4914ca2e2885b0fe311c72d55726d0a48528f673d`. Thay module KT có thể thay broad source identity. Đường wrapper ngoài KT được ưu tiên để giữ nguồn model/calibrator đã nghiệm thu.

## 5. Thống kê và hình so sánh cần khóa trước execution

- Primary theo Protocol21 là LogLoss/Brier. AUC,ECE15,coverage và sai số quanh ngưỡng là phụ. Báo raw và calibrated riêng, không dùng outer chọn temperature/model/threshold.
- Đơn vị ghép cặp là người học outer, cùng learner resample qua model conditions. Bootstrap2000lượt theo protocol, giữ cả tổng sufficient statistics để dựng lại. CI này có điều kiện trên một fold và training seed, không biểu diễn độ biến thiên5fold hay nhiều trainingseed.
- Đối chiếu fullcoverage và tập supported chung một cách tường minh. Cần đủ row identity/source_row, learner,chrono,fold,label,raw/calibratedprobability hoặcnullreason. Báo OOV trước bảng metric.
- Family Holm phải freeze trước đọc outcome. Cần xác nhận family chính xác trong request bốn model, không tự lấy family45/72của Paper2. Đề xuất3so sánh A1/A2/A3 với A0 ×2primary calibrated=6; raw dùng chẩn đoán. Đây là đề xuất còn cần đối chiếu quyết định đã duyệt. Nếu cảraw/calibrated đều confirmatory thì family phải thể hiện cả12test.
- Existing pairedbootstrap cho CI không tự cung cấp một p-value hợp lệ. Cần ghim đúng thủ tục p-value đã duyệt nếu muốn Holm. Không tự chọn Wilcoxon hay test mới chỉ vì source có sẵn.
- BKT/GAM-KT lịch sử fit trên phạm vi train khác refit90. Chúng có thể cung cấp ngữ cảnh hoặc bảng đã công bố đúng nhãn. Main matched comparison A0–A3 phải cùng population/roles, không gọi so sánh lịch sử là matched protocol.

Figure tối thiểu là bảng primary raw/calibrated với CI paired, calibration curve có số mẫu từngbin, coverage/OOV và pairedΔ theo learner. Lưu SVG độc lập, CSV nguồn và cách dựng cùng bundle kết quả sau nghiệm thu. Chưa dựng figure dữ liệu outer vì chưa chạy đánh giá.

## 6. Gói thực thi hữu hạn sau khi khép blocker

| Bước | Chạy ở đâu | Đầu vào/đầu ra và điều kiện dừng |
|---|---|---|
| O1. Freeze request | CPU local nhẹ |4index/checkpointSHA,4temperatureSHA,roles,encoding,outerview,nguồnsource,populationcount/OOV,hypothesisfamily; thiếu trường thì dừng |
| O2. Outer preparation | Local hoặc Colab CPU miễn phí | Chỉ Development fold4; stream bounded, đủ39.616learner, kiểm target/OOV/chronology; inputstaging cloud, không đặt output lớn trên D; chốt windows/maxhistory sau count thật |
| O3. Wrapper và binding tests | CPU tổng hợp | Native known/OOV+calibrator source/domain admission, graphphaseouter, fullcoverage; không thay model/temperature |
| O4. H100 pilot | Một H100, không CPU-onlyModal | Cohort kỹ thuật được ghim trước, timeout/budget hữu hạn theo request; đủ counts,finiteprobabilities, đúngrowkeys, logNVML,Drivechecksum,returnGPU ngay; pilot không là final metric |
| O5. Full outer inference | H100 lần lượt A0–A3 |4weightsfrozen,sameouter,batched128 đã kiểm; raw numeric shards/checkpoint/source/config/telemetry lên Drive; lỗicoverage,budget,identity thì dừng, không auto retry |
| O6. Join/transform/metrics | Local hoặc Colab CPU miễn phí | Nối labels bằng đúngrowkeys, apply4frozenT, đủcoverage,pairedbootstrap/Holm theo request; outputsDrive,localreceipt nhỏ; cập nhật báo cáo sau nghiệm thu |

Numeric calibration hiện xử lý1,62triệu target trong42–58giây/GPUworker tùyvariant. Outer candidate4,14triệu target xấp xỉ2,55lần về sốrow nhưng chưa có windows/OOV/độ dài phù hợp để ngoại suy runtime chính xác. Không cấp một dự toán phút hoặc chi phí giả. O4 phải đo throughput/end-to-end và kiểm credit trước O5, gồm cảinference+upload, không chỉ kernel.

## 7. Điều kiện còn thiếu trước launch

1. Hoàn tất và đọc lại calibrator A2/A3 cùng nguồn binding đã freeze.
2. Xác nhận target/OOV/countgeometry outer bằng CPU có nguồn lực phù hợp. Hai phép đếm local thất bại đã giữ nguyên.
3. Chọn native wrapper giữ source hoặc release cachedOOVfix có kiểm tương thích. NativeOOV tổng hợp đã đạt, wrapper thực chưa có.
4. Hợp đồng apply calibrator sang domain outer giữ calibration provenance và source identity.
5. Request inference/statistics cụ thể gồm family/p-value/coverage/budget và Drive sink. Khi chưa đủ các điều kiện này, chưa chạy fullouter và chưa kết luận RQ3.
