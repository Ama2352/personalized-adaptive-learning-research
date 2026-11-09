# RQ2 — đề xuất chẩn đoán mechanism từ cache CPU09

09/11/2026. Bản chuẩn bị trước phân tích, sau khi Root chọn ưu tiên dữ liệu đã lưu. Task hiện tại chỉ đọc source/metadata và một record đầu của gzip để kiểm schema. Chưa tính kết quả mới, CI, p-value hoặc tạo worker/phép chạy. Các nguồn và SHA nằm cuối note.

## 1. Hai thí nghiệm cần giữ riêng

| Thuộc tính | CPU09 ngày 07/11 | Controlled ability ngày 08/11 |
|---|---|---|
| Seed families | 21000–21009, đủ 10 | 21000–21002, ba seed tái sử dụng |
| Initial ability | Persona PG/PY/PYH, mỗi persona có latent vector/residual khác | Một PY anchor mỗi seed, residual centered/bounded60 dùng chung, scalar a1000/1150/1300 |
| Estimator intervention | S/P cùng bật hoặc cùng tắt, L tắt cả hai, source graph đầy đủ giữ nguyên | Cùng S/P bật và L tắt, thay estimator edges full/empty |
| World mechanism | λ0 hoặc .55 | λ0 hoặc .55 |
| World/controller graph | Cùng historical graph | Cùng historical graph |
| Population đã chạy | 120 worlds, 14.400 interactions, 30 four-cell contrasts | 36 worlds, 4.320 interactions, 9 Ψ và 6 adjacent Ω |
| Outcome | Mean28 final theta minus own base tại cuối lịch120steps | Cùng đơn vị Elo net, explicit T41ngày |
| Đơn vị ghép | 10 seed clusters với ba persona lặp bên trong seed | Ba seed clusters với ba scalar abilities lặp bên trong seed |

CPU09 là contrast bật/tắt **hai parent pathways cùng nhau**. Nó khác full-package111−000 vì L đã tắt cả hai, và khác thao tác thay tập cạnh của thí nghiệm ngày08. Flag `graph_on` trong cache CPU09 phải được giữ đúng operational definition này.

Protocol `CPU09_CPU10_PROTOCOL_DRAFT.md` dòng3–5/25 và README/manifest closed run ghi user chấp thuận pilot10seeds/profile×120steps×4cells. Manifest `cpu-factorial-20261107-01` có status completed, max14.400events/120s, elapsed62.049792100006016s. Đây là hồ sơ của allocation đã thực hiện.

Controlled run có approval_reference `root-reviewed-finite-ability36-cells-4320-interacts-60s-20261108`, plan fce299…5c72 và actual counts4320 trong native__run.json. Receipt outer lưu12.361254453659058s, report ghi worker11.757589600s và max RSS94.793.728B/minfree3.038.347.264B. Root tool observation ghi whole tool outer wall chưa được lưu. Các đo này cho thấy diagnostic nhỏ có thể chạy nhanh trong điều kiện cũ, chưa đảm bảo thời gian/RAM hiện tại hoặc tự cho phép một lượt mở rộng180s.

### Quyết định về đề xuất thêm bảy block

Về thiết kế, có thể giữ nguyên ba controlled blocks cũ và tạo riêng bảy blocks21003–21009 theo recipe centered-residual/full–empty ngày08, rồi tổng hợp mười controlled seed clusters nếu source/RNG/profile/clock thật sự khớp. Tuy nhiên cả mười seed families đã được dùng trong CPU09. Cách ghi đúng sẽ là “bảy controlled-ability blocks bổ sung, mười seed clusters tổng”, với số seed families chưa từng xem vẫn bằng0. Các endpoints PG/PY/PYH cũ không được ghép vào endpoints A1000/A1150/A1300.

Root đã chọn ưu tiên cache-only. Note này giữ phương án thêm bảy ở trạng thái đề xuất chưa phân bổ, không dùng lại approval CPU09 hoặc allocation36worlds. Nếu cần triển khai sau, phải có packet riêng cho84worlds/10.080interactions cùng exact source/call/resource caps trước dispatch.

## 2. Câu hỏi mới nhỏ nhất trả lời được từ CPU09

Các báo cáo hiện có đã tính Ψ theo seed/profile, pooled deficit exposure, empirical bootstrap/LOO và profile-difference sensitivity. `rq2_conditions_evidence_20261108.md` dòng29 còn ghi rõ selected inputs thiếu exposure theo seed/cell. Đề xuất mở duy nhất stored synthetic trace để bổ sung hai lớp thông tin còn thiếu.

1. **Mechanism có được gặp ở từng arm/seed hay không?** Báo n(D>0), meanD, maxD, root/nonroot event counts và số concept đã phục vụ, đủ120arms×120steps. Ghép các summary này với đúng30 stored Ψ và hai graph-effect components. Giữ cả zero/exposed-positive/exposed-negative/Ψzero. Đây là bảng đồng xuất hiện đầy đủ để định vị điều kiện, không điều chỉnh Ψ theo exposure sau can thiệp.
2. **CRN ghép theo step còn giữ query chung đến đâu?** Với mỗi seed/profile, giữ cả hai λ-pairs bên trong policy và cả hai policy-pairs bên trong λ. Tổng60 mechanism pairs và60 policy pairs. Báo first_query_difference_step, first_label_difference_step, common_query_prefix_steps, tổng same-query steps và mismatch counts. Query tuple dùng (concept,question) từ trace. Step/time schedule chung được source pin. Nếu cần difficulty phải join exact pinned question_bank, không tự suy từ tên question. Giá trị “chưa từng khác” dùng null cùng count đầy đủ.
3. **Quan hệ giữa can thiệp world và kết quả đã báo có cần đọc cùng divergence?** Mỗi Ψ row giữ đủ bốn Y, hai Δ và hai mechanism-pair summaries cùng bốn arm exposure summaries. Bảng này cho phép đọc có điều kiện những khác biệt endpoint sau khi action/label history đã tách. Đăng ký giữ cả30rows theo seed/profile cố định, không chọn các rows có Ψ dương hoặc exposure cao.

Giá trị mới dự kiến là xác định exposure và divergence ở đúng seed/cell, thay vì dùng pooled exposure làm mô tả cho mọi Ψ hoặc ngầm ghép losses sau policy divergence. Việc có hay không có những pattern cụ thể là kết quả còn chờ phân tích. Gói này không mở thêm bootstrap/CI/p-values, fit, graph generation hoặc corpus mới. Đơn vị suy luận nếu được đăng ký ở một bước sau vẫn là mười seed clusters, giữ ba profiles và bốn arms cùng cluster.

## 3. CRN, ability và giới hạn cơ chế

Exact historical factorial source được tham chiếu bởi manifest với SHA aea2ff…c157. Current runner bytes khác lịch sử, nhưng protocol ngày08 ghi factorial AST hash giống nhau. Phân tích cache chỉ cần đọc/hash source để mô tả, không import hoặc gọi current runner.

Source tạo `default_rng(seed).random((120,2))` một lần cho mỗi seed/profile và dùng hai cột outcome/learning theo step. Bốn arms mỗi seed/profile có cùng latent_identity và random_stream_identity. Cùng seed qua persona có cùng U hash nhưng latent identities khác. Query lựa chọn và y có thể tách sau can thiệp. Đây là coupling exogenous noise của simulator, không đảm bảo cùng-target predictions hay cùng nhãn ở ordinal step sau phân kỳ.

G_env còn giữ graph-correlation trong latent initialization. λ0 chỉ gỡ multiplier prerequisite trong learning equation. Estimator pathways, policy selection, challenge và spacing vẫn có thể tạo Δ khác0 tại λ0. PG là persona với latent vector riêng, nên so Ψ(PYH)−Ψ(PY) vẫn là profile contrast có điều kiện. Controlled-ability ngày08 đã sửa yếu tố này bằng initialization recipe mới nhưng dùng population và edge intervention riêng.

Primary outcome Y vẫn lấy stored endpoint net mean theta gain. `learning_gain` từng event là gross immediate gain, chịu cap/decay/time và khác Y. Không cộng learning_gain rồi thay endpoint Y, không dùng y làm mastery truth. Root/world paths cần có nguyên cả zero-deficit events, còn exposure là biến nội sinh có thể thay theo selected actions. Phân tích theo exposure ở đây chỉ mô tả, không causal mediation hoặc dose-response.

## 4. Admission và toàn bộ negative controls của cache analysis

- Hash manifest/outputs trước đọc, xác nhận gzip928.419B SHA `2a136fbf627cfa59170deec54c10ae562c2f8214eb00970ce41b96c43d065dcc`. Stream hết gzip với giới hạn decompressed bytes/line/count, kiểm EOF/CRC. Reader không gọi native builders, RNG, teacher, GAM select/predict/update, Torch hoặc network.
- Closed grid đúng10seeds×3profiles×2policyflags×2λflags×120steps. Mỗi key duy nhất, steps0–119 đủ, schema/boolean/finite/ranges đúng. Unknown/missing/duplicate row làm dừng admission, giữ failure artifacts. Outcomes đủ120 và contrasts đủ30, source identities và grouping khớp cache.
- Metadata checks giữ cùng latent/U identity trong bốn arms từng seed/profile. Cross-profile latent khác được ghi rõ. Điều này kiểm recorded binding, không tự nhận là runtime audit độc lập của mỗi PRNG draw.
- Recompute arithmetic hai Δ và Ψ từ stored bốn Y với tolerance arithmetic1e−12 đã dùng ở báo cáo cũ. Đối chiếu cached contrasts, không đổi objective hoặc tolerance scientific.
- PG mechanism-null check theo source giữ D=0. Với mỗi fixed g, hai λ traces phải khớp các trường semantic đã lưu, và endpoint Y phải exact. Vẫn giữ toàn bộ policy on/off Δ nếu chúng khác0. Nếu negative bất ngờ fail, dừng/report source mismatch, không bỏ seed hoặc đổi epsilon để đạt.
- Same-query/label comparison phải có first-step witness và flags null/none một nghĩa rõ. Dùng known-answer synthetic arrays nhỏ để kiểm first mismatch, never mismatch, last-step mismatch và zero-D nhưng Δ khác0. Đây là phép kiểm arithmetic/joins của reader, không tạo simulator cases.
- Tất cả120arms/120pair rows/30contrast rows và zero cells đều được giữ. Không paired LL/AUC giữa query khác nhau, không loại hậu nghiệm các arms đã divergence hoặc exposed ít. Có thể báo common-prefix length như diagnostic, không thay population endpoint bằng prefix subgroup.

## 5. Gói thực thi tương lai để Root review

Một script stdlib trong P đọc allowlist `manifest.json,outcomes.json,contrasts.json,summary.json,source_provenance.json,traces.jsonl.gz` của CPU09 và source/report pins. Dùng tối đa32MiB decompressed input/16KiB mỗi line, max14.400records, không gọi simulator. Output nhỏ gồm input hashes,120arm summaries,120pair diagnostics,30joined endpoint rows, validation/result và log. New exclusive output directory, SHA pre/post, failure retention. Reference bundle gốc, không copy lại gzip vào gói mới.

Đề nghị cap30s whole gồm reserve3s cleanup/publication, worker24s, RSS512MiB/free1GiB, một owned process. Đây là cap đề xuất của phân tích cache, chưa dispatch. Raw gzip nhỏ và các reanalysis cũ có runtime thấp, nhưng chưa đo pass đọc trace mới. Kết quả vượt cap phải rejected và giữ raw, không tự retry. Các fixtures join hữu hạn có thể chạy cùng controller nếu Root duyệt exact cases/pins. Các kết quả inference của CPU09/controlled study giữ nguyên artifact và được dẫn riêng.

## Nguồn và SHA của bước chuẩn bị

Đã đọc metadata/report/source cùng một record đầu của trace bằng decompressor hệ thống để xác nhận có concept/question/y/p_true/prerequisite_deficit/learning_gain/gap_days. Chưa đọc toàn population để tạo kết quả mới. SHA dưới đây khóa các inputs của đề xuất.

| File | SHA-256 |
|---|---|
| `research_tracking/reports/CPU09_CPU10_PROTOCOL_DRAFT.md` | `cc6d44da33d0a6cba2c09738e7bcbbe085f1064b2b0ca7e73cca50cd70b02678` |
| `research_tracking/reports/cpu_pilots_20261107.md` | `f3678872f82d2830d6bc7e95d10b78f1004ad0f9d26998fd584e43235d8d0dcd` |
| `research_tracking/reports/rq2_conditions_evidence_20261108.md` | `eee69a64331c8d6aa198ca9f3f42cdd98d2ef1c9978f1b898768d3c7b5d47cce` |
| `research_tracking/reports/factorial_pilot_uncertainty_20261107.md` | `ad202ed3eb28a597e4e6c8003a9358fde5e45a7058ec44c909d70dabbae842bb` |
| `research_tracking/reports/rq2_controlled_ability_prerequisite_protocol_DRAFT_20261108.md` | `5b8b9be0ee847ae5c8457024da63df7f4096fa744def8c2a330292ce39000b24` |
| `research_tracking/reports/rq2_controlled_ability_prerequisite_results_20261108.md` | `5bd3f075bf3a352ad84ce3cf259a4420ba1d7194bf39cf1895fc5e2197da8e23` |
| `research_tracking/runs/cpu-factorial-20261107-01/manifest.json` | `371985977d32ddd1f3b95c3bab9858d20e4e463b2284b057f1b94db78c5f5cee` |
| `research_tracking/runs/cpu-factorial-20261107-01/outcomes.json` | `e758ae6aa08fc3da0c855e4476f9b71a6c7a9156a65a38073d68ee3475e4f234` |
| `research_tracking/runs/cpu-factorial-20261107-01/contrasts.json` | `3434777a92aca5e44032d281a36a8d95aa7b390ac909c2dc24832c553b125327` |
| `research_tracking/runs/cpu-factorial-20261107-01/traces.jsonl.gz` | `2a136fbf627cfa59170deec54c10ae562c2f8214eb00970ce41b96c43d065dcc` |
| `research_tracking/runs/cpu-factorial-20261107-01/source_provenance.json` | `8b296d89d869e90696be04592a5dc627e617af6c39055a863b9eb88b6cd5560d` |
| `research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/manifest.json` | `a910612fdb0b3c728a715a3f5250eb9736016fdd9e691bc8fd29cdc89a146f57` |
| `research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__run.json` | `2042b5e30b2b124767458e603287f2002c289124a3af1016179f3de01f3389e1` |
| `research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__worker_run.json` | `4b8f917da1df9c6fabc7d86b1d513d305ee6546be4be7255001d94109f3e8554` |
| `artifacts/akt/local-tests/controlled-ability-20261108-01/plan.json` | `fce29998c3a94c8c1a499fc43ff9e8aed77f68d62544de82bd4c3d9d66d15c72` |
| `artifacts/akt/local-tests/controlled-ability-20261108-01/worker.py` | `973a1973da7982aac9a44b4112786915a127447ac57c6bce07f51c06e381f119` |
| `scripts/research/run_approved_cpu_pilots.py` | `55e8e3c74c8daa92d572c809353da5546fa435b55e18b8ab30fdcf46e8413e8e` |
| `src/knowledge_tracing/gam_kt/simulator_mechanisms.py` | `0cbfaf1b4735c188e04ed822197121118dcb65849b582af7413e157fd8d847fa` |
| `src/knowledge_tracing/gam_kt/simulator_pathways.py` | `33ad34140f7b08eb22f86e6cc3caf7b0e7c98f09e4fd74945a6f7e9718b07560` |
