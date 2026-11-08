# RQ1 — trạng thái ước lượng, cổng mastery và ba câu tham chiếu

**Kết quả mới:** trên cùng lịch sử truy vấn đã lưu, khác biệt trạng thái số không tự chuyển thành khác biệt mastery boolean. Trong 30.240 cặp **khái niệm–thời điểm full/empty**, có 3.428 cặp đổi cổng bất định nhưng giữM,90 cặp đổi cổngθ vàM, còn 26.722 cặp giữ cả hai cổng. Đây là chẩn đoán quy tắc native, **không phải đánh giá độ đúng của mastery/calibration hoặc lợi ích học tập**.

Nguồn số: [summary](../runs/rq1-prediction-mastery-trace-20261109-01/summary.json), [validation](../runs/rq1-prediction-mastery-trace-20261109-01/validation.json), [đối chiếu raw độc lập](../runs/rq1-prediction-mastery-trace-20261109-01/native_mastery_gates_crosscheck01.json). Các alias do archiver cố định; chỉ phát hành sau khi ROOT đóng bundle và kiểm các liên kết. Không thay báo cáo người đọc hiện hành trong đợt này.

## 1. Vì sao phải đo state và hai cổng riêng?

[Phân tích controller trước](rq1_fixed_controller_candidates_20261109.md) đã phục hồi chính xác R/C/B và khóa chọn CID. Chỗ còn thiếu của RQ1 là sự liên hệ giữa prediction và boolean mastery: native GAM **không** đặtM bằng `P_query>=.5` hoặc ngưỡng trên mastery_score.

Nguồn `GAMKTPolicy.is_mastered` dùng:

`T=(theta_est>=1250); U=(pi_task<=.55); M=T AND U`.

`theta_est` là state ước lượng trên thangElo; `pi_task` là tham số bất định native, không là xác suất nắm vững đã hiệu chuẩn. `S_legacy` dùng virtualconceptfeature ở1250; `P_query` dùng câu hỏi thật/difficulty và time-decay. Trong fixed runner, S/M/P là các readout từ cùng pre-update state; không suy P hiện tại là causalparent củaM cùngbước. P cùngcachedy đi vào update cho state tươnglai. Selector xếp CID theo S vàcontext, không trực tiếp theo queryP.

Trace mới thêm θ/pi toàn bộ 28 concepts và3rawreal-reference probabilities của **concept đang được hỏi** (difficulty1050/1200/1350). Currentquery đã là một trong3 nên reuseP, chỉ thêm2probes trên deepcopy. Mean3 rawrefs được so vớiτ0.5637150147511514 theo định nghĩa tham chiếuV1, **chưa có calibratorT**, không đổi controller/M/hyperparameters. Không dùng currentqueryy làm nhãn cho virtualconceptscore hoặc mastery.

## 2. Population, bảo toàn hành vi và đơn vị

Cùng 9 chuỗi lịch sử20000–20002×PG/PY/PYH, mỗi chuỗi 120 events. Full vàempty cùng enabled graphpackage; chỉ estimator-edge input khác, controllergraph đầy đủ giữ nguyên. Nativehistory/update pathways có thể khác theoedges; contrast này không là direct-logit-only hoặc chất lượng riêng từngedge. Không tạo teacher/world/responses/RNG mới; dùng lạicachedqueries/y. Source fixed runner đã phục hồi từGit e4e6a262…, không mang provenance-gap của nhánh closed-loop khác.

18 policy instances hoàn tất 2.160 online updates,6.480 predict,2.160 preview select,4.320 ready_set; actual native S 67.060/M 284.290 (direct S/M 60.480 mỗi loại). Cả 2.160 P/S28/M/R/fullpreview và18 initial + 18 final fingerprints khớp C13 trước analysis.18 gzip đóng riêng, 120 records mỗi file, đầy đủCRC/keys; [nativeworkerreceipt](../runs/rq1-prediction-mastery-trace-20261109-01/native__worker_run.json) và [ROOTouter](../runs/rq1-prediction-mastery-trace-20261109-01/native_outer__final.json). Native14fixtures vàpure8analysisfixtures là kiểm kỹ thuật, không researchN.

- 1.080 paired event snapshots: cùngseed/profile/event/query/y, full soempty.
- 30.240 paired concept snapshots: 1.080 × 28, lặp state qua thời gian; không30240independent learners.
- 2.160 queried-arm rows: mỗivariant tại một currentquery; không đánh giá cả28truthconcepts.

Profiles vàseedblocks chỉ phân tầng mô tả, không controlledabilityeffect. Reusedstreams/newN0; không p-value/CI hoặc generalization. Action cũ là preview, không served learningoutcome.

## 3. Khác biệt hai cổng đã bị che ở đâu?

Mãcells là `(T_full≠T_empty,U_full≠U_empty,M_full≠M_empty)`; đây là **so sánh hai điều kiện ở cùng snapshot**, không chuyển trạng thái theo thời gian.

|Mã|Số cặp khái niệm–thời điểm|Diễn giải|
|---|---:|---|
|000|26722|Cả hai gate vàM giống nhau; **không** có nghĩa θ/pi numeric giống nhau|
|001|0|Bất khả thi nếuM làAND đúng nguồn|
|010|3428|GateU khác, gateT/M giữ|
|011|0|Không quan sát|
|100|0|Không quan sát|
|101|90|GateT vàM khác, gateU giữ|
|110|0|Không quan sát|
|111|0|Không quan sát|

Đối chiếu raw độc lập từ18gzip, không dùng hàm analyzer, xác nhận:

- Ở 3.428 cặp 010, θ ở cảhai dưới1250; full không qua gatepi, empty qua. Mfalsecảhai vì AND. Khác biệt bất định bịθ-gate thấp che trong boolean này, không chứng minh uncertainty full sai.
- Ở 90 cặp 101, cảhai qua gatepi; fullθ≥1250 vàemptyθ<1250 nênMfull=true/Mempty=false. Đây là lời giải thích **cơ học của phép phân loại snapshot**, không phải 90 learning transitions hay 90 lần học đượcconcept.

Có 90 event snapshots cóM-set khác và 90 concept-pair disagreements **trong cohort này**. Legacyfield tên `M_concept_crossings` được giữ để đối chiếu, nhưng “crossings” ở đây làcross-conditionclassificationdisagreements; không thời-điểm vượt ngưỡng, không phải 90 concepts khác nhau. Cùng mộtconcept có thể bất đồng qua nhiều t.

Hai witness được chọn bằng quy tắc firstchronological cho cell, không theo outcome gain:

|Cell; seed/profile/t; concept|θfull/empty|pi full/empty|Mfull/empty|
|---|---|---|---|
|010;20000/PG/t=9;NhanBietCacTrungBinhHoc|1184.5248/1184.3321|.5675/.5400|false/false|
|101;20001/PG/t=83;VanDungHamSoBacHaiDeGiaiBaiToanThucTien|1250.1128/1248.3928|.331851/.292486|true/false|

t là event index zero-based. Raw values đầy đủ và rule chọn witness nằm trong crosscheck JSON. Không dùnghai ví dụ thay toàn population.

## 4. Numericstate khác nhiều hơn gate, nhưng chưa có truth để gọi đúng/sai

|Rawdifference full−empty trên30240cặp|θ_estimated (Elo-scale)|pi_task (dimensionless)|
|---|---:|---:|
|Numeric khác|20319|20319|
|Dương/âm/zero|16963/3356/9921|20319/0/9921|
|Mean delta|.3690689563|.0163002503|
|Mean absolute delta|.4776414790|.0163002503|
|Min/max delta|−2.7578184371/7.0318577748|0/.0569157762|

Hai marginal 20.319 bằng nhau **không chứng minh cùng nhữngrecords thayθ vàpi**; analysiskhôngđăngký intersection này. Meanθ nhỏ không chứng minh practicalsignificance hay learninggain: đây là ước lượng model, không latentteacherθ. Fullpi cao hơn ở 20.319 cặp cũng không tự là “uncalibrated hơn”; chưa có evaluationtruth. GateT khác ở90events, gateU khác ở880events; hai đơn vịevent này khác countsconceptpairs trong bảng trên.

## 5. NativeM và rawreferencecriterion không tương đương

Trên 2.160 queried-arm rows:

|NativeM|Mean3rawrefs≥τ|Số rows|
|---|---|---:|
|false|false|1748|
|false|true|253|
|true|false|0|
|true|true|159|

253 bất đồng đều là rawcriteriontrue/nativeMfalse (full113,empty140). Đây là **bảng agreement giữa hai readout**, không confusionmatrix với nhãntruth; không phải 253 errors hoặc chứng minh calibration kém. Cần evaluator độc lập trên đúnglearner/history vàteacherreference target để đánh giá độ đúng; oracle không được mở/dùng vào model trongrun này.

So sánh **thayđổi giữa full vàempty** tại cùng current query:

|QuerynativeM đổi?|Rawcriterion đổi?|Paired events|
|---|---|---:|
|Không|Không|1053|
|Không|Có|22|
|Có|Không|5|
|Có|Có|0|

5 query-M differences và 22 raw-criterion differences không trùng nhau trong bảng này. Hai con số khác 90 M-set events bởi currentquery chỉ chọn mộtconcept. Con số 22 raw criterion cũng **không được đồng nhất** 22 preview changes của báo cáo cũ; chúng là biến khác, analysis này không tính giao vớipreview. Không gọi trườnghợp này “score-only” hoặc causalmediation.

## 6. Giữ toàn bộ nhóm và concept, kể cả kết quả bằng0

Mỗirow dưới báo **số event snapshots** có bấtđồng; cột “Mconceptpairs” là số cặpconcept–thờiđiểm, không temporaltransitions. Profile/seedtables lồng nhau, không cộng chúng như thêmindependentN.

|Nhóm|Paired events|M-set events|Mconceptpairs|T-gate events|U-gate events|Query-M differences|Rawcriterion differences|
|---|---:|---:|---:|---:|---:|---:|---:|
|pooled|1080|90|90|90|880|5|22|
|profile:PG|360|86|86|86|236|4|8|
|profile:PY|360|0|0|0|322|0|7|
|profile:PYH|360|4|4|4|322|1|7|
|seed:20000|360|0|0|0|257|0|11|
|seed:20001|360|18|18|18|350|1|6|
|seed:20002|360|72|72|72|273|4|5|
|trajectory:20000:PG|120|0|0|0|65|0|3|
|trajectory:20000:PY|120|0|0|0|96|0|4|
|trajectory:20000:PYH|120|0|0|0|96|0|4|
|trajectory:20001:PG|120|18|18|18|114|1|3|
|trajectory:20001:PY|120|0|0|0|118|0|2|
|trajectory:20001:PYH|120|0|0|0|118|0|1|
|trajectory:20002:PG|120|68|68|68|57|3|2|
|trajectory:20002:PY|120|0|0|0|108|0|1|
|trajectory:20002:PYH|120|4|4|4|108|1|2|

Perconcept pooled: mỗiconcept có1080state-snapshot pairs, **không**1080câu hỏi củaconcept haytrain-support count. SummaryJSON giữ cảfinite numeric-delta summaries vàall8cells cho28concepts; bảng dưới giữzero cases.

|Concept ID|Bất đồngM full/empty|U-gate differences|
|---|---:|---:|
|MenhDeVaTapHop|0|0|
|MenhDe|0|123|
|TapHop|0|174|
|CacPhepToanTrenTapHop|0|90|
|HieuMenhDeVaDieuKienLogic|4|214|
|NhanBietKhaiNiemCoBanVeTapHop|0|303|
|ThucHienPhepToanTrenTapHop|0|48|
|XacDinhTinhDungSaiCuaMenhDe|0|214|
|VanDungPhepToanTapHop|0|88|
|BatPhuongTrinhBacHaiMotAn|0|0|
|DauCuaTamThucBacHai|0|129|
|GiaiBatPhuongTrinhBacHaiMotAn|0|28|
|GiaiThichDinhLyVeDau|0|135|
|GiaiDuocBatPhuongTrinhBacHai|36|14|
|PhuongTrinhQuyVePhuongTrinhBacHai|0|79|
|VanDungDuocBatPhuongTrinhBacHai|0|4|
|GiaiPhuongTrinhChuaCanThuc|0|175|
|HamSoBacHaiVaDoThi|0|0|
|HamSoVaDoThi|0|11|
|NhanBietDinhNghiaDuocHamSo|12|104|
|HieuKhaiNiemCoBanVeHamSo|0|132|
|NhanBietCacTrungBinhHoc|0|270|
|VanDungHamSoDeGiaiQuyetVaiBaiToan|0|327|
|HamSoBacHai|20|88|
|NhanBietHinhDangCuaDoThiParabol|0|46|
|TimTapGiaTriCuaHamSoBacHai|0|302|
|VeDoThiParabolCuaHamSoBacHai|0|142|
|VanDungHamSoBacHaiDeGiaiBaiToanThucTien|18|188|

## 7. Phạm vi kết luận và đường bằng chứng

Kết quả tiến RQ1 từ các marginal P/M/R sang cơ chế của **mastery native hiện hành**: cổngAND che nhiều khác biệtstate, vàrawreference criterion không là bản thaythế tươngđương. Nó không trả lời mastery nào đúng với learnerlatentstate, không đánh giá responsecalibration, không chứng minh controller học tốt hơn hoặc edgescausal. Reference/calibration/controllerV1 áp dụng cho researchmode phải được kiểm riêng; không nâng native trace thành fittedneuralmodel/RQcomplete.

Native03 ROOTterminal200.3490072s; storedouter200.0550102s là elapsed trước receipt. Analysis ROOTownedaccepted1.9611873s/10, không nativecalls; pure8capture.1934681s. Nguồn14fixture native và8analysisfixture cóscope khác, không cộng thành số mẫu nghiên cứu. RSS/peak guard512MiB/free1GiB; ROOTrecordedpeak133324800B. KhôngGPU/NNoptimizer/remote/spend.

Các setupfailure/timeout trước và benchmarkmanufactured không bị viết lại: [failure report](rq1_prediction_mastery_trace_failures_20261109.md), [microbenchmark](mastery_observer_cost_microbenchmark_20261109.md). Original60STOPcharged56.3709122;03làallocation300mới explicit, không hiddenreset/retry. Microbenchmarkratio không dùng suyGAMruntime. Native03/control/analyzer/crosschecksource vàreceipts được snapshot trongbundle mới; cached3240gzip/nguồn154/bundles cũ chỉ thamchiếuSHA, không copy lại.

Scienceoutputs: summarySHA625095a6421b050f0592e9aecfa4767690ed863d3a5489a414a7b614fb3dde38; analysis source52370bcc…ade27; acceptedROOTouter81cf9dd9…4594. CrosscheckJSONca428a9c…cc573 độc lập xác nhậncells/directions/witnesses/18CRC. Closuremanifest xác nhận archiveintegrity, không thêmindependentN hoặc nghiêncứu mới.

