# RQ1 — khả năng chẩn đoán hiệu chuẩn từ cache hiện có

09/11/2026. Bản chuẩn bị source-only. Đã đọc source, manifest/report và một record đầu của các gzip để xác định schema. Chưa phân tích toàn bộ rows, fit temperature, chạy model/world, test, import Python hoặc Git trong task này. Kế hoạch là phân tích thứ cấp mô tả trên seeds/endpoints đã xem, với new independent N0. Giữ các kết quả hữu hạn, không p-value, CI hoặc generalization claim.

## Dữ liệu nào trả lời được câu hỏi nào?

| Cache chính xác | Population đã nghiệm thu | Fields liên quan | Khả năng và giới hạn |
|---|---|---|---|
| `research_tracking/runs/cpu-factorial-20261107-01/traces.jsonl.gz` | 10seeds21000–21009×3personas×2policysettings×2λ×120steps =14.400served rows/120worlds | prediction,y,p_true,theta_before,concept,question,step,flags | Có thể tách response reliability so với observed y và world p_true tại đúng served item/history. Mỗi arm có distribution riêng sau feedback divergence. Trace thiếu native M/pi và reference3 predictions để chấm native mastery/ref criterion. |
| `research_tracking/runs/rq1-query-observability-reproduction-20261108-01/observed_legacy.jsonl.gz` và `observed_query_sidecar.jsonl.gz` | 9fixed streams, seeds20000–20002×PG/PY/PYH×120, ba variants =3.240arm rows | P,y,native score28/M/R; sidecar query/difficulty/time/legacy-rowSHA | Chọn full/empty có2.160rows trên1.080shared query/y identities, phù hợp response reliability mô tả trên cùng logging population. World p_true/true theta không được ghi trong fixedstream cache này. Graph-free có thể được báo riêng để giữ distinction package/edge. |
| `research_tracking/runs/rq1-prediction-mastery-trace-20261109-01/native__trace-01.jsonl.gz` … `native__trace-18.jsonl.gz` | 18streams×120=2.160queried-concept snapshots, 6.480raw reference probability entries | query,raw_references3,raw_reference_mean,raw_reference_criterion,native_state(theta_est,pi,T,U,M),frozen-stateSHA | Có thể join đúng y của actual query qua legacy/query bindings. Hai reference items còn lại mỗi snapshot có prediction nhưng thiếu riêng observed/oracle outcome. Score/criterion/native-M agreement đã được báo, tự nó chưa đánh giá đúng/sai latent mastery. |

Các population này giữ riêng. CPU09 là S/P joint on/off với Loff, common full world/controller graph. RQ1 full/empty là estimator-edge-set contrast trong cùng enabled package, cùng logged history. Query của CPU09 là served closed-loop, còn lựa chọn trong fixed RQ1 là preview. Mười reused CPU09 seed clusters và ba reused fixedstream seed clusters không được cộng thành independent confirmation mới.

## Đề nghị nhỏ nhất có thêm nội dung nghiên cứu

Ưu tiên **một phân tích CPU09 response-reliability có oracle decomposition**, dùng nguyên admission/hash/grid của cache vừa được nghiệm thu. Các báo cáo cũ đã có global LL/Brier, endpoint I/Δ, exposure và divergence. Chưa thấy bảng reliability theo probability bin có cả y lẫn p_true và phân rã sai lệch từng bin. Câu hỏi mới là phần sai lệch quan sát quanh các mức P phản ánh chênh lệch với world response probability đến đâu, và phần nào chỉ thuộc realized binary responses trong tập quỹ đạo hữu hạn.

Giữ15bins equal-width theo source reporting hiện có `gam_kt/evaluation.py:15–16`, cùng `bkt_baseline/metrics.py:32–39`: bin=min(floor(15p),14), bin cuối chứa1. Mỗi bin ghi N, meanP, meanY, meanOracleP và ba đại lượng:

`empirical_gap = mean(P−Y)`

`oracle_response_gap = mean(P−p_true)`

`realized_response_residual = mean(p_true−Y)`

Kiểm arithmetic `empirical_gap = oracle_response_gap + realized_response_residual` trên từng bin. Đây là decomposition của cùng stored rows, chưa phải phép kiểm định hoặc chứng minh unbiasedness/generalization. Bin rỗng có count0 và means/gaps=null. Giữ mọi sign, mọi zero và tất cả bins. ECE15 theo Y có thể ghi để đối chiếu convention, nhưng không chọn binning/arm theo ECE thấp nhất. Chưa cần thêm scalar metric hoặc model calibration fit.

Group output giữ đầy đủ120seed/persona/arm groups,12persona/arm aggregates và4arm aggregates. Các seed groups hoặc strata được trình bày lồng nhau, không tăng N theo số bins/events. Main interpretation vẫn theo từng policy×λ served distribution. Có thể mô tả khác biệt giữa arms, nhưng không gọi đây là paired same-target accuracy/calibration sau khi queries/histories đã tách. Không chọn common-prefix như quần thể thay thế nhằm giữ effect thuận lợi.

Bin index7 nằm quanh response decision0,5, tương ứng Accuracy convention hiện tại. Nếu cần thêm band0,45…0,55 của diagnostics cũ, phải ghi rõ đó là response-only support convention. Thresholdτ_ref không dùng để thay band này. Phân tích quanh response0,5 không đánh giá native theta/pi/M hoặc concept reference mastery.

## Fixedstream RQ1 có thể bổ sung gì sau gói nhỏ trên?

P/y reliability theo15bins có thể làm trực tiếp cho full/empty trên cùng1.080identities, giữ pooled/3profiles/3seeds/9streams và các bin rỗng. Nó bổ sung nơi xảy ra under/overprediction và support, trong khi global LL/Brier đã được báo. Không cần chạy lại predictor.

Điểm cần sửa trong cách đọc legacy `threshold_local_calibration` là mỗi model tự chọn rows có |P−0,5|≤0,05 (`diagnostics.py:85–94`). Các mẫu số có thể khác nhau. Nếu phân tích band, giữ bốn nhóm joint membership của full/empty gồm both/full-only/empty-only/neither, đếm đủ identity population. So signed gaps trên cùng matched subset và báo support, đồng thời ghi việc subset được định nghĩa từ predictions. Đây là support/composition diagnostic, chưa ước lượng mediation hoặc calibration treatment benefit. Chỉ tính lại global LL/Brier để kiểm khớp artifact cũ, tránh phát hành lại chúng như phát hiện mới.

## Vì sao reference threshold vẫn cần bằng chứng riêng?

Native M là `(theta_est≥1250) AND (pi_task≤.55)`, còn pi_task là uncertainty parameter. ECE của P/y không xác nhận calibration của pi hoặc native M. Score S_legacy dùng virtual concept feature tại1250 cũng khác P của actual item.

Protocol21 dòng24–30 định nghĩa reference bank3items1050/1200/1350, τ_ref=0.5637150147511514 tương ứng mean true response probability tại theta1250. Research S là mean calibrated responses với frozen predictor/calibrator đúng roles. Raw mean3 trong diagnostic mastery chưa được temperature-calibrated. Áp τ_ref trực tiếp lên item-conditional P không đánh giá tiêu chí này, vì item difficulty khác nhau.

Một current-query y không được nhân ba để gán nhãn cho cả ba reference predictions. Sáu nghìn bốn trăm tám mươi entries là repeated model readouts, không thêm response labels hoặc independent N. Fixedstream chưa lưu true pre-update theta/p_true cho toàn reference bank nên chưa thể chấm false-positive/false-negative latent mastery ở từng concept–history. CPU09 có true theta_before của served concept nhưng thiếu native M và reference scores trong cùng records. Hai study không có cùng query/history/seed identity để ghép các fields đó.

Có một khả năng response-only cần review riêng nếu muốn tận dụng raw reference mean. Archived exact fixed runner `historical_runner.py:62–73` chọn qid bằng uniform integer trên danh sách84items, bank có đúng3items/concept. Theo logging design, difficulty có trọng số1/3 khi đã điều kiện vào queried concept, và probes dùng frozen pre-update state. Khi source/propensity/query independence và toàn84uniqueitems được kiểm đầy đủ, một y của actual randomly logged item có thể là một sample cho mixture response target của queried concept. Khi đó reliability của mean3 đối với y vẫn là **reference-mixture response reliability** trên queried concept histories, chưa là latent mastery calibration hoặc đánh giá tất cả28concepts. Chưa đưa nhánh này vào gói thực thi đầu tiên, và không xem đó là nhãn riêng cho từng off-policy reference.

## Hợp đồng phân tích tương lai và phần còn mở

First batch chỉ stream/hash gzip CPU09 đã đóng, exact120worlds/14.400rows, field probabilities finite0…1, y binary, source/manifest/grid đầy đủ. p_true được kiểm nguồn world `LatentStudentEnvironment.interact` cell9, và chỉ dùng posthoc evaluator. Giữ original actualitem query/difficulty binding, no oracle-to-model/confidence transfer. Các tests nhỏ trước execution cần known-answer bins gồm p0/p1/boundaryk/15, missing/duplicate rows, empty bins, oracleP=P thì oracle gap0 trong khi Y vẫn có thể noise, và decomposition identity.

Đề nghị tái dùng caps/cache reader đã có, whole60s/RSS1GiB/free2GiB với owned cleanup và SHA pre/post, thay vì dựng framework mới. Đây là đề nghị để Root duyệt exact source/inputs trước analysis. Output nhỏ gồm bin tables, group counts/gaps và receipt cùng nguồn/formulas/limits. Không fitT trên cùng used cache rồi gọi in-sample loss giảm là calibrated research result. Genuine temperature evaluation cần frozen predictor và role/seed-family separation của Protocol21, đồng thời vẫn cần truth/outcome cùng reference target để đánh giá mastery.

Kết luận khả thi hiện tại là có đủ cache cho response reliability và oracle response-gap decomposition. Calibration accuracy của concept mastery quanh theta1250/π.55/τ_ref vẫn cần fields đúng target/history và evaluation design riêng. Các agreement/masking counts đã công bố tiếp tục là chẩn đoán quy tắc native.

## Pins cho bước feasibility

Các SHA được đọc từ actual files, không sửa hoặc copy bundle đã đóng. Bảng pin các entrypoints dữ liệu chính cùng source định nghĩa metric/threshold. Manifest mastery pin toàn bộ18trace members cho một packet tương lai.

| File | SHA-256 |
|---|---|
| `research_tracking/runs/cpu-factorial-20261107-01/manifest.json` | `371985977d32ddd1f3b95c3bab9858d20e4e463b2284b057f1b94db78c5f5cee` |
| `research_tracking/runs/cpu-factorial-20261107-01/traces.jsonl.gz` | `2a136fbf627cfa59170deec54c10ae562c2f8214eb00970ce41b96c43d065dcc` |
| `research_tracking/runs/rq1-query-observability-reproduction-20261108-01/manifest.json` | `112cd15f69b63fec730a4b4a67acf98650986adc58138f68ef4a5105adbf81d7` |
| `research_tracking/runs/rq1-query-observability-reproduction-20261108-01/observed_legacy.jsonl.gz` | `eeef1796da63e3fb8c9c02b4af2065491a9ff744cfe276b05f78d12f90f4206d` |
| `research_tracking/runs/rq1-query-observability-reproduction-20261108-01/observed_query_sidecar.jsonl.gz` | `6452e88c62c4fe33b1ce759015c6ef0f1cab4c79f82d57e1a029069662564939` |
| `research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01/historical_runner.py` | `402dca905694d850f126e41f3b5dcc91b327e986ae2cfbb240dda739eed8dd45` |
| `research_tracking/runs/rq1-prediction-mastery-trace-20261109-01/manifest.json` | `a45099f30ab6d4e239275fae6e40cf174b2dcac615fcb55a6e2b9d79f0c35ae3` |
| `research_tracking/runs/rq1-prediction-mastery-trace-20261109-01/validation.json` | `13c90b544299362e56bbd7035c83063e12796d46679a4bbab62a6cdd8ca81f02` |
| `research_tracking/runs/rq1-prediction-mastery-trace-20261109-01/prediction_mastery_trace_worker03.py` | `fc067d67ebc9018722aa66367fc186fe4a10e0f0b112475372f8024d4d74d631` |
| `src/knowledge_tracing/diagnostics.py` | `651da44e7f8e2ce94fc5733f8a962d6fb1a5776d08c8224fb86aab879ac24d95` |
| `src/knowledge_tracing/gam_kt/evaluation.py` | `c39b6ca9c87dc92f9e3a6dc7636f5249c7c33f69549284bdcf844c4958acaa65` |
| `src/knowledge_tracing/bkt_baseline/metrics.py` | `359502d7e7a4ee822841dbf603206d84ec5a5d2f85a4cd012e5ec7fd5495158b` |
| `docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md` | `c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6` |
| `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb` | `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f` |
| `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/question_bank.csv` | `fb5924ac0d19049ef1a5be23352592e30dfa3a4bde3e3fa07f10979fe0887e4d` |
