# GRAPH29 — chuẩn bị continuous control A0

10/11/2026. SOURCE-ONLY. Chưa chạy Python/AST, metadata, NN, teacher, Git hoặc ghi config/auth/request. ROOT cần review nguồn và allocation, rồi chạy dry metadata trước. Đây là control của phép kiểm intentional-pause lifecycle, chưa triển khai pause/resume child.

## Bốn source mới

| File trong prep | SHA-256 |
| --- | --- |
| prepare_graph29_a0_control_package01.py | e462f4d39e15a59918b894d7c92127818f9c458af4723fd33bccc0517955817b |
| run_prepare_graph29_a0_control_package01.py | c1c71628907e61bebf6a016498ab8bbdf2ed34ab42d1065044916a0ca10cbeec |
| check_graph29_a0_continuous01.py | 005b5bf8bb69071c8ed48f0e0fdcc1361d99962952419f1f715c133f3d849d96 |
| run_graph29_a0_continuous01.py | 1ea86c4af457157e143b3dfb14edef12476c83f57c19e98456aaec95e310f9a4 |

Inventory before/after `graph29_a0_control_source_inventory01.json` SHA792382618ec6245abd51e5b5491571ea636e7a08eae438dbd54a0194d9c15ee6. Originals và outputs cũ không sửa.

Metadata builder/outer derive từ tiny-A0 package01. NN worker derive từ `check_main_tiny_selected_a0_01.py`, còn NN outer derive từ actual successful `run_main_tiny_selected_a0_02.py`. Old builder từng ghim NNouter01. Bản mới ghim chính bốn file mới, tránh tái sử dụng ref sai đó. Mọi kiểm admission/reader/model chạy original normal entry. Pass-through observers chỉ gọi original methods, không thay factory/reader hoặc tạo execution guard giả.

Diff ngoài đổi tên/path/request kind gồm Gate183/index mới và tăng native prelaunch RAM từ2GiB lên4GiB để ROOT review. Không đổi geometry, recipe, loss, optimizer, seed, EarlyStopping hoặc main phase policy. Các source mới nằm trong prep, ngoài native Gate build map.

## Đầu vào thực đã ghim

- Corpus `grade10-main-lifecycle-engineering10x84-20261109-01`, corpus SHA78da1a4fd1708bb1efca723caed4976ed518687eb70b847fbdf780f111191151 và DONE9b565431267a1e0e6f6fb4c05b42a989b2d533d2de98991e64927149b1c5b710. Dùng nguyên public10 qua actual reader, không đọc oracle/final hoặc gọi collector/teacher.
- Actual Gate index `artifacts/akt/preflight/gate2-main183-win-current-gate-20261110-07.json`, SHAdd8bd24f6a71e57e6206e56dc9c101648558e8dc7b5779abe015c221ea828fd0. Public preflight/reader kiểm current source183 thật. Không ghép native18/cold299 thành Gate.
- Actual publication outer SHA24f7c562591df062fe05c2416bd8b94594047c5bdc8b7dd16cd5767da57bcf05 được inventory tham chiếu. Report/log/raw Gate giữ nguyên.
- Runtime schema2 giữ SHA3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b và lock3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a. Basename runtime có177 là tên lịch sử. Genuine preflight hiện hành phải chấp nhận source/runtime/lock, không dựa vào basename.

## Trần cần ROOT duyệt

Giữ d_model256/d_ff1024/final_fc512, một block/tám heads, context100/target_block100, batch4, dropout0,05, Adam lr0,0001, seed42, max_epochs20, patience3/min_delta0,0001. Budget giữ300s training/540s main wall, worker560/owned580/outer600/cleanup3. Đây là trần tĩnh, chưa là measured runtime hoặc cam kết hoàn tất.

| Công việc của riêng continuous control | Trần tĩnh |
| --- | --- |
| Adapter/backbone constructors, Adam constructors | 2 mỗi loại, gồm fresh-best reload |
| Optimizer steps, backward, clip, training forwards | 40 mỗi loại |
| Training targets được tối ưu | 13.440, bằng672 × tối đa20 epochs |
| Selection forward passes | 21, gồm tối đa20 validations và final best export |
| Selection target evaluations | 1.764, bằng84 ×21 |
| Architecture forward tổng | 61 |
| Checkpoint saves | tối đa20 lần best cải thiện |
| Fresh best restore | 1, checkpoint inspect observer2 |

Mỗi actual epoch có hai train batches/672targets và một selection batch/84targets. Acceptance theo actual E và best-save count, không ghim E7 hoặc best4 từ pilot cũ. Lower bound E≥4 trong observer suy từ first finite best và patience3, không ép controller chạy thêm epoch. Complete terminal/claim/exports phải đi qua original public producer, không chuyển bằng chứng này thành system winner/refit/calibration.

Native admission đề xuất4GiB, disk free2GiB; worker observed RSS cap1GiB và global available floor2GiB. Existing worker monitor là polling telemetry của worker. Owned helper quản lý descendant cleanup, không được diễn giải worker RSS thành hard whole-family memory quota. ROOT có thể yêu cầu profile khác trước dispatch, không tự nới sau failure.

Metadata là operation riêng whole60/owned≤57/worker50/cleanup3, RSS1GiB/free2GiB. NumPy data geometry được phép. Torch/model/teacher/runner imports bị chặn. Dry gọi genuine `_metadata`, original preflight10Git, actual public reader và typed context/condition/spec. Output dry không phải authorization đã nghiệm thu hoặc actual fit.

## Thứ tự ROOT

1. Review và kiểm AST bốn scripts bằng stdlib. Agent chưa chạy AST.
2. ROOT truyền exact reviewed Win03 process Git profile. Metadata outer không strip các biến Git/GH khác hoặc sửa global config. Các config là fsmonitor=false, safe.directory đúng upstream và autocrlf=true. Root profile launcher đã duyệt có thể cấp chúng cho child, giữ parent environment.
3. Chạy dry command sau. Kết quả chỉ được chấp nhận nếu raw owned receipt/Job0, nguồn/input/output SHA, actual10Git, resources và no-model scope đều đạt.

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_prepare_graph29_a0_control_package01.py --worker-sha256 e462f4d39e15a59918b894d7c92127818f9c458af4723fd33bccc0517955817b --outer-sha256 c1c71628907e61bebf6a016498ab8bbdf2ed34ab42d1065044916a0ca10cbeec --approval-reference <ROOT_CONTROL_ALLOCATION_REFERENCE> --prepare-dry
```

4. ROOT đọc exact dry `P/graph29_a0_control_package01_dry.json`, kiểm config/authorization proposal, nguồn và allocation. Chỉ sau review mới materialize. Giữ cùng `--approval-reference` như dry để equality toàn proposal có nghĩa. `--review-reference` là record riêng của lần ROOT duyệt dry.

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_prepare_graph29_a0_control_package01.py --worker-sha256 e462f4d39e15a59918b894d7c92127818f9c458af4723fd33bccc0517955817b --outer-sha256 c1c71628907e61bebf6a016498ab8bbdf2ed34ab42d1065044916a0ca10cbeec --approval-reference <SAME_ROOT_CONTROL_ALLOCATION_REFERENCE> --materialize --expected-dry-sha256 <ACTUAL_REVIEWED_DRY_SHA> --review-reference <ROOT_EXACT_DRY_REVIEW>
```

Materialization có ba exclusive targets mới, giữ partial/failure nếu không hoàn tất.

- `experiments/akt/configs/main-a0-graph29-continuous-engineering10x84-20261110-01.json`
- `experiments/akt/authorizations/main-a0-graph29-continuous-engineering10x84-20261110-01.json`
- `P/graph29_a0_continuous01_request.ROOT.json`

5. Actual continuous dispatch là quyết định riêng sau materialization/source/allocation/RAM review. Command dự kiến dưới đây chưa được cấp dispatch từ source handoff.

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_graph29_a0_continuous01.py --request artifacts/akt/local-tests/akt-research-runner-20261108-01/graph29_a0_continuous01_request.ROOT.json --request-sha256 <ACTUAL_MATERIALIZED_REQUEST_SHA> --worker-sha256 005b5bf8bb69071c8ed48f0e0fdcc1361d99962952419f1f715c133f3d849d96 --outer-sha256 1ea86c4af457157e143b3dfb14edef12476c83f57c19e98456aaec95e310f9a4 --approval-reference <SAME_ROOT_CONTROL_ALLOCATION_REFERENCE>
```

Model output mới nằm ở `experiments/akt/results/main-a0-graph29-continuous-engineering10x84-20261110-01`. Operational output ở `P/graph29-a0-continuous01` và owned counterpart. Không ghi đè pilot cũ.

Sau khi control actual hoàn tất mới chọn pause epoch từ history thật và chuẩn bị parent/child closed authorization riêng. Nếu không có continuing nonbest epoch thì chưa có coverage latest≠best, không sửa labels/min_delta/recipe để tạo coverage. Phase2 unexpected-crash/partial-epoch recovery vẫn là gap trước long paid runs. Source prep và continuous engineering control không cấp GPU/CV/Holdout hoặc nghiệm thu ma trận nghiên cứu.
