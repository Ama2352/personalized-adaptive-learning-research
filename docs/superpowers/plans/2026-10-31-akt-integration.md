# AKT Graph-Free Junyi Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tích hợp AKT NonRasch exercise-level có provenance, adapter nhân quả và bounded Development smoke/pilot, rồi bàn giao readiness cho outer fold đầu tiên.

**Architecture:** Giữ nguyên implementation AKT tác giả tại commit đã pin; adapter riêng xử lý vocabulary train-only, timeline xuyên exercise, cửa sổ H=100/T=100 và OOV barrier giữ global anchors. Training dùng mean masked BCE với inner selection rồi refit; benchmark giữ shared row/metric contracts, tách coverage AKT khỏi fallback semantics GAM-KT.

**Tech Stack:** Python riêng `.venv/`, PyTorch CPU FP32 ban đầu, NumPy, DuckDB, pandas, scikit-learn, psutil, pytest; exact versions phải được resolve/kiểm chứng trong Gate 1. Không thêm PyKT, pyBKT hoặc graph dependency vào runtime AKT.

**Spec:** `docs/superpowers/specs/2026-10-31-akt-integration-design.md`.

**DRAFT — PENDING PLAN REVIEW**

Ngày: 31/10/2026. Người dùng đã duyệt revised design làm cơ sở lập plan trong yêu cầu “AKT Implementation Planning”. Spec trên đĩa vẫn mang draft marker của lần bàn giao trước; approval trong yêu cầu mới là căn cứ cho planning, không sửa spec trong task này. Hyperparameters/environment pins vẫn chưa được kiểm chứng thực nghiệm. Plan approval và execution authorization là hai việc riêng; hiện chỉ được tạo tài liệu này.

Approved-spec snapshot SHA-256 đọc khi lập plan: `21d1316853cbd48f78af3c5cce71c45526a0f6a0edf7c54c677ae6714f01879f`. Nếu spec thay đổi, review lại task mapping trước execution; không coi plan này tự duyệt mọi design mới.

## Global Constraints

- Không sửa/di chuyển `dataset/`, `artifacts/bkt_baseline/`, `venv/`, `.wsl/JunyiBKT-Ubuntu/`, historical results hoặc frozen assignments/manifests. Không sửa BKT/GAM-KT/shared contracts và các uncommitted files có trước task.
- Không đọc Holdout interactions, không dùng outer-fold outcomes để tune/early-stop. `suggested` chỉ reporting; topic/area/prerequisites không là model inputs. Không KC giả, graph, Rasch-topic-proxy hoặc learned-UNK augmentation trong baseline này.
- Source: `https://github.com/arghosh/AKT.git`, commit `01b7e8d7d7c862cabc9467108e3e7f2555653a88`, MIT; checkout mới `artifacts/akt/dependencies/upstream/`, không sửa upstream files. Compatibility patch cần STOP và approval riêng trước áp dụng.
- NonRasch `n_pid=0`, `model_type='akt'`, `separate_qa=False`; current exercise biết trước response, strict-past retrieval; native upstream input q=1..N, PAD=0, qa=q+r*N.
- Frozen Development folds 0..4; sequence `(user_id,time_done,source_row)` xuyên exercise; time integer Unix us, không làm tròn. Không dùng BKT per-exercise order_id.
- Window `context_prefix=100`, `target_block=100`, max length=200; first interactions/short learners giữ lại; mỗi eligible target đúng một direct loss/export mỗi epoch/eval. OOV current null, barrier giữ global rank/block anchors.
- Source-sum parity giữ nguyên; training adapter mean masked BCE chỉ trên scored valid targets. Initial hypotheses: d_model=256, heads=8, blocks=1, d_ff=1024, final_fc=512, dropout=0.05, kq_same=1; Adam lr=1e-4, betas=(0.9,0.999), eps=1e-8, weight_decay=0; clip global norm=1.0 sau normalization; B=4 windows, FP32, no accumulation/scheduler; seed=42.
- Preferred selection: inner learner-disjoint 90/10; inner Log Loss, min_delta=0.0001, patience=3, max 20 epochs, earliest tie; fresh outer-train refit đúng selected epoch E. Fixed E=3 chỉ fallback có approval, không tự chọn vì chạy nhanh.
- Dữ liệu/nguồn/cache AKT chỉ ghi dưới `artifacts/akt/`; run outputs dưới `experiments/akt/results/<run_id>/`, không overwrite completed run. Tiếng Việt cho vận hành/research docs. Không relocate artifacts cũ; nếu tương lai phát sinh relocation phải có inventory SHA-256 trước/sau và manifest riêng.
- Lượt planning này không acquisition/install/env/test/train/smoke, không stage/commit hay execution skills. Các lệnh dưới đây là **lệnh tương lai**, chưa chạy. Task steps commit của skill được thay bằng local review checkpoint theo giới hạn không commit; không tự commit user work khi thực thi nếu chưa có authorization mới.

## Review Focus

1. **Batch boundary cắt learner:** fetch block không được reset history hoặc bỏ phần đuôi learner; fixture fetch_rows=2 phải giống loader không chia batch (Task 5).
2. **OOV ngay tại block boundary/chuỗi OOV liên tiếp:** không re-anchor 1/101/201, không kéo prior qua barrier, không tính row null thành fitted (Tasks 6, 10).
3. **Zero valid targets / N biến thiên:** không divide-by-zero/optimizer step vô nghĩa; mean gradient đúng sum/N, không normalize theo padded length (Tasks 8, 9).
4. **Crash/resume và input drift:** không export trùng, không resume checkpoint khác vocab/config/source hoặc thay đổi sampler order (Tasks 9, 10, 12).
5. **Metric adapter dùng sai fallback semantics:** current unseen=null/is_fallback=false phải vẫn được đếm unseen, finite-known missing phải fail; common metrics recompute mọi model trên cùng giao (Task 11).

---

## 1. Bản đồ files và dependency

Tất cả files dưới đây là **dự kiến**, chưa được tạo bởi task planning. Không thêm CLI vào pyproject ở milestone đầu: dùng module `python -m knowledge_tracing.akt.cli`, tránh sửa entrypoints hiện có.

| Task | Files tạo / sửa | Trách nhiệm |
|---|---|---|
| 1 | Tạo `src/knowledge_tracing/akt/{__init__,config,provenance}.py`, `tests/akt/{conftest,test_provenance}.py`, `docs/akt-provenance.md`; sửa `.gitignore` với đúng AKT output rules | Pin, identity, config/safety, source acquisition |
| 2 | Tạo `requirements-akt.in`, `requirements-akt.lock.txt`, `scripts/akt/check_runtime.py`, `tests/akt/test_runtime.py`; cập nhật provenance doc | Compatibility, isolated environment, runtime evidence |
| 3 | Tạo `akt/upstream.py`, `tests/akt/test_upstream_parity.py` | Immutable source import, native forward/loss/gradient reference |
| 4 | Tạo `akt/{types,encoding}.py`, `tests/akt/test_encoding.py` | Stable exercise IDs/support, OOV classification |
| 5 | Tạo `akt/data.py`, `tests/akt/test_data.py` | Development-only chronological streaming |
| 6 | Tạo `akt/windows.py`, `tests/akt/test_windows.py` | Global-anchor windows, context barrier/target masks |
| 7 | Tạo `akt/tensors.py`, `tests/akt/test_causality.py` | Response reconstruction, right-pad batches, masks tests |
| 8 | Tạo `akt/model.py`, `tests/akt/test_model.py` | Shared SequenceKTModel adapter, mean-loss step |
| 9 | Tạo `akt/{splits,training,checkpoint}.py`, `tests/akt/{test_training,test_checkpoint}.py` | Inner selection/refit, epoch streaming/shuffle, checkpoint |
| 10 | Tạo `akt/prediction.py`, `tests/akt/test_prediction.py` | Full row export/alignment/coverage, atomic resume |
| 11 | Tạo `akt/evaluation.py`, `tests/akt/test_evaluation.py` | Existing metrics, common rows, paired uncertainty adapter |
| 12 | Tạo `akt/{runner,cli}.py`, `tests/akt/test_runner.py`, `experiments/akt/configs/{smoke,pilot,fold0}.json`, `experiments/akt/README.md` | Explicit phase runners, config schema, authorization guards |
| 13 | Tạo `experiments/akt/results/<smoke_run_id>/{manifest,smoke}.json` và checkpoint/prediction shards khi được phép | Bounded real-data smoke evidence |
| 14 | Tạo `experiments/akt/results/<pilot_run_id>/{manifest,pilot}.json`, `docs/akt-pilot-readiness.md` khi được phép | Intended-architecture pilot, resource estimates |
| 15 | Tạo `experiments/akt/readiness/fold0-readiness.md` và `fold0-readiness.json` khi được phép | Readiness review; không chạy full fold/CV |

`akt/*.py` trong bảng là dưới `src/knowledge_tracing/akt/`. Chỉ những file đã liệt kê được sửa ở từng task; task nào cần mở rộng scope phải giải thích trước, không chỉnh baseline để test mới pass.

```text
Task 1 -> Task 2 -> [Gate 1: nguồn/runtime/import]
                     -> Task 3 ----------------------+
Task 1 -> Task 4 -> Task 5 -> Task 6 -> Task 7 --------+-> Task 8
Task 5 -----------------------------------------------> Task 9
Tasks 8+9 -> Task 10 -> Task 11 -> Task 12
Tasks 1..12 -> [Gate 2: correctness] -> Task 13 [Gate 3]
Task 13 -> Task 14 [Gate 4] -> Task 15 [Gate 5: STOP chờ full-fold approval]
Full fold tương lai -> [Gate 6: STOP chờ five-fold approval]
```

Thực thi mặc định tuần tự 1..15 để dễ kiểm interface. Sơ đồ chỉ mô tả dependencies, không tự cho phép parallel agents, cài dependency hoặc chạy thí nghiệm. Skill execution/method sẽ do người dùng chọn sau plan review.

## 2. Hợp đồng interfaces dùng chung trong plan

Các dataclass definitions thuộc file/task được ghi rõ; executor không cần tự đặt tên giữa các task:

- **Task 1 / config.py:** `DataPaths(canonical: Path, assignments: Path, canonical_manifest: Path, split_manifest: Path)`. `AKTConfig` chứa `phase`, `outer_fold`, source_root/source_commit, model hyperparameters, H/T, optimizer settings, inner settings, seed, device, batch_size, DuckDB memory/threads, fetch_rows, output_dir, giới hạn users/targets/steps/time/RSS và protocol_version. `load_config(path: Path) -> AKTConfig`; `validate_config(config: AKTConfig) -> None`. `RunIdentity` là dict JSON chỉ gồm primitives, chứa source/data/assignment/config/vocab/lock hashes.
- **Task 4 / types.py:** `KTEvent(user_id: str, exercise: str, time_done: int, source_row: int, correct: int, suggested: int, fold: int)`; `LearnerEvents(user_id: str, fold: int, events: tuple[KTEvent,...])` đã sort. `ExerciseEncoding(vocabulary: StableVocabulary, train_support_students: dict[str,int])` được định nghĩa ở encoding.py, encode known về shared zero-based ID, unknown=-1 chỉ metadata.
- **Task 6 / types.py:** `WindowInputs(inputs: CausalSequenceInputs, target_mask: np.ndarray[bool], global_ranks: np.ndarray[int64], history_available: np.ndarray[int64], history_used: np.ndarray[int64], context_reset: np.ndarray[bool], window_id: str)` chỉ chứa known tokens và không có current targets. `TrainingWindow(window: WindowInputs, targets: np.ndarray[int8])` riêng. `UnseenTarget(event: KTEvent, global_rank: int)` không đưa vào model. `WindowRecord = TrainingWindow | WindowInputs | UnseenTarget` theo mode train/infer.
- **Task 6 / types.py:** `WindowSlice(start: int, stop: int, target_start: int, global_ranks: np.ndarray[int64], unseen: bool)` dùng half-open indexes trong flattened input; unseen slice có một row, không forward. Geometry helper chỉ nhận item IDs/offsets, không nhận labels, dùng chung cho raw learner windows và shared-input predict để không phải tái tạo current labels khi predict.
- **Task 7 / tensors.py:** `AKTBatch(q_data: Tensor[int64,B,L], qa_data: Tensor[int64,B,L], loss_targets: Tensor[float32,B,L], valid_mask: Tensor[bool,B,L], target_mask: Tensor[bool,B,L], source_rows: ndarray[int64,B,L])`; outputs/targets ngoài loss không là network inputs. Pad source_row=-1, target=-1, q/qa=0. `PredictionRecord` ở types.py có toàn schema spec §8, `prediction: float | None`, prediction_kind fitted/unseen, is_fallback luôn false ở baseline.
- **Task 9:** `InnerSplit(inner_train_users: tuple[str,...], inner_val_users: tuple[str,...], outer_fold: int, split_hash: str)` trong splits.py. `EpochStats(loss_sum: float, valid_targets: int, optimizer_steps: int, complete: bool, resource: dict)` trong training.py. `SelectionResult(selected_epoch: int, split_hash: str, checkpoint: Path, history: list[dict])`. Không lấy incomplete epoch làm selection candidate.
- **Task 12:** `RunResult(status: str, run_id: str, identity: dict, gate_records: dict, metrics: dict, resources: dict, artifacts: dict)`; status completed/bounded/incomplete/failed. Gate record objective PASS không đồng nghĩa được user authorize full fold.

Fixtures tạo trong `tests/akt/conftest.py`: `events(n, *, user='u', fold=0, oov_ranks=(), tie_ranks=())` trả KTEvent sequence có source_rows one-based độc nhất, timestamps integer us, correct xen kẽ 1/0; `tiny_model_config` d=32/heads=4/blocks=1/dropout=0; `frozen_fixture(tmp_path)` tạo canonical/assignment Parquet **synthetic** có Dev users đủ fold và Test sentinel user, không đọc Test thật; `assert_tree_hashes_equal(before, after)` chỉ kiểm files test fixture/protected inventories được cấp, không tự quét Holdout. Helpers được bổ sung cùng task sở hữu type, không import module tương lai ngay Task 1.

## 3. Quy ước verification tương lai

Mọi Run dưới đây là instructions cho execution sau approval, không bằng chứng pass hiện tại. Tests mới fail RED do API chưa có; lỗi source missing/runtime thiếu Torch là **BLOCKED**, không phải test RED hợp lệ. Không dùng pytest.skip cho nguồn/runtime thiếu để Gate 1/2 “pass”. GPU tests chỉ opt-in sau hardware verification; CPU-required tests không được skip.

PowerShell từ `D:\Dev\KLTN`, sau Task 2:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
$AktPython = (Resolve-Path .\.venv\Scripts\python.exe).Path
$env:AKT_UPSTREAM_ROOT = (Resolve-Path .\artifacts\akt\dependencies\upstream).Path
```

Mỗi task TDD: viết test assertions → Run RED và đọc lý do → implement tối thiểu → Run GREEN → review diff/files, không commit tự động. Test phase thuần synthetic có thể forward/backward/optimizer trên fixture để kiểm đúng số học, không là Junyi training. Gate 2 phải PASS trước bất kỳ cập nhật weight trên dữ liệu Junyi nào.

### Task 1: Nguồn pinned, config và vùng ghi an toàn

**Goal / prerequisites:** sau plan review + execution authorization; kiểm working tree và bảo toàn uncommitted work trước acquisition. Chưa cần Torch. Nếu execution dùng worktree, phải bảo toàn shared_kt untracked prerequisites, không tự commit/copy tất cả user work.

**Files:** Create files Task 1 ở bảng; Modify `.gitignore` chỉ thêm `/artifacts/akt/`, `/experiments/akt/results/`, `/experiments/akt/readiness/` nếu output cần ignore; không bỏ rule `/docs/superpowers/`. Acquisition tạo checkout mới ở path đã chốt. Đích tồn tại thì verify, không overwrite/reset/clean.

**Interfaces:** `sha256_file(path: Path) -> str`, `verify_upstream(root: Path, expected_commit: str) -> dict`, `make_run_identity(config: AKTConfig, input_hashes: dict) -> dict` trong provenance.py; config/data types ở §2. Import provenance/config không import Torch/BKT.

- [ ] **Step 1 — viết test trước:** `test_verify_upstream_rejects_wrong_commit_or_dirty_source`, `test_config_rejects_graph_holdout_and_protected_output`, `test_phase_and_source_are_explicit`. Dùng local synthetic Git fixture trong tmp_path; assertion ví dụ:
  ```python
  with pytest.raises(ValueError, match='protected output'):
      validate_config(config_with(output_dir=Path('artifacts/bkt_baseline/new')))
  assert config_with().source_commit == '01b7e8d7d7c862cabc9467108e3e7f2555653a88'
  ```
  `config_with` được định nghĩa trong test_provenance.py bằng config hợp lệ. Kiểm path resolved, symlink/junction escape, empty output và existing completed run; không thử tạo link nếu platform thiếu quyền, dùng mocked resolution.
- [ ] **Step 2 — RED:** interpreter hiện có có pytest dùng `venv\Scripts\python.exe -B -m pytest tests/akt/test_provenance.py -q -p no:cacheprovider` trước Task 2; không install vào venv. Cache/pyc test được đặt dưới test temp hoặc AKT output, không ghi environment/protected folders.
- [ ] **Step 3 — implement config/provenance:** explicit known paths, protocol version, fail closed phase/device/partition/graph; verify clean HEAD/remote/source files, MIT LICENSE presence, record `akt.py`/LICENSE/README SHA-256 và Git tree. Đọc version/identity bằng subprocess argument arrays, không shell interpolation. Không coi hash mới đo là trusted expected pin nếu commit chưa đúng.
- [ ] **Step 4 — acquisition khi execution đã được phép:**
  ```powershell
  git clone --no-checkout https://github.com/arghosh/AKT.git artifacts/akt/dependencies/upstream
  git -C artifacts/akt/dependencies/upstream checkout --detach 01b7e8d7d7c862cabc9467108e3e7f2555653a88
  git -C artifacts/akt/dependencies/upstream rev-parse HEAD
  git -C artifacts/akt/dependencies/upstream status --porcelain
  ```
  Expected exact SHA và clean status; xác minh softmax bug fix có trong source. Ghi notice MIT/citation, snapshot hashes và URL trong `docs/akt-provenance.md`; chưa import source. Không có fetch/checkout vào working repo KLTN.
- [ ] **Step 5 — GREEN và local review:** rerun test_provenance; chỉ diff file allowlist, ghi source/config readiness. Không stage/commit.

**Expected / completion:** provenance/file integrity PASS, config safe, source nguyên vẹn; runtime chưa được coi ready.

**Failure / rollback:** network/license/SHA mismatch, dirty checkout hoặc vùng ghi vượt AKT paths → STOP. Giữ evidence và đích incomplete để inspect, không recursive delete/reset user paths; chưa chạy code nguồn không xác minh. Nếu cần upstream patch, ghi failing case + parent hash + patch đề xuất để user duyệt trước áp dụng.

### Task 2: Compatibility và môi trường AKT riêng — Gate 1

**Goal / prerequisites:** Task 1 PASS, execution authorization bao gồm isolated environment/source setup; exact Python/Torch/NumPy pins chưa được chọn. Không reuse `venv/` hoặc cài vào WSL BKT.

**Files:** Create `requirements-akt.in`, `requirements-akt.lock.txt`, `scripts/akt/check_runtime.py`, `tests/akt/test_runtime.py`; Modify `docs/akt-provenance.md` với compatibility matrix/lock hashes. Tạo `.venv/` chỉ ở execution, không trong planning.

**Interfaces:** `inspect_runtime(upstream_root: Path, *, required_device: str='cpu') -> dict` trong script, import source thông qua importlib chỉ sau verify_upstream; report ABI/module origins/version/device/parameter import. `write_lock_from_report(report_path: Path, output_path: Path) -> None` trong cùng script xử lý native pip resolution JSON, chỉ nhận wheels cùng platform và SHA-256, reject source distributions/missing hashes/unpinned records. Script command probe `--upstream <path> --device cpu --output <new-json>`; lock command `--resolution-report <json> --write-lock <new-lock>` không import Torch. Script tự thêm ROOT/src vào sys.path như existing repo scripts, không đòi project đã installed trước bootstrap.

- [ ] **Step 1 — tests trước:** `test_probe_rejects_wrong_interpreter_or_upstream`, `test_runtime_report_records_exact_versions_and_origins`; mock module origins cho protected venv leakage. `test_lock_report_requires_wheel_hashes_and_exact_urls` dùng synthetic pip report, assert mỗi resolved distribution có name/version/direct wheel URL/hash trong lock. Viết riêng `test_native_akt_import_cpu` yêu cầu runtime thật; không thay import failure bằng skip.
  Run RED phần pure/mock bằng interpreter pytest đã có: `venv\Scripts\python.exe -B -m pytest tests/akt/test_runtime.py -k "not native" -q -p no:cacheprovider`, rồi implement minimal report/lock helpers và rerun GREEN trước dùng lock writer. Native import test chưa được coi đã chạy/pass ở bootstrap; sau installation phải run full file trong `.venv` ở Step4.
- [ ] **Step 2 — compatibility trước install:** kiểm absolute Python 3.13.5 path, 64-bit ABI, official Windows CPU Torch wheel tags/requires-python/dependency metadata và API dùng trong pinned akt.py. Ghi matrix source-inspected/wheel-available/import-tested/parity-tested, chưa đánh dấu tested trước chạy. Python 3.12 mới chỉ dùng sau approval nếu 3.13 không phù hợp; không tự chọn obsolete Torch1.2 chỉ vì README cũ.
- [ ] **Step 3 — resolve và lock trong environment mới:** `.venv/` chưa tồn tại mới được tạo bằng interpreter đã xác minh. `requirements-akt.in` gồm torch/numpy/pandas/duckdb/scikit-learn/psutil/pytest; candidate direct pins được chọn theo compatibility evidence Step2, Torch CPU dùng exact official wheel URL/ABI đã kiểm, không placeholder version. Dùng native pip resolver report để khóa toàn transitive wheel URLs/hashes, không cần lock-tool dependency. Dùng fetchmany nên không cần pyarrow; không thêm torchvision/torchaudio/wandb/pyBKT/PyKT. Ghi version pip resolver, indexes và wheel metadata; không sửa requirements.txt cũ.
  ```powershell
  & 'C:\Users\AmaDev\AppData\Local\Programs\Python\Python313\python.exe' -m venv .venv
  .\.venv\Scripts\python.exe -m pip install --dry-run --ignore-installed --only-binary=:all: --report artifacts/akt/preflight/resolution.json -r requirements-akt.in
  .\.venv\Scripts\python.exe scripts/akt/check_runtime.py --resolution-report artifacts/akt/preflight/resolution.json --write-lock requirements-akt.lock.txt
  .\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-akt.lock.txt
  .\.venv\Scripts\python.exe -m pip check
  ```
  Install command chỉ hợp lệ sau lock đủ exact versions/hashes/platform wheel URLs; không có placeholder version được phép install. Không editable install project cần thiết: dùng PYTHONPATH=src.
- [ ] **Step 4 — RED/GREEN runtime tests và import:** run `.\.venv\Scripts\python.exe -m pytest tests/akt/test_runtime.py -q`; lỗi probe/API chưa implement → RED, implement probe rồi GREEN. Nếu native Torch/upstream import lỗi → BLOCKED Gate 1, không sửa upstream khi chưa duyệt patch.
- [ ] **Step 5 — ghi evidence Gate 1:**
  ```powershell
  & $AktPython scripts/akt/check_runtime.py --upstream $env:AKT_UPSTREAM_ROOT --device cpu --output artifacts/akt/preflight/runtime.json
  ```
  Record CPU selected trên host có/không CUDA, Python executable nằm `.venv`, dependency origins và lock hash, source SHA/license integrity, `pip check` output. Recheck available RAM/free disk; không suy từ folder .wsl rằng Torch tồn tại/không tồn tại trong distro.

**Expected / completion:** **Gate 1 PASS** chỉ nếu compatible installed stack, pinned source integrity và import thật thành công. Parity/causality thuộc Gate 2. CPU path bắt buộc; CUDA vẫn UNVERIFIED nếu không inspect được driver/VRAM.

**Failure / rollback:** missing wheel/dependency resolution/API/import failure → STOP báo exact traceback, giữ isolated env/run failed để review, không repair bằng nâng cấp/downgrade venv BKT. Source patch candidate phải được approve riêng. Không ghi pin “validated” dựa chỉ vào version bounds.

### Task 3: Native AKT import wrapper và source parity

**Prerequisites / goal:** Gate 1 PASS; có reference nguyên vẹn để so adapter. Chỉ synthetic tensors, không Junyi fit.

**Files:** Create `akt/upstream.py`, `tests/akt/test_upstream_parity.py`; Modify provenance doc nếu ghi measured parity.

**Interfaces:** `load_upstream(root: Path, *, device: str) -> ModuleType`; `build_native(config: AKTConfig, *, n_items: int) -> nn.Module`. Load `akt.py` bằng explicit file spec, verify hash, module device theo requested device rồi `.to(device)`; một device/process, không global mutation lúc concurrent forward.

- [ ] **Step 1 — tests trước:** `test_wrapper_matches_reference_probabilities_sum_loss_and_gradients` tạo hai model cùng state_dict từ pin, q=[[1,2,1]], qa=[[1+N,2,1]], targets=[[1,0,1]], dropout=0. Assert p/logits (hook head trước sigmoid), loss_sum/N-count và mỗi named parameter gradient allclose atol=rtol=1e-6 CPU FP32; detached distance behavior/source masks giữ nguyên.
- [ ] **Step 2 — RED:** `& $AktPython -m pytest tests/akt/test_upstream_parity.py -q`; expected module/API chưa có, không phải mất Torch/source.
- [ ] **Step 3 — implement wrapper:** giữ `n_pid=0`, no concept/PID tensors, no extra embedding/attention; kiểm d_model chia hết heads. Native forward target=-1 chỉ cho inference loss mask, không đổi head để bỏ arg; source zero-pad first retriever attention giữ nguyên.
- [ ] **Step 4 — GREEN:** thêm `test_cpu_request_overrides_cuda_auto_selection`, `test_no_pid_or_graph_parameters_in_nonrasch`, `test_source_files_unchanged_after_import_and_forward`; kiểm state_dict/native parameter count đúng theo cùng config, dropout eval repeat ổn định.
- [ ] **Step 5 — review evidence:** source/prediction parity, masks/parameter identity report; không tuyên bố paper results đã reproduced.

**Expected / completion:** upstream nguyên vẹn chạy CPU và wrapper số học đúng. **Failure / rollback:** bất kỳ parity/device/compatibility lệch → dừng downstream; wrapper-only fix bằng TDD được phép, upstream-file patch cần approval riêng, giữ reference immutable.

### Task 4: Vocabulary exercise và support train-only

**Prerequisites / goal:** Task 1; dùng shared_kt đang có, không đổi file đó. Fit chỉ user train scope.

**Files:** Create `akt/types.py`, `akt/encoding.py`, `tests/akt/test_encoding.py`; bổ sung fixture KTEvent trong conftest.

**Interfaces:** `fit_vocabulary(learners: Iterable[LearnerEvents]) -> ExerciseEncoding`; `encode_exercises(exercises: Sequence[str], encoding: ExerciseEncoding) -> np.ndarray`; `save_encoding(encoding, path: Path) -> str` và `load_encoding(path: Path) -> ExerciseEncoding`. Vocabulary zero-based như shared, unknown=-1 tách khỏi native PAD/known+1; support đếm distinct train users/exercise.

- [ ] **Step 1 — test trước:** `test_sorted_vocabulary_support_and_oov_without_resize`:
  ```python
  assert enc.vocabulary.values == ('A', 'B')
  assert encode_exercises(['B', 'X', 'A'], enc).tolist() == [1, -1, 0]
  assert enc.train_support_students == {'A': 2, 'B': 1}
  ```
  Fixture train u1:A,A,B; u2:A. Thêm test label/suggested/topic/area changes không đổi encoding; stringify user/exercise đúng shared convention, shuffled rows cùng encoding; empty train scope fail.
- [ ] **Step 2 — RED:** `& $AktPython -m pytest tests/akt/test_encoding.py -q`.
- [ ] **Step 3 — implement:** dùng `StableVocabulary.from_values`, one-user seen exercise set và global support map; serializable token list/support/schema/hash, không union với outer/catalog, không unknown embedding.
- [ ] **Step 4 — GREEN:** round-trip saved encoding hash/ID stable; mutate eval-only labels/exercise không đổi fitted encoding; unknown không làm `StableVocabulary.encode` raise nếu đã được split ra bằng OOV adapter, known encoding kiểm exact shared parity.
- [ ] **Step 5 — local review:** type contract KTEvent/LearnerEvents/encoding rõ, dữ liệu gốc không sửa.

**Completion:** deterministic train-only encoding và OOV metadata đúng. **Failure / rollback:** scope không xác định hoặc train/eval vocab trộn → STOP, bỏ kết quả encoding mới khỏi downstream; không sửa catalog/assignments để chữa OOV.

### Task 5: Loader chronological Development xuyên exercise

**Prerequisites / goal:** Task 4; tận dụng DuckDB nhưng không gọi baseline runners/sidecar builders. Chưa read Junyi cho training.

**Files:** Create `akt/data.py`, `tests/akt/test_data.py`; bổ sung frozen_fixture synthetic.

**Interfaces:** `read_development_assignments(paths: DataPaths) -> pd.DataFrame`; `iter_development_learners(paths: DataPaths, *, user_ids: Sequence[str], allowed_folds: tuple[int,...], fetch_rows: int=50000) -> Iterator[LearnerEvents]`. Users được validate subset Development/allowed folds trước query; output sort user/time/source; reuse `validate_fold_isolation` và invariant assignments phù hợp mà không sửa baseline APIs.

- [ ] **Step 1 — tests trước:** `test_loader_keeps_user_history_across_fetch_batches` với fetch_rows=2 và user ở nhiều exercise/files; `test_ties_use_source_row_across_exercises`; `test_non_development_user_request_fails_before_interactions_query`. Fixture Test sentinel chỉ synthetic, không đọc Test thật; assert output chỉ requested Dev users và expected source row order, no duplicate/invalid binary/null time accepted.
- [ ] **Step 2 — RED:** `& $AktPython -m pytest tests/akt/test_data.py -q`.
- [ ] **Step 3 — implement:** bounded DuckDB memory=512MB, threads≤2, temp directory riêng `artifacts/akt/tmp/<run_id>/`; relational join assignments đã `partition='development'`, requested users và allowed folds trước materialize. ORDER BY user_id,time_done,source_row; fetchmany, giữ learner tail khi fetch boundary. Materialize tối đa một learner + fetch buffer, log highwater; không load tất cả Dev dictionaries/arrays, không phụ thuộc predictions baseline làm input.
- [ ] **Step 4 — GREEN:** thêm reject duplicate assignments/source IDs, unknown partition/fold, empty cohort, invalid negative/non-int source/time, preserve integer us/no seconds rounding; chronological outputs match `build_causal_sequence_inputs(...,item_key='exercise')` trên known-only fixture.
- [ ] **Step 5 — review scope:** SQL không có Test query branch hoặc raw ProblemLog scan; không ghi canonical/assignments. Shared physical Parquet có thể chứa mọi partition, nhưng query chỉ trả/materialize Development rows được phép; không log/count/score Test records.

**Expected / completion:** toàn timelines requested users đủ rows, đúng order, memory bounded. **Failure / rollback:** identity/order/scope/memory fail → STOP, không truncate/drop learner để vượt test; tuning I/O config được log riêng, không thay chronology.

### Task 6: Block windows và OOV context barrier giữ global anchors

**Prerequisites / goal:** Tasks 4–5; tạo window protocol trước tensor/model code.

**Files:** Create `akt/windows.py`, `tests/akt/test_windows.py`; add WindowInputs/TrainingWindow/UnseenTarget/WindowRecord types vào types.py.

**Interfaces:** `iter_window_slices(item_ids: np.ndarray, sequence_offsets: np.ndarray, *, context: int=100, target_block: int=100) -> Iterator[WindowSlice]`; `slice_causal_inputs(inputs: CausalSequenceInputs, window_slice: WindowSlice) -> WindowInputs` reset first prior=-1, không reconstruct labels. `iter_windows(learner: LearnerEvents, encoding: ExerciseEncoding, *, context: int=100, target_block: int=100, training: bool) -> Iterator[WindowRecord]` gọi cùng geometry helper. Infer chỉ WindowInputs/UnseenTarget, current targets không gắn vào WindowInputs; train wrapper chứa target riêng. CausalSequenceInputs item_ids zero-based known, concept_ids=None; prior đầu segment/window=-1.

- [ ] **Step 1 — tests trước:** parametrized `test_target_partition_for_short_and_long_histories` cho n=1,100,101,200,201,22067; expected window ranges spec: n201 có W1 T1..100, W2 C1..100/T101..200, W3 C101..200/T201. Assert target source rows đúng 1..n, không duplicate/lost, mỗi rank/target mask đúng, history_used của targets 101/200/201 là 100/199/100.
- [ ] **Step 2 — RED:** `& $AktPython -m pytest tests/akt/test_windows.py -q`.
- [ ] **Step 3 — implement:** giữ global rank trước split OOV, zero-based target i: block_start=floor(i/100)*100, a=max(0,block_start-100), a'=max(a,lastOOV+1). Tách known segments trong từng block; window end không vượt block/end-of-segment; prefix context-only, scored segment một lần. OOV current phát UnseenTarget, không tensor; rank không bị nén/re-anchor.
- [ ] **Step 4 — GREEN OOV:** `test_oov_at_100_and_101_keeps_201_anchor`, `test_consecutive_oov_and_oov_first_last`, `test_barrier_expires_when_outside_base_context`. Ví dụ zero-based OOV rank100: target101 history=0, target200 base_start100 nhưng effective_start101; target300 base_start200 không còn bị barrier100 ảnh hưởng. Assert prior không đọc r_OOV và source_row/labels metadata giữ nguyên.
- [ ] **Step 5 — local review:** config H/T khác chạy synthetic ownership test, không sửa topology; no pad here, targets/context/pad/zero-history counters đã phân biệt. Empty learner trả không records.

**Completion:** eligible known targets exactly once, OOV null placeholders complete. **Failure / rollback:** lệch counts/anchors → STOP Task7+, không dedup output hoặc reindex data để che lỗi.

### Task 7: Response reconstruction, masks và behavioral causality

**Prerequisites / goal:** Tasks 3+6; chứng minh input/mask correctness trước model adapter training.

**Files:** Create `akt/tensors.py`, `tests/akt/test_causality.py`; add AKTBatch type.

**Interfaces:** `collate_windows(windows: Sequence[WindowInputs], *, n_items: int, device: str, targets: Sequence[np.ndarray] | None=None) -> AKTBatch`; `causal_masks(length: int, device: str) -> tuple[Tensor,Tensor]` trả diagnostic allow-self encoder và strict-past retriever masks, kiểm khớp mask source thật (không chỉ test helper).

- [ ] **Step 1 — test trước:** `test_reconstructs_aligned_interactions_without_double_shift`: A:1/B:0/C:? shared prior[-1,1,0] → native q[1,2,3], qa[1+N,2,3+0*N]. Last response dummy=0; đổi dummy không đổi native p cuối. targets=None cho loss_targets toàn -1; right pad q/qa0, target-1, source_row-1, valid=false.
- [ ] **Step 2 — RED:** `& $AktPython -m pytest tests/akt/test_causality.py -q`.
- [ ] **Step 3 — implement collator:** r_j=prior_(j+1) chỉ trong cùng retained window/segment, cuối dummy; native known=shared+1. Không đưa target hiện tại từ training labels vào qa, không dùng prior từ user/window bên cạnh. Key masks source nguyên vẹn; không thay strict mask bằng shared allow-self mask.
- [ ] **Step 4 — GREEN behavioral tests:** `test_current_response_corruption_keeps_own_probability`, `test_future_responses_and_items_do_not_change_prefix`, `test_past_response_has_detectable_effect`, `test_right_pad_and_other_user_do_not_change_valid_predictions`. Fixed weights/RNG/dropout0, perturb full response input rồi dựng lại prior; test qua block/OOV boundary. Inspect forbidden attention mass=0 trên actual native forward và finite first row; assert single-target prefix matches batched retained-prefix output.
- [ ] **Step 5 — gradient check:** source gradient p_t đối với **activation response riêng vị trí t** =0; không assert shared response embedding parameter grad=0. Eval repeat deterministic; train-mode causality reset RNG hoặc dropout0. Source files vẫn cùng hash.

**Completion:** masks, leakage, dummy/padding/user isolation PASS. **Failure / rollback:** serious leakage/fidelity issue → STOP trước Junyi training, ghi minimal reproducer; không “fix” bằng bỏ first/short/OOV learners hoặc bỏ behavioral assertion.

### Task 8: AKT adapter và masked mean-loss step

**Prerequisites / goal:** Task 7 PASS; giữ shared fit/predict, không dùng BKT/GAM mechanisms.

**Files:** Create `akt/model.py`, `tests/akt/test_model.py`.

**Interfaces:** `AKTAdapter(config: AKTConfig, encoding: ExerciseEncoding)` có `native: nn.Module`, `fit(inputs: CausalSequenceInputs, targets: np.ndarray) -> AKTAdapter`, `predict(inputs: CausalSequenceInputs) -> np.ndarray`, `step(batch: AKTBatch, optimizer: Optimizer) -> dict`. fit là convenience **một epoch** trên supplied small contract batch theo config; production multi-epoch streaming dùng Task9/step, không materialize dataset qua fit. Predict trả p theo thứ tự inputs.source_rows, OOV biểu diễn np.nan trong array và được exporter chuyển null.

- [ ] **Step 1 — test trước:** `test_mean_gradient_equals_sum_divided_by_valid_count` so hai identical models, dropout0, same masks, assert mean=sum/N và gradient từng tham số=sum_grad/N; padding/context không góp N. `test_zero_valid_targets_does_not_step_optimizer` mock optimizer.step count=0.
- [ ] **Step 2 — RED:** `& $AktPython -m pytest tests/akt/test_model.py -q`.
- [ ] **Step 3 — implement:** native summed loss/N cho NonRasch, backward, pre-clip global norm và clip=1.0 rồi step; clear grads; finite checks p/loss/grads, no optimizer step nếu N=0. Adam defaults theo config; predict eval+no_grad, khôi phục mode cũ sau inference, không forward labels qua predict API. Shared contract inputs chỉ dùng known window classification/OOV metadata, không thêm concept/graph.
- [ ] **Step 4 — GREEN:** small synthetic forward/backward có nonzero gradients và params đổi; predict p_t bất biến r_t; SequenceKTModel structural check, fitted known p finite [0,1], OOV np.nan. Predict dùng `iter_window_slices` + `slice_causal_inputs` trực tiếp trên shared inputs, không gọi `iter_windows` qua fabricated KTEvent.correct. `test_eval_repeats_and_train_dropout_is_not_forced_equal` phân biệt expected train/eval; native state_dict topology không đổi so reference.
- [ ] **Step 5 — review:** fit convenience và trainer.step chỉ dùng một loss implementation; không claim lr/clip/B validated vì synthetic step pass.

**Completion:** adapter/normalization/gradient correct; no Junyi training. **Failure / rollback:** NaN/clipping/normalization mismatch → STOP và sửa wrapper bằng TDD; không đổi source/candidate hyperparameters để che architecture bug.

### Task 9: Inner split, epoch training, selection/refit và checkpoint

**Prerequisites / goal:** Tasks 5+8; hoàn thành protocol bằng synthetic fixture/fake trainer trước real data.

**Files:** Create `akt/splits.py`, `akt/training.py`, `akt/checkpoint.py`, `tests/akt/test_training.py`, `tests/akt/test_checkpoint.py`; add dataclasses §2.

**Interfaces:**

- `make_inner_split(development_assignments: pd.DataFrame, *, outer_fold: int, seed: int=42) -> InnerSplit`.
- `train_epoch(adapter: AKTAdapter, windows_factory: Callable[[],Iterator[TrainingWindow]], *, optimizer: Optimizer, epoch: int, budget: dict) -> EpochStats`.
- `select_checkpoint(config: AKTConfig, *, inner_split: InnerSplit, train_learners_factory: Callable[[],Iterator[LearnerEvents]], val_learners_factory: Callable[[],Iterator[LearnerEvents]], identity: dict) -> SelectionResult`.
- `refit_outer_train(config: AKTConfig, *, outer_train_users: tuple[str,...], train_learners_factory: Callable[[],Iterator[LearnerEvents]], selected_epochs: int, identity: dict) -> AKTAdapter`.
- `save_checkpoint(path: Path, adapter: AKTAdapter, optimizer: Optimizer, *, identity: dict, progress: dict) -> None`; `load_checkpoint(path: Path, *, expected_identity: dict, device: str) -> dict`.

Selection/refit validate returned learner IDs against declared lists/split before fitting; factories can be reopened for vocabulary/epochs but không có outer-eval callback argument. Identity xuất checkpoint bổ sung encoding hash được fit đúng scope, không reuse inner encoding hash cho refit vocab mới.

- [ ] **Step 1 — tests trước:** `test_inner_split_is_disjoint_deterministic_and_outer_free`: sort SHA256 tag `akt-inner-v1|42|k|user_id`, tie ID; n_val=ceil(0.10*n_outer_train), remainder train, fail nếu cohort không đủ mỗi phía≥1; shuffle input assignments không đổi split hash. `test_outer_labels_never_enter_fit_or_selection` mutate outer synthetic labels và spy loader calls: selected epoch/vocab/support không đổi, outer user không được requested.
- [ ] **Step 2 — RED:** `& $AktPython -m pytest tests/akt/test_training.py tests/akt/test_checkpoint.py -q`.
- [ ] **Step 3 — implement epoch stream:** train-only window shuffle bằng bounded buffer 1.024 windows, RNG seed/epoch logged; không nạp toàn dataset. Save checkpoints ở complete epoch boundaries; resume giữa epoch chưa hỗ trợ thì mark incomplete và replay epoch từ checkpoint trước đó, không nhận partial model làm complete. Buffer order/RNG/optimizer giữ deterministic trên same runtime/device. Counters loss_sum/targets/steps và mean epoch=sum/targets, no duplicate direct targets. Empty train epoch/inner-val không có known predictions → fail.
- [ ] **Step 4 — implement selection bằng tests:** synthetic validation losses [0.4,0.3,0.3,0.31,0.32] → selected epoch2, patience3, tie giữ sớm; improvement rule `new_loss < best_loss - 0.0001`, đúng bằng threshold không improve (test boundary bằng cùng biểu thức float). Max20, chỉ complete epochs, inner loss known rows kèm coverage. Refit mới seed42 trên full outer-train E epochs, refit vocab/support; test object/optimizer/RNG fresh và vocab có thêm item inner-val nhưng không outer.
- [ ] **Step 5 — checkpoint tests/implementation:** state_dict/optimizer, Python/NumPy/Torch RNG, epoch/sampler seed, vocabulary/support, protocol/source/lock/data/split/config hashes, selection record và resource log; atomic write temp→rename, không overwrite completed checkpoint run. `test_save_load_eval_and_next_epoch_match`, `test_resume_rejects_changed_vocab_config_source_or_split`, CPU load map_location explicit. Không hứa bitwise cross-device/version.
- [ ] **Step 6 — GREEN/local review:** synthetic fixed-budget branch `test_fixed_epoch_mode_requires_explicit_choice_and_ignores_eval_scores`: E3, final checkpoint epoch3, no inner-selection/refit double loop, safety-timeout→incomplete. Không tự switch protocol khi estimate selection+refit đắt. Record staged tests/protocol evidence.

**Completion:** deterministic selection/refit/checkpoint API và training coverage accounting PASS. **Failure / rollback:** split/scope/resume mismatch → STOP, không regenerate frozen assignments hoặc reuse checkpoint khác identity. Crash giữ checkpoint complete trước đó; không delete artifacts cũ. LR/B/normalization change là run/protocol version mới trước outer.

### Task 10: Prediction export đủ source_row và coverage

**Prerequisites / goal:** Tasks 6+8+9; scoring mọi requested target bằng checkpoint đã khóa, kể cả null OOV.

**Files:** Create `akt/prediction.py`, `tests/akt/test_prediction.py`; add PredictionRecord schema ở types.py.

**Interfaces:** `iter_predictions(adapter: AKTAdapter, learners: Iterable[LearnerEvents]) -> Iterator[PredictionRecord]`; `export_predictions(records: Iterable[PredictionRecord], output_dir: Path, *, expected_learners_factory: Callable[[],Iterator[LearnerEvents]], identity: dict, shard_rows: int=50000) -> dict`. Expected factory cho phép đối chiếu lại canonical cohort stream, không lấy những rows đã predict làm expected population.

- [ ] **Step 1 — tests trước:** `test_export_contains_every_source_row_once_including_first_and_oov`: 201 targets + OOV ở block edge; all row count=201, OOV prediction None, fitted=N_known, is_fallback=false; identity keys user/exercise/time/correct/suggested đúng. Duplicate/missing/extra/source identity mismatch và known NaN phải raise, không drop/dedup.
- [ ] **Step 2 — RED:** `& $AktPython -m pytest tests/akt/test_prediction.py -q`.
- [ ] **Step 3 — implement:** Parquet shards qua DuckDB/pandas đúng schema spec §8, p float64 nullable; native p cast chỉ sau finite check. Counters history_available/global rank, used retained history, context_reset, zero-history-after-OOV, support và unique learners/items; fitted coverage khác output coverage. Shared `check_prediction_alignment(..., identity_keys=('user_id','exercise','time_done','correct','suggested'))` trên fixture/small batches, scalable SQL uniqueness/full-join cho complete run.
- [ ] **Step 4 — GREEN crash tests:** `test_incomplete_shard_is_not_counted_on_resume`, `test_complete_user_shards_are_not_exported_twice`, `test_changed_checkpoint_cannot_resume_predictions`. Commit shard/manifest atomically; checkpoint at completed user boundary để không duplicate khi learner qua shards. `.tmp` không glob vào metrics; output mới/namespace run riêng.
- [ ] **Step 5 — review:** coverage tổng expected=finite fitted+unseen null, no unsupported finite; null keys/a missing user cause failure. Không sửa BKT/GAM prediction file hoặc overwrite their outputs.

**Completion:** aligned complete row accounting, source identity stable, resume safe. **Failure / rollback:** count/identity/provenance mismatch → export run failed/incomplete, không score/compare; giữ previous completed runs nguyên vẹn.

### Task 11: Metrics/common rows và uncertainty compatibility

**Prerequisites / goal:** Task10; reuse metric definitions, không reuse sai fallback coverage. Chỉ synthetic benchmark files ở unit tests.

**Files:** Create `akt/evaluation.py`, `tests/akt/test_evaluation.py`; không sửa `gam_kt/evaluation.py`, `paired_bootstrap.py`, existing bootstrap script/results.

**Interfaces:** `score_akt_shards(prediction_glob: str) -> dict`; `compare_common_rows(akt_glob: str, bkt_glob: str, gam_glob: str) -> dict`; `paired_stats_for_comparison(connection: duckdb.DuckDBPyConnection, common_view: str, *, reference: str, candidate: str) -> PairedFoldSufficientStats`. Common view là giao đã validate của một fold, chứa user_id/correct và prediction columns akt/bkt/gam; identifiers chỉ nhận allowlist, không interpolate arbitrary SQL. Bootstrap dataclass fields bkt/gam là legacy labels, map reference/candidate explicit và output model names/delta rõ; không relabel file gốc hoặc materialize full interactions thành Python dictionaries.

- [ ] **Step 1 — tests trước:** `test_metrics_and_unseen_coverage_do_not_follow_gam_fallback_flag`: null OOV/is_fallback=false vẫn count unseen/support0; known null/NaN/Inf/outside[0,1] fail. Fixture p=0,0.5,1 có labels0/1 verifies Accuracy ≥0.5, ECE15 bin cuối p1; AUC one-class=None/denominators rõ.
- [ ] **Step 2 — RED:** `& $AktPython -m pytest tests/akt/test_evaluation.py -q`.
- [ ] **Step 3 — implement:** AKT validation/coverage độc lập, gọi existing `gam_kt.evaluation.score_frame` cho vector **finite known rows** và chép phần metric definitions/results phù hợp; không tin coverage/unseen count trả từ GAM cho all AKT rows. Shard scorer group/report bằng DuckDB bounded reads và numeric vectors khi exact AUC cần; nếu memory thiếu thì BLOCKED exact AUC, không approximate silent.
- [ ] **Step 4 — common tests/implementation:** validate each side unique/full row identity trước intersection; common=AKT finite fitted ∩ BKT train_skill_students>0 finite ∩ GAM nonfallback finite. Recompute cả3 trên same rows, report attrition/pair masks và expected train-support matching; `test_intersection_recomputes_every_model`, `test_identity_mismatch_or_duplicate_is_not_hidden_by_inner_join`.
- [ ] **Step 5 — paired compatibility GREEN:** sufficient stats per learner/fold từ same common rows, legacy fields map tested sign candidate−reference; cùng user multiplicities cho cả model, seed20261030/replicates1000 khi chạy tương lai. Small-fixture compare `paired_cluster_bootstrap` với direct learner resampling cho Log Loss/Brier/ECE/Accuracy; exact AUC CI không có thì ghi BLOCKED riêng. Không chạy bootstrap thật trong implementation milestone trước full-fold evidence/authorization.

**Completion:** native/supported/common denominators và uncertainty API hợp protocol. **Failure / rollback:** coverage/mismatch/undefined metric bị giấu hoặc finite-known missing → STOP reporting, không đặt AKT subset score cạnh bảng BKT/GAM cũ rồi gọi matched comparison.

### Task 12: CLI/runner guards và Gate 2 review

**Prerequisites / goal:** Tasks1..11; chuẩn bị smoke/pilot/readiness, chặn full-fold/full-CV automatic execution.

**Files:** Create `akt/runner.py`, `akt/cli.py`, `tests/akt/test_runner.py`, ba config JSON và README Task12. Không sửa pyproject entrypoints.

**Interfaces:** `run_smoke(config: AKTConfig) -> RunResult`; `run_pilot(config: AKTConfig) -> RunResult`; `prepare_fold_readiness(config: AKTConfig, *, pilot_result: Path) -> dict`; private complete-fold orchestration nối selection/refit/export nhưng entry phải nhận explicit `authorization: dict`. CLI `preflight`, `smoke`, `pilot`, `fold-readiness`; `fold` command nếu có chỉ planning/dry-run trong milestone này, execution mặc định refuse; không `cv`/Test command. Unit tests toàn fake/synthetic; không Junyi training khi test runner.

- [ ] **Step 1 — tests trước:** `test_no_phase_runs_by_default`, `test_full_fold_and_cv_refuse_without_future_authorization`, `test_smoke_and_pilot_never_request_outer_users`, `test_config_cannot_expand_smoke_pilot_caps`. Parse configs schema, run_id new, out paths safe, locks/gates source-hash matched; objective gate JSON PASS không tự cấp authorization.
- [ ] **Step 2 — RED:** `& $AktPython -m pytest tests/akt/test_runner.py -q`.
- [ ] **Step 3 — implement explicit phases/configs:** smoke/pilot đều outer-train folds khác k=0, inner-user split; cohort SHA tag fixed `akt-smoke-v1|42|0|user_id` hoặc `akt-pilot-v1|42|0|user_id`, rank deterministic. Target cap chọn prefix chronological theo cohort order, không chọn bằng label/loss. `fold0.json` preferred inner-select-refit, outer_fold=0, H/T100, seed42, provisional model/training, execution_enabled=false. No automatic switch fixed-budget.
- [ ] **Step 4 — budget enforcement tests/GREEN:** clock/memory/steps guards trước phase và giữa batches, watchdog subprocess cho smoke; caps fail/stop bounded, no completed full-eval claim sau timeout. Logs command/config/source/data/assignment/env hashes, cohort user hashes/counts, status/error/retries và gate records. Không gửi cohort/labels ra remote service.
- [ ] **Step 5 — Gate 2 verification (future):**
  ```powershell
  & $AktPython -m pytest tests/akt tests/shared_kt -q
  & $AktPython -m pytest tests/bkt_baseline tests/gam_kt -q
  git diff --check
  & $AktPython -m knowledge_tracing.akt.cli --help
  ```
  Baseline regression nếu runtime AKT không có pyBKT thì chạy baseline tests bằng venv gốc với bytecode/cache ngoài protected env, **không cài pyBKT vào AKT để test pass**; record exact interpreter/results. Chỉ run tests không gọi historical pipelines/train/Test. Gate2 đòi mọi required CPU AKT parity/behavior/mask/window/OOV/loss/checkpoint/coverage tests pass và source/data manifests unchanged.
- [ ] **Step 6 — local readiness review:** tất cả primary command APIs documented là planned/generated sau Task12, no full fold/CV execute; record test output và code/source hashes của build đã verify. Nếu code đổi sau review, gate evidence bị invalidated cho phần liên quan, phải reverify.

**Completion:** Gate2 PASS có output thật, Gate1 identity còn đúng, runner safety/budget tested; đủ điều kiện đề nghị smoke. **Failure / rollback:** required skipped/missing tests hoặc false PASS, upstream patch chưa approve, Test/outer access → STOP trước real-data weight update, không bypass guards.

### Task 13: Bounded Development-only smoke — Gate 3

**Prerequisites / goal:** Gate1+2 PASS, execution authorization bao gồm đúng smoke bounds; không là full fold. Không viết thêm model khi bước này bắt đầu.

**Files:** Generated `experiments/akt/results/<smoke_run_id>/manifest.json`, `smoke.json`, checkpoint, predictions, logs; update `experiments/akt/README.md` với measured command/result. Model/config changes cần quay task có tests trước rồi issue run_id mới.

- [ ] **Step 1 — tests first evidence:** rerun required smoke guard test Task12 và checkpoint/alignment tests nếu build thay đổi; không thêm “test” mirror smoke summary. Verify cohort subset inner train/val, không outer users.
- [ ] **Step 2 — pin resource limits:** CPU FP32 B4, d32/heads4/blocks1, H/T100, ≤32 inner-train và16 inner-val users, ≤4096 targets **mỗi phía**, ≤20 optimizer steps, ≤120s train. Tổng smoke subprocess ≤300s, max RSS 2 GiB và available-RAM floor 1 GiB; đây là safety hypotheses, fail preflight nếu import/runtime headroom không đủ. Loader workers0, DuckDB512MB/threads≤2. No repeated seeds/config search.
- [ ] **Step 3 — chạy duy nhất command qua watchdog CLI:** Dùng config và authorization dành riêng cho run; authorization phải khớp phase, run_id, SHA-256 config, source/runtime/data identity và toàn bộ resource caps. Config template `smoke.json` giữ `execution_enabled=false`.
  ```powershell
  & $AktPython -m knowledge_tracing.akt.cli smoke --config experiments/akt/configs/smoke-task13-20261031-01.json --authorization experiments/akt/authorizations/smoke-task13-20261031-01.json
  ```
  CLI hiện không nhận `--run-id`; `run_id` được khóa trong config. Run-id nếu tồn tại phải từ chối/đổi sang ID mới, không overwrite. Complete train→inner-val→save/load→prediction cycle trong bounds; validate train/val actual rows/users/hash, no full dataset scan artifact re-generation. Authorization chỉ dùng được cho chính phase/config/source/data identity này; không tái sử dụng cho pilot, full fold, CV hoặc config khác.
- [ ] **Step 4 — đánh giá:** finite loss/grad, at least one nonzero gradient/parameter update, finite known p không trivially constant (range>1e-6 và variance>0 trên ≥2 distinct inputs), checkpoint reload eval allclose1e-6, expected/export/fitted/OOV accounting đúng. Không gate trên AUC phải hơn BKT/GAM hoặc training loss phải đẹp. Synthetic tests đã cover first/short/long/OOV dù sampled real cohort không có mọi case.
- [ ] **Step 5 — Gate3 report:** exact command/build/env, actual steps/time/RSS, p/loss/gradient observations, completed/bounded/incomplete/failed. Max-step limit là bounded success chỉ nếu save/val/export complete; watchdog/memory kill trước cycle xong là failure/incomplete. Gate3 PASS chỉ khi full bounded cycle xong, không trace leakage và caps được giữ.

**Completion:** smoke correctness evidence đo thật, không HPO. **Failure / rollback:** serious leak/numerical/metadata/parity issue → STOP pilot; resource failure báo điều kiện thiếu, không nới cap âm thầm. Giữ failed run riêng, không chạm old benchmarks/env.

### Task 14: Intended-architecture pilot và go/no-go — Gate 4

**Prerequisites / goal:** Gate3 PASS, authorization cho pilot trong caps, không tự chuyển full fold. Architecture candidate d256/heads8/d_ff1024, đủ L200 khác tiny smoke.

**Files:** Generated `experiments/akt/results/<pilot_run_id>/{manifest,pilot}.json`/checkpoint/predictions/logs; Create `docs/akt-pilot-readiness.md`; config pilot.json chỉ sửa nếu protocol amendment được log trước chạy.

- [ ] **Step 1 — preconditions/tests:** verify same locked build/gates và actual full architecture shapes; Task12 budget tests, no new tests chỉ để xác nhận value summary. Cohort hash-fixed ≤1024 train/256 inner-val, chọn từ inner scopes outer-train k0; report history/window length distribution, đảm bảo có intended L200 batches hoặc report BLOCKED representative-throughput claim.
- [ ] **Step 2 — lock caps:** ≤100000 train+val target rows **tổng**, ≤1 epoch train hoặc900s train (đến trước), tổng subprocess≤1200s; B4 FP32, worker0; RSS max2GiB/available floor1GiB như smoke trừ khi resource preflight chứng minh cần cap mới và user duyệt trước. Không cố full inner selection20 epochs hoặc refit ở pilot.
- [ ] **Step 3 — run duy nhất pilot command:**
  ```powershell
  & $AktPython -m knowledge_tracing.akt.cli pilot --config experiments/akt/configs/pilot.json --run-id pilot-001
  ```
  B8 chỉ được dùng trong **run riêng được duyệt**, resource-only comparison có log, không thay B giữa folds/selection/refit sau outer outcomes. Timeout partial epoch ghi bounded pilot resource evidence, không giả training complete hoặc chọn checkpoint tốt nhất từ outer.
- [ ] **Step 4 — measurements/report:** wall I/O/sort/load/train/val/export/checkpoint riêng; windows/s, valid-targets/s, context/pad tokens, actual optimizer steps, pre/post-clip gradients/fraction, finite p spread, micro losses/coverage; peak RSS, minimum available RAM, disk/temp spill, VRAM allocated/reserved nếu GPU được kiểm sau. Log CPU/hardware/thread/runtime, actual L distribution; source/data identity giữ nguyên.
- [ ] **Step 5 — estimate không headline:** dựa cost từng phase/window-length profile và target/window counts Dev đã audit, ước lượng **range** selection + fresh refit E + outer infer/I/O; nêu startup/cache/sort overhead, pilot sampling uncertainty và E chưa biết (range1..20 cho selection, refit1..20). Không ngoại suy tiny smoke hoặc lấy BKT/GAM replay time làm AKT training time. Năm folds outer-train tổng khoảng4×Dev targets/epoch trước inner/context expansion, không phải chỉ1× validation replay.
- [ ] **Step 6 — Gate4 decision:** PASS-feasible nếu test/smoke/pilot numeric/alignment giữ đúng, peak resource/headroom/disk đủ và estimated preferred protocol nằm trong budget user sẽ duyệt; BLOCKED/NO-GO nếu không. Nếu selection+refit quá đắt, đề xuất fixed E3 hoặc compute khác với tradeoffs, **không tự chọn**. Pilot metric không dùng chọn model; nếu có tuning thì register inner-only amendment/candidate budget trước outer runs.

**Completion:** measured feasibility report và preferred/fallback recommendation có evidence, chưa permission full fold. **Failure / rollback:** caps/throughput unrepresentative/gradient unstable → báo NO-GO hoặc inconclusive; không giảm population outer hoặc chọn checkpoint trên outer để tiết kiệm.

### Task 15: Readiness review outer fold đầu — Gate 5 STOP

**Prerequisites / goal:** Gate4 report hoàn tất, không còn scientific/compatibility blocker; chuẩn bị concrete review bundle cho user, không chạy complete outer fold.

**Files:** Create `experiments/akt/readiness/fold0-readiness.md`, `fold0-readiness.json`; update README với proposed future command và lý do gates. Không sinh full-fold model/predictions/metric artifacts trong task này.

- [ ] **Step 1 — kiểm coverage spec→evidence:** Gate1 source/runtime/license/lock; Gate2 output tests; Gate3 smoke full cycle; Gate4 intended-architecture measurements; frozen hashes và preservation của uncommitted work. Mỗi item PASS/FAIL/BLOCKED có path/hash/command, không chỉ checkbox tự điền.
- [ ] **Step 2 — generate readiness-only command sau Task12:**
  ```powershell
  & $AktPython -m knowledge_tracing.akt.cli fold-readiness --config experiments/akt/configs/fold0.json --pilot-result experiments/akt/results/pilot-001/pilot.json
  ```
  Assert không fit/infer outer hoặc đọc outer labels để score; chỉ cohort assignments/config/resource sizing và evidence đã có. Expected authorization.full_fold=false, authorization.five_fold=false.
- [ ] **Step 3 — concrete proposal:** exact build/lock/source/config/vocab-fit scope/inner split seed, checkpoint rule, expected outer cohort/population, output path/run ID, wall/RAM/disk budget và preferred select+refit. Fixed E3 nếu đề nghị phải nằm lựa chọn riêng để user duyệt, không enabled mặc định. Ghi command full fold sẽ chỉ hợp lệ khi future authorization được ghi lại theo run identity; không tạo authorization=true từ PASS gates hoặc script-generated JSON.
- [ ] **Step 4 — STOP xin full-fold approval:** trình bundle; không launch private runner/subprocess hoặc “first epoch” outer-training để kiểm thử ngoài smoke/pilot. Nếu upstream minimal patch cần thiết, bundle patch riêng phải được duyệt và gates1/2 reverified trước gate này.
- [ ] **Step 5 — ghi Gate6 tương lai:** ngay cả khi user sau này duyệt và hoàn thành fold0, phải review protocol/coverage/resources/resume/cost trước xin authorization 5-fold riêng. Không tự gọi cv/all-fold loops; không dùng score fold0 để tune rồi gọi cùng CV là unbiased. Holdout tiếp tục ngoài scope.

**Expected / completion:** readiness bundle reviewable + exact safe future execution proposal; Gate5 vẫn **PENDING AUTHORIZATION** ở cuối plan. **Failure / rollback:** any missing evidence/config changed/estimated budget không khả thi → BLOCKED, quay task liên quan trong authorized bounds, không đổi completed artifacts hay nới gate.

## 4. Bảng approval gates

| Gate | Evidence tối thiểu | Cho phép sau khi đã có execution authorization phù hợp | Điều kiện dừng |
|---|---|---|---|
| 1 — Environment/source | Exact pinned clean source + MIT/hash + compatible lock/env + successful CPU native import | Synthetic architecture/correctness work | Missing wheel/import/integrity; upstream patch chưa approve |
| 2 — Architecture/leakage | Native sum parity, actual masks, response/future/pad/user causality, OOV/global windows, mean gradients, split/checkpoint/export/metrics tests PASS | Đề nghị/chạy bounded smoke đúng phạm vi được duyệt | Missing/skip required test, leakage hoặc drift |
| 3 — Smoke | Complete bounded Development-only train/val/save-load/predict cycle, finite/nonconstant p, aligned rows/resources | Đề nghị bounded intended-architecture pilot | Timeout/limit trước cycle hoàn tất, numeric/leakage |
| 4 — Pilot | Realistic architecture throughput/L profile/memory + preferred select/refit cost range | Bàn giao full-fold readiness để duyệt | Insufficient RAM/time/disk hoặc representative evidence |
| 5 — Full fold | User explicit future approval cho exact build/protocol/budget/run | Chỉ complete outer fold được duyệt, không CV | Mặc định pending, objective PASS không cấp quyền |
| 6 — Five-fold CV | Fold review + user explicit future CV approval | Chỉ CV Development theo config khóa | Không auto-chain, không Holdout |

Upstream-file patch là **cổng bổ sung bắt buộc ở mọi giai đoạn**: stop, lưu failing evidence/parent SHA/đề xuất minimal patch và scientific effect, xin approval; chỉ sau đó áp dụng patch được duyệt và kiểm lại source/runtime/parity/causality gates. Không bypass bằng sửa vendored source dưới tên adapter.

## 5. Failure/rollback chung và Git persistence

Không destructive Git reset/clean hoặc xóa recursive source/output/environment. Task fail giữ run mới incomplete/failed cùng traceback/checkpoint complete trước đó; selection/export bỏ qua partial artifact. Chỉ resume exact identity; không resume thì dùng run ID mới. Revert code chỉ trong allowlist thay đổi của executor sau review, không discard uncommitted work khác. Không di chuyển historical artifacts; không touch protected environment để rollback AKT.

`docs/superpowers/` đang ignored tại `.gitignore:13`; plan này tồn tại cục bộ, không được stage/commit trong planning. Sau approval, người dùng quyết định force-add riêng từng approved spec/plan hoặc allowlist policy; không `git add -f docs/superpowers/` cả cây. Mọi future commit là action riêng có authorization; skill header không vượt giới hạn user.

## 6. Self-review planning (không phải implementation verification)

- Spec §1–5, upstream/metadata/fidelity: Tasks1–4; source nguyên vẹn và NonRasch không metadata features.
- Spec §6–8, contracts/sequence/window/OOV/output: Tasks4–8,10–11; global anchors sau barrier và current targets tách inputs.
- Spec §9–10, training/environment: Tasks2,8–9,12; mean vs sum và compatibility chưa validated được ghi rõ, fixed-budget conditional.
- Spec §11–12, behavioral tests/checkpoint/extensions: Tasks3,7–11; baseline không graph, future graph-off/capacity controls được giữ trong spec, không triển khai graph hooks.
- Spec §13–15, feasibility/approvals/provenance: Tasks12–15/gate table; six gates rõ, no full-fold/full-CV automatic task.
- 14 yêu cầu planning người dùng đều có task: source1; env2; parity3; encoding4; loader5; window6; causality7; adapter/loss8; inner/checkpoint9; export10; benchmark11; smoke13; pilot14; readiness15; runner/guards12 hỗ trợ các phase.
- Review Focus1→Task5 tests; Focus2→Tasks6/10; Focus3→Tasks8/9; Focus4→Tasks9/10/12; Focus5→Task11. Interfaces/types/paths và lệnh có prerequisite tương ứng; không claim tests đã chạy.
- Approval của revised design trong yêu cầu mới cho phép **lập plan**; task planning này không tạo môi trường, acquisition source, code, test outputs hoặc run artifacts liệt kê ở trên. Chỉ tạo file plan này và tự rà nội dung. Không dispatch agent để self-review vì writing-plans yêu cầu tự review.

## 7. Handoff

**DRAFT — PENDING PLAN REVIEW.** Đọc cùng approved spec và review các API/task boundaries, caps provisional, source-patch stop và six gates. Người dùng chọn execution method **Native** (executor tự làm task tuần tự, review cuối) hoặc **Subagent-driven** (implementer/reviewer độc lập theo task). Khuyến nghị Native cho milestone adapter nhỏ dùng nhiều shared interfaces; correctness được khóa bằng gates/tests và review, giảm chi phí handoff. Đây là lựa chọn chưa được xác nhận, không kích hoạt execution skill bây giờ.

Sau khi người dùng review plan và explicitly authorize phạm vi execution, mới invoke skill tương ứng; authorization phải ghi rõ source/env setup và bounded smoke/pilot nếu muốn chạy chúng. Complete outer fold và five-fold CV luôn cần future approval riêng. Dừng ở planning trong lượt hiện tại.
