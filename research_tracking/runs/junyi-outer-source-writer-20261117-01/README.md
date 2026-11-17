# Sourcewriterouter CPU, ngày17/11

Mã ngoàiKT tại `scripts/akt/prepare_junyi_outer_source.py`, entrypointthực thi tại `research_tracking/runs/junyi-calibration-real-20261117-01/run_outer_source_request01.py`. Chỉ đã chạy dữ liệu tổng hợp. Không queryouterthật, không cloud/GPU, không sửa source7c/frozen77 hoặc artifactmodel/calibrator.

## Hợp đồng nguồn và đầu ra

Driver processmới boot source7c/src trước KTimports, kiểmidentity, inspect4MODEL_INDEX/SUPPORT bằng API gốc và cùngrefit90encoding. Không nạpweights/Torch. Sourcewriter yêu cầu fit_viewrefit90 phủ đủtrain+selectionroles. Chỉ lấy fullroles.outer_validation_users qua joinassignments với `partition='development' AND fold=4`. Sốlearner metadataDevfold4 phải khớp toànbộrole trước đọc labels. Nguồngốc partitionexercise dùng chunglearner, vì vậy đây là logicalrowfilter, không claim filegốcphysicallyDev-only.

Inventory nguồn hiện hành có732pin, gồm726canonicalfile và6filemetadata/source. Hash trước và sau, không thay bản gốc. Không có Testartifact trong inputinventory. Sourcewriter chỉ xuất một `canonical.parquet` outer-only và `assignments.parquet` Developmentfold4 dùng chung4models, giữ nguyênexercise/time/source_row/correct/suggested. Ordering user_id/time_done/source_row và compressionZSTD như writercalibration.

`manifest.json` chỉ được ghi cuối sau kiểmcounts, binarylabels, uniquesource_row, đủlearners, maxhistory, OOV, coveragefilecopy và sourceinventoryunchanged. Manifest ghi purpose `JUNYI_REFIT90_OUTER_EVALUATION_SOURCE`, fullphase/role/encoding/modelindex/checkpoint/condition/sourcepins, filebytes/SHA. `known_oov_exercise_counts_sha256` là digest bảng sốtarget theoexercise và trạng tháiknown/OOV, không phải digesthistory/prefix. FileSHA ghim toàn dữ liệu, windowprefix/rank/counts được kiểm qua cachebuilder gốc sau đó.

Expected4.137.050target/39.616learner/144OOV trong request là các giá trị **phải được xác nhận lại**. Không dùng chúng làm kết quả đã đạt. Khác counts hoặc label/duplicate/fold lỗi thì dừng, không publishmanifest. PartialParquet/tempgiữ để root xem log và quyết địnhdọn, không overwriteđích cũ.

## Tài nguyên sau code review

- DuckDB1thread/256MB engine, SQLinterrupttimer hữu hạn. Maxseconds chỉ số hữu hạn dương≤7200, không nhậnbool/NaN/Inf.
- Checkwall/RSS rẻ mỗi fileinventory. Diskrglob tối đa một lượt mỗi30giây trong luồng và bắt buộc ở stage/writeboundaries. Không quét60kcachefile sau từngfileinventory.
- Spillcap tính từ diskcap còn lại sau currentcache và reserveđầu ra. Reserve=min160MiB,cap/4; capthật4GiB cho reserve160MiB. Parquet lớn hơn reserve thì dừng. Lượt thật có thể điều chỉnh recipe qua review nếu dự toán không đủ, không tự tăngcap.
- Các capRAM/disk/wall tổngthể là cooperative. Root cần ownedsubprocess/watchdog khi chạy thật. TimerSQL không là OSRAM/diskhardlimit. Temporaryspillfolder có tên riêng trong vùngcache, giữpath trongmanifest.

## Kiểm chứng

`review-green01.txt` ghi **17PASS/6,56s**, gồm9testwriter/cache và8testmới finitewall/fullrefitrole. Case mixedrows chứa train/calibration/outer/Holdouttổnghợp, Holdoutlabel cố ý khônghợplệ để xác nhận không lọt vào phép kiểmouter. Output chỉ2rowouter theo canonicalorder. Negativecases duplicateouter/source_row, labelouter sai và foldassignment sai bị từ chối.

Integration dùng Parquettinyđãwriterxuất, reader/nativewindowcache/CPUadmission và3graphcacheAPI thật, giữOOVnull/rank và chỉknownvàographcache. KhôngimportTorch được assert trong processpytest. `red01`,green01/02 giữ lỗi fixturepath và DuckDBCREATEVIEWparameter đã xử lý bằng publicrelation.create_view. `red-model-pins01` giữ lỗi thiếumodelpins trước khi bổ sung. Các log sau đó ghi kết quả đạt. Không có benchmarkperformance thật hoặc modelCUDAadmission.

## Lệnh root chạy sau review/quota

1. Từ `SOURCE_REQUEST_DRAFT01.json`, tạo bảnrequest mới đặt `status=READY_OUTER_SOURCE_PREPARATION` sau kiểmSHA/khôngđèđích/quota. Giữ candidatecounts để xác minh và budget. Driver từ chối bảndraft.
2. TrongPowerShellROOT, dùng `.venv`, đặtOPENBLAS/OMP/MKL_NUM_THREADS=1 rồi chạy `.\.venv\Scripts\python.exe -B research_tracking/runs/junyi-calibration-real-20261117-01/run_outer_source_request01.py --request <SOURCE_REQUEST_READY01.json>` qua ownedsubprocess và capturelog.
3. Nếu đạt, stdout trảpath/SHAmanifest, source_pins, counts vàDataPaths. Điền các giá trị này vào cache request, đặc biệt max_learner_events thật. Chạy `run_outer_cpu_cache_request01.py --request <CACHE_REQUEST_READY01.json>` để tạo fullwindowcache/3graphcaches dưới source7cPROJECT_ROOT/artifacts.
4. Nghiệm thu cache/artifactSHA/Drive trước H100numeric. CPUreplay/applyfrozenT và statisticalrequest còn được root nối riêng. Sourcewriter và cachehelper không tự khởi chạy bước kế tiếp.

Source/cache mới trong cachetạm≤4GiB, Parquetước35–40MB chưa đo. Không đồng nghĩa toàn bộcachewindow/3graph sẽ chắc chắn vừa cap trước khi chạy. Nếu vượt cap thì dừng, giữlog/partial và xem lại allocation thay vì tự mở rộng.
