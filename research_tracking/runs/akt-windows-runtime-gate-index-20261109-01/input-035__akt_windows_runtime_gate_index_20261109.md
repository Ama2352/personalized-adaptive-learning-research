# Runtime schema2 và index Gate cho main driver trên Windows

Ngày09/11/2026, hai lượt kỹ thuật đã được ROOT thực chạy và chấp nhận. Lượt thứ nhất chạy public CLI để đo runtime CPU hiện tại. Lượt thứ hai tạo index mới dẫn đến native Gate05 đã accepted, kiểm tra bằng public preflight và reader hiện có.

| Lượt | Kết quả actual | Thời gian lưu trong outer | Quan sát bộ nhớ |
|---|---|---|---|
| Native runtime schema2 | ACCEPTED, schema2 CPU, Torch2.7.1+cpu và NumPy2.5.4 |5,2641881giây trên trần60giây|Worker peak191.430.656B, RAM trống tối thiểu5.213.077.504B|
| Index publication | ACCEPTED, public readers cùng xác nhận index mới |3,9922830giây trên trần30giây|Max observed mỗi process31.674.368B, RAM trống tối thiểu4.194.992.128B|

Mỗi lượt chạy qua actual-worker GO trước native work và owned Job cleanup đạt active0. Bộ nhớ được poll hợp tác. Con số publisher là peak lớn nhất của một process được quan sát trong family, không phải tổng RSS cùng thời điểm của toàn family.

## Báo cáo runtime được đo mới bằng native CLI

`scripts/akt/check_runtime.py` chạy nguyên CLI với `--device cpu`, upstream checkout và Windows lock hiện có, output exclusive tại `artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json`. Nguồn/root/prefix/lock và origins của Torch/NumPy được kiểm tra trước/sau trong cùng .venv. Original `verify_upstream` thực hiện10read-only Git commands. Report được bind bằng SHA3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b.

Observer ghi0body model constructor, forward, backward, optimizer constructor/step, solver và teacher. Hai availability queries thật trả False tại upstream module device selection và cuối native runtime report. Torch có `cuda_build=null` và `cuda_initialized=false`. Các imports framework được thực thi thật. Metadata tensors khi import không thuộc tuyên bố0model body này.

Worker hoàn tất trong4,7197692giây. Root profile launcher lưu tổng5,3565497giây cho lệnh gọi outer và raw streams của nó. Các mốc này có phạm vi bao hàm khác nhau và được giữ trong receipts tương ứng.

File legacy `runtime-v2.json` SHA259c171fe63e39a14d9bdf42793bd854a5be73ded19a7a800a2e8a982906f1b4 thiếu trường `runtime_schema_version`, dù basename chứav2. Main guard cần schema2 thực, vì vậy report mới được đo và lưu riêng. Legacy bytes được kiểm tra nguyên vẹn sau lượt chạy.

## Profile môi trường được cấu hình rõ ràng

Runtime launcher bắt đầu với caller có `GH_PAGER` và `GIT_PAGER`. ROOT đã review việc loại hai biến hiển thị đó khỏi child environment, rồi cung cấp exact Win03 profile gồm `core.fsmonitor=false`, exact upstream `safe.directory` và `core.autocrlf=true`, cùng các biến Git read-only đã ghim. Child profile và tên biến bị loại được lưu trong reservation. Parent environment của launcher giữ nguyên.

Publisher outer dùng cùng profile theo runtime packet. Nó cấu hình tạm environment của chính outer trong khoảng gọi owned worker, loại đúng hai biến PAGER đã review, từ chối các biến GIT_/GH_ khác nếu ngoài profile và khôi phục full caller environment trong `finally`. Worker publisher kiểm tra exact profile và giữ môi trường của mình. Đây là setup được ghi nhận trong bằng chứng actual.

## Index dẫn đến Gate05 đã được chấp nhận

Native Gate05 đã có actual outer ACCEPTED, current source177/81 và1.748testcase. Report/log/JUnit và Gate archive được dẫn bằng path/SHA trong bundle metadata này. Publisher dùng report schema2 mới để public preflight xác nhận lại source/lock/venv, rồi ghi một index năm trường theo native format tại `artifacts/akt/preflight/gate2-main177-win-current-gate-20261109-05.json`.

Index có SHAe8162f6efce3ca0a443f6c40f69308b06b610e95d5a02504ba146e92b6f87366, dẫn đến report9dfc6f8592ef1d90b7430c06dbcbc96a92808f810c503043b5045c5560850afe và merged logcbc97aad1e5f28aedc173e6a9c5e0c1b5ee44d92226a97e450191b5b8b8b8eec. Worker chạy original public preflight với10Git commands, gọi public reader hai lần, và outer gọi reader độc lập thêm một lần. Toàn bộ nguồn177, input files và raw metadata được hash lại. Worker publication mất2,3537651giây, outer lưu3,9922830giây.

Gate05 ban đầu dùng runtime legacy259c. Public Gate reader bind report/log/source/lock và elapsed, còn public preflight xác thực schema2 mới cùng source/lock/venv. Receipt giữ riêng `gate_original_runtime_reference` và `selected_runtime_report`. Main guard có thể tiêu thụ explicit index path cùng SHA schema2 qua typed `ResearchRuntimeEvidence`.

Global `gate2-current.json` vẫn có exact SHA9e768aadcf084482a2eeb9be814fc399100dd1a507eaa89afbbae87100365cd6 trước/sau. Nó tiếp tục là index lịch sử154. Publisher mới dùng một index riêng cho explicit admission. Closed authorization, caps và phase của actual main A0 vẫn cần được kiểm tra trong stage tiếp theo.

## Mức bằng chứng và lưu trữ

Runtime final SHAa5fb17e05ad07b0562ceb05045a8f9f8a2d749490efd18ce465308aa18c37fe6 và index final SHA718ae04bf5d8ad8c717be08f7de8803576db317f6f39235642d38e674eca09d7 là receipts actual của hai lượt. Bundle dự kiến `akt-windows-runtime-gate-index-20261109-01` giữ raw worker/owned/launcher logs, source/packet/reviews, report schema2 và index nhỏ, cùng copy inventory SHA trước/sau. Gate05 JUnit và dependencies được giữ theo references thay vì nhân đôi.

Hai lượt này đo runtime và nối software evidence vào đường admission. Chúng có0world transitions và0model-training bodies theo guards đã nêu. Research corpus, Holdout và model artifacts không được đọc để tính dữ liệu trong hai lượt. Các lần đọc source/upstream/runtime metadata và opaque source hashing được ghi đúng phạm vi. Chưa có kết quả actual main fit, refit, calibration, CUDA hoặc hiệu quả RQ từ bundle này.
