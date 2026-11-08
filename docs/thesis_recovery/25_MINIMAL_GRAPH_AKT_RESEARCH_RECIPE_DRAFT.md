# Draft: nhánh graph tối thiểu cho lifecycle AKT nghiên cứu

08/11/2026 · **DRAFT_ONLY — chưa adopt, chưa cấp quyền thực thi.**

Tài liệu này cụ thể hóa phương án root đề xuất để review trước implementation. Không sửa [protocol21](21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md), [lifecycle22](22_A0_RESEARCH_LIFECYCLE_CONTRACT.md), [hạch toán23](23_TRAINING_MATRIX_ACCOUNTING_V1.md), prototype engineering hoặc run đã đóng. Không có model/optimizer/data run mới. Nếu root chọn phương án, cần quyết định adoption riêng gắn đúng SHA của draft và recipe; không suy adoption từ việc tài liệu tồn tại.

## 1. Câu hỏi kiểm được và mức đóng góp

**Giả thuyết hữu hạn:** trên cùng observable corpus, backbone initialization và effective causal window, một residual vô hướng dựa trên đáp án quá khứ của các concept cha có thể bổ sung giá trị dự báo so với A0; weighting bằng predictive stability và gate có thể điều chỉnh mức ảnh hưởng ấy. Giả thuyết có thể không được dữ liệu ủng hộ: alpha có thể gần0, các variants có thể không tốt hơn A0, gate có thể hằng hoặc selector giữ A0.

Đây là **một candidate CG-AKT tối thiểu**, không đại diện mọi graph-aware KT hoặc mọi cách dùng quan hệ tiên quyết. A1–A3 được huấn luyện riêng; không gọi wrapper hoặc random initialization là model đã fitted. Việc thêm nhánh không buộc xác suất, loss hoặc kết quả học phải tốt hơn. Không coi low gate là bằng chứng cạnh sai.

Phương án cố ý giảm capacity và số lựa chọn kiến trúc: không concept embeddings, không learned message MLP, không query embedding bổ sung, không learner-ID feature. Lợi ích là dễ kiểm thông tin và chi phí; đánh đổi là giới hạn những quan hệ có thể biểu diễn, nêu tại mục5.

## 2. Recipe được đề xuất chốt

Tên recipe dự thảo: `cgakt-centered-parentmean-scalar-v1-draft`. Không dùng lại tag `engineering-observed-parent-mean-v1` như thể prototype đã được adopt cho nghiên cứu.

Với target item thuộc concept q tại global rank t:

- Dùng đúng prefix trước t và **effective window của native AKT**, gồm global block anchors, context100/targetblock100 và OOV reset thực tế. Không cấp full-history cache riêng cho graph.
- Với mỗi cạnh khai báo j→q, `n_j` là số observable responses của concept j trong effective prefix; `o_j=1[n_j>0]`. Khi đã quan sát, `mu_j` là mean correctness0/1 của các responses đó. Không đọc current/future y hoặc latent theta/mastery.
- Fixed message một chiều: `s_j=mu_j−0.5` nếu `o_j=1`; nếu chưa quan sát thì message0 và observed weight0. Đây là **tóm tắt đáp án**, không xác suất thành thạo đã hiệu chuẩn.
- `a_j=c_jq*o_j`, `mass=sum_j a_j`, `normalizer=max(1,mass)`; `m_q=sum_j(a_j*s_j)/normalizer`. Giữ nguyên kernel normalizer hiện có, không đổi sang mean chia mass khi mass<1.
- Residual `r_q=alpha*g_q*m_q`; augmented logit `z_q=z_native+r_q`. **alpha là một Parameter scalar signed, khởi tạo0**, train cùng backbone bằng response loss. D=1, fixed identity message; không có message weights/bias trainable.

| Variant | Confidence | Gate | Tham số graph bổ sung |
|---|---|---|---|
| A0 | Không dùng | Không có nhánh |0|
| A1 | c=1 trên đúng declared graph | g=1 | alpha:1|
| A2 | Actual accepted Method24 score trên đúng declared graph | g=1 | alpha:1|
| A3 | Cùng artifact c với A2 của graph condition tương ứng | sigmoid Linear4→1 | alpha1 + gate weights4/bias1 =6|

**Gate A3:** `x=(S/(1+S),mean(c),population_variance(c),observed_fraction)`; `S=sum_j n_j` qua các declared parents, không phải số learner train. Mean/variance confidence dùng **toàn bộ declared query parents**, kể cả chưa được quan sát trong prefix; observed fraction là số parents có n_j>0 chia số declared parents. Không có parent cho vector0 nhưng phải native-bypass trước khi gọi gate. Gate weights và bias đều0, nên g=0.5 ban đầu ở active contexts. Các feature này giống định nghĩa đã kiểm trong prototype; việc adopt chúng cho research vẫn là quyết định mới của draft này.

### Native path, objective và numerical contracts

Whole graph-off, graph-empty, không observed parent hoặc zero observed confidence mass phải gọi nguyên native path trước branch arithmetic. Cùng native backbone/batch/mode/RNG cho exact output/loss/count và backbone-gradient parity. Đây là intra-model disable, **không** independent A0 checkpoint fallback.

**Không bypass theo alpha==0 hoặc residual==0.** Ở khởi tạo alpha0, branch vẫn phải giữ computational graph để alpha nhận gradient. Mỗi inactive slot trong mixed batch dùng base logit/probability từ **cùng forward**, không chạy native lần thứ hai để tạo control dưới dropout. Gate0 do sigmoid saturation có thể ghi actual gate0; chỉ ghi null khi gate thực sự không được tính/bypass.

Training dùng đúng response cross-entropy của pinned upstream: `BCEWithLogitsLoss(reduction=none)` trên supported target slots, sum rồi chia count trước backward; n_pid0 không có Rasch regularization. Không inverse-sigmoid từ native probability, detach branch, patch hooks hay rewrite upstream. Raw epoch-selection objective tiếp tục theo runner hiện có: Torch BCE mean trên **cùng exported float32 p và label**; canonical reporting metrics giữ evaluator hiện hành. Không trộn training-logit loss, selection BCE và temperature-fit objective thành một số.

## 3. Initialization, optimizer và lifecycle

Native geometry/hyperparameters giữ policy nghiên cứu hiện hành: d_model256,8heads,1block,d_ff1024,final_fc512,dropout0.05,batch4,context100/targetblock100,max_length200; seed42,maxepochs20,patience3,min_delta0.0001. Adam dùng lr1e−4,betas(0.9,0.999),eps1e−8,weight_decay0 và native gradient clipping1.0 trên **toàn bộ backbone+alpha+gate parameters**. Không extra L1/L2, alpha penalty, gate entropy penalty, separate learning rate hoặc tuning theo selection/final. Cấu hình/budget thực thi phải khai báo riêng; maxepochs20 không tự cấp quyền chạy20epoch.

Mỗi candidate có fresh backbone và Adam, cùng initial backbone **tensor state** đã ghim identity với A0. Có thể dựng lại từ cùng seed/source/config và kiểm exact initial-state hash; không warm-start từ A0 đã train. Branch construction phải tách/preserve backbone RNG stream; alpha/gate constants không được làm thay dropout/RNG exposure trước native construction. Same initial state không bảo đảm trajectories hoặc fitted checkpoints giống nhau sau optimization.

Selected-fit dùng train80, raw selection10 chọn epoch theo objective/tie hiện có. **Tất cả candidates phải xuất raw best-epoch selection trước system-selector freeze và trước mọi main refit90.** A0 single-candidate pilot đang có không được gọi tuần tự rồi hồi tố thành main matrix đã đúng thứ tự.

Refit90 dựng lại backbone, alpha và gate từ cùng initialization recipe với Adam mới; train đúng selected epoch count, không tiếp tục best weights và không chọn lại winner bằng selection đã thành train. Response calibration10 thực hiện sau refit trên checkpoint cuối, không cập nhật neural weights. Giữ toàn target ledger, null/reason cho OOV/unsupported; graph không cứu target ngoài vocabulary.

**Đề xuất freeze graph/confidence:** fit learned graph và confidence chỉ từ **train80**, giữ nguyên exact edges/c-values/artifact qua neural refit90. Không chạy thêm2352surrogate fits, không relabel union90 thành train để vượt API Method24 hiện tại. Đây là policy cần được ghi rõ khi adopt, không phải implementation trick đã mặc nhiên được protocol21 chọn. Nó giảm chi phí và tránh đổi topology sau raw candidate comparison; đánh đổi là graph/confidence chưa khai thác thêm selection10 dù neural weights có. Các ngân hàng/vocabulary mới vẫn có lineage90 riêng.

Metadata bắt buộc phân biệt `neural_fit_scope=select_train80`, `neural_refit_scope=refit_union90`, `graph_fit_scope=train80`, `confidence_fit_scope=train80`, `graph_confidence_refit_policy=frozen_train80_through_refit90`, `graph_refitted_on_union90=false`, `confidence_refitted_on_union90=false`. Không gọi toàn bộ pipeline “mọi thành phần fit trên90%”.

## 4. Graph/confidence provenance và independent A0 fallback

G_env và G_controller chuyên gia giữ nguyên giữa conditions; chỉ G_estimator thay expert/learned/noisy như protocol21. Mapping item84→concept28 lấy từ actual bank đã ghim domain/vocabulary, không lấy numeric-index coincidence hoặc Junyi checkpoint để thay.

Declared graph phải canonical, direction rõ, endpoints thuộc actual domain; learned graph chỉ được nhận nếu accepted artifact đạt rule edge-budget/support đã freeze. Không fill thêm cạnh để ép đủ31 hoặc nhận thiếu-budget graph như supported graph. Đếm rõ declared edges, supported/unsupported edges, effective observed mass và query coverage. Lợi ích/khả năng nhận diện không được suy từ số cạnh hoặc support đơn thuần.

A2/A3 chỉ nhận Method24 artifact được nghiệm thu hoàn chỉnh và đúng recipe/role, không reservation/pending/partial result. Parser cần bind đồng thời corpus/DONE, plan, train observable/provenance/shard hashes, source+runtime/recipe, cross-fit/fold population, accepted output manifest và actual graph hash. C-values phải join exact(parent,child); không duplicate/missing/extra edges, nonfinite hoặc oracle labels. A1 fixed c=1 có provenance declared graph riêng.

Method24 định nghĩa paired OOF response-loss reduction, lấy trung bình theo learner rồi bootstrap learner trên frozen deltas; c là fraction200draws có reduction>0 với tối thiểu20eligible train learners. Đây là **predictive-stability score có điều kiện trên surrogate đã fit**, không P(edge true), Bayesian posterior hoặc calibrated edge-correctness probability. Enum hiện có `EdgeConfidence.kind='estimated_probability'` là tên kỹ thuật kế thừa; metadata/display phải ghi `score_semantics=predictive_stability`, không suy ý nghĩa probability từ tên enum.

Unsupported edge giữ nguyên flag/reason; nếu implementation cần tensor c thì operational c=0 với support metadata riêng, không được diễn giải là chứng minh cạnh sai. Oracle labels/noise-generator knowledge không vào main branch/gate; privileged oracle reference là condition riêng chưa nằm trong draft này. Actual artifact đáp ứng điều kiện hay chưa phải kiểm lúc admission; tài liệu này không tuyên bố Method24 đã thành công trên corpus nào.

System selector giữ nguyên rule21: so A1/A3 với **checkpoint A0 train riêng**, trên common-supported raw selection targets kèm full coverage; chỉ graph eligible khi upper95%learner-bootstrap bound của `LL_graph−LL_A0`<0, rồi chọn eligible có meanLL nhỏ nhất; nếu không có thì A0. **A2 chỉ là ablation, không tự thêm vào eligible winners.** Freeze kết quả trước main refit/calibration; không dùng gate-off A3 như A0 độc lập hoặc dùng calibrated/final labels để thay winner.

## 5. Phản biện capacity và identifiability

| Đánh đổi có thật | Hệ quả cần ghi, không “sửa” sau khi thấy outcome |
|---|---|
| D1 là weighted centered mean | Hai pattern cha khác nhau có thể cùng summary; positive/negative messages có thể triệt tiêu. Không học tương tác nhiều cha hoặc đặc trưng query/edge riêng. Không improvement không bác bỏ mọi graph representation. |
| Một alpha toàn cục | Không biểu diễn trực tiếp việc parent evidence có dấu khác nhau theo target. Alpha signed có thể âm; không ép monotonic prerequisite benefit. |
| Alpha0 và gate0.5 | Gate gradient chính xác0 ở bước đầu vì nhân alpha0; không được coi là bug. Alpha có thể nhận gradient nếu message và loss derivative không triệt tiêu. Khi alpha vẫn0 vì dữ liệu/saturation, gate có thể không học; phải báo, không random-restart để tìm hiệu ứng. |
| Alpha và gate cùng scale residual | Có scale confounding/weak identifiability; low gate không có diễn giải causal edge invalid. Mean/variance confidence cố định theo parent set còn có thể hoạt động như query-concept proxy. |
| Normalizer max(1,mass) | Giữ attenuation khi mass<1. Khi tất cả observed c được scale đều và mass≥1, scaling có thể triệt tiêu trong normalized mean; không hứa absolute confidence luôn giảm residual theo tỷ lệ. |
| A1/A2 mean0.5 có thể cho residual0 | Có support không bảo đảm branch influence/gradient không0; instrumentation phải phân biệt supported, numerical residual0 và disabled. Không yêu cầu metric cải thiện để “pass”. |
| A3 khởi tạo g0.5 | Initial forward vẫn A0 vì alpha0, nhưng alpha gradient bị scale0.5 so A2; optimizer có thể bù khác nhau. Không mô tả A2/A3 như identical optimization ngoài gating. |
| Graph/confidence train80 giữ nguyên qua refit90 | Tiết kiệm một fit-surrogate phase và giữ graph candidate identity; không là fully-refitted estimator trên90%. |

**Khuyến nghị:** D1 đủ để kiểm một giả thuyết residual hạn chế và có thể triển khai đầu tiên, không cần thêm MLP chỉ để tăng capacity. Chưa có evidence yêu cầu thay đổi. Nếu về sau cần phân biệt positive/negative evidence bị triệt tiêu, phương án nhỏ tiếp theo là fixed two-channel positive/negative centered messages với hai scalar readouts; đó là **variant mới phải version/freeze trước chạy**, không fallback âm thầm của draft này. Không dùng metric bất lợi của D1 để chọn thêm features trên final.

## 6. Contract checkpoint, routing và failure

Research context phải typed và purpose riêng, không nới các smoke/d32/engineering caps của `GraphPrototypeSpec/GraphEngineeringSetup`, không sửa role checkpoint engineering thành research. A0 mặc định giữ đường hiện có; raw-selection candidate stage và refit-after-system-freeze cần admission rõ ràng. Không truyền full corpus/calibration labels vào optimizer context.

Checkpoint constructor/identity phải kiểm **trước torch.load/model allocation**: variant, recipe version, initial-state SHA, graph/confidence source artifact+train80 lineage, item↔concept map/bank, encoding80/90, phase/freeze, native recipe, full module schema/source/runtime và byte cap. Save/load toàn native backbone+alpha+gate khi có; không pickle callable. Reload strict keys/shapes/dtypes/finiteness, bounded deterministic native-window prediction/loss/count parity. Old toy Linear-message checkpoints khác schema, phải bị từ chối.

Durable global counters reservation/body-returned/completed/targets/time trải selected-fit và refit; adapter không tạo một budget reset riêng. Không fake complete epoch hoặc promote wrapper vì có state_dict. Lỗi sau step không rollback; lỗi source/runtime/coverage/budget/artifact STOP giữ partial/failure và output cũ, không repair/retry tự động. Owned-process cleanup/terminal receipt là điều kiện riêng; xóa tham chiếu không bảo đảm RSS trả về OS ngay.

## 7. Acceptance cần chuẩn bị, chưa thực thi trong draft

1. **Pure admission/serialization:** reject engineering tag, wrong role/domain/map/corpus/graph/recipe/artifact SHA, structural toy hoặc oracle c trong main condition trước lazy Torch. Method24 artifact thiếu edge/unsupported phải có explicit handling, không guessed confidence. Refit identity giữ graph/confidence train80 trong khi encoding/neural phase chuyển90.
2. **Known-answer arithmetic:** centered means0/0.5/1, observed masks, empty graph, c0, mass<1, mass≥1, confidence scaling/cancellation; D1 kernel khớp weighted sum/max(1,mass). Không duplicate arithmetic implementation trong production.
3. **Causality/geometry:** current/future-label perturbation không đổi p_t/context; prefix và global source/rank/window anchors giữ nguyên; rollover100/200, OOV barrier, cross-learner isolation; oracle/future/extra-history bị từ chối. Không giả max12toy đã chứng minh full rollover.
4. **Forward/backward có ý nghĩa:** same initial backbone/mode/RNG; whole-off/mass0 exact native p/loss/count+backbone gradients; mixed inactive slots khớp cùng-forward base. Alpha0 active path không detach/bypass: trên nondegenerate fixture alpha nhận finite nonzero gradient, gate gradient0 ở step đầu là expected. Sau alpha nonzero, kiểm gradient gate/backbone khi fixture có đường truyền, không ép gradient trên mọi dataset.
5. **Một genuine step khi được cấp quyền riêng:** Adam sở hữu đúng toàn parameters, clipping bao cả branch; durable start/body/complete counters đúng cả injected post-step failure. Không yêu cầu loss improvement, alpha positive hoặc gate phân tán để nghiệm thu phần mềm.
6. **Lifecycle/selection/fallback:** candidate exports đủ same supported/full keys; system freeze trước mọi main refit; fresh alpha/gate/backbone/Adam ở refit, không calibration leak; A2 không eligiblewinner; negative selector chọn đúng independent A0 manifest. Gate-off A3 được gắn nhãn same-backbone ablation.
7. **Checkpoint/reference:** full state restore và prediction/telemetry parity; bank item SHA khác domain SHA đúng nghĩa; calibrator public payload reload được, model_id/checkpoint/vocab/reference đúng binding; graph-off checkpoint không giả A0 fitted. No optimizer trong calibration/prediction.

Mọi actual model/update/test budget phải được root cấp sau source review; draft không cấp4steps/60s hay bất kỳ quyền chạy nào. Source map đi kèm chỉ ghi nguồn đọc và các thay đổi **đề xuất**, không test result, adoption receipt hoặc artifact acceptance.

## 8. Quyết định root cần ghi nếu adopt

- Chọn hoặc bác recipe D1 fixed centered mean + alpha0 và gate4 zero-init như trên; nếu đổi capacity/features/initializers phải có version mới trước fits.
- Chấp thuận explicit graph/confidence freeze train80 qua neural refit90 và hạn chế inference tương ứng; không gọi đây là refit graph trên90%.
- Giữ A2 ablation-only/system rule21, cùng shared native initialization và response-loss recipe, không thêm regularization/tuning.
- Chỉ sau quyết định đó mới giao source scope research condition/adapter và shared-lifecycle routing; required baselines/36planned optimization phases của23 không bị rút bớt bởi draft tối thiểu này.
