# Episode prospective theo PDF Paper1 — đề xuất02

Ngày09/11/2026. Chỉ đọc nguồn và chuẩn bị đặc tả, chưa đổi production, import, test, simulation hoặc Git. D37 xác định PDF phát triển dùng để nộp là nguồn có thẩm quyền. Đích tiếp theo là một episode có phiên bản và đầu vào rõ, chưa là ma trận50seeds hoặc tái lập số liệu lịch sử.

## 1. Quy tắc đã xác định từ PDF và primitives

Nguồn chính là PDF SHA256 `984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4`, bản trích `docs/thesis_recovery/evidence/paper1.txt` SHA `b6d2d4a518a0b40f27c695bdde3ca624ce16ee976cb59151b15b85cee11eda85`. Dùng tr.2 Eq.(3)–(6), tr.3 Eq.(7)–(9), Algorithm1 và IV.A–C, tr.4 IV.D. Spec01 SHA `3d35b05549eddf593b62314fcd31097323375151f4910d386228a4768afd72a2` giữ nguyên.

| Thành phần | Quy tắc PDF phải giữ |
|---|---|
| US | Latent mỗi concept từ Normal(1400,50²), estimate tất cả1200 |
| UW | Latent mỗi concept từ Normal(1050,50²), estimate tất cả1200 |
| FW | Latent unit hàm số bậc hai từ Normal(1000,50²), nơi khác Normal(1250,50²). Estimate unit hàm số1050, nơi khác1200 |
| Response | Bernoulli với logistic Elo trên latent của concept được hỏi và difficulty item, dùng state trước feedback |
| Learning | Sau mọi item có feedback, latent của đúng concept tăng12, operator `min(1500,latent_before+12)`, không phụ thuộc Y |
| Estimate | Probability từ estimate riêng, sau đó update đúng selected concept bằng K(N_previous)×(Y−P). K40/24/16 tại N<5,5≤N<15,N≥15 |
| Ready | Estimate concept<1250, mọi graph parent có estimate≥1250. Không exposure escape hoặc prerequisite penalty |
| Item | Difficulty gần estimate nhất trong1050/1200/1350, tie prior item exposure rồi itemID |
| Continuity | Nếu chương vừa chọn còn ready, chỉ chọn trong chương đó, rồi lowest-Elo. Equal-Elo tie bằng fixed traversal rank |
| Horizon | Tối đa500feedback đã commit, dừng sớm khi ready rỗng |
| Metrics | Chapter switches, re-entry, estimated mastery rate trên đủ28concept, số feedback và stop reason |

Reuse `Paper1PdfLearner`, `elo_probability`, `dynamic_k` và hợp đồng pending/observe hiện có. Không đưa pi/uncertainty, forgetting, prerequisite learning penalty hoặc world của Paper2 vào. Latent và p_true là oracle diagnostic/world, không là field đầu vào của selector/estimator.

Gaussian chưa được PDF nêu rõ independence, PRNG hay tail handling theo byte. Đề nghị prospective là28standard-normal độc lập theo node, scale/shift đúng bảng trên, không clip initial latent. Giữ operator cap hiện có một cách literal. Nếu initial latent>1500, lần feedback đầu có thể đưa latent xuống1500; ghi nhận corner này, không âm thầm đổi thành truncation hoặc operator chỉ tăng. Estimated Elo cũng không thêm clip.

## 2. Domain và các lựa chọn còn phải chốt

Reuse nguyên `load_prospective_paper2_domain()` hiện có. Nó kiểm năm CSV đã pin, trả28node/84item, B1 gồm25cạnh, GA gồm31cạnh, B1⊂GA và additions3intra+3cross. Dùng active chapter map28node và giữ tám extra keys riêng trong provenance. Receipt load thực tế đã có, nhưng đây vẫn là prospective input reuse, không historical-byte identity. `domain.py` SHA `c37e32420c90f98289b9e21c2e6ea9197324f77a2452b7faae79f8c60985fb18`; primitives SHA `b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f`.

Chỉ ba choice khoa học/triển khai dưới đây cần Root xác nhận trước code. Tên version phải biểu đạt lựa chọn, không gọi là historical policy implementation.

| Điểm PDF chưa định từng thao tác | Quy ước prospective đề nghị |
|---|---|
| Graph dùng cho B0 và cách tiến cursor | `B0_B1_first_unmastered_lex_v1`. Dùng fixed lexicographic topological order của B1 từ loader. Chọn node chưa mastered đầu tiên theo order, lặp node đó đến threshold rồi tiến tiếp. Kiểm node chọn thuộc B1-ready trước serve. Không continuity hoặc ưu tiên Elo trong B0. Đây là một baseline mới được cụ thể hóa từ mô tả fixed order, chưa đại diện duy nhất cho B0 lịch sử |
| Tie traversal của B1/GA | Dùng hai lexicographic topological orders riêng đã trả từ loader. Python Unicode string order, equality theo float64 thực tế, không tolerance/locale/tie RNG. Khác biệt tie rank giữa graph được ghi rõ trong structural contrast; contrast này không được mô tả là chỉ đổi ba cross edges |
| Cross-chapter-unlock chỉ được nêu tên | `direct_cross_unlock_count_v1`, luôn chọn trong ready. Với node v, đếm direct children ở chương khác còn chưa mastered mà mọi parent khác ngoài v đã mastered. Đó là số child sẽ được mở nếu v đạt threshold, không giả sử một đáp án chắc đưa v qua ngưỡng. Chọn score cao nhất, tie lowest estimated Elo rồi fixed traversal rank. Không dùng latent, p_true, gain kỳ vọng hoặc hậu nghiệm đáp án. Chỉ là lựa chọn prospective chờ adopt, chưa khẳng định đúng scoring lịch sử |

Global lowest-Elo là bỏ continuity filter và chọn argmin(estimated Elo, traversal rank) trên cùng ready. Hai ablation global/unlock giữ GA cố định như PDF tr.3 IV.C. Structural conditions B1 và GA giữ continuity; B0 không bị gán continuity. Khi so sánh phải lưu graph bytes, policy rule và traversal order đủ rõ, không gộp thay đổi thành edge-only effect.

B0 định nghĩa trên bảo đảm node đầu chưa mastered ready vì mọi parent đứng trước nó trong B1 topological order đã mastered. Nếu kiểm này sai thì dừng lỗi, không fallback ra ngoài ready. Không thêm cursor reset/sweep policy mà chưa đổi version.

Nhận diện unit FW bằng một chapter key tường minh trong spec, phải đúng một trong ba active chapters và đúng11node của domain hiện tại. Khuyến nghị key `Hàm số bậc 2 và đồ thị` được bind cùng domain identity. Không đoán bằng substring tên concept hoặc tám extra map keys.

## 3. Pure core và runner sở hữu RNG

Version đề nghị `paper1-pdf-prospective-episode-v1`. Chưa adopt tại tài liệu này. Không cần thêm OnlineSession hoặc framework policy tổng quát.

**Pure core nhận draws đã cấp.**

- `initialize_profile(domain, persona, *, function_chapter, normal_z_by_node)` trả immutable initial latent/estimated pairs theo sorted28node. Đòi đúng keys, finite values, persona thuộc US/UW/FW. Standard-normal z là dữ liệu caller cung cấp, hàm này không tự sinh RNG hoặc chứng nhận phân phối của tape dựng tay.
- `run_episode_supplied(domain, spec, profile, *, response_uniforms_by_node)` chạy một episode, dùng primitive predict→world.respond→observe. Tape mỗi node có500u trong[0,1), index bằng số feedback đã commit trước đó của concept. Episode dừng trước khi tiêu thụ draw nếu không có query. Tape sai phải reject trước interaction đầu. Không arbitrary policy callable.
- Selector chỉ nhận estimate/count/current chapter, declared graph và rank. World giữ latent riêng. Core trả trace observable gồm step, q/concept/chapter, P trước Y, N/exposure trước, Y, selected estimate sau; oracle sidecar riêng gồm latent trước/sau và p_true. Kết quả chứa snapshot/metrics/stop reason, không fit hoặc authority claim.

Tên API trên là thiết kế, chưa có production functions. Lựa chọn tuple500u×28node hữu hạn khoảng14.000scalar chỉ là tape RNG, không14.000responses mới. Chỉ tối đa500entries được tiêu thụ trong episode. Có thể cấp tape như immutable tuple pairs, không tạo cache/service riêng.

**Runner sở hữu RNG và provenance.** `run_episode_seeded(domain, spec, *, root_seed, replicate_id)` là wrapper mỏng tạo profile/tape rồi gọi đúng pure core. Root seed và replicate ID bắt buộc, không default50seeds, không seed search. Dùng stdlib `random.Random` private instances, không global seed/state. PRNG/version, Python implementation/version và stdlib random.py SHA được lưu. Không hứa bitwise cross-version/cross-platform trước kiểm chứng.

Đề nghị key được serialize bằng JSON canonical UTF-8, có schema version, rồi SHA256 làm integer seed cho private Random tại mỗi event.

| Event | Key |
|---|---|
| Initial standard-normal tại node v | `(rng_version, root_seed, replicate_id, persona, 'initial_normal', v)`; gọi riêng `Random(key_seed).gauss(0,1)` đúng một lần |
| Response uniform tại lần thực hành thứ n của v | `(rng_version, root_seed, replicate_id, persona, 'response_uniform', v, n_previous)`; gọi `Random(key_seed).random()` |

Graph ID, policy ID và global step không vào key để các branch cùng persona/replicate chia sẻ initial latent và uniform ở cùng concept-local practice count. ItemID không vào response key, nên cùng lần thực hành concept có cùng u khi branch chọn difficulty khác; p_true vẫn tính đúng theo item thực chọn. Không có forgetting/time trong world này, latent tại cùng concept-local count chỉ phụ thuộc initial latent và số feedback. Đây là một coupling prospective có định nghĩa, không tuyên bố historical CRN alignment.

Branch chọn concept khác nhau vẫn có lịch sử và đáp án khác nhau. Shared draw không biến chúng thành fixed-stream comparison, cũng không chứng minh hiệu ứng trên học sinh. Chạy branch khác không được tiêu thụ hoặc làm đổi draw của branch trước; thêm trace/metric không tiêu thụ RNG. Keys chỉ dùng để tái tạo world, không chuyển sang controller. Lưu key scheme và tape/profile SHA, không cần ghi rawtape14.000u trong trace.

## 4. Một episode phải kết thúc và xuất gì?

Spec có enum condition/policy, domain identity, function_chapter, B0/unlock/tie/RNG versions và horizon500. Không có trường rộng cho arbitrary model. Production entry dùng actual domain loader, các test nhỏ dùng domain/bank dựng tay với nhãn chưa xác minh.

Ở đầu mỗi vòng kiểm ready. Nếu rỗng thì `ALL_ESTIMATED_MASTERED` trong finite DAG hợp đồng hiện tại. Nếu đã commit500feedback và vẫn còn ready thì `HORIZON_REACHED`. Đề nghị ưu tiên kiểm ready sau feedback cuối để run vừa hoàn tất ở bước500 được ghi là completed, đồng thời lưu `budget_exhausted=True`. Stop enum và cap flag là hai thông tin riêng. Không dùng `ALL_TRUE_MASTERED` hoặc đồng nhất estimated/latent.

Manifest nhỏ ghi exactsource/input/domain/policy/profile/RNG identities, seed/replicate/persona, horizon, sốdraw thực tiêu thụ, stop/cap flags và initial/final snapshot SHA. Observable trace và oracle diagnostic sidecar tách nhau bằng vai trò, nhưng cùng event keys để kiểm một-to-một. Không thêm reader/authorization framework, không dùng input dataset/Holdout, không xuất credential/private state.

Metrics sequencing reuse switches/re-entry/estimated mastery denominator28. Nếu xuất latent mastery diagnostic thì tên `latent_mastery_rate_at_1250` riêng, explicit source-defined diagnostic, không thay metric PDF hoặc gọi là hiệu quả giáo dục. Chưa aggregate50seeds, chưa SD/CI/p-value và không golden-test số TableI.

## 5. Bốn task triển khai nhỏ sau khi Root chọn quy ước

1. **Profile và draw mapping.** Thêm `paper1_pdf/episode.py` với profile initializer và private RNG/tape wrapper cùng focused unittest. Fixtures z=0 kiểm đúng các means/estimates, sai key/nonfinite reject, FW chỉ đúng declared function chapter, initial latent trên1500 không bị clip. Kiểm global random state không đổi và thêm branch không đổi profile/tape branch cũ. Tests phải phân biệt handmade z với actual Gaussian draw provenance.
2. **Narrow policy dispatch.** Bổ sung enum/rule lựa chọn tường minh vào `Paper1PdfController` sau scope review riêng, giữ default continuity và toàn bộ pending/observe semantics hiện tại. Không nhân bản Elo/world update. B0 fixed order, global và unlock dùng cùng ready/item selection. Fixtures kiểm hard continuity/global phân biệt, unlock không đếm child còn parent khác chưa mastered, tie và B0 cursor không bỏ concept yếu. Existing primitives cần regression sau thay đổi, không tự mở matrix.
3. **Một vòng supplied episode.** Nối initializer/controller/world qua `run_episode_supplied`, max500. Fixtures kiểm forecast trước Y, selected-only estimate/latent, gain12 kể cả Y=0, một draw mỗi commit, R-empty không draw, cap/exact500 completion priority, oracle không vào selector. So sánh hai lần cùng supplied tape cho trace bitwise như nhau và kiểm changed Y chỉ tác động sau prediction tương ứng. Giữ theorem B1 và counterexample liên chương, không ép GA zero re-entry.
4. **Seeded wrapper và một bounded integration được Root cấp riêng.** Kiểm key collision/namespaces bằng metadata và tiny supplied fixtures trước. Sau đó mới đề xuất một episode actual28domain với persona/condition/seed được freeze trước chạy, 500feedback cap và wall/RSS hữu hạn được Root review từ phép đo thích hợp. Không phát450runs hoặc full ablation từ việc chấp nhận code. Evidence ghi cả failure, immutable output theo run và source-before/after.

File scope dự kiến `src/knowledge_tracing/paper1_pdf/episode.py`, focused tests mới và narrow enum dispatch trong `paper1_pdf/simulator.py` khi Root cho phép. `domain.py`, Paper1 historical notebook, dataset, AKT177, protocol/model training và các bundle cũ không cần đổi. Root review file scope/pins trước bất kỳ import/test/execution.

## 6. Quyết định cần trước implementation

Root cần chấp nhận hoặc thay cụ thể ba lựa chọn B0/B1 order + first-unmastered, pergraph lexicographic ties và direct-cross-unlock scoring. Cần chấp nhận coupling theo concept-local occurrence, Gaussian không initial clipping và literal cap sau feedback như mô tả. Những lựa chọn này làm phiên bản mới executable mà không giả lịch sử đã biết. D37/PDF authority vẫn đã được giải quyết; các lựa chọn không làm đổi kết quả PDF kế thừa hoặc ba RQ đề cương.

Đặc tả02 không có simulation mới, mức cải thiện mới, công nhận policy tối ưu hoặc quyền chạy ma trận. Mọi acceptance ở trên là đề nghị chưa thực thi.
