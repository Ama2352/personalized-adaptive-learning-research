# RQ1 — Replay native mastery CPU09 chưa đạt xác minh toàn bộ

Ngày09/11/2026. Hồ sơ kỹ thuật của hai suite pure đạt và năm lượt native bị từ chối. Nhánh native đã dừng theo giới hạn được duyệt. Chưa có bảng accuracy, confusion hoặc kết luận khoa học mới về mastery từ nhánh này.

## Mục tiêu và ranh giới diễn giải

Phân tích response reliability đã chỉ ra sai lệch trái dấu giữa các persona trên các bài thực sự được phục vụ. Nó chưa xác định native mastery M đúng hay sai. Cache CPU09 còn lưu `theta_before`, tức theta thật của concept đang được hỏi trước đáp án và learning update. Nguồn Paper2 dùng ngưỡng1250 cho true mastery. Vì vậy, có một cách đối chiếu hẹp bằng replay estimator từ đúng q/y/time đã ghi, sau đó so native M với `theta_before>=1250` trên queried concept. [Response reliability](rq1_response_reliability_diagnostic_20261109.md), [cache CPU09](../runs/cpu-factorial-20261107-01/README.md).

Hợp đồng giữ toàn bộ120streams,14.400events,10seedclusters cũ và bốn arms. Mỗi stream phải khớp selected concept/question/difficulty và bit float64 của P trước update. Đồng hồ được dựng từ source, không được gọi là timestamp đã lưu trong trace. Native M dùng stored theta_est và stored pi_task, còn P dùng pi đã decay theo thời điểm. Hai loại pi được giữ thành các trường riêng.

Projection sang estimator chỉ gồm step/concept/question/P/y. Cache reader có parse và kiểm numeric các trường oracle trước parity. Việc phân loại `theta_before>=1250`, join truth và lập confusion chỉ được phép sau **toàn bộ**14.400events đạt parity và nguồn được kiểm lại. Không có phép chuyển oracle vào estimator. Quần thể này cũng khác reference-mixture criterion tại τ và khác mastery-rate toàn28concept sau update. [Feasibility nguồn](../runs/rq1-cpu09-native-mastery-replay-attempts-20261109-01/RQ1_CPU09_NATIVE_MASTERY_REPLAY_FEASIBILITY02.md), [review ngữ nghĩa](../runs/rq1-cpu09-native-mastery-replay-attempts-20261109-01/RQ1_CPU09_NATIVE_MASTERY_STATIC_REVIEW01.md).

## Các kiểm tra nhỏ đã thực chạy

| Lượt | Kết quả thực tế | Phạm vi | Elapsed lưu trong outer |
|---|---|---|---:|
| Pure replay |12methods,9subtests,0failure/error/skip|Dict dựng tay và fake deterministic policy, không đọc cache hoặc import NumPy/Pandas|1,6316085s/30s|
| Pure source adapter |5methods,0failure/error/skip|12lần gọi helper trên nguồn module dựng tay,7body compile trả về và5entry bị từ chối|1,9602711s/30s|

Suite đầu kiểm mốc clock28/56, selector side effects, readout trước update, phân biệt stored/decayed pi, lỗi parity ở stream cuối và việc chặn truth khi kiểm lại nguồn thất bại. Suite thứ hai kiểm real module metadata, đăng ký namespace trước body, parent attributes, hash sai, preexisting module và đường parent sai. Nó khôi phục các entry/attributes đã thay sau từng fixture. Cả hai có owned cleanup đạt và Job0. Các trường hợp dựng tay chưa chứng minh replay native trên cache hoàn tất. [Pure12 receipt](../runs/rq1-cpu09-native-mastery-replay-attempts-20261109-01/replay_pure__result.json), [adapter5 receipt](../runs/rq1-cpu09-native-mastery-replay-attempts-20261109-01/adapter_pure__result.json).

## Năm lượt native và nguyên nhân dừng

Các thời gian dưới đây lấy từ `final.json` của outer. Chúng chứa thời gian worker/owned lồng nhau, không cộng các thành phần lồng nhau thành runtime mới.

| Lượt | Outer elapsed | Nguyên nhân được xác nhận | Trạng thái native |
|---|---:|---|---|
|01|0,3154979s|Log cap2MiB vượt cap helper1MiB, bị từ chối trước GO. Sau đó cố ghi receipt vào OWNED chưa tồn tại tạo lỗi thứ hai, receipt gốc vẫn nằm trong final.|Không tạo worker/owned namespace hoặc INNER|
|02|2,8585531s|Pandas/dateutil cần resource UTC, audit chỉ cho runtime code và inputs đã pin.|Profiler chưa ghi constructor/estimator body. INNER có metadata và failure|
|03|3,3201092s|Normal import thử đọc project PYC cũ của `paper2_reference`; `-B` chỉ chặn ghi PYC.|Profiler chưa ghi constructor/estimator body. INNER có metadata và failure|
|04|127,8221705s|Monitor đạt4.001samples, vượt journal sample cap4.000 và terminate owned Job trước cap180s.|Chỉ có native metadata/reservation. Actual native counts UNKNOWN trong reservation bounds|
|05|174,0944021s|Worker hết allocation173s. Monitor mới hoạt động bình thường, nhưng replay chưa hoàn tất.|Có failure ledger, truth chưa được chấp nhận, không có full parity/confusion output|

Bốn lỗi thiết lập đầu được xử lý bằng các derivative riêng, giữ nguyên nguồn và artifacts trước đó. Log cap được hạ xuống65.536bytes. Hai resource UTC111bytes được pin riêng, không mở timezone wildcard. Sáu project modules được compile từ exact `.py` bytes đã pin với real module names/package metadata, không đọc hoặc xóa project PYC. Cadence monitor sau cùng dùng0,1giây, giữ nguyên các giới hạn nguồn, thời gian và RAM. [Review trước lượt cuối](../runs/rq1-cpu09-native-mastery-replay-attempts-20261109-01/ROOT_RQ1_CPU09_MASTERY_NATIVE_REVIEW05.md).

Ở lượt04, family peak167.587.840bytes và available RAM thấp nhất3.225.903.104bytes vẫn nằm trong allocation1GiB/free2GiB. Lỗi đã xác nhận thuộc sample cap, không phải RAM floor hoặc deadline180s. Owned cleanup đạt Job0 sau khi monitor terminate. Việc không có failure ledger trong INNER của lượt này không có nghĩa native đã làm0calls. [Final04](../runs/rq1-cpu09-native-mastery-replay-attempts-20261109-01/native04_outer__final.json).

## Lượt cuối cho biết điều gì?

Lượt05 lưu worker elapsed173,0554238s và outer elapsed174,0944021s. Monitor có1.594samples, errors rỗng, family peak170.905.600bytes, available RAM thấp nhất3.357.061.120bytes, không terminate Job. Worker tự báo `worker elapsed allocation` trong phase `matched_estimator_replay_before_truth`. Owned cleanup đạt và Job còn0process. Như vậy cấu hình replay kèm global profiler hiện tại chưa hoàn tất trong thời hạn được duyệt, dù các quan sát RAM vẫn nằm trong bounds.

Failure ledger ghi profile-call events cho25constructor entries,2.963select,2.963predict,2.963update và8.889`_decayed_pi`. Các return events có cùng số đếm. Python profile return events có thể xuất hiện khi exception unwind, nên ở lượt bị từ chối chúng không tự chứng minh số body hoàn tất thành công. Không dùng các số này làm accepted sample count hoặc kết quả partial mastery. [Failure05](../runs/rq1-cpu09-native-mastery-replay-attempts-20261109-01/inner04__failure.json), [final05](../runs/rq1-cpu09-native-mastery-replay-attempts-20261109-01/native05_outer__final.json).

Chưa có phép đo profile-OFF tương ứng. Vì vậy chưa tách được chi phí riêng của global profiler khỏi chi phí native selector/Pandas, capture và các guard. Không ngoại suy runtime toàn bộ corpus, throughput GPU hoặc thời gian nghiên cứu từ các partial counters này.

## Trạng thái bằng chứng và việc còn thiếu

Toàn bộ năm native attempts giữ verdict REJECTED. Chưa có toàn bộ14.400P/query parity, source-postcheck tại ranh giới hoàn tất, truth join hoặc confusion được nghiệm thu. Nhánh này không bổ sung phát hiện khoa học về độ đúng native M, không thay đổi kết quả response reliability đã đóng và không đánh dấu RQ1 hoàn tất. Mọi hash kiểm tại lúc đóng gói chỉ chứng minh bytes hiện tại và bản sao, không biến source-after rỗng trong các native final thành post-run guard đã đạt.

Nguồn nghiên cứu vẫn là các histories CPU09 đã có. Các workers chỉ replay estimator, không gọi teacher/world để tạo dữ liệu mới, không fit NN hoặc đổi threshold. Mười seed cũ giữ nguyên vai trò, không có independent N mới. Ngay cả khi replay sau này đạt, queried-concept truth theo simulator cũng cần giữ giới hạn với mastery của người học và criterion V1.

Không có lần native thứ sáu hoặc tăng cap trong hồ sơ này. Bước khả thi tiếp theo là một đề xuất vận hành riêng để đo chi phí observer trên một world120events đã có, trước khi quyết định tối ưu hoặc chia bounded shards. Đề xuất đó chưa được triển khai hoặc chạy trong lượt này.

## Nguồn và lưu trữ

| Artifact | SHA-256 |
|---|---|
| Pure12 result |`05542d273613da117ede00d2c90421735183fb5af41dc6421f902c52d6ca38ee`|
| Adapter5 result |`ff7089d8112df51e6b577779839443e5a4fcbe95a85896e8793ad211ec01b517`|
| Native01 final |`1d9a6910bc5c8cf58e3677e380b31bd30a0ca524753e0232a230d74578957e4c`|
| Native02 final |`42ca471369f2d2cfb92c18e9c5ae8f9adc8d0fa041507c611538162faeb422fe`|
| Native03 final |`3406e35320346e038d6c4279d7b730ac2a90f3a551ac79d420fb0af0234c626b`|
| Native04 final |`181f491b335f7313aed12cf3437b37db0bfd36434e38e58cf176ebfbe7752886`|
| Native05 final |`67563ec93cb263748710f26a2c756c16c69b0d949796c42f2ab11fe461bc59d0`|

Canonical report và archiver được chuẩn bị để Root review/dry/close riêng. Bundle dự kiến giữ toàn bộ worker/controller/contract/packet versions, các source-only snapshots, reviews, raw logs và receipts. Hai memory journals lớn chỉ tham chiếu exactpath/size/SHA. Gzip CPU09 và dependency/runtime files giữ tại vị trí gốc, không sao chép. [Hồ sơ dự kiến](../runs/rq1-cpu09-native-mastery-replay-attempts-20261109-01/README.md).
