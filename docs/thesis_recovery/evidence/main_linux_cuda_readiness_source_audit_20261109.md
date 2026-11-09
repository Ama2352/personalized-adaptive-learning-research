# Audit source-only về Linux/CUDA của Main selected-only

Ngày09/11/2026. Chỉ đọc source và SHA, không import Python/Torch, chạy tests/model/Git, truy cập web/cloud hoặc đổi production. Các source177 hiện hành giữ nguyên. ROOT vừa báo một lượt selected-only CPU đạt7epochs, best4,14Adam và84raw selection targets. Đó là bằng chứng hữu hạn của Windows CPU path, chưa là Linux/CUDA hoặc full research fit.

## 1. Kết luận có thể hành động

Linux CPU provenance và CUDA numerical execution là hai gói khác nhau. Main guard hiện chỉ nhận Windows/CRLF profile. Graph model, selected runner và checkpoint hiện chủ ý chỉ hỗ trợ CPU. Cấu hình `device='cuda'` đơn lẻ sẽ bị từ chối qua nhiều lớp trước khi có một CUDA lifecycle hợp lệ. Đây là ranh giới hỗ trợ hiện hành, chưa phải lỗi của lượt CPU đã nghiệm thu.

Gói nhỏ nhất nên làm trước là nhánh Linux CPU provenance của `research_main_execution.py` và regression tương ứng, giữ nguyên model/optimizer/checkpoint CPU. Gói CUDA sau đó cần sửa đồng bộ config, model, runner, checkpoint và admission/resource binding. Không thể chỉ bỏ một CPU guard hoặc đổi map_location rồi gọi là CUDA-ready.

## 2. Linux CPU admission và owned launcher

| Source hiện hành | Hành vi cụ thể | Hệ quả |
|---|---|---|
| `research_main_execution.py`59–85 | MainGitProfile chỉ `windows-native03-v1`, executable Git Windows, proof EOL và ba raw upstream hashes cố định. `_git_environment` chỉ nhận win32, GIT_CONFIG_GLOBAL=nul/autocrlf=true | Không chứng nhận được Git Linux hoặc raw LF. Không dùng Windows EOL proof để thông qua Linux |
| Cùng file105–115 | Actual Git executable phải khớp fixed Windows binary SHA, kiểm ba raw CRLF sources và genuine preflight | Nhánh Linux phải có actual Git executable/source/normalization proof riêng, vẫn gọi original verify_upstream |
| Cùng file182 | Spec gọi profile validator với literal win32 | Phải phân nhánh platform/profile rõ ràng, không đổi label profile thành Linux rồi giữ body Windows |
| Cùng file127–131,191 | CUDA phải hidden, runtime schema2CPU/cuda_availableFalse, configCPU | Linux CPU có thể giữ nguyên các điều kiện thiết bị này sau khi có provenance hợp lệ |
| `windows_owned_worker.py`76,87,303–316 | Owned helper dùng Windows Job API và child env luôn hide CUDA | Không chạy được trên Linux và không cấp visible-CUDA worker. Không dùng helper này như generic GPU launcher |
| `authorization.py`126–195 và `upstream.py`18–42 | Public Gate/runtime readers và genuine upstream validator đã nhận runtime interpreter Linux; upstream hỗ trợ cpu/cuda và một device mỗi process | Có thể tái dùng public validators. Không cần clone loader, cache giả hoặc bỏ provenance checks |

### Gói Linux CPU nhỏ nhất được đề nghị

Chỉ sửa `src/knowledge_tracing/akt/research_main_execution.py` và `tests/akt/test_research_main_execution.py` ở batch production được ROOT mở riêng. Giữ Windows profile/env/byte checks như hiện tại. Thêm một Linux LF profile được review, bind actual platform, physical source root, Git binary SHA, upstream HEAD/tree/raw LF sources và proof receipt có SHA. Actual factory phải kiểm host/profile khớp trước data/model work. Không mặc định Git config Linux theo Windows và không tắt filters để né verify_upstream.

Profile mới vẫn dùng exact caller Git environment, source/runtime/Gate/lock SHA và original public validators. Cần actual schema2 Linux CPU runtime, lock/dependency/ABI origins phù hợp và Gate của current source population. Các bằng chứng Linux cũ của source khác chưa tự chứng nhận batch177 hiện tại. Không chỉnh report/index cũ hoặc coi Windows Gate05 là mới chạy trên host Linux.

Owned launch Linux là artifact controller riêng do ROOT review, tái dùng mẫu POSIX owned process-group/cleanup đã có trong hồ sơ Colab. PID/PG ownership, timeout/kill/reap/descendant-empty và actual receipt là điều kiện riêng của dispatch. `watchdog.py`187–205 chỉ kill direct Popen PID khi timeout, nên không thay thế proof cleanup toàn owned tree của selected-run operation. Không thêm daemon hoặc framework production mới.

Regression đề nghị trước native work gồm Windows mapping unchanged, Linux exact profile accepted metadata, cross-OS/CRLF-vs-LF/binary/source-root mismatch bị từ chối, unknown Git variables không bị strip để tạo acceptance, cùng public Gate/runtime/lock staleness trước constructor. Sau đó ROOT có thể duyệt một bounded Linux CPU engineering path riêng. Đây chưa phải quyền cloud/GPU.

## 3. CUDA model và runner cần sửa đồng bộ

| Source | Giả định CPU cần xử lý trong batch CUDA |
|---|---|
| `config.py`160–171 | Frozen simulator-research config chứa deviceCPU. CUDA cần execution contract/version được review, giữ scientific geometry/lr/dropout/epochs/seed, không lách phase |
| `research_graph_model.py`78–84 | Batch seal yêu cầu tensorCPU rồi gọi `.numpy()` trực tiếp. CUDA cần kiểm exact target device và hash canonical host copy có budget, vẫn giữ ticket/input tamper checks |
| Cùng file125–134,159–171 | Backbone build trong CPU context, alpha/gate tạo trênCPU, forward và parameter guardCPU | Phải có cùng device cho mọi registered parameter và tensors, giữ alpha0 gradient và same-forward inactive branch |
| Cùng file304,338 | Collate và AKTAdapter.step bị épCPU | Phân bổ theo explicit approved execution device, không fallback |
| Cùng file132,362 | `fork_rng(devices=[])` chỉ bảo vệ CPU RNG | CUDA inference cần bảo vệ selected-device RNG bên cạnh CPU. Giữ module modes và inference_mode |
| `research_selected_runner.py`95–102,141 | Seed chỉ CPU default_generator, construction/train_epoch trong CPU context | Thêm seed/RNG policy của đúng visible CUDA device. Không gọi manual_seed_all hoặc default CUDA ngoài approved phase một cách ngầm định |
| Cùng file153–155 | Runtime profile hash mới gồm lock và cpu_threads | CUDA identity cần bind device/backend profile tương ứng, không chỉ đổi config label |
| `upstream.py`18–42 | Một process chỉ dùng một device, genuine loader đặt module.device rồi model.to(config.device) | Giữ loader thật. Kiểm riêng fresh fit/reload, không warm-start hoặc đổi device giữa cùng process |

Đề nghị giữ CPU initialization recipe cho shared-backbone comparisons rồi di chuyển toàn wrapper sang approved device theo một quy tắc được chốt, trước khi cache parameter ownership. Cần kiểm actual parameter/tensor devices và initial backbone hash. Điều này chưa chứng minh CPU/GPU outputs bitwise bằng nhau. Không tự chọn AMP, TF32 hoặc kernel/backend settings trong audit này.

CUDA batch cần ít nhất `config.py`, `research_main_execution.py`, `research_graph_model.py`, `research_selected_runner.py`, `research_graph_checkpoint.py` và tests đúng từng module. `tensors.py`29–69 đã nhận explicitdevice. `model.py`25–64 chủ yếu dùng batch-device operations nên có thể tái dùng primitive, giữ objective và optimizer ownership. Không đổi `training.py` thành một loop song song.

## 4. Adam và checkpoint không được migrate mù theo device

Installed source được đọc là Torch2.7.1+cpu, không phải proof ABI của target CUDA wheel. Trong `torch/optim/adam.py`164–178, noncapturable/nonfused Adam cố ý giữ scalar `step` trênCPU, còn `exp_avg`/`exp_avg_sq` đi theo parameter device. `optimizer.py`728–758 giữ nguyên step khi load ở chế độ này và cast moments theo parameter. Vì vậy “mọi optimizer tensor cùng CUDA” là kiểm tra sai đối với backend này.

`research_graph_checkpoint.py`183–210,229,263–301 hiện yêu cầu CPU cho cả model/Adam/rng tensors. Bản CUDA cần phân biệt live model/moments trên approved CUDA, scalar stepCPU và canonical serialized CPU tensors. Giữ ordered named ownership, fullshape/dtype/finiteness, exact per-parameter participation, zero-gradient participation và absent/empty state hợp lệ cho inactive graph parameters. Không ép mọi parameter có step bằng global Adam count.

Save/restore hiện ở571,699–721 dùng CPU contexts/map_locationCPU. CPU map_location là lựa chọn staging an toàn có thể giữ cho checkpoint CUDA, nhưng phải validate CPU payload trước mutation rồi load vào live target containers qua native strict load/optimizer load policy. Không đổi map_location thànhcuda cho mọi tensor, không sửa bytes hoặc device metadata của checkpoint cũ để nhận quyền mới. CPU schema1/identity cũ giữ semantics của chúng. Bản CUDA cần version/schema hoặc execution-profile extension rõ ràng và rejection cho sai backend/device/runtime trước mutation.

### Backend Adam là quyết định cần review

`research_selected_runner.py`100 không truyền foreach/fused, nên param groups giữNone. Installed `adam.py`900–910 tự chọn foreach khi cả haiNone, tùy backend. Vì vậy khi sang CUDA, dispatch có thể khác CPU. Chọn explicit foreach=False/fused=False có thể làm behavior dễ kiểm hơn nhưng **không tự là numerical invariant**. ROOT cần review quyết định backend/protocol này và bind nó vào execution/checkpoint identity trước code. Không tự thay config/backend hoặc nới current guards ở batch này.

## 5. RNG, asynchronous timing và tài nguyên

- Checkpoint458–479 chỉ lưu Python/NumPy/CPU Torch RNG, restore743 cũng vậy. Nếu CUDA training có dropout, state của đúng CUDA device phải được lưu/validate/restore cuối cùng sau khi toàn model/Adam/modes đã qua kiểm tra. Cần bind device mapping và RNG schema, không lấy CPU RNG làm CUDA replay proof.
- `resources.py`10–20 dùng portable psutil RSS/freeRAM nhưng peak_wset là field Windows. Trên Linux `process_peak_rss_bytes` có thểNone. Không đọcNone thành peak0 đã đo. Có thể giữ instantaneous checks và outer observed peak theo polling, ghi đúng scope. Đây là phần chưa có historical process peak trên Linux, không phải lý do bỏ RAM floor.
- `device_budget.py`4–25 đã có single visibleGPU, allocator fraction, reset/snapshot allocated/reserved peaks và cap tối đa2GiB cho smoke. Có thể tái dùng đúng semantics trong approved GPU profile với budget explicit trước constructor và tại boundaries. RSS/freeRAM không thay VRAM. Allocator cap chưa là driver/cloud billing cap.
- `AKTAdapter.step`35–60 đo perf_counter ngay quanh calls. Trên CUDA đây có thể chỉ là enqueue latency vì kernels bất đồng bộ. Các `.item()`/CPU copies đồng bộ ở thời điểm khác. Không dùng các phase timings CPU hiện tại làm CUDA throughput/cost forecast. Cần sync selected device ở operation/terminal acceptance boundaries để lỗi CUDA hoàn tất trước COMPLETE, và quy định timing là host-enqueue hay CUDA-event time. Không thêm per-op sync tùy tiện rồi coi performance không đổi.
- Full state hashing/checkpoint validation dùng host bytes và nhiều finite/state checks. Chuyển tensor vềCPU để giữ integrity có chi phí sync/copy. Phải đo representative window/corpus throughput sau correctness. Tiny CUDA fixture chưa là main training readiness, và audit không bịa timing/VRAM feasibility.

## 6. Regression hữu hạn đề nghị sau ROOT mở batch

1. CPU baseline behavior, output schema và Windows profile tiếp tục qua các fixtures hiện có. Linux profile thuần metadata có positives/negatives nêu ở mục2. Không gọi CUDA hoặc fit từ các pure tests này.
2. Device mismatch/OOV/ticket/source tamper bị từ chối trước genuine forward. Same init A0/A3 trong cùng approved device profile, alpha0 còn gradient, inactive/mass0 dùng cùng backbone forward. Không đòi exact CPU-vs-CUDA outputs nếu chưa có tolerance/method decision.
3. Fixture một inactive rồi hai active Adam steps kiểm actual named participation. Inactive graphNone/absent hợp lệ, active1 gate-zero gradient/state hợp lệ, active2 actual gradient/update. Giữ scalarstepCPU/moments-device rule và backend flags đã review. ROOT phải chốt allocation mới trước actual steps, không dùng lại quota cũ.
4. Complete-epoch checkpoint save→inspect→fresh restore→raw prediction parity trên cùng CUDA profile. Wrong device/runtime/step-device/RNG/schema/participation bị từ chối trước hoặc poison khi mutation failure theo contract. Không suy sampler/lifecycle resume từ complete-epoch state restore.
5. Inference giữ CPU+selectedCUDA RNG và module modes, source/context readonly. CUDA unavailable/multiplevisibleGPU/overVRAM/latekernelerror không fallback hoặc COMPLETE. Old CPU receipts không được relabel CUDA.

Chưa có test hoặc native workload mới trong audit. Nên hoàn tất các targeted batches rồi freeze toàn source và refresh software Gate một lần trên đúng population, thay vì rerun full Gate sau từng chỉnh sửa nhỏ. Actual target discovery, genuine runtime/source/lock và device check vẫn cần riêng trước dispatch.

## 7. Source pins của lần đọc

| Source | SHA-256 |
|---|---|
| research_main_execution.py |902018762fde6433a9bd9e33ce770df0057f6b0623327b8ff6b798e1faf4d881|
| research_selected_runner.py |fcaa0c1850a0de391e26d4b3eb915fc91b3848f1e8d834898fa7fb788e868e20|
| research_graph_checkpoint.py |f40b47e6ea0eb090b1edd3d4ffcb0b1feb5890aa238805aafd1d26ca4896c905|
| research_graph_model.py |77e365e4ffc6861f34a9ae05cbca947f057be967389f74f75bf5caacc7ee2397|
| config.py |beb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f|
| resources.py |8c1e5970efb6aa9966a8f583e11172632426f3318d396c3e28d24b5d16b9c5ba|
| device_budget.py |79d6dff68f0cc36ec94c5f92097f5bdfe94f4f367386e989c03543d9a8dc4906|
| .venv Torch optim/optimizer.py |59118a947ba542b6ef8c5e3075c87a43ef16cd5442a94e08cdcc23930c7164b7|
| .venv Torch optim/adam.py |dca23a7bfdf3a086292528269b815df7fba9f0cf764a18e84b26b3fee2c7147c|
| .venv Torch version.py |d51e444df58269c4d10d5e5bcf7bcdb89a29f545cef5dc484a572952a46b8e66|

Những tên file đầu bảng nằm dưới `src/knowledge_tracing/akt/`. Installed Torch files nằm dưới `.venv/Lib/site-packages/torch/`. Các line refs là source tại các SHA trên. Không sửa source177 hoặc proof cũ khi lưu note.
