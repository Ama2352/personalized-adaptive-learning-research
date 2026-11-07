# Main worker AKT qua synthetic Parquet — 07/11/2026

## Kết quả và phạm vi

Sau sửa fixture nesting, hai targeted cases **PASS trong20,36s trên Gate-style deep UUID basetemp101ký tự**,0fail/error/skip; outer launcher wall22,8552s, timeout180s. Lượt shallow03 trước đó PASS17,15s nhưng full Gate16 sau đó fail vì đường dẫn export dài; giữ cả hai thay vì dùng shallow PASS nghiệm thu full gate. Main worker smoke thật đọc Parquet fixture qua loader/split thật, tối ưu1step trên8targets, validation3known+1OOV, lưu/reload best epoch1 exact và export4unique target rows. Negative case thay assignment identity bị authorization thật từ chối trước learner query/output creation. Gate17 cần PASS riêng trước tích hợp.

Đây là **software-only synthetic CPU fixture**, gọi `runner._worker_main` **in-process**; không claim watchdog/fresh-process proof từ hai cases mới. Không Junyi/Holdout/GPU/cloud, không benchmark hoặc mô hình nghiên cứu mới. Source production/runtime/main config không sửa **trong tiểu tác vụ worker này**; toàn batch có thay đổi runtime/authorization do agent khác phụ trách. Chỉ thêm `tests/akt/test_worker_lifecycle.py`; không cần script runner mới.

## Audit trước implementation và khoảng trống cụ thể

| Phần đã có | Nguồn | Khoảng trống / cách reuse |
|---|---|---|
| Actual CLI parent/worker, interrupt tại batch/export, fresh attempt, prediction/checkpoint parity | `tests/akt/test_cli_recovery.py`, `cli_recovery_fixture.py` | Fixture cũ thay `_load_phase_inputs` bằng in-memory learners. Không chứng minh Parquet→actual cohort loader→worker liền mạch. Giữ nguyên và reuse2historical PASS cases, không chạy lại6CLIattempts. |
| Actual selection resume sau validation, stale epochs/weights/Adam/RNG/best checkpoint guards | `tests/akt/test_selection_recovery.py` | Reuse3historical PASS cases, không viết lại recovery. |
| Actual refit resume, fresh outer-train vocabulary/epoch budget/Adam/RNG | `tests/akt/test_refit_recovery.py`, `test_training.py` | Reuse2historical recovery PASS cases; refit nằm ở flow khác smoke. Không ép refit vào main worker smoke hoặc mở public full-fold. |
| Full-fold selection→refit→save→export ordering | `test_runner.py::test_private_fold_workflow_is_guarded_and_orders_selection_refit_export` | Test hiện có stub các stages; không coi nó là end-to-end actual full-fold training. `run_full_fold` public vẫn disabled. |
| Parquet chronology/duplicate/fold guards, split disjointness, best-epoch tie convention | `test_data.py`, `test_training.py`, `splits.py` | Các unit contracts đã có; bổ sung đúng integration gap, không nhân đôi mọi unit case. |

Sáu module/source trên cùng `runner.py`, `training.py`, `data.py`, `config.py`, `authorization.py`, `checkpoint.py` và worker entry đã được đọc để xác định scope. Không cần nới authorization guard.

## Fixture và đường chạy thật

Fixture ghi `SYNTHETIC_ONLY.json` với real-data authorization=false; root và mọi Parquet/output nằm dưới basetemp do invocation đặt trong `artifacts/akt/local-tests/`. Lượt03 dùng nested test-name root; bản sửa dùng `tmp_path_factory.mktemp('wk')/'p'`, có assert vẫn nằm trong chính Gate basetemp.6dummy learners ×4events=24rows,1outer-fold sentinel và5outer-train learners. Đây là schema Development giả lập cho test runner, không phải corpus simulator/learner allocation hoặc split nghiên cứu được duyệt.

Assignments/events là Parquet thật, events cố ý lưu đảo thứ tự, có timestamp ties và source_row duy nhất. `make_inner_split` thật chọn parent train/validation; `_load_phase_inputs`/`_capped_learners` thật chọn2train learners(`synthetic-1`,`synthetic-5`) và1validation(`synthetic-3`). Train8rows, validation4rows301–304. Outer sentinel `FORBIDDEN_OUTER_ITEM` không lọt vào train/vocabulary; learner/event folds khớp và train/validation disjoint.

Model giữ smoke template d32/heads4/block1/d_ff64/final_fc32/context100/target_block100/batch4/max_epochs1/dropout0, seed42, cùng optimizer hyperparameters. Chỉ thu nhỏ fixture caps: train users2, val users1, targets/side8, maxsteps2, training seconds30, phase wall90; fetch_rows2 để kiểm learner history xuyên fetch batches. Không sửa `experiments/akt/configs/smoke.json` hoặc hyperparameters của main config.

Chỉ dependency injection cho external Gate1/Gate2 provenance và RAM snapshots, có nhãn `TEST_ONLY`/`PASS_CPU_TEST_FIXTURE_ONLY` trong marker/approval/manifest/proof. `require_authorization`, exact config/data identities, cap comparison, split/Parquet loader, native AKT forward/backward/Adam, validation, checkpoint và exporter không mock. Test root rebind chỉ sống trong pytest monkeypatch context; không tạo Gate2 giả để gọi realdata pipeline. RAM snapshots cố định nên PASS không chứng minh RSS thực hoặc system RAM floor trong môi trường tải khác.

`_load_phase_inputs` chỉ được wrapper quan sát; wrapper vẫn gọi nguyên hàm thật, không thay learners. Test đối chiếu loader highwater fetch_rows2, chronology(timestamp,source_row), user/fold mapping, selected split hash, immutable input hashes và exact prediction target identities.

## Acceptance actual của lượt03

| Kiểm | Output xác nhận |
|---|---|
|Train|8targets,1optimizer step, nonzero gradient/parameter update1step|
|Best/reload|`inner-best-epoch-1.pt`, selected epoch1, state reload exact, vocab đúng`('A','B')`|
|Validation|Loss0,7202878395716349;3predicted known rows,1unseen, expected4; đây là readout fixture, không metric nghiên cứu|
|Prediction export|4unique source_rows301–304 đúng user/exercise/correct của validation;3fitted và1`unseen` với null probability|
|Identity|Parent split SHA`cbb4918de046f20ac7939d7fc728cb2f8b99005a849c55036ce89571245eb0c0`; active split SHA`1f7ad5d61d2c6916928db55673f6d43ccde0c64ace86948ebe1ac2ab5748dac3`|
|Checkpoint|SHA`0d90abc247cc3cf4339cd8b87503ccd728d466a09f690c315d8b377fc8863a6d`; encoding/split identity trong checkpoint được đối chiếu|
|Data integrity|Marker, assignments Parquet, events Parquet, canonical/split fixture manifests SHA giữ nguyên trước/sau|
|Negative contract|Đổi `approval.identity.assignments_sha256` → `PermissionError` trước `_load_phase_inputs`, không tạo run output|

Proof đầy đủ tại `parallel-worker-20261107-03/t/test_main_worker_reads_parquet0/synthetic-project/experiments/akt/results/synthetic-worker/worker-acceptance.json`; manifest, checkpoint và prediction Parquet giữ cùng output. Negative proof tại `.../t/test_main_worker_rejects_chang0/synthetic-project/authorization-rejection.json`. Các đường dẫn `parallel-worker-*` tương đối với `artifacts/akt/local-tests/`.

## Failure và invocation được giữ

| Trial | Output thật | Giải thích / sửa |
|---|---|---|
|01|2fixture setup errors38,54s; launcher41,6841s|Fixture rebind trusted root trước load unchanged smoke template, nên config root guard từ chối. Sửa thứ tự load template trước monkeypatch; không nới guard. Giữ log/XML/source snapshot/inventory.|
|02|1failed+1passed8,71s; launcher10,3361s|Negative authorization PASS. Actual loader chạy nhưng native build bị Git upstream ownership guard từ chối trước model construction; không model failure. Giữ log/XML/source snapshot/inventory.|
|03|2passed17,15s; launcher19,3652s|Invocation dùng process-scoped exact safe.directory cho pinned upstream; không persistent/global/repository Git config thay đổi.|
|Full Gate16|512passed+1failed372,65s|Worker mới fail khi DuckDB mở export pending file264ký tự trong deep UUID basetemp; không publish gate pointer.|
|04(deep)|2passed20,36s; launcher22,8552s|Bản sửa chỉ rút ngắn fixture nesting; basetemp101ký tự cùng độ dài prefix/UUID Gate16, actual worker/export và negative authorization đều PASS.|

Lượt02 còn có assertion tên unseen chưa tới đường chạy; đối chiếu exporter contract rồi sửa literal thành`unseen` trước03. Đây là sửa test contract, không thay prediction schema hoặc production code.

Lệnh targeted03 nằm trong `parallel-worker-20261107-03/invocation.json`: `.venv\Scripts\python.exe -B -m pytest tests/akt/test_worker_lifecycle.py -q -p no:cacheprovider --basetemp artifacts/akt/local-tests/parallel-worker-20261107-03/t --junitxml artifacts/akt/local-tests/parallel-worker-20261107-03/pytest.xml`. Outer launcher gọi `subprocess.run(timeout=180)`; env `PYTHONPATH=src`, `CUDA_VISIBLE_DEVICES=''`, `PYTHONDONTWRITEBYTECODE=1`. Mỗi trial dùng thư mục mới và dưới180s.

Git đọc dependency đã pin thuộc user `CodexSandboxOffline`, còn process chạy user `AmaDev`. Theo parent review, lượt03 chỉ thêm exact `safe.directory=D:/Dev/KLTN/artifacts/akt/dependencies/upstream` qua `GIT_CONFIG_COUNT/KEY_n/VALUE_n` trong subprocess env. Native verifier vẫn kiểm commit/tree/file hashes thật. Không wildcard/global config hoặc sửa ownership/source upstream.

## Reuse bằng chứng recovery và handoff

`parallel-worker-20261107-03/reused_existing_coverage.json` đối chiếu7existing cases(2CLI,3selection,2refit) với actual Colab CPU505 XML và sourcekit139 hashes. XML nguồn SHA`a338f88d647aaa61a2da414be1098d002389923dd6a933f58be305459ab24878`, đã so với RESULT_MANIFEST. Cả7case PASS trong run lịch sử; đây không phải7tests mới chạy trong lượt này và không cộng thành9newtests.

`handoff_inventory.json` ghi59source/output/temp-fixture files theo SHA trước parent archive; includes failures, input Parquet, acceptance, `.pt` và prediction artifacts. Không xóa/di chuyển file để làm đẹp tree. Snapshot source pass03 SHA`734f28bd0aea487a67b364a83e3def69a3ca1cd34e3c658583055c5f8ec28b47` nằm tại `test_worker_lifecycle_pass03.py`. Log03 SHA`45359eb1eb957a9425931d76ae252a94f36ce2ac7e750ee6bb75d5a43fee0583`; XML03 SHA`dfad218c01254cc9136d2363a450f0c9ff0a82a0e3b3a04c14b72674018826d8`.

Không chạy full Gate2/Gate16 ở tiểu tác vụ này; source suite đã đổi nên parent phải dùng gate mới sau khi các agents ổn định. Không viết script production mới vì chỉ thiếu integration test. Parent chịu trách nhiệm review/index/archive/commit; không sửa state/tasks/index/Git trong gói này.

## Bổ sung sau failure full Gate16 — path-length contrast và deep regression

Full Gate16 do parent chạy ghi512pass/1fail372,65s, không publish pointer; pointer vẫn Gate15 tại failure receipt. Log/XML SHA lần lượt`340578e4ddf024ad9167f0fb58c08c18b5390239fff26d692ae37b45bb9cda0e` và`ccf574f90f132d699c0bd7ff0446b2a6f608c18fd4d33890b9e4e2c459cffa17`. Parent receipt`artifacts/akt/local-tests/linux-gate16-failure-receipt.json` ghi source worker734f28bd… và **build hashes chụp sau failure**, không phải wrapper-issued PASS report. Source đúng hash này đã snapshot trước fix tại `parallel-worker-path-20261108-01/test_worker_lifecycle_gate16_failed_source.py`.

Trước sửa test, diagnostic DuckDB1.5.6 chỉCOPY/roundtrip1synthetic row, root mới có cùng độ dài với failed Gate basetemp, không ghi vào old Gate directory:

| Control | Tổng ký tự path | Kết quả |
|---|---:|---|
|Baseline ngắn|87|PASS|
|Cùng deep parent, filename ngắn`a.parquet.tmp`|227|PASS|
|Cùng deep parent, filename UUID/đuôi giống failure|264|IOException, Cannot open file, path not found|
|Compact fixture root, filename UUID giữ nguyên|220|PASS|

`parallel-worker-path-20261108-01/path_control.json` lưu exact paths/errors/timings/source/log/XML hashes; `path_probe.py` giữ mã diagnostic. Đây là contrast độ dài/path trong môi trường DuckDB/Windows hiện tại, phù hợp nguyên nhân long path; không phải graph/model failure và không chứng minh mọi đường dẫn dưới một ngưỡng đều hợp lệ.

Fix chỉ chuyển root fixture từ`<test-name>/synthetic-project` sang`wkN/p` ngay trong cùng basetemp, giữ run_id/model/config/caps/split/input/authorization/OOV/assertions. Không sửa production exporter/guards/settings, không đổi registry hoặc bật chế độ long-path. Bản mới vẫn tạo `.pending/<UUID>-00000.parquet.tmp` bằng exporter thật.

Lượt04 dùng basetemp`artifacts/akt/local-tests/gate2-20261107-linux-worker-dp-919f6cd39bec4493939349f9784fe6e4`,101ký tự, cùng độ dài với Gate16 UUID prefix. Log/XML/invocation/source snapshot tại`parallel-worker-20261108-04/`. Source final SHA`fd583722bc3f3b97e990cfde83715601b49d4daae793c587603305dbc79ab225`; log SHA`449d1a1e8595ea45871c85ab66e372417a461fe8a516c52f0bef68d57b43088e`; XML SHA`3e58a4d631119bc7b92d36d66c72fe0bf272d594315e42b4e7224b73d88f1005`.

Actual acceptance04 ở`<deep-basetemp>/wk0/p/experiments/akt/results/synthetic-worker/worker-acceptance.json`, negative proof ở`<deep-basetemp>/wk1/p/authorization-rejection.json`. Train8/val4/fitted3/unseen1, target identities301–304, split hashes và validation loss giữ đúng lượt03; best checkpoint mới SHA`6a574ce31d0c480b66ea9b3b2ae8f1e932af747ebb345fd7e33e2bda738a5e34`. Source/runtime identity chứa test source/root mới nên không mong checkpoint file bytes giống lượt03.

**Rủi ro production còn riêng:** một workspace/output root thật đủ sâu vẫn có thể đẩy DuckDB pending-file path vào cùng vùng lỗi; rút ngắn fixture không chữa hoặc chứng minh production exporter hỗ trợ mọi long path. Điều này cần issue/acceptance riêng trước deployment vào root dài; không tự thay production behavior trong gói này. Chưa archive combined hoặc coi Gate17 PASS khi chưa có output xác nhận.

Giới hạn còn lại: chưa actual public full-fold worker/refit end-to-end, chưa main realdata authorization, chưa resource load/hard-kill/Volume durability hoặc full training. Fixture PASS không tự thông qua S04/S05, không chứng minh efficacy hoặc hoàn tất RQ3.
