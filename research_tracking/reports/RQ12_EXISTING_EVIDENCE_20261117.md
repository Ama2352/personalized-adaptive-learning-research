# RQ1–RQ2 — từ kết quả hai paper đến các nguyên nhân và điều kiện đã xác định

Ngày 17/11/2026. Báo cáo tổng hợp bằng chứng đã nghiệm thu và kiểm chéo hậu nghiệm, giữ nguyên simulator, model và kết quả lịch sử. Phần số học của lượt17/11 dùng pilot GAM/graph package, fresh120 đã lưu và bảng thống kê frozen Paper2. Bản tổng hợp nối chúng với các chứng minh Paper1, cơ chế retention và kiểm exposure Junyi. Không bổ sung người học, seed block hoặc phép chạy độc lập trong lượt tổng hợp này.

## Kết luận tiến độ hiện tại

RQ1 đã xác định được các cơ chế cụ thể khiến một thay đổi dự báo không dẫn đến thay đổi gợi ý, đồng thời chỉ ra một số kết quả đường học có thể suy ra từ controller. RQ2 đã có đối chứng mô phỏng tách được ảnh hưởng của núm phạt tiên quyết khỏi lịch sử mà KT quan sát, cùng phép đo cho thấy một graph control có thể rất ít làm thay đổi thông tin thực sự xuất hiện trong log Junyi. Các phát hiện này đủ nguồn để trình bày thành phần chẩn đoán của luận văn. Kết quả về chất lượng dự báo độc lập, hiệu chỉnh quanh ngưỡng thành thạo và lợi ích học tập của model fitted vẫn cần được nối thành thực nghiệm chính.

| Câu hỏi | Đã làm được gì | Phần còn mở |
| --- | --- | --- |
| RQ1 — vì sao graph chưa cải thiện mastery | Chứng minh zero re-entry có điều kiện, kiểm tính bất biến của chuyển trạng thái concept-local, đo đường dự báo/quyết định và vai trò ngoại lệ controller | So prediction/calibration/mastery/action/outcome trên checkpoint fitted với cùng target và controller |
| RQ2 — khi nào graph hữu ích hoặc bất lợi | Thực nghiệm paired ability×graph×phạt, đối chứng bất hoạt, phân biệt retention readouts, đo exposure và hạn chế của graph controls Junyi | Noise/history/support theo protocol chính, predictive order-controls và bất định trên mẫu xác nhận độc lập |

Trạng thái được đối chiếu theo các tiêu chí C01–C07 và T1–T3 trong ma trận hoàn tất. Hai RQ còn các đường thực nghiệm cần khép, nên báo cáo không gán tỷ lệ phần trăm hoàn thành. [Ma trận nghiệm thu](RQ12_CLOSURE_MATRIX_20261112.md)

## 1. Vì sao cần đọc lại các kết quả này

### Bước đầu — hai paper đã để lại câu hỏi gì

Paper1 nghiên cứu thứ tự luyện trong mô phỏng toán Grade10 có28khái niệm. Bài báo so đồ thị rỗng, đồ thị nội chương25cạnh và đồ thị mở rộng31cạnh, với50seed cho mỗi hồ sơ trong3hồ sơ người học, đồng thời thay chính sách chọn bài. Ở hồ sơ thấp và yếu hàm số, hai điều kiện graph giảm số lần đổi chương trung bình11→2 và re-entry9→0. Tuy vậy, đồ thị mở rộng chưa có lợi thế nhất quán so với đồ thị nội chương, còn ablation cho thấy controller giữ chương đóng vai trò quan trọng. Câu hỏi còn lại là lợi ích nào đến từ cạnh tiên quyết, lợi ích nào đến từ cách chọn bài và chỉ tiêu nào đã được quy tắc bảo đảm. PDF Paper1 là nguồn lịch sử có thẩm quyền của phần này. [Paper1 PDF](../../paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf), [bản trích để tìm nội dung](../../docs/thesis_recovery/evidence/user_documents_20261108_paper1.txt)

Paper2 chuyển sang knowledge tracing và so cùng luồng tương tác trước khi xét vòng kín. Gói graph/context/adaptation cải thiện Log Loss ở nhóm Low và Function-weak, nhưng kết quả vòng kín ở hai nhóm này chưa có khác biệt sau hiệu chỉnh Holm. Development Junyi chọn cấu hình all-pathways-off. Bài báo cũng giới hạn rằng contrast của cả gói chưa quy được cải thiện cho riêng các cạnh. Từ đó, luận văn cần theo dõi sự chuyển tiếp từ dự báo đến quyết định, rồi đến kết quả học trong môi trường có cơ chế được kiểm soát. [Paper2, phần kết quả và giới hạn](../../docs/thesis_recovery/evidence/user_documents_20261108_paper2.txt)

### Bước tiếp — RQ1 và RQ2 phát triển từ các kết quả đó

RQ1 hỏi nguyên nhân. Đầu tiên cần biết dự báo có cải thiện đủ hay không, tiếp đến xác suất quanh ngưỡng thành thạo có đáng tin cậy hay không, rồi kiểm bộ chọn bài có thực sự đổi hoạt động. RQ2 hỏi phạm vi hiệu lực. Cần giữ được các yếu tố khác khi thay chất lượng graph, lượng lịch sử và đặc điểm người học, đồng thời kiểm ba bẫy GVHD đã chỉ ra. [Đề cương, ba RQ](../../docs/thesis_recovery/evidence/user_documents_20261108_proposal.txt), [phản hồi GVHD đã lưu](../runs/akt-protocol-audit-20261112-01/advisor-context.md)

Các chỉ tiêu dự báo LL/Brier/AUC/ECE tiếp tục phục vụ so sánh KT như baseline. Số lần đổi nhãn mastery, tập đủ điều kiện và gợi ý giúp giải thích vì sao cải thiện dự báo có hoặc chưa có tác dụng lên hệ thống. Các số đếm này được dùng để kiểm cơ chế truyền ảnh hưởng. Bảng dự báo và bảng quyết định cần được đọc cùng nhau khi trả lời RQ1.

Các số 964 thay đổi xác suất, 90 thay đổi mastery, 60 thay đổi ready và 22 thay đổi gợi ý đã được lưu. Chúng cùng dùng 1.080 cặp trạng thái pilot nhưng đo các biến khác nhau. Lần này đối chiếu từng dòng CSV với bảng joint PMRA để hiểu chính xác những thay đổi nào cùng xuất hiện. Nguồn theo [pilot transitions](../runs/cpu-rq1-transitions-20261108-01/README.md).

Đối với RQ2, mười block fresh đã so expert với một learned graph cố định, đồng thời bật/tắt mức phạt thiếu tiên quyết. Lần này đối chiếu trực tiếp chuỗi câu hỏi, đáp án và xác suất KT giữa hai mức phạt trong cùng block/ability/graph. Mục đích là phân biệt thay đổi trạng thái kiến thức ẩn của simulator với thay đổi hành vi quan sát được của hệ thống. Nguồn theo [fresh120](rq2_fresh_graph_source_replication_20261110.md).

### Đã tính lại phần nào của kết quả thống kê Paper2

Để xác nhận nền số liệu trước khi phát triển chẩn đoán, nhóm đã tính lại model means, mean paired delta và Holm từ outcome frozen của Paper2. Mỗi phase có600dòng model×profile×seed, mỗi hồ sơ có50seed ghép cặp. Toàn45hypotheses fixed-replay và72hypotheses closed-loop khớp bảng lịch sử. Lượt đầu còn kế thừa raw p-value/CI, sau đó followup02 chạy nguyên functions nguồn để tính lại Wilcoxon, rank-biserial,3.000paired-bootstrap draws mỗi hypothesis và Holm. Cả10trường số của117hypotheses khớp chính xác giá trị float đã lưu, không đổi cờ quyết định nào. Không chạy lại simulator hoặc model. [Nghiệm thu bảng mean/Holm ban đầu](../runs/paper2-statistical-reproduction-20261117-01/ACCEPTANCE.json), [kết quả tái tính p-value và CI](../runs/paper2-statistical-reproduction-20261117-02/attempt01/RESULT.json)

| Hồ sơ Paper2 | Δ Log Loss cùng luồng, graph package−GAM | Qua Holm family45 | Δ learning gain mỗi bước | Δ retained theta gain14ngày |
| --- | ---: | --- | ---: | ---: |
| Năng lực cao | −0,000255888 | Chưa | +0,007455 | −0,006615 |
| Năng lực thấp | −0,003194533 | Có | +0,026815 | +0,037761 |
| Yếu hàm số | −0,001692390 | Có | −0,015907 | −0,009136 |

Hai outcome gain ở cả ba hồ sơ đều chưa qua Holm trong family72, pHolm bằng1 cho sáu contrast này. Phần tái lập cho phép đặt câu hỏi RQ1 trên số liệu đã đối chiếu rõ, dự báo tốt hơn ở Low/Function-weak vẫn chưa dẫn đến bằng chứng cải thiện outcome chính theo family đã chốt. Độ bất định và các đường tác động còn cần được phân tích tiếp. Contrast này tác động cả gói context/adaptation, nên câu hỏi về đóng góp riêng của cạnh vẫn mở. [Bảng39contrast chính](../runs/paper2-statistical-reproduction-20261117-01/PRIMARY_PACKAGE_CONTRAST.csv), [SVG độc lập và dữ liệu dựng](../runs/paper2-statistical-reproduction-20261117-01/paper2-prediction-outcome-v01.svg)

Đây là một phần hoàn thiện Sprint1 về tái lập và thực hành thống kê của Sprint5 theo đề cương. Gói đầu có13kiểm thử hồi quy tổng hợp đạt, followup có3kiểm CLI/AST đạt. Lượt tính lại đầy đủ dùng5,57giây CPU và peak140,56MiB trong trần180giây/256MiB. Phiên bản thư viện historical chưa được pin đủ, còn runtime local hiện hành tái hiện đúng toàn bộ số thống kê từ outcomes đã lưu. Chưa tái chạy trajectory để xác nhận việc sinh outcomes. Kết quả không tăng số sample nghiên cứu hoặc xác nhận hoàn tất RQ. [Quy trình p/CI, versions và giới hạn](../runs/paper2-statistical-reproduction-20261117-02/README.md), [receipt tài nguyên](../runs/paper2-statistical-reproduction-20261117-02/attempt01/RESOURCE_RECEIPT.json)

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

## 5. Ba bẫy GVHD — phát hiện nào đã có bằng chứng

### Bẫy1 — outcome có thể xuất phát từ thiết kế mô phỏng

Sau khi lấy PDF Paper1 làm nền, nhóm đã chứng minh rằng nếu graph là DAG nội chương, mastery đã đạt không bị mất và controller tiếp tục ở chương hiện tại khi còn bài đủ điều kiện, mỗi chương xuất hiện tối đa một khối liên tiếp. Re-entry bằng0 khi các giả thiết ấy giữ. Bốn tình huống dựng tay đã kiểm đúng cơ chế và cho phản ví dụ A→B→A khi có cạnh liên chương. Điều này giải thích vì sao zero re-entry tự nó chưa xác nhận chất lượng dự báo hoặc lợi ích học tập. [Chứng minh và phản ví dụ](paper1_reentry_mechanism_20261109.md), [receipt bốn tình huống](../runs/paper1-reentry-mechanism-20261109-01/result.json)

Phân tích tiếp theo xác định rằng với chuyển trạng thái chỉ phụ thuộc concept đang luyện, cùng trạng thái đầu và cùng random tape theo concept, khi hai nhánh đều hoàn tất thì đổi thứ tự có thể giữ nguyên trạng thái cuối. Đây là mệnh đề có điều kiện về cơ chế và cách ghép randomness. Finite horizon hoặc thay tương tác liên concept có thể thay kết luận. Các fixture mới phục vụ chẩn đoán cấu trúc, chưa tái hiện các random draws lịch sử của PDF. [Bất biến concept-local và sáu fixture](paper1_concept_local_invariance_20261109.md)

Ở Paper2, dưới cùng luật quên đồng nhất0,06/ngày và không luyện sau kết thúc, retained net mean-theta gain sau14ngày bằng khoảng43,17% gain khi kết thúc. Chỉ tiêu này giữ thứ tự xếp hạng final gain. Tuy nhiên, phép đo mastery phi tuyến có thể đổi thứ tự. Fixture đã lưu cho soft-mastery gain đổi B>A tại kết thúc thành A>B sau14ngày. Vì vậy, kết luận dư thừa cần ghi đúng readout. Fixture là trạng thái dựng để kiểm phép đo, chưa chứng minh policy nào tạo được trạng thái đó. [Công thức và số liệu retention](rq2_retention_metric_separation_20261108.md)

### Bẫy2 — chênh lệch graph có thể đi qua cơ chế năng lực chung

Nhóm đã bổ sung núm bật/tắt phạt thiếu tiên quyết, giữ world/controller graph cố định và ghép cùng block trạng thái/ngẫu nhiên. Contrast K ở mục3 lấy chênh lệch expert–learned khi bật phạt trừ chênh lệch ấy khi tắt phạt. Đây là can thiệp điều khiển trực tiếp trong simulator. Phạm vi diễn giải phụ thuộc việc núm chỉ thay pathway đã khai báo, cùng cách ghép trạng thái và randomness giữa các nhánh.

Kết quả fresh120 và kiểm chuỗi hậu nghiệm chỉ ra giới hạn cụ thể của câu “graph giúp”. Ở mức1150, cả20cặp giữ cùng lịch sử quan sát nhưng gain ẩn giảm khi bật phạt. K dương8/10block phản ánh tương tác trong phương trình môi trường ở các lượt ấy. K1300 bằng0 ở10block cung cấp đối chứng bất hoạt. Khoảng bootstrap thăm dò của chênh lệch K1150−K1000 chứa0, nên khác biệt theo năng lực còn bất định. Đơn vị suy luận là10paired blocks, mỗi block chứa toàn bộ ability×graph×lambda. [Bất định10block](rq2_fresh_block_uncertainty_20261110.md), [kiểm chuỗi trực tiếp](../runs/rq12-existing-evidence-20261117-01/LAMBDA_OBSERVABLES.json)

### Bẫy3 — thay graph trên Junyi có thể vẫn giữ gần như nguyên thông tin người học đã thấy

Vì log Junyi chịu ảnh hưởng của bản đồ kiến thức, một cạnh có thể trùng với thứ tự luyện sẵn có. Nhóm đã kiểm khả năng đối chứng trước khi so predictive metrics. Trong pilot256learner/12.575event, common population có239learner đủ điều kiện và1.361cơ hội cố định. Ba graph controls chỉ làm đổi exposure score ở1,7và1learner tương ứng. Phần common-coobserved chỉ giữ khoảng41% cơ hội. Đây là bằng chứng rằng perturbation topology có thể rất yếu khi đi qua lịch sử cụ thể. [Aggregate common population](../runs/cpu-junyi-common-20261107-01/common_population.json)

Sau đó, phép đọc label-free toàn TRAIN80 đúng cửa sổ AKT đã bao phủ126.774learner,13.347.331target và232.662window. Trong976cạnh catalog,876cạnh có ít nhất một parent xuất hiện trước childtarget. Có58cạnh thiếu child trong vocabulary TRAIN,28cạnh thiếu parent và14cạnh có đủ hai endpoint nhưng chưa gặp parent trước child trong native prefix. Tổng100cạnh thiếu dạng exposure đang xét đã được tách nguyên nhân. [Kết quả fullTRAIN80 và kiểm độc lập](../runs/rq2-junyi-window-exposure-preflight-20261112-01/FINDINGS.md), [CSV976cạnh](../runs/rq2-junyi-window-exposure-preflight-20261112-01/full01/edge-exposure.csv), [SVG đã lưu](../runs/rq2-junyi-window-exposure-preflight-20261112-01/junyi-native-window-edge-coverage.svg)

Hai phép đo này chưa có bảng prediction treatment/control đi kèm để xác nhận false positive dự báo. Các controls pilot dùng outer0, còn AKT hiện hành dùng outer4, nên cần dựng đối chứng đúng TRAIN80 hiện hành. So graph-free, catalog, matched-null và graph học từ thứ tự TRAIN trên cùng target, báo changed-edge exposure và coverage, là phần còn thiếu để khép bẫy3. Những kết quả Junyi sẽ được diễn giải theo khả năng dự báo trên logged sequence.

## 6. Từ chẩn đoán đến thực nghiệm chính còn thiếu

Controller Paper2 còn có cơ chế làm đường graph khó nhận diện. Trong2.740served actions có tiên quyết,2.041cần ngoại lệ visits≥6. Same-state strict-frontier làm đổi2.557/3.240frontiers và loại18.520/30.572memberships. Strict frontier còn concept ở3.240snapshot, nhưng số này được đo trước anti-repeat/coverage/ranking. Shadow action và learning outcome chưa được suy ra từ thay eligibility. [Nghiệm thu strict readiness](../runs/rq1-strict-readiness-shadow-20261112-01/README.md)

| Thứ tự nghiên cứu tiếp | Mục đích cần trả lời | Bằng chứng nghiệm thu cần có |
| --- | --- | --- |
| 1. Nối prediction độc lập và calibrator fitted | Dự báo có tốt hơn, và xác suất quanh ngưỡng có đáng tin hơn không | Cùng exact target, coverage/OOV, LL/Brier/AUC/ECE raw và calibrated, reliability quanh ngưỡng, paired learner uncertainty |
| 2. Đo reference/mastery/readiness/action trên cùng trace | Ảnh hưởng của graph dừng ở prediction, threshold hay controller | Reference/query probabilities đúng phase, nhãn mastery, tập ready, candidate và hành động được ghi cùng state trước observe |
| 3. Một core batch Grade10 dùng chung RQ1–RQ3 | Những thay đổi quyết định có dẫn đến học tốt hơn ở điều kiện nào | Checkpoint Grade10 fitted/calibrated, fresh paired blocks, true-state evaluator, gain/censoring/path metrics và family thống kê đã freeze |
| 4. Tái dùng batch ấy cho graph noise/history/support | Xác định điều kiện lợi, trung tính, bất lợi và giới hạn support | Perturbation/type/history đã chốt, strata TRAIN-only, đủ mẫu số và khoảng bất định, confidence/gate ablation |
| 5. Predictive Junyi order-controls | Lợi thế graph còn tồn tại sau đối chứng thứ tự và exposure không | Controls đúng TRAIN80 outer4, sequence/targets chung, âm tính kiểm soát được và inference unit theo learner |

Junyi có thể cung cấp bằng chứng dự báo và hiệu chỉnh đáp án. Grade10 có28khái niệm,84item và trạng thái thật đã biết, phục vụ kiểm mastery và vòng kín. Hai miền dùng vocabulary/corpus riêng. Refit hoặc calibration Junyi không tự tạo ra kết quả học tập Grade10. Các lifecycle và baseline còn thiếu được giữ trong ma trận phạm vi đề cương. [Vai trò training đối với ba RQ](TRAINING_RQ_SCOPE_REVIEW_20261116.md), [Recipe26](../../docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md)

## 7. Phân loại thành quả để dùng trong luận văn

| Loại công việc | Thành quả đã có | Cách trình bày đúng phạm vi |
| --- | --- | --- |
| Kế thừa và tái hiện | Kế thừa kết quả lịch sử theo PDF Paper1/Paper2, dựng source prospective theo PDF và kiểm primitive/parity ở phạm vi đã ghi | Ghi rõ điều gì lấy từ paper và điều gì chạy mới, giữ thiết kế/đơn vị gốc khi trích số lịch sử |
| Chẩn đoán | Proof re-entry, concept-local và retention, PMRA pilot, strict-readiness, paired knob/observable checks và Junyi exposure | Trình bày giả thiết, mẫu số, version, đơn vị ghép cặp và phản ví dụ. Các proof không thay thế outcome của model fitted |
| Nghiên cứu mới đã thăm dò | Factorial fresh120 và các phân tích điều kiện từ artifact đã lưu | Giữ nhãn exploratory/pilot và một learned graph cố định, không nâng10block hậu nghiệm thành mẫu xác nhận độc lập |
| Nghiên cứu chính còn mở | Fitted prediction/mastery/outcome, graph-confidence/gate và order-controls đã khớp protocol | Đóng bằng thực nghiệm và uncertainty theo các tiêu chí ở mục6, kết quả âm hoặc bất định vẫn cần được báo đầy đủ |

Báo cáo này khép phần tổng hợp các phát hiện đã đủ nguồn, đồng thời định vị rõ phần còn đòi thí nghiệm. Không có kết luận mới rằng RQ1 hoặc RQ2 đã hoàn tất toàn phạm vi.

## 8. Phạm vi tài nguyên và lưu bằng chứng

Phân tích dùng `.venv`, đọc CSV/JSON tổng hợp đã lưu và khoảng4,22MB trace/ledger simulator. Không nạp checkpoint, chạy simulator, fit, bootstrap mới, dùng GPU/cloud, đọc Junyi gốc hoặc Holdout. Tất cả nguồn đã hash trước/sau, giữ nguyên bytes. Raw traces của parent61complete cộng child59complete được ghép theo hồ sơ recovery, loại30dòng partialF062 ở parent để tránh đếm lặp.

[Bundle17/11](../runs/rq12-existing-evidence-20261117-01/README.md) giữ đặc tả hậu nghiệm, nguồn/script, CSV, output số học, kiểm phụ, SVG/PNG và manifest. RQ1 dùng snapshot pilot để giải thích sự khác nhau giữa dự báo/quyết định. RQ2 dùng paired block10đơn vị để mô tả cơ chế môi trường. Các quan sát thời gian không được tính như các mẫu độc lập cho suy luận thống kê.
