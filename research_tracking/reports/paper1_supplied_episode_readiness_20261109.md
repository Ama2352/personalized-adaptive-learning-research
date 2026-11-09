# Mức sẵn sàng của episode Paper1 với draws cấp sẵn

Ngày09/11/2026. Đây là kiểm kỹ thuật của phiên bản triển khai prospective theo PDF Paper1. Chưa có nghiên cứu mô phỏng mới, lấy mẫu Gaussian hoặc chạy ma trận so sánh.

## Thành phần đã nối

`initialize_profile` nhận z hữu hạn do caller cấp, persona US/UW/FW và chapter hàm số tường minh. Hàm áp dụng đúng mean/sigma và estimate khởi tạo của PDF, trả các cặp initial state bất biến. Nó không tự rút mẫu hoặc chứng minh rằng z dựng tay tuân phân phối Normal.

`run_continuity_episode_supplied` nối profile với controller và world đã có. Bank, chapter map, edges và traversal order được khai báo tường minh. Mỗi node có tape đúng horizon, từ1 đến500uniform trong[0,1). Tất cả tape được kiểm trước khi tạo state. Chỉ số draw là số phản hồi đã commit trước đó của concept, không phải global step.

Controller dự báo từ estimate trước đáp án hiện tại. World dùng latent riêng để sinh Y từ uniform được cấp, rồi tăng đúng selected latent12 với cap sau feedback1500. Controller chỉ nhận Y để cập nhật selected estimate. Kết quả có trace observable và oracle riêng, đều là tuple của frozen records. Đạt estimated mastery ở bước cuối được ưu tiên ghi thành completed, đồng thời cap flag vẫn cho biết đã dùng hết horizon.

Không sửa primitives hoặc domain loader. API có thể dùng bank nhỏ dựng tay hoặc bank28node từ loader hiện có. Trong lượt kiểm này, các episode chỉ dùng fixture dựng tay, không nạp CSV domain thật để chạy trajectory.

## Kết quả đã quan sát

Root chạy đúng một lượt `unittest discover` trên `tests/paper1_pdf/test_*.py`. Receipt ghi **72tests đạt, gồm18trường hợp episode mới**, returncode0, không timeout. Wrapper đo2,675402899971232giây dưới cap30giây. Log unittest ghi1,742giây cho phần test bên trong, đây là hai scope thời gian khác nhau. Hash của tám source/test trước và sau bằng nhau. [Raw receipt](../runs/paper1-supplied-episode-engineering-20261109-01/result.json), [stdout](../runs/paper1-supplied-episode-engineering-20261109-01/stdout.log), [stderr đầy đủ](../runs/paper1-supplied-episode-engineering-20261109-01/stderr.log).

72 là số phương thức kiểm thử trong bộ regression hiện hành, không phải72episode nghiên cứu hoặc mẫu độc lập mới. Bộ cũ có26primitive,24domain và4re-entry mechanism cases;18episode cases là phần bổ sung.

| Nhóm kiểm mới | Kết quả được xác nhận trên fixture |
|---|---|
| Profile US/UW/FW | Mean, scale50 và estimate khởi tạo đúng unit đã khai báo; z sai/mất/thừa/nonfinite bị từ chối |
| Tail/cap | Không clip initial latent, giữ literal post-feedback cap, kể cả initial1550 xuống1500 |
| Binding và input | Sai bank/chapter/derived profile, tape sai key/length/value và graph/order không hợp lệ bị chặn |
| Thứ tự thông tin | Đổi current Y không đổi prediction của chính nó; đổi uniform tương lai không đổi prefix hay pre-update readout |
| State isolation | Đáp án sai vẫn tăng selected latent12, concept khác không đổi; oracle không được truyền vào constructor controller |
| Tape và tính bất biến | Index theo concept-local count, kết quả deterministic với cùng draws; caller inputs và global RNG state giữ nguyên |
| Điểm dừng | Hoàn tất trước cap, hoàn tất đúng bước cuối và còn việc khi hết horizon được phân biệt |
| Upper boundary | Một fixture một concept với500uniform dựng sẵn commit đúng500feedback, không mở rộng horizon |

Những checks này xác nhận đường nối và quy tắc trên input hữu hạn đã khai báo. Chúng không xác nhận phân phối persona, tần suất re-entry hoặc cải thiện mastery trong nghiên cứu.

## Phạm vi còn thiếu

Batch này chỉ thực hiện continuity episode với draws cấp sẵn. RNG-owned runner, pairing giữa branch, B0, global/unlock policy dispatch và ma trận50seeds chưa được triển khai. Các đề xuất trong Spec02 vẫn là lựa chọn prospective chờ chấp nhận, không được tự suy thành phương pháp đã adopt từ việc18tests đạt.

PDF bản nộp vẫn là nguồn có thẩm quyền theo D37. Bằng chứng hiện tại không xác nhận historical input bytes/traversal order hoặc tái lập số TableI/Fig.3. Zero re-entry của B1 có chứng minh riêng dưới các giả thiết đã nêu trong báo cáo cơ chế; episode engineering này không thêm một kết quả nghiên cứu về graph hoặc lợi ích giáo dục.

## Identity và nguồn

- `src/knowledge_tracing/paper1_pdf/episode.py` SHA256 `e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471`.
- `tests/paper1_pdf/test_episode.py` SHA256 `d0bf6e052d9e2618b0b2d3ecf729164da68d99fc49a42e4c6dc0eadf6b4db1c0`.
- Actual receipt SHA256 `013690ce194175525525f06bc4afd8a0b94085c4b47b61d5937c169886b7beff`; wrapper SHA `2ad916cba7c9765872be31cddaa928928d906ac884bcf3d7fa1da99e0700d800`.
- Spec02 SHA256 `2c83655f63d973e3d009a5d091bfd2405513b89e00f782b1f68ab2b03268b176`, giữ nguyên các quy ước còn đang đề nghị.
- PDF Paper1 SHA256 `984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4`, tr.2–3 Eq.(3)–(9), Algorithm1 và IV.A. Bản PDF và sáu file cũ được tham chiếu bằng SHA, không nhân đôi trong bundle mới.

Bundle đích `paper1-supplied-episode-engineering-20261109-01` lưu source/test mới, wrapper, ba raw outputs, spec, báo cáo và copy inventory. Manifest hoàn tất mới là bằng chứng closure. Bản báo cáo chuẩn bị này chưa tự chứng nhận archive đã được đóng. Các liên kết raw ở trên dùng vị trí canonical dự kiến `research_tracking/reports/paper1_supplied_episode_readiness_20261109.md`.
