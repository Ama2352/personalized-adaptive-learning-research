# SAKT: delta strict Adam counter tại completed epoch boundary

09/11/2026 · **Targeted33 đã kiểm thu native CPU; không research fit.**

ROOT review sau khi đóng [bundle70 lịch sử](../runs/sakt-research-checkpoint-engineering-20261109-01/README.md) tìm thấy một gap có ý nghĩa: guard cũ cho phép Adam `step=1` khi cumulative progress ghi2 hoặc3. Với exact SAKTCore đang hỗ trợ, tất cả trainable parameters tham gia mỗi batch và optimizer state coverage đã được kiểm đủ; stale positive step sẽ làm bias correction khác khi tiếp tục. Vì vậy chỉ finiteness/positive/bounded step là chưa đủ.

Sửa mới chỉ đổi một điều kiện: mọi Adam state step phải **bằng đúng** `progress.optimizer_steps`. Không thay model, data, epoch loop, architecture, hyperparameters, loss hoặc selected-fit protocol. Closed70 và báo cáo31 cũ giữ nguyên byte;31PASS vẫn là kết quả của source cũ trong giới hạn đã ghi, không được đổi thành test failure hồi tố. Source cũ `1b074595…` /tests `0d9c4942…` có trong closed70 manifest SHA `378046f4605a431d4a404975cb46201f8b982d059736d34d329bf26ceacb4611` và ROOT báo đã commit tại `7f1d1fc`.

Hai regression mới sử dụng **second epoch đã có trong module fixture**: lưu/restore boundary với counters `(epochs2,steps2,targets64)` thành công, rồi copy artifact đó, chỉnh một parameter step thành1, re-sign metadata/COMPLETE trong fixture và yêu cầu từ chối trước model/optimizer mutation. Một test khác cung cấp wrong previous cumulative steps ở SAVE và yêu cầu từ chối trước tạo directory/serialize. Không cần thêm training epoch hoặc model constructor để kiểm hai trường hợp này.

Lượt native02 do ROOT chạy đạt **33PASS,0failure/error/skip**. Actual counters:2Core constructors,5forwards,3logical backwards,2Adam constructors,3Adam bodies,13save,23load,2model-restore và2optimizer-restore; reservation/body-return đều khớp. Hai regression mới không làm tăng native update/constructor inventory so với suite31. Hai lượt31 và33 là scopes kiểm khác revision, không64independent cases: mỗi lượt dùng3Adam bodies, **cộng6tiny updates lịch sử**, không xóa chi phí cũ. FES mới0, actual-corpus fit/fitted baseline đều false.

| Scope thời gian/tài nguyên | Actual |
|---|---:|
| Pytest XML duration |14,504s|
| Child controller |21,017403699981514s /83s|
| Stored outer prepublication |22,294452800008003s /90s|
| ROOT-reported terminal |22,2962247s /90s|
| Observed peak RSS |289.107.968bytes|
| Observed minimum available RAM |5.012.586.496bytes|

ROOT terminal acceptance được ghi riêng với stored outer value; không giả phần transcript là independent raw tool capture. Actual owned receipt có worker returncode0, cleanup accepted, active Job processes0 và handle closed. Memory bounds là cooperative telemetry, không hard OS quota; thời gian fixture không là throughput forecast.

Patch được chuẩn bị ở PREP trong lúc Gate39909 còn live; production giữ nguyên đến khi ROOT báo terminal và release freeze. Sau release chỉ hai file SAKT được áp dụng, byte-exact với proposed module SHA `40fa69b861fb93d565fb2a37a0f126509c5239e681fdf3a3c5ae022f3b6cb3c7` và tests SHA `e7a144ac5fafff4d90c2f0ae5613fbbd261db76f43c906d9aa61fed207e4a2c0`. Apply receipts ghi old/new SHA, không tự sửa Git hoặc closed artifacts.

Driver02/packet mới dùng exclusive output và basetemp02, cùng whole90s/owned≤87s gồm cleanup3s/worker83s, CPUFP32/thread2, max512MiB/free1GiB. Counter reservation/body-return được fsync; chỉ logical `torch.autograd.backward`, không double-count Tensor dispatch. ROOT-designated154source freeze03 SHA `b0030c112a9ea72c8aecdf7d86675ea575f47c962f7800f36ee581648051ae6b` được pin riêng với hai file SAKT ngoài map154. Đây là identity guard, không training permission hoặc tự promote current Gate.

Compact delta bundle dự kiến [`sakt-research-checkpoint-counter-delta-20261109-01`](../runs/sakt-research-checkpoint-counter-delta-20261109-01/README.md) tham chiếu closed70, không copy lại30component source files hoặc binary/cache. Chỉ source/test mới, patch/apply/controller/allocation/raw02 và metadata epoch2 positive/stale-counter proof được chọn; `.pt` chỉ có SHA/size references. [Outer](../runs/sakt-research-checkpoint-counter-delta-20261109-01/native_owned__final.json), [child](../runs/sakt-research-checkpoint-counter-delta-20261109-01/native_child__result.json) và [ROOT handoff](../runs/sakt-research-checkpoint-counter-delta-20261109-01/root_terminal_handoff.json) là các scope khác nhau. Links là aliases để materialize sau ROOT closure approval, không tuyên bố bundle đã đóng lúc soạn báo cáo.

Chỉ Adam roundtrip đã thực thi; SGD format vẫn chưa có execution proof. Không mid-epoch resume, full research resume, selected-fit/refit/calibration orchestration, actual corpus fit, GPU/cloud hoặc RQ efficacy trong delta này. Model/data/research-training và154sources của Gate không được sửa bởi delta; freeze154 là lịch sử identity tại targeted02, không training permission. Source/profile/counters vẫn là contract hợp tác; không chống caller giả toàn bộ receipt. Báo cáo31 và closed70 giữ nguyên, không rebase thành source40fa/e7a.
