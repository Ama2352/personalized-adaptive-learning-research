# GRAPH13 · file admission và external freeze V1

10/11/2026. SOURCE-ONLY, chờ Root review contract. Không đọc predictions/checkpoints Main, corpus, Holdout hoặc chọn winner. Không import hay chạy Python, test, model hoặc Git trong lượt chuẩn bị. Phạm vi tài liệu là thiết kế API đủ cụ thể để triển khai. Chưa có validator thực thi hoặc quyền refit.

## Quy tắc đã cố định

Giữ nguyên `MAIN_SELECTOR_CONTRACT01.md`, Protocol21/22, Accounting23, Recipe26 và allocation. Đủ chín candidate gồm A0, A1/A2/A3 × expert/learned, SAKT và GKT phải hoàn thành selected-fit80/raw-best-selection10 trước freeze và mọi main refit. A0 cộng bốn A1/A3 là common-support/eligible population. A2/SAKT/GKT vẫn được admit và báo coverage, nhưng không đổi U hoặc thành eligible. Không thêm minimum n, practical-effect epsilon, Holm, p-value hoặc rút bớt2000 draws.

Tái dùng `MainAdmissionAccumulator` và `select_from_common_statistics`. Hai core này đã có kiểm thu riêng, không viết lại loss/bootstrap. Dùng response-pooled LL, private MT19937 seed42,2000 shared learner draws, type7 upper0,975 strict<0, stable ID tie và A0 fallback hợp lệ. U rỗng là inconclusive, không tạo freeze hoặc nhận A0. n=1 vẫn hợp lệ theo algorithm, có cờ conditional_single_learner.

## Ba chỗ cần contract file thật trước implementation

1. Chưa có request source-authoritative cho tập file của cả chín producer. `SelectedCandidateClaim` chỉ là khai báo typed. Cần Root đóng một request có externally supplied SHA, chỉ rõ các artifacts và receipt operation đã được duyệt. Không tự diễn giải một boolean hoặc tên COMPLETE là bằng chứng operation đã nghiệm thu.
2. `PopulationExpectation` cần full K và K/y hash đúng scheme `model-neutral-selection-K-y-jsonl-v1`. AKT `coverage.population_sha256` được tạo bởi `_public_population` từ learner/item/time/source/rank cùng role shard, không có history prefix trong payload và khác algorithm. Không relabel nó thành canonical K/y hash. Cần chuẩn bị expectation từ trusted selection-role enumeration trước selector, bằng public reader cùng prefix-chain semantics đã dùng trong data bridge. Đây là dữ liệu selection, chưa phải oracle hoặc metric mới. Không tạo expectation bằng cách tin một export candidate rồi bỏ kiểm independent population.
3. Ba producer không có một COMPLETE schema hoặc checkpoint schema chung. Cần ba adapter cụ thể dưới đây. Riêng receipt owned/outer là sản phẩm controller, không phải producer schema. Root review phải ghim exact receipt bytes và acceptance theo đúng controller phiên bản đó. Không tạo universal predicate dựa duy nhất `status` chứa chữ ACCEPTED.

Đây là các quyết định implementation và provenance thông thường, không mở lại phương pháp hoặc yêu cầu GVHD. Chưa nên xuất bản một partial validator với tên completed external freeze khi ba điểm này chưa được Root chốt.

## API tối thiểu đề nghị

Một module riêng trong prep trước khi apply. Khi được duyệt có thể chuyển thành `research_selection_files.py`, cùng một file tests/shared_kt. Không sửa kernel, reader, model, checkpoint hoặc Main stage trong batch này.

```python
def inspect_selected_files(root, *, request_file, expected_request_sha256, limits):
    # Đọc/hash/validate đủ9, rồi trả file-admitted population và sufficient stats.
    # Không chọn model, ghi freeze hoặc cấp authority.
    ...

def calculate_freeze_candidate(admitted, *, kernel_limits):
    # Gọi đúng frozen kernel, giữ các coverage/draws/negative cases.
    # Trả prospective freeze metadata, chưa durable và không refit permission.
    ...

def publish_closed_freeze(root, admitted, statistics, *, output_directory):
    # Exclusive files + source/input rehash + readback + COMPLETE cuối cùng.
    # Đầu ra cached selection evidence. Mainrefit consumer phải được nối riêng.
    ...
```

Không callbacks I/O/model hoặc arbitrary verifier trong các argument. Các đối tượng admitted chỉ được tạo bởi factory file inspection của module, giữ private seal và immutable serialized contents. Seal hỗ trợ consistency giữa API, không chống caller độc hại hoặc thay actual Root review.

Initial consumer chỉ nhận `grade10_simulator` vì các public producers hiện chưa hỗ trợ Junyi. Từ chối environment khác trước mở model files. Junyi vẫn là required environment và cần adapter/version riêng khi có actual producer, không được coi đã hoàn thành bởi Grade10.

## Request đề nghị để Root chốt

Đây là closed-field blueprint, không actual authorization/request. Mọi SHA/size/path đều lấy từ file thật khi chuẩn bị một cached operation, không điền giá trị minh họa thành evidence.

| Field | Ý nghĩa và kiểm bắt buộc |
|---|---|
| schema_version, kind | 1, `MAIN_NINE_CACHED_SELECTION_REQUEST_V1` |
| execution_scope | `CACHED_SELECTION_ONLY_NO_MODEL_OR_REFIT_GRANT` |
| context | Exact `MainSelectionContext` theo adopted constants và cùng domain/bank/split/train/selection roles |
| population_expectation | Exact `PopulationExpectation`, kèm file/source receipt của trusted canonical selection enumeration |
| candidate_inputs | Exact chín ID, không array cho phép duplicate và không optional candidate |
| source_inventory | Pins module validator, hai core, adopted docs và allocation của cached operation |
| limits | Explicit limits cho read bytes, CSV buffers/indexes/rows/fields, open files, clock và output |
| kernel_limits | Existing `SelectionKernelLimits`, đủ2000 draws, không tự giảm R để vừa cap |
| review_reference | Root review của chính request SHA, không assertion về actual fit hoặc quyền refit |

Mỗi `candidate_inputs[id]` có đúng các field sau.

- `producer_kind` là AKT_MAIN_SELECTED_V1, SAKT_MAIN_SELECTED_V1 hoặc GKT_MAIN_SELECTED_V1 đúng với ID.
- `run_directory` và FileRef cho invocation, COMPLETE, selected-terminal, selected-claim, events, predictions, targets và coverage.
- `checkpoint_directory` với ba FileRef COMPLETE.json, metadata.json và state.pt. Các refs phải cùng một directory, đúng best selected epoch.
- `expected_claim_binding` ghim context, config/source/runtime, phase/encoding/vocab, candidate/estimator/graph train80 condition, epoch objective và initial identity. Không dùng field này thay kiểm bytes của artifacts claim trỏ tới.
- `expected_checkpoint_identity` là full identity đúng producer, được đối chiếu exact metadata. Không chỉ so selected_epoch hoặc một SHA rời.
- `producer_source_files` ghim logical source path cùng FileRef tới bytes đã sử dụng. Cho phép snapshot đã đóng ở đường dẫn khác nhưng phải giữ logical key. Digest vector đúng algorithm nguồn của producer phải khớp invocation/claim. Không bắt training lịch sử khớp một file current đã sửa sau đó, cũng không lấy file current bất kỳ để làm historical attestation.
- `runtime_file` và `config_or_spec_file` với FileRef đúng bytes đã review.
- `accepted_operation_receipts` là exact refs của terminal outer, owned result, Root reconciliation nếu có và source-specific acceptance receipt. Root review adapter phải chỉ rõ required fields, lỗi null/empty, cleanup và late failure của phiên bản đó trước implementation. Không có generic boolean trust.
- `forbidden_failure_markers` là danh sách exact path do adapter phiên bản đó quy định, tối thiểu producer `failure.json` và các late/postwrite rejection paths của controller. Sự vắng mặt cũng kiểm lại trước đóng freeze.

FileRef chỉ gồm `path`, `sha256`, `size_bytes`. Path relative chuẩn POSIX trong root, không absolute, backslash, `.`/`..`, symlink/junction hoặc ancestor alias. Không mở dataset, BKT protected artifacts, legacy venv, final/oracle hoặc arbitrary import. Paths tương đối bên trong producer COMPLETE không được tin để mở file ngoài request allowlist. State.pt chỉ streaming hash/size, không pickle/deserialization/Torch.

## Adapter theo producer thật

### AKT A0–A3

Nguồn `akt/research_selected_runner.py:204–220,353–383` và `research_runner.py:253–313,432–436`.

- COMPLETE status `COMPLETE_MAIN_SELECTED_ONLY_CANDIDATE`, terminal_sha256 và claim_sha256 phải khớp bytes. outputs_sha256 có bản kê toàn run trước khi ghi COMPLETE. Kiểm toàn bộ các refs đã allowlist cần thiết và không mở path khác theo bảng kê.
- Terminal kind `MAIN_SELECTED_ONLY_CANDIDATE_V1`, status SELECTED_ONLY_COMPLETE. Đối chiếu candidate, own selected epoch, complete epochs, raw_prediction_sha256, target_sha256, journal_sha256, checkpoint ref và các flags refit/calibration/system selection false. Resume lineage nếu có phải giữ nguyên, không đổi latest thành best.
- Claim artifact hashes/sizes phải khớp terminal, checkpoint state.pt, predictions, targets và coverage thực. Shared initial backbone là cùng SHA cho đủ bảy A-conditions, A0 độc lập và không graph condition bên ngoài. A1/A2/A3 đúng condition/graph train80 role của request.
- Checkpoint COMPLETE status `COMPLETE_CGAKT_EPOCH_TRAINING_STATE`. COMPLETE→metadata/state SHA và metadata.checkpoint_bytes phải khớp. Metadata receipt.completed_epochs bằng selected epoch, neural_binding.phase_scope=select_train80 và profile.purpose=selected_fit_candidate. So full checkpoint identity theo request, gồm condition, encoding, sources và execution profile nếu schema2. Các low-level flags fitted_research_model=False không phải lỗi và không được đổi sang true.

### SAKT và GKT

Nguồn `sakt/research_runner.py:234–277,373–388` và `gkt/research_runner.py:283–326,437–452`.

- COMPLETE status lần lượt `COMPLETE_SAKT_MAIN_SELECTED_ONLY` hoặc `COMPLETE_GKT_MAIN_SELECTED_ONLY`, chỉ có terminal/claim SHA cùng system_freeze_performed=False. Chúng không thay một full-files inventory.
- Terminal đối chiếu candidate/epoch/completeepochs, checkpoint_sha256/complete_sha256, source_sha256/runtime_sha256 và refit/calibration/external-freeze false. Predictions/targets/coverage/events đi qua claim artifact refs, không tự suy COMPLETE đã bind chúng.
- SAKT checkpoint status `COMPLETE_SAKT_EPOCH_TRAINING_STATE`, metadata.progress.completed_epochs bằng selected epoch. Identity phase_scope=select_train80, encoding/vocabulary và source vector phải khớp.
- GKT checkpoint status `COMPLETE_GKT_EPOCH_STATE`, metadata.counters.complete_train_epochs bằng selected epoch. Identity phase_scope=select_train80, model_spec/graph/encoding, source_sha256 và recipe29 phải khớp.
- Không ép cả hai dùng graph checkpoint receipt layout. SAKT graph disabled; GKT expert/static và graph_train_role phải đúng train80. Không yêu cầu backbone identity của baseline bằng AKT.

Hash/metadata validation không độc lập chứng minh tensor contents, Adam/RNG hoặc actual execution. Những phần đó đến từ producer checkpoint restore cùng actual accepted operation đã ghim và review. Hợp đồng consumer phải ghi giới hạn này, không gọi file SHA là machine attestation.

Giữ raw file SHA riêng với semantic identity. AKT config_sha256 dùng `native_auth.config_hash(config)`, còn SAKT/GKT config_sha256 trong claim là spec.identity. Corpus raw plan.json SHA khác logical split.identity. Claim.sources_sha256 là identity hash của build/source mapping, không raw SHA của file inventory JSON. AKT lấy mapping từ invocation.identity.native_evidence.build_hashes, hai baseline lấy invocation.identity.source_files. Checkpoint source vectors có hệ logical keys riêng, có thể là list các cặp sau JSON serialization. So đúng cấu trúc đã pin, không tự biến mọi vector thành cùng một dict rồi đổi hash semantics. `identity_hash` dùng JSON UTF-8 sorted keys/compact/ensure_ascii=False không newline, còn population hash dùng từng canonical JSON record kèm newline.

## CSV và canonical statistical view

Key trung tính theo đúng `ModelNeutralKey` có tám field learner_id, item_id, timestamp, source_row, global_rank, history_hash_scheme, history_sha256 và origin_role. Origin selection, scheme observable-prefix-chain-v1. Dùng literal decimal integer và label0/1, probability binary64 finite[0,1] hoặc ô trống cùng reason unsupported. Không float32 recast, round hoặc điền0,5.

Header AKT predictions gồm key tám field, phase_scope/phase_sha256/encoding_sha256, window_id/history_available/history_used/context_reset, probability và support_reason. Targets có key tám field, phase/encoding ba field và correct. Header SAKT/GKT predictions gồm key tám field, probability/support_reason/input_support_reason, phase/encoding ba field. Targets chỉ có key tám field và correct. Kiểm exact field set, duplicate column hoặc extra/calibrated fields bị từ chối. Giữ phase/encoding riêng từng candidate, không đưa chúng vào K để làm vỡ population chung.

CSV hai baseline được sort canonicalK trong producer, AKT giữ thứ tự scoring targets theo chronology. Vì K sắp learner rồi item trước timestamp, không được giả cả ba CSV đều cùng sort order. Giải pháp nhỏ là xây bounded row-offset index của mỗi file, chỉ giữ canonical K và byte spans. Scan header/body và reject duplicate K trước. Sau đó đọc chín cặp dòng theo canonical K chung, tạo đúng chín `RawSelectedRow` một lần và gọi accumulator. Không materialize chín full row tables, không sửa exports hoặc chronology của training. Nếu dùng line offsets, phải reject multiline field và control characters đúng schema identities hiện có; không tự split CSV bằng dấu phẩy.

Prediction và target phải khớp K đầy đủ, phase/encoding ở những field có mặt, số hàng/F/y và claim coverage. Support_reason của p khác null phải là supported. GKT input_support_reason giữ cold_query_only/known_history hoặc oov_item/unsupported_history theo source, không đồng nhất trained_item với target eligibility. Giữ zero-contribution learners riêng. Mọi row đều được kiểm, kể cả A2/SAKT/GKT và unsupported. Full F/K-y hashes phải khớp expectation độc lập đã pin, không chỉ khớp giữa hai candidate.

## State machine và đóng artifact

Các state dự kiến là REQUEST_VERIFIED → NINE_FILES_ADMITTED → FULL_POPULATION_ADMITTED → STATISTICS_COMPLETE → CLOSED_FREEZE. Failure làm state terminal failed, không retry hoặc trả partial winner. Tất cả phases dùng một cumulative cooperative deadline. Kernel nhận remaining time nhỏ hơn deadline chung, không reset cap giữa chín candidates hoặc giảm draws.

Limits explicit gồm max_metadata_bytes, max_csv_file_bytes, max_checkpoint_bytes, max_total_read_bytes, max_csv_buffer_bytes, max_index_entries, max_fields, max_field_bytes, max_rows, max_learners, max_row_checks, max_seconds và max_output_bytes. Resource telemetry/owned hard deadline nằm ở outer do Root review, không gọi cooperative check là hardkill. Hash streaming source/state và check clock mỗi chunk. Input before/after pins gồm source/runtime/config/checkpoint/exports/request cùng failure-marker absence. Không chỉ dùng size/mtime làm integrity.

Publication exclusive tại run output đã review, dự kiến `selection-freeze.json`, `admission.json`, `coverage.json`, `statistics.json`, `input-inventory.json` và COMPLETE cuối. Mỗi file fsync/readback và quota trước/sau. COMPLETE bind exact outputs và request SHA. Freeze ghi all9 epochs/terminal/checkpoint refs, F/U hashes, coverage, draw SHA/algorithm IDs và chosen ID/reason. ROOT actual cached execution receipt còn cần xác nhận không late postwrite failure hoặc timeout sau COMPLETE. Sau khi source ổn mới gọi kết quả là closed selection freeze.

`main_refit_authorized=False`, `optimizer_authorized=False`, `paid_execution_authorized=False` luôn giữ trong cached output. Main stage hiện vẫn phải từ chối refit. Một batch riêng mới nối consumer externally pinned COMPLETE+freeze với genuine execution grant trước fresh90 constructor. Không viết ngược freeze để biến candidate chưa xong thành đủ barrier.

## Tám fixture families nhỏ cần có trước actual cached selection

1. Positive chín manufactured producer layouts, cùng F/y, nontrivial unequal learner counts và một OOV ở comparison-only. Reconcile current kernel/accumulator known answers, không sửa bootstrap để thuận kết quả.
2. Missing/extra/duplicate model, wrong variant/topology và shared-backbone mismatch. Refuse trước kernel/RNG.
3. Wrong domain/corpus/roles/source/runtime/config hoặc phase refit/calibrated export. Bao gồm body có SHA hợp lệ nhưng provenance không khớp request.
4. Duplicate/missing/extra K hoặc cùng K khác y. Một trường hợp chín candidate cùng bỏ một row nhưng bù cùng extra row phải bị expectation F/hash phát hiện.
5. CSV header duplicate/extra, quoted commas hợp lệ, multiline identity bị cấm, malformed decimal/binary label/NaN/Inf và null thiếu unsupported reason. Không đổi probability khi parse.
6. Checkpoint state byte mismatch, COMPLETE→metadata mismatch, wrong selected epoch/phase/source identity và source snapshot byte drift. Không import Torch để phát hiện các lỗi này.
7. Common-U chung khác pairwise U, zero-contribution learner, empty U và valid noneeligible A0. n1 giữ conditional flag, không thêm threshold mới.
8. Late failure marker, tampered accepted-operation receipt, input change giữa parse và publish, byte/clock/quota breach. Không có COMPLETE/winner accepted, giữ failure, nguồn ngoài owned TMP không bị ghi.

Workload fixtures dự kiến bốn keys × chín candidates, textual fake state.pt chỉ kiểm hashing. Đây là IO/schema/statistics fixtures, không tensor/NN/fit proof. Root có thể chọn cap30s cho pure operation sau review source, nhưng chưa cấp quyền chạy từ note này. Không mở actual Main data để chọn test expectations.

## Đề xuất chốt tiếp theo

Root review ba điểm contract file và exact per-controller accepted-operation receipt schema. Sau đó triển khai một module file adapter và một fixture file theo tám families, giữ ba producer adapters rõ ràng. Không cần thay primitive/kernel hoặc current Gate trong giai đoạn candidate ở prep. Đây là phần còn thiếu cụ thể để nối chín actual selected outputs với frozen kernel, thay vì một implementation rút gọn có thể nhầm COMPLETE/claim thành authority.

## Source pins của lượt review

Chỉ đọc nguồn/schema, không đọc actual prediction hoặc model payload trong lượt này.

| File | SHA-256 |
|---|---|
| docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md | c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6 |
| docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md | 96858efc6d99915390d841f45144d2e2be29e244e825b58cee993a148f05f3d1 |
| docs/thesis_recovery/23_TRAINING_MATRIX_ACCOUNTING_V1.md | 6f9e5adc2f075cb9c0c43ebbf1852e2365dd1baf5ff7c59dd8630561b3d72567 |
| docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md | 13a81ad6a5173e1f215e3df01f3917fcbc1cce128c87c93985b57af76faa353a |
| docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json | e939d24e35b66e7da19751fb51e8f9fd696a2aca50442d421c7f3188729644a5 |
| artifacts/akt/local-tests/akt-research-runner-20261108-01/MAIN_SELECTOR_CONTRACT01.md | 5cd1973763ff9783781cc756ad57c5544886657ad63ff8f77369fda58cf44c60 |
| src/knowledge_tracing/research_selection.py | 0e3cf12d15626a76000c6cdc04779ac769806aae2a5e52f769d4c70f3580a348 |
| src/knowledge_tracing/research_admission.py | b8601da03a972834cfd2f5596ea6a6b9c5759437796b4f4b65720f7abc1a92f2 |
| src/knowledge_tracing/akt/research_selected_runner.py | b2b045d4673ff6cbc8e4e4ade8e5599806e52e501f5c8612e894ff636c2f7a46 |
| src/knowledge_tracing/akt/research_runner.py | 19627a1aa1bbf76069f1a07e0b56a3b5c79a1651863a31c37ac1c08c6cf62092 |
| src/knowledge_tracing/akt/research_main_stage.py | 77b7dbfd75f715f3a4179286cd742780581151dc39c39748213c9c55c25b13c1 |
| src/knowledge_tracing/akt/research_graph_checkpoint.py | e17e14199bc2179794a017303344ff1b67e27cdfa9035cb2a18eb85237513992 |
| src/knowledge_tracing/sakt/research_runner.py | 2d6ec4f6f0be78013c610964479ee085d9effecace83259ba525bd066ae8de7f |
| src/knowledge_tracing/sakt/research_checkpoint.py | 40fa69b861fb93d565fb2a37a0f126509c5239e681fdf3a3c5ae022f3b6cb3c7 |
| src/knowledge_tracing/gkt/research_runner.py | 173fbf7cea845a649da4a79f92394883210de239743e4f8f6c687e0730530d30 |
| src/knowledge_tracing/gkt/research_checkpoint.py | d877dfebac8ad626902995c1627a855c3073be2638aaa061a0a2a692c8a9aa4b |
