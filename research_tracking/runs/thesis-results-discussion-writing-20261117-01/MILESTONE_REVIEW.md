# Đếm mốc nghiệm thu theo nguồn ngày 17/11

`PUBLIC_MILESTONES_20261117.json` rà riêng 25 task gốc T01–T25, giữ nguyên acceptance và nhãn RQ trong `TASKS.json`. Toàn file có 182 task; 157 task bổ sung không tham gia mẫu số. Mọi hàng có lý do và nguồn. Authority không được chỉnh sửa.

## Kết quả của checklist gốc

| Trạng thái | Số task |
|---|---:|
| COMPLETE | 5 |
| PARTIAL | 17 |
| APPROVAL_NEEDED | 1 |
| OPEN | 2 |

Năm task đóng trong phạm vi hẹp gồm T03 nguồn PDF Paper1, T08 CUDA image/entrypoint hữu hạn, T09 bốn variant và causal guards, T14 ladder CUDA nhỏ/checkpoint/export, T21 demo artifact có API/UI. T21 đóng acceptance của task replay nhưng demo đầy đủ trong đề cương còn cần mastery và lựa chọn hoạt động từ model hiện đại.

T11 vẫn một phần. Các receipt đã kiểm gồm CPU 7 vòng so với 5+2 và T4 hai bước có resume, chưa xác nhận đúng phép 20 so với 10+resume10 mid-epoch của task gốc. T07 giữ một phần vì các phép publish thật chưa tự chứng nhận hết hợp đồng fault/permission/race. T02 giữ yêu cầu xác nhận phạm vi decision record advisor. Các nhiệm vụ khoa học rộng như T19–20 vẫn một phần dù có selected fits/pilot.

Đếm máy móc cho 5/25 = 20% mốc backlog đã đóng. Với nhãn RQ gốc, tỷ lệ tương ứng là RQ1 1/11, RQ2 0/13, RQ3 4/23. Các số này chỉ đếm task đã đạt toàn acceptance. Backlog trộn hạ tầng nhỏ và nghiệm thu khoa học rộng, đồng thời nhiều nhãn tập trung RQ3. Vì vậy, chúng không đủ làm tỷ lệ hoàn thành nội dung ba RQ hoặc toàn KLTN. Các task dùng chung còn xuất hiện ở nhiều mẫu số RQ.

## Các tỷ lệ có thể công bố kèm phạm vi

| Checklist/phase | Đã đóng | Tỷ lệ đúng phạm vi |
|---|---:|---:|
| RQ1, bảy claim chẩn đoán C01–C07 | 5/7 | 71,4% claim hẹp |
| RQ2, bảy claim ba bẫy T1a–T3b | 6/7 | 85,7% claim hẹp |
| Junyi expert outer4, selected-fit A0–A3 | 4/4 | 100% phase này |
| Junyi expert outer4, refit A0–A3 | 4/4 | 100% phase này |
| Junyi expert outer4, suy luận calibration | 4/4 | 100% phase này |
| Junyi expert outer4, fit temperature đã xác minh | 2/4 | 50% phase này |
| Junyi expert outer4, đánh giá outer độc lập | 0/4 | 0% phase này |
| Grade10, selected-fit bảy AKT và hai comparator hiện đại | 7/9 | 77,8% block này |

RQ1 còn C04 mastery/calibration và C07 learning outcomes fitted. RQ2 còn T3b predictive order controls. Sáu chiều điều kiện cuối gồm history, training support, graph noise, learner profile, loại cạnh nội/liên chương và selection/simulator đều có bằng chứng một phần, chưa khép nghiệm thu cuối. Do đó 85,7% claim ba bẫy chưa đại diện 85,7% RQ2.

Block Grade10 9 cấu hình đếm bảy cấu hình A0/A1–A3 expert/learned cộng SAKT/GKT main. Kết quả engineering nhỏ của SAKT/GKT không được tính là selected-fit chính. GAM/BKT tham chiếu và các Junyi learned conditions nằm ngoài mẫu số riêng này, vẫn giữ trong phạm vi cần theo dõi.

## Khuyến nghị dùng khi báo tiến độ

Báo số claim hoặc phase đã khép cùng mẫu số và phần còn thiếu. Giữ tỷ lệ tổng ba RQ/KLTN ở trạng thái chưa có thang đo nghiệm thu có trọng số được thống nhất. Không suy tỷ lệ ấy từ số test, số artifact, số epoch hay số folder. Việc đóng thêm một phase có thể cập nhật trực tiếp bộ đếm tương ứng mà không đổi mẫu số để làm tiến độ cao hơn.

Đây là rà soát read-only và phân loại đề xuất cho root review. Không cập nhật `TASKS.json`, proposal, hai báo cáo GVHD, nguồn model hoặc dữ liệu. 56 tham chiếu bằng chứng theo task đã kiểm đường dẫn tồn tại. Kiểm này không hash lại toàn repository hoặc chạy lại thí nghiệm.
