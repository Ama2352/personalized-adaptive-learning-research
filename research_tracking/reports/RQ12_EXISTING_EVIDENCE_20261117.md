# RQ1–RQ2 — làm rõ cơ chế từ bằng chứng đã có

Ngày 17/11/2026. Lượt này đọc lại các phép chạy đã nghiệm thu, giữ nguyên simulator và model. Nguồn gồm pilot GAM/graph package của RQ1 và fresh120 của RQ2. Các kết quả mới là kiểm chéo và diễn giải hậu nghiệm, chưa bổ sung người học, seed block hoặc phép chạy độc lập.

## 1. Vì sao cần đọc lại các kết quả này

Paper 1 đặt vấn đề tác động của đồ thị có thể bị chính sách chọn bài che khuất. Paper 2 cho thấy thay đổi dự báo nhỏ chưa dẫn đến lợi ích vòng kín rõ ràng. RQ1 cần xác định tác động dừng ở đâu, còn RQ2 cần tách đóng góp của đồ thị khỏi điều kiện người học và giả định môi trường.

Các số 964 thay đổi xác suất, 90 thay đổi mastery, 60 thay đổi ready và 22 thay đổi gợi ý đã được lưu. Chúng cùng dùng 1.080 cặp trạng thái pilot nhưng đo các biến khác nhau. Lần này đối chiếu từng dòng CSV với bảng joint PMRA để hiểu chính xác những thay đổi nào cùng xuất hiện. Nguồn theo [pilot transitions](../runs/cpu-rq1-transitions-20261108-01/README.md).

Đối với RQ2, mười block fresh đã so expert với một learned graph cố định, đồng thời bật/tắt mức phạt thiếu tiên quyết. Lần này đối chiếu trực tiếp chuỗi câu hỏi, đáp án và xác suất KT giữa hai mức phạt trong cùng block/ability/graph. Mục đích là phân biệt thay đổi trạng thái kiến thức ẩn của simulator với thay đổi hành vi quan sát được của hệ thống. Nguồn theo [fresh120](rq2_fresh_graph_source_replication_20261110.md).

## 2. RQ1 — tập đủ điều kiện đổi thường vẫn giữ cùng gợi ý

| Tập chủ đề đủ điều kiện | Gợi ý đổi | Gợi ý giữ | Tổng cặp trạng thái |
|---|---:|---:|---:|
| Có thay đổi | 5 | 55 | 60 |
| Giữ nguyên | 17 | 1.003 | 1.020 |
| Tổng | 22 | 1.058 | 1.080 |

Trong 60 cặp có ready set đổi, 55 cặp vẫn giữ gợi ý, tương ứng 91,7%. Đồng thời, 17 trong 22 cặp đổi gợi ý lại giữ nguyên ready set và nhãn mastery. Bộ chọn bài còn phụ thuộc điểm số và các quy tắc khác ngoài tập đủ điều kiện. Các số đếm hỗ trợ câu hỏi về những đường ảnh hưởng đó, nhưng chưa tách riêng đóng góp nhân quả của từng đường.

Ở cùng pilot, trong 964 cặp đổi xác suất của câu đang xét, 944 cặp giữ gợi ý, tương ứng 97,9%. Hai cặp đổi gợi ý dù xác suất câu đang xét giữ nguyên. Do đó, việc đọc bốn số 964/90/60/22 cần giữ thông tin đồng biến và đúng phase của served probability. Trong Paper2 lịch sử, bộ chọn bài hoạt động trước bước dự báo served item, nên xác suất ấy chưa là một biến trung gian đi trước selection theo thời gian.

Các số này giải thích rõ hơn vì sao khác biệt dự báo và khác biệt quyết định có thể tách rời trong pilot. Gợi ý được đo là concept preview khi replay cùng lịch sử. Kết luận về lợi ích học tập vẫn cần reference/mastery, fitted calibration và outcome vòng kín độc lập. Pilot có 3 seed families ×3 hồ sơ, tức9cụm seed–hồ sơ. Phụ thuộc giữa các hồ sơ cùng family cần được giữ khi suy luận, và các tỷ lệ ở đây chỉ là mô tả.

[CSV điều kiện đã kiểm](../runs/rq12-existing-evidence-20261117-01/rq1_conditionals.csv) giữ mọi mẫu số. [SVG bảng chéo](../runs/rq12-existing-evidence-20261117-01/rq1-ready-preview-v01.svg) có bản PNG, nguồn dữ liệu và script dựng lại trong cùng bundle.

## 3. RQ2 — bật cơ chế môi trường có thể đổi kiến thức ẩn khi hệ thống quan sát cùng lịch sử

Fresh120 có 10 block, ba mức khởi tạo, hai nguồn đồ thị estimator và hai mức phạt lambda0/0,55. World và controller cùng giữ expert graph. Có 60 cặp bật/tắt phạt sau khi ghép đúng block, mức khởi tạo và nguồn đồ thị, mỗi cặp 120 bước.

| Mức khởi tạo | Cặp có nguyên chuỗi câu hỏi/đáp án/xác suất KT giống nhau | Chênh lệch gain ẩn khi bật phạt so với tắt, Elo | Cặp gain ẩn giảm / giữ nguyên |
|---|---:|---|---:|
| 1000 | 18/20 | −1,086595 đến −0,896530 | 20 / 0 |
| 1150 | 20/20 | −0,257317 đến −0,018351 | 20 / 0 |
| 1300 | 20/20 | 0 đến 0 | 0 / 20 |

Ở mức 1150, cả 20 cặp giữ cùng chuỗi câu hỏi, đáp án và xác suất KT trong 120 bước, trong khi gain kiến thức ẩn giảm ở cả 20 cặp khi bật phạt. Đây là một kết quả cơ chế cụ thể. Mô hình nhận lịch sử quan sát giống nhau, nhưng phương trình học của môi trường làm trạng thái thật sau cùng khác nhau.

Trên toàn 60 cặp, có 58 cặp nguyên chuỗi quan sát giống nhau. Trong 7.200 vị trí so cặp chỉ có 2 câu hỏi, 2 nhãn đúng/sai và 3 xác suất KT đổi. Các khác biệt tập trung ở hai block21010/21011, ability1000, expert estimator. Mức1300 là đối chứng bất hoạt, cả quan sát lẫn gain ẩn đều giữ nguyên khi đổi lambda trong các ca đã chạy.

Source đã được đối chiếu SHA với phép chạy gốc. Núm lambda thay hệ số `1 − lambda × prerequisite_deficit` trong learning gain của world. Worker chọn bài, dự báo, lấy đáp án từ world rồi cập nhật policy. Các giá trị query/correct/probability đã lưu cho phép kiểm trực tiếp lịch sử quan sát. Chúng chưa bao phủ mọi trạng thái nội bộ của estimator và controller. Nguồn là [hàm can thiệp](../../src/knowledge_tracing/gam_kt/simulator_mechanisms.py), [kiểm chuỗi trực tiếp](../runs/rq12-existing-evidence-20261117-01/LAMBDA_OBSERVABLES.json) và [kiểm phụ canonical](../runs/rq12-existing-evidence-20261117-01/SECONDARY_CHECK.json).

### Cách đọc contrast đồ thị sau kiểm này

Q là gain của estimator expert trừ estimator learned tại cùng lambda. K là Q khi bật phạt trừ Q khi tắt phạt, tính trong từng block.

| Mức khởi tạo | Q trung bình khi tắt phạt | Q trung bình khi bật phạt | K trung bình | K dương / âm / zero |
|---|---:|---:|---:|---:|
| 1000 | +0,078604 | +0,083100 | +0,004496 | 6 / 4 / 0 |
| 1150 | +0,005212 | +0,029742 | +0,024530 | 8 / 2 / 0 |
| 1300 | +0,116623 | +0,116623 | 0 | 0 / 0 / 10 |

K1150 dương ở8/10block có nghĩa chênh lệch expert–learned thay đổi theo núm world trong các realization đó. K dương chưa chứng minh KT hoặc bộ chọn bài đã điều chỉnh tốt hơn khi bật phạt. Kiểm chuỗi mới làm rõ giới hạn này. Các khoảng thăm dò đã có tiếp tục theo [bootstrap10block](rq2_fresh_block_uncertainty_20261110.md), bao gồm khoảng của chênh lệch K1150−K1000 chứa0. Lượt này giữ nguyên family, không tạo thêm kiểm định.

Q1300 khác0 cả10block dù K1300 bằng0. Expert/learned vẫn có thể tạo đường học và mức thử thách khác nhau trong cùng world. Kết quả cần được giới hạn vào một graph học được, estimator GAM, horizon120 và world đã khai báo. Chưa suy chất lượng cạnh thật hoặc hiệu quả dạy học trên Junyi/người học thật.

## 4. Phần nào được khép trong lượt này

Đã khép việc kiểm chéo số đếm RQ1 và diễn giải chính xác bảng đồng biến, giữ một figure đọc được. Đã kiểm lại 120 outcome keys, 60Q, 30K, latent/uniform identities ghép cặp và 60 cặp lịch sử quan sát giữa hai mức lambda. Tổng hợp numeric dùng Decimal precision60 để kiểm số học trung bình và subtraction binary64, sai lệch lớn nhất 2,455×10⁻¹⁵ Elo, nhỏ hơn tolerance1×10⁻¹² đã ghi trước phép kiểm.

Các output mới chỉ bổ sung phân tích trên bằng chứng đã có. Chưa khép RQ1 hoặc RQ2. Những việc còn nằm trên đường chính gồm hiệu chỉnh và đánh giá độc lập trên fitted checkpoint, reference/mastery quanh ngưỡng, controller/action/outcome cùng trace, đối chứng Junyi kiểm soát thứ tự và khảo sát graph/history/support theo protocol. Giữ trạng thái theo [ma trận hoàn tất hiện hành](RQ12_CLOSURE_MATRIX_20261112.md) và [rà soát16/11](RQ12_COMPLETION_REVIEW_20261116.md).

## 5. Phạm vi tài nguyên và lưu bằng chứng

Phân tích dùng `.venv`, đọc CSV/JSON tổng hợp đã lưu và khoảng4,22MB trace/ledger simulator. Không nạp checkpoint, chạy simulator, fit, bootstrap mới, dùng GPU/cloud, đọc Junyi gốc hoặc Holdout. Tất cả nguồn đã hash trước/sau, giữ nguyên bytes. Raw traces của parent61complete cộng child59complete được ghép theo hồ sơ recovery, loại30dòng partialF062 ở parent để tránh đếm lặp.

[Bundle17/11](../runs/rq12-existing-evidence-20261117-01/README.md) giữ đặc tả hậu nghiệm, nguồn/script, CSV, output số học, kiểm phụ, SVG/PNG và manifest. RQ1 dùng snapshot pilot để giải thích sự khác nhau giữa dự báo/quyết định. RQ2 dùng paired block10đơn vị để mô tả cơ chế môi trường. Các quan sát thời gian không được tính như các mẫu độc lập cho suy luận thống kê.
