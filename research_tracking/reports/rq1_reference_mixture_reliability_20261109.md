# RQ1 — Độ khớp của forecast hỗn hợp ba câu reference

Ngày09/11/2026. Phân tích mô tả hậu nghiệm trên fixed stream đã lưu. Không sinh thêm đáp án, chạy lại policy hoặc fit calibrator. Tình trạng đóng gói được xác định bởi manifest của [bundle bằng chứng](../runs/rq1-reference-mixture-reliability-20261109-01/manifest.json). Các liên kết tới bundle này được materialize khi ROOT đóng gói, không tự là bằng chứng closure trước thời điểm đó.

## 1. Câu hỏi nghiên cứu và đúng đối tượng cần đo

RQ1 cần làm rõ vì sao thay đổi dự đoán không luôn dẫn đến thay đổi quyết định. Các phân tích trước đã tách native mastery, ready set và các tập ứng viên của controller. Một khoảng trống còn lại là score trung bình trên các câu reference có khớp tần suất trả lời đúng hay không. Không thể lấy xác suất của một câu đang hỏi làm truth cho mastery của cả concept, hoặc dùng một đáp án làm nhãn cho cả ba câu reference chưa được phục vụ.

Fixed runner hiện có tạo ra một cách đánh giá response-mixture hợp lệ theo thiết kế logging. Mỗi bước lấy đều một câu trong ngân hàng cố định84câu, gồm28concepts, mỗi concept đúng ba câu có difficulty1050/1200/1350. Việc lấy qid không phụ thuộc estimator hoặc selector. Có điều kiện theo concept và history trước đáp án hiện tại, difficulty của câu được lấy có phân phối đều trên ba reference theo source. Do đó một đáp án đã ghi là một mẫu response cho hỗn hợp này. Phân phối thiết kế không đòi tần suất hữu hạn thực tế phải cân bằng. [Fixed runner đã khôi phục](../runs/rq1-fixed-edge-set-contrast-20261108-01/historical_runner.py), [loader reference](../runs/rq1-fixed-edge-set-contrast-20261108-01/source__paper2_reference.py)

Forecast được đánh giá là `q = (p1050 + p1200 + p1350)/3` của queried concept trên state đông cứng trước current-label update. Các readout reference được lưu trong trace đã được admit đủ2160legacy rows và18initial/final fingerprints. Current-item P được dùng lại cho một reference, hai reference còn lại đọc trên clone giữ nguyên state. Capture không nhận y. Phân tích này chỉ đọc cache. [Source capture](../runs/rq1-prediction-mastery-trace-20261109-01/prediction_mastery_trace_worker03.py), [validation trace](../runs/rq1-prediction-mastery-trace-20261109-01/validation.json)

Về mặt target, `E[Y | H,C,t]` dưới logger này là trung bình ba xác suất response của teacher tại cùng history/concept/time. Đó là lập luận từ source sampling. Không đọc, tính hoặc kiểm oracle probabilities trong phân tích này. Native mastery vẫn là quy tắc khác, `theta >= 1250 && pi_task <= .55`. Kết quả dưới đây không đánh giá truth hoặc accuracy của quy tắc đó.

## 2. Quần thể, ngưỡng và phép đo đã chốt trước khi tính

Giữ nguyên3seed blocks20000–20002 ×3profilesPG/PY/PYH ×120events, tức9paired trajectories và1080query–response. Hai arms `graph_package` và `empty_graph_package` được ghép chính xác theo seed/profile/event, full query/timestamp và y, tạo2160arm rows. Mỗi arm-row dùng đúng một y cho một forecast mean3. Hai arms dùng lại cùng1080labels, không tạo2160quan sát độc lập hoặc6480reference labels. `new_independent_N=0`. [Contract đã chốt](../runs/rq1-reference-mixture-reliability-20261109-01/rq1_reference_mixture_contract01.json), [các dòng đã ghép](../runs/rq1-reference-mixture-reliability-20261109-01/joined_rows.jsonl)

Dùng15equal-width bins, `bin=min(int(q*15),14)`, bin cuối chứa1. Signed gap là `mean(q)-mean(y)`. ECE15 là tổng `n_bin/n_view × abs(gap_bin)`. Giữ bin rỗng với count0 và mean/gap null. Ngưỡng raw reference cố định là0.5637150147511514. Hai phía `<tau` và `>=tau` chỉ báo count, mean forecast, mean response và signed gap. Không fit temperature, chọn ngưỡng lại hoặc thêm estimator calibration.

Toàn bộ16group specifications gồm pooled1, profile3, seed3 và trajectory9, nhân2arms thành32views. Giữ đầy đủ480bins và64threshold strata, kể cả rỗng, trong [summary gốc](../runs/rq1-reference-mixture-reliability-20261109-01/summary.json). Các dòng được dùng lại ở các cấp tổng hợp, các bảng không tạo thêm mẫu.

## 3. Kết quả response-mixture reliability

### Gộp chung và theo profile

Mỗi ô là ECE15 của raw mean3, đơn vị xác suất response. Số được làm tròn6chữ số để đọc, JSON giữ binary64 values.

| Nhóm | Query–response/arm | Full graph package | Empty graph package |
|---|---:|---:|---:|
| Gộp ba profiles | 1080 | 0.043185 | 0.042526 |
| PG | 360 | 0.263534 | 0.261267 |
| PY | 360 | 0.131945 | 0.137415 |
| PYH | 360 | 0.069198 | 0.075091 |

ECE gộp nhỏ hơn nhiều ECE của từng profile. Trong cả hai phía ngưỡng, PG có mean forecast thấp hơn mean response, còn PY và PYH có mean forecast cao hơn mean response. Vì vậy số gộp không đại diện cho độ khớp trong từng profile. Full có ECE cao hơn empty ở PG, thấp hơn ở PY/PYH. Những kết quả này không hỗ trợ kết luận cải thiện đồng nhất. [Toàn bộ32views và các signed gaps](../runs/rq1-reference-mixture-reliability-20261109-01/summary.json)

### Theo cả ba seed blocks

| Seed block | Query–response/arm | Full | Empty |
|---|---:|---:|---:|
| 20000 | 360 | 0.038275 | 0.043004 |
| 20001 | 360 | 0.071961 | 0.068058 |
| 20002 | 360 | 0.067465 | 0.064573 |

### Cả chín paired trajectories

| Seed | Profile | Query–response/arm | Full | Empty |
|---|---|---:|---:|---:|
| 20000 | PG | 120 | 0.262482 | 0.265749 |
| 20000 | PY | 120 | 0.127338 | 0.133409 |
| 20000 | PYH | 120 | 0.075261 | 0.087123 |
| 20001 | PG | 120 | 0.234674 | 0.232413 |
| 20001 | PY | 120 | 0.210563 | 0.199099 |
| 20001 | PYH | 120 | 0.067752 | 0.080616 |
| 20002 | PG | 120 | 0.299089 | 0.296824 |
| 20002 | PY | 120 | 0.102120 | 0.103043 |
| 20002 | PYH | 120 | 0.089952 | 0.102411 |

Các hướng full–empty không giống nhau giữa seed/profile. Không chọn trajectory thuận lợi để thay bảng gộp. Các seed cũng là những blocks cũ đã tái dùng, không là các replications mới. Không CI, p-value hoặc suy rộng ra năng lực người học ngoài các trajectories này.

### Score ở trên ngưỡng raw reference

| Nhóm | Arm | n có q≥tau | Mean q | Mean y | Signed gap |
|---|---|---:|---:|---:|---:|
| Gộp | Full | 195 | 0.608980 | 0.753846 | −0.144866 |
| Gộp | Empty | 217 | 0.606643 | 0.728111 | −0.121468 |
| PG | Full | 149 | 0.613252 | 0.825503 | −0.212251 |
| PG | Empty | 157 | 0.611895 | 0.821656 | −0.209761 |
| PY | Full | 13 | 0.585260 | 0.461538 | +0.123721 |
| PY | Empty | 20 | 0.583233 | 0.400000 | +0.183233 |
| PYH | Full | 33 | 0.599037 | 0.545455 | +0.053583 |
| PYH | Empty | 40 | 0.597734 | 0.525000 | +0.072734 |

Ví dụ vùng trên ngưỡng của PY chỉ có13 hoặc20rows. Hai arms không nhất thiết có cùng membership trong stratum vì q khác nhau. Đây là các nhóm được điều kiện bằng forecast của từng arm, không phải paired effect trên cùng subset. Phía dưới ngưỡng và mọi seed/trajectory strata vẫn nằm trong64strata gốc. Không diễn giải n195/217 là số người đã mastered, meanY là mastery probability, hoặc signed gap là mastery error rate.

## 4. Điều gì được làm rõ cho RQ1

Đã có một phép kiểm response-target phù hợp cho raw reference mixture trên cùng fixed history. Nó bổ sung một mảnh bằng chứng giữa dự đoán và các quy tắc controller. Sai lệch trái dấu theo profile còn thấy rõ khi chuyển từ actual-item P sang mean3-mixture, và ECE pooled có thể che các sai lệch này. Kết quả cung cấp lý do phải tách target và profile khi kiểm calibration trong vòng nghiên cứu chính.

Phép kiểm này không chứng minh mean3 được calibrated, không cho biết native M đúng hay sai, và không đo cải thiện học tập do graph. Full/empty là edge-set ablation bên trong cùng package đang bật, graph information có thể thay đổi update pathways. Không tách được individual-edge quality hoặc tác dụng nhân quả riêng của một cạnh. Score raw không phải temperature-calibrated V1. Tác vụ native-mastery truth replay đã dừng vẫn không được thay bằng các đáp án mixture này.

## 5. Kiểm số học, execution và lịch sử failure

ROOT thực chạy cached analyzer một lần, accepted với đủ2160arm rows/1080query–Y/32views/480bins. Worker ghi1.0967958s trước receipt, outer lưu1.4970078s, ROOT thông báo1.5012412s sau finalwrite và toolwall2.0847346s, đều trong cap10s. Các thời gian lồng nhau không cộng lại. Owned process clean exit, Job active0, cleanup accepted, môi trường khôi phục, không postwrite rejection. Outer đọc lại actual four-file hashes/sizes và kiểm source/input SHA sau thao tác. Không tuyên bố worker đã fsync mọi output chỉ từ in-memory hashes. [Actual outer](../runs/rq1-reference-mixture-reliability-20261109-01/cached_outer__final.json)

Kiểm độc lập của ROOT dùng Decimal precision50 tính lại từ2160joined rows, đối chiếu đủ32groups/480bins/64strata trong0.0607666s/cap5. Tolerance rel1e-13/abs1e-14 chỉ dùng cho đối chiếu số học Decimal–binary64. Các query/y/source/mean wire-exact admissions của analyzer không được nới. [Receipt số học](../runs/rq1-reference-mixture-reliability-20261109-01/reference_mixture_numeric_check01.json), [source kiểm độc lập](../runs/rq1-reference-mixture-reliability-20261109-01/crosscheck_reference_mixture_numeric01.py)

Pure01 thực chạy8cases,7PASS/1FAIL trong0.2433938s. Failure là known-answer fixture so exact constant-folded expression với Python3.13 improved sum, khác1ulp. Sau khi snapshot old test/contract và before/copy/after SHA, chỉ assertion của fixture được đổi sang tolerance1e-15. Analyzer không đổi. Pure02 thực chạy8PASS trong0.2771935s. Đây là manufactured fixtures, không là tám samples nghiên cứu. Old failure/logs/snapshots được giữ cùng actual cached outputs trong bundle. [Pure01 raw](../runs/rq1-reference-mixture-reliability-20261109-01/pure01__result.json), [pure02 raw](../runs/rq1-reference-mixture-reliability-20261109-01/pure02__result.json)

Source trước/sau và closed manifests được ghim trong [validation](../runs/rq1-reference-mixture-reliability-20261109-01/validation.json). Gzip cũ và18native traces được tham chiếu bằng SHA ở các bundles đã đóng, không nhân bản lại trong gói này. Closure chỉ xác nhận tính toàn vẹn gói cùng review đã ghi. Phân tích vẫn là mô tả hậu nghiệm với newN0, không hoàn thành RQ1 hoặc thay thế thí nghiệm research models/calibration/controller theo protocol.
