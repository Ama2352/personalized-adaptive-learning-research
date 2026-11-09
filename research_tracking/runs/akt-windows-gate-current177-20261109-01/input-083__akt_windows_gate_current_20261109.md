# Kiểm kê và Gate phần mềm Windows với177 nguồn

Ghi nhận kỹ thuật ngày09/11/2026. Full Gate04 kết thúc REJECTED. Bộ kiểm tra tập trung của bản sửa parser/merger đã đạt99/99ca.

Sau khi đóng băng batch graph/mainproducer và dependency inventory, population theo native `gate2_build_hashes` gồm177đường dẫn nguồn và81mô-đun kiểm tra. So với Gate03 lịch sử154/69, có23đường dẫn thêm và2file đổi, gồm builder Colab và kiểm thử tương ứng. Năm tài liệu protocol21/22/23/26/allocation có hashes riêng ngoài native build map. Snapshot nguồn và protocol chỉ xác định input cần kiểm tra.

Collection10 đã hoàn tất với1.726nodeIDs, gồm19stdlib,271no-torch và1.436remaining. Thời gian ghi trong receipt là28,1445431giây trên trần60giây toàn lượt. Ba nhóm được thu trong ba process mới. Cả ba đều ghi source/supportdocs trước=sau, counters testbody/model/backward/optimizer/solver/teacher/data/CUDA bằng0, profiler khôi phục và Job active0 sau cleanup. Bộ đếm collection đo calls thuộc các vị trí guard đã nêu. Import có thực thi module tops và Torch CPU có thể tạo metadata tensors.

## Hai lỗi chuẩn bị được bảo toàn

Lượt helper04 dừng trước tạo packet vì thứ tự module trong snapshot PowerShell khác native Python. Actual diagnostic ROOT xác nhận toàn bộ build hashes và membership đều bằng nhau. Bốn vị trí khác là context/context_recovery và edge_confidence/artifact. Snapshot05 lấy nguyên orderedgroups từ actual native diagnostic và helper05 yêu cầu exact whole canonical maps/lists/order. Record `prior_failure` trong diagnostic là normalized tool transcript, gắn toolchunk và thời gian của lệnh gốc. Raw stderr riêng của helper04 chưa được lưu thành tệp.

Lệnh ROOT đầu tiên gọi helper05 dùng relative `--output`, bị `safe()` từ chối. Canonical equality đã qua, packet và collection chưa được tạo. ROOT giữ normalized failure rồi dùng cùng helper/pins với absolute output. Lượt sau tạo packet05 có SHA3264b3eb506a0cb0bb4dfd1746c048f7bf75dc0c79973b7682dc1333398b7597. Hai failure thuộc preparation và invocation, được phân biệt với kiểm thử phần mềm.

## Full Gate04 bị từ chối tại bước ghép JUnit

ROOT đã review actual collection và chốt packet fullGate từ toàn bộ1.726nodeIDs. Job04 dùng native CLI `refresh_gate2.py`, ba partition canonical và JUnit identities ánh xạ bằng installed pytest utility đã ghim. Limits là native580giây, owned tối đa600giây gồm cleanup3, outer630giây. Admission cần4GiB RAM trống, floor1GiB và RSS/peak tối đa3GiB cho từng process được quan sát. Run `win-current-gate-20261109-04` kết thúc worker exit1, stored outer293,1832575giây. Job cleanup đạt active0. Lỗi nằm ở `combine_junit` khi đòi số testcase bằng count lấy từ thuộc tính `tests`.

Ba raw JUnit groups chứa19/271/1.436testcase vật lý, toàn bộ identities khớp packet và0failure/error/skip. Thuộc tính `tests` lần lượt là19/271/1.501, tổng1.791. Console remaining ghi `1436 passed, 65 subtests passed`. Diagnostic hậu kiểm ROOT giữ riêng kết quả physical1.726 và phần dư65. Gate04 tiếp tục có status REJECTED, native report PASS chưa được tạo và lệnh không publish pointer.

Primary installed `_pytest/junitxml.py` tăng thống kê passed theo mỗi call report tại dòng188–189 và555–561, trong khi node reporter dùng cùng nodeID. Dòng657–679 xuất thuộc tính `tests` theo tổng call reports và từng testcase từ node reporters. `_pytest/subtests.py` dòng411–416 chuyển parent sang failed khi có subtest thất bại. XML của passed subtest không chứa dấu riêng để truy ngược từng subtest. Với lượt này, raw console và source semantics giải thích65passedsubtests. Parser giữ phần dư thuộc tính làm thông tin, không cộng thành nodeIDs mới.

## Bản sửa và99 kiểm thử tập trung

Parser mới đếm physical testcase. Mỗi suite phải có testcase, bốn count attributes là số nguyên hợp lệ, `tests` ít nhất bằng số physical cases và toàn bộ FESattributes bằng0. Mọi descendant failure/error/skipped vẫn bị từ chối ngay cả khi tổng thuộc tính ghi0. Guard kiểm tra nesting, tên và uniqueness. Merger giữ nguyên thuộc tính raw và kiểm tra reported group result với physical items trước ghi output. Exact collection-to-JUnit mapping ở outer tiếp tục kiểm tra population độc lập.

ROOT chạy riêng module `tests/akt/test_gate2_refresh.py`, gồm77ca semantic cũ và22ca mới với identities cố định. Lượt đạt99/99,0FES, stored outer3,8001483giây trên trần60giây, child3,4756981giây. Peak quan sát54.964.224B và minimum available5.421.867.008B. Job cleanup active0, env/cache được khôi phục, heavy imports và các attempted forbidden calls bằng0. Fixture cover count surplus/raw preservation, malformed attributes, hidden FES, empty/nested/underreported cases, duplicate/missing identities và stale group counts. Kết quả này xác nhận bản sửa trong allocation tập trung. Nguồn và population mới của full Gate tiếp theo chờ ROOT freeze/collection/review.

Suite gồm synthetic model/backward/Adam/checkpoint fixtures. Workload dùng wall/RAM bounds và các test cases đã đóng băng. Counts từ các lượt fixture độc lập trước đây có shared fixture/modulecache nên không được cộng thành một operation cap cho whole suite. Kết quả mainproducer16mock đã đóng riêng. Actual research fit, CV, refit, calibration và CUDA có acceptance riêng trong pipeline.

## Lưu bằng chứng

Bundle dự kiến `akt-windows-gate-current177-20261109-01` giữ raw collection10, helpers/snapshots04/05, reviews, normalized metadata failures, fullGate04 REJECTED và targeted99 ACCEPTED. Terminal Gate04 được bind bằng SHA12e9418c43045e48d0bead6c3be0b8cfd3a4733379c23c01ac91b30c6326639b. Targeted99 được bind bằng SHA4f7b109e7b927116d78fd7293b2528366796f0f58f44cbdbe6ad7e4e553b15a7. Copy inventory giữ hashes trước/sau và deduplicate bằng SHA. Trong177source bindings của failed Gate04, hai source trước sửa được bảo toàn bằng snapshot9608/255c,175nguồn còn lại dùng reference hashes. Hai source sửa8689/268a được lưu riêng cùng targeted receipts. Báo cáo và helper dự thảo trước terminal cũng được snapshot. Năm supportdocs và namespace/runtime dependencies được dẫn bằng đường dẫn/hash. Manifest Gate154 cũ được tham chiếu với SHAf53291c057515f1159e1d520065e3d46744307511c428383cab8494ea5160d26.

Các kiểm soát RAM là quan sát hợp tác trong process tree đã sở hữu. Scope của bộ chứng cứ là kiểm phần mềm Windows CPU và integrity của input/output. Các kết luận hiệu quả nghiên cứu cần thí nghiệm và estimand tương ứng.
