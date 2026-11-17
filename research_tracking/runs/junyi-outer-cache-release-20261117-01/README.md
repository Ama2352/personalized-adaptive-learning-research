# Sửa guardfold cache outer, ngày17/11

Root cho phép sửa tối thiểu checkout để chuẩn bịouter. Calibration đang chạy từ SOURCEfrozen riêng, không sửa nguồn đang chạy, model/checkpoint/calibrator/encoding hoặc artifact cũ.

## Thay đổi và kiểm

Chỉ một dòng trong `src/knowledge_tracing/akt/research_junyi_window_cache.py`, thay `event.fold in (0,1,2,3)` bằng `event.fold in view.allowed_folds`. Vớiouterfold4, nhận OOVđúngfold và từ chối fold0/3. Calibration vẫn nhậnfold0–3 và từ chối4. Giữ nguyên learner/rank/chronology/type/binarylabel/OOVvocabularyguards, geometry và forward.

`red01.txt` giữ3FAIL/5PASS trước sửa. `green01.txt` giữ63PASS/24,10s sau sửa, gồm wholewindowcachesuite, nativeouterwrapper và2known-onlyboundarytests. Test mới roundtrip đầy đủ known/OOV/known qua shard→strictsession→CPUadmission→admittedreplay giữ3target/1OOV, rank0/2 và nativehistoryreset. XFAIL cũ chuyển thành testđạt. Không chạyTorch/model/GPU hoặc dữ liệuouter thật. Tinypytestoutput ở `artifacts/akt/test-temp/outer-cache-release-20261117-01`, chưa dọn.

## Nguồn trước và sau

`SOURCE_BEFORE01.json` ghim toàn bộ sourcecheckout trước sửa. `SOURCE_DELTA01.json` so byte với frozenD22trong cache readonly.

- FrozenD22 `d22f6d2e3d6bb4a6c2d7f72da748e55c5c647ce8b41a7ab46b25c82290a4c96c`.
- Checkout trước `16f97eb396fb0202a1e250ec59d2b3a9cb170070b3f0f8b8575488ad0cf20764`.
- Checkout sau `a841100f1d2089d6a17ffdd7e076c7a268ec7d116fbfb403e3cefae913e22dd2`.

Chỉ2file khácD22. Windowcache là một điều kiệnfold như trên. Upstream `artifacts/akt/dependencies/upstream/akt.py` khác sẵn từ trước doCRLF/LF, ASTvànewline-normalizedbytes bằng nhau, không sửa file này. So guardcache trướccheckout vớifrozen khớpbyte. Không tự coi nguồn cóhashkhác là tương thích chỉ vìASTtrùng.

## Hợp đồng compatibility đề xuất, chưa áp dụng

Để giảm delta, gói thực thiouter có thể lấy bản sao đầy đủ frozenD22 rồi chỉ đưa windowcachefile mới vào gói source **mới**, giữ upstreamLF. Identity dự kiến đã tính từ mappingfileSHA trong `SOURCE_DELTA01.json`; phải kiểm identity thật khi bundle mới được dựng. Không sửa SOURCEfrozen cũ.

CalibratorD22giữ nguyên binding vàidentity. `RefitCalibrationPredictor.assert_boundary` và `attach_refit_export` yêu cầu nguồn inference hiện hành, nên predictorouter phải bindnguồnmới. `free_outer_evaluation.admit_outer` hiện kiểm7fieldnon-domainbằng tuyệt đối, vì vậy sẽ từ chối calibratorD22với predictornguồnmới. Đây là blocker có chủ đích còn lại, chưa nới sourceguard.

Giải pháp tối thiểu sau rootduyệtcompatibility là receiptapplicationngoàiKT chứa frozen_source/new_source/fullfilemaps, allowlist1guardfile (hoặc2file nếu chọncheckoutCRLF), exactone-linepatchproof, source/moduletestpins,4checkpointSHA và4calibratoridentity. Trướcapply, caller kiểm6fieldnon-domain/non-source còn lại trùng hoàn toàn, domaincalibration vàdomainouter riêng, fullouterrolesdisjoint, temperatureimplementationSHA không đổi, hai sourcemaps khớp đúng receipt đã duyệt và không cófiledelta ngoàiallowlist. Sau đó gọi `iter_calibrated_predictions` với **calibration.binding cũ**, ghi receiptmodelsourcehiện hành riêng. Consumer kiểmcheckpoint từngrecord và nguyêncalibratorimplementation, không cần sửa oldbinding hay fit lạitemperature.

Không thay `bind_probability_calibrator` hoặc giả predictor mang D22 khi thực chạy nguồn mới. Receiptcompatibility chỉ cho read-cacheguardrelease này, không dùng làm cơ chế chấp nhận sourcekhác tùy ý. Cần kiểmnumericalparity native/cached trên knownwindows với model thật trước fullouter, và kiểm đủOOV/coverage. Các tests hiện tại chỉ chứng minh cachegeometry/guards, chưa chứng minh kết quả4modelCUDA.

## Các bước production còn lại

Root duyệt sourcebundle/compatibilityadmission → CPUlocal/Colab chuẩn bịouterfullcache và3graphcaches, ghim counts/rowkeys/rankcoverage/OOV144 → Driveinputreceipt → H100numeric → CPUreplay/apply4frozenT → thốngkê theo request đãfreeze → Driveoutputs. Không cần tách144OOVra khỏi windowcache sau fix vì fullcachegiữ nguyên causalbarrier. Numericshards vẫn chỉ chứaknownprobabilities, CPUreplay xuấtOOVnull.
