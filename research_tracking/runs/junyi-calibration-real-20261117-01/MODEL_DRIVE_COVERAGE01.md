# Chỉ mục model và checkpoint trên Drive

Rà soát ngày17/11/2026. Sau khi phát hiện13backup cũ thuộc owner Dương, root đã cho phép sao chép server-side sang Sang. Đã hoàn tất13/13file,471.348.196byte, kiểm lại SHA/byte/owner/parent của bản mới và source cũ. Không tải/mở payload ZIP/PT, nạp model, dùng Modal hoặc xóa nguồn. Chỉ có GET metadata và server-side files.copy trong lượt này.

[Thư mục backup độc lập do Sang sở hữu](https://drive.google.com/drive/folders/1--Q-yO2ja7q2RwWWfyv6nDtw80PDrnyZ) giữ các archive model, log/catalog và bộ ghép phần. `MODEL_DRIVE_COVERAGE03.json` là index hiện hành.

## Trạng thái theo phạm vi được kiểm

| Nhóm | Đã có Drive | Sang sở hữu | Điểm cần giữ rõ |
| --- | ---: | ---: | --- |
| Junyi A0–A3 refit cuối, epoch9 | 4/4 | 4/4 | Cùng nằm trong INPUT.zip có pin từng member và metadata Drive khớp |
| Checkpoint Junyi epoch9 và A3 batch cuối | 5/5 mục | 5/5 mục | Bốn archive lịch sử có owner Sang, SHA archive và pin từng state member |
| Grade10 selected-fit | 7/7 | 7/7 qua ba phần archive mới | Ba phần đã được copy server-side, SHA/byte khớp và owner Sang |
| Chỉ còn ở Volume trong phạm vi11model/5checkpoint trên | 0 | — | Volume đang dùng là bản staging, Drive đã có bản sao theo bằng chứng nêu trên |
| Chưa có bằng chứng Drive trong phạm vi trên | 0 | — | Bảng này chưa kiểm mọi artifact khác của KLTN |

Kiểm trước copy đọc metadata của14file model-backup và4archive checkpoint. Kiểm sau copy đọc lại13file nguồn và13bản mới. Nguồn cũ vẫn giữ nguyên SHA/byte và owner Dương, các bản mới có owner Sang. Tài khoản uploader lịch sử và owner được tách riêng. Bộ backup mới cho phép lưu độc lập các bản cần giữ trong tài khoản Sang.

## Bốn model Junyi đã refit

[Mở INPUT.zip do Sang sở hữu](https://drive.google.com/file/d/1GlPhrWOLwFNeUiv1unYaEATypWmV9_Vy/view). ZIP134.525.060byte, giữ source calibration và bốn portable model. Đây là link archive, từng model là member bên trong.

| Model | Epoch | Checkpoint member dưới `experiments/akt/results/` | Byte |
| --- | ---: | --- | ---: |
| A0 không graph | 9 | `model-export-a0-refit-20261114-01/A0_JUNYI_REFIT.pt` | 28.968.311 |
| A1 graph cố định | 9 | `model-export-a1-refit-20261114-01/A1_JUNYI_REFIT.pt` | 28.971.439 |
| A2 confidence cạnh | 9 | `model-export-a2-refit-20261114-01/A2_JUNYI_REFIT.pt` | 28.971.567 |
| A3 confidence và gate | 9 | `model-export-a3-refit-20261114-01/A3_JUNYI_REFIT.pt` | 28.974.239 |

Đối chiếu current MODEL_INDEX, INPUT_PLAN04, member inventory của archive backup01 và protected44files sau dọn. Byte và SHA metadata trùng nhau. Mỗi model còn có MODEL_INDEX.json và SUPPORT.zip giữ encoding, roles, graph/confidence và provenance. Bản backup01 chia hai phần trong thư mục backup mới cũng đã có owner Sang và giữ đúng SHA. INPUT.zip mới và backup01 đều được định vị trong index.

## Checkpoint cuối và trạng thái resume

| Model | Snapshot đã định vị | Archive do Sang sở hữu |
| --- | --- | --- |
| A0 | `checkpoints/epoch-009/state.pt` | [Archive A0 cuối](https://drive.google.com/file/d/1FK01_AM--uIC8ZVzek8wEDEirCle_Hvh/view) |
| A1 | `checkpoints/epoch-009/state.pt` | [Archive A1 cuối](https://drive.google.com/file/d/17Qs1t0wb3SYYiQm85xUqglB19RuZWycK/view) |
| A2 | `checkpoints/epoch-009/state.pt` | [Archive A2 cuối](https://drive.google.com/file/d/1OxrDW1w8jKvDvnLuOrovAi8_Jl6me6lJ/view) |
| A3 | `checkpoints/epoch-009/state.pt`, thêm batch epoch9/step2040 | [Archive A3 cuối](https://drive.google.com/file/d/18m36JGiFFMtVEdAQQjzBxchTDhAf5nsy/view) |

Mỗi state epoch9 có cùng SHA với portable export tương ứng. Chain gồm member pin trong remote-inventory, archive SHA trong COMPLETE, relocation sau offload35GB và metadata Drive. Đây là kiểm nguồn member và archive đã có hồ sơ xác minh, không chỉ suy nội dung từ tên ZIP. SHA của member inventories được ghi trong index JSON.

A3 có receipt final xác nhận model/Adam hữu hạn và RNG hiện diện. Với A0–A2, lượt này xác nhận vị trí/byte/SHA state epoch9 từ metadata, không mở lại tensor để kiểm optimizer/RNG. Tính resume trên runtime hoặc GPU mới chưa được kiểm trong audit này. Snapshot batch A3 cũng có pin archive/member, chưa được nạp thử để resume trong lượt này. Các trạng thái epoch3 recovery cũ vẫn ở archive lịch sử, không dùng chúng thay checkpoint epoch9 cuối.

## Bảy model Grade10 đã có bản backup do Sang sở hữu

Các model nằm trong `03_GRADE10_SELECTED_AND_LEGACY.zip`, archive được chia ba phần. Đã có member inventory, chứng cứ source/member verification và proof ghép các phần khớp archive SHA. Metadata Drive của từng phần vẫn khớp các pin ấy.

| Model | Epoch đã chọn | Member dưới `experiments/akt/results/model-export-20261112-01/Grade10/` |
| --- | ---: | --- |
| A0 | 5 | `A0.pt` |
| A1 expert | 5 | `A1_EXPERT.pt` |
| A1 learned | 4 | `A1_LEARNED.pt` |
| A2 expert | 4 | `A2_EXPERT.pt` |
| A2 learned | 4 | `A2_LEARNED.pt` |
| A3 expert | 4 | `A3_EXPERT.pt` |
| A3 learned | 4 | `A3_LEARNED.pt` |

Đây là selected-fit, còn lifecycle refit/calibration và đánh giá vòng kín. Bản model local vẫn giữ trên D. JSON index có từng đường dẫn, byte và SHA nguồn đã biết để root uploader dùng nếu cần.

- [Phần01, 100.663.296byte](https://drive.google.com/file/d/1hJs-k1_vSTdvXfOHyQC38V4hfV-crOU3/view).
- [Phần02, 100.663.296byte](https://drive.google.com/file/d/1qVPZjxNtV-uR_ZcHqqDllVPHQ0iorw7W/view).
- [Phần03, 1.018.261byte](https://drive.google.com/file/d/1az9pytSeoonGNn9-9Cml-vc_Kz2ysnLu/view).
- [Manifest ghép phần](https://drive.google.com/file/d/1wpExEiVPuuWz-25ry3cV5TdvrDfZbcc0/view), [helper phục hồi](https://drive.google.com/file/d/1MXC3M3-9JtEZA19oFA4As1fA5hpdwHje/view).

Owner của ba phần và hai file hỗ trợ được liên kết ở trên hiện là Sang. Bản gốc do Dương sở hữu vẫn giữ nguyên. `MODEL_BACKUP_COPY_STATE01.json` lưu mapping13sourceIDs sang13destinationIDs. `MODEL_BACKUP_POSTCOPY_VERIFY01.json` ghi lần GET metadata kiểm lại cả26file nguồn/đích sau copy. Không dùng kết quả này làm quyền xóa file local.

## File bằng chứng và cách kiểm lại

`MODEL_DRIVE_COVERAGE03.json` là index có mapping backup Sang mới. Bản01 giữ kết quả offline, bản02 giữ trạng thái trước copy. `MODEL_DRIVE_OWNERS01.json` và `MODEL_DRIVE_HISTORY_OWNERS01.json` giữ kết quả GET metadata qua account Sang. `audit_model_drive_coverage01.py`, `check_model_drive_owners01.py` và `copy_verified_model_backups01.py` giữ cách dựng/kiểm. Có5test giả đạt, gồm idempotency, canCopy/quota guard, ACK không chắc và source không bị đổi. Không có token hoặc URL xác thực trong các file này.

Lượt này tái hash metadata nhỏ và kiểm kích thước file local. SHA binary được đối chiếu từ inventories/receipts đã nghiệm thu, không hash lại mọi PT hoặc mở archive. Vì vậy, kiểm hồi phục thực tế từ Drive trên runtime mới vẫn là bước riêng khi cần sử dụng lại.
