# Khoảng trống port GPU của AKT/CG-AKT — kiểm tra source ngày 09/11/2026

## Kết luận thực dụng

Sau Gate trên đúng source, việc GPU nhỏ nhất mà **entrypoint hiện tại** có thể làm là native AKT `cuda-smoke` d32 trên dữ liệu tổng hợp được context cho phép. Đây là kiểm thiết bị/pipeline, chưa là fit nghiên cứu. Đường AKT Junyi có model/tensor/checkpoint biết CUDA nhưng public full-fold vẫn bị khóa; pilot Junyi hiện là CPU. CG-AKT Grade10 hiện có kiểm CPU forward/backward/Adam và checkpoint complete-epoch/fresh-process, **chưa có execution profile, model adapter hoặc checkpoint hỗ trợ CUDA**. Không giải quyết bằng đổi riêng `device='cuda'` hoặc tái sử dụng runtime report CPU.

Đề xuất gói engineering tiếp theo: port **một primitive research CG-AKT FP32 có device contract rõ**, kiểm A0 và A3 trên cùng hình học/recipe đã chốt; sau đó port checkpoint/restore GPU và kiểm complete E1 → fresh process full E2. Chỉ sau các mốc ấy mới đáng cấp GPU để đo workload đại diện và lập trần thời gian/chi phí cho fit nghiên cứu. Không thay kiến trúc, effective batch, graph recipe, seed hoặc AMP trong gói này. Đây là đề xuất, không cấp quyền chạy/cài/cấp phát.

Phạm vi audit: đọc source/metadata và tính SHA bằng filesystem; không import Python/Torch, chạy test/model, đọc corpus learner/oracle, duyệt web, gọi Colab/Modal, cài gói hoặc sửa source. Note này không xác nhận trạng thái Gate hiện tại.

## 1. Entry points thực tế và ý nghĩa của Task14

| Bề mặt source | Điều thực sự có | Giới hạn đang chặn |
|---|---|---|
| `src/knowledge_tracing/akt/upstream.py:18–53` | Loader nhận cpu/cuda, kiểm availability và pinned upstream, gán module-global `device`, chuyển model sang thiết bị config. | Một thiết bị trong mỗi process (`:22–23`); kiểm CPU/GPU nên ở process riêng. Upstream nguyên bản có mask/arange/zero dùng global device (`artifacts/akt/dependencies/upstream/akt.py:204–205,301–327`), phải giữ loader routing, không patch dependency. |
| `model.py:18–66,85,120–143`; `tensors.py:29–69` | Native adapter và collator đã dùng config/device, loss/gradient/Adam có thật; export chủ động `.cpu().numpy()`. | `step` chỉ dùng perf_counter quanh các pha, không synchronize CUDA. Các thời gian forward/backward/optimizer đó không phải đo GPU kernel hoàn tất. Không suy throughput GPU từ CPU hoặc từ timing enqueue. |
| `watchdog.py:96`; `runner.py:318–372,670` | Public worker có smoke/cuda-smoke/pilot. CUDA yêu cầu context riêng, identity/auth/Gate và allocator guard. | `config.py:133–147`: cuda-smoke là d32, batch≤4, một epoch, ≤20steps, ≤8192targets tổng, native≤120s/wall≤300s; không phải d256 research benchmark. `context.py:48–105,189–194`: scope synthetic-development-only, một visible GPU, allocator64MiB–2GiB. |
| `config.py:149–159`; `experiments/akt/configs/pilot-task14-20261105-01-authorized.json` | Pilot d256 Junyi và config mang tên Task14 đã có. | Cả guard và config này dùng CPU. Tên file Task14 không chứng minh có Junyi GPU worker hay authority mới. |
| `runner.py:703–780,783–786` | Có private full-fold orchestration/selection/refit/export primitives. | `run_full_fold` public luôn PermissionError, kể cả authorization.full_fold=True; watchdog không có public full-fold execution. Không gọi private helper để vượt khóa. |
| `docs/thesis_recovery/TASKS.json:417–447`; `07_GPU_TRAINING_AND_COST_PLAN.md:53–66` | T14 trong registry là CUDA ladder/durability; có stage/run-spec dự kiến. | `scripts/akt/modal_plan_runner.py` được ghi là future, không tồn tại trong danh sách scripts/akt đã kiểm. Không tìm thấy Modal App/function GPU training entrypoint trong scripts/src. Stage table không phải launcher đã triển khai. Một số blocker T14 còn mô tả failure CPU cũ; không dùng nó phủ định các kiểm CPU mới hơn. |

`synthetic_device_probe.py:39–107` và `synthetic_recovery_probe.py` là probe riêng có nhánh CUDA; tài liệu `07...:19–23,121–135` ghi actual kitv12/T4 nhỏ trong quá khứ. Không đồng nhất kitv12 inherited/system-site-packages với isolated runtime/source/Gate/context mainworker hiện tại. Probe script hiện có cũng không thay public authorization. `scripts/colab_mcp_client.py` chỉ là transport, không phải research trainer.

## 2. Chốt CPU cụ thể của đường nghiên cứu Grade10

| File/line | Ràng buộc thực tế | Phần cần port nhỏ nhất |
|---|---|---|
| `config.py:160–187` | simulator-research frozen device CPU; d256, heads8, block1, dff1024, dropout.05, batch4 và optimizer/selection policy cố định. | Profile/phase CUDA tường minh, được admission riêng; giữ nguyên guard CPU cũ. Không sửa device trong receipt CPU hoặc nới tất cả phase. |
| `research_main_execution.py:81,127–134,191` | Main selected-only guard giữ CUDA hidden/schema2 CPU và frozen Grade10 CPU; reviewed Git profile hiện Windows-only. | Linux/GPU profile cần actual pinned Git/raw-byte/runtime receipt riêng; không đổi nhãn profile Windows thành Linux hoặc bỏ source check. |
| `research_execution.py:159,190–195` | Guard yêu cầu scope CPU; môi trường không expose CUDA; schema2 report.device=cpu và cuda_available=False. | Admission GPU riêng: actual executable/prefix/origins/lock/source/runtime + visible-device/VRAM/resource caps; không bỏ guard hoặc coi decision string là quyền. |
| `research_runner.py:334,409,418,485–489`; `research_selected_runner.py:97,141` | Collate/load/state assertions và outer context là CPU, runner từ chối CUDA visible. | Route thiết bị xuyên train/predict/reload và guard trước lazy model import. Phase-input/labels/selector/refit/calibration giữ nguyên. `research_selected_runner.py:21–27,97–98,195–253` đã có source graph selected-only dùng adapter/context/CP thật; không mô tả nó như còn thiếu adapter source, nhưng chưa có GPU execution proof hoặc main refit/calibration từ các proof CPU checkpoint. |
| `research_graph_model.py:78–84,125–134,159–171,298–304,338,362–373` | Ticket hash đòi tensor CPU và gọi numpy trực tiếp; backbone/alpha/gate/forward/collator là CPU; fork_rng(devices=[]) chỉ bảo toàn CPU RNG. | Backbone, alpha, gate và q/qa/targets/masks phải cùng explicit device/FP32. Dùng GPU-aware fork_rng và RNG construction policy; giữ branch initialization không tiêu backbone RNG. Audit digest cần bản CPU detached có giới hạn, không chuyển tensor forward về CPU ngầm. |
| `research_graph_model.py:196–199` | Residual zeros_like và gate features `base_logits.new_tensor(...)` đã theo tensor nền. | Có thể reuse; không cần thay toán feature/normalizer. Đo chi phí host→device/synchronization riêng, không gọi nó miễn phí. |
| `research_graph_context.py` | Index/evidence NumPy label-free, effective-window/OOV/global-rank/source bindings. | Có thể tiếp tục nằm CPU. Chỉ transfer các feature cần thiết sang model device; không đổi prefix/history advantage, hash lineage hay train80 graph/confidence frozen khi refit90. |

Do đó sớm nhất có giá trị **nghiên cứu** là sau port+acceptance primitive GPU trên đúng geometry d256 và sau khi đường graph selected-fit/export hiện có được admit/chạy/kiểm artifact trên GPU thật. Một CUDA-smoke d32 PASS chỉ gỡ rủi ro môi trường. Nó không chứng minh selected80/mainselector/refit90/calibration10 của A1–A3, và không tạo fitted research weights. Junyi item vocabulary/checkpoint không được chuyển sang Grade10 để rút ngắn đường này.

## 3. Checkpoint và resume: phần có thể reuse, phần chưa có

- Generic AKT `checkpoint.py:23–39,56–67,89–104` đã lưu model/Adam, Python/NumPy/CPU Torch và `cuda_rng`, load map_location theo device, chuyển RNG ByteTensor về CPU trước set_rng_state_all. Đây là primitive CUDA có thật. `synthetic_recovery_probe.py` kiểm continuous/interrupted nhánh riêng; không suy nó có named participation/phase ownership của CG checkpoint.
- CG checkpoint `research_graph_checkpoint.py:141–153,181–204,219–300,458–479,636,699–743` chỉ chấp nhận CPU simulator research/CUDA hidden; mọi state tensor kiểm CPU, hash numpy trực tiếp; RNG chỉ Python/NumPy/CPU Torch; save/load/restore literal CPU. Không có CUDA RNG/topology/optimizer device restore trong format này. Không gọi format f40 là CUDA-portable vì torch.load có tham số map_location.
- Port nên có version/profile thiết bị mới, không sửa bundle CP119/fresh50. Lưu payload portable CPU có thể là thiết kế hợp lệ nhưng phải chủ động clone/copy bounded, kiểm dtype/shape/finite/bytes rồi restore vào owned GPU adapter/Adam. Sau restore phải chứng minh parameter/moment placement thực tế; Adam scalar step placement tùy cấu hình runtime không được ép mù quáng “mọi tensor trên CUDA” hoặc “mọi tensor trên CPU”. Chưa có bằng chứng nguồn đủ để kết luận generic optimizer.load_state_dict sai trên CUDA; đó là acceptance cần đo.
- Giữ participation semantics đã kiểm: Nonegrad/absent state khác zero-gradient state; per-parameter Adam step có thể nhỏ hơn global hoặc vắng hợp lệ. Không sao chép giả định SAKT mọi parameter.step==global. Graph E1 phải full window/target ledger; fresh OS E2 phải cùng sampler/ordered-input ledger, không lấy partial update làm complete epoch.
- **Semantics Adam kiểm từ primary source local, không từ suy đoán GPU:** `.venv/Lib/site-packages/torch/optim/adam.py:164–185` chủ động đặt scalar `step` trên CPU khi capturable và fused đều false/off, còn exp_avg/exp_avg_sq/(amsgrad max) là zeros_like(parameter). `optimizer.py:729–757` khi load: key step chỉ được cast float32/param.device nếu capturable hoặc fused bật; nếu không thì trả nguyên value; các floating moment khác được cast theo dtype/device parameter. Vì vậy checkpoint portable CPU + noncapturable/nonfused GPU Adam hợp lệ có thể giữ step CPU và moments CUDA. Ngược lại, map_location='cuda' có thể đưa step lên CUDA rồi policy noncapturable giữ nguyên; không hứa loader tự chuyển step về CPU. Future port phải công bố save/load map policy, construct trong explicit device context và kiểm đúng per-key semantics; không move_all hoặc assert tất cả state cùng device. Nhánh noncapturable tạo step bằng torch.tensor không truyền device; default-device/context vẫn cần kiểm. Không bọc lazy Adam initialization trong context CUDA rồi mặc nhiên giả định scalar step còn CPU. Source version.py ghi local2.7.1+cpu: đây là code-level primary evidence, **không phải actual CUDA execution hoặc bảo đảm binary target giống local**. Sampler hiện ở `training.py:94–108,178` dùng Python Random/ReplayableWindowCursor với seed=config.seed+epoch, không biến thành CUDA RNG/array sampler khi port; full ordered sample ledger phải giữ nguyên.
- CUDA RNG thêm phải ràng visible topology, selected device và generator states; CPU/NumPy/Python/modes vẫn phải phục hồi trực tiếp sau deliberately perturb. CPU↔GPU bitwise trajectory không được hứa. Same-GPU fresh-process replay cần policy deterministic/tolerance công bố trước, giữ discrete/sample/identity exact; không tự thêm allclose để biến mismatch thành PASS. Graph-off exact parity là cùng GPU/cùng backbone và cùng RNG/dropout context, khác independent A0 system fallback.

## 4. Thứ tự proof và hợp đồng artifact trước khi dùng GPU cho fit

1. **Host/runtime proof**: descriptor mới của actual GPU host (warm/cold đúng trạng thái, source/ABI/target-tags thật), isolated project venv, đúng root/executable/prefix, selected lock+install/origin evidence, Torch build/driver/device compatibility đo thật. Lock Linux cu12644wheels lịch sử là candidate đã có CPU import/isolated install evidence, không tự thành actual GPU kernel proof. CPU report hoặc startup-hidden audit không đổi nhãn thành CUDA-ready. Gate hiện tại/source kit phải ràng đúng bytes; raw producer notebook/dependency bytes của corpus không được strip/rewrite rồi giữ SHA cũ.
2. **Bounded primitive GPU FP32**: một fresh approved profile, một visible GPU, tiny handmade A0/A3 đã biết shape; native forward/backward/clip/Adam finite, backbone/alpha/gate đúng placement và participation, graph-off same-backbone parity, no OOV rescue/future labels. Không teacher/corpus generation hoặc extra architecture search; counts/caps được Root duyệt trước. Native d32 smoke có thể làm bước phụ trước đó nếu thật sự cần gỡ môi trường, không đo đại diện từ nó.
3. **State/cleanup proof**: complete tiny E1 save → owned process mới restore → full E2, ordered target/input/sampler ledger, direct CPU+CUDA RNG/modes restore, model/Adam/readout parity với control, source pre/post, hash/byte caps, marker-last và parent reaped/cleanup. Readback/return artifact trước giải phóng host; chưa mặc nhiên có Modal Volume durability.
4. **Đo chi phí đại diện**: chỉ sau khi pipeline chạy đúng, giữ geometry/model/batch/protocol cố định và đồng bộ CUDA hoặc CUDA events ở ranh giới đo. Báo riêng host preparation/context/collate, transfer, forward/back/Adam, tracker/checkpoint/export, startup/return và VRAM allocated/reserved/peak. Không suy GPU throughput từ graph CPU for_windows API benchmark hoặc fixture vài chục targets; không mở rộng dữ liệu chỉ vì smoke PASS.
5. **Actual research run**: nguồn/corpus/role/condition train80, vocab/refit90 lineage, mainselector freeze trước mọi refit, complete selection/calibration exports và external exact allocation riêng. GPU port không cấp quyền realdata/fullCV, không chọn A2 làm eligible winner trái recipe26 và không dùng calibration/final labels chọn model.

Artifact tối thiểu cho mỗi stage: immutable config+approval/allocation+runtime/lock/source/Gate SHA; PID/process creation/owned cleanup; counts dự kiến và actual model/forward/backward/Adam/targets; all named parameter/batch device+dtype summary; wall postcheck/RAM/VRAM và failure counters giữ cả UNKNOWN; checkpoint metadata/COMPLETE/binary SHA+size refs; RNG/modes/participation + full coverage/query/OOV ledger; prediction export identity đúng target và không bỏ unsupported. Chỉ accepted khi tất cả điều kiện stage đạt; failure vẫn giữ artifact, không tự retry/fallback Modal.

`device_budget.py:1–24` giới hạn PyTorch allocator, không phải hard driver VRAM quota hay bill cap. Cần owned shutdown/timeout và account-level spend control độc lập trong bất kỳ stage cloud nào; note không triển khai hay cấp quyền chúng. Giá, GPU availability, throughput và tổng chi phí hiện **không đo trong audit này**; không đưa forecast số hoặc dùng giá planning cũ làm giá hiện tại.

## 5. Kết quả CPU đã có và giới hạn còn nguyên

Theo handoff Root, CP119 và fresh50 đã đóng, fresh50 commit56053e4: CPU complete E1 và full E2 fresh OS process đã kiểm; không phải graph research lifecycle/mainstage. Audit này không chạy lại hoặc xác nhận GPU bằng các kết quả ấy. Source selected-only đã nối graph adapter/context/checkpoint (`research_selected_runner.py`), nhưng các proof CPU checkpoint không chứng minh actual selected research fit. Khâu cần kiểm/hoàn thiện trước actual CG-AKT GPU research là admit/execute/accept selected-fit/export hiện có, external main freeze rồi refit/calibration orchestration, và profile GPU thật. T14 registry/07plan là lịch sử và kế hoạch, không phải bằng chứng mọi stage đã hiện thực. Chưa có lý do kỹ thuật để tiêu credits chỉ cho một invocation chắc chắn bị CPU guard từ chối.

## Nguồn source kiểm tại thời điểm ghi note

Các SHA dưới đây ghi đúng bytes đã đọc; không chuyển/copy source và không là runtime attestation. Các đường dẫn trong bảng tính từ repository root.

| Đường dẫn | SHA-256 |
|---|---|
| `src/knowledge_tracing/akt/upstream.py` | `c31715c7659470b6d2e839512f2f9ac1f9b83023a9ba1dbfb6db12d4dd687515` |
| `src/knowledge_tracing/akt/model.py` | `e40b068bc305d0157a03f4baea3cd8e06c5777611c492f02fb65f792760e9e9f` |
| `src/knowledge_tracing/akt/tensors.py` | `688fb915f8aa4958f47ee541e9ed92be577c0e14bc9c29e1d969be94863a4867` |
| `src/knowledge_tracing/akt/config.py` | `beb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f` |
| `src/knowledge_tracing/akt/context.py` | `73455648b43212c23282f6fa2f417329f5d9f81b831f88aa8bbbfc546fffca39` |
| `src/knowledge_tracing/akt/authorization.py` | `bd6be914e3b5049927ba6358ee4872097a46469fede9ad1b71ee63df951ac7f0` |
| `src/knowledge_tracing/akt/runner.py` | `a79dbcd8b5341eeddaf8a5606ed984209ef7786fdb8d70804f6619faf7ce2852` |
| `src/knowledge_tracing/akt/watchdog.py` | `b94fd1c6468a440138b26be4cdcdefecfb1087805db9eac4d419be9b3663ac2e` |
| `src/knowledge_tracing/akt/device_budget.py` | `79d6dff68f0cc36ec94c5f92097f5bdfe94f4f367386e989c03543d9a8dc4906` |
| `src/knowledge_tracing/akt/checkpoint.py` | `bc1a6fbdcaa55c864cb9f18d531dcede440f9cf364dc9025420615520394fc91` |
| `src/knowledge_tracing/akt/research_execution.py` | `5ea3d7283f6d8da6eab712d4e4fedb48cd41717f99cd3ae51fb7b8651b16c7b6` |
| `src/knowledge_tracing/akt/research_runner.py` | `19627a1aa1bbf76069f1a07e0b56a3b5c79a1651863a31c37ac1c08c6cf62092` |
| `src/knowledge_tracing/akt/research_selected_runner.py` | `fcaa0c1850a0de391e26d4b3eb915fc91b3848f1e8d834898fa7fb788e868e20` |
| `src/knowledge_tracing/akt/research_graph_model.py` | `77e365e4ffc6861f34a9ae05cbca947f057be967389f74f75bf5caacc7ee2397` |
| `src/knowledge_tracing/akt/research_graph_context.py` | `8bfe0dca095d1de6c898fd849be6c5d1ee7033dffc13c20b24c7857de92bb029` |
| `src/knowledge_tracing/akt/research_graph_checkpoint.py` | `f40b47e6ea0eb090b1edd3d4ffcb0b1feb5890aa238805aafd1d26ca4896c905` |
| `scripts/akt/synthetic_device_probe.py` | `95b5bce7a83ea088cea0e42289dcc03dc8e627c5a69fd99fac40766841381472` |
| `scripts/akt/synthetic_recovery_probe.py` | `8e5d61ac48faa35e7fbbe21d08e6e4573f9106fe03ccc290f2ba0b16e27945ea` |
| `docs/thesis_recovery/07_GPU_TRAINING_AND_COST_PLAN.md` | `d57f9a561f97b21be06e23aee59e75e83020672b6538dfdcdb9051fa71fb1a5c` |
| `docs/thesis_recovery/TASKS.json` | `013b822f4af44b7d74b793ae148750afc3d67d697e2268e81750904d9ec0bb3f` |
| `docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md` | `13a81ad6a5173e1f215e3df01f3917fcbc1cce128c87c93985b57af76faa353a` |
| `src/knowledge_tracing/akt/research_main_execution.py` | `902018762fde6433a9bd9e33ce770df0057f6b0623327b8ff6b798e1faf4d881` |
| `.venv/Lib/site-packages/torch/optim/optimizer.py` | `59118a947ba542b6ef8c5e3075c87a43ef16cd5442a94e08cdcc23930c7164b7` |
| `.venv/Lib/site-packages/torch/optim/adam.py` | `dca23a7bfdf3a086292528269b815df7fba9f0cf764a18e84b26b3fee2c7147c` |
| `.venv/Lib/site-packages/torch/version.py` | `d51e444df58269c4d10d5e5bcf7bcdb89a29f545cef5dc484a572952a46b8e66` |
