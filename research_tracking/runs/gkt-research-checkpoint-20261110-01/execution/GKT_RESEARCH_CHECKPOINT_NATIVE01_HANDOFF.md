# GKT checkpoint canonical và native28 — bàn giao nguồn

ROOT đã duyệt apply hai file mới. Không thay GKT model/trainer/data/kernel hoặc SAKT checkpoint. Chưa chạy native28, pytest collection hay test body.

## Apply đã đối chiếu

`src/knowledge_tracing/gkt/research_checkpoint.py` là byte-copy candidate d877dfebac8ad626902995c1627a855c3073be2638aaa061a0a2a692c8a9aa4b. `tests/gkt/test_research_checkpoint.py` SHAa6cf290b74afb537cbf73322a8f3a1925a42e0287c570bb17498447035143c43 chỉ đổi ROOT.parents2 và import canonical. Dynamic loader còn lại chỉ phục vụ helper fixture đã có, không load candidate alias.

`gkt-research-checkpoint-apply01/before.json` SHA8a8ff6907046dadd72d33734a796a4df0e51e110efdcf0718a99c529a629fb8a được ghi trước khi tạo canonical files. `after.json` xác nhận byte-copy, hai candidate và model/trainer không đổi. Canonical destinations trước đó đều vắng. Hai candidate lịch sử vẫn nguyên byte.

## Harness và packet

| File dưới P | SHA-256 |
|---|---|
| check_gkt_research_checkpoint01.py | 24e56725be63ab7c0b21d5e03d318b0a5e72274412ef23d95d8c9ac361d383ab |
| run_gkt_research_checkpoint01.py | 2f29ea60a6864bf6dad15463bd9850fd25ab6e5a0633e2735dcb2ed724d0c0bf |
| gkt_research_checkpoint01_packet.json | 9e7709b2a90e2684ddedb1b5e30f1ac65a2e9ecc61264da5f490a249d146e936 |

56 source pins và14 runtime pins đều khớp actual files. Nguồn của cả hai prerequisite được giữ đủ để so sánh before/after với packet mới. AST bốn file canonical/harness hợp lệ, không import Torch hoặc chạy body. 28 IDs được suy ra tĩnh, worker vẫn phải actual-collect đúng danh sách trước allocation fixture. Ba namespaces `gkt-research-checkpoint01`, `gkt-research-checkpoint01-owned`, `gcp01` còn vắng tại lần kiểm cuối.

Model11 actual receipt206adada39430061acd4aed4f2e75a47b2cae6b4e2f21cd91da4542a88367489 và trainer8 actual receipt0ff33d2672d6803526d5bb6878c3c829db8e007fdeb1664ec4bbb4b0540889f8 đều bắt buộc qua CLI và packet. Worker/outer kiểm accepted status, exact tests/0FES, source/runtime ổn định, cleanup Job0. Probe Job API6mẫu là chứng cứ của bộ đo, không thay nghiệm thu model/trainer.

## Hạn mức

Whole120s, owned tối đa116s gồm cleanup3s, worker110s và reserve outer4s. Admission4GiB, minimum available2GiB, sampled exact owned Job family1GiB và worker high-water1GiB. Thread2, CUDA bị chặn. Inner handmade training budget60s/1GiB/free2GiB giữ nguyên, không tự tăng khi có lỗi.

Planned native workload2 models/2 Adam,6 forward/sequence và6 backward/clip/Adam body returns,96 training target exposures. Ba complete-epoch calls gồm E1 full8learners×4events/2steps, control E2 cùng population và restored E2 cùng population. Control và restored logical cumulative counter đều4. Không cộng thành8 physical steps.

Serialization planned11save/13load, bao gồm10 authenticated malformed fixture artifacts. Save/restore API attempts có expected semantic rejections. Hai underlying model.load_state_dict returns gồm strict restore và fixture cleanup reset. Synthetic mutator failure không gọi underlying model loader. Optimizer restore1. State snapshots và các tensor âm tính không thêm neural update.

Worker giữ exact method counters, finite/nonzero gradients, actual postclip norm, changed parameter names và phase counters. Ba completed phases lưu model/BN state digest, Adam digest và advanced owned RNG digest. Hai E2 phải khớp tất cả. Native assertions kiểm direct caller-global RNG, saved modes, owned RNG và authenticated payload rejection. Những mục này đều còn chờ actual outputs.

File checkpoint dựng tay nằm duy nhất dưới basetemp mới, tối đa96files/32MiB, mỗi leaf8MiB. Outer chỉ ghi SHA/size references, không torch.load output hoặc copy checkpoint vào report. Không actual corpus, teacher, oracle, dataset, Holdout, cloud hoặc fitted baseline. Các read/write guards kế thừa GKT trainer02 đã được nghiệm thu, chỉ mở thêm quyền checkpoint dưới chính basetemp mới.

## Lệnh ROOT sau review

```powershell
& .venv/Scripts/python.exe -I -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_gkt_research_checkpoint01.py 9e7709b2a90e2684ddedb1b5e30f1ac65a2e9ecc61264da5f490a249d146e936 206adada39430061acd4aed4f2e75a47b2cae6b4e2f21cd91da4542a88367489 0ff33d2672d6803526d5bb6878c3c829db8e007fdeb1664ec4bbb4b0540889f8
```

Không tự retry. Khi chưa có child result, actual counts giữ UNKNOWN/null theo receipt. Checkpoint format chỉ là complete-epoch persistence cùng budget origin, chưa public selected producer resume, fresh OS process proof, refit/calibration orchestration hoặc research-fit authority. ROOT review/dispatch và nghiệm thu riêng.
