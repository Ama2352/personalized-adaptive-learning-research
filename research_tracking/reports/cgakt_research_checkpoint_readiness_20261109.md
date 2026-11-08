# CG-AKT: checkpoint complete-epoch CPU — nghiệm thu kỹ thuật09/11/2026

Gói GRAPH11 đã kiểm được lưu và restore model, Adam, ba RNG và module modes tại
một complete epoch thật trên fixture tự tạo. Đây là bằng chứng persistence CPU
và một bước tiếp diễn có kiểm soát trong **cùng process**, không phải selected-fit,
research corpus fit, fresh-process resume hoặc lifecycle resume.

## Điều đã kiểm thực tế

Native03 có16PASS/0failure/error/skip. Một epoch dùng đủ8windows/48targets qua
2batches; sau đó control và container mới restore cùng thực hiện thêm một batch
24targets. Hai batch tiếp diễn không hoàn tất epoch2 và bị từ chối cấp receipt
complete-epoch. Cả lượt có2backbone/wrapper/gate/Adam constructors,6forward,
4logical backward,4clip,4Adam bodies,7save/8load và1model/1optimizer restore.
Tổng actual supported training targets của lượt này là96, không96 học sinh.

Ở E1,47parameter có participation2,3parameter(alpha/gate) có1,6parameter có0.
Các parameter count0 thực tế thuộc nhánh backbone không tham gia forward này;
không được tạo fake moments hoặc ép mọi step bằng global2. Native Adam skip
grad=None nhưng zero tensor vẫn tham gia. Payload phân biệt absent/empty/count0
với initialized moments và đòi step đúng participation riêng từng tên parameter.

Fixture cố ý perturb Python/NumPy/Torch CPU RNG và đảo mọi module mode trước
restore. Assertions trực tiếp sau restore đều đạt, trước evaluation. Sáu payload
âm tính(hash/COMPLETE hợp lệ nhưng thiếu participated state, hỏng từng RNG hoặc
mode) bị từ chối trước cả model/optimizer mutator. Dtype float64 cũng bị guard
trước Adam body. Không đổi architecture, native Adam, hyperparameters hoặc recipe26.

E1prediction/loss/count exact; sau controlled continuation, modelSHA của control
và restored đều `97c7891f67fede71ccbc2b05a8388237bc454bab9dd30c6715093626777ac024`;
AdamSHA đều `6b4caf941f14d73a76d1055dee3047e79c537aaecef5448d6a0287e47f1ca08c`.
Kết quả không đòi loss giảm, alpha dương hoặc lợi ích graph.

## Lịch sử attempts được giữ nguyên

| Lượt | Kết quả nguyên gốc | Actual Adam bodies | Giải thích |
|---|---|---:|---|
| Native01 | Không có JUnit/result terminal |3|Monitor stat file `.pending` đã biến mất khi atomic publish; không lỗi RAM/training, không gọi là16tests fail.|
| Native02 |16setupERROR/0FAIL,35deselected|3|Một shared fixture bị inner cap512MiB, dù outer đã duyệt1GiB. Production resource guard chặn đúng trước update thứ tư.|
| Native03 |16PASS/0FES,35deselected|4|Inner fixture budget sửa đúng1GiB/free2GiB; source checkpoint không đổi.|

Tổng cộng10actual Adam bodies qua ba attempts. Pure02 và pure03 mỗi lượt35PASS,
nhưng là35case logic được revalidate, không70case mới. Monitor02/03 mỗi lượt5PASS
trên cùng5canary stdlib; không10logic mới. Các snapshots a2f/538 và0ff ban đầu là
lịch sử source/review, không được gắn ngược với kết quả thực thi hiện hành.

## Thời gian, tài nguyên và overhead

Native03 child43.350752s, native interval34.704402s. Stored outer49.5579507s là
**charged** gồm fixed5s cho canary; raw controller44.5579562s. Terminal observation
Root49.5635752s giữ riêng. Không cộng fixed5 lần nữa. Hai attempts trước giữ charged
terminal27.0467988s và42.5576678s; ceiling bảo thủ của cả ba là159.6044666s, không
reset lịch sử. Các pure revalidations là allocation riêng không neural.

Peak observed RSS634,617,856bytes, minimum available RAM4,178,722,816bytes của
native03. Đây là fixture gồm deepcopy/negative serialization, không dự báo RAM của
corpus. Actual metadata queries28,240đều trảFalse; không CUDA initialization/GPU run.

| Step | Real Adam body(s) | Tracker pre(s) | Tracker post(s) | Adapter optimizer_seconds(s) |
|---|---:|---:|---:|---:|
|1|0.0363|0.1264|0.1477|0.3198|
|2|0.0197|0.1198|0.1867|0.3328|
|3|0.0256|0.1478|0.1852|0.3638|
|4|0.0371|0.1167|0.2278|0.4055|

Có24calls full-state validation, gồm save/restore/negative cases và post-hook.
State validation nằm lồng trong post-hook nên không cộng các tổng lồng nhau.
Bookkeeping đang tốn thời gian đáng kể trong fixture này; đây không GPU throughput,
epoch benchmark hoặc bằng chứng main training đã đủ ngân sách.

## Boundary của API và phần chưa chứng minh

Format CPU FP32 `weights_only=True` dùng owned fresh paths và COMPLETE-last,
external markerSHA, byte/tensor caps; model+Adam/RNG/modes được validate trước
mutation. Loader final-attach đúng owned optimizer sau strict restore; lỗi mutation
poison/discard, không rollback. Không nhận generic pickle/callable; format không
ghi corpus/trajectory/truth/oracle và lượt kiểm không chạy teacher. Binary checkpoints giữ trong experiments, bundle
chỉ lưu metadata và SHA/size references, không copy `.pt`.

Identity pin recipe26, actual protocol21, train80graph/confidence, neural phase/
encoding/vocab, initial backbone, sources/profile. Metadata binding không tự chứng
thực corpus, runtime execution, main selector hoặc external freeze authority.
Operational run/output paths không làm sai numerical restore identity; producer
config/budgets vẫn lưu riêng. Inherited handmade config2GiB/free1GiB không bị sửa;
explicit train_epoch budget và outer monitor1GiB/free2GiB mới là giới hạn hiệu lực.

Chưa kiểm actual research corpus, main selected-fit/refit/calibration, sampler/
earlystop/global-budget resume, mid-epoch cursor, fresh OS process, cross-platform
byte/source portability hoặc CG-AKT efficacy. History fixture chỉ6events, không
bằng chứng long-history rollover100. Same-backbone graph-off không thay independent
trained A0fallback. Confidence scores không được gọi là P(edge true).

Nguồn bền vững sau closure: [native proof](../runs/cgakt-research-checkpoint-engineering-20261109-01/graph-checkpoint-native03__native-proof.json),
[JUnit](../runs/cgakt-research-checkpoint-engineering-20261109-01/graph-checkpoint-native03__junit.xml),
[lịch sử/source copies](../runs/cgakt-research-checkpoint-engineering-20261109-01/copy_inventory.json),
[timing scope](../runs/cgakt-research-checkpoint-engineering-20261109-01/timing_scope.json).
Trạng thái đóng gói do manifest của bundle ghi; report không thay integrity receipt.
