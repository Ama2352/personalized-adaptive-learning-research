# Chuẩn bị CPUouter bằng API hiện có

Ngày17/11, gói code tổng hợp ngoàiKT, không chạy dữ liệuouter thật hoặc cloud. Source7c và SOURCEfrozen giữ nguyên. Refit90encoding/graph/confidence chỉ được đọc từ4portableexports, không fit lại.

## Đã cài

`scripts/akt/prepare_junyi_outer_caches.py::prepare_outer_caches` nhận4assetsmetadata đã inspect, `DataPaths` trỏ **một outer-onlyParquet chung**, manifestnguồn và2metadatapins. Chỉ nhận phase/purposeouter, đủroleoutervàencodingrefit90. Filecanonical/assignments được kiểm byteSHA trước và sau.

API dựng fullwindowcache có mọiOOV/rank, strictCPUadmission, rồi3graphcaches. Graphbuilder chỉ nhậnknownWindowInputs, expectedtargets=alltargets−OOV. Tái đếmOOV trong windowcache phải bằng sourcemanifest144ở lượt thật. Không giảcalibrationphase hoặc đổi rank sauOOV. Graph/encodingguards được reuse nguyên API.

Cache dùng defaultownedpaths dưới PROJECT_ROOT của source7c, lần lượt `artifacts/akt/window-cache/<tag>` và `artifacts/akt/graph-context-cache/<tag>`. Diskbudgetroot bao trùm hai vị trí và cachetạm chung, cap tối đa4GiB. Guardwall/RSS/disk là cooperative, kiểm mỗi512record và khi kết thúc. Root cần processwatchdog riêng khi chạy thật. Lỗi giữ partials nhưng không xuất finalreceipt. Không gọiHTTP/Drive/GPU từ helper.

`research_tracking/runs/junyi-calibration-real-20261117-01/run_outer_cpu_cache_request01.py` là entrypointCPU nhậnrequestJSON. Process mới đưa source7c/src vào sys.path trướcKTimports, kiểm identity, inspect4index/SUPPORTmetadata, gọi helper và xác nhận chưa importTorch. Chưa chạy entrypoint với request thật vì outer-onlysource chưa được dựng.

Tests4PASS/0,95s tronggreen02, giữred vàgreen01. Fixturetiny cóOOVgiữa chuỗi và3graphconditions thực tạo bằng API, không Torch. Kiểm từ chối phasecalibration/OOVcountmismatch/nguồnSHAkhác. Chưa phải kiểm dataset thật hoặc hiệu năng.

## Điểm chặn còn lại

Thiếu **outer-onlysourcewriter** và manifestnguồn thật. Existing `prepare_junyi_calibration_data.py` hardcodecalibrationroles,purpose và cap3triệutarget, nên không gọi nguyên lệnh choouter4,14triệu. Không sửa source7c để đổi data phase. Root có thể bổ sung một entrypoint nhỏ ngoàiKT tái dùngSQLreader/copy củawriter hiện có với fullouterview, rolepredicate và caps phù hợp, rồi dùng requestdriver đã có.

Originalcanonical partitiontheoexercise, file vật lý dùng chung các nhómlearner. Không có tậpfilenameDevelopmentriêng. Writer mới phảijoinassignments và fullroles.outer_users, chỉ trả `partition='development' AND fold=4` trước xuấtcorrect/suggested. Mọicount/check cùngpredicate. Không đọc Testartifact hoặc tính metrictrênHoldout. Outer-onlyParquet đầu ra mới thực sự có toànrowouter, được dùng chung4model. Đây là row-filteredaccess trên nguồnphysicallymixed, không được ghi sourcegốc làDev-only.

Schema cần cho sourcepreparedmanifest được ghi trong `OPERATION_PLAN01.json`. Fulltarget4.137.050 vẫn candidate từmetadataBKT, writer phải xác nhận độc lập, OOV144phải khớp countđã nghiệm thu, đủ39.616learner, chronology/unique source_row/maxhistory. Sauwindowbuild còn kiểm đủrank/learner/target. Không lấy28.653windowcalibration làmwindowouter.

## Lệnh sau khi có nguồn thật và requestREADY

PowerShell tạiROOT, dùngROOT.venv, đặtOPENBLAS/OMP/MKL_NUM_THREADS=1. Chạy `.\.venv\Scripts\python.exe -B research_tracking/runs/junyi-calibration-real-20261117-01/run_outer_cpu_cache_request01.py --request <READY_REQUEST.json>`. `CACHE_REQUEST_DRAFT01.json` hiện làdraft, driver từ chối chạy. Điềnpath/SHAnguồn/maxhistory thật và statusREADY chỉ sau nghiệm thu writer và quota4GiB.

SauCPUbuild, root stream/cacheinput lênDrive trướcH100. NumericGPUreuse `run_cuda_cached_numeric`, expected_oov_targets144, expectedrecords/windows lấy cachemanifest thật. CPUreplayreuse `prepare_prediction_windows` + `iter_numeric_prediction_records`, giữOOVnull. `join_numeric_calibration_snapshot` chỉcalibration, không dùng nguyênhàmchoouter. Applytemperaturequa compatibility đãduyệt, khôngfitlại hoặc sửaoldbinding. NumericH100/CPUjoinentrypointouter còn phải nối ở orchestration ngoàiKT.
