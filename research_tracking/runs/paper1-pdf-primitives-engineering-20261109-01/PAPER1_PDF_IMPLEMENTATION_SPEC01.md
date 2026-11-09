# Đặc tả candidate triển khai simulator theo PDF Paper1

Ngày09/11/2026. Chỉ đọc PDF, bản trích đã kiểm và các CSV simulator nhỏ. Chưa triển khai, import, test hoặc chạy simulator. Đây là đặc tả để review trước code.

## 1. Nguồn chính thức và phạm vi D37

Theo xác nhận trực tiếp của tác giả được ghi tại D37, **PDF Paper1 là chuẩn thiết kế và kết quả kế thừa của KLTN**. Notebook Enhanced là bản tiền kỳ. Phiên bản simulator mới phát triển theo PDF và có identity riêng. Việc tiếp tục không phụ thuộc tìm lại source cuối. Bằng chứng đã chạy trên bản tiền kỳ giữ đúng phạm vi lịch sử của chúng. [D37](../../../../docs/thesis_recovery/09_DECISION_REGISTER.md).

Nguồn chính là `paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf`,5trang, SHA `984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4`. Bản `docs/thesis_recovery/evidence/paper1.txt` có các mốc trang1–5, đã được kiểm khớp text theo trang trong hồ sơ trước. Ghi chú này dùng các mốc đó để dẫn Eq./Algorithm/Table/Figure. Không chạy lại extraction hoặc simulation. [PDF chính thức](../../../../paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf), [bản trích](../../../../docs/thesis_recovery/evidence/paper1.txt).

Các kết quả TableI/Fig.2/Fig.3 là kết quả kế thừa từ PDF. Code mới chỉ được gọi là triển khai theo đặc tả sau khi kiểm các quy tắc tương ứng. Chỉ gọi tái lập đúng số lịch sử khi có output thực chạy và provenance chứng minh. Ba RQ của Paper1 không thay ba RQ của đề cương KLTN. [Truy vết đề cương hiện hành](../../../../docs/thesis_recovery/02_RESEARCH_TRACEABILITY.md).

## 2. Hợp đồng domain và các cấu hình

| Thành phần | Quy tắc từ PDF | Nguồn |
|---|---|---|
| Domain |28concept thuộc ba đơn vị mệnh đề–tập hợp, bất phương trình bậc hai và hàm số bậc hai|tr.2,III.B|
| Bank |Mỗi concept đúng3items, difficulty cố định1050/1200/1350, tổng84items|tr.2,III.B;tr.3,IV.A|
| B1 |DAG trên cùng28nodes,25edges, tất cả nội chương|tr.2,Eq.(1)|
| GA |DAG trên cùng28nodes,28edges nội chương và3edges liên chương, tổng31|tr.2,Eq.(2)|
| Quan hệ hai graph |GA bổ sung3intra và3cross so với B1. Cần kiểm B1⊂GA và đúng hai nhóm additions|tr.2,III.B|
| B0 |Fixed lexicographic topological order|tr.3,IV.A|
| B1/GA |Cùng continuity-aware lowest-Elo controller trong structural comparison|tr.3,IV.A|
| Horizon |Tối đa500interactions, kết thúc sớm khi ready set rỗng theo Algorithm1|tr.3,IV.A,Algorithm1|

Điều kiện GA−B1 thay đổi cả cạnh nội chương lẫn liên chương. Khi triển khai matrix theo PDF, không đặt tên contrast này thành hiệu ứng riêng của ba cạnh liên chương.

Input domain cho phiên bản mới cần có items, chapter mapping đúng28nodes, exact B1/GA edge sets và stable traversal rank. PDF mô tả cardinalities và ngữ nghĩa graph, không in danh sách từng cạnh hoặc traversal order đầy đủ. Có thể chọn artifact cụ thể để triển khai mới với provenance rõ. Đây là bước cụ thể hóa input, không phải việc mở lại câu hỏi nguồn chính thức đã được D37 giải quyết.

## 3. Tách trạng thái learner thật, estimator và controller

### Learner/world

World giữ `latent_ability[v]` riêng cho từng concept. Với item q của concept v, xác suất sinh đáp án dùng latent ability tại trước interaction

`p_true = 1 / (1 + 10**((difficulty[q] − latent_ability[v])/400))`.

Sau khi lấy đáp án Bernoulli và cho feedback, latent ability của **concept được hỏi** tăng12, tối đa1500. Gain này áp dụng sau mỗi item, không phụ thuộc đáp án đúng/sai theo mô tả. Các concept khác giữ nguyên. PDF không thêm forgetting, prerequisite penalty, motivation hoặc các đặc trưng item ngoài fixed difficulty. Không mang learning/decay dynamics của Paper2 sang phiên bản này. Nguồn tr.3,IV.A và tr.4,IV.D.

| Persona của PDF | Latent initialization | Estimated initialization |
|---|---|---|
| US |Mỗi concept từ Normal(1400,50²)|1200 cho mọi concept|
| UW |Mỗi concept từ Normal(1050,50²)|1200 cho mọi concept|
| FW |Normal(1000,50²) cho unit hàm số bậc hai, Normal(1250,50²) ở nơi khác|1050 cho unit hàm số bậc hai,1200 ở nơi khác|

Các tên US/UW/FW và công thức ở tr.3,IV.A được giữ nguyên. Không đổi chúng thành PG/PY/PYH hoặc sử dụng cơ chế graph-correlated initialization của một simulator khác. Khởi tạo estimate theo persona FW là điều kiện được công bố trong PDF. Nó không cho phép truyền các giá trị latent đã rút mẫu vào estimator.

### Estimator

Estimator giữ `estimated_elo[v]`, số lần tương tác concept `N[v]` và item exposure counts. Dự báo trước cập nhật dùng

`P = 1 / (1 + 10**((difficulty[q] − estimated_elo[v])/400))`.

Sau khi nhận Y∈{0,1}, cập nhật đúng concept được hỏi

`estimated_elo[v] ← estimated_elo[v] + K(N[v])*(Y−P)`.

K dùng số lần tương tác **trước câu hiện tại**. K=40 khi N<5, K=24 khi5≤N<15, K=16 khiN≥15. Sau cập nhật mới tăng N. Không cập nhật difficulty hoặc các estimate còn lại. Mastered khi updated estimate≥1250. Nguồn tr.2,Eq.(5)–(6), tr.3,Eq.(7).

Phiên bản mới cần tuân đúng ranh giới N=15 của Eq.(7). Không lấy một helper từ simulator khác chỉ vì tên cùng là dynamic K. PDF không yêu cầu pi, memory residual hoặc uncertainty gate cho estimator này.

### Ranh giới thông tin

Controller/estimator chỉ nhận domain, fixed initial estimates, q/difficulty, lịch sử Y và các counts của mình. World không phải field của controller. Oracle latent/p_true chỉ đi vào response generation và diagnostic logging tách biệt. Forecast P phải được ghi từ state trước khi current Y được dùng để cập nhật. Trong Algorithm1,tr.3, biểu thức P đứng sau bước nhận S nhưng vẫn chỉ phụ thuộc pre-update θ/difficulty. Triển khai predict-before-observe làm rõ ranh giới đó và giữ nguyên Eq.(5)–(6).

## 4. Controller có thể triển khai trực tiếp từ PDF

Với threshold1250, ready set chỉ chứa concept chưa mastered mà **mọi** predecessor đã mastered. Nếu ready set rỗng thì dừng. Không thêm readiness theo số exposure, least-deficit escape hoặc lựa chọn vi phạm prerequisite. Nguồn tr.2,Eq.(3),tr.3,Algorithm1.

Continuity filter lấy các ready concepts trong chương được chọn ở interaction trước. Nếu nhóm này khác rỗng, chỉ chọn trong nhóm đó. Nếu rỗng, chọn trong toàn ready set. Sau đó chọn concept có estimate nhỏ nhất. Equal-Elo ties theo fixed graph traversal rank đã khai báo. Đây là hard filter trước argmin, không phải một tie-break ưu tiên chương sau khi xét global Elo. Nguồn tr.3,Eq.(8)–(9).

Item được chọn có |difficulty−estimated_elo| nhỏ nhất trong ba items của concept. Nếu bằng nhau, ưu tiên item ít exposure trước, rồi item identifier. Cập nhật current chapter bằng chương của concept đã phục vụ. Counts phải có nghĩa previous interactions/exposures tại thời điểm chọn, được commit một lần sau response trong thiết kế simulator một lượt đầy đủ. Nguồn tr.2,Eq.(4),tr.3,Algorithm1.

Plain lowest-Elo bỏ continuity filter nhưng giữ cùng ready-set/item/Elo components. Với cross-chapter-unlock, PDF tr.3,IV.C chỉ nêu tên policy, không đưa scoring/tie formula. Cần khai báo rank rule của phiên bản mới trước khi thực hiện nhánh ablation đó.

## 5. Matrix và metrics phải giữ ngữ nghĩa

Structural comparison gồm3personas×3conditions(B0/B1/GA)×50seeds=450runs, mỗi run tối đa500interactions. Policy ablation giữ GA, so continuity/plain lowest-Elo/cross-chapter-unlock trên ba personas và50seeds. PDF không cung cấp seed IDs, thuật toán RNG hoặc manifest việc tái dùng GA-continuity giữa hai bảng. Không cộng các ô thiết kế thành số physical runs lịch sử mới. Các lựa chọn RNG/pairing và reuse phải ghi trong manifest triển khai mới. Nguồn tr.3,IV.A–C và tr.5,Fig.3.

| Metric | Định nghĩa executable | Kiểm tra |
|---|---|---|
| Chapter switches |Đếm t>1 khi chapter[t]≠chapter[t−1]|Lặp cùng chương không tăng count|
| Chapter re-entry |Một switch vào chương đã từng xuất hiện trước interaction đó|A→B→A có2switches và1re-entry|
| Mastery rate của kết quả sequencing |Số concept đạt estimated threshold1250 trước khi run kết thúc, chia28|Đặt tên field `estimated_mastery_rate` rõ nghĩa; latent truth nếu log phải là field khác|
| Steps/budget stop |Số responses thực nhận và lý do stop, phân biệt R_empty với horizon500|UW tại cap mô tả progress trong budget, không eventual mastery|
| Aggregates |Mean±SD theo50seeds của từng persona-condition|Không gọi SD là CI, không coi events/bins là independent N|

Mastery mapping trên xuất phát từ tiêu chí concept được đánh dấu mastered sau Elo update tại tr.3 và mô tả rate ngay sau Algorithm1. Nếu cần báo latent true mastery ở simulator mới, phải dùng tên và mục đích diagnostic riêng, không thay numerator TableI âm thầm. SD cần khai báo sample/population convention trong implementation manifest vì PDF không nêu ddof.

### Kết quả kế thừa dùng làm ngữ cảnh, không làm golden acceptance bằng số

| Persona | B0 switch/re-entry/mastery | B1 switch/re-entry/mastery | GA switch/re-entry/mastery |
|---|---|---|---|
| US |11/9/1,000|2/0/1,000|2/0/1,000|
| UW |2,940/0,940/0,476|1/0/0,435|1/0/0,466|
| FW |11/9/0,999|2/0/0,998|2/0/0,998|

Đây là các **mean đã báo trong TableI,tr.4**, không phải output mới. Bản gốc còn có SD. Fig.3/tr.3–4 báo mean re-entry của plain lowest-Elo16,70/17,22/18,36 và cross-chapter-unlock16,86/17,26/19,36 cho US/UW/FW, còn continuity bằng0 trong tested runs. GA không có lợi thế nhất quán so với B1. Không ép unit tests hoặc chọn seed/input để khớp các số này. Tuyên bố về behavior mô phỏng giữ tách biệt với classroom effectiveness như PDF đã giới hạn ở tr.1,4–5.

## 6. Các trường cần khai báo thêm trước implementation/matrix

| Trường chưa được PDF quy định từng byte | Đề nghị cụ thể hóa, chưa adopt trong ghi chú này |
|---|---|
| Exact domain artifacts |Khai báo28IDs, chapter mapping,84item IDs và exact B1/GA edges cùng SHA. Không dùng cardinality làm bằng chứng identical historical input|
| Graph traversal tie order |Caller cung cấp stable rank hoặc chọn một thuật toán deterministic được version. B0 giữ lexicographic topological order như PDF|
| Graph dùng để tạo B0 order |Ghi rõ lấy topological order theo topology nào, không tự mặc định là GA/B1|
| Cách tiến cursor B0 |Candidate nhỏ là first-unmastered theo fixed order, lặp concept đó tới mastery. Cần ghi rõ trước code vì PDF chỉ mô tả fixed order|
| Unlock policy |Cần exact scoring/candidate/tie rule riêng. Core continuity có thể triển khai và kiểm trước khi hoàn thiện ablation này|
| Seed/RNG/pairing |Khai báo50seed IDs và RNG algorithm, thứ tự rút Normal/Bernoulli. Common random numbers là lựa chọn thiết kế mới phải ghi rõ, chưa được coi là chi tiết lịch sử đã biết|
| Gaussian tails và cap1500 |PDF viết Normal initialization và cap sau learning. Không tự thêm initial clipping. Cần ghi cách xử lý nếu initial latent vượt1500 để ngữ nghĩa update rõ ràng|
| Estimated mastery representation |Eq.(3) dùng current estimate; không tiếp tục chọn concept đã mastered. Với unselected estimate bất biến và không forgetting, mastery sẽ absorbing trên normal loop. Nếu lưu sticky flag, phải kiểm nó tương đương quy tắc này|
| Numeric/summary convention |Chọn float64/stable Elo computation, exact-equality tie convention và SD ddof. Không thêm probability clipping hoặc tolerance làm đổi kết quả mà thiếu version metadata|
| Logical time/export |Paper1 không có decay/timestamp dynamics. Có thể dùng step index, nếu nối ItemQuery thì caller khai báo logical timestamp và source_row≥1. Không kế thừa schedule6/72giờ của CPU09|

Các trường trên là đầu vào cụ thể hóa cho triển khai mới. Chúng không mở lại Q01/S01 hoặc biến PDF authority thành điều kiện đang chờ. Những lựa chọn thay domain edges, policy ablation hoặc pairing cần được ghi rõ trong kế hoạch nghiên cứu mới, còn module layout/hash/log formatting là quyết định engineering thông thường.

## 7. Bank Paper2 có thể tái dùng đến đâu?

Đọc tĩnh bốn CSV Paper2 cho thấy28unique nodes,84unique items, mỗi concept đúng3items và mỗi difficulty1050/1200/1350 có28items. Item concepts đều nằm trong28nodes. Chapter map có36unique keys, trong đó28node-domain được phủ đầy đủ và8keys nằm ngoài domain. Nếu dùng candidate bank này, cần materialize hoặc bind mapping restricted đúng28nodes với provenance, không tự mở rộng thành36concept.

Trên mapping restricted, `edges.csv` có31edges, gồm28intra và3cross, endpoints đều trong domain. Ba cross pairs là `ThucHienPhepToanTrenTapHop→GiaiDuocBatPhuongTrinhBacHai`, `GiaiThichDinhLyVeDau→VeDoThiParabolCuaHamSoBacHai`, `XacDinhTinhDungSaiCuaMenhDe→VeDoThiParabolCuaHamSoBacHai`. Cardinalities phù hợp hình dạng GA trong PDF, chưa chứng minh historical byte identity. Chưa có kiểm DAG mới trong lượt source inspection này. B1 không thể được tạo bằng cách chỉ xóa3cross từ file này, vì sẽ còn28intra thay vì25. Cần exact declared B1 artifact và sáu additions được kiểm độc lập trước simulation.

Chỉ domain bank là candidate reuse. Không dùng latent learner, initialization, forgetting, prerequisite penalty, GAM uncertainty hoặc controller escape của Paper2 để thực hiện phương trình PDF Paper1. Dữ liệu CPU09/Protocol21 đang có giữ environment/source identities của chúng, không relabel thành output của simulator mới.

## 8. Gói implementation nhỏ nhất đề xuất sau review

Version candidate `paper1-pdf-controller-simulator-v1`. Phạm vi code sau này có thể chỉ gồm một module mới `src/knowledge_tracing/paper1_pdf_simulator.py` và một file tests mới `tests/shared_kt/test_paper1_pdf_simulator.py`. Giữ notebook tiền kỳ và các source đã gated nguyên vẹn. Reuse `SimulatorItem`/`SimulatorBank` cho item/domain identity. `PrerequisiteGraph` là representation dùng được nhưng constructor hiện có chưa chứng minh DAG, nên vẫn cần validation DAG/rank riêng.

API nhỏ cần biểu đạt đủ ba phần, không thêm trainer hoặc OnlineSession framework song song.

- `Paper1PdfSpec` giữ declared bank/chapters/B1/GA/traversal/B0/unlock/RNG choices và source identities. Fields chưa được chốt không được rơi về default ngầm.
- `EloLearnerState` giữ estimates/counts/exposure/current chapter. `choose` chỉ thấy state này và domain. `predict` chỉ dùng estimated state và item.
- `LatentLearnerState` giữ latent vector và response RNG riêng. `respond_and_learn` nhận item, sinh Y rồi tăng đúng selected latent concept12/cap1500.
- `run_episode` ghép predict-before-observe/update, trả immutable interaction trace, stop reason và metrics. Chạy thật cần budget/output/seed manifest riêng do Root review. Không mở450runs chỉ từ việc chấp nhận source spec.

### Acceptance nhỏ cần kiểm trước bất kỳ matrix nào

1. K ởN=4/5/14/15 lần lượt40/24/24/16. Dự báo hiện tại bất biến khi đổi current Y, estimate chỉ đổi sau observe. Một update không đổi difficulty hoặc estimate khác.
2. World response dùng latent value, không dùng estimate. Đổi latent nhưng giữ observable history không tự đổi controller state. Learning+12 áp dụng cảY=0 vàY=1, chỉ ở selected concept, không forgetting trong các bước chưa phục vụ.
3. Ready set từ all-parents mastered. Continuity chỉ lọc trong R, không cứu prerequisite chưa đạt. R rỗng dừng, không dùng exposure fallback.
4. Current chapter có ready node thì giữ chương đó ngay cả khi chương khác có Elo thấp hơn. Nếu current chapter không có ready node thì chuyển chương theo global argmin và stable tie rank.
5. Item ties dùng prior exposure rồiID. Chọn item không tự nhìn Y hoặc latent state. Counts commit đúng một lần.
6. Unit fixture A1→B1→A2 với chapters A/B/A và scripted mastered snapshots phải cho A→B→A khi dependency buộc phải đi như vậy. Nó kiểm conditional controller semantics, không thay tested domain hoặc bác kết quả0re-entry trong các tested runs của PDF. Không thêm closed-chapter ban chỉ để force0 cho mọi DAG.
7. Metric fixtures gồm rỗng/single-chapter, A-A-B-B-C với2switches/0re-entry và A-B-A với2/1. Mastery denominator luôn28 ở production domain, không chỉ concepts đã phục vụ.
8. Bank/domain/edge counts, no duplicate IDs/edges, endpoints, DAG, B1⊂GA và3intra+3cross additions. Snapshot/RNG replay cùng declared configuration phải deterministic, còn identity khác phải được phân biệt.

Các kiểm tra này là đề xuất source/fixture. Chưa có test hoặc trajectory mới được thực hiện trong ghi chú này. Tái dựng thuộc Paper1 cung cấp môi trường/phân rã cơ chế để phát triển KLTN, giữ nguyên yêu cầu RQ1/RQ2/RQ3 và các baselines trong đề cương.

## 9. Inventory nguồn đã đọc

| Nguồn | SHA-256 |
|---|---|
| PDF Paper1 |`984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4`|
| `docs/thesis_recovery/evidence/paper1.txt` |`b6d2d4a518a0b40f27c695bdde3ca624ce16ee976cb59151b15b85cee11eda85`|
| Decision register chứa D37 tại lúc đọc |`be1c275b0797b0d37548861180ad6d7f8dde770ecb046c62dd661fe802b3d5d1`|
| Paper2 `nodes.csv` |`6db464d1fd3df5d4215d51c9f90dc0f7e24f252517252784c80bdb5fa6291650`|
| Paper2 `edges.csv` |`ecd910d8df52f8790997391de657ea0f9e8357446212c168b73e500d0facc2fb`|
| Paper2 `concept_to_chapter_map.csv` |`aa99cffb251ce6757258d2e87fe707455bc74b6b3917ead1acf48c5e96ee0a17`|
| Paper2 `question_bank.csv` |`fb5924ac0d19049ef1a5be23352592e30dfa3a4bde3e3fa07f10979fe0887e4d`|

Các CSV ở `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/`. Page correspondence của extract có trong `research_tracking/reports/paper1_revision_reconciliation_20261107.json` mục `pdf.page_checks`,5trang text khớp. Chỉ dùng hồ sơ đó cho text provenance trong ghi chú này. D37 là quyết định hiện hành về authority. Không chỉnh hồ sơ audit hoặc source lịch sử.
