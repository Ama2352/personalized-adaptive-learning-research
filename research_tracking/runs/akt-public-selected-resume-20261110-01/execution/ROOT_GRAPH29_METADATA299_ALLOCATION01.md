# Phân bổ kiểm metadata hiện hành sau GRAPH29

Root duyệt một lượt collection trước, chỉ chạy tests sau khi đã đọc và ghim SHA của collection thật. Dùng `.venv` của repository. Đây là gói kiểm phần mềm local theo yêu cầu engineering của người dùng.

Nguồn GRAPH29 candidate02 đã được Root đọc, kiểm chéo độc lập và áp dụng ở sáu file. Bộ metadata02 hợp 221 ca cũ, 40 ca GRAPH29 chạy lạnh và 38 ca checkpoint opaque. Dự kiến 299 ca được chọn. Collection và JUnit thực tế phải xác nhận số lượng cùng từng ID. Giữ đúng ba ca loại trừ đã nêu trong packet, gồm probe import native và hai ca EarlyStopping cần Torch thật.

Packet `351bbf1788c817e56468e612c4d91044056ecf2c0288c5effed27703b5707463`, worker `5203ad5be2959dc0515840b022dbe8a6dfc15e9dc45fc9e2383de1f0eef98235`, controller `b0eb00a649a1de9b8e92c353d750a64f4872a9f7cd1675281e1c1befcb99eee2`. Root kiểm lại 44 source và 11 runtime pins trước chạy.

Collection giữ trần whole20/owned17/worker13 giây, cleanup3 giây. Tests giữ whole120/owned115/worker110 giây, cleanup3 và final reserve5 giây. Profile metadata đã đo ở lượt trước giữ worker128MiB, free floor1GiB và admission1280MiB. Đây là samples hợp tác trong worker, chưa là hard quota RAM hoặc số đo whole Job. Các profile native và GPU giữ nguyên giới hạn riêng.

Không có world, forward/backward, Adam hoặc truy cập corpus được cấp từ gói này. Các launch/checkpoint trong fixtures là metadata dựng tay. Cần kiểm actual cold scientific imports, nguồn trước/sau, khôi phục môi trường, exact IDs/JUnit, owned Job0 và hậu kiểm thời hạn. Exit0 riêng lẻ chưa đủ nghiệm thu. Mọi failure được giữ, không tự retry.

Gộp hai nhóm kiểm trong một nguồn hiện hành để tránh chạy lại từng nhóm và tạo hai cold process riêng. Hai ca EarlyStopping thật sẽ ghép với native checkpoint16 trong gói18 riêng, giữ nguyên workload NN. Nghiệm thu metadata chưa xác nhận public resume, crash recovery hoặc CUDA.

Sau NO_GO02 trướcchild, harness03 bổ sung --attempt hai chữ số để giữ source qua các lần admission, không tự retry hoặc sửa output cũ. Root đã đọc diff và AST/pins. Packet faa0b50a56c071374b30a4fa43ff498131dad15c21d16df9df02192397f8363e, worker aeeaed2f94a5cb3dcbd1dbf6a5b68034ef828b56f0b97eb543e8bc4d4442f97d, controller 71c30bbe71eeb2345a29eebf1a5b7e3f1efc25cadfc3b5a6b5ef18bf351c2941. Root chọn thêm cushion512MiB trên pipelineadmission1280MiB từ mức giảm404.508.672B đã quan sát, thay lựa chọn buffer2GiB ban đầu chưa có dispatch. Ba samples mới2.257/2.262/2.259GB đủ1792MiB. Giữ nguyên cap/floor của pipeline, Root duyệt một collectattempt03 trước tests cùngattempt sau actualcollectionreview.
