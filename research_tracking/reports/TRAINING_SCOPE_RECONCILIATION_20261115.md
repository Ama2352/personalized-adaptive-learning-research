# Đối chiếu phạm vi training KLTN ngày 15/11/2026

## Kết luận sau đọc lại đề cương

Đã đọc trực tiếp PDF đề cương do người dùng gửi, trang2–4. Bản Desktop có SHA khớp inventory08/11 và bản trong paper2. Đề cương yêu cầu AKT, SAKT, GKT, GAM-KT, Graph-GAM-KT và BKT tham chiếu; hai môi trường Junyi/Grade10; đồ thị chuyên gia/học dữ liệu/nhiễu; đánh giá dự báo, quyết định và vòng kín. Không ấn định5fold, sốepoch, sốtrainingseed hoặc tích đầy đủ mọi model với mọi graph trên cả hai môi trường. Trang4 cho phép kiểm ổn định bằng nhiều phép chia **hoặc bootstrap**. Bootstrap người học không thay được kết luận về biến động do trainingseed hoặc nhiều phép chia.

Protocol nhóm08/11 đã chọn một Junyi fold4 và một trainingseed để tiết kiệm. Đó là phạm vi development đang thực thi. Chưa có căn cứ lấy5fold làm điều kiện bắt buộc hoàn tất toàn KLTN. Không được so trực tiếp kết quả một fold hiện tại với trung bình5fold lịch sử rồi gọi là đối chứng cùng dữ liệu và giới hạn thông tin.

## Phần training đã xác nhận

| Môi trường | Đã có | Giới hạn |
|---|---|---|
| Junyi | A0/A1/A2/A3 expert hoàn tất selected-fit; A0/A1/A2 refit đủ9epoch | A3 lần quan sát cũ đủ7epoch, checkpoint epoch8/bước256. Phiên T4 mới phải đọc Drive trước xác nhận tiến độ mới |
| Grade10 |7checkpoint selected gồm A0, A1/A2/A3 × expert/learned |7archive đều có COMPLETE_MAIN_SELECTED_ONLY_CANDIDATE; chưa refit/calibration. Epoch đã chọn lần lượt5/5/4/4/4/4/4 |
| SAKT/GKT | Có source và selected engineering trên corpus10×84 | Chưa thấy model nghiên cứu Junyi hoặc Main60 tương ứng. Không tính engineering checkpoint là đã hoàn tất baseline nghiên cứu |
| BKT/GAM | Có kết quả lịch sử, được giữ nguyên | BKT là tham chiếu; matched GAM/Graph-GAM trong protocol mới cần đối chiếu cohort vàfit, không mặc nhiên tái dùng như cùng trainingpopulation |

Nguồn trực tiếp gồm [epochplanJunyi](../runs/junyi-refit-pipeline-20261114-01/epoch-plan.json), [tiến độ](../runs/junyi-refit-pipeline-20261114-01/refit-loop-progress.json), MODEL_INDEX của các gói model tại experiments/akt/results và7selected-terminal/COMPLETE đọc trongarchive Grade10. [SAKT](../runs/sakt-selected-engineering-20261110-01/README.md) và [GKT](../runs/gkt-selected-engineering-20261110-01/README.md) ghi rõ giới hạnengineering.

## Đếm theo ma trận development hiện hành

Một **phase training** ở đây là selected-fit hoặc refit, không phải một epoch. Một selected-fit có nhiều epoch và sốepoch cuối phụ thuộc quy tắc dừng đã chốt.

Sau khi A3 expert Junyi hoàn tất refit, nếu giữ nguyên toàn bộ bảng model×environment ở ProtocolV1 thì còn các mục sau.

| Phần | Cấu hình | Phase training chưa có bằng chứng hoàn tất |
|---|---:|---:|
| Junyi learned graph | A1/A2/A3, mỗi bản selected-fit vàrefit |6|
| Junyi baseline hiện đại | SAKT/GKT, mỗi bản selected-fit vàrefit |4|
| Grade10 AKT |7cấu hình đã chọn epoch, cònrefit |7|
| Grade10 baseline hiện đại | SAKT/GKT, mỗi bản selected-fit vàrefit |4|
| Tổng neural ngoài A3 đang dở | |**21phase**|

Con số21 là nghĩa vụ còn lại của **ma trận nhóm đã chọn**, không phải sốlượt bắt buộc được ghi nguyên trong đề cương. Chưa gồm matched GAM/Graph-GAM CPU, fit graph/confidence nếu cần, hoặc calibration scalar. Chưa tính bất kỳ5fold bổ sung nào. Grade10 bảyrefit dùng lại các epoch đã chọn sẽ là30epoch trên corpus nhỏ, có điều kiện đóng plan và nghiệm thu input trước thực thi. Không lấy30epochGrade10 nhân thời gian mộtepochJunyi. Chưa có cơ sở gán9epoch choSAKT/GKT hoặc learnedJunyi.

## Ưu tiên để hoàn thành nghiên cứu cốt lõi

1. Hoàn tất và nghiệm thu A3 expert Junyi, giữ trọn bốnmodel hiện có.
2. Hiệu chỉnh và đánh giá độc lập bốnmodel trên cùng target, bootstrap theo learner. Bước đánh giá outerfold không cập nhật trọng số.
3. Hoàn thiện model Grade10 và đối chứng SAKT/GKT để đánh giá vòng kín. Graphlearned đã có7selectedGrade10, cần tận dụng trước khi thêm trainingJunyi.
4. Đóng chuỗi dự báo→quyết định→lựa chọn→outcome choRQ1/RQ3 và đối chứng ba bẫy củaRQ2, báo giới hạn history/profile/noise.
5. Tổng hợp thống kê/figure, demo và luận văn.

Đề xuất tiết kiệm là cân nhắc hoãn6phase learnedJunyi, vì đã có hướng learnedgraphGrade10 và cần ưu tiên vòng kín theo góp ý GVHD. Đề xuất này chưa áp dụng và chưa xóa task. Cần ghi rõ phân bổ minh chứng theo môi trường và giới hạn kết luận khi thay ma trận hiện hành. SAKT/GKT vẫn giữ. Không thêm dataset thứba, fullnestedCV, sweep lớn, nhiều trainingseed hoặc modelngoàiđềcương để hoàn tất criticalpath.

## Đánh giá tiến độ và thời gian

Hoàn tất refitJunyiExpert là một mốc engineering. Chưa RQ nào được nghiệm thu hoàn tất chỉ từ mốc đó. Hiện chưa có thước đo đủ để báo một phần trăm toàn KLTN đã kiểm chứng; sốphầntrăm quản lý nếu dùng phải ghi là ước lượng và nêu checklist còn thiếu. Bằng chứng chắc chắn là4/4selected-fitJunyi và3/4refitJunyi đã nghiệm thu,7selectedcheckpointGrade10, còn calibration/đánh giá độc lập/vòng kín và baseline nghiên cứu.

Trong một tối có thể nhắm hoàn tất A3 và đóng gói model nếu Drive/runtime ổn định. Không có cơ sở cam kết hoàn tất toànKLTN trong một tối. Thời gian các nhóm training còn lại cần benchmark đúngmodel/dataset; không ngoại suy tốc độAKTJunyi sangSAKT/GKT hoặc suy toànchi phí từ hai epochA3.

## Sửa các nhận định trước

- “Chỉ còn hai epoch là xong training toàn KLTN” thiếu các model/bước nghiên cứu bên trên. Phạm vi đúng là phần còn lại của A3 expert Junyi ở thời điểm quan sát.
- “Phải chạy thêm bốnfold để đúng đề cương” không được PDF quy định. Đủ5fold là lựa chọn thiết kế đánh giá khác, cần dự toán và đóng protocol riêng.
- Bảntraceability cũ nói giữ5outerfold không được dùng thay ProtocolV1 đã adopt sau đó. Giữ snapshot lịch sử và bổ sung chỉ dẫn hiện hành.

Không thay split, hyperparameter, model hay quyền truy cậpHoldout qua audit này. Thư viện đọcPDF cài riêng trong .venv, không cài vàoPython global.
