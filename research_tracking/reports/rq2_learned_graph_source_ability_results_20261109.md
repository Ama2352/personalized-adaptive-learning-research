# RQ2 — đổi nguồn đồ thị trong cùng cơ chế ước lượng và điều kiện người học

Ngày09/11/2026. Kết quả hữu hạn trong simulator Paper2, dùng lại ba seed blocks. Root đã nghiệm thu19worlds, đóng bundle32outputs và cập nhật Chặng13 của hai báo cáo GVHD. Bản phân tích hiện hành `research_tracking/reports/rq2_learned_graph_source_ability_results_20261109.md`. Bundle đã đóng `rq2-learned-graph-ability-20261109-01`.

## Vì sao cần phép kiểm này?

Paper1 đã tách ảnh hưởng của đồ thị và chính sách, còn Paper2 cho thấy dự báo có thể thay đổi mà kết quả học chưa cải thiện ổn định. Đối chứng năng lực trước đây của khóa luận mới so đồ thị expert với tập cạnh rỗng trong cùng package ước lượng. Chưa biết điều gì xảy ra khi vẫn có31cạnh nhưng thay nguồn cạnh bằng đồ thị học từ lịch sử luyện tập.

Lần này giữ G_env và G_controller expert31, cùng bộ câu, clock, residual năng lực và uniforms. Chỉ đổi G_estimator expert31 sang learned31 đã có từ TRAIN48 của Method24. Mô hình GAM vẫn bật cùng signal/parent adaptation và tắt local adaptation, S1P1L0. Không đưa điểm độ ổn định c_e làm trọng số GAM. Đây là phép kiểm nguồn đồ thị trong một pipeline cụ thể, chưa xếp learned graph thành đúng/sai hoặc tốt/xấu bằng tri thức thật.

## Thiết kế và điều kiện ghép

Dùng ba blocks21000–21002, mỗi block có cùng residual được đặt quanh mức nền1000/1150/1300, và world prerequisite strength λ0/.55. Ba mức này là scalar ability của mọi concept cộng residual, khác ba persona PG/PY/PYH của pilot CPU09. Outcome Y là mean28concept final-minus-base latent theta/Elo tại cuối lịch T41ngày, sau120phản hồi. Khác gross learning gain và tỷ lệ thành thạo.

Có18worlds learned mới cùng một expert sentinel, tổng2.280interactions.18expert outcomes để so lấy từ study36worlds đã đóng, không chạy lại. Sentinel chính là oldc26 ở block21000/ability1150/λ.55. Toàn120observable rows,120oracle rows và endpoint/state khớp exact trước khi18learnedworlds bắt đầu. Independent metadata verifier còn đối chiếu raw serialized lines sau duy nhất đổi cell alias c26→S01.

Oldstudy có accepted assertion cùng initial-policy fingerprint giữa36cells và theta1200, nhưng không lưu raw initial-policy SHA. Root chấp nhận `SOURCE_RECONSTRUCTED_INITIAL_STATE` dựa nguồn constructor/runtime/namespace cùng sentinel exact. Trường oldhash giữ null. New19 ghi initial environment/nonedge policy states/hash và treatment binding riêng. Không suy một sentinel thành chứng minh mọi library/hardware/arm đều tương đương.

## Kết quả đủ18components và9tương phản

Định nghĩa Q_b(a,λ)=Y_expert−Y_learned. Qdương nghĩa net gain expert cao hơn trong cell đó. K_b(a)=Q_b(a,.55)−Q_b(a,0) mô tả thay đổi của khoảng cách nguồn đồ thị khi bật phạt thiếu nền tảng. Đây là finite paired potential-outcome contrast của world đã chỉ định, không humanDiD, mediation hoặc suy luận quần thể.

| Block | Ability | Q, λ0 | Q, λ.55 | K |
|---|---:|---:|---:|---:|
|21000|1000|−0,055965|−0,073775|−0,017810|
|21001|1000|−0,022627|−0,038715|−0,016087|
|21002|1000|+0,056961|+0,086262|+0,029300|
|21000|1150|−0,743541|−0,778692|−0,035150|
|21001|1150|+0,333994|+0,295720|−0,038274|
|21002|1150|−0,620649|−0,656658|−0,036009|
|21000|1300|−0,197266|−0,197266|0|
|21001|1300|+0,181461|+0,181461|0|
|21002|1300|+0,076440|+0,076440|0|

Số trong bảng làm tròn6chữ số, đơn vị theta/Elo points, không phần trăm. Mọi seed/zero/negative được giữ. Independent verifier lấy đúng18oldexpertY và18newlearnedY, kiểm từng component, base/U identities và phép trừ binary64 của18Q/9K bằng nhau theo bit. [Q đầy đủ](../runs/rq2-learned-graph-ability-20261109-01/native__graph_source_contrasts.json), [K đầy đủ](../runs/rq2-learned-graph-ability-20261109-01/native__conditional_lambda_contrasts.json).

Chưa có thứ hạng nguồn đồ thị nhất quán. Ở1000 và1150, expert thấp hơn learned trong hai blocks và cao hơn trong block còn lại, tại cả haiλ. Ở1300, chiều đảo lại theo block, expert thấp hơn một block và cao hơn hai. K1150 âm cả ba, còn K1000 có hai âm/một dương. Không suy dấu này thành một quy luật năng lực hoặc ưu thế learned chung.

Ba K1300 bằng0 đúng negative control, nhưng ba Q1300 đều khác0. Haiλ ở mỗi high block có toàn semantic trace và endpoint exact giống nhau do prerequisite multiplier không hoạt động. Đổi nguồn đồ thị vẫn đổi netgain theo hai chiều dù world không phạt thiếu nền tảng. Kết quả chỉ ra đường tác động qua mô hình/chọn bài và challenge/response dynamics vẫn còn, không xác định riêng đóng góp signal hay parent adaptation, và không chứng minh đồ thị giúp người học thật.

## Đường đi quan sát được thay đổi thế nào?

Ghép oldexpert với newlearned theo đúng block/ability/λ. Cả18cặp đều có ít nhất một question ID khác. Tổng1.409/2.160vị trí ordinal khác câu hỏi; đây là các vị trí trên18cặp quỹ đạo, không2.160independent targets. Bảng sau giữ từng block, mẫu số120mỗi cell. Hai cột cuối đi theo λ0/λ.55.

| Block | Ability | Số vị trí khác câu hỏi, λ0 / λ.55 | Lượt khác câu đầu tiên, λ0 / λ.55 |
|---|---:|---:|---:|
|21000|1000|90/120 / 87/120|23 / 23|
|21001|1000|18/120 / 18/120|89 / 89|
|21002|1000|61/120 / 61/120|47 / 47|
|21000|1150|96/120 / 96/120|12 / 12|
|21001|1150|85/120 / 85/120|34 / 34|
|21002|1150|56/120 / 56/120|47 / 47|
|21000|1300|103/120 / 103/120|10 / 10|
|21001|1300|111/120 / 111/120|6 / 6|
|21002|1300|86/120 / 86/120|4 / 4|

Lượt trong bảng đánh số từ1, trong raw step từ0. Phân số từng cell và first divergence đầy đủ ở [verification JSON](../runs/rq2-learned-graph-ability-20261109-01/independent_verification.json). Tổng theo ability lần lượt335/720,474/720,600/720. Đây là mô tả cùng ba blocks; không ước lượng population rate hoặc so độ khó sau khi bài đã khác.

Trong18cặp, phần đáp án trước khác biệt câu hỏi đầu tiên vẫn trùng. Source cũng giữ predict trước world response và update. Phép đọc này gợi rõ đường truyền graph-source→trạng thái/đề xuất bài, trước khi có đáp án khác trong lịch quan sát; chưa cô lập một mediator. Sau phân kỳ, cùng ordinal step có thể là câu hỏi và history khác, nên không tính paired response Log Loss hoặc gọi mọi Pdelta là matched-query effect.

## Phần mới so với bằng chứng đã có

Study36cũ đổi expert/full sang empty; CPU09 đổi package/pathways/persona. Lần này lần đầu thêm learned31 đang có vào đúng controlled-ability world với G_env/G_controller cố định và source/sentinel đã kiểm. Phát hiện bổ sung là graph-source delta vẫn khác0 ở high-ability negative control dù penaltyλkhông hoạt động, chiều delta phụ thuộc block, và cả18action histories phân kỳ. Không nhân đôi nhận định prediction–learning gap vốn đã có trong Paper2 thành novelty văn liệu.

Graph học từ một TRAIN48/corpus/generation recipe, predictive-stability confidence không P(edge true) và không được dùng như probability. Learned source có thể phản ánh logged order/support; kết quả không là recovery của đồ thị thật hoặc calibrated mastery. Một native GAM variant không thay required AKT/SAKT/GKT/CG fits hay hai environments trong main matrix.

## Thực thi, provenance và giới hạn

Root actual terminal RC0, outer stored33,851749500026926s/60, worker32,67743921279907s/50. Root tool terminal33,8794518s là scope khác, không cộng thời gian nested. Có19environment constructors,19policy builders, mỗi select/predict/interact/update2.280returns và19snapshots.0new graph/offline/neural solver fits, nhưng2.280policy.update là actual adaptive state/model calls.19new initial states ghi riêng, không backfill oldunloggedhash.

Actual563resource samples, family peak117.989.376bytes, min free2.132.578.304bytes; RSS512MiB/free1536MiB và prelaunch2GiB giữ nguyên. Job0/cleanup/handles/GO đã kiểm.63source/input pins trước/sau khớp. Native không có failure hoặc postwrite rejection. Metadata-only independent verifier chạy sau kết quả, không simulation/model call, kiểm32nativefiles before/after cùng SHA, allQ/K và action joins. Đây là post-run verification, không preregistration mới.

Raw observables/oracle/endpoints và19initial snapshots giữ tại output scientific `experiments/simulator/results/rq2-learned-graph-ability-20261109-01/`. Bundle nhỏ giữ summary/log/source/receipts và SHA/size references, không copy69MB Method24 export hoặc runtime/corpus. [Nguồn và bản kiểm](../runs/rq2-learned-graph-ability-20261109-01/README.md).

Giới hạn còn lại gồm chỉ một learned graph và một native estimator recipe, ba reused seedblocks/newindependentN0, scalar ability/residual cụ thể,120feedback/T41days, same-step common uniforms và graph/source initialization assumption đã nêu. Không CI/p-value, causal ability generalization, independent confirmation hoặc human learning benefit. Full noise grid, independent worlds, common calibrated controller và required neural comparators vẫn cần riêng. Kết quả19không hoàn tất RQ2 hoặc RQ3.
