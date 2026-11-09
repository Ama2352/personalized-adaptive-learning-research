# Gate phần mềm Windows CPU trên 177 nguồn đã đạt

## Kết quả và phạm vi

Lượt `win-current-gate-20261109-05` đã chạy toàn bộ 1.748 ca kiểm phần mềm, gồm 19 ca stdlib, 271 ca no-Torch và 1.458 ca còn lại. Không có failure, error hoặc skip. Bộ kiểm ngoài xác nhận đúng toàn bộ định danh đã thu thập trước khi chạy, đúng nguồn và đúng artifacts. Native report ghi 477,3461261 giây trong giới hạn 580 giây. Outer receipt ghi 480,8069867 giây trong giới hạn 630 giây. Thời gian 480,8569538 giây in khi kết thúc là quan sát ở thời điểm khác, không cộng vào thời gian receipt. [Receipt ngoài](../../artifacts/akt/local-tests/akt-research-runner-20261108-01/win-current-gate-20261109-05-outer/result.json), [native report](../../artifacts/akt/preflight/gate2-evidence-win-current-gate-20261109-05.json)

Owned worker và cleanup đều được chấp nhận, Job còn 0 tiến trình sau cleanup, danh sách lỗi rỗng. Global `gate2-current.json` được giữ nguyên byte trong lượt này. Lệnh native không yêu cầu publish. Đây là kiểm phần mềm synthetic, có các fixture neural/optimizer trong toàn bộ suite, chưa phải kết quả fit nghiên cứu hoặc cải thiện RQ1–RQ3. [Log thực chạy](../../artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-05.log)

## Vì sao cần lượt05

Gate04 trước đó đã chạy 1.726 physical items nhưng merger từ chối vì thuộc tính `tests` của JUnit đếm thêm 65 successful subtest call reports. Verdict Gate04 vẫn là **REJECTED**. Bản sửa chỉ thay cách đọc physical testcase và vẫn từ chối failure/error/skip, thiếu hoặc trùng định danh. Bundle Gate04 giữ cả failure và 99 fixture kiểm parser, được tham chiếu nguyên trạng trong bundle mới. [Hồ sơ Gate04](../runs/akt-windows-gate-current177-20261109-01/README.md)

Sáu canary của outer03 thực tế đạt với child exit0. Driver ban đầu tìm chuỗi LF quanh `OK` trong log Windows CRLF nên ghi receipt từ chối. Reconciliation đọc lại đúng raw output bằng `splitlines`, giữ receipt gốc và không chạy lại canary. Kết quả này chỉ kiểm parser và các XML lịch sử, không thay cho full Gate05. [Reconciliation](../../artifacts/akt/local-tests/akt-research-runner-20261108-01/current_gate_outer03_canary01_reconciliation.json)

## Nguồn, population và admission

Snapshot06 giữ 177 đường dẫn nguồn và 81 module, ba nhóm theo đúng thứ tự native. So snapshot05 có hai nguồn thay đổi và không thêm/bớt đường dẫn. So mốc154nguồn lịch sử có 23 đường dẫn thêm và bốn nguồn thay đổi. Collection11 thực thu 1.748 nodeIDs trong 53,0412358 giây/60, có source/support-document trước=sau, environment restored và ba ownedJobs cleanup sạch. Các số ca của Gate05 lấy từ collection11, không suy từ số ca Gate04. [Collection11](../../artifacts/akt/local-tests/akt-research-runner-20261108-01/gate-collection11-outer/final.json)

Gate05 dùng runtime lịch sử `runtime-v2.json`, SHA bắt đầu `259c171f`. Tên file này không chứng minh schema2. Sau Gate05, ROOT đã chạy riêng native runtime CLI tạo `runtime-schema2-main177-20261109-01.json` và publisher tạo index `gate2-main177-win-current-gate-20261109-05.json`, không thay globalpointer. Hai bước sau có hồ sơ/bundle riêng và không được gộp ngược vào điều kiện chạy Gate05. Main execution vẫn phải xác minh runtime/index/auth/config/source/data thực tế theo guard. [Runtime schema2 riêng](../../artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json), [index riêng](../../artifacts/akt/preflight/gate2-main177-win-current-gate-20261109-05.json)

## Bằng chứng đóng gói và giới hạn

Archiver chọn metadata nguồn, controllers, packet, collection/owned receipts, raw canary và reconciliation, native log/JUnit/report, outer receipt và hai bản pointer. Không nhân đôi 177 nguồn, dependencies hoặc bundle Gate04. Inventory lưu SHA/size trước copy, SHA bản copy và nguồn sau copy. Khi ROOT chốt dry inventory và đóng run, manifest tại `research_tracking/runs/akt-windows-gate-accepted177-20261109-01/manifest.json` xác nhận closure. Báo cáo này mô tả kết quả thực chạy đã accepted, không tự xác nhận archive đã đóng trước khi có manifest.

GatePASS không cấp quyền fit/corpus/GPU, không chứng minh runtime Linux/CUDA hoặc đủ chín mô hình và hai môi trường nghiên cứu. Một thay đổi nguồn tiếp theo vẫn cần admission theo hashes hiện hành. Không dùng số tests hoặc số outputs làm số mẫu nghiên cứu hay mức hoàn thành RQ.
