# RQ1 — trace θ/pi chưa được nghiệm thu: hai failure vận hành

**Chưa có kết quả nghiên cứu mới về Prediction/Calibration → Mastery.** Cả native attempt01 và02 đều REJECTED; toàn bộ2160legacy rows và18final fingerprints chưa hoàn tất. Các snapshot partial không được dùng để tính hiệu ứng, phân nhóm hay tuyên bố calibration/mastery. Ngân sách native hiện tại đã dừng, không retry.

## 1. Cần đo gì và đã xảy ra gì?

[Phân tích fixed controller đã đóng](rq1_fixed_controller_candidates_20261109.md) đã phân biệt ready set R, candidates C, balanced set B và CID preview. Bước tiếp theo cần xem native mastered gate `theta>=1250 AND pi_task<=.55` khác query responseP/scoreS ra sao. Vì cache chỉ lưu hashes chứ không fullstate có thể phục hồi, trace được thiết kế replay18policies trên1080cachedqueries,2160onlineupdates và6480predict, không sinh teacher responses/RNG/optimizer, không đọc oracle.

Admission bắt buộc là **all2160legacy P/S28/M/R/fullpreview exact và18initial+18finalstate hashes**. Hai trajectory hoàn tất riêng lẻ không thay điều kiện toàn bộ này. Preview không là served action, raw3refs không là calibratedV1, reusedstreams/newN0. Nguồn fixed runner được phục hồi từGit e4e6a262…, không mang giới hạn missingrunner của nhánh closed-loop khác.

| Lần chạy | Bằng chứng terminal | Kết luận đúng phạm vi |
|---|---|---|
|Pure01|12PASS, ROOT quan sát0.9320891s; owned receipt/logs nguồn01|Kiểm12fixtures giả lập; không chứng minh native parity|
|Native01|REJECTED, ROOT terminal1.6197814s; worker_run/failurelog có|Pandas metadata `platform.machine→uname→socket.gethostname` bị broadsocketguard chặn. Chưa load Paper2/instantiatepolicy/reserve/callupdate. Đây là **avoidable setup failure**, không scientific mismatch|
|Pure02|14PASS, ROOT quan sát1.1860165s;12cases cũ+2metadata guards|Regression trên revision02; không cộng12+14 thành26samples hoặc26unique cases|
|Native02|REJECTED, ROOT terminal34.7511308s; ownedreason `TimeoutError: active deadline preserves cleanup reserve`|Owned process bị kết thúc để giữ cleanup reserve; không có terminalworker_run/failurelog. Toàn bộ research admission chưa đạt|

ROOT terminal observations tách khỏi elapsed trước receipt: native02 outer ghi34.547052145s trước receipt; owned helper ghi34.079090118s trong max36.054955338s/cleanup2; worker được cấp33.963205575s. Đây là các đồng hồ/phạm vi khác nhau, không thay thế nhau. Các timing ROOT cung cấp được gắn rõ provenance là observation từ ROOT, không giả rawworker terminal.

## 2. Native02 biết được và chưa biết được gì?

Ownedreceipt cho `actual_worker_in_job_before_GO=true`, `cleanup_accepted=true`, `job_active_after_cleanup=0`, `popen_handle_closed=true`, cleanup_errors rỗng. Vì vậy cleanup đã nghiệm thu dù nghiên cứu bị từ chối. stdout/stderr rỗng không chứng minh0nativecalls.

Reservation bền vững trước constructor giữ trần18policies/2160updates/6480predict. Hai trajectory receipt còn nguyên:

| Progressreceipt | Elapsed worker tại mốc | Cumulative completed updates | Cumulative predict | Legacy/fullpreview đã kiểm tại mốc |
|---|---:|---:|---:|---:|
|20000–PG/full|13.346649647s|120|360|120|
|20000–PG/empty|23.888545700s|240|720|240|

Hai endpoint có finalfingerprints khớp C13 tại chính hai mốc đó; đây chỉ là progress/admission cục bộ. Sau mốc thứ hai và trước hardtimeout: **actual total updates UNKNOWN, ít nhất240 và không vượt2160; predict ít nhất720 và không vượt6480**. Không được ghi actual0 hoặc actual240 như tổng cuối. Nativeallcall ledger mới nhất:29884is_mastered/7446mastery_score/480ready_set/240select; không biết tổng cuối vì hardkill trước workerreceipt.

Chỉ có dispatch/reservation/2trajectory receipts và `trace.jsonl.gz`67248B. Gzip là stream partial chưa đóng; CRC/recordcount chưa được kiểm và không parse/repair/extract research metrics từ nó. Không có bằng chứng một parity mismatch toàn cục; terminal reason được ghi là resource timeout. Không suy toàn bộ trường hợp chưa hoàn tất sẽ khớp.

Revision02 đã đi qua bootstrap metadata để đến native work, nhưng metadatafields/helpercounts chỉ chuẩn bị đưa vào terminalworker_run nên mất khi hardkill. **Không có durable metadatareceipt để khẳng định helpercount=0 hoặc trích OSfields.** Một revision sau nếu được duyệt cần persist metadatareceipt ngay sau phaseclosed, trước modelwork; không sửa/fill hồi tố bản02.

Source/plan/raw01–02 đóng băng trong inventory `prediction_mastery_failed_attempts_frozen01.json`. Snapshot trước metadatafix giữ23files với before/copy/afterSHA. Archiver sẽ copy raw nhỏ; partialgzip chỉ giữ path/size/SHA reference, raw gốc nguyên vị trí. Immutable cached3240gzip/nguồn cũng chỉ được tham chiếu theoSHA, không nhân đôi. Việc bundle manifest `completed` sau closure chỉ là **đóng gói thành công một batch research chưa accepted**, không PASSnative/RQ.

## 3. Ngân sách đã dừng và chẩn đoán throughput

Ledger bảo thủ:10oldpure+1.6197814native01+10newpure+34.7511308native02 = **56.3709122/60s**, còn3.6290878s. Phần còn lại không đủ một wholetrace; dừng native retry trong allocation này. Không chuyển số giây pure thực tế nhỏ hơn thành quyền chạy thêm, không ẩn reset60.

Source cho thấy hai chi phí có thể tránh, **chưa được benchmark định lượng**:

1. `capture()` làm4lần toàn bộpolicy→state_data→canonicalJSON→SHA mỗi snapshot (gốc trước, clone saucopy, clone saurefs, gốc saupreview):8640fullserializations nếu hoàn tất. Mỗi lần duyệt28states/memory arrays/counters/deques và tạo JSON dù modelpredict chỉ đọc. Full endpoint fingerprints và direct legacy parity vẫn cần giữ, nhưng không buộc4JSON mỗi event.
2. `sys.setprofile` được bật cho mọi Python/Ccall trong NumPy/Pandas/deepcopy/fingerprint/JSON. Callback vẫn đọc frame globals/module ở nonnativecalls để xét RNG; vì vậy chính các lần fingerprint/selector dataframe cũng tạo callback overhead. Native GAM graphsummary và dataframequestionselector vẫn có chi phí thật. Không có per-operation timer hoặc đối chứng tắtprofile để gán tỷ lệ timeout cho nguyên nhân cụ thể; không đổ cho RAM/Windowsfilesystem từ suy đoán.

Hai mốc progress đủ kết luận revision02 chưa đáp ứng allocation, không đủ dự báo runtime của full18trajectories hoặc nói metadatafix làm thuật toán chậm đi bao nhiêu.

## 4. Đề xuất rẻ hơn, cùng semantics — chưa implement/run

Giữ source native,18policies/queries/y/order,2160updates/6480predict,all2160legacy/fullpreview và18initial/final fingerprints. Không bỏ theta/pi/reference observables hay chọn subset. Native predict/_decayed_pi/_context đã được ROOT đọc AST là readonly; giữ deepcopy cho probes/preview.

- Thay4fullJSONhash/event bằng một **lightweight immutable byte/tuple view** đầy đủ các trường state/selector có thể đổi: floatbits, memory dtype/shape/rawbytes, counters/deques/timestamps/flags; đối chiếu view gốc và clone trước/sau probes. Source/constantparameters vẫn bind và endpoint canonicalfingerprints giữ đúng C13. Nếu cần giữ hash từngsnapshot để truy vết, tạo tối đa1hash/view thay vì4canonicalJSON; version rõ serializer, không giả nó là C13hash cũ. Đây là operational representation change phải review trước, không modelmethod change.
- Thay globalprofile bao mọi helper bằng các proxy/direct-call counters ở lớp ngoài (constructor/current/refpredict/update/preview/directS/M/R), và selectorcounter riêng nếu cần. Native internalcall caps có thể dùng early code-ID filter tối thiểu hoặc source-derived upperbound+explicit top-level counters; **không giữ nhãn “actual all-call counts” nếu không còn đo chúng**. RNG/teacher prohibition dựa trên exact source/callreachability và denyknownentrypoints, không thêm teacher/RNG để kiểm.
- Persist metadata/phase/callcounter progress sau mỗi trajectory; before-native globalreservation giữ nguyên. Hardkill cuối vẫn actualUNKNOWN≤reserved, không giả complete từ partial.

Trước bất kỳ nativebatch mới: ROOT có thể duyệt **một operational microbenchmark ≤5s,0native/model/teacher/RNG** trên fabricated28-state×fixedmemorybytes. So sánh4canonicalJSON+SHA với directbyteview và overhead globalprofile so với explicitcounter cho cùngfinite dummycall graph; kết quả/checksum/views phải exact, profilerstop/restore, fixed operationcount, không tuning theo desiredspeed. Mục đích đo overhead thiết kế, không dự báo GAMfulltrace/inference/GPU hoặc chấp thuận nghiên cứu. Allocation operational này cần được khai riêng; original56.3709122s và batch thất bại giữ nguyên. Chưa có sourcefix/benchmark/native retry nào từ tài liệu này.

