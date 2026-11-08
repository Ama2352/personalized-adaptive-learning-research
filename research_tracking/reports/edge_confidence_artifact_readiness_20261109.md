# Bộ đọc độ tin cậy cạnh — đã kiểm với artifact thực

`src/knowledge_tracing/edge_confidence_artifact.py` đã nhận đúng artifact Method24 do lượt TRAIN48×210 tạo ra, kiểm các ràng buộc và trả31điểm của đồ thị ứng viên. Lượt đọc03 được outer chấp nhận trong1,3800554giây, trần30giây; không fit lại, không gọi mô hình neural và không đọc nhãn người học hay oracle. Public corpus chỉ mở đúng `bank.json` đã ghim để kiểm danh tính item/concept của caller.

API nhận external pins của outer/request/terminal/owned/DONE cùng training binding và read limits. Nó kiểm cả14output hashes,13hashes trong DONE, source/runtime/public provenance và trạng thái cuối; pending marker riêng lẻ không đủ. CSV lớn chỉ được stream-hash, không parse hoặc nhân đôi. Edge summaries phải đủ756cặp có hướng, không trùng/thiếu, có denominators hợp lệ. Kết quả giữ unsupported/null khác supported score0. Binding đồ thị khai báo được tách khỏi binding đồ thị học, vốn cần đủ ngân sách31cạnh và DAG đúng cấu trúc.

**66kiểm thử trên dữ liệu tự dựng đạt PASS**, gồm giới hạn byte/time, path alias, binding sai, artifact pending/failure, null/0, resource snapshots và biên seed64bit. Đây là bằng chứng phần mềm; lần đọc artifact thực là bước kiểm tương thích riêng. Bộ đọc không tự biến điểm ổn định dự báo thành xác suất cạnh đúng, không tự chuyển null→0, chưa nối gate/CG-AKT hoặc tạo checkpoint fitted.

Hai lượt đọc thất bại trước đó được giữ nguyên:

- Lượt01: consumer yêu cầu hai resource snapshots bằng hệt nhau, trong khi producer đã lấy thêm mẫu kiểm tra giữa hai thời điểm (2.582và2.584samples). Bản sửa kiểm schema/bounds của cả hai và tính tích lũy: samples/peak không giảm, minimum free RAM không tăng.
- Lượt02: consumer áp giới hạn signed63bit cho bootstrap seed, trong khi producer dùng8bytes SHA unsigned64bit. Bản sửa chỉ áp đúng range cho seed, không nới giới hạn các counts khác. Đã kiểm cả biên0,2⁶³−1,2⁶³,2⁶⁴−1 và các giá trị không hợp lệ.

Không sửa producer hoặc artifact để qua các kiểm này. [Bundle106outputs](../runs/edge-confidence-artifact-integration-20261109-01/README.md) giữ revisions58/66pure, cả ba lượt đọc, source snapshots, ROOT reviews, logs và SHA trước/sau copy. [Bundle60pure cũ](../runs/edge-artifact-cross-ready-engineering-20261109-01/README.md) thuộc source trước hai sửa lỗi và không được dùng làm bằng chứng current-source compatibility. Không cộng số ca của các revisions thành thí nghiệm độc lập.

Greedy-ranking fidelity của đồ thị vẫn dựa trên producer và artifact được review/pin, không có tuyên bố bộ đọc đã thực hiện một kiểm chứng greedy độc lập. Runtime provenance là của producer lịch sử, không phải attestation môi trường hiện tại. Chưa full software Gate, CUDA readiness hoặc hiệu quả của CG-AKT. Bước kế tiếp là kiểm chung source hiện hành rồi nối artifact này vào recipe mô hình đã được chốt.
