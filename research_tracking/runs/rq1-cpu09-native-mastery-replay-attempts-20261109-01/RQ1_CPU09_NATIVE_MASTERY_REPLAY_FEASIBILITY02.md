# Khả thi replay estimator để đối chiếu native mastery trên CPU09

Ngày 09/11/2026. Kiểm nguồn, chưa replay, chưa đọc lại các dòng gzip, chưa tạo số liệu mới. Ghi chú này nằm ngoài inventory của báo cáo response reliability vừa chuẩn bị.

## Kết luận nguồn

Có một nhánh khả thi để bổ sung truth cho **concept đang được hỏi trong CPU09**. Trace đã lưu `theta_before`, là trạng thái thật của concept tại thời điểm trước trả lời và trước học từ câu đó. Native M chưa được lưu trong cùng dòng nhưng có thể được dựng lại bằng estimator nhận đúng lịch sử q/y/time đã ghi. Cần chứng minh parity trước khi dùng bản dựng lại để tính đúng/sai.

Nguồn notebook Paper2 có SHA `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f`. Trong cell9, dòng45 lấy `theta_at(cid,timestamp)`, dòng48–49 dùng nó tạo xác suất/đáp án và dòng73–78 trả `theta_before`. Cell3 dòng33 đặt `MASTERY_ELO=1250.0`. Cell19 dòng26/61 chấm true mastery từ `theta >= MASTERY_ELO`. Vì vậy, nhãn hậu nghiệm có thể dùng là `theta_before>=1250` trên query hiện tại, với ngữ nghĩa đúng simulator nguồn. Đây là nhãn do mô hình thế giới quy định, chưa là nhãn thực nghiệm về học sinh.

## Vì sao không cần dựng lại thế giới tiềm ẩn?

Cell13 dòng24–46 khởi tạo estimator bằng `MODEL_INITIAL_ELO`, memory zeros, các pi và counters cố định. Nó không nhận `base_theta` của người học. `predict` và `update` ở dòng117–149 nhận concept/question/difficulty/time và y/P đã dự báo, dùng state của estimator. Adapter `build_pathway_policy` chỉ thay `_context` theo switches S/P/L, không truyền λ hay latent theta cho estimator. CPU09 khởi tạo policy mới cho mỗi world. Do đó nhánh đề xuất chỉ dựng estimator, không gọi constructor hoặc `interact` của world, không sinh uniforms và không tạo lại latent vectors.

Giữ đủ 120 streams, mỗi stream120events, với khóa `(seed,profile,graph_on,mechanism_on,step)`. Mười seed và toàn bộ q/y có sẵn được dùng lại, không tạo independent N mới. Gzip gốc có SHA `2a136fbf627cfa59170deec54c10ae562c2f8214eb00970ce41b96c43d065dcc`. Population khác giữa arms sau closed-loop divergence vẫn được giữ riêng.

## Replay nhỏ nhất cần được duyệt trước thực hiện

1. Tái dùng admission/hash/grid/query validation của parser `8590381c…6f1311`, cùng bank/nodes/graph và notebook đã đóng nguồn. Kiểm current loader và dependency hashes tương ứng. Chưa dùng lại một approval vận hành cũ như quyền chạy mới.
2. Mỗi stream tạo đúng `build_pathway_policy(reference, signal=g, parent_adaptation=g, local_adaptation=False)`. Environment/controller graph đúng nguồn CPU09. Không dùng full/empty package của study fixed-stream để thay switches.
3. Dựng timestamp theo runner nguồn từ UTC 2026-01-01. Mỗi bước tăng6giờ, riêng bước dương chia hết cho28 tăng72giờ. Bank giải difficulty của qid. `gap_days` là khoảng cách của concept, không thay trực tiếp cho global timestamp.
4. Gọi original `select()` một lần theo thứ tự cũ và bắt buộc cid/qid/difficulty khớp logged query. Nó cập nhật selection/question counters, recent concepts và chapter ở cell11 dòng75–81. Nếu chỉ replay update bằng logged queries thì phần estimator có thể vẫn đúng, nhưng chưa chứng minh selector replay đầy đủ. Mismatch phải dừng và giữ log.
5. Trước update, tính P theo native `predict` và yêu cầu parity với **mọi** stored `prediction`, không chỉ mean/loss. Cần chốt tiêu chuẩn exactness/runtime trước chạy, không nới tolerance sau khi thấy mismatch. Lưu state/query/time identity và bằng chứng không có world/teacher calls.
6. Đọc `theta_est`, **stored** `pi_task` và native `is_mastered(cid)` trước update. Native M tại cell13 dòng50–52 dùng stored pi, còn P dùng pi đã decay theo timestamp ở dòng92–100/117–127. Có thể ghi thêm decayed pi với tên riêng, không thay pi trong M âm thầm. Nhãn truth của query là stored `theta_before>=1250`. Sau khi dự báo/đọc trạng thái mới gọi native update với logged y và đúng P.
7. Có thể probe ba reference items của queried concept trên bản sao/frozen pre-update state, kiểm state hash trước/sau giống nhau. Các readout raw này dùng để đối chiếu tiêu chí nguồn. Chúng chưa là predictor/calibrator nghiên cứu V1 đã fit đúng roles. Nhánh này không cần oracle outcomes giả cho từng item và không tự cấp nhãn reference-item response từ một y.

## Câu hỏi mô tả có thể trả lời sau parity

Có thể lập bảng M native so với source-defined true mastery của queried concept, giữ toàn bộ seeds/personas/arms, support hai lớp và các cell bằng0. Có thể tách theta-gate và pi-gate để biết một bất đồng thuộc phía nào. Đây là khả năng mở rộng thực sự so với ECE response vừa có, nhưng chưa có số đếm hoặc kết quả thực hiện trong ghi chú này.

Không có true theta cho toàn bộ28concept tại mỗi thời điểm trong trace CPU09, nên quần thể truth trực tiếp vẫn là concept đang được hỏi. Không ghép nó với fixed9streams khác seeds/query/history. Các probes chỉ thêm readouts, không thêm quan sát độc lập. Các nhãn threshold của simulator không xác nhận chuẩn tri thức con người, calibration xác suất của pi hoặc tác động học tập nhân quả của graph. V1 reference criterion và native M cần giữ tên/target riêng.

## Nguồn được kiểm bằng đọc file

| File | SHA-256 | Anchor |
|---|---|---|
| Notebook Paper2 nguồn | `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f` | cells3/9/11/13/19, dòng nội bộ như trên |
| `scripts/research/run_approved_cpu_pilots.py` | `55e8e3c74c8daa92d572c809353da5546fa435b55e18b8ab30fdcf46e8413e8e` | factorial dòng34–95, chronology/select/predict/update dòng62–84 |
| `src/knowledge_tracing/gam_kt/simulator_pathways.py` | `33ad34140f7b08eb22f86e6cc3caf7b0e7c98f09e4fd74945a6f7e9718b07560` | factory và `_context` |
| `src/knowledge_tracing/paper2_reference.py` | `a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1` | chọn definitions/constants, estimator/controller namespaces |
| `src/knowledge_tracing/gam_kt/simulator_mechanisms.py` | `0cbfaf1b4735c188e04ed822197121118dcb65849b582af7413e157fd8d847fa` | λ chỉ thay phương trình world interact |

Đây là đề xuất nguồn để Root review, chưa phải parser/controller được duyệt, chưa có runtime/cost measurement cho replay mới. Không sửa production, protocol, artifacts hoặc báo cáo đã đóng.
