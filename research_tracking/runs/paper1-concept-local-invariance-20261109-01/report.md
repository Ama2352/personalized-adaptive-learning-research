# Khi đổi đồ thị chỉ đổi thứ tự học — bất biến có điều kiện trong Paper1

Ngày09/11/2026. Báo cáo kỹ thuật nghiên cứu theo implementation prospective kế thừa PDF Paper1, quyết định D37. Kết quả gồm chứng minh nguồn và sáu fixture xác định đã chạy. Chưa chạy matrix nghiên cứu, không tái lập random draws hay số liệu lịch sử PDF.

Vị trí canonical dự kiến `research_tracking/reports/paper1_concept_local_invariance_20261109.md`. Các liên kết tương đối dưới đây dành cho vị trí đó. Manifest của bundle mới là bằng chứng đóng gói khi ROOT hoàn tất closure, không suy closure từ tên hoặc wording của báo cáo.

## 1. Câu hỏi nghiên cứu

Một lượt engineering trước đây dùng cùng US42/tape cho graph B1 và GA. Cả hai hoàn thành28khái niệm với172phản hồi, có cùng final-latent SHA nhưng số lần quay lại chương là0và2. Đây là một witness hữu hạn. Câu hỏi mới là liệu equality có được bảo đảm bởi các phương trình và cách ghép randomness khi cả hai nhánh hoàn thành, thay vì cần một thí nghiệm mới cho mỗi graph. [Witness domain28](../runs/paper1-seeded-domain-smoke-engineering-20261109-01/README.md).

Trong implementation hiện tại, latent của mỗi concept tăng12 sau mỗi phản hồi, bị chặn tại1500. Xác suất trả lời chỉ phụ thuộc latent của concept đang hỏi và độ khó item. Đồ thị đi vào ready set và thứ tự chọn concept. Readiness và estimated mastery dùng estimate≥1250, không dùng latent thật. Đây là các vai trò khác nhau của state trong simulator. [Nguồn primitives](../../src/knowledge_tracing/paper1_pdf/simulator.py).

## 2. Mệnh đề bất biến quỹ đạo cục bộ

Giả sử hai nhánh có cùng bank, chapter mapping, initial estimate/latent, item tie rule và tape `u[c,n]` theo concept c và số phản hồi đã dùng n. Giữ đúng source hiện tại với update selected-only, K theo local count, không forgetting/spacing/transfer hoặc phản hồi phụ thuộc global history. Cho phép hai finite DAG và traversal order khác nhau.

**Nếu cả hai nhánh thực sự hoàn thành mọi concept, mỗi concept có cùng local stopping count, local response/item trajectory, terminal estimate/latent và item exposures. Tổng số phản hồi của hai nhánh bằng nhau. Thứ tự global, chapter switches và re-entry có thể khác.**

Mệnh đề không giả định mọi supplied tape hoặc mọi horizon đều đủ để hoàn thành. Nó có điều kiện trên việc hoàn thành. Không cần giả định đáp án luôn đúng hoặc initial latent luôn dưới cap.

### Chứng minh từ source

Đặt local state của concept c gồm estimate, latent, số lần observe và exposures của các item thuộc c. Các item chỉ thuộc một concept.

1. Khi c được chọn, item được xác định bằng khoảng cách difficulty–estimate, item exposure và item ID. Các đại lượng đó đều là local state của c. Graph, current chapter và traversal rank chỉ quyết định concept được chọn, không thay local item rule. Nguồn `simulator.py:144–160`.
2. World tính `p_true=elo_probability(latent_c,difficulty)` rồi `y=int(u[c,n]<p_true)`. Nó chỉ đổi latent_c thành `min(1500,latent_c+12)`. Controller chỉ đổi estimate_c theo `estimate_c+K(n)*(y−p_est)`, local attempt count và exposure của item vừa hỏi. Nguồn `simulator.py:52–59,164–189,238–248`.
3. Bởi induction theo n, hai nhánh có cùng item, estimated P, true P, y và local state trước/sau tại mọi local visit chung. Tape trong supplied episode thực sự được đọc bằng `tape[prediction.concept_id][prediction.previous_interactions]`, trước current label. Nguồn `episode.py:150–168`.
4. Khi estimate_c≥1250, c bị loại khỏi ready và không được update tiếp. Đặt N_c bằng first local hitting count, hoặc0nếu c đã đạt lúc đầu. N_c được quyết định bởi local trajectory, nên không phụ thuộc thứ tự global. Với DAG, nếu còn concept chưa đạt, induced subgraph của các concept đó có root. Mọi parent còn lại đã đạt, do đó ít nhất root ấy ready. Ready rỗng tương đương mọi concept đã đạt trong source này.
5. Nếu hai nhánh đều hoàn thành, mỗi nhánh đã dùng đúng prefix dài N_c cho mọi c. Final local states bằng nhau và tổng phản hồi bằng `Σ_c N_c`. Global chapter history không thuộc kết luận equality này.

Cap không phá proof khi hai nhánh dùng cùng N_c. Tuy nhiên công thức tăng đúng12mỗi lượt chỉ áp dụng cho những update không bị clip. Supplied initial latent>1500 còn có thể bị giảm về1500 ở lần feedback đầu, như source đã khai báo.

## 3. Sáu fixture đã chạy và ranh giới được kiểm

Các fixture dùng API public `initialize_profile`, `run_continuity_episode_supplied` và `Paper1PdfController.ready_set`. Bank dựng tay tối đa3concept/9items có nhãn unverified. Oracle sidecar dùng để kiểm kết quả world, không được đưa vào selector. Không sửa class hoặc private state và không redraw random stream.

| Fixture | Điều được assertion thực kiểm |
|---|---|
| Hai DAG đều complete | Graph rỗng cho chapter blocks A→B, graph b→a2 cho A→B→A. Local prefixes, first stopping counts, item exposures, final estimates/latent và tổng lượt exact bằng nhau; re-entry0/1 |
| Có đáp án sai trước completion | Supplied uniforms.999tạo ít nhất3wrong responses rồi dùng0. Equality vẫn giữ; prefix sai của từng concept được kiểm trực tiếp |
| Finite horizon H4 | Cả hai hết horizon, số phản hồi bằng nhau nhưng allocation/counts và final states khác. Mọi shared local prefix exact và overlap dương |
| Finite H1 có cap | Latent đầu a1498/b1200. Graph rỗng hỏi a, graph b→a hỏi b. Tổng latent gain lần lượt2và12 với cùng một phản hồi |
| Finite H2 không update bị cap | Allocation và tổng đáp án đúng khác nhau, nhưng mỗi oracle increment đúng12 và tổng gain của mỗi nhánh bằng24 |
| Local chain dài và singleton | Sáu wrong uniforms trước0, có hơn một difficulty và local previous count≥15. Chain của concept a1 exact giữa singleton và hai complete interleavings |

Hai phản ví dụ finite horizon không phủ định mệnh đề completion. Chúng phân biệt các giả thiết cần thiết. Đặc biệt, finite H riêng lẻ chưa đủ làm tổng gain khác nhau nếu mọi feedback vẫn cộng đúng12. Khi đó tổng net latent gain là12×Nfeedback, dù response accuracy hoặc allocation khác nhau. Cap cùng allocation khác có thể tạo khác biệt endpoint. [Source test được chạy](../../tests/paper1_pdf/test_concept_local_invariance.py).

## 4. Bằng chứng thực thi và đơn vị

ROOT đã chạy toàn bộ91phương thức Paper1, gồm85hồi quy và6fixture mới. Tất cả đạt, failures/errors/skips/expected-failures/unexpected-successes đều0. Danh sách collected, started và completed trùng exact, không trùng ID. Wrapper đo **5,624195799988229giây dưới cap30giây**. Receipt ghi returncode0, timed_out=false và11source/test trước/sau cùng SHA. [Receipt](../runs/paper1-concept-local-invariance-20261109-01/result.json), [raw stderr](../runs/paper1-concept-local-invariance-20261109-01/stderr.log), [raw stdout](../runs/paper1-concept-local-invariance-20261109-01/stdout.log).

Child audit hook cấm import Torch/NumPy/pandas và các framework được liệt kê, subprocess/os.system và socket creation. Denied list rỗng, Torch/NumPy/pandas không có trong sys.modules cuối lượt. Wrapper sở hữu một subprocess chạy tests. Không gọi đây là0processes hoặc chứng minh OS sandbox tổng quát. Không có model neural, optimizer, teacher Paper2 hay dữ liệu người học nghiên cứu trong fixture.

**13supplied episode calls, tổng horizon464feedback và một controller chỉ đọc ready là trần workload suy tĩnh từ source sáu fixture mới.** Đây không phải measured interaction ledger. Hồi quy85ca khác có workload riêng. Không đổi464thành số phản hồi đã quan sát, không cộng91tests với domain28witness thành sample nghiên cứu.

Candidate ban đầu và file áp dụng khác docstring/comment tiếng Việt. Hồ sơ apply giữ hai SHA riêng. Kết quả91thuộc file đã áp dụng, không gán cho candidate chưa chạy. [Candidate và kế hoạch](../runs/paper1-concept-local-invariance-20261109-01/test_candidate.py), [apply receipt](../runs/paper1-concept-local-invariance-20261109-01/apply_receipt.json).

## 5. Ý nghĩa đối với RQ1/RQ2 và phần còn thiếu

Bằng chứng xác định một trường hợp trong đó graph đổi đường đi quyết định nhưng không đổi terminal local learning states nếu mọi concept đều được học đến cùng local threshold. Vì vậy equality ở witness US42phù hợp với một hệ quả cấu trúc đã chỉ ra. Không cần coi equality đó là bằng chứng graph không thể hữu ích ở mọi điều kiện.

Ranh giới gồm horizon chưa complete, clipping, time/forgetting, prerequisite-dependent learning, cross-concept transfer và update/item selection phụ thuộc global state. Một world chứa các cơ chế đó cần audit riêng. Không thêm cơ chế vào phiên bản này để tạo effect, không quy việc Paper2 có prerequisite dynamics sang Paper1.

Coupling concept/local-count là lựa chọn prospective rõ nguồn trong `seeded_episode.py:60–66,102–120`. Đổi sang shared global-step tape có thể làm phản hồi hai nhánh khác pathwise khi order đổi. Điều đó chưa tự chứng minh marginal-distribution effect nếu các transition kernels và iid noise vẫn giống nhau. Không dùng coupling mới để tuyên bố khôi phục historical random draws. Chưa có claim PDF mâu thuẫn, thay đổi authority D37, empirical graph inefficacy, causal teaching benefit hoặc RQ completion.

Factorial graph-source×ability×prerequisite của Paper2 vẫn là bước thực nghiệm riêng còn thiếu. Note audit đề xuất learned31gắn vào cùng enabled estimator package, G_env/G_controller cố định và matched residual/U. Batch này không thực hiện đề xuất đó. [Audit và giới hạn factorial](../runs/paper1-concept-local-invariance-20261109-01/next_evidence_source_review.md).

## 6. Nguồn và lưu trữ

- Source primitive `b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f`, supplied episode `e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471`, seeded wrapper `7c7ac305cd49fd79f5768173198705be7fa32586114acf5871950c7540dda1b2`.
- Test đã chạy `e38a72290e51b2e9b9bd418829bbe2344b85604ce3f6e8ebad5f6bd845a70780`, candidate `dfa6b07572a76fcf53e48d7815f957bda40c00755ea44cb3d5fc705f2767104f`, runner `e8e0e8770de6c54675a9ed3fd70e06287e97f777e52a110ab48b6731fc9e718e`.
- Paper1 PDF authority SHA `984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4`. Witness domain28manifest SHA `a12e409be45a3c900154b2f7f1d1118bd2e3cda59a66476d6cb32b886da85131` chỉ là tham chiếu độc lập.
- Bundle mới giữ các nguồn chuẩn bị nhỏ, test mới, raw receipt/logs, inventory trước/sau và proof report này. Core và old tests được reference bằng SHA, không nhân đôi. Manifest completed sau closure cùng verify_evidence_bundle xác nhận integrity; mathematical scope vẫn cần review nội dung. [Bundle](../runs/paper1-concept-local-invariance-20261109-01/README.md).
