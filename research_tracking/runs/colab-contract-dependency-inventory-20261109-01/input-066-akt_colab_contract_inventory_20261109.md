# Kiểm dependency closure của builder local —09/11/2026

ROOT đã nghiệm thu **8pytest cases/0failure/error/skip** cho inventory trong bộ
nhớ, sau ba lỗi bootstrap trước test. Không tạo ZIP, upload/source export hoặc
chạy cloud/model. Đây không là GatePASS của toàn source đang phát triển.

## Thiếu dependency nào đã được sửa?

Builder tự lấy các Python modules mới nhưng trước đó chưa lấy tài liệu mà graph
code đọc tại runtime: recipe26 của condition và protocol21 của checkpoint. Patch
chỉ thêm năm fixed public paths: protocol21, lifecycle22, accounting23, recipe26
và EXPERIMENT_ALLOCATION_V1.json. Không docs glob hoặc arbitrary runtime/auth
files. Builder SHA `4fdb7e9512653984d2ebf30a982284dfe0303a6dfc467a4f6f4a2c918a94aabb`;
test SHA `29f3ccea4aa2efed5c32af3bd8eb2c44b140c83be01e63ab3e59a99a3b699295`.

Test kiểm actual dependency IDs từ source, raw bytes của năm tài liệu và closure
của chúng; synthetic tmpFS kiểm không lấy tài liệu ngoài allowlist, thiếu từng
tài liệu phải dừng. Source cells của ba notebook giữ nguyên; copy vẫn strip
outputs/execution metadata và giữ original SHA/transform provenance. Không sửa
notebook gốc và không thực thi code trong notebook. Trước patch đã giữ raw hai
source cũ cùng inventory SHA trước/copy/sau.

## Ba lỗi bootstrap được giữ nguyên

|Lượt|Actual trước test|Sửa cho lượt kế tiếp|
|---|---|---|
|01|Generic write guard chặn khi metadata chưa hoàn tất; không ghi raw path|Theo installed platform/subprocess source, bổ sung đúng `os.devnull` stdio sink ở metadata phase|
|02|Một literal `cmd /c "ver"` và raw `nul`/modeNone/flags130 đã qua; tempfile thử ghi GLOBALTEMP, flags34178|TEMP/TMP/TMPDIR và cache tempfile chuyển vào OUT/runtime-temp mới, không nới write guard|
|03|Windows metadata và owned runtime-temp đã qua; pytest logging mặc định mở `\\.\nul`, modew/flags33665|Thêm explicit `--log-file=OUT/pytest-file.log`, giữ logging plugin và guard alias NUL|
|04|8cases thực chạy, đủ JUnit0FES; no blocked writes|Accepted local inventory only|

01–03 đều **counts=null, không JUnit/test cases**; không ghi thành ba lần8FAIL
hoặc lỗi assertion của builder/test.01 raw path vẫn unknown, không dựng lại thành
fact NUL từ giả thuyết source. Các lượt không overwrite lịch sử.04 giữ strict
NUL predicate, source/protected/write guards, owned temporary directories và
restore cache/environment; không disable logging để qua kiểm tra.

ROOT còn chạy **4stdlib canaries PASS** trên predicate AST thật của02: exact sink,
raw alias/path rejection, mode/flag rejection và phase/count bound. Đây là kiểm
guard nhỏ, không model/RQ evidence. Output gốc chỉ nằm trong tool reply hỗn hợp
(có cả GetContent preview), không có raw stdout/stderr riêng. Bản chuẩn hóa
`root_colab_canary02_tool_capture.json` giữ exact observed JSON/case names/exit0;
không rerun để tạo log đẹp. Tool wall0.9413438s không được coi là Python-only
elapsed; unittest hiển thị0.000s do độ phân giải. Predicate bytes giữ nguyên ở03/04,
không gọi các revision này là bốn canaries mới.

## Actual04 và phạm vi những SHA đã kiểm

JUnit ghi8cases/1.035s. Worker stored elapsed2.48529330000747s; helper Job
2.7408690452575684s; outer final3.015408754348755s. ROOT printed
3.0203936000471003s và terminal3.8232603s là các điểm capture khác. Profile04 là
whole60/owned≤57/worker53/cleanup3; không gọi bốn attempts là một continuous60s.
Các allocation trước và canary reserve5s được giữ; ceiling ROOT cho profile04
cùng prior charges khoảng70.7154843s theo độ chính xác đã khai báo.

Observed worker peakRSS50327552B, minimum freeRAM4674363392B,17samples trong
guards1GiB/free2GiB; cooperative observations, không hardOSquota. Actual worker
được GO sau Job membership, cleanup active0/handles closed.04 có một metadata
command thật và một rawNUL stdio event, không query GPU. ZipFile observer ghi
**constructor0/read-return0/write-attempt0**, observer intact và method restored.
Worker không import Torch/NumPy/domain model; no scientific modules/denied
attempts trong lượt accepted. Không construct/fit/forward/backward/optimizer,
actual corpus/Junyi interactions/Holdout hoặc training artifacts.

04 pin trước/sau **9selected sources,18fixed fixture inputs,11runtime fingerprints**.
18inputs gồm5public contract docs,3source notebooks,5public simulator-input CSV,
3config fixtures hiện có và2requirements files. Bundle lưu SHA refs, không copy
notebooks/CSV/dependencies/runtime/corpus. Các Python files khác được inventory
đọc dưới dạng bytes có thể còn WIP; read paths được ghi nhưng **không claim global
source stability**, final source count, runnable kit hay source authorization.

Final04 receipt SHA `798d347cab9d3e1c50baf28f0b1136f8c7a010c7ec13e3c8bc5a880cbcaf6e8a`;
worker SHA `27e1d1ad38355a0eb8e5229fd3db0d0be7026af602cd90084e4bd2c86259925a`.
Bundle dự kiến `colab-contract-dependency-inventory-20261109-01` giữ raw01–04,
normalized canary capture, source/controller/packet snapshots, before/after copy
SHA và `CURRENT_GATE_REFRESH_GAP01.md`. Các log tạm của pytest/runtime-temp không
được dùng như model artifacts hoặc copy toàn bộ vào hồ sơ.

## Điều chưa được cấp quyền hoặc chứng minh

Prior remote source-export auto-review denial vẫn binding; local inventory
verification không cấp quyền ZIP build/upload/source export hoặc route thay thế.
Không có remote invocation, GPU/Modal allocation hoặc Git mutation từ agent.
ROOT đóng/commit hồ sơ riêng. Fresh software Gate chỉ chuẩn bị sau final WIP
source/test freeze, actual collection và reviewed packet; old154/69/1418 là lịch
sử, không certification source mới. Linux materialization/runtime/CUDA/throughput
và main selected-only producer cần acceptance riêng; dependency closure không
thay các ranh giới đó hoặc hoàn tất RQ.
