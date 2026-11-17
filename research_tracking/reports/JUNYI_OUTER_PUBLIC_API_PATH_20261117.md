# Đường production outer với nguồn AKT frozen

Rà tĩnh và kiểm tổng hợp ngày17/11/2026. Gói này nối tiếp readiness, không chạy dữ liệuouter, GPU hoặc cloud. NguồnKT hiện hành được giữ nguyên. Root đang hoàn tất CPUcalibration, vì vậy chưa thay sourceidentity hoặc binding đã fit.

## 1. Đầu vào đã rõ thêm

[Lượt đếm03](../runs/junyi-outer-count-20261117-03/OOV_COUNTS03.json) xác nhận **144targetOOV**, gồm41/40/63row trên3exercise ngoài refit90vocabulary717. Query chỉ5fileParquet7.381byte, không đọc correctness hoặc chọn Holdout. Đây là sốOOV đã xác minh, thay cho trạng thái chưa biết trong readiness trước. Fulloutertargetcount4.137.050 vẫn là metadata BKT đối chiếu, chưa independentlyscan fullouter. Sốwindow/maxhistory phải lấy từ CPUpreparation đúng nativegeometry.

## 2. Tách OOV sidecar chưa đủ để dùng cache frozen

`build_junyi_window_cache` gọi `_parts`, sau đó `_SequenceAudit.add`. NhánhOOV `_parts` chỉ nhận fold0–3. Nếu bỏOOV ra sidecar và đưa knownwindows nguyên trạng vào cache, `_SequenceAudit.add` vẫn yêu cầu globalrankliên tục từ0 cho từnglearner. Known/OOV/known tạo rank0/1/2, lọcOOV giữ rank0/2 nên bị từ chối tại rank2.

Kiểm tổng hợp mới `tests/akt/test_outer_known_only_cache_boundary.py` xác nhận2điều. Outerknown-only không cóOOV được audit nhận. LọcOOV giữa chuỗi giữ nativehistory/reset đúng nhưng audit báo `Target rank/chronology mismatch`. Không renumberrank hoặc ghép lại history để vượt guard vì sẽ thay contract và làm mất khả năng kiểm đúng target.

`run_cuda_cached_numeric` yêu cầu **exacttype** `JunyiWindowCacheSession`, CPUadmission và targetcount đủ. Một objectloaderngoàiKT hoặc known-onlysidecar không được publicCUDAcore nhận. Không dựng fakeadmission, sửamanifest sau build hoặc giảphasecalibration.

## 3. Các entrypoint có thể tái dùng

| Giai đoạn | PublicAPI và cách dùng hợp lệ | Trạng thái |
|---|---|---|
| CPU đọc nguồnouter | `research_junyi_data.iter_junyi_phase_learners`,viewouterfold4; `windows.iter_windows` | Hỗ trợouter; nativeknown/OOV/history đã kiểm tổng hợp |
| CPUwindowcache/admission | `build_junyi_window_cache`, `JunyiWindowCacheSession`, `write_cpu_admission` | Bị chặn bởiOOVfold4; known-onlyfilter cũng bị chặnrankgap |
| CPUgraphcontext | `JunyiGraphPhaseSession(condition,outer_view)`, `build_graph_context_cache` | Hỗ trợouter vàknownWindowInputs; expectedtargets là sốfittedtargets, không gồm144OOV |
| H100modelbuilder | `inspect_cpu_refit_export`, `build_cuda_refit_predictor` | Weights/sourceguard tái dùng; assetsgraph ban đầu calibration, phải setouterphase qua public `adapter.set_phase` trước dự đoán |
| H100numeric từcache | `run_cuda_cached_numeric`, `run_cached_numeric` | Đòi CPUadmittedtypedcache đủpopulation; chưa cócacheouter hợp lệ |
| Numericshard | `NumericWindow.from_window`, `write_numeric_shard` | Có thể giữ probabilities không nhãn, nhưng chưa thay thế được persistentinputcache/admission thiếu ở trên |
| CPUreplay/join | `prepare_prediction_windows`, `iter_numeric_prediction_records` | Replay đúngwindowkeys+sidecar, tự phátOOVnull, không gọimodel |
| CPUapplytemperature | `evaluation.iter_calibrated_predictions` + `free_outer_evaluation.admit_outer` | Giữbindingcalibration, kiểm7fieldnon-domain trùngouter; source/domain/role admission tách riêng |
| Existingcalibrationcloudjoin | `join_numeric_calibration_snapshot` | Chỉfullcalibration_predict; không tái dùng nguyên hàm choouter |

Các API trên được rà từ source tương ứng trong `src/knowledge_tracing/akt/`. Không gọi `runner.run_full_fold` vì entrypoint này còn chọn epoch và refit, trong khi4weightsrefit90 đã có.

## 4. Quyết định kỹ thuật cần root chốt

**Đường tái dùng ngắn nhất** là một sourcerelease có kiểm soát sau khi nghiệm thu đủ4calibrator. Điều kiệnOOVcache cần dựa vào `view.allowed_folds`, rồi dựng cache đầy đủ nguyên nativewindows+UnseenTarget để giữ mọi rank và144OOV. Đây là thay nguồnKT và sourceidentity nên chưa được thực hiện trong nhánh này. Sourceidentity/binding compatibility phải được xử lý rõ trước khi dùng model/calibrator cũ. Không chỉnh sourcehash hoặc binding cũ để cho qua.

Sau release hợp lệ, CPU local/Colab dựng fulloutercache+admission và3graphcaches, upload Drive. H100 đọc cache, chạy4weights lần lượt, ghi numericshards, commit và trả GPU ngay. CPUlocal/Colab replay đúngrawsource/geometry để nối nhãn, xuấtOOVnull, apply4frozenT và thống kê. Đường publicCPUreplay cho phép nốiOOV lại màkhông numericprobabilitygiả.

**Giữ tuyệt đối nguồn hiện hành** đồng nghĩa chưa có productiontypedcacheouter hợp lệ. Có thể dùng nativeiterator từ `free_outer_evaluation.py` nhưng vẫn kèmCPU đọc/encode/join trong vòngsuy luận. Đây là fallback để kiểmđốichiếu, chưa đáp ứng yêu cầu đưa CPU ra khỏi thời gian thuêH100. Tạo formatinput/admission/loader/GPUloop mới ngoàiKT sẽ là một nhánh kiến trúc lớn hơn sửa guard, nên đã dừng ở chẩn đoán theo phạmvi đượcgiao.

## 5. Nghiệm thu và phần còn thiếu

Log [OUTER_PUBLIC_API_TEST01.txt](../runs/junyi-calibration-real-20261117-01/OUTER_PUBLIC_API_TEST01.txt) có **16PASS/1XFAILstrict trong4,60s**. Trong đó2test mới chứng minh giới hạnknown-onlyfilter,11testwrapper và3testboundaryđạt. XFAIL giữ lỗiOOVfold4 hiện hành. Toàn bộ kiểm dùng dữ liệu tổng hợp, không nghiệm thu CUDA hoặc model nghiên cứu thật.

Chưa cần thêmtraining để sửa vấn đề này. Cần đóng4calibrator, quyết địnhsourcecompatibility/release, CPUcount/prepouter đầyđủ và launcherproduction. Holmfamily/p-valuerecipe final phải đốichiếu protocol đã duyệt trước xemoutermetrics; Recipe26 chỉ chốt bootstrapseed42/2000draws/upper0,975 cho Devselector, không tự thành finalsignificance.
# Cập nhật sau release guardfold

Guardfold đã sửa theo `view.allowed_folds` và kiểm75ca cùng đường outer/compatibility. Gói nguồn mới từD22 giữ đúng một delta guard và upstreamLF, identity7c72414e…, được dựng riêng trong cache. Các biên nhận `OUTER_SOURCE_PACKET_MANIFEST01.json` và `A2_OUTER_SOURCE_ACTUAL_VERIFY01.json` tại bundle calibration thật xác nhận77sourcefile và pin A2 bằng file thực. Predictor, numericalparity và cacheouter toàn cohort còn chờ. Phân tích dưới đây giữ lý do bác bỏ cách lọc OOV thành sidecar và căn cứ cho sửa guard.

