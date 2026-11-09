# Pilot targeted observer CPU09 — failure trước estimator

Ngày09/11/2026. Hồ sơ vận hành của một allocation riêng, không phải kết quả mastery hoặc lượt thứ sáu tiếp tục full replay. Năm lượt native mastery trước vẫn giữ trạng thái STOPPED trong bundle `rq1-cpu09-native-mastery-replay-attempts-20261109-01`. Manifest của bundle mới `rq1-cpu09-targeted-observer-attempt-20261109-01` xác nhận việc đóng gói thực tế khi được ROOT thực hiện. Manifest archive hoàn tất không đổi verdict của pilot bị từ chối.

## Mục đích và nguồn đã duyệt

Pilot dự kiến phát lại đúng history cũ `(21000, PG, graph_on=False, mechanism_on=False)` gồm120events, bằng hai fresh policies. OFF rồi ON chỉ trạng thái targeted observer. Cả hai phải khớp archived selected query/P bits, native readout và full initial/final fingerprints, tổng không quá240updates. Không tạo teacher/world/response mới, fit hoặc truth metric. Allocation mới giữ whole60s, worker53s, owned tối đa57s có cleanup reserve3s, RSS1GiB/freeRAM2GiB.

Revision D39 cho phép strict reader parse stored truth để validation cache cũ, rồi chỉ chuyển immutable public projection sang model. Đây là data-role boundary đã được ROOT duyệt, không phải quyền đưa oracle vào prediction. Source đã duyệt cho lần này là worker `23698def…14660`, outer `c892124f…38e86`, contract `7f8f8b16…3e163`. Review02 thay review01 về source pins và5inline checks, giữ nguyên ngân sách/scenario. Original3files và review01 được snapshot byte-identical trước sửa rollback, có before/copy/after inventory.

## Điều thực sự quan sát được

| Thành phần | Bằng chứng actual |
|---|---|
| Terminal | `REJECTED_KEEP_PILOT_NO_RETRY`, worker/owned returncode1 |
| Năm inline checks | `pure_checks.json` ghi đủ5manufactured checks trước native, không là mẫu nghiên cứu |
| Pha lỗi đầu | `native_import_and_full_cache_validation`, message `read outside pinned sources/inputs/runtime` |
| Pha lỗi tiếp theo | `postchecks`, cùng message read guard |
| Cache truth validation | `loader_truth_validation_started=false`, `completed=false` |
| Estimator work | `direct_started={}`, `direct_returned={}`, `phases=[]`; không có reservation/OFF/ON outputs |
| Metadata Windows | Real metadata phase đã đóng,1helper command `/c "ver"`,1local hostname lookup; hostname không lưu; late process/socket/blocked counters0 |
| Resource sampling |31samples,30samples có child, observed family peak101126144B, minimum available2576224256B, resource errors rỗng |
| Cleanup | Job active0, `cleanup_accepted=true`, Popen handle đóng, monitor dừng, environment khôi phục |

Worker ghi elapsed2.9323118000174873s trước failure receipt, stdout sau receipt ghi2.934267100004945s. Owned receipt ghi3.2617015838623047s. Outer lưu3.395690800040029s trước final receipt; ROOT thông báo terminal khoảng3.3976s. Các thời gian lồng nhau không cộng lại. Resource limits chưa bị chạm trong dữ liệu lấy mẫu. Helper `accepted=false` do worker returncode1, không phải bằng chứng cleanup bị hỏng.

Không có estimator constructor hoặc update nào được bắt đầu. Điều này được hỗ trợ đồng thời bởi empty direct ledgers, vị trí source reservation nằm sau validation, hai validation flagsfalse và không có reservation/OFF/ON outputs. Khẳng định này chỉ áp dụng terminal cooperative failure đã được lưu của lần này, không dùng quy tắc đó cho mọi hardkill/partial run.

## Chẩn đoán giới hạn theo evidence

Hai read-guard denials được ghi với message tổng quát, không kèm path hoặc traceback của lần đọc đầu tiên. Không xác định file gây lỗi đầu từ phase label. Pha đó bao gồm import và source/cache preparation, nên không suy file thiếu permission, parser error, parity mismatch hoặc chi phí observer từ message này.

Có một lỗi source-level xác định được ở postcheck. Worker gọi `sha(CONTRACT)` sau khi audit đã cài, nhưng current contract JSON không nằm trong `allowed_reads` tạo từ `contract.bindings`. Không thể giải quyết bằng cách tự đưa hash toàn contract vào chính nó vì tạo hash cycle. Đây là lỗi admission/read-guard configuration, cần thiết kế tách explicit self-contract read entitlement với nội dung contract được kiểm bằng external pin nếu có revision sau. Hồ sơ này không triển khai sửa hoặc cấp lượt chạy tiếp theo.

Failure receipt có33source bindings trước/sau bằng nhau sau vòng `verify()`, nhưng postcheck tổng thể vẫn thất bại khi đọc self-contract. Outer dừng ở điều kiện clean owned terminal, nên không có successful artifact validation hoặc outer source-after proof. Archive có thể hash lại hiện trạng để chứng minh bytes được đóng gói, không gán kiểm sau copy thành successful worker postcheck trong lịch sử.

## Điều chưa hoàn thành

Chưa phát lại một stream, chưa có120P/query parity, OFF/ON state/readout parity, targeted method counts hoặc timing của observer. Chưa chứng minh whole120streams khả thi, không có confusion/masterytruth/calibration/learning-benefit result. Không phân tích hoặc sử dụng partial data của lane cũ. `new_independent_N=0`.

ROOT đã dừng allocation sau failure, không retry hoặc tăng cap. Bất kỳ bước sau nào phải bắt đầu từ review nguyên nhân đọc đầu, source-level guard revision rõ ràng và allocation mới có ledger minh bạch. Các file raw, source cũ/mới, reviews và inventory giữ nguyên. Việc đóng gói chỉ lưu bằng chứng của một pilot bị từ chối.

## Các file cần đối chiếu trong bundle

- `worker__failure.json`, `worker__pure_checks.json`, `worker__native_metadata.json` giữ dữ liệu worker actual.
- `outer__final.json`, `outer__admission.json`, `outer__memory.jsonl` giữ parent verdict và resource sampling.
- `owned__receipt.json`, các original stdout/stderr/GO/launch/ready giữ ownership/cleanup và terminal output.
- Ba source hiện tại, `CPU09_TARGETED_OBSERVER_ROOT_REVIEW02.md`, old source/review01 snapshots và before/copy/after inventories chứng minh source history.
- Original CPU09 gzip và closed5-attempt bundle chỉ được tham chiếu bằng source/input SHA; không copy lại raw corpus, checkpoint hoặc runtime dependencies.
