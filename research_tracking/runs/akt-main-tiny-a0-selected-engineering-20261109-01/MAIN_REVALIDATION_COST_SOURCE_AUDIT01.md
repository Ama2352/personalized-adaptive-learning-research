# Chi phí kiểm toàn vẹn trong selected-only runner

Audit nguồn09/11/2026, không import/chạy benchmark, mô hình, tests hoặc Git. Không sửa production, auth hoặc allocation. Các counts dưới đây là suy luận đường đi source, chưa là throughput hoặc thời gian dự báo.

## 1. Một heavy dispatch thực sự làm gì

`research_selected_runner.py`55–56 gọi `run.guard()` → `execution.revalidate()` → `run.guard()`. `guard()`50–53 chỉ kiểm resource/clocks/outputquota qua `_resource`; đây là **guard nhẹ tương đối**, vẫn có syscall memory và chi phí thực tế.

`research_main_execution.py`325–333 revalidate gọi `_auth`239–261. `_auth` đọc/hash auth, đối chiếu toàn bộ caps/identities rồi gọi `_metadata`219–236. Mỗi lần `_metadata` gọi `_main_native_evidence`104–135 và `_corpus` của research_execution.py290–367. Sau đó revalidate còn kiểm lại typed corpus/condition seals và graph files.

Một dispatch thành công do đó có một genuine `preflight`, một genuine Gate reader và một full corpus metadata/hash audit. `preflight`178–196 trong authorization.py gọi `verify_upstream`; provenance.py32–55 gọi đúng10Git processes gồm HEAD/status/remote, ba cặp hash-object/rev-parse và tree. Ngoài Git còn nhiều công việc khác.

- `_main_native_evidence` hash executableGit, EOLproof, ba upstream files, runtime/lock/index. Gate reader gọi `gate2_build_hashes` một lần; return ở135 gọi lại map này một lần. Với map177 hiện hành, đó là **hai lượt full map,354source-file SHA calls mỗi successful dispatch**, chưa tính hashes khác.
- `_metadata` hash5docs, `_corpus` đọc/validate bank/plan/role manifests, stream-hash cả ba JSONL và kiểm DONE. Hash calibration bytes phục vụ integrity, không phải calibration labels dùng vào optimization/selection.
- Mỗi revalidate còn `self._corpus.assert_integrity()` và condition seal. Adapter có lớp kiểm riêng, gồm source_inventory/full context audits, named tensor checks và prediction state hashes. Các việc này không được tính chung thành “chi phí Git”.

## 2. Counts đường đi hoàn tất

Đặt E là số complete selected epochs thực sự chạy, S là số best checkpoints được save thành công trên đường đi hoàn tất. Fresh reload không train tiếp. Factory tạo actual guard đúng một lần nhưng nội bộ có **hai** `_metadata` calls, tại340 và362 qua revalidate.

| Callsite trong research_selected_runner.py | Số heavy dispatch |
|---|---:|
|Actual guard factory, main_execution340/362|2|
|Đầu runner199 và sau chuẩn bị context223|2|
|Hai fresh constructors, mỗi constructor94/103|4|
|Mỗi epoch233, train entry118, selection110/112|4E|
|Mỗi best save160/167|2S|
|Sau actual best restore255|1|
|Final raw selection110/112|2|
|Sau exports265 và thread restore269|2|
|Trước terminal output inventory287 và sau COMPLETE292|2|
|**Tổng trên successful path**|**15+4E+2S**|

Mỗi heavy dispatch này có một `_metadata`/native preflight/full `_corpus`, tức số Gitprocesses là10×(15+4E+2S). Tiny corpus8trainwindows/2batches mỗi epoch không nhân thêm heavy dispatch theo batch. `primitive._predict`253–311 và native train_epoch/resource_callback142–144 dùng `run.guard()` quanh các batches; callback/progress/Adam hooks không gọi full main revalidate. Chúng vẫn có adapter/tensor/context/resource checks riêng.

Frozen `EarlyStopping.observe` training.py365–374 chọn best ngay ở finite epoch đầu tiên, patience3. Successful completion sớm nhất là E4/S1, cho **33dispatch/330Git**. Nếu đi đủ20epochs thì S phải ít nhất7, chẳng hạn best tại1/4/7/10/13/16/19. Vì vậy **full20 successful path có109–135dispatch,1.090–1.350Git processes**, và218–270lượt map177, tương ứng38.586–47.790source-file SHA calls từ riêng hai map mỗi dispatch.

S0 không có successful full20/freshreload path. Formula successful không được áp vào failure prefix. Ví dụ nếu các training caps đã đủ nhưng vẫn dùng output16MiB hiện tại, first best save sẽ bị quota check162 chặn trước ghi checkpoint. Khi mọi check trước đó đều thành công, prefix này có11complete metadata dispatch/110Git, rồi fail. Đây là suy luận source, không phải một lượt đã chạy. Bản prelim97lower hoặc E20/S0 không mô tả valid path theo patience3 và đã được loại khỏi kết luận này.

## 3. Bằng chứng thời gian đã có và điều chưa biết

Actual guard-only receipt `main-selected-actual-guard01/outer-final.json` ghi10,923278299975209giây, worker result ghi9,169897899962962giây và20Git calls,0model/optimizer/teacher. Factory2metadata phù hợp count20Git. Lượt này audit canonical60, chưa train. **Không chia thời gian này cho20 để gọi là Git latency, không nhân với109–135 để dự báo tinyfit**, vì còn startup, publicreader, hashing, JSON/seals, provenance và owned lifecycle. Tiny10×84 có bytes/encoding/cache khác; chưa có component timings.

## 4. Output quota phải tách guard-only với fit

Current guard-only request giữ checkpoint upper limit64MiB, metadata limit1MiB và total output16MiB. `_save`159–167 yêu cầu `used+64+2×1≤total`, tức cần reserve **66MiB** ngay trước mỗi save.16MiB không thể qua điều kiện này ngay cả khi used0. Đây là allocation cố ý chỉ cho guard admission, không phải authorization cho fit.

Source giữ mọi best tại `checkpoints/epoch-N`, không xóa bản cũ. Với tối đa20best, conservative checkpoint envelope là20×66=1.320MiB, cộng metadata/journal/CSV. Không chỉ reserve một checkpoint cuối. Hồ sơ GRAPH11 binary_references.json ghi state.pt của một fixture handmade là26.704.993bytes. Nếu kích thước ấy lặp20lần sẽ là534.099.860bytes chỉ payload; đây là **minh họa theo fixture cũ**, không kích thước đã đo cho A0/84vocab mới. Metadata/core/state participation có thể khác. Actual tinyfit request cần quota riêng đủ upfront reserve và tổng retention, cùng measurement bytes thực tế, không tái dùng guard-only auth hoặc tự thay checkpoint limit để lọt16MiB.

## 5. Đo overhead trong future genuine tinyfit

Trước dispatch, ROOT cần chốt corpus10×84 thật/DONE/publicreader, fresh current runtime/Gate và một selected-only config/auth mới có full40Adam/13.440target exposures upper bound, đủ output/CP/disk/wall/RAM. Không giảm20epochs hoặc patience để ép resource. Source-only instrumentation proposal cho worker của lượt fit sau này là wrappers gọi **nguyên hàm gốc một lần**, giữ args/returns/exceptions và không thêm model/provenance calls.

Ghi counter cùng inclusive elapsed cho boundary/revalidate, `_auth`, `_metadata`, `_main_native_evidence`, `preflight`, `verify_upstream`, Gate reader, `_corpus`, typed corpus seal, adapter context audit và CP I/O. Dùng nested timing stack để báo exclusive segments hoặc chỉ báo inclusive mà không cộng chồng. Ghi file hash call count/bytes theo path class; journal theo completed boundary, không fsync từng byte hash. Pair mỗi record với epoch/phase và reserved/returned/committed optimizer counts. Giữ riêng model-forward/backward/Adam, window/context prep và checkpoint read/write timings sẵn có. Instrumentation overhead và hardkill phần chưa hoàn tất phải có scope, không biến partial thành full estimate. Đây là thiết kế đo, chưa có source wrappers hoặc benchmark mới.

## 6. Nếu sau đo cần đổi granularity

Bước đầu an toàn nhất là đo nguyên guard hiện tại. Một hướng sau đó để ROOT review là admission một run capsule gồm actual source/runtime/Gate/auth/lock/upstream/public inputs đã bind SHA, parse/public audit một lần, giữ immutable typed objects. Resource/target/ticket/named-parameter/context access checks vẫn chạy hot path. Full input/source/auth drift checks phải còn ở các critical boundaries đã chốt, đặc biệt trước/sau train, prediction, CP publication/restore và terminal. Có thể khảo sát tách identity/schema reconstruction khỏi byte-identity recheck để không lặp Git processes/JSON parse khi bytes không đổi.

Đó là **thay đổi guard contract cần explicit review**, không phải cache mặc định hoặc bỏ integrity checks. Caching file size/mtime đơn thuần không thay SHA, A→B→A vẫn là giới hạn race; immutable dataclass/read-only flag cũng không tự là cryptographic attestation. Nếu giảm Git HEAD/status/remote frequency phải xác định chính xác drift nào được phát hiện lúc nào, giữ negative mutation fixtures và failed-run semantics. Chưa có thay đổi nào được áp dụng trong audit này.

CUDA còn có blockers độc lập. Main spec188–193 và frozen simulator config hiện chỉCPU; checkpoint `_torch`183 yêu cầu CUDA unavailable. Không thể chỉ đổi device hoặc lấy software Gate/guard-only thành GPUready. Trước trả tiền cần CUDA-capable contract/source/runtime/owned origin proof được review, actual model/Adam/checkpoint parity và measured inference+training+integrity+I/O throughput cho đúng geometry. Không có giá GPU hoặc thời gian cloud nào được suy ra ở đây.

## Source pins của lượt đọc

|Source|SHA256|
|---|---|
|research_selected_runner.py|fcaa0c1850a0de391e26d4b3eb915fc91b3848f1e8d834898fa7fb788e868e20|
|research_main_execution.py|902018762fde6433a9bd9e33ce770df0057f6b0623327b8ff6b798e1faf4d881|
|research_runner.py|19627a1aa1bbf76069f1a07e0b56a3b5c79a1651863a31c37ac1c08c6cf62092|
|research_execution.py|5ea3d7283f6d8da6eab712d4e4fedb48cd41717f99cd3ae51fb7b8651b16c7b6|
|training.py|ca074a15dd5e45d016fd29d78b0b5ddbb0ccee3555b194699464d4cded6bf979|
|research_graph_checkpoint.py|f40b47e6ea0eb090b1edd3d4ffcb0b1feb5890aa238805aafd1d26ca4896c905|
|authorization.py|bd6be914e3b5049927ba6358ee4872097a46469fede9ad1b71ee63df951ac7f0|
|provenance.py|493d82af749baefcacec9ece0a7abe3297e64398eb4cd93c1d639ca41752cb59|
|P/main-selected-actual-guard01/outer-final.json|5a0a0b7e8d03f2f9fd3b5d123fea86f7071f3d4a5aa9069baeee6822ce18ff2d|
|runs/cgakt-research-checkpoint-engineering-20261109-01/binary_references.json|6fea45e23760d2210fdaa4a88ed2df2b5ba3fbead0f2bead991311266f412696|

Các Python sources trong bảng thuộc `src/knowledge_tracing/akt/`. P là cùng prep hiện tại. Chỉ đọc SHA/metadata của checkpoint inventory, không mở checkpoint/model hoặc corpus event/oracle data trong audit.
