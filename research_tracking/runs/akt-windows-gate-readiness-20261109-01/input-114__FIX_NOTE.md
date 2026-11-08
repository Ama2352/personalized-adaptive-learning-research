# Gate2: tạo UUID temporary root trước các nhóm, chưa kiểm thực thi

Actual fullGate01 ROOT báo failed5.7286902s,19ERROR nhóm stdlib trước test bodies.
Native log: `artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-01-stdlib.log`.
Runtime preflight và ownedJob cleanup đạt; không coi failure này là GatePASS.

Nguyên nhân source: refresh chỉ tạo temporary.parent, rồi đưa temporary/stdlib
cho pytest. `_pytest/tmpdir.py::TempPathFactory.getbasetemp` dùng
basetemp.mkdir(mode=0o700), parents=False, nên UUID intermediate chưa tồn tại
làm fixture tmp_path lỗi. Đây là bug production path lifecycle, không là lỗi
protocol/model hay thiếu quyền import.

Hai snapshot trước thay đổi đã copy nguyên byte, SHA nguồn trước=sau copy=SHA
snapshot: refresh5b7e60d342f8c2ab27536d3ec02d208a9bdb04728ca5ccdf7371b13d784fa31b;
test9a0a41ffde24d0d12996f7294d000d50d9cbc8c1adced6853a0abf2c0c7de758.
`before.json` lưu inventory. Không sửa logs/receipt hoặc closedbundle lịch sử.

Fix: giữ run-ID/UUID/path/group/caps như cũ, từ chối symlink/junction parents,
tạo UUID run-root exclusive bằng mkdir(exist_ok=False) trước group loop. Không
reuse/xóa thư mục attempt cũ. Parent mkdir chỉ hỗ trợ ancestor còn thiếu.

ONE regression mới: `test_gate2_unique_run_root_supports_real_nested_pytest_basetemps`.
Các test subprocess và report vẫn là fixturefake; chỉ sử dụng actual installed
TempPathFactory.getbasetemp/mktemp và filesystem ghi/đọc payload cho3group.
Trước getbasetemp: require absolute leaf thuộc fresh owned fakeproject và chưa
tồn tại/không alias, tránh pytest recursively delete một path có sẵn. Sau3group
xác nhận cùng1UUIDroot vật lý, payload nhóm trước còn nguyên và pointer không đổi.
Source cũ sẽ fail real getbasetemp khi thiếu parent, không chỉ fail mockedmkdir.

Agent không chạy Python/AST/pytest/native/Git. ROOT review rồi chạy bounded
focused node dưới `.venv`, ví dụ pytest node trên, `-q -o addopts= -p no:cacheprovider`,
basetemp mới/ngắn `artifacts/akt/local-tests/g2b01`, JUnit/log theo attempt mới.
Sau focused regression và module checks được ROOT nhận, cần sourcefreeze/collection
mới; collection07 và packet154source trước fix giữ nguyên, đã stale cho fullGate.
Không chạy lại fullGate bằng packet/source cũ, không tăngcap hoặc đổi populations.
