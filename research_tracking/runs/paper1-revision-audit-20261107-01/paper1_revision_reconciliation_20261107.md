# Đối chiếu revision Paper1 với PDF — 07/11/2026

## Kết luận và ranh giới tái lập

**Chưa tìm được exact source revision tạo kết quả của PDF Paper1 trong phạm vi local đã kiểm.** Không chỉ thiếu seed manifest: notebook `Enhanced` đang có khác PDF về controller, mô hình sinh đáp án, latent learning, orchestration và metrics. Notebook này không đủ để tái lập Table I/Fig. 2–3 rồi gọi là reproduction của bài báo.

Phạm vi tìm kiếm đã thu hẹp: Git all refs và reflog chỉ có một blob notebook Paper1; bản trích source lịch sử có cùng AST; chín bản notebook trong source kits v4–v12 có cùng toàn bộ ordered source cells. Bốn notebooks trong archive Paper2 là nguồn khác, không bổ sung revision Paper1 còn thiếu. Chưa thấy bundle Paper1 gồm source + inputs + seed list + per-seed outputs liên kết PDF. Kết quả này **không chứng minh** bản đúng không tồn tại ở máy tác giả, Drive, thư mục ngoài repository hoặc Git object không reachable/reflog.

Q01 được thu hẹp thành yêu cầu artifact cụ thể ở cuối tài liệu; chưa đóng câu hỏi toàn cục. S01 vẫn cần tác giả/advisor xác nhận revision tương ứng bản submitted hoặc quyết định cách trình bày phần không tái lập được. Audit không tự thông qua S01 hoặc thay RQ/required baselines của KLTN. Ba RQ trong Paper1 là câu hỏi của manuscript lịch sử, không thay ba RQ hiện hành của KLTN.

## Phạm vi và kiểm chứng

Chỉ inventory, đọc source/PDF/metadata và Git read-only; không thực thi notebook, simulator, model, benchmark, GPU/cloud, realdata query, raw learner predictions hoặc Holdout/Test. Không fetch/checkout/reset/commit và không chỉnh source, archives, bundles, shared indexes/state/tasks. Notebook embedded outputs không được dùng làm kết quả tái lập.

[JSON audit](paper1_revision_reconciliation_20261107.json) lưu 33 input files với SHA-256, archive members được đọc, cell/definition hashes, Git blob identities, page checks và preview inventory. Snapshot Git tại lượt lập JSON: `e7dcf6b63a92bb532663eec40948b835f5b7155f`. Source/PDF được preserve vào Git tại commit `06f6199c1d0b4e8772ec370b1531eb1bb4c75ef6`, ngày 07/11/2026; thời điểm preserve không phải ngày chạy thí nghiệm hay chứng nhận submission.

PDF được extract trực tiếp cả năm trang bằng project `.venv` với `pypdf` bundled đã có sẵn, không cài dependency. Nội dung sau chuẩn hóa whitespace khớp bản trích lịch sử ở cả 5/5 trang. Đã render và xem đầy đủ trang 2–4 để kiểm equations, Algorithm 1 và Table I. Preview PNG nằm ngoài repository, có đường dẫn/hash trong JSON và được giữ để review. Metadata PDF hoặc tên file “RIVF_2026” không thay xác nhận submitted version.

| Định danh | Đường dẫn | SHA-256 |
|---|---|---|
| P1-PDF | `paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf` | `984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4` |
| P1-NB | `paper1/AdaptiveEngineSimulation_Enhanced.ipynb` | `6941e0d103cb5fddb5fbc572dc01f2fa870531dbde4b4612ada6a225c8e4479d` |
| P1-SOURCE-FINGERPRINT | Ordered `{cell_type, source}` của cả 34 cells, bỏ outputs/execution/metadata | `7d881f2b21be1ea6acd8bf6b174579b9a3ce6d8c2fd62dca893718adedd05e5b` |
| P1-SELECTOR | `select_adaptive_question`, cell 11, lines 1–100 trong cell | `9cede51557101cbeecf263d92356a4b9681e4215f048414f64a8b21d6e9e8fc5` |
| P1-RUNNER | `run_adaptive_simulation`, cell 13, lines 1–117 trong cell | `ddf2e710c8f6d85fc7635141fac728629fe8abd2be5c145ed8045a7f59bf9ebc` |

Cell indices trong báo cáo/JSON là **zero-based**, theo notebook gốc và hồ sơ audit hiện có. Definition hash là SHA-256 của UTF-8 `ast.get_source_segment`; cell hash là SHA-256 của toàn `join(source)`, vì vậy hai loại không cùng giá trị. Cell 11 hash là `1b91ed58a6a66d5791e2fc99fe30536185cc5c0d597f7317686659b0396c8384`; cell 13 hash là `e7187bd6ff28e51f629d9de6ce5faae73ac4c8f8d5bed376e91fc1d3757126d5`.

## Các candidate thực sự tìm thấy

| Candidate / nơi tìm | Đối chiếu thực hiện | Kết quả về provenance |
|---|---|---|
| `paper1/` hiện tại | Inventory kể cả hidden: đúng PDF và Enhanced notebook; notebook 34 cells, 18 code cells. | Một source candidate. Không có năm CSV relative inputs hoặc `sensitivity_summary.csv` ngay trong `paper1/`. Sự vắng mặt ở đây không phủ định việc tác giả từng chạy từ working directory khác. |
| Git history của P1-NB/P1-PDF | `git log --all --follow`; `git rev-list --all --reflog --objects` và `git cat-file blob` cho đúng paths. Local branch `main`, không tag; không thấy remote-tracking branch khác trong inventory. | Notebook chỉ blob `30cc2a3824a767f83dbe2d6f0f348f9a0c6db2d6`, PDF chỉ blob `7d1ed2ea76c6c20d10751986052ff5b4d481468e`; bytes/SHA khớp workspace. Không tìm được prior code revision từ refs/reflog đã có. |
| `docs/thesis_recovery/evidence/paper1_source.py.txt` | Parse toàn bộ source đã trích; AST bằng toàn bộ code cells hiện tại. Git blobs `20dfbd…` và `2b035b…` có cùng LF-normalized SHA `e12816a535d60970d0d4877f32faa365363a78e936b0b189f4504bc0678d0e6d`. | Hai byte variants chỉ khác CRLF/LF, không phải hai thuật toán hoặc candidate revision độc lập. Commit `8fd0275b73416b4e17e30a644878424e5c200afc` bảo toàn evidence bytes; bản trước có tại `b3c592a06029670231c6ac1f5838e0b099a0b8d1`. |
| `docs/thesis_recovery/evidence/paper1.txt` và `source_inventory.json` | Extract PDF lại, 5/5 page-text matches sau whitespace normalization; source/PDF hashes trùng inventory cũ. Hai Git blobs của text cũng chỉ khác newline. | Là bản trích của cùng nguồn đang có, không cung cấp source tạo Table I/Fig. 3. |
| 14 ZIP trong `artifacts/akt/colab/` | Đọc directory và chỉ member Paper1 source. Chín source kits v4–v12 chứa `paper1/AdaptiveEngineSimulation_Enhanced.ipynb`; ba kit đầu và hai failure ZIP không có candidate này. | Cả chín copies có source fingerprint P1-SOURCE-FINGERPRINT. Raw member SHA đều `acd43d4bf9a2cff3024e1832980734794e66f9f2ba779e1747b79289fea667ba` vì đã strip outputs/metadata. Đây là copies đóng gói, không là revision lịch sử mới. |
| Hai failure ZIP trong `research_tracking/runs/colab-mcp-preflight-20261107-01/` | Directory inventories 14 và 7 members; không có tên Paper1/AdaptiveEngine hoặc nested ZIP. | Không có source candidate mới theo archive member names; không mở các logs/results của failure archives để tìm kết quả khoa học. |
| `paper2/rivf2026_gam_kt_artifact_v20.zip` | 89 archive members; đọc source cells của bốn notebooks và targeted metadata/builders, không đọc frozen Junyi/simulation result payloads. | Ba simulator notebooks và một Junyi notebook; không định nghĩa `select_adaptive_question`/`run_adaptive_simulation` của P1. Các source có latent dynamics/selector khác PDF Paper1; không được dùng thế chỗ và gọi exact reproduction. |
| `ref-papers/`, `docs/`, `_context/`, `.superpowers/`, selected repository paths | Inventory filenames và targeted searches tên Paper1/AdaptiveEngine/graph-policy/archives. `ref-papers` là tài liệu KT; đề cương tìm thấy ở `paper2/DC KLTN0127 23520355&23521338_LeVanTuan.pdf` theo source inventory. | Không có candidate Paper1 khác trong các kết quả đã thấy. Đề cương/KT references không chứng nhận source Paper1 hoặc cho phép thay RQ KLTN. |

Danh sách kits/members/hash chính xác nằm trong JSON. Không truy cập raw data trong các archive chỉ vì container nằm trong phạm vi tìm kiếm. Discovery có một lỗi Access denied tại `.pytest_cache`; không đọc nội dung, không đổi ACL hoặc retry. Không scan các vùng dataset, protected BKT artifacts, environments/WSL hoặc các dữ liệu bị cấm. Không tìm ngoài repository, không mở Drive và không quét toàn bộ unreachable Git objects.

### Các notebooks trong archive Paper2 không phải bản Paper1 còn thiếu

Đường dẫn dưới đây nằm trong `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/source/`; archive member tương ứng bỏ một lớp wrapper. Raw bytes của bốn candidates đã được hash riêng.

| Candidate | SHA-256 | Khác biệt liên quan |
|---|---|---|
| `adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb` | `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f` | Cell 9 `LatentStudentEnvironment` có decay quanh base, learning gain phụ thuộc challenge/spacing/prerequisite/stochastic factor, cap 1600; cell 11 selector ưu tiên coverage/anti-drill rồi chapter tie, khác +12/cap1500 và hard current-chapter filter của P1-PDF. |
| `…v2_1_library_snapshot.ipynb` | `0339a01191f8a9b94a8a93d95b80aaed572b6a64ed736dcc1f02785ba96aa2ba` | Cùng họ environment/selector Paper2, không có source link tới submitted Paper1. |
| `adaptive_lms_vs_graph_gam_kt_research_ready_v2.ipynb` | `ed95979cececaab609c94344b490770bdcfd613384f0c65efaac042920839407` | Cùng họ source Paper2; có separate latent state nhưng không đủ để coi là model trong PDF Paper1. |
| `junyi_cycle_corrected_ablation_confirmation.ipynb` | `26270cc8e2c057d9c15b7070cc01304b2646b9575e632eaee8b5eeb3de357f3c` | Junyi offline/graph processing; không có controller/runner Paper1. Chỉ source được inspect, không kết quả/holdout của notebook. |

Năm simulator CSV names trong P1-NB cũng tồn tại như file names trong Paper2 artifact. Trùng tên/counts hoặc quan hệ chuyên môn không chứng minh chính các bytes đó đã được dùng để tạo bảng Paper1. Không copy, relink hoặc sửa working-directory assumption trong lượt này.

## PDF claims/equations so với Enhanced notebook

Các hàng “mismatch trực tiếp” so sánh semantics **hai tệp đang có**; không kết luận manuscript sai hoặc không từng có implementation đúng. Hàng “thiếu provenance” chỉ ra phần chưa chứng minh được. Không lấy khả năng code gây khác biệt để khẳng định một actual historical trajectory chắc chắn đã khác khi chưa có inputs/run logs.

| Nội dung | P1-PDF: page/section/equation | P1-NB: exact cell/definition | Kết quả đối chiếu và giới hạn |
|---|---|---|---|
| Graph domain | Trang 2, III.B, Eq. (1)–(2): chung V gồm 28 concepts; B1 25 intra, GA 28 intra + 3 cross; cả hai DAG. | Cell 3 đọc `nodes.csv` và hai edge CSV; cell 5 `build_graph_from_edges` chỉ `add_edge`. | **Thiếu provenance inputs.** Code không explicit `add_nodes_from(V)` nên không bảo toàn isolated concepts nếu input có; chưa chứng minh actual mất node trong run Paper1. Không có CSV gốc của Paper1 ở folder này để khẳng định counts/ordering. |
| Ready-set formula | Trang 2, Eq. (3): unmastered concepts có mọi predecessors mastered. | Cell 11 `select_adaptive_question`, phần `READY NODES`. | **Khớp có điều kiện** ở nhánh ready thông thường nếu node universe/threshold/input columns đúng. Không có evidence về actual inputs của submitted run. |
| Khi không có ready concept | Trang 3, Algorithm 1, lines 3–5: ready rỗng thì dừng. | Cell 11: nếu ready rỗng nhưng còn unmastered, gán toàn bộ unmastered làm ready; runner cell 13 chỉ dừng khi selector trả `None`. | **Mismatch trực tiếp.** Notebook có escape hatch không giữ prerequisite feasibility ở trường hợp này; PDF algorithm dừng. Chưa kiểm actual frequency nhánh fallback trong các runs lịch sử. |
| Chapter continuity | Trang 3, III.D, Eq. (8)–(9), Algorithm 1 lines 7–11/19: giữ current chapter nếu nó còn ready concepts, sau đó lowest Elo. | Cell 11 signature không nhận previous/current chapter; `lowest_elo` lấy min toàn ready set. Cell 13 `prev_chapter` chỉ dùng log switch, không truyền selector. | **Mismatch trực tiếp.** Không có hard current-chapter candidate filter theo PDF. `cross_chapter_unlock` là ưu tiên newly unlocked cross-edge concepts, không phải continuity filter. |
| Elo probability và update | Trang 2, Eq. (5)–(6): logistic với thang 400; θ cộng K(S−P), concepts khác và difficulty giữ nguyên. | Cell 13 `expected_p`, `correct`, `s_elo_after`. | **Khớp estimator equations.** Khớp update không bảo đảm khớp process sinh S; xem latent row dưới. |
| Dynamic K | Trang 3, Eq. (7): 40 trước 5 exposures, 24 trước 15, sau đó 16. | Cell 7 `get_k_factor`, cell 13 đếm concept exposures. | **Khớp khi `k_mode="dynamic"`.** Source cũng có constant-K nhánh sensitivity; cần frozen configuration để biết nhánh nào tạo paper outputs. |
| Mastery threshold/budget | Trang 3, III.C/IV.A: τ1250, dynamic K, 500 interactions. | Selector/runner default τ1300; cell 19 grid có 1250/1300/1350 và constant/dynamic K; cell 15 default 500. | **Configurable difference, chưa là contradiction tự thân.** τ1250 và 500 có thể được chọn từ code; không có run manifest Paper1 chứng minh exact setting used. |
| Latent persona và estimator initialization | Trang 3, IV.A: US latent N(1400,50²), UW N(1050,50²), FW N(1000,50²) ở functions/N(1250,50²) nơi khác; observable Elo1200, FW functions1050. | Cell 3: strong1200 mọi concept; weak800 mọi concept; function-weak800 mọi concept. Cell 13 dùng chính observable Elo để sinh response. | **Mismatch trực tiếp.** Function-weak source initialization không phân biệt functions; không có separate latent realization Gaussian như PDF trong 34 source cells. |
| Response/learning dynamics | Trang 3, IV.A: response probability từ latent ability; latent tăng12 sau feedback, cap1500. | Cell 13: `correct ~ Bernoulli(expected_p)` từ estimator hiện tại; chỉ Elo estimator được cập nhật. | **Mismatch trực tiếp.** Không có latent +12/cap1500 process. Suy luận từ code: với history trước response, E[ΔElo]=K(E[S]−P)=0; mastery crossings có thể là stochastic drift. Điều này nói về current notebook, không bác bỏ latent-learning simulations được PDF mô tả. |
| Item selection và tie | Trang 2, Eq. (4): closest difficulty; ties theo prior exposure count và item ID. | Cell 11: `.abs()` rồi `.idxmin()`; không truyền/lưu item exposure counts trong selector. | Closest-difficulty **khớp**; tie handling **khác trực tiếp** khi có tie: current code lấy first minimum theo DataFrame row/index order, không explicit exposure/ID rule. Không tự suy actual tied event đã xảy ra. |
| Concept tie | Trang 3, III.D: fixed graph traversal order. | Cell 11: `min(ready_nodes, key=Elo)` trên graph node iteration order. | **Có thể tương thích nếu ordering inputs frozen**, chưa có input/node-order manifest để xác nhận. Không đánh đồng thiếu sorted call với demonstrated nondeterminism. |
| Seeds và design | Trang 3, IV.A: 50 seeds/persona–model; structural B0/B1/GA tạo450 runs; sau đó GA policy ablation. | Cell 13: `np.random.seed((int(time.time()) + hash(student_id)) % 2**32)`; cells 15/19 lặp students và sensitivity grid hai graph engines, hai strategies. | **Mismatch orchestration trực tiếp + thiếu execution provenance.** Không có explicit 50-seed list/argument hoặc B0 lexicographic topological runner trong notebook. Wall clock và process hash không là frozen reproducibility seed manifest. |
| Outcomes/table generation | Trang 3–4: chapter switches, re-entry, mastery rate; Table I mean±SD trên50 seeds, Fig. 3 policy re-entry. | Cell 17 `summarize_experiment`: total_questions, chapter_switches, avg_ready_size; cells 23–33 plots chủ yếu switches/ready size. | **Không có code tạo re-entry/mastery-rate bảng trong source đang có.** Không thấy `visited_chapters`/re-entry counter hoặc multi-seed aggregation. Một notebook output/plot sẵn có không thay source+run linkage. |
| Zero re-entry | Trang 3, IV.C; trang4 Table I/discussion: continuity zero trong **tested runs**, non-continuity means16,70–19,36. | Selector source hiện có và [counterexample đã lưu](../runs/cpu-rq12-20261107-03/paper1_counterexample.json) cell11 hash P1-SELECTOR. | Source fixture cho A→B→A ở hai strategies với scripted mastery; **không là contradiction của finite tested-run claim hoặc exact PDF controller**. Không nâng zero observed thành theorem cho mọi DAG. |

## Điều gì đã được chứng minh, điều gì vẫn thiếu?

**Đã chứng minh bằng local static evidence:** current source không triển khai hard chapter filter, separate latent +12/cap1500 hoặc 50-seed/B0/re-entry pipeline theo PDF; source history/copies đã tìm không cung cấp implementation khác. Có một số estimator formulas/settings tương thích, nhưng không cứu được toàn bộ experimental-design mismatch.

**Chưa chứng minh:** PDF claims được sinh từ notebook hiện tại; numerical Table I/Fig. 3 có lỗi; exact submitted source không còn tồn tại; Paper2 inputs đã được dùng cho Paper1; teacher review hoặc metadata date ràng buộc đúng artifact bytes. Không tái dựng source từ paper rồi gắn nó vào lịch sử.

Counterexample `cpu-rq12-20261107-03/paper1_counterexample.json` có SHA khớp manifest và function hash khớp current selector. Nó xác nhận provenance của fixture hiện có; không thực thi lại. Mastery được scripted và graph synthetic, nên dùng để giới hạn universal inference từ current source. Ngay Eq. (8)–(9) của PDF cũng là current-chapter preference, không có closed-chapter ban được mô tả; muốn nói invariant toàn DAG cần proof/assumptions riêng, không suy từ zero re-entry trên tested concept graph.

## Gói artifact tối thiểu để xử lý Q01/S01

Owner theo [sổ quyết định](../../docs/thesis_recovery/09_DECISION_REGISTER.md): Dương tìm nguồn; tác giả/advisor xác nhận S01. Không cần dữ liệu người học thật cho việc này; Paper1 là synthetic study. Không yêu cầu credentials hoặc raw Junyi/Holdout.

| Thành phần cần tác giả/user cung cấp | Acceptance để nhận diện đúng revision |
|---|---|
| Source đúng bản PDF | Notebook/scripts nguyên gốc cùng auxiliary modules, immutable commit/archive hoặc SHA; xác nhận bằng văn bản nó tạo bản PDF SHA P1-PDF hoặc chỉ rõ PDF revision khác. Cần code continuity filter, latent personas/+12/cap1500, B0 và policy ablation; không chỉ bản sửa hôm nay. |
| Exact synthetic inputs/config | `nodes.csv`, `edges.csv`, `edges_baseline.csv`, `question_bank.csv`, `concept_to_chapter_map.csv`; SHA, node/edge/item ordering, chapter labels, working directory và τ/K/budget. Counts đúng chỉ là check sơ bộ, không thay identity. |
| Seeds và RNG recipe | 50 actual seeds cho mỗi comparison, RNG/library versions, cách pairing persona/conditions, latent initial realizations hoặc recipe deterministic để tái dựng, response/learning random channels nếu có. Giải thích rõ mọi reuse của seeds/GA continuity runs giữa structural/policy analyses. |
| Per-seed aggregate outputs và code tạo bảng/hình | Records đủ structural450 runs và policy-ablation per-seed records theo design thực tế, chứa switches/re-entry/mastery/horizon; Table I/Fig. 2–3 derivation, hashes/config/source linkage và logs. Không chỉ screenshot hoặc con số mean đã làm tròn. Không tự yêu cầu tổng số runs ngoài design chưa xác minh. |
| Runtime/provenance note | Exact command, dependencies/version, execution time/context nếu còn, policy tie rules, stopping/mastery semantics, known deviations; chữ xác nhận chủ sở hữu artifact và revision submitted. Timestamp filesystem/PDF/Git preserve không đủ độc lập. |

Nếu chỉ khôi phục được source nhưng thiếu run outputs/seed identity, có thể kiểm implementation fidelity, chưa gọi exact numerical reproduction. Nếu chỉ có outputs mà không source/input linkage, có thể trích “manuscript-reported results” kèm giới hạn, chưa coi là repo-verified result.

Nếu tác giả xác nhận source đúng không còn: S01 cần ghi nhận rõ phần Paper1 không independently reproduced, cho phép dùng nó làm historical motivation với uncertainty hoặc dựng **implementation mới, version mới** từ mô tả. Implementation mới là reconstruction/diagnostic, không gọi original source recovered. Không đề xuất tự thay đổi hoặc bỏ ba RQ, required comparator set, graph-learned/noise conditions của KLTN.

## Bàn giao cho nghiên cứu tiếp theo

- Giữ nguyên Paper1 source/PDF và counterexample historical. Không sửa controller/latent initializer trong notebook để “cho khớp” rồi reuse old identity.
- Dùng discrepancy table này làm E01/source reconciliation boundary: local search đã có kết quả âm trong phạm vi cụ thể, exact reproduction vẫn thiếu provenance. Parent có thể cập nhật Q01/T01/CPU08 sau review; tài liệu này không sửa trạng thái hộ.
- Reuse Paper2 source đúng provenance cho diagnostics riêng và giữ environment identity độc lập. Separate latent state trong Paper2 không làm nó thành implementation Paper1.
- Mọi new-variant controller/learning sensitivity cần tên/assumptions/protocol riêng; không lấy zero-reentry counterexample hoặc mismatch hiện tại làm bằng chứng graph harm/benefit.

## Kiểm đã chạy và giới hạn discovery

Kiểm thành công: PDF SHA trùng source inventory; text5/5 trang khớp stored sau whitespace normalization; visual pages2–4; notebook 18 code cells parse được AST; historical extract AST bằng current; duy nhất một Git notebook blob trong all refs/reflog; chín portable copies bằng ordered-source fingerprint; saved counterexample output SHA khớp manifest. Không behavioral tests/model runs vì lượt này chỉ thêm audit và không execution source.

Danh sách tệp/archives đọc và members chọn có trong `input_inventory`, `paper2_archive`, `portable_kits` của JSON. Các kết quả inventory/từ khóa ngoài các inputs đó chỉ dùng discovery, không làm căn cứ numerical research claim. Full parent `research_tracking/`/`docs/` có thay đổi song song, nên SHA của shared docs là snapshot lúc audit, không là cam kết chúng giữ nguyên sau tích hợp. Giữ hai outputs audit riêng để parent review/index/archive/commit.
