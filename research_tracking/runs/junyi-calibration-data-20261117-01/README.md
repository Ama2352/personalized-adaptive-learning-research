# Nguồn calibration10 Junyi thật đã chuẩn bị

Ngày17/11/2026. Gói này chuẩn bị dữ liệu Development cho pipeline response-calibration của bốn model A0–A3 đã refit. Chưa tạo model prediction hoặc fit temperature. Source canonical, assignments, roles và encoding cũ giữ nguyên.

## Nguồn và số liệu đã kiểm

Chỉ lấy frozen `roles.calibration_users` gồm15.847người học Developmentfold0–3. Phần train80, selection, outerfold4 và Holdout tách khỏi các row được chọn. Vocabulary được kế thừa nguyên từ refit90 đã fit trên142.621train+selectionusers,717exercise. Calibration không fit vocabulary hoặc graph/confidence.

| Đại lượng | Kết quả |
|---|---:|
| Người học calibration | 15.847 |
| Targets, gồm từ lần tương tác đầu | 1.621.484 |
| source_row duy nhất | 1.621.484 |
| Nhãn đúng / sai | 1.343.648 / 277.836 |
| Exercise đã quan sát / vocabulary refit90 | 693 / 717 |
| OOV / invalid rows | 0 / 0 |
| Chuỗi người học dài nhất | 13.491tương tác |

Target count calibration khác selection vì hai nhóm learner khác nhau. Cả nhóm calibration được giữ đúng role có sẵn. Class counts là kiểm dữ liệu đầu vào, chưa là metric dự báo hoặc căn cứ chọn model.

## Output thực dùng

Cache riêng nằm tại `artifacts/akt/junyi-cohorts/outer4-calibration-full-20261117-01/`.

| File | Byte | Vai trò |
|---|---:|---|
| `canonical.parquet` | 14.143.412 | Toàn bộ event calibration, giữ exercise/time/source_row/correct/suggested |
| `assignments.parquet` | 52.569 | Đúng15.847learner/fold với partitionDevelopment |
| `manifest.json` | 122.998 | Pin nguồn726Parquet, metadata và hai output |

Một cache14,14MB được dùng chung cho A0–A3. Không dựng lại encoding hoặc nhân bản cacheTRAIN90. `PREPARED.json` giữ DataPaths vàsource_pins cho producer. `POPULATION.json` giữ exacttarget/prefix identity tính bởi `prepare_calibration_population` từ nguồn riêng này.

Population identity là `008a6752151d1a868e15f4bbb890755be28ef311420b17f2d5058f3627eb06e6`. Prefix key của mỗi target được tạo từ lịch sử đã quan sát trước đáp án hiện tại. Population manifest ghi đủ1.621.484target, phaseidentity và hai pin metadata. Binding checkpoint của từng model do runner/builder tiếp theo gắn riêng.

## Kiểm ranh giới và nội dung

Preprocessor kiểm SHA roles/assignments, tạo `calibration_predict` full-role view, kiểm đúng fold0–3 và lineage vocabulary refit90. COPY dùng JOIN với danh sách calibration đã đối chiếu Developmentassignments. Native reader vẫn quyết định timeline theo `user_id,time_done,source_row`.

Đã hash726filecanonical, tổng249.372.459byte, trước/sau COPY và khớp inventory nguồn của cache selected đã đóng. Đếm lại output khớp toàn bộ target/OOV/class counts. Kiểm semantic độc lập dùng `EXCEPT ALL` theo cả hai chiều giữa source projection và cache trên đủ6cột, kết quả0/0row khác. Assignmentscache đủ15.847uniquelearner và0foreign/mismatchedfold. `SEMANTIC_SOURCE_ACCEPTANCE.json` giữ output/hash/checkscope.

Kiểm source chỉ trả row calibration và hash byte nguồn cho integrity. Những con số về role không thay cho một đánh giá Holdout. Graph/confidence vẫn thuộcTRAIN80 đã fit, không nhận các label calibration từ công việc này.

## Thực thi và tài nguyên

| Stage | Trạng thái | Giây theo wrapper | Sampled peakRSS |
|---|---|---:|---:|
| Count từcanonicalnguồn | Hoàn tất | 21,58 | 268.644.352byte |
| COPY+hash+đếm cache | Hoàn tất | 8,75 | 388.653.056byte |
| Population01 | Dừng MAX_SECONDS ởcap180s | 180,24 | RSS tại stop368.324.608byte |
| Profile10.000targetđầu | Chỉ kiểm kỹ thuật | 15,96, trong đócProfile7,46 | 336.474.112byte |
| Population02 | Hoàn tất trongcap600s | 229,70 | 372.428.800byte |
| Semantic source/cache | Hoàn tất | 84,59 | 426.401.792byte |

Các phép chạy cùng thời điểm root đang hash archive lớn và agent khác kiểm code, nên timing giữ bối cảnh contention. Profile10k có startup/query/profiling và watchdog, chưa là phép đo throughput chuẩn để ngoại suy thẳng. Guard ban đầu statoutputfolder ởmọistage mỗi0,1s; đã bỏ đọc thư mục output ở các stagechỉđọc và giảm prepare-outputcheck xuống1s, giữ time/RSSsample0,1s. APIprefix và công thức không đổi.

Population01 giữ failure nguyên. Sau profile, root cho một retry600s/RSS640MiB với exacttarget1.621.484. `population-02-SOURCE.json` ghim source/argv trước lượt thành công. Count/prepare đầu được chạy trước khi bổ sung nhánhpopulation vào script; source hiện hành đã được re-test và semantic checker xác nhận lại toàn nội dung cache, bản cache đã công bố giữ nguyên byte. Đây là giới hạn provenance được ghi rõ thay vì suy có pin source tại lúc launch đầu.

## Test và cách chạy lại

Hai lượt unit fixtures đều đạt10ca. `tests02.txt` giữ10passed/9,50s với sourcepreprocessor hiện hành. Fixtures kiểm calibration-onlyfilter, giữ target/OOV/chronology/assignments, từ chối giá trị sai/duplicatedsource_row, protectedoutput và overwrite.

Entrypoint là `scripts/akt/prepare_junyi_calibration_data.py`, chạy bằng `.venv/Scripts/python.exe -B`. `COMMANDS.json` giữ lệnh đã chạy và cap. Mọi output mới dùng đường owned riêng, script từ chối ghi đè. Khi lặp một stage thất bại, chọn attempt mới và giữ failure của lượt cũ. Cache cũ không được đổi tên thành input mới hoặc sửa role.

## Tích hợp tiếp theo

Đã gửi agent builder cả `PREPARED.json` và `POPULATION.json` cùng SHA. Runner nhận datareceipt/population bằng path+pin, kiểm cachemanifest/output/source boundary trước nạp model. Cần giữ grant/resource/source-runtime phù hợp, prediction batch128 theo recipe, checkpoint binding và actual target/prefixcoverage trước fit temperature. Temperaturefit1,62Mtargets có thể materialize lượngRAM lớn hơn nguồn14MB, cần dự toán riêng từ API hiện hành.

Theo chỉ thị cloud-first mới của user qua root, các file14MB/population của lượt đã hoàn tất này giữ vai trò inputstaging. Root sẽ cấp remotesink và chuyển input được duyệt lêncloud trước GPU. Config, prediction, checkpoint và artifact của các lượt tiếp theo được lưu Drive theo hợp đồng root, tránh dùngD làm nơi nhận output lớn. Gói này chỉ chốt hồ sơ của việc chuẩn bị đã chạy, không triển khai lượt calibrationfit mới trênlocal.

Lượt này không gọi model, optimizer, simulator, GPU hoặc cloud và không tạo kết luận mới về hiệu quả A0–A3. Nó khép nguồn calibration thật và population/prefix provenance, các bước prediction, calibrationfit và outerevaluation tiếp tục có artifact/acceptance riêng.
