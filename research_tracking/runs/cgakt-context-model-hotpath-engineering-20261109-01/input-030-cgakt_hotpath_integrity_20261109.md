# CG-AKT: integrity trên hot path, kiểm kỹ thuật ngày09/11/2026

Đã kiểm riêng **135cases dữ liệu/condition/context** và **25cases model**; cả hai
lượt PASS,0failure/error/skip. Tổng160cases là số kiểm phần mềm của hai scope,
không phải160lượt forward hay một thí nghiệm research training. Lượt native vẫn
chỉ có1backbone/1wrapper/1gate, **8Architecture.forward/5logical backward/
0Adam constructor/0optimizer step**.

## Thay đổi và các invariant giữ lại

Baseline context5a5ada91 và model7ed087 được giữ nguyên trong bundle lịch sử
context52outputs và core74outputs. Bốn source hiện hành:

| File | SHA-256 |
|---|---|
|`src/knowledge_tracing/akt/research_graph_context.py`|`8bfe0dca095d1de6c898fd849be6c5d1ee7033dffc13c20b24c7857de92bb029`|
|`tests/akt/test_research_graph_context.py`|`d54b188ce56fa913551ce54c33209151a1b9456fac0031c541930370471299a8`|
|`src/knowledge_tracing/akt/research_graph_model.py`|`77e365e4ffc6861f34a9ae05cbca947f057be967389f74f75bf5caacc7ee2397`|
|`tests/akt/test_research_graph_model.py`|`579359ff7b8ac64a75f9a343200724091d0d5b78af9a87e3d33ad023f1742ffc`|

Trước thay đổi, một batch train gọi7lần serialize/hash **toàn context index**.
Giờ `seal_for_access` full-audit cache tại attach và giữ root/header/record seals
theo process. Hot path kiểm header/source/root và hash các record/evidence thật
được chọn, cộng WindowInputs và exact one-use batch ticket. Native call có
expected evidence digest để bắt drift từ lookup→bind→forward. Không đổi math
parent-mean−0.5, confidence, alpha0/gate4, native six operations, initializer/RNG,
window/OOV geometry, loss objective hoặc optimizer policy của recipe26.

`assert_integrity`, `identity` và đường `for_windows` mặc định vẫn audit đầy đủ.
Model có `audit_context_boundary`; public model identity cũng full-audit.
`predict_windows` không full-audit ở mỗi call vì caller có thể gọi theo batch:
lifecycle phải bao **toàn prediction pass/epoch** bằng explicit full boundaries.
Lượt kiểm native này thực sự gọi boundary trước/sau đúng một whole inference.
Chưa thêm trainer/checkpoint/lifecycle để tự thực hiện nghĩa vụ đó trong research.

Tamper ở selected record bị chặn trước dùng; nested tamper ở record chưa chọn
có thể chỉ bị phát hiện khi record được chọn hoặc full boundary. Đây là kiểm
lazy có khai báo, không O(1)attestation mọi byte hay bảo vệ hostile caller. Nếu
boundary phát hiện drift sau optimizer mutation, phải giữ partial failure, không
claim rollback. Lượt này không có optimizer mutation; positive control alpha1
chỉ là assignment fixture để kiểm gradient như core trước.

## Bằng chứng dữ liệu:135PASS, không model

`graph-context-hotpath-pure04/`:66conditioncases và69contextcases, trong đó26
contextcases mới. JUnit và result ghi135PASS/0F/E/S. Stored controller
**12.7679038000s**, terminal ROOT **12.7690966s**, cap90s/pytest-child75s.
Cold-import canaries riêng xác nhận condition không load NumPy/Torch; context
load NumPy nhưng không Torch. Không corpus/teacher/model/optimizer được chạy.

Tests kiểm full/default và selected-access equality, nguồn/header/root/tuple
replacement, selected parent/query/observed-row/input drift, foreign seals,
lazy unselected mutation và full-boundary rejection. Full serializer được spy
để chứng minh fast lookup không gọi nó; không đổi assertion sang allclose.
Các kiểm geometry/global ranks/OOV cũ giữ lại. Process kiểm pure dùng subprocess
thông thường với timeout/reap, không có native worker Job/RSS quota được đo như
lượt native; không gộp hai mức giám sát tài nguyên.

## Bằng chứng native:25PASS,0optimizer

`cgakt-research-hotpath04/` và `cgakt-research-hotpath04-owned/` ghi exact25case
IDs.25=18corecases trước+7negative/controlcases cho hot path. Có kiểm native
off/parity, mass0, alpha0 gradient, mixed inactive slots, causal/peer invariance,
inference readonly và tamper trước/sau stub primitive. Stub primitive chỉ kiểm
orchestration; không chứng minh Adam body đã chạy. Đây vẫn là A3 với graph-off
trên **cùng backbone**, không A0 được train độc lập hoặc native A1/A2.

Observer ghi **0full-index serializer attempts trong hot regions**, còn
**61full payload calls/61returns** ngoài các regions: gồm preparation/attach và
explicit audits/negative controls. Vì vậy không nói toàn chương trình0full
audits. Region invocations:collate20,step11,native10,inference7; các số này gồm
cả call bị reject theo test, **không** là số NN update/forward thành công.
Inventory NN thực đo vẫn8Architecture.forward/5logical backward và5raw
Tensor.backward entries,0Adam constructor/step. Full audit trước/sau whole
inference mỗi loại1lần, held index/condition/encoding identities bằng nhau.

Stored child **13.6201884000s**, stored outer **14.5909762383s**, terminal ROOT
**14.5938191000s**; child80s,owned<=87s gồm cleanup3s,outer90s gồm final3s.
Observed worker peakRSS **278994944B**, minimum availableRAM **4623921152B**,
121samples; dưới1GiB và trên2GiB trong fixture này. Actual Job sau cleanup0;
method/runtime/environment restored. Thread2,Torch2.7.1+cpu; một upstream
availability query thật trả false, CUDA không initialized. Không claim0query
hoặc whole-library syscall attestation. Normal loader và10lệnh Git local thật
giữ nguyên; process-only fsmonitor/safe.directory/autocrlf config của core03
được kế thừa, không global Git config/source/filters bypass.

## Đính chính vận hành và giới hạn

Handoff message từng ghi nhầm basetemp `cgh04`. Frozen worker thực tế dùng
`artifacts/akt/local-tests/cgm01`; ROOT kiểm absent trước dispatch, giữ nguyên
worker đã review. `cgakt_hotpath04_basetemp_handoff_erratum.json` giữ đính chính
này. Không có một failed execution hoặc acceptance repair do lỗi tên trong prose.
Output attempt vẫn là `cgakt-research-hotpath04` và `...-owned` riêng.

Chưa có benchmark representative trong bằng chứng này: không lấy thời gian
25cases so với18cases cũ để suy speedup/cost. O(W)lookup và source-byte checks
vẫn còn, cần đo phù hợp quy mô; chưa tự refactor thành framework mới. Không
actual corpus, optimizer step, fitted baseline, checkpoint/resume/refit/calibration/
selector/OnlineSession, CUDA/cloud, hoặc main-training readiness được chứng minh.
Benchmark đang chuẩn bị phải có receipt riêng; chưa được dùng làm kết quả ở đây.

Archive mới dự kiến `cgakt-context-model-hotpath-engineering-20261109-01`, chỉ
hash/copy bytes đã có, giữ source4 trước/sau và raw logs. Hai bundle52/74 chỉ
được tham chiếu bằng manifest; không sửa/nhân đôi toàn bằng chứng lịch sử.
