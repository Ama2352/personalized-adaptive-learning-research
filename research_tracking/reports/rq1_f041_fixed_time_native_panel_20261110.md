# RQ1 · Native panel đủ28 khái niệm trên một lịch sử F041

Ngày10/11/2026. Đây là phép đo có giới hạn trên lịch sử mô phỏng đã lưu, không tạo response hoặc world mới. Phạm vi khác witness PG120 trước đây. [Plan nguồn](../runs/rq1-f041-native-panel-20261110-01/RQ1_F041_NATIVE_PANEL_PLAN01.md).

## Câu hỏi và phép đo

Witness trước chỉ quan sát khái niệm policy đang hỏi. Phép đo này kiểm đủ28 khái niệm tại mỗi thời điểm của một lịch sử để tránh bỏ các khái niệm không được chọn khỏi mẫu số quan sát. F041 được chọn theo thứ tự plan, là cell đầu tiên ngoài high-controls, block21010, năng lực nền1000, graph full, λ0, S/P bật và L tắt. Một history ở đây không đại diện cho mọi profile hoặc mức khởi tạo.

Recorder ghi θ, π lưu và M từ28 getter native đã có trong first pass của ready_set. Một policy mới replay đúng120 câu hỏi/lựa chọn và P gốc, cập nhật bằng đáp án hiện tại sau predict. Không gọi thêm getter của policy, predict, shadow action hoặc OFF policy. Native endpoint khớp trước khi đóng raw panel. Getter M dùng θ≥1250 và π_task lưu≤0,55. Không đổi sang π suy giảm theo thời gian hoặc mastery score S04.

Phần latent được dựng lại riêng từ actual initial28 dưới encoding float_hex và các chuyển trạng thái đã ghi. Mỗi prestate phải khớp full environment vars SHA gốc, sau đó mới tính θ_at cho28 khái niệm bằng hàm nguồn thuần đọc. Chỉ áp dụng learning gain và timestamp đã lưu để đi tới bước tiếp theo, không sinh Y hoặc tính lại learning dynamics. Full final environment cùng28 giá trị endpoint khớp. Đây là source-equation reconstruction đã kiểm, không backfill thành trace latent toàn miền được ghi trực tiếp trong lịch sử.

## Kết quả đủ mẫu số

Criterion latent cùng dùng ngưỡng θ_at≥1250. Các ô TP/FP/FN/TN chỉ là đối chiếu hai phân loại trong simulator, chưa là ground truth của người học thật.

| Quần thể lặp theo thời điểm | Hàng | TP | FP | FN | TN | Native M true | Latent criterion true |
|---|---:|---:|---:|---:|---:|---:|---:|
| Đủ28 khái niệm ×120 thời điểm | 3360 | 0 | 0 | 0 | 3360 | 0 | 0 |
| Khái niệm thực sự được hỏi | 120 | 0 | 0 | 0 | 120 | 0 | 0 |
| Các khái niệm không được hỏi ở thời điểm đó | 3240 | 0 | 0 | 0 | 3240 | 0 | 0 |

Trong cả3360 cặp, θ gate native đều false. Số cơ hội θ gate true để xem π có chặn M hay không bằng0. Vì vậy, kết quả chưa kiểm được vai trò của cổng bất định. Không báo AUC hoặc dùng toàn bộ TN để khẳng định khả năng classifier. Kết quả cũng chưa chứng minh sự lựa chọn concept gây ra hoặc không gây ra sai lệch. [Summary và phạm vi đơn vị](../runs/rq1-f041-native-panel-20261110-01/native__summary.json).

Kết quả mới xác nhận việc quan sát có thể bao phủ đủ28 concept theo thời điểm trên một history và tái hiện trạng thái nguồn. Riêng F041 chỉ có lớp latent âm trong cửa sổ này. Đây là một điều kiện ban đầu cụ thể, không thay thế kết quả witness PG120 ở quần thể khác, không ghép chúng thành so sánh graph hoặc causal ability effect.

## Kiểm nghiệm thu và review độc lập

Nguồn worker/outer giữ nguyên sau review. Actual operation có một policy builder,120 select/predict/update và3360 theta_at evaluator calls.3360 M observations lấy từ first pass sẵn có. Các getter parent lặp trong selector được ghi số gọi riêng, không cộng thành thêm mẫu. Getter trong update nằm ngoài phạm vi recorder.

Native panel đủ3360 hàng,120 action/P và endpoint của policy khớp.120 fullvars prestate SHA, final environment và28 endpoint latent đều khớp. Job cleanup về0, môi trường được phục hồi và không có guard violation. Outer ghi5,0822833 giây, worker ghi3,8090678 giây trước final, trong allocation whole60 giây. Hai thời gian khác phạm vi, không cộng nhau. Đây là GAM online updates thật, không phải NN optimizer hoặc research fit.

Checker độc lập chỉ dùng stdlib và dữ liệu đã lưu. Nó tính lại3360 phương trình θ_at,120 fullvars prestate SHA, full final environment,28 endpoint và toàn bộ các ô summary, trong0,3837179 giây trước final. Không import hoặc gọi GAM, không gọi getter nguồn, không RNG/world mới trong checker. Native policy parity vẫn dựa vào actual receipt đã nghiệm thu, không được chạy lại trong review. [Kiểm độc lập](../runs/rq1-f041-native-panel-20261110-01/independent_cached_review.json).

## Bằng chứng và giới hạn còn lại

[Bundle](../runs/rq1-f041-native-panel-20261110-01/README.md) giữ nguồn, plan/contract, review, receipt và logs nhỏ. Hai JSONL native/joined giữ tại `experiments/gam_kt/results/rq1-f041-native-panel-20261110-01`, tham chiếu SHA và size qua inventory thay vì nhân đôi. Raw parent và bundles cũ giữ nguyên.

Đơn vị history/block vẫn là1, không phải3360 người học độc lập. Có đủ miền khái niệm giúp làm rõ mẫu số được quan sát, nhưng không tự loại conditioning từ lịch sử policy đã tạo. Cần các điều kiện ban đầu bổ sung đã chốt trước phép đo mới để biết có xuất hiện latent positives hoặc θ-gate opportunities hay không. Các điều kiện đó chưa được chạy hoặc báo kết quả trong hồ sơ này. Không thay calibrated mastery S04, không CI/p-value, causal teaching, graph benefit hoặc hoàn tất RQ.
