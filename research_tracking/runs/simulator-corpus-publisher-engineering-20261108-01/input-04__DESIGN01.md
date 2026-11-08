# Publisher corpus simulator — thiết kế trước implementation

08/11/2026. Chỉ thiết kế, chưa code writer/test, chưa collect hoặc publish dữ liệu/model/remote. Guard do agent `graph_gate_prototype` sở hữu. Schema đã thống nhất với root: `artifacts/akt/local-tests/akt-research-execution-20261108-01/CORPUS_SCHEMA_V1.json`, SHA `f61e2d6340d741d6bc145ab339d71c44a4e383934cad57b26b5996e52bbf5939`; snapshot trước DONE `6a22a093…` được giữ riêng. Publisher không sửa native training/config/authorization hoặc schema observable cũ.

## API tối thiểu đề nghị

Module riêng `src/knowledge_tracing/simulator_corpus_publisher.py`, tests riêng `tests/shared_kt/test_simulator_corpus_publisher.py`:

```python
publish_research_corpus(
    plan: ResearchSplitPlan,
    results_by_role: dict[str, ResearchCollectionResult],
    *, project_root: Path, corpus_id: str,
    expected_sources: dict[str, str], expected_protocol_sha256: str,
    limits: CorpusPublicationLimits,
) -> CorpusPublicationReceipt
```

`results_by_role` có đúng train/selection/calibration, không final; tất cả type exact. `limits` buộc caller khai báo max_file_bytes/max_total_bytes/max_oracle_bytes, wall/RSS/freeRAM và shard limits; không default scientific counts, profiles hoặc workload. Receipt trả corpus/DONE raw-byte SHA, mọi file paths/sizes/SHA, audit/support, source trước/sau và publisher implementation SHA; status chỉ `PUBLISHED_OBSERVABLE_CORPUS_NOT_MODEL_FITTED`. Không sinh authorization/approved/execution_enabled, trainer, CLI hoặc daemon.

## Output khớp guard

Đích duy nhất `PROJECT_ROOT/artifacts/simulator/corpora/<corpus_id>/`; ID whitelist như guard. Đường dẫn ROOT/ancestors phải physical, không symlink/reparse alias; không nhận arbitrary dataset/output root, không ghi protected paths hoặc corpus ID đã tồn tại, kể cả partial.

- 9model-input files: `corpus.json`, `bank.json`, `plan.json`, ba `<role>.jsonl`, ba `<role>.manifest.json`. Exact14 corpus keys/7role-entry keys/14role-manifest keys/7normalized-recipe keys và plan wrapper theo schema đã pin, không tự thêm coverage/status/oracle keys.
- `bank.json={schema_version:1,environment_id,items}`; difficulties normalize float, sort items by item_id để tái lập. `plan.json={schema_version:1,manifest:plan.manifest()}` giữ đúng10keys, final chỉ metadata; không final event path.
- Mỗi JSONL line là **một learner** `ObservableTrajectory.payload()`; learners sort theo ID, không sort hoặc tái tính thứ tự events. UTF-8, canonical compact JSON `sort_keys=True,allow_nan=False`, LF cuối mỗi line. Không oracle/profile/theta/uniform/RNG channels vào observable payload.
- Normalized recipe lấy collector_version/policy/events_per_learner/start_unix_seconds/gap_seconds + UTC unit/timezone; **không** so raw composite recipe SHA giữa roles vì raw SHA gồm role profile map. Role profile SHA giữ riêng, xác minh từ actual sidecar profile map.
- `oracle/<role>.json`: nguyên logical sidecar; `oracle/<role>.collection.json`: nguyên logical collector manifest/provenance, không ghi đè hoặc relabel raw recipe SHA. Serialization strict JSON, không `default=str` âm thầm đổi kiểu. Collector đã tính strict `identity_hash(sidecar)` nên writer kiểm lại cùng identity. `oracle/publication-inventory.json` giữ all-file inventory, source/publisher bindings và recomputed coverage; inventory không tự hash chính nó/DONE.
- `DONE.json` có đúng4keys `{schema_version:1,status:'COMPLETE_SIMULATOR_CORPUS',corpus_sha256,files_sha256}`. `files_sha256` đúng9model-input names kể trên, gồm corpus.json; không chứa DONE/oracle/failure. Guard kiểm DONE + không failure trước/sau, ghim DONE raw SHA vào identity và không list/open oracle/.

## Toàn bộ kiểm tra trước write đầu tiên

1. Reconstruct typed plan/recipe/provenance/limits, verify actual protocol21 bytes và expected source inventory hiện hành; không load Paper2 definitions hoặc gọi environment. Ba manifests phải COMPLETE_REQUESTED_ROLE_NOT_MODEL_FITTED, sources_before=sources_after=expected_sources, actual plan/bank/provenance identities khớp, no oracle-access, counters attempts=returns=completed events và learner counts đúng. Đây vẫn là consistency trên workspace/caller hợp tác, không attestation generator chưa từng gian lận.
2. Kiểm chung actual bank/domain/G_env/environment-semantics/source/normalized recipe/policy/UTC giữa3roles; đúng complete role assignments/seed-family separation, global source_rows unique. Mỗi learner đúng events_per_learner, query times/source-row formula và outcome/query alignment với sidecar; không dùng latent fields để chọn/drop observations.
3. Gọi lại `audit_research_shard` với expected provenance SHA và explicit shard limits, full84reference IDs. Publisher dành cho training-input chỉ commit khi **mỗi role reference_complete**, không subset renormalization hoặc tự collect thêm để lấp thiếu. ≥1 observed learner/item là coverage tối thiểu, **không** chứng minh diversity/calibration adequate hay confidence20learners/edge; không tạo research_ready authority. Các audits vẫn giữ per-item events và unique learners để downstream đặt support policy riêng.
4. Serialize/seal toàn bộ payload bytes và tính SHA/len trước mkdir, kiểm mọi file/all-output/oracle byte caps và cooperative wall/RSS/freeRAM. Buffer chỉ được tăng trong cap caller, không tiếp tục khi telemetry unknown; kiểu invalid/nonfinite JSON bị từ chối. Snapshot bytes làm nested mutable caller metadata sau validation không đổi file sẽ publish. Tính hash theo raw bytes riêng với semantic identity_hash, không lẫn bank_sha256/file SHA với domain_sha256.

Nếu corpus lớn khiến sealed bytes vượt memory/byte cap thì STOP trước mkdir; streaming lớn là batch riêng, không giảm validation hoặc tự tăng cap trong implementation tối thiểu này. Không lấy planned60learners×210events từ schema làm default hoặc coi đã được sinh.

## Exclusive publication và failure

Sau prevalidation/seal, tạo **một canonical corpus directory mới bằng exclusive mkdir**. Ghi tất cả data/metadata và oracle files bằng exclusive-create, flush/fsync, đóng và readback SHA/size so với bytes đã seal. Recheck source/protocol, elapsed/resources, exact expected file inventory và không failure trước commit. Đủ cả9model inputs + oracle/raw receipts/inventory mới tạo DONE **cuối cùng**, exclusive-create và flush/fsync. Không rename lên existing root, không sửa old manifests/inputs, không auto retry/repair/delete partial.

Atomic ở đây là **logical completion bằng valid DONE marker**, không tuyên bố filesystem transaction hoặc power-loss/directory-fsync guarantee đa nền tảng. Trước DONE, reader phải reject; DONE chỉ xác nhận publication, không execution authority. Authorization/actual observable re-audit trước lazy model allocation vẫn là bước riêng của execution pipeline; guard hiện chỉ hash JSONL, chưa parse labels.

Failure trước mkdir: không tạo corpus path, raise `CorpusPublicationFailure` kèm small receipt để caller lưu riêng. Failure sau mkdir: giữ bytes đã ghi và ghi `failure.json` bằng exclusive-create nếu I/O còn hoạt động; không DONE nếu chưa commit. Receipt có stage/error type/files written + SHA/source trước/sau/no rollback/automatic_retry:false/done_created; không dump oracle vào exception. Nếu lỗi commit/postcommit thì returned outcome không accepted; reader vẫn cần nofailure và authorization exact identity, không suy PASS từ marker đơn lẻ. Không hứa ghi được failure receipt khi disk/permission đã hỏng.

## Kiểm thử và handoff trước actual corpus

Sau root duyệt implementation: chỉ synthetic typed fixtures, không native collection/model/NN/GPU/remote. Kiểm roundtrip đúng schema/9DONE hashes, guard metadata-reader path nếu có pure helper phù hợp, cross-role recipe/graph/source/plan mismatch, source-row/correct/query drift, missing coverage, caps trước mkdir, protected/existing/symlink paths, caller mutation, injected write/fsync/readback failure và không DONE/không usable partial. Giữ RED thật nếu có, không fabricate. Bounded suite và source pins gửi root **trước execute**; actual corpus collection/publication cần config/caps/authority riêng. Fresh Gate/kit phải bao phủ collector/publisher/guard trước research execution; writer không giả oldGate đã bao gồm source mới.
