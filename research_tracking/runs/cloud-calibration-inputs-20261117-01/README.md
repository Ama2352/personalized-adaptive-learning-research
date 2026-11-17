# Đầu vào tối thiểu cho calibration Junyi trên cloud

## Kết quả kiểm local

`INPUT_PLAN02.json` giữ danh sách đầy đủ **177 file, 134.424.683 byte**, khoảng 128,20 MiB. Mỗi file có đường dẫn repository, kích thước và SHA-256. Chỉ đọc/hash các đầu vào đang có. Không sao chép model/dataset, không tạo ZIP thật, không gọi cloud/GPU và không chạy lại thí nghiệm dữ liệu thật.

| Nhóm | File | Byte | Vai trò |
| --- | ---: | ---: | --- |
| Calibration và provenance | 6 | 14.321.107 | Cache đúng 15.847 learner, 1.621.484 target, assignment, manifest, PREPARED/POPULATION và split manifest metadata |
| Portable export A0–A3 | 12 | 118.081.493 | Mỗi model giữ MODEL_INDEX.json, SUPPORT.zip và một checkpoint refit đã xong |
| Source và đặc tả | 159 | 2.022.083 | Module knowledge_tracing, sink/uploader, Protocol21 và recipe CG-AKT26 |

Hai source plan ghi hai thời điểm working tree. `INPUT_PLAN01` được đặt tên `INPUT_PLAN.json`. Plan02 tăng 602 byte do source của nhánh khác cập nhật trong lúc kiểm. **Root phải tạo/pin plan mới sau source freeze trước staging** và kiểm SHA đầu vào cloud. Hai plan trong bundle này được giữ làm hồ sơ kiểm, không tự coi là manifest cho mọi lượt chạy sau.

## Các file dữ liệu cần chuyển

- `artifacts/akt/junyi-cohorts/outer4-calibration-full-20261117-01/canonical.parquet`, 14.143.412 byte.
- Cùng thư mục có `assignments.parquet`, 52.569 byte và `manifest.json`, 122.998 byte.
- `artifacts/bkt_baseline/splits/manifest.json`, 272 byte. Đây là metadata nguồn, không chuyển assignments gốc hoặc interaction ngoài calibration.
- `research_tracking/runs/junyi-calibration-data-20261117-01/PREPARED.json`, 1.123 byte và `POPULATION.json`, 733 byte.

Cache được đối chiếu byte/SHA với manifest đã chuẩn bị. Cờ chứa train, selection, outer và Holdout event đều bằng false. Cache có đáp án calibration thật để export prediction và fit temperature sau đó. Không dùng phần này để chọn epoch hoặc fit lại model KT.

## Các model cần chuyển

Giữ nguyên đường dẫn dưới `experiments/akt/results/model-export-a<i>-refit-20261114-01/`.

| Model | Checkpoint | MODEL_INDEX.json | SUPPORT.zip |
| --- | ---: | ---: | ---: |
| A0 | 28.968.311 | 2.086 | 516.826 |
| A1 | 28.971.439 | 2.692 | 543.059 |
| A2 | 28.971.567 | 2.692 | 562.097 |
| A3 | 28.974.239 | 2.692 | 563.793 |

Checkpoint có tên `A<i>_JUNYI_REFIT.pt`. SHA checkpoint và SUPPORT.zip khớp MODEL_INDEX.json. SUPPORT giữ roles, mapping encoding80/90 và receipt, epoch plan, cấu hình, graph và confidence khi áp dụng. Không cần gửi lại các bản roles/mapping/confidence rời hoặc window cache TRAIN80/TRAIN90 nhiều GB.

SUPPORT được kiểm chỉ chứa tên metadata trong allowlist, member duy nhất và tổng giải nén tối đa 32 MiB. Loader inference tiếp tục kiểm inventory từng member, roles/phase/encoding/condition và checkpoint lineage trước nạp model.

## Upstream và các việc còn thiếu

AKT vẫn gọi `verify_upstream`, yêu cầu Git checkout thật, HEAD đúng commit, working tree sạch và remote chính xác. Cloud CPU/image phải clone `https://github.com/arghosh/AKT.git`, checkout `01b7e8d7d7c862cabc9467108e3e7f2555653a88` vào `artifacts/akt/dependencies/upstream`, rồi chạy kiểm provenance. Không chuyển `.git` local hay credentials. Chỉ sao ba file akt.py/README/LICENSE sẽ thiếu Git metadata mà verifier cần.

Root cần gắn worker GPU inference hiện hành và cấu hình runtime vào image sau source freeze. Source knowledge_tracing hiện giữ theo allowlist `.py` để bảo toàn các import và source identity, khoảng 2 MB. Không cần notebooks, paper PDF, test fixture, checkpoint trung gian, archive lịch sử, Holdout events hoặc source canonical Junyi gốc 249 MB.

Cloud first sink đã được nhánh khác nghiệm thu riêng. Gói này chưa xác minh source/input được stage đúng trên cloud, chưa nạp cả bốn model từ bundle remote, chưa chạy inference calibration thật và chưa fit temperature. Mọi đầu ra mới phải đi từ cloud Volume sang Drive qua sink đã kiểm.

## Builder và kiểm lại

`scripts/akt/prepare_junyi_calibration_cloud.py` có CLI chỉ tạo plan nhỏ, không có CLI tạo ZIP local. API `write_archive` dùng streaming, giới hạn 256 file, source/output chỉ cloud Volume hoặc `/tmp`, xác minh SHA trước và trong khi ghi. ZIP dùng STORE để tránh CPU nén lại checkpoint/Parquet vốn đã nén. Lỗi giữ ZIP chưa nghiệm thu trên cloud để điều tra.

16 kiểm thử tổng hợp đạt trong 0,16 giây tại `tests02.txt`. Bao gồm traversal, Windows drive path, ký tự điều khiển, tên quá dài, private/Holdout path, giới hạn byte, member trùng, pin mismatch trước ghi và source đổi sau preflight. Không dùng dataset/model thật trong pytest.

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/akt/test_junyi_calibration_cloud_inputs.py -q -p no:cacheprovider --basetemp=artifacts/akt/runtime/calibration-cloud-input-tests-20261117-04
.\.venv\Scripts\python.exe -B scripts/akt/prepare_junyi_calibration_cloud.py --plan research_tracking/runs/cloud-calibration-inputs-20261117-01/INPUT_PLAN03.json
```
