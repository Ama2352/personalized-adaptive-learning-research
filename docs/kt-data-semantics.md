# Ngữ nghĩa dữ liệu Junyi và hợp đồng dùng chung cho KT

## Nguồn và định danh

Đối chiếu metadata dùng `dataset/junyi_Exercise_table.csv` (837 dòng, 835 giá trị `name` duy nhất). Hai `name` bị lặp, mỗi một lần; các bản ghi lặp giống nhau ở `prerequisites`, `topic`, `area` và `live`. Có 776 exercise có `live=true` và 59 có `live=false` trong tập ID duy nhất. `name` là exercise/item ID. `topic` và `area` là thuộc tính phân loại, không phải bảng ánh xạ concept độc lập.

Tập Development đã lưu trong GAM-KT CV chứa 720 exercise ID duy nhất; cả 720 đều khớp trực tiếp với `name` trong metadata. Đây là đối chiếu ID giữa Development và catalog, không phải khẳng định có ID concept hoặc mapping một exercise sang concept. Không có bảng concept mapping rõ ràng trong các nguồn được kiểm tra. Các mô hình cần concept IDs phải nhận mapping đã được cung cấp và kiểm toán rõ ràng; không suy diễn từ tên, topic hoặc area.

## Graph prerequisite

`prerequisites` được đọc như danh sách các exercise cha, phân cách bằng dấu phẩy, chấm phẩy hoặc `|`. Mỗi quan hệ hợp lệ được đặt hướng `prerequisite → dependent` (từ giá trị trong `prerequisites` đến `name` của dòng). Tập graph tái dựng trong bộ nhớ gồm 835 node ID, 979 cạnh duy nhất sau khi bỏ self-edge; 2 self-edge bị loại, không có endpoint nào ngoài catalog. Có 776 node incident với ít nhất một cạnh và 59 node cô lập. Bảy tham chiếu cạnh bị lặp trong dữ liệu thô được gộp theo cặp đầu mút.

720 exercise ID có trong Development hiện diện nguyên dạng trong graph/catalog node set. Hướng cạnh mô tả quan hệ theo cột `prerequisites`; chưa có kiểm chứng độc lập rằng mọi quan hệ đó phản ánh quan hệ sư phạm nhân quả. Vì vậy graph là metadata cấu trúc để nghiên cứu, không phải bằng chứng về thứ tự học tối ưu hay causal prerequisite. Node cô lập vẫn được giữ lại, không tự xóa.

## Shared KT contracts

`src/knowledge_tracing/shared_kt.py` định nghĩa các thành phần dùng chung cho tích hợp sau này:

- `StableVocabulary` tạo ID ổn định theo thứ tự từ vựng và mã hóa/giải mã; ID ngoài vocabulary bị từ chối. Với validation/test, caller phải tạo item/concept vocabulary trên train của fold rồi truyền lại; exercise chưa thấy cần có chính sách OOV tường minh.
- `audit_exercise_concept_mapping` báo exercise chưa map, exercise map tới nhiều concept và graph node chưa có mapping. Hàm chỉ báo cáo; không tự chọn mapping.
- `PrerequisiteGraph` giữ node/cạnh có hướng, từ chối endpoint thiếu và self-edge. Cạnh được hiểu prerequisite → dependent.
- `validate_fold_isolation` từ chối learner xuất hiện ở nhiều fold.
- `build_causal_sequence_inputs` sắp event theo `(user_id, time_done, source_row)`, giữ item hiện tại và response đã shift từ event trước cùng learner. Response hiện tại được trả riêng làm target, không nằm trong input model. Concept ID là tùy chọn và chỉ nhận mapping đơn trị tường minh.
- `causal_attention_mask(n)` cho phép vị trí hiện tại nhìn về quá khứ và chính nó, không nhìn tương lai.
- `check_prediction_alignment` kiểm tra uniqueness của `source_row`, row thiếu/thừa và identity (`user_id`, exercise, `correct`, `suggested`). `coverage_summary` tách tổng dự đoán khỏi fitted predictions.
- `SequenceKTModel.fit(inputs, targets)` và `.predict(inputs)` là API batch; predict không nhận target hoặc yêu cầu cập nhật state kiểu online. BKT/GAM-KT hiện hữu không bị thay API.

Các hợp đồng này chuẩn bị giao diện dữ liệu cho AKT, SAKT, GKT, Graph-GAM-KT, fixed-graph AKT và CG-AKT; chưa có model nào trong số đó được triển khai hoặc huấn luyện ở Sprint này. Causal mask chỉ mô tả giới hạn attention. Code huấn luyện tương lai vẫn phải đảm bảo nhãn validation/test không lọt vào input hoặc vocabulary/model fitting của fold đó.

## Giới hạn nguồn

Số liệu Development lấy từ predictions CV đã lưu. Metadata catalog được đọc tại chỗ và graph chỉ được dựng trong bộ nhớ; không ghi lại CSV hay artifact graph. Báo cáo này không dùng Holdout/Test để xác nhận mapping hoặc chọn cấu hình. Mọi thay đổi tương lai đối với catalog, split hoặc graph cần có lineage và hash riêng trước khi dùng vào thí nghiệm.
