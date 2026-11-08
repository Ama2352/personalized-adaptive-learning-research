# Ước lượng độ tin cậy cạnh từ TRAIN mô phỏng — kết quả bước Method24

## Mục đích và kết quả đã có

RQ3 cần một nguồn điểm cho từng cạnh có thể kiểm chứng được, thay vì mặc định mọi quan hệ đúng như nhau hoặc dùng nhãn cạnh thật của simulator để giả làm ước lượng triển khai. Ngày08/11, ROOT đã duyệt và chạy đúng một operation CPU theo recipe Method24 đã đóng băng, chỉ khớp mô hình từ48người học TRAIN ×210tương tác. Không dùng nhãn cạnh thật, neural model, Holdout hoặc Modal.

Lượt chạy **được outer chấp nhận**, terminal RC0,45,1694439giây trong trần120giây; active cap110giây. Có **2.352 solver fits thật**, không chỉ slot dự kiến. Toàn756cặp có hướng giữa28khái niệm đủ điều kiện theo recipe; xuất272.160hàng OOF theo cạnh và10.080hàng baseline. Có304cạnh với chênh lệch dự báo dương được cân nhắc; thuật toán chọn đồ thị có hướng không chu trình lấy31cạnh theo ngân sách định trước, bỏ2đề xuất gây chu trình trước khi đủ ngân sách.

Điểm này là mức ổn định bootstrap của lợi ích dự báo có điều kiện, **không phải xác suất cạnh tiên quyết đúng**.756supported summaries không phải756quan hệ thật;31cạnh không phải bằng chứng khôi phục đúng đồ thị. Chưa đối chiếu nhận diện cạnh đúng/sai, chưa huấn luyện CG-AKT hoặc đánh giá lợi ích chọn bài/học tập. Ba folds nội bộ phục vụ OOF của surrogate trên TRAIN; đây không phải full Development CV của các mô hình KT.

## Ranh giới dữ liệu và tài nguyên

Public reader kiểm schema9tệp đầu vào công khai và DONE, sau đó chỉ role TRAIN được chuyển vào optimization. Không nói toàn operation chỉ mở tệp TRAIN. Selection/calibration không dùng để fit, xếp hạng cạnh hoặc chọn cấu hình. Source11, recipe, runtime profile, request và các tệp public đều được ghim và đối chiếu lại sau chạy.

Peak RSS quan sát263.442.432B, RAM available nhỏ nhất1.599.983.616B; trần RSS512MiB/free floor1GiB. Monitor và inline checks là quan sát hợp tác, không hard OS quota. Owned Job xác nhận worker membership trướcGO, cleanup accepted, active0 và handle closed. CPU thread1,0teacher calls,0neural optimizer steps và0USD Modal. Không retry operation hoặc đổi recipe theo kết quả.

Một lỗi môi trường đã được chẩn đoán trước lượt này: Windows có thể gọi system `cmd /c "ver"` khi xác định platform. Bản sửa chỉ cho phép command metadata hữu hạn trong giai đoạn khởi động và chặn Popen trong giai đoạn fit. Sau review độc lập, thêm kiểm live counters trước/sau DONE để một exception bị thư viện bắt không làm receipt cũ che mất attempt bị chặn. Revision43purePASS và revision45purePASS là hai bản kiểm riêng, không88ca độc lập. Smoke ABI trước đó có2fits trên dữ liệu tự dựng, không cộng vào2.352fits của corpus.

## Bằng chứng và vị trí lưu

[Bundle đã đóng](../runs/edge-confidence-windows-bootstrap-20261108-01/README.md) giữ113outputs nhỏ, nguồn đã chạy, các kiểm43/45, failure smoke đầu tiên, smoke ABI thành công, request/ROOT review và receipts native. Manifest kiểm output integrity; validity của estimand vẫn theo [đặc tả Method24](edge_confidence_method24_plan_20261108.md).

Native operation có14tệp,69.519.761B tại `artifacts/akt/local-tests/akt-research-runner-20261108-01/method24-native01/`. Năm exports lớn (`fit-ledger.jsonl`, `baseline-oof.csv`, `edge-oof.csv`, `learner-deltas.csv`, `edges.jsonl`) giữ nguyên tại đó, không đưa Git hoặc nhân đôi trong bundle. `native_artifact_inventory.json` ghi đủ14đường dẫn, kích thước, SHA trước/sau;9JSON nhỏ được copy byte-exact. Không sửa corpus hoặc artifacts lịch sử. Terminal observation của ROOT được giữ riêng với raw worker/outer receipt, không giả thành log do worker phát sinh.

## Việc tiếp theo

1. Làm bộ đọc artifact có kiểm đầy đủ lineage và trạng thái outer; chưa đưa raw score vào graph model chỉ vì có DONE.
2. Đánh giá confidence trên các điều kiện đồ thị đã định, giữ riêng privileged oracle diagnostic với performance không dùng oracle. Không chỉnh recipe để tăng điểm khôi phục sau khi xem nhãn thật.
3. Chốt recipe graph neural tối thiểu và chính sách cạnh unsupported trước implementation nghiên cứu; draft25 chưa tự thành phương pháp được adopt.
4. Hoàn tất full software Gate/CUDA lifecycle và so AKT không đồ thị, đồ thị cố định, confidence/gate theo cùng protocol trước mọi kết luận RQ3.
