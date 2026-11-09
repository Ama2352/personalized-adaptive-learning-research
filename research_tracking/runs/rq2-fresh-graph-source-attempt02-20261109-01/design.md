# RQ2 — thiết kế robustness với mười khối mới, chưa cấp dispatch

09/11/2026. Chuẩn bị source-only trước code/draw/outcome cho study mới. Không world/model/test/Python/Git hoặc thay canonical. Mục tiêu là fresh controlled join và độ bền của tương phản nguồn đồ thị, giữ một learned31 cố định. Không tạo thêm learned graphs hoặc gọi đây là hoàn tất RQ2.

## Câu hỏi và khóa thiết kế

Kết quả19worlds trước cho18Q khác0 với dấu phụ thuộc block,9K gồm cả âm/dương/0. Chúng ghép expert cũ theo SOURCE_RECONSTRUCTED_INITIAL_STATE với một sentinel. Study đề nghị chạy mới toàn bộ expert và learned trong cùng invocation, lưu đủ initial state của120arms. Không dùng old36 outcomes làm component và không cần sentinel lịch sử để admit scientific join mới. Old19 chỉ cung cấp motivation, source/runtime/graph provenance và dữ liệu đo chi phí.

Giữ S1P1L0, G_env=G_controller=expert31, cùng bank28concept/84items, chọn bài/predict/update native Paper2. Chỉ G_estimator đổi expert31/learned31. Learned31 từ TRAIN48/Method24 giữ nguyên typed artifact identity a51fbf935be3dda0ee2d89c2ebe61ce736a2c87d7fe604c126f79f77e73cbb7a, không dùng c_e làm weights hoặc P(edge true). Không solverfit/neuralfit mới. 14.400adaptive policy.update vẫn là thực thi mô hình online thực tế.

## Seed và private RNG

Primary ROOT đã chọn21010–21019, trước mọi draw. Đề nghị21003–21012 đã bị thay vì21003–21009 tái dùng bảy CPU09 seed blocks. Không giữ đề nghị đó như primary được cấp quyền.

`run_approved_cpu_pilots.py:47,63–66` dùng21000–21009, còn controlled36 worker973a lines94–112 dùng21000–21002. Raw audit02 dùng rg --hidden --no-ignore trên py/md/json/jsonl, kể cả artifacts bị gitignore. Có59hit lines, gồm source/copies range(21000,21010), PID21016, kích thước21014 và log-likelihood BKT, không thấy record scientific execution gán21010–21019. Một access error ở .pytest_cache được giữ nguyên, rg exit2. Audit không đọc protected dataset/Holdout, dependency trees hoặc giải nén binary caches. Bởi vậy đây là audit nguồn/metadata scientific đã lưu, không khẳng định mọi byte không truy cập đều đã kiểm. ROOT cần chấp nhận phạm vi này trước freeze packet; nếu thấy prior execution thì STOP trước draw và chốt một danh sách mới, tuyệt đối không đổi seed sau xem outcome.

Nguồn notebook pin353f487... cell persona_base_abilities và loader a12edc... xác định private `np.random.default_rng(20260721 + block*101 + 1*10007)` cho PY (PERSONAS=(PG,PY,PYH)). Gọi đúng public native persona function10lần trong ENV expert namespace, không learned namespace. Hàm dùng normal global/chapter/node, propagation qua expert parents và clip850..1500 như nguồn. Không viết lại generator.

Reuse controlled36 initializer nguyên thứ tự nodes và arithmetic. Trừ mean của28anchor, chia max(1,max(abs(centered))), nhân60. Ba base là1000/1150/1300 cộng cùng residual, không clip thêm. Residualmean gần0 theo bound1e-10, absolute≤60. Mỗi block dùng private `default_rng(block).random((120,2))`, dtype native float64/C order, không global np.random. Lưu anchor, centered/residual, scale, all3bases, U và raw-byte/semantic SHAs trước world đầu tiên. Không gọi profile labels là latent ability factor, vì ba scalar levels là thiết kế khác CPU09 personas.

Hai private generators mỗi block xác định deterministic streams khác seed công thức, không chứng minh Monte Carlo independence bằng SHA hoặc seed khác. Mười block mới đối với scientific seed records đã audit, không mười independent graphs/datasets/human learners. Graph có training lineage riêng, không suy unseen-world thành dataset generalization. RNG state global trước/sau preparation và initializer source/runtime được kiểm, không đổi RNG scheme để tìm effect.

## Workledger chính xác

Tổng10blocks×3abilities×2graphsources×2λ=120worlds, mỗi120responses. File JSON đi kèm khóa toàn bộ cell IDs/order và totals trước code. Chạy high1300 trước40worlds (10×2sources×2λ), kiểm20source-specific high negative-control pairs, rồi80worlds ability1000/1150. Không loại block hoặc arm sau outcome. Failure của high control làm STOP, giữ partial không retry.

120fresh environment constructors và120policy factories,120initial snapshots,120final snapshots. Select/predict/interact/update và hai oracle probes mỗi loại14.400started/returned tối đa, durable reservation120 trước mỗi arm. Anchor_generation10, uniform_array_generation10. Shared values gồm280anchorconcepts,840baseconcepts và2.400uniformvalues. Nested policy constructors do factory phải khai phạm vi riêng, không gọi120 là mọi nested constructor.

Mỗi initial snapshot lưu full environment và nonedge policy state cùng byte/semantic hashes. Cùng block/ability/λ, hai grapharms phải có environment snapshot hash bằng nhau và policy NONEDGE hash bằng nhau. Treatment binding khác graph đúng chủ đích, không yêu cầu full graph fingerprint giống nhau. Cácλtrong mỗi source cũng có fresh initial states bằng nhau trước interact; λlà class treatment binding riêng. Snapshot completion+hash trước response1, không chỉ assertion constructor. Hardkill actualcounts UNKNOWN≤reserved; không biến thiếu child receipt thành0.

Clock giống worker cũ. Timestamp bắt đầu2026-01-01UTC, trước mỗiquery cộng6h, riêng step>0 chia hết28 cộng72h thay6h, endpointT41days. Select→predict→oracle evaluator probe→world.interact(U[step])→policy.update(y,p). Oracle fields chỉ vào evaluator/oracle output, không chọn bài/estimator/confidence. Source unchanged guards cho pathways/mechanism adapters và notebook definition hashes. Sau divergence, cùng ordinal không còn cùng item/history, không paired LL hoặc matched-query P claim.

## Phép đọc kết quả khóa trước

Y_b(a,g,λ) là mean28 final-minus-base latent theta tại endpoint, không gross gain/mastery rate. Q_b(a,λ)=Y_expert−Y_learned gồm60components; K_b(a)=Q_b(a,.55)−Q_b(a,0) gồm30contrasts. Giữ120outcomes/60Q/30K và zero/negative trong output. Bảng mặc định đầy đủ10blocks×3ability, mỗi hàngQ0,Q.55,K; summary theoability/λ giữ min/max/mean và số dấu như mô tả, không thay bảng gốc.

Kiểm20highpairs (mỗi block và source) semantic full120rows/endpoints exact giữaλ0/.55, deficit/violation đều0 do a1300+residual≥1240>1150. K1300phải0, nhưng Q1300 có thể khác0. Không ép sign K1150 hay tái hiện old signs làm acceptance threshold. Trajectory table cho60expert/learnedpairs có qdiffcount/120, fraction/first difference và prefixlabel equality; không kết luận mediator hoặc outcome benefit chỉ từ divergence.

Toàn bộ mười seed clusters là unit mô tả, không nhân profile/λ/steps thành independentN. Không signflip/permutation/p-value/CI hoặc cơ học DiD. Muốn inference sau này phải đề xuất riêng distribution/coupling/exchangeability, multiplicity và rule trước phân tích; không tự thêm sau nhìn signs. Không causal human ability law, graph truth recovery, quality ranking chung hoặc independent learned-graph replication. Có thể đối chiếu ba oldblocks riêng như historical comparison, không gộp thànhN13 để che nguồn/thiết kế.

## Tài nguyên và output đề nghị đã được ROOT sửa trước code

Actual19 outerstored33.8517495s, worker32.6774392s. Resource stages cho pre-first-world12.1224072s, after-last-world32.5211718s; worldphase19=20.3987646s. Linear extrapolation đơn giản cho120worlds là128.8343s +prelude≈140.9567s trước finalization, không measured benchmark hay cam kết hoàn tất. Vì vậy150whole/130worker ban đầu được thay, không giữ như cap đủ.

Planning allocation hiện tại whole240s, worker210s, owned≤235s gồm cleanup5s, outerfinalreserve≥5s, familyRSS512MiB/free1536MiB, prelaunchavailable≥2GiB. Timer/deadline từ invocation, finalpostpublication verdict, no autoreset/retry/extension. Không chi cloud. Actual19 peakfamily117.989.376B/minfree2.132.578.304B chỉ là dữ liệu đã đo, không bảo đảm120worlds. Streaming traces, không giữ toàn bộ row lists; state/control pair hashes nhỏ được lưu để đối chiếu.

Actual19 kích thước oracle1.199.527B, observable583.554B, endpoints139.712B, initial-L01 18.267B. Nhân120/19 chỉ là tham chiếu khoảng7,58MB/3,69MB/0,88MB traces. Không reuse oracle leaf4MiB của19. Đề nghị oracle12MiB, observable6MiB, endpoints2MiB, mỗiinitial32KiB (120×32KiB=3,75MiB), sharedinputs256KiB, mỗismallmetadata≤1MiB, riêng worker_run≤2MiB, toàn scientificoutput32MiB và≤160flatfiles. Mọi append/write kiểm cả leaf và total trước ghi; cap không là permission tăng row population. Worker monitor cadence giữ.1s. Old19 cap2000samples không đủ cho210s+120cell progress guards, nên proposal mới5000samples/worker_run2MiB trước code, có bound fixed guard callsites cộng≤2100periodic samples và phải chứng minh tổng<5000 từ final source. Không giảm cadence/RAMcheck để né cap. Resource rows embed trong scientific worker_run vẫn tính trong32MiB; outer logs/journal riêng phải có finite cap.

Scientific output mới riêng `experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-01/`. Worker/controller/plan ởP, bundle nhỏ sau nghiệm thu riêng `research_tracking/runs/rq2-fresh-graph-source-robustness-20261109-01`. Không overwrite old36/19, corpus/runtime/dependencies hoặc artifacts của mô hình khác. Source/input pre/post phải exact, no historical mutation. File120initial và traces lớn giữ output, bundle chỉ refs SHA/size cùng summary/log/receipts/source.

## Ba phần implementation sau ROOT review

1. Derivative worker từ accepted learned19 c1f1..., giữ fingerprint/scoring/draw/clock/native APIs; đổi block initializer thành public native calls và120cell join mới, không oldoutcome/sentinel authority. Pin learned artifact one typed load và source/runtime trước world.
2. Finite outer/packet mới, bound genuine helper0dc, read/write allowlists, family monitor, exact call/output/Q/K/high-control/initialpair checks và Job0. Output cap32MiB/160files phải đồng nhất mọi layer. Không global profiler.
3. Meaningful small synthetic checks chỉ cho120key ledger, initializer formula/source body equivalence, wronginitial/treatment split, Q/K joins/zero controls, caps/failureUNKNOWN. Không tự chạy thêm19worlds hoặc hidden preliminary native pass để kiểm code. ROOT review exact source/test allowance trước execution.

Nguồn quyền là user general safe/cost-saving local Development scope và ROOT quyết định finite batch, không paid/fullCV grant. Tài liệu này không là runtime permission hoặc actual allocation receipt. Cần ROOT review source/actualRAM/pins/caps/owned admission rồi một dispatch riêng. Oldbudget33.8517495/60 giữ lịch sử, không reset thành0; new240 là allocation khác có ledger riêng, cumulative ceiling protective300s nếu tính cả old60, actualold+new được báo riêng. No automatic human-permission question cho source prep trong scope đã giao.

## Nguồn khóa

| Nguồn | SHA-256 |
|---|---|
| Old controlled worker |973a1973da7982aac9a44b4112786915a127447ac57c6bce07f51c06e381f119|
| CPU09 runner |55e8e3c74c8daa92d572c809353da5546fa435b55e18b8ab30fdcf46e8413e8e|
| Paper2 native loader |a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1|
| Pathways adapter |33ad34140f7b08eb22f86e6cc3caf7b0e7c98f09e4fd74945a6f7e9718b07560|
| Mechanism adapter |0cbfaf1b4735c188e04ed822197121118dcb65849b582af7413e157fd8d847fa|
| Notebook |353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f|
| Accepted learned19 bundle manifest |6d848a6bd8bbb4b26abd3f3caef4a8de2a1b80c9176cbaa4c3a8bce5164bf5a5|
| Raw audit02 |c7001c9f2db6ce9a46b6f019c163341a98b7e359c438e5cf9e55f0c9ea47ea87|

Line refs áp dụng exact sources, notebook function được loader lưu cell/AST hash. Các approved36/19 historical receipts không được sửa. Không có outcome của mười khối mới trong design này.