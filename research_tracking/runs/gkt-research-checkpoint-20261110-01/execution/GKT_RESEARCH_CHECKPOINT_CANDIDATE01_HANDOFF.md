# Candidate checkpoint nghiên cứu GKT08

Ngày10/11/2026. Chuẩn bị nguồn để ROOT review. Chưa import candidate, chạy test, tạo model hoặc lưu checkpoint thật. Không áp dụng canonical.

## API và ranh giới

`research_checkpoint_identity(model, view, spec, optimizer, *, budget, profile)` nối recipe29, model/config/spec, expert graph/train80, adjacency, view/encoding/phase/corpus, actual nguồn, profile và budget đã cấp. `GKTCheckpointProfile` yêu cầu protocol/runtime/profile SHA, initial model SHA đã capture trước update và run reference. Factory đối chiếu protocol với public plan và file21 actual. SHA profile là consistency binding của caller, không runtime authorization.

`save_epoch_state(...)` yêu cầu receipt `train_research_epoch` complete và progress khỏe. Kiểm đủ population epoch, started=returned, không pending, counters/delta đầy đủ, model digest, source, budget và owned RNG. Tổng optimizer steps phải bằng số complete epochs nhân số batch của toàn phase. Không nhận phase prediction/calibration hoặc receipt partial/poisoned. Đây là kiểm nhất quán bằng chứng compute, không chứng minh receipt không thể do caller giả tạo.

`restore_epoch_state(...)` nhận fresh model có initial digest đúng, Adam owned rỗng và progress ban đầu đúng. Kiểm COMPLETE externally pinned, exact3members, size/SHA/schema/identity trước `torch.load(weights_only=True,map_location='cpu')`. Kiểm toàn payload trước `load_state_dict`. Nếu mutator hoặc postvalidation thất bại, progress poisoned và caller phải bỏ model/optimizer/progress đó. Không rollback.

## Trạng thái lưu

- Registered parameters và toàn bộ state_dict, gồm adjacency, ba BN running means/variances/counters và singleton counters. Variance/counter không âm, tensor CPU FP32 hoặc int64 đúng vai trò, exact keys/shape, tensor detached.
- Ordinary Adam theo settings recipe29 và exact owned parameter order. Mỗi tên có witness `absent`, `empty` hoặc `state` với step nguyên0..global count. Payload phải khớp witness được SAVE vào metadata đã ghim. Không dùng giả định SAKT mọi parameter step bằng global step. Witness là snapshot thực ở SAVE, không một ledger độc lập từng gradient.
- Moment hữu hạn, đúng shape/FP32, second moment không âm. Postrestore so sánh cả nội dung Adam, không chỉ step.
- Advanced `progress.rng_state` là luồng dropout thực. Initial dropout stream không phải registered buffer, nên identity ghim SHA của giá trị constructor hiện có và restore yêu cầu fresh constructor cùng binding. Không nhầm initial stream với advanced stream.
- Native module modes lưu đúng tên và bool, bắt buộc coherent như `_bound` hiện hành. Restore đặt lại modes. Không lưu recurrent hidden state vì mỗi epoch/batch dựng state từ đầu.
-19 counters của progress và source/budget lineage được lưu. Object IDs parameter/optimizer được bind lại vào container mới sau restore. Không restore object IDs cũ.

Python/NumPy/Torch RNG toàn cục của caller được giữ nguyên. Trainer dùng private Python Random(42+epoch) cho thứ tự learner và owned Torch stream cho dropout. Candidate không thay global RNG bằng snapshot của training process. Các direct assertions và continuation fixture dưới đây còn chờ chạy.

## Công bố file

Tái dùng bounded read/strict JSON và publish-new-file của SAKT/AKT hiện có. Có path guard riêng cho GKT. Checkpoint mới dùng exclusive directory, file pending và COMPLETE cuối cùng, fsync và readback bytes trước marker. Serialize dùng buffer giới hạn trước từng write. Không ghi đè hoặc sửa artifact cũ. Tensor/serialized/metadata caps bắt buộc, outer resource/time guard vẫn cần khi thực thi.

## Nguồn và kiểm tĩnh

- Candidate `gkt_research_checkpoint_candidate01.py`, SHA d877dfebac8ad626902995c1627a855c3073be2638aaa061a0a2a692c8a9aa4b,417lines.
- Test `test_gkt_research_checkpoint_candidate01.py`, SHA7fde629362f98d088df5aec7695dfff218c8fcb060af8a9a1caca97b53d86f00,304lines.
- Inventory27 nguồn trực tiếp/helper, SHA69cbf54d858e588d226f2d393890590abed161dbb3534b272a52423de2d99aff. Không phải allowlist runtime đủ để dispatch.
- Canonical model4b866ca058c281faa8d69671d118758a31f982d68628da853f15f613e6c6c861 và trainer305fccf1038f41751a1137444cb2be469baf6f15090e27dc1595334ce3cb19cc không bị sửa. Recipe29 SHA059c98909c38856afd830d1cd296ce8875682ba9c7c226ad923c432e4328ce64.
- Hai nguồn đã qua stdlib AST parse bằng .venv -I -S -B. Không import candidate/Torch hoặc chạy body. Bộ đếm AST đầu tiên dùng literal_eval gặp biểu thức chuỗi nhân64 trong decorator, sau đó sửa bộ đếm metadata để chỉ đếm AST list elements. Hai nguồn không đổi vì lỗi bộ đếm này.

## Kiểm tương lai đề xuất

28 cases tĩnh từ11 test functions. Chưa collection/JUnit/PASS. Gồm4 profile negatives,3 limit negatives,10 authenticated malformed payloads,4 participation-format positives và7 cases còn lại về scope/partial/poison/bytes/protocol/mutator/continuation.

Fixture dùng typed handmade corpus đã có, cập nhật protocol metadata về hash actual21 bằng public constructors/auditor. Source map ghi rõ metadata còn là handmade, không publication hoặc trained artifact. Không đọc actual corpus, oracle, dataset hoặc Holdout.

Workload nếu toàn fixture hoàn tất là2 GKT models/2 Adam, fullE1 trên8learners×4events rồi fullE2 control và fullE2 restored. Mỗi epoch2batches, tổng6 physical forward/backward/clip/Adam bodies và96 training target exposures. Logical cumulative restored/control count đều4, không phải6 cho từng model. Không thêm forward để kiểm parity, so sánh exact final parameters/BN buffers/Adam và advanced RNG. Modes khác trước restore được kiểm trực tiếp.

Kế hoạch serialization theo nguồn là11 `torch.save` và13 `torch.load`, gồm baseline fixture load cùng10 authenticated negative artifacts. Có1 successful owned restore,1 synthetic mutator failure và1 cleanup load_state_dict để reset shared fresh fixture. Các counter này là source plan, ROOT phải instrument và xác nhận actual nếu chạy.

Helper training budget hiện có60s/1GiB worker RSS/free2GiB, không được tự nới. Outer/native allocation và RAM admission cần ROOT review riêng sau khi model/trainer normal-entry native đủ bằng chứng. Gợi ý lệnh chỉ để review, chưa được thực thi và không kèm allocation tự động.

```powershell
& .venv/Scripts/python.exe -I -B -m pytest artifacts/akt/local-tests/akt-research-runner-20261108-01/test_gkt_research_checkpoint_candidate01.py -q
```

`started_at` và budget SHA được giữ nguyên, không tự reset cho attempt/process khác. Candidate chưa giải quyết chuyển wall-clock/cumulative allocation qua fresh OS process, producer selected-fit, stopper/best checkpoint, refit/calibration hay main lifecycle resume. GKT model/trainer hiện hành cũng chưa có native verification ở thời điểm chuẩn bị này. Không fitted baseline, numerical reproduction hoặc kết quả RQ mới từ bản nguồn này.

## Cập nhật prerequisite sau khi candidate đóng băng

ROOT đã nghiệm thu native model11 và trainer8 trên đúng nguồn model4b866/trainer305fcc nêu trên. Model receipt `gkt-research-model02-owned/final.json` SHA206adada39430061acd4aed4f2e75a47b2cae6b4e2f21cd91da4542a88367489. Trainer receipt `gkt-research-training02-owned/final.json` SHA0ff33d2672d6803526d5bb6878c3c829db8e007fdeb1664ec4bbb4b0540889f8 có8/0FES và owned cleanup. Bundle `research_tracking/runs/gkt-research-model-trainer-20261110-01/manifest.json` SHAac5e2fd0565aabf71c2b5fac3623f96c965e6bbf18a261c23d70818bd8c64340.

Cập nhật này thay trạng thái prerequisite chưa native trong các đoạn ghi theo thời điểm chuẩn bị phía trên. Hai nguồn checkpoint candidate và28cases không đổi, vẫn chưa chạy hoặc áp dụng. Model/trainer compute acceptance không phải nghiệm thu checkpoint, fitted baseline hoặc public producer resume.
