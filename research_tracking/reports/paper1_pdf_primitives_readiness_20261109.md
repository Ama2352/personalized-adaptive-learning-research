# Quy tắc mô phỏng riêng theo PDF Paper1 đã qua kiểm nhỏ

## Mục đích và phần đã có

Theo D37, PDF Paper1 là nguồn chuẩn thiết kế và kết quả kế thừa. Module mới tại `src/knowledge_tracing/paper1_pdf/simulator.py` giữ riêng world latent, estimator Elo và continuity controller, dùng lại representation item bank. Nguồn notebook và các kết quả lịch sử được giữ nguyên.

Đã kiểm26ca synthetic trên CPU local. Các ca bao phủ K theo số lượt trước cập nhật, dự báo trước đáp án, tập sẵn sàng theo toàn bộ tiên quyết, ưu tiên chương hiện tại, xếp hạng và tie, tách latent khỏi estimate, learning+12/cap1500, thống kê chuyển/quay lại chương và từ chối input sai trước mutation. Fixture A→B→A chỉ kiểm điều kiện controller trên DAG dựng tay, không thay kết quả zero re-entry của các tested profiles trong PDF. [Log và nguồn đã đóng](../runs/paper1-pdf-primitives-engineering-20261109-01/README.md), [output26tests](../runs/paper1-pdf-primitives-engineering-20261109-01/attempt03__stderr.log).

## Quá trình và giới hạn

Lượt01 lỗi import do bộ chạy thiếu đường src trong child environment. Lượt02 đạt25tests. Peer review phát hiện payload của frozen prediction có thể bị cưỡng ép sửa đồng bộ; đã lưu riêng payload ban đầu để kiểm trước observe và thêm một negative test. Lượt03 đạt26tests trong0,1958331giây dưới cap30giây. Gói giữ cả logs và source trước sửa. Kiểm payload bảo vệ tính nhất quán API trong phạm vi đã thử.

Các kiểm này dùng domain dựng tay. Hàm kiểm shape28concept/84item/25–31edges và3intra+3cross additions chưa chứng nhận bytes của domain thực. Các CSV Paper2 được khai báo như input ứng viên có provenance, chưa được gọi là exact historical input của PDF.

Còn phải nối input thật được version rõ, profile/RNG, B0, unlock policy và runner có budget trước các đối chứng RQ1–RQ2 theo PDF. Chưa chạy matrix450runs hoặc tái lập số liệu lịch sử. Chưa kết luận mới về hiệu quả đồ thị từ các kiểm kỹ thuật này.


## Cập nhật sau kiểm primitives, nạp bộ input ứng viên

Bộ nạp riêng tại `src/knowledge_tracing/paper1_pdf/domain.py` đã qua24fixtures trong1,5103692giây dưới cap30giây. Một lượt đọc5CSV thật đã pin hoàn tất0,1828113giây dưới cap5giây. Đã xác nhận28nodes/84items/B1=25/GA=31, subset và3intra+3cross additions. Chapter map gốc có8keys ngoài domain, được giữ rõ trong metadata, active mapping chỉ dùng28concepts. Các CSV gốc không thay đổi. [Bundle13outputs](../runs/paper1-pdf-domain-engineering-20261109-01/README.md), [receipt nạp thật](../runs/paper1-pdf-domain-engineering-20261109-01/actual_domain_load.json).

Identity của input ứng viên là96e83ad02e21cdd52617cc9c07c1068d2ecfc5dd4983d11a81d8f02326b65f91. Mỗi graph có traversal topo lexicographic riêng, đây là lựa chọn triển khai mới được ghi rõ. Chưa chọn B0 topology, profile/RNG, unlock policy hoặc chạy matrix. Nạp bộ input ứng viên không chứng nhận exact historical PDF input identity. Câu còn phải nối input ở mục trước mô tả trạng thái trước cập nhật này.
