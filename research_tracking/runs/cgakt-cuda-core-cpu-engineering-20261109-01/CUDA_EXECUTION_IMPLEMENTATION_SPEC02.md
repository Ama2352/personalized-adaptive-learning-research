# Spec02 — mở rộng CUDA execution cho Main selected-only CG-AKT

Ngày09/11/2026. Đọc source hiện hành và installed Torch2.7.1+cpu bằng PowerShell, không import/chạy Python, tests, model, Git, GPU hoặc cloud. Đây là đề xuất triển khai để ROOT chọn batch, chưa release production. Audit01 được đọc trước. Linux profile và additive Gate execution_profile đã có batch metadata154PASS/Windows, commit33a948b; không lặp lại thiết kế Linux đó. Actual Linux source/runtime/current Gate và actual CUDA target vẫn chưa được chứng nhận bởi batch này.

## 1. Các bất biến và quyết định phải chốt

Giữ protocol21/22/23/26, learner/role boundaries, full-population/null accounting, train80 graph/confidence frozen, predict-before-current-answer, selected-only terminal và original source verification. Giữ seed42; context100+target100/max_length200; d_model256/heads8/blocks1/d_ff1024/final_fc512/dropout.05; batch4; Adam lr1e-4/betas(.9,.999)/eps1e-8/weight_decay0; clipping1; max_epochs20/patience3/min_delta.0001. Không AMP, GradScaler, architecture mới, warm-start hoặc thay data. Required SAKT/GKT không được miễn bởi CUDA CG-AKT support.

ROOT cần duyệt execution recipe mới trước code bật CUDA.

- Đề nghị Adam foreach=False, fused=False, capturable=False, differentiable=False, amsgrad=False, maximize=False, decoupled_weight_decay=False. CPU legacy giữ foreach/fusedNone như hiện hành. CUDA explicit flags là lựa chọn backend/numerical execution, không phải phép biến đổi được chứng minh bitwise invariant với CPU/default CUDA.
- Đề nghị FP32, TF32 matmul/cudnn disabled, float32_matmul_precision highest, deterministic_algorithms=True/warn_only=False, cudnn.benchmark=False. Child có CUBLAS_WORKSPACE_CONFIG=:4096:8 trước CUDA context. Nếu target không hỗ trợ deterministic operation, STOP và review; không tự đổi warn_only hoặc fallback.
- Native AKTAdapter.step hiện gọi clip_grad_norm_ với foreach=None. Installed clip_grad.py64–65/88–91/165–168 có thể chọn foreach cho CPU lẫn CUDA. Gói nhỏ nhất giữ nguyên primitive này và bind profile clip_foreach=native-default-None; không gọi toàn bộ pipeline single-tensor. Nếu ROOT muốn clip_foreach=False, đó là quyết định execution bổ sung, cần mở model.py với keyword-only optional argument giữ defaultCPU và regression riêng. Spec này đề nghị chưa mở thêm file đó.

Đây là thay đổi execution có version, không đổi RQ hay phương trình/per-edge confidence/gate. ROOT có thể duyệt trong delegated engineering scope. Chưa coi các lựa chọn trên là methodology đã được thông qua hoặc dùng GPU.

## 2. Profile nhỏ, không đổi hash CPU lịch sử một cách ngầm định

Đề nghị một frozen ResearchCUDAExecutionProfile trong config.py, thuần stdlib, không module mới. Các fields đóng gồm recipe_id=cgakt-cuda-fp32-v1, device=cuda:0, initialization=cpu-default-generator-42-then-device, dtype=float32, seed42, Adam flags ở mục1, clip_foreach=native-default-None, deterministic/TF32/matmul/cudnn settings, max_vram_bytes explicit trong khoảng device_budget hiện hỗ trợ64MiB..2GiB. Actual lock/runtime/source và device facts là identity riêng, không hardcode phiên bản wheel hoặc tênGPU từ CPU host.

MainSelectedExecutionSpec và model/checkpoint API nhận cuda_profile optional keyword. None chỉ hợp lệ khi config.device=cpu; config.device=cuda bắt buộc exact typed profile. Khi None, conditional serialization phải giữ CPU identity/caps/schema legacy, không thêm key cuda_profile:null vào asdict-derived hashes rồi giả là tương thích cũ. Khi CUDA, normalized profile được thêm vào spec/caps/auth identity, adapter identity và checkpoint schema2. Không đổi AKTConfig dataclass defaults/hash chỉ để chứa các flags. Config validator chỉ tách device khỏi frozen scientific dict, nhận cpu/cuda cho simulator-research; main/adapter phải reject CUDA thiếu profile trước constructor. Legacy A0 runner _native_evidence vẫn CPU-closed, không cấp CUDA pilot từ việc config validator biết device.

Profile không phải execution grant. Actual Main authorization, native runtime/source/current Gate/corpus identity và global limits vẫn cần. research_admission.py chứa claims/context/runtimeSHA, không cần sửa để một claim trở thành CUDA authority.

Caller phải đặt workspace/device environment trước CUDA init. Runner kiểm exact giá trị và giữ before/after ledger cho các Torch backend flags mà nó thực sự đặt, restore trong finally cả khi lỗi; không strip env hoặc sửa global máy để tạo admission. Đây là owned process seed policy, không hứa bảo toàn training RNG của caller như inference fork. Cleanup là thu hồi owned process/context, không GPU reset hoặc can thiệp process khác.

## 3. Device placement và CPU initialization đúng với genuine loader

Current anchors model119–138, adapter230–252, upstream18–55.

Genuine build_native(configCUDA) đặt module globaldevice CUDA và giữ một-device-per-process. Trong outer torch.device(cpu), nn weights được initialize trênCPU bằng CPU default generator, rồi build_native thực hiện .to(config.device). Vì vậy không truyền replace(config,device=cpu) để dựng backbone rồi chỉ .to(cuda) ở ngoài. Cách đó lock loader process thànhCPU và để global mask/arange trênCPU trong upstream akt.py203–205/301–312.

Thứ tự tối thiểu đề nghị trong ResearchGraphNative.

1. Caller admitted một visible GPU, current device0, allocator cap và deterministic profile trước constructor. Dùng genuine loader cùng config.device=cuda, vẫn CPU ambient context cho init.
2. Dựng backbone, alpha0 và gate4 theo recipe hiện hành. Gate init vẫn fork CPU RNG rồi zero weights/bias, không ăn thêm backbone RNG stream.
3. Đưa toàn wrapper sang cuda:0, gồm graph parameters; kiểm mọi parameter FP32/đúng device. Cache _parameter_ids và adapter ownership SAU placement, không giả định Module.to luôn giữ object IDs.
4. Hash initial backbone từ validated canonical host copies. So shared initialization A0/A3 cùng seed/profile trên cùng target, không dùng fitted weights và không đòi CPU-vs-CUDA forward bitwise bằng nhau.

GIỮ CPU ambient context quanh Adam construction/step. Installed adam.py164–173 tạo noncapturable/nonfused scalarstep bằng torch.tensor không explicit device. Nếu thay bừa with torch.device(cpu) thành cuda, scalarstep có thể lênCUDA trái contract. CUDA parameters/inputs đã explicit device nên chạy CUDA trong CPU ambient vẫn hợp lệ. Native mask/arange trong upstream được .to(module.device) như nguồn. Wrapper forward CPU ambient có thể giữ, chỉ các guards actual tensor/parameter device đổi theo explicit profile.

_collate dùng selected device, _batch_sha kiểm đúng device rồi chuyển detach.contiguous CPU copy để hash cùng bytes/dtype/shape scheme. Không bỏ ticket/native/input/evidence seals. Các D2H copies/synchronization này nằm trong budget; chưa tối ưu bằng unchecked cache/version counters. Inactive/mass0 dùng same backbone forward, alpha0 vẫn giữ gradient khi graph active, mixed inactive slots trong cùng forward giữ semantics hiện hành.

## 4. RNG, optimizer và failure accounting

Construct entry tiếp tục seed Python/NumPy/CPU default generator42. Với đúng CUDA device0, seed CUDA current-device generator42 sau admitted initialization, không manual_seed_all hoặc implicit multiGPU. Fresh best reload là container mới, không reset global step/target/time counters.

predict_windows dùng fork_rng(devices=[0]) cho CUDA, devices=[] cho CPU; giữ inference_mode, mọi module mode và CPU+CUDA RNG sau cả failure. Không forward bằng autocast. Single visibleGPU và một-device-per-process là điều kiện trước module load, không fallback CPU khi CUDA unavailable.

Live Adam model/moments nằmcuda:0, nhưng noncapturable/nonfused scalarstep là CPU FP32 singleton. exp_avg/exp_avg_sq shape/dtype/device theo parameter. Giữ absent/empty state cho named participation0; initialized step bằng named participation, không global step của mọi parameter. Active1 gate zero tensor gradient vẫn là participation/state1; inactive branch gradNone/stateabsent hợp lệ. Không yêu cầu mọi backbone parameter tham gia mọi bước.

Adapter step gọi genuine AKTAdapter.step. Thêm synchronize(0) trước khi coi step completed/return tới training progress, và trước immutable snapshot/full inference receipt/terminal. Nếu asynchronous error xuất hiện sau optimizer posthook body_returned, giữ returned reservation nhưng không completed; mark failed/partial, không rollback hoặc reset. Không thêm synchronize trước/sau từng operation để làm thay đổi hotpath rộng. Existing primitive timings là host intervals với một số .item() sync, không đổi nhãn thành CUDA kernel timings. Whole synchronized wall và throughput được đo riêng.

## 5. Checkpoint schema2 CUDA, CPU schema1 giữ nguyên

Current CP anchors identity141–178, tensor187–215, ownership219–246, state validation263–303, RNG458–479, save544–578, restore697–747.

Tách strict serialized CPU tensor validator khỏi live-device validator. Live model/moments kiểm selectedCUDA, stepCPU; payload loadedCPU kiểm model/moments/step đềuCPU. Hash canonical bytes giữ FP32/dtype/shape/named order; một hash function không được mặc định cho CPU và CUDA lẫn lộn trước device validation.

Save phải explicitly clone model/moment tensors thành CPU snapshots trước torch.save. with torch.device(cpu) quanh torch.save KHÔNG tự di chuyển payload CUDA. Giữ named param layout, absent/empty/initialized representations, finite/nonnegative second moment, totalbytes và perparam participation. Đồng bộ target trước snapshot; clone chống alias live state. Tính hash trên chính snapshots sẽ serialize và kiểm live state không đổi quanh boundary.

CUDA identity/metadata/COMPLETE dùng schema2, đóng thêm execution_profile. CPU schema1 readers/writers hiện hành giữ wire/semantics. Runtime_profile_sha256 mới choCUDA bind lock/CPUthreads/execution flags và actual CUDA facts từ reviewed target runtime/controller, gồm Torch/CUDA build, device0/name/capability/totalmemory. Nếu driver chưa được thu thập thì ghi unknown và không claim driver equivalence. Không hardcode driver API hoặc gọi nvidia-smi trong production để lấp trường thiếu.

CUDA RNG envelope giữ Python/NumPy/CPU Torch cộng đúng một cuda record index0 + CPU ByteTensor từ get_rng_state(0). Tensorbytes của cả CPU/CUDA RNG tính vào cap. Validate CUDA RNG bằng isolated generator đúng device trước mutation. Restore vẫn weights_only=True/map_location=cpu, inspect JSON/hash/identity/limits trước load và toàn payload trước live mutation. Native strict model.load_state_dict rồi optimizer.load_state_dict đưa moments tới params; optimizer.py728–758 cố ý giữ stepCPU khi capturable/fusedfalse. Validate lại live devices, hashes và representations trước accept. Set Python/NumPy/CPU/CUDA RNG CUỐI CÙNG sau hooks/event sink/mode restoration. Failure sau mutation poison containers như hiện hành.

Không gọi completed-epoch state replay là iterator/lifecycle resume. Không resume partial epoch hoặc global authorization counter từ checkpoint. CPU checkpoint cũ không được đổi device label/schema để nhận CUDA.

## 6. Admission và resources — chỗ phải nối, không infrastructure mới

Main current242–246/309 vẫn CPU-runtime/config guard. Nhánh CPU giữ CUDA-hidden/schema2cpu/availablefalse. CUDA cần exact profile + configcuda + actual genuine schema2runtimecuda/availabletrue, current source Gate với actual execution_profile của host/interpreter, cùng Linux Git/source profile nếu ởLinux. Software Gate vẫn CPU/software scope, không là CUDA algorithm proof. Không dùng Windows Gate/CPU runtime đổi nhãn.

Reuse configure_cuda_budget đúng một lần trước constructor, không reset peak mỗi epoch hoặc best reload. cuda_budget_snapshot kiểm allocated/reserved và cumulative peaks tại boundaries, đồng thời giữ RSS/freeRAM/time/output limits hiện có. Proposed cap không được suy feasible từ CPU400MB. Helper allocator cap không bao driver/otherprocess/cloud billing. Peak_wset Linux có thểNone; outer phải ghi peak observed đúng sampled scope. Kết quả input/output/checkpoint/sync đều charge chung time; reserve cleanup và finalize trong actual ROOT controller sau.

Current Windows owned helper luôn hide CUDA, không làm visibleCUDA launcher bằng cách bỏ guard. Actual GPU/Linux owned PG controller là bước dispatch riêng được ROOT review, tái dùng existing pattern, không thêm daemon/productionlauncher trong batch này. Hardware/free-T4 choice và cloud authority vẫn tách khỏi code readiness.

## 7. Ba batch tối thiểu và acceptance

### A — profile và core device, chưa mở actual Main CUDA fit

Chạm config.py, research_graph_model.py và tests tương ứng; thêm typed optional profile, device placement/collate/hash/RNG/backend checks. CPU legacy regressions phải giữ. Không chạm condition/context/data/old A0 runner. Main CPU guard giữ cho đếnbatchC.

Pure tests kiểm exact closed recipe/profile, missing/wrong device/backend/unsupportedmultipleGPU/cap/config mismatch bằng metadata, CPU legacy hash/flags; không giả actualGPU. Native CUDA fixture nằm trong owned artifact controller riêng, không thêm pytest skip vào full CPU Gate. ROOT phê duyệt compute inventory trước actual run.

Core proof đề nghị tái dùng tiny geometry fixture hiện hành với một A3/Adam và3batches inactive→active→active, đúng3Architecture forward/3logical backward/3clip/3Adam/18targets nếu fixture asserts6target/batch trước run. Kiểm actual live grad/update, stepCPU/momentsCUDA, perparam counts, alpha0 và gate active1zero/active2update. Không thêm controlmodel/inference vào quota đó. Cần core parity forward/RNG check riêng có counter envelope được ROOT chọn; không gọi optimizer proof3steps tự đủ mọi core parity.

### B — CUDA epoch checkpoint

Chạm research_graph_checkpoint.py và test checkpoint; dùng profile đã freeze từA. Pure schema/hash/limit negatives không model. Native proposal reuse genuine valid CP fixture có8windows/48targets, full firstepoch2batches, evaluate, onecontrol active-batch continuation, fresh restore/evaluate và oneidentical continuation. Source hiện hành suy ra2model+2Adam constructors,6forwards,4logicalbackwards/Adamsteps; manufactured byte/RNG negatives không thêm NN body. Đây là workload đề nghị, chưa reserved hoặc executed. Giữ full phase receipt, không gán arbitrary direct3steps thành epochcomplete. SameGPU/profile continuation yêu cầu exact model/Adam/RNG/probability/loss parity; mismatch STOP, không tự nới tolerance. Không đòi CPU-vs-CUDA bitwise parity.

### C — Main selected-only wiring sau A/B được kiểm

Chạm research_main_execution.py và research_selected_runner.py + hai test files. Metadata normalized profile/caps/auth, actual device admission/budget/seed/backend, checkpoint profile/schema2 và final sync/receipts. Reuse original train_epoch/public reader/selection export; primitive._predict vẫn join labels sau prediction và common CPU loss metrics hợp lệ. Không mở legacy A0 runner/refit/calibration/systemselector.

ROOT cần một allocated tiny selected-only run mới sau genuine actual CUDA runtime/current-source software Gate, không dùng lại CPU tiny run làmCUDAproof. Số epoch/steps/targets/caps phải freeze từ fixture/actual request trước dispatch, không chọn dựa validation thuận lợi. Một run đó không là full9candidate matrix hoặc RQ completed. Batching ba phần để API coherent, rồi freeze và refresh software Gate một lần sau stable source; không full Gate lại sau từng dòng.

## 8. Blockers và phần routine

Cần ROOT adoption trước implementation CUDA enable cho backend flags/determinism/TF32/clip policy, initialization recipe, schema2 execution binding và same-target parity policy. Đây là lựa chọn numerical execution, không đổi graph equations/scientific hyperparameters. Không thêm ablation matrix mới để bù việc chưa chọn backend.

Routine engineering sau adoption gồm explicit placement/ownership, host-byte hashes, split validators, CUDA RNG serialization/restore, proper Adam devices, poison-on-partial, actual public runtime/Gate bindings và owned budget/cleanup. Actual CUDA wheel ABI, target driver/device/deterministic support/VRAM/throughput/cost còn là evidence gap cần đo, không thể giải bằng mock. Chưa có import/test/native/CUDA result trong spec này.

## 9. Source pins của lần đọc

| Source | SHA-256 |
|---|---|
|src/knowledge_tracing/akt/config.py|beb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f|
|src/knowledge_tracing/akt/research_main_execution.py|73bbacc8c8bd196cc9d3eeb7e3ac65f27a51f3a52fa8d3fe83d14dd87ac8c7aa|
|src/knowledge_tracing/akt/research_graph_model.py|77e365e4ffc6861f34a9ae05cbca947f057be967389f74f75bf5caacc7ee2397|
|src/knowledge_tracing/akt/research_selected_runner.py|fcaa0c1850a0de391e26d4b3eb915fc91b3848f1e8d834898fa7fb788e868e20|
|src/knowledge_tracing/akt/research_graph_checkpoint.py|f40b47e6ea0eb090b1edd3d4ffcb0b1feb5890aa238805aafd1d26ca4896c905|
|src/knowledge_tracing/research_admission.py|b8601da03a972834cfd2f5596ea6a6b9c5759437796b4f4b65720f7abc1a92f2|
|src/knowledge_tracing/akt/device_budget.py|79d6dff68f0cc36ec94c5f92097f5bdfe94f4f367386e989c03543d9a8dc4906|
|src/knowledge_tracing/akt/upstream.py|c31715c7659470b6d2e839512f2f9ac1f9b83023a9ba1dbfb6db12d4dd687515|
|src/knowledge_tracing/akt/model.py|e40b068bc305d0157a03f4baea3cd8e06c5777611c492f02fb65f792760e9e9f|
|src/knowledge_tracing/akt/research_runner.py|19627a1aa1bbf76069f1a07e0b56a3b5c79a1651863a31c37ac1c08c6cf62092|
|src/knowledge_tracing/akt/research_execution.py|5ea3d7283f6d8da6eab712d4e4fedb48cd41717f99cd3ae51fb7b8651b16c7b6|
|src/knowledge_tracing/akt/authorization.py|bd6be914e3b5049927ba6358ee4872097a46469fede9ad1b71ee63df951ac7f0|
|src/knowledge_tracing/akt/tensors.py|688fb915f8aa4958f47ee541e9ed92be577c0e14bc9c29e1d969be94863a4867|
|scripts/akt/check_runtime.py|4f5be1c58db40cd8875865275bb50f0b8171dc781615d4ce9f862ca598c1f795|
|tests/akt/test_research_graph_model.py|579359ff7b8ac64a75f9a343200724091d0d5b78af9a87e3d33ad023f1742ffc|
|tests/akt/test_research_graph_optimizer.py|5bdc3e5373c04a8f0a6199628b00461039e51c35bbfab8186f46a2ce342f4afc|
|tests/akt/test_research_graph_checkpoint.py|332c48af10eb983433117fe994a92fccf628866e04fb24f83390a5e6ce11045e|
|tests/akt/test_research_main_execution.py|f7ed9b4dc7d28c54e3899089c5db8876d2f0fd4bf9532a901fa5eaef46431e55|
|tests/akt/test_research_selected_runner.py|05f85bd487e93fca925f568fdb326852dc9bcc07ef0d32f994e4051dd03fdeaa|
|tests/akt/test_cuda_budget.py|1210c26cdee9d9183a81ff643dfc278793a2d034623e5b1378055e4e93f13a5e|
|.venv/Lib/site-packages/torch/optim/adam.py|dca23a7bfdf3a086292528269b815df7fba9f0cf764a18e84b26b3fee2c7147c|
|.venv/Lib/site-packages/torch/optim/optimizer.py|59118a947ba542b6ef8c5e3075c87a43ef16cd5442a94e08cdcc23930c7164b7|
|.venv/Lib/site-packages/torch/nn/utils/clip_grad.py|d0e557d351fdae29109c46cb335884fb8fc9c13475e4127c863d293fa1c9d311|
|.venv/Lib/site-packages/torch/random.py|5419e3a0de3c7c3ebcccc72c987834a6f796cfe3837fb3d91a902b52930d5b79|
|.venv/Lib/site-packages/torch/cuda/random.py|0954f8337cf1f8746f9eb84e993fdc4b8f5308a5e202fbf76ddffaa1df937489|
