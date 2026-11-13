# Đối chiếu kiến trúc A1 với nghiên cứu và source tham khảo

Ngày 13/11/2026. Trạng thái LITERATURE_AND_SOURCE_REVIEW / DESIGN_DECISION_PENDING. Review dùng paper, trang nhà xuất bản và source công khai. Chưa thay kiến trúc hoặc chạy thêm GPU.

## Điểm xuất phát

A1 hiện dùng backbone AKT NonRasch và cộng tín hiệu làm đúng của các khái niệm cha vào logit qua alpha. Đây là recipe tối giản do nhóm chọn trong tài liệu26, chưa phải bản tái hiện RKT, GKT hoặc GIKT. Đề cương yêu cầu AKT kết hợp đồ thị cố định, confidence và gate cho CG-AKT; cách tích hợp cụ thể cần được lập luận và kiểm chứng.

Epoch1 A1 đã train13.347.331target, checkpoint trước validation được giữ. Mẫu đo GPU trung bình4,98% cùng CPU gần một lõi chỉ ra giới hạn hệ thống. Profile128window Junyi định vị chi phí prefix/context và chuyển dataclass sang payload hash lặp. Bộ kiểm số học đã có giúp đánh giá phạm vi đúng của implementation, chưa xác lập sức biểu diễn hoặc hiệu quả nghiên cứu của thiết kế residual.

Nguồn nội bộ gồm [recipe26](../../docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md), [đề cương](../../docs/thesis_recovery/evidence/user_documents_20261108_proposal.txt), [profile CPU](../runs/junyi-a1-selected-20261113-01/actual-graph-cpu-profile.md) và [hồ sơ training](../runs/junyi-a1-selected-20261113-01/README.md).

## Các nguồn đã kiểm

| Nguồn | Điều đã xác nhận | Ý nghĩa đối với KLTN |
|---|---|---|
| AKT, KDD2020 | Monotonic/context-aware attention trên lịch sử tương tác; upstream có Rasch và NonRasch | Backbone và causal masking hiện tại có nguồn gốc rõ ràng |
| RKT, CIKM2020 | Kết hợp quan hệ bài tập và thông tin thời gian vào attention | Nguồn đối chiếu cho cách đưa quan hệ vào attention |
| GKT, WI2019 | Biểu diễn trạng thái khái niệm trên graph, aggregate/update bằng mạng học | Tham khảo graph tensor và baseline GKT trong đề cương |
| GIKT, ECML-PKDD2020 | GCN lan truyền embedding trên quan hệ question–skill | Tham khảo tổ chức graph và embedding propagation |
| KSGKT, IJIS2022 | Knowledge structure có quan hệ tiên quyết, graph representation và attention | Nguồn trực tiếp hơn về semantics tiên quyết |
| pyKT, NeurIPS2022 Datasets and Benchmarks | Chuẩn hóa preprocessing/evaluation, phân tích nguy cơ rò rỉ nhãn | Đối chiếu protocol và tính nhất quán benchmark |

Nguồn sơ cấp cho các dòng trên lần lượt là [AKT paper](https://arxiv.org/abs/2007.12324), [RKT paper](https://arxiv.org/abs/2008.12736), [GKT source được pyKT dẫn](https://github.com/jhljx/GKT), [GIKT paper](https://arxiv.org/abs/2009.05991), [KSGKT tại Wiley](https://doi.org/10.1002/int.22763) và [pyKT proceedings](https://proceedings.nips.cc/paper_files/paper/2022/hash/75ca2b23d9794f02a92449af65a57556-Abstract-Datasets_and_Benchmarks.html).

## Quan sát cụ thể từ code

### RKT

Source pyKT biểu diễn relation và attention thành tensor, phối hợp bằng các hệ số học được. Phần tra relation vẫn chuyển question IDs về CPU; helper dictionary có vòng lặp lồng, helper matrix có vòng lặp qua batch. Việc lựa chọn source cần kiểm cả đường chuẩn bị dữ liệu. [Source RKT](https://raw.githubusercontent.com/pykt-team/pykt-toolkit/main/pykt/models/rkt.py).

Quan hệ bài tập của RKT dùng thông tin nội dung và dữ liệu thực hiện, cùng thành phần thời gian. Áp dụng cho cạnh tiên quyết có hướng của KLTN là một adaptation cần đặc tả. [Bài RKT](https://doi.org/10.1145/3340531.3411994).

### GKT

Code aggregate khai báo tensor theo batch và khái niệm, tra adjacency thuận/ngược để kết hợp thông tin láng giềng. Forward vẫn lặp qua thời gian; nhánh VAE có xử lý NumPy/SciPy. Hiệu năng tùy nhánh và kích thước graph. [Source GKT](https://raw.githubusercontent.com/jhljx/GKT/master/models.py).

### GIKT và KSGKT

GIKT dùng quan hệ question–skill, cần ánh xạ semantics khi tham khảo cho graph tiên quyết. README nhóm tác giả ghi TensorFlow1.12/Python3.6.5. Review này đã đọc abstract và README, chưa audit toàn bộ core implementation GIKT. [Bài GIKT](https://arxiv.org/abs/2009.05991), [repo GIKT](https://github.com/ApexEDM/GIKT).

KSGKT kết hợp knowledge structure, graph embeddings, difficulty và attention. Các thành phần này làm phạm vi phương pháp rộng hơn recipe A1 hiện tại. Review đã kiểm abstract nhà xuất bản; toàn văn và code tác giả còn cần kiểm. [KSGKT](https://doi.org/10.1002/int.22763).

## Hai hướng cần đánh giá trước khi sửa tiếp

### Hướng E — giữ công thức A1, tổ chức lại đường tính toán

Giữ nguyên residual, raw message và alpha. Tham khảo cách biểu diễn graph theo tensor, adjacency lookup và batch từ source trên. Chuẩn bị phần dữ liệu cố định ngoài vòng GPU, dùng cache có provenance gắn dataset/roles/encoding/window/graph. Phần phụ thuộc tham số học như alpha, gate và embedding học được vẫn tính trong training.

Điều kiện để chọn hướng này gồm cơ sở lập luận cho residual tối giản và phép đối chiếu causal window, raw message, logit, loss, gradient, optimizer, RNG và resume. Cần xác định cách nghiệm thu integrity ở ranh giới artifact và batch để giảm chuyển đổi Python lặp mà giữ phát hiện sai dữ liệu. Đây là tối ưu biểu diễn/thực thi nếu công thức được bảo toàn.

### Hướng R — quan hệ tiên quyết tham gia attention trên AKT

Đánh giá một candidate lấy cảm hứng từ RKT, dùng bảng quan hệ có hướng và confidence để dựng tensor quan hệ giữa target hiện tại với tương tác quá khứ. A1 dùng confidence1, A2 dùng confidence theo cạnh và A3 thêm gate theo thiết kế được chốt. Causal mask cần bảo đảm vị trí s<t, đúng chiều cạnh và cùng effective window.

Cần chỉ rõ vị trí tác động vào monotonic attention AKT, cách chuẩn hóa, cạnh thiếu hỗ trợ, gate0 và graph-off. Các phép toán tensor phải được đối chiếu với bản tham chiếu nhỏ. Đây là thay đổi kiến trúc của phương pháp. Checkpoint residual hiện tại được giữ dưới recipe lịch sử, tính tương thích trọng số phải đánh giá riêng. Số liệu training, refit và ngân sách cần lập lại trước khi quyết định áp dụng.

Ở cả hai hướng, phép chia learner và biên train/selection/calibration của KLTN được dùng làm điều kiện kiểm. Junyi và Grade10 cần vocabulary và checkpoint riêng. Việc đưa relation vào attention vẫn cần chương trình kiểm confounding thứ tự log Junyi của RQ2.

## Quyết định sau review

Đã có cơ sở để ưu tiên đọc sâu RKT/AKT về cơ chế relation-aware attention, GKT về graph tensors và pyKT về benchmark. Hướng E và R đều còn là phương án, chưa có lựa chọn kiến trúc mới được áp dụng. Bước cần hoàn tất trước sửa tiếp là bảng ánh xạ phương trình/semantics từ nguồn tham khảo sang A0–A3 và ước lượng phạm vi thay đổi, sau đó chọn thiết kế phù hợp ba RQ và hạn mức compute.

GKT giữ vai trò baseline theo đề cương. RKT/GIKT/KSGKT giữ vai trò nguồn thiết kế trong review này. Đồ thị học từ log hoặc confidence thống kê phải gắn train-only lineage. Quan hệ từ nội dung, correlation, question–skill và cạnh tiên quyết cần được ghi đúng loại khi so sánh.

Nghiệm thu GPU cần đo utilization trung bình trong training theo mục tiêu50% người dùng đặt, kèm target/giây, chi phí/target, VRAM, CPU và thời gian data preparation. Chưa nguồn paper hoặc phép kiểm hiện có nào chứng minh A1 sửa mới sẽ đạt50%. Checkpoint và dữ liệu đúng là điều kiện song hành với hiệu năng.

## Giới hạn của review

Đây là đối chiếu ban đầu ở mức abstract, đặc tả hiện hành và các core source đã nêu. Chưa tái hiện các paper, chưa benchmark repo ngoài, chưa pin snapshot source ngoài cho implementation và chưa xác minh license của mọi file có thể tái sử dụng. API GitHub tree không đọc được trong lượt tra cứu; các raw source đã đọc được dẫn trực tiếp. H100 giữ trạng thái đã dừng trong suốt review. Đề xuất tiếp theo là hoàn thiện quyết định thiết kế có nguồn trước khi sửa code và cấp GPU.
