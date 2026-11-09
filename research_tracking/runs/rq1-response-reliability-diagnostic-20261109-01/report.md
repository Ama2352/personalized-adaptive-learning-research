# RQ1 — Reliability của dự báo đáp án và sai lệch bị che khi gộp persona

Ngày 09/11/2026. Phân tích thứ cấp mô tả trên cache CPU09 đã công bố. Phân tích giữ nguyên mười seed, toàn bộ bốn arms và các bin rỗng. Không có lượt sinh thế giới, fit mô hình hoặc fit temperature mới. Kết quả thực tế đã được nghiệm thu trong receipt `e68aae35…ae6ca8`. Hồ sơ đóng gói được chuẩn bị riêng để đối chiếu nguồn và bản sao.

## 1. Vì sao cần đo thêm reliability?

Paper2 kết hợp dự báo đáp án với trạng thái tri thức và chính sách chọn bài. Một dự báo có thứ hạng tốt hoặc log loss trung bình thấp vẫn có thể lệch theo nhóm người học. Điều cần kiểm tra ở đây là khi hệ thống dự báo xác suất trả lời đúng gần một giá trị nào đó, tỷ lệ đúng quan sát được của những lần dự báo ấy có tương ứng hay không. Đây là một mắt xích cụ thể của RQ1, trước khi diễn giải dự báo thành quyết định học tập.

Các báo cáo trước đã nêu giới hạn của correctness quanh xác suất 0,5 và đã có các chỉ số dự báo tổng hợp. Phân tích này bổ sung phân bố reliability theo cùng 15 bins của evaluator baseline, giữ riêng từng persona và tách phần lệch so với xác suất tạo đáp án của simulator. Báo cáo RQ2 từ cùng cache tập trung vào exposure, query và label divergence. Nó chưa trình bày các bảng reliability này. Vì dùng lại dữ liệu đã xem, đây là phân tích thứ cấp khám phá. [Chẩn đoán trước](cpu_rq12_20261107.md), [pilot CPU09](cpu_pilots_20261107.md), [RQ2 từ cache](rq2_cached_mechanism_diagnostic_20261109.md).

## 2. Quần thể và phép đối chiếu

Nguồn gồm 10 seed 21000–21009, ba persona PG/PY/PYH, hai cấu hình policy và hai giá trị mechanism λ∈{0, 0,55}. Mỗi trajectory có 120 bước, tổng cộng 120 worlds và 14.400 dòng. Một persona-arm có 1.200 dòng và một arm gộp ba persona có 3.600 dòng. PG/PY/PYH là các profile khả năng tiềm ẩn do nguồn tạo, không phải ba mức scalar ability được can thiệp độc lập.

Trong báo cáo, `gOFF` tắt đồng thời parent signal và parent adaptation. `gON` bật cả hai. Local pathway tắt ở cả hai cấu hình, graph môi trường và graph controller giữ nguyên. Vì vậy, phép so này chưa cô lập tác động của từng cạnh và khác với phép so full-package/empty-graph ở các nghiên cứu fixed-stream. Hệ số 0,55 là giá trị nguồn đã dùng trong CPU09. Việc diễn giải tập trung vào hệ số này có lý do lịch sử, đồng thời bảng dưới giữ đầy đủ λ=0 để tránh chọn arm sau khi nhìn kết quả. [Nguồn factorial, hàm `factorial`](../../scripts/research/run_approved_cpu_pilots.py), [bundle CPU09](../runs/cpu-factorial-20261107-01/README.md).

Mỗi dòng dùng dự báo `prediction` trước cập nhật, đáp án `y` và `p_true` tại đúng bài, thời điểm và trạng thái thế giới đã phục vụ. Sau khi hành động hoặc đáp án phân kỳ, các arms có thể đi qua những bài và lịch sử khác nhau. Reliability vì thế mô tả quần thể được phục vụ của từng arm. Mười seed là mười cụm dùng lại. Ba persona và các lần biểu diễn lại cùng dòng trong bảng gộp không tạo thêm đơn vị độc lập.

## 3. Quy tắc đo và vai trò của oracle

Phép chia bin giữ đúng evaluator BKT/GAM-KT hiện có, với `bin=min(int(15P),14)`. Bin k có khoảng [k/15,(k+1)/15), riêng bin cuối chứa P=1. Mỗi bin lưu số dòng, trung bình P, trung bình Y và trung bình `p_true`. Bin rỗng có số đếm 0 và các trung bình bằng null. [Evaluator GAM-KT](../../src/knowledge_tracing/gam_kt/evaluation.py), [evaluator BKT](../../src/knowledge_tracing/bkt_baseline/metrics.py).

Ordinary ECE15 là tổng có trọng số `Σ_b (n_b/N)|mean(P)_b−mean(Y)_b|`. Nó đo chênh giữa forecast và feedback trong từng khoảng dự báo. Oracle-response ECE15 thay Y bằng `p_true`. Xác suất này thuộc mô hình tạo đáp án và chỉ được đọc hậu nghiệm ở evaluator. Nó giúp phân biệt lệch dự báo với dao động của đáp án hữu hạn trong simulator đã chọn.

Trong từng bin, đẳng thức có dấu được kiểm trực tiếp

`mean(P−Y) = mean(P−p_true) + mean(p_true−Y)`.

Sau khi lấy trị tuyệt đối và cộng các bins, hai ECE phải được tính riêng. Đẳng thức có dấu không cho phép cộng oracle ECE với một ECE của noise để suy ordinary ECE. Một fixture P=`p_true` nhưng Y hữu hạn còn dao động minh họa rõ giới hạn này. Toàn bộ quy tắc và các trường hợp biên được giữ trong [contract](../runs/rq1-response-reliability-diagnostic-20261109-01/rq1_response_reliability_contract01.json).

## 4. Kết quả đủ bốn arms

Bảng làm tròn sáu chữ số thập phân. Mỗi ô persona dùng 1.200 dòng, ô gộp dùng 3.600 dòng. ECE thấp hơn biểu thị lệch trung bình theo bins nhỏ hơn trên đúng quần thể đó.

| λ | Policy | Nhóm | Ordinary ECE15 | Oracle-response ECE15 |
|---|---|---|---:|---:|
| 0 | gOFF | PG | 0,200792 | 0,215098 |
| 0 | gOFF | PY | 0,171412 | 0,160990 |
| 0 | gOFF | PYH | 0,094043 | 0,087773 |
| 0 | gOFF | Gộp | 0,030269 | 0,032524 |
| 0 | gON | PG | 0,197034 | 0,212556 |
| 0 | gON | PY | 0,152721 | 0,150017 |
| 0 | gON | PYH | 0,089085 | 0,074047 |
| 0 | gON | Gộp | 0,040044 | 0,039275 |
| 0,55 | gOFF | PG | 0,200792 | 0,215098 |
| 0,55 | gOFF | PY | 0,171412 | 0,162006 |
| 0,55 | gOFF | PYH | 0,094876 | 0,088478 |
| 0,55 | gOFF | Gộp | 0,030547 | 0,032927 |
| 0,55 | gON | PG | 0,197034 | 0,212556 |
| 0,55 | gON | PY | 0,152529 | 0,150806 |
| 0,55 | gON | PYH | 0,089085 | 0,074731 |
| 0,55 | gON | Gộp | 0,040606 | 0,039902 |

Ở λ=0,55, cả ba persona có ordinary ECE15 của gON thấp hơn gOFF. Khi gộp ba persona, thứ hạng theo ordinary ECE15 đảo lại, với 0,040606 ở gON và 0,030547 ở gOFF. Bảng λ=0 cũng cho thấy hiện tượng tương tự. Đây là mô tả phép gộp trên các quần thể served riêng. Nó chưa xác định một policy làm calibration tốt hơn trên cùng query/history. [Số chính xác của 16 nhóm](../runs/rq1-response-reliability-diagnostic-20261109-01/synthesis.json), [toàn bộ bins](../runs/rq1-response-reliability-diagnostic-20261109-01/reliability.json).

### Vì sao ECE gộp thấp hơn nhiều?

Ở λ=0,55, trung bình dự báo thấp hơn xác suất thế giới của PG, nhưng cao hơn xác suất thế giới của PY và PYH. Hai phía có thể bù trừ khi những dòng cùng khoảng dự báo được đưa vào một bin chung.

| Policy | Persona | Mean P | Mean Y | Mean `p_true` | Mean(P−`p_true`) |
|---|---|---:|---:|---:|---:|
| gOFF | PG | 0,553375 | 0,754167 | 0,768473 | −0,215098 |
| gOFF | PY | 0,470044 | 0,300833 | 0,308038 | +0,162006 |
| gOFF | PYH | 0,485820 | 0,394167 | 0,397342 | +0,088478 |
| gON | PG | 0,552132 | 0,749167 | 0,764689 | −0,212556 |
| gON | PY | 0,458534 | 0,307500 | 0,307727 | +0,150806 |
| gON | PYH | 0,472995 | 0,387500 | 0,398264 | +0,074731 |

Chênh của các trung bình trên cho biết hướng lệch toàn nhóm. Chứng cứ về bù trừ trong phép tính ECE cần nhìn vào từng bin. Với gOFF, λ=0,55, bin [7/15,8/15) có kết quả sau.

| Nhóm | Số dòng trong bin | Mean P | Mean Y | Mean(P−Y) |
|---|---:|---:|---:|---:|
| PG | 341 | 0,501296 | 0,736070 | −0,234774 |
| PY | 430 | 0,496678 | 0,309302 | +0,187376 |
| PYH | 436 | 0,498715 | 0,410550 | +0,088164 |
| Gộp | 1.207 | 0,498719 | 0,466446 | +0,032273 |

Trong cùng khoảng forecast, các gap có dấu trái nhau trước khi lấy trị tuyệt đối ở mức gộp. Một ECE gộp nhỏ vì thế có thể che lệch lớn ở từng persona. Quan sát này cho thấy cần đọc reliability theo nhóm cùng với bảng tổng hợp. Nó chưa chứng minh nguồn gốc nhân quả của sai lệch hay hiệu quả của một biện pháp sửa calibration. [Các bản ghi `persona_arm` và `arm`, gOFF/λ=0,55, `bins[7]`](../runs/rq1-response-reliability-diagnostic-20261109-01/reliability.json).

## 5. Đóng góp mới và giới hạn đối với RQ1

Đóng góp mới của lần phân tích này là bằng chứng định lượng về sai lệch response trái dấu theo persona và sự đảo thứ hạng descriptive khi gộp, kèm các bins đầy đủ để kiểm tra cơ chế số học. Các thống kê log loss/Brier toàn cục và các khoảng probability cục bộ đã có trước chưa cung cấp phép phân rã này. Đối chiếu `p_true` còn cho thấy phần lớn hướng lệch toàn nhóm tồn tại so với xác suất đáp án của simulator, thay vì chỉ xuất hiện trong tần suất Y hữu hạn.

Phạm vi suy luận vẫn là simulator CPU09, các nguồn, lịch thực hành và mười seed đã dùng. 14.400 events có phụ thuộc trong trajectory. 136 group views và 2.040 bins biểu diễn lại cùng dữ liệu ở ba mức, với 43.200 lượt sử dụng dòng trong các tổng hợp. Chúng không phải 43.200 quan sát mới. Báo cáo giữ toàn bộ seed, persona, arms và bins rỗng, không có CI, p-value hoặc khẳng định tổng quát hóa.

Native mastery M của GAM-KT còn phụ thuộc trạng thái theta_est và pi. Pi không có nghĩa xác suất trả lời đúng. Criterion reference-mixture tại τ dùng một quần thể query khác với các bài thực sự được phục vụ. Vì vậy, response reliability ở đây chưa xác định được M đúng hay sai, chưa hiệu chuẩn concept mastery và chưa chấm được độ đúng của quyết định tại τ. Hai reference items chưa được phục vụ trong các fixed-stream snapshots vẫn thiếu observed/oracle outcomes tương ứng. Cần thiết kế truth và population riêng để giải quyết khoảng trống đó. [Đánh giá khả thi và ngữ nghĩa threshold](../runs/rq1-response-reliability-diagnostic-20261109-01/RQ1_CACHED_CALIBRATION_FEASIBILITY01.md).

## 6. Kiểm chứng và truy vết

Lượt kiểm công thức dùng 7 methods và 31 subtests trên dữ liệu dựng tay, đạt 0 failure/error/skip. Nó kiểm exact bin edges, endpoints, bin rỗng, noise, tính không cộng tuyến của trị tuyệt đối, dữ liệu sai và grouping. Lượt actual đọc cache đạt đủ 120 world groups, 12 persona-arm groups và 4 pooled arms. Outer kiểm riêng số đếm, signed identity, từng ECE và việc gộp các world bins tái tạo đúng 12+4 nhóm. Nguồn và 21 inputs gốc giữ SHA trước/sau, cleanup đạt và Job còn 0 process. Không có model, simulation hoặc temperature fit trong hai lượt này.

Native outer lưu 0,8742171 giây, helper lưu 0,6735654 giây và parser lưu 0,3482247 giây. Đây là thời gian lồng nhau. Quan sát terminal riêng của Root là 1,4715582 giây. Family peak RSS đo được 97.083.392 bytes, available RAM thấp nhất 4.976.648.192 bytes, dưới giới hạn RSS 1 GiB và trên floor 2 GiB. Những con số vận hành này chỉ ghi lại phạm vi lượt đọc cache.

Recipe tổng hợp 16 nhóm được lưu sau phép tổng hợp ban đầu và đã chạy đối chiếu toàn bộ JSON có sẵn với bins được nghiệm thu. Không gán ngược thời điểm lưu recipe cho thao tác đầu. Report và archiver mới chỉ được chuẩn bị trong lượt viết này, chưa chạy đóng bundle. [Recipe kiểm lại bảng](../runs/rq1-response-reliability-diagnostic-20261109-01/verify_response_reliability_synthesis01.py), [receipt kiểm bảng](../runs/rq1-response-reliability-diagnostic-20261109-01/synthesis_verification.json).

| Bằng chứng | SHA-256 |
|---|---|
| Gzip CPU09 gốc, chỉ tham chiếu | `2a136fbf627cfa59170deec54c10ae562c2f8214eb00970ce41b96c43d065dcc` |
| Source phân tích response | `baf5e6a73e3fca66d04f9d8199e9c4174565f2a19d82c9ce2e8eeaef955545a0` |
| Pure receipt | `087c94b14e67939e66792e07217bdf0ebdda4dfab0a74e15dfecdad52bff5edd` |
| Native outer receipt | `e68aae35eca99c111107d2748a62baeb1a78bf5e4b5952bb777befe980ae6ca8` |
| Bins reliability | `a139398062bcb424ad759d5ee07c81521d322c49ab119b8deedc3c3d98697d26` |
| Tổng hợp 16 nhóm | `9cbfef811bc496f7c29c093ad80fcd1d14947fe2d60450e88835591f48cfe03a` |
| Recipe kiểm tổng hợp | `44137a62e1762568ad3c043bedec79549e753c4ce4a7932e4a397ea9286bea8c` |

Trong `synthesis.json`, các số ở bảng chính nằm tại `groups[*].ordinary_ece15` và `oracle_response_ece15`, với khóa `level/profile/graph_on/mechanism_on`. Bảng bias lấy `mean_prediction`, `mean_observed_correct`, `mean_true_response_probability` và `mean_model_bias`. Bản bins gốc giữ toàn bộ chi tiết ở `groups[*].bins[*]`. Các receipt và raw logs được chọn cho [bundle của phân tích](../runs/rq1-response-reliability-diagnostic-20261109-01/README.md). Gzip gốc và dependency runtime giữ nguyên vị trí, chỉ ghi reference SHA trong inventory.
