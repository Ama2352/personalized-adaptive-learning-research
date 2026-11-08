# Core CG-AKT recipe26: kiểm kỹ thuật Windows CPU ngày09/11/2026

ROOT đã nghiệm thu attempt03: **18PASS,0failure/error/skip**, một backbone AKT,
một wrapper, một gate4→1; **8Architecture.forward,5logical backward,0Adam
constructor và0optimizer step**. Đây là fixture A3 cùng đường graph-off trên
**cùng backbone**, chưa phải A0 được train độc lập hoặc kết quả nghiên cứu fitted.

## Source và phần đã triển khai

Recipe được chọn tại [tài liệu26](../../docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md)
(`13a81ad6…faa353a`). Hai file mới:

- [research_graph_model.py](../../src/knowledge_tracing/akt/research_graph_model.py),
  SHA `7ed0878f844d67598a6b684be92e770ea98d9b57ebbdb6a67c89cfef65020150`.
- [test_research_graph_model.py](../../tests/akt/test_research_graph_model.py),
  SHA `dd1e0bae0374c90159837d97d0f09d3936faae3227bf214ede9b2ffe598e9a9e`.

Model nhận condition train80 và index observables đã seal. Context hiện hành
`5a5ada91…5c56c4d5`, condition `6678f04c…875cf0`; đọc manifest của
[condition bundle](../runs/cgakt-research-condition-engineering-20261109-01/manifest.json)
và [context bundle](../runs/cgakt-research-context-engineering-20261109-01/manifest.json)
để đối chiếu các kiểm dữ liệu trước đó. Bundle core chỉ trỏ manifest, không sao
lại toàn bộ13/52outputs của hai gói đó.

`ResearchGraphAKTAdapter` giữ toàn bộ backbone/alpha/gate trong `.native`. Message
là parent past-correctness mean−0.5, confidence theo từng edge, normalizer
max(1,sum observed confidence); alpha0 signed và gate sigmoid Linear4→1 zero-init.
Không bypass alpha0 vì phải giữ gradient. Graph-off/empty/mass0 đi thẳng native;
slot inactive trong batch hỗn hợp dùng output của cùng forward. Sáu thao tác
NonRasch backbone giữ theo source AKT commit `01b7e8d7d7c862cabc9467108e3e7f2555653a88`.

Adapter trả exact `AKTBatch` cho batch factory, giữ ticket một lần theo object và
payload, kiểm optimizer sở hữu đủ parameter, rồi tái dùng `AKTAdapter.step`
unbound. Lượt này **chỉ kiểm wiring step bằng stub**; không chạy Adam body.
Prediction dùng inference mode, khôi phục từng module mode/RNG và không đổi
state/gradient. Không giữ full phase/shard/trajectory trong model. Caller vẫn
chịu trách nhiệm truth sidecar chính xác; SHA/typed metadata là consistency
contract hợp tác, không corpus-origin attestation.

## Diễn tiến ba lượt: giữ nguyên failure

Logs/JSON/XML nằm tại `artifacts/akt/local-tests/akt-research-runner-20261108-01/`;
mỗi lượt có `cgakt-research-model0N/` và `cgakt-research-model0N-owned/` riêng.

| Lượt | Kết quả JUnit | Native đã thực hiện | Stored outer / cap |
|---|---|---|---|
|01|18setup errors,0body|Mọi counter0|4.0915434361 /90s|
|02|18setup errors,0body|Wrapper bắt đầu1 nhưng không return; backbone/forward/backward/optimizer0|5.1900269985 /90s|
|03|18PASS,0F/E/S|Backbone1/wrapper1/gate1;8forward/5logical backward; Adam ctor0/step0|7.4787712097 /90s|

01 dùng fixture bank28items, chưa đủ V1 **84items/28concepts×1050/1200/1350**.
Sửa fixture thêm các item chưa quan sát; vẫn chỉ quan sát `i0/i1/i2` ở1200,
vocabulary3 và tối đa2learners×6tokens mỗi call. Không nới validator, thêm event
hoặc đổi labels. Các snapshot trước sửa được giữ byte-for-byte.

02 gặp `verify_upstream` source-content mismatch vì môi trường Git cô lập đã
tắt system `core.autocrlf=true`; **rawsource không đổi**. ROOT kiểm Git config
và hash chỉ đọc, sau đó original `verify_upstream` PASS với process config:
fsmonitor=false, safe.directory đúng một physical upstream path, autocrlf=true.
Không sửa global Git config, source, Git filters hay bỏ validator.03 dùng đúng
cấu hình này; vẫn chạy original loader/provenance với10lệnh Git local chỉ đọc.

Bốn proof `windows_git_audit_shape01.json`, `upstream_git_env_preflight01.json`,
`upstream_git_eol_preflight01.json`, `upstream_verify_process_eol03.json` là
**preflight metadata**, không phải Model PASS. Windows audit trả raw executable
null cho shell=False; receipt giữ null, tách khỏi path lookup, không giả đó là
handle-verified Git process identity. Không nới whitelist thành arbitraryPopen.

## Kiểm đã qua và tài nguyên thực

18cases kiểm native graph-off parity với loss/probability/backbone gradients,
mass0 không tạo branch gradient, alpha0 giữ gradient khác0, alpha1 là assignment
fixture để có positive-control gate gradient, và mixed inactive slots dùng đúng
base của cùng forward. Có low-level current/future-response và peer invariance;
đây không là cách sửa hay khôi phục metadata của corpus lịch sử. Changed-window
admission, ticket/parameter ownership, wrong phase, source/recipe drift và exact
boolean enable cũng được kiểm trước forward. Inference giữ state/gradient/RNG
và các module modes; failure ở collation cũng khôi phục modes.

Stored child03 **6.8380186000s**, stored outer **7.4787712097s**; terminal ROOT
**7.4830612s**. Child timer80s, owned<=87s gồm cleanup3s, outer90s gồm final3s.
Observed worker peakRSS **277712896B**, minimum availableRAM **5426839552B**,
62samples; trong ngưỡng1GiB/2GiB của đúng fixture này. Giám sát là cooperative,
không hardOSquota hoặc dự báo chi phí corpus lớn. Job active sau cleanup0;
methods/runtime/environment restored. Torch `2.7.1+cpu`, NumPy `2.5.4`, thread2.
Source28pins và current allocation được giữ trước/sau.

Có đúng một actual upstream `torch.cuda.is_available()` trả false; CUDA không
initialized. Đây là0CUDAallocation được kiểm trong scope, **không** claim0query
hoặc whole-dependency syscall attestation. Raw Tensor.backward entries5 được ghi
tách khỏi5logical `torch.autograd.backward`, không dùng raw dispatcher để đổi
định nghĩa số backward.

## Giới hạn và bước còn thiếu

Chưa kiểm native A1/A2 hoặc A0 train độc lập; không actual research corpus,
optimizer update, epoch trainer, checkpoint/resume, refit/calibration/selector,
OnlineSession/fitted promotion, CUDA, cloud hay hiệu quả RQ. Config là research
geometry256/context100/targetblock100, nhưng sequence6tokens là fixture kỹ thuật.

Source hiện tại còn **7full-index JSON hashes mỗi batch train** và lookup toàn
windows lặp lại. Tiny PASS không giải quyết hot-path cost hoặc main-training
readiness. Memo `CGAKT_CONTEXT_INTEGRITY_HOTPATH01.md` lưu phân tích source;
ROOT ưu tiên bỏ full-cache scans, giữ boundary/selected-evidence audits trong
batch sau. O(W)lookup còn lại phải được đo ở quy mô phù hợp, không tự kết luận
thất bại throughput chỉ bằng asymptotic. Chưa apply patch tối ưu ở bằng chứng này.

Gói dự kiến: `research_tracking/runs/cgakt-research-core-engineering-20261109-01/`.
Archiver chỉ hash/copy receipts đã có, không chạy lại test/model. Manifest có
before/afterSHA và mapping alias khi hai snapshot cùng bytes; ROOT review/đóng
gói và Git riêng. Không coi việc archive thành công là research approval.
