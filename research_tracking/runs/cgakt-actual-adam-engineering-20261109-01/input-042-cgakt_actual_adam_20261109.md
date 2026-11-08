# GRAPH10: kiểm Adam thật trên CG-AKT fixture, ngày09/11/2026

Attempt02 đã được nghiệm thu: **một testcase PASS**, một A3/Adam thật,3forward/
3logical backward/3clip bodies/3Adam steps và18lượt target training. Đây là kiểm
optimizer engineering, chưa actual corpus/trainer/epoch selection/checkpoint hay
fitted baseline. Attempt01 cũng đã thực hiện3updates thật và JUnit1PASS, nhưng
**run bị reject** vì observer restoration sai; không được xóa failure hoặc tính
lượt01 thành0work. Tổng actual Adam updates hai attempts là **6**.

## Thiết kế hữu hạn và source

File mới `tests/akt/test_research_graph_optimizer.py`, SHA
`5bdc3e5373c04a8f0a6199628b00461039e51c35bbfab8186f46a2ce342f4afc`.
Model77e365e4, context8bfe0dca và helper fixture579359ff giữ nguyên. Kế hoạch
`CGAKT_ACTUAL_ADAM_CHECK_PLAN01.md` SHA
`1ed422550556e6cfcf31b89d711053e5ff56e9959218fa92f254274c7661ca76`
được giữ bytes gốc; không đổi native algorithm, learning rate, objective hay
scientific recipe26. Chỉ explicit replace resource `max_steps=3` trước constructor;
config native-work cap60s giữ nguyên.

Dùng bình thường `handmade()` đã freeze, không reload hoặc namespace giả. Bank84,
vocabulary quan sát3, mỗi window6tokens; config research256/context100/targetblock100.
Chuỗi batch cố định **inactive entry1→active entry0→active entry0**. Vì batch active
được dùng lại,18lượt training target gồm **12event target IDs khác nhau** của hai
learner trong fixture, không phải18quan sát độc lập. Hai attempts lặp cùng fixture,
không tăng independent research N. Không thêm inference/control model, manual
alpha assignment, corpus/teacher/solver hay checkpoint save/load.

## Actual optimizer/state assertions

Mỗi batch dùng graph collate/ticket và `adapter.step` thật, cùng một owned Adam
sở hữu mọi registered parameter. Test quan sát clip original đúng một lần/bước,
recompute live post-clip norm bằng FP64 readout của gradients FP32; không chỉ tin
diagnostic `min(pre,limit)`. Không sửa gradient để ép clipping hoặc ép loss giảm.

| Bước | Graph gradients | Graph Adam state step | Điều thực kiểm |
|---|---|---|---|
|1inactive|alpha/gate `None`|absent/null|Branch weights giữ0; backbone update thật|
|2active khi alpha0|alpha nonzero; gate **zero tensor**|1|Adam làm alpha khác0; gate weights/bias chưa đổi nhưng đã có state|
|3active lần2|gate weight/bias nonzero|2|Gate đổi thật nhờ alpha do Adam bước2 tạo; không manual assignment|

Backbone có ít nhất một tensor đổi ở **mỗi** bước; diagnostic ghi47tensor thay
đổi/bước trong fixture này. Mọi state counter được đối chiếu số lần parameter
thực có gradient, **kể cả zero tensor**. Không ép mọi backbone parameter tham
gia cả3 hoặc mọi parameter step==global3. Moment tensors/parameters finite, CPU,
đúng shape; target masks xác nhận6/batch. Reservation/attempts/ledger được export
trước terminal acceptance để không che partial work nếu có failure.

Live post-clip norms attempt02 lần lượt **1.0000018926**, **1.0000011296**,
**1.0000007977**; trong tolerance FP32 đã đặt trước `1+1e-5+1e-8`, không claim
chính xác<=1. Pre-norms1.8632642031/1.6040642262/1.6217477322 được quan sát, không
được tạo bằng scale nhân tạo. Các số này không là prediction/research metrics.

## Failure01 và sửa observer02

01: JUnit1PASS/0FES, model/Adam/3forward/backward/clip/steps thật đều return;
`methods_restored=False` nên overallREJECTED. Env/runtime restored, forbidden=[]
và Job cleanup0. Không rollback hoặc relabel01 thành accepted sau khi giải thích.

Source Torch2.7.1: `AdamW(Adam)` không own `step`; `Optimizer._patch_step_function`
có thể wrap parent `Adam.step` lúc constructor chạy. Observer01 lưu inherited
baseline **sau khi parent đã bị patch**, rồi kiểm child ngay trong reverse restore
khi parent còn tạm wrap. Điều này có thể cho false failure dù final inheritance
đã đúng.01 không có per-entry restoration records; không dựng lại record còn thiếu.

ROOT chạy riêng **5stdlib tests PASS**,0Torch/model: tái hiện false failure kiểu
Parent/Child, giữ own override, reject late inherited capture và kiểm mọi entry
kể cả khi restore có lỗi.02 capture mọi static baseline trước patch đầu, restore
toàn bộ rồi mới final-check resolved identity/own-presence/own-value. Dynamic
methods của actual AKT/Architecture chỉ được capture muộn khi là own method.
Actual02 có **30/30final checks true**, kể cả AdamW trở lại inherited original
Adam.step. Đây là sửa observer, không bỏ guard hoặc đổi model/test5bd.

## Thời gian, ngân sách và tài nguyên

| Lượt | Stored child | Stored native work | Stored outer | Verdict |
|---|---:|---:|---:|---|
|01|14.1920147000s|7.6777780000s|15.3174691200s|REJECTED observer;3updates đã xảy ra|
|02|13.0195320000s|6.6040610000s|14.3352365494s|ACCEPTED;3updates mới|

Terminal ROOT01 **15.3190763s**,02 **14.338291899999604s**. Pure5 stored
**0.3043836000s**, terminal **0.3168521000s**, nhưng charge bảo thủ **5s** vào
**trong** allocation90s của02. Native outer02 còn tối đa85s; owned deadline lấy
từ remaining budget, cleanup3s/final3s được giữ; child80s là upper ceiling,
native-work60s. Root dùng helper ownership hiện có, không thêm Job framework.

Receipt02 ghi new charged **19.33524009998655s** và cumulative charged
**34.65431779999721s**, dưới cap **105.3190763s** (old terminal+new90). Các field
được chụp ở thời điểm khác nhau: không gọi cumulative này bằng phép cộng các
terminal rounded (khoảng34.6574s khi cộng full5charge). Không reset old spend.

02 observed peakRSS **400715776B**, minimum availableRAM **4621434880B**,114samples,
trong guard1GiB/free2GiB của fixture;01 peak401412096B/free4894949376B. Cả hai
owned Jobs đã cleanup0 và handles closed.02 methods/runtime/env restored;37source
pins giữ trước/sau. Đây là monitor cooperative, không hardOSquota/cost forecast.

Original upstream loader/provenance và10lệnh Git local chỉ đọc vẫn thật; process
config exact safe.directory/fsmonitor/autocrlf như lượt core đã nghiệm thu. Mỗi
attempt có **1actual upstream availability query false**, Adam-extra queries
quan sát0, CUDA không initialized. `graph10_plan_cuda_query_erratum01.json` sửa
wording “không CUDAquery” của plan mà giữ bytes gốc: không giả query trảfalse,
không claim0query hoặc whole-dependency syscall attestation. Không GPU/cloud.

## Bằng chứng và giới hạn

Gói dự kiến `cgakt-actual-adam-engineering-20261109-01` giữ raw01/02, cả source
controller/packet thực dùng, pure5/helper/canary/ROOTlauncher, plan/test snapshots,
before/after SHA và erratum. Chỉ giữ snapshots tồn tại thực; không dựng lại prep
729/3eec chưa dispatch nếu không có bytecopy. Bundle hotpath41outputs chỉ được
tham chiếu manifest, không copy dependencies/venv hoặc sửa bundle cũ.

Đã chứng minh actual Adam trên một A3 fixture hữu hạn và hợp lệ của missing/
lagged per-parameter state. Chưa selected epoch, fitted A0/A1/A2/A3 main matrix,
research corpus fitting, restore/resume ownership, calibration, OnlineSession,
main-training throughput/cost hay kết quả RQ. Checkpoint là batch riêng sau đây;
không suy ra readiness đó từ1PASS hoặc từ việc archive metadata.
