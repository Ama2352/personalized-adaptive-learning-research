# Kiểm nguồn trước lượt đối chiếu toàn bộ cache CPU09

Ngày 09/11/2026. Root đã đọc toàn bộ worker, controller, contract và API replay nguyên bản. Phạm vi là 120 lịch sử cũ, mỗi lịch sử 120 tương tác, tổng 14.400 tương tác. Không sinh đáp án, người học hoặc tham số mô hình mới. Kết quả chỉ mô tả các khái niệm thực sự được hỏi trong pilot cũ.

Worker SHA `703875efd07854874dc68c042ef5a7f1a84b83be504e8c090c94e418d437cebc`. Controller SHA `feba22d87f10adf7b0065d6ace261b08c4ca4c53d3be27a289ecaef513351900`. Contract SHA `6cfd2cfbe6d3398ea96128c2dcf72a1cad9da052c82b1289a9f6527afc6822d8`.

Mỗi policy được quan sát đúng một lần, khôi phục class trước policy tiếp theo. Dự đoán, câu hỏi và độ khó phải khớp từng bit với cache trên toàn bộ 14.400 dòng. Cả 19 trường readout được ghi lossless, đóng file, fsync và kiểm SHA trước khi gọi evaluator truth nguyên bản. Policy chỉ nhận projection quan sát, đáp án hiện tại chỉ vào update sau prediction và capture. Controller đọc lại theo dòng, kiểm 136 nhóm, 120 observer receipts và toàn bộ confusion counts. Truth là theta thực trước tương tác của khái niệm được hỏi đạt 1250. Native mastery còn đòi pi_task lưu trong state không vượt 0,55.

Allocation bảo vệ cho một lượt mới có trần tổng 300 giây, worker 270 giây, owned 285 giây và cleanup reserve 5 giây. Giới hạn RSS cả process family 1 GiB, RAM hệ thống còn trống ít nhất 2 GiB. Tối đa 16 MiB output. Chỉ khởi chạy khi kiểm RAM ngay trước chạy đạt giới hạn và còn biên cho worker. Không chạy đồng thời native workload khác. Nếu thất bại, giữ raw outputs và dừng để xác định nguyên nhân, không tự động retry. Timing một lịch sử đã nghiệm thu là cơ sở chọn biên bảo vệ, chưa phải benchmark tốc độ đủ 120 lịch sử.

Readouts và truth sidecar mới giữ tại `experiments/gam_kt/results/rq1-cpu09-native-mastery-20261109-01`. Logs điều khiển giữ tại vùng chuẩn bị, sau đó lưu bundle nhỏ có tham chiếu. Không ghi đè source, dữ liệu hay bundle lịch sử. Các seed đã dùng lại, các arm có thể đi theo lịch sử khác nhau, nên không diễn giải chênh lệch pooled là hiệu ứng nhân quả của graph. Lượt này không chứng nhận hoàn tất RQ1 hoặc cho phép chi GPU.

Quyết định khởi chạy còn phụ thuộc kiểm chéo nguồn độc lập và RAM tại thời điểm chạy. Tài liệu này ghi review của Root, không thay phê duyệt phương pháp của GVHD.
