# Junyi A1 — condition đồ thị và evidence quá khứ

## Phần đã hoàn thành

Gói ngày12/11/2026 bổ sung `src/knowledge_tracing/akt/research_junyi_graph.py` và `tests/akt/test_junyi_graph.py`.

- Condition A1 ghim đúng encoding TRAIN80, role/cohort, graph đầy đủ và SHA nguồn topology. Giữ cả node chưa fitted, node cô lập và cạnh có parent chưa fitted. Confidence của A1 bằng1 cho từng cạnh.
- Evidence lấy từ `WindowInputs` do windowing hiện có cung cấp. Tại vị trí `j`, chỉ các item ở `[:j]` và responses dịch phải ở `prior_responses[1:j+1]` góp vào thống kê parent. Các vị trí context giữ `None`; chỉ target có evidence cho `ResearchGraphNative.bind`.
- Kiểm graph chuẩn, DAG, cạnh trùng/self-edge/endpoint, membership vocabulary, chronology, role, encoding integrity và geometry. Context ngoài native window không được cấp vào API.
- A2/A3 bị từ chối rõ ràng vì Junyi chưa có confidence artifact fitted. Module không tạo hoặc suy đoán confidence từ nhãn cạnh đúng/sai.

## Bằng chứng kiểm

`tests01.log/xml` ghi26tests mới đạt. Các ca bao gồm thay correctness hiện tại/tương lai và item tương lai nhưng evidence quá khứ giữ nguyên, thay response quá khứ gây thay đổi đúng chỗ, OOV barrier, context100, graph malformed và encoding sai phase.

`tests02.log/xml` ghi55tests cùng11subtests đạt khi chạy chung với phase data/roles/cache. `import-check.json` xác nhận fresh process import module không nạp Torch.

## Tối ưu kiểm ranh giới phase

`JunyiGraphPhaseSession` kiểm full condition/roles/encoding ở lúc attach và `assert_boundary()`. Caller tạo một session cho mỗi phase, gọi `session.prefix_evidence(window)` cho các window và kiểm boundary khi kết thúc. Mỗi window kiểm header của các tuple frozen được giữ tham chiếu và hash phần vocabulary/support có thể thay đổi. Membership learner dùng frozenset. Danh sách gần198nghìn learner IDs không được hash lại theo số window.

`tests03.log/xml` xác nhận59tests cùng11subtests đạt, gồm bốn ca bổ sung. Ca đếm số lần truy cập full role identity xác nhận20window calls không làm tăng số lần hash, trong khi attach và boundary vẫn thực hiện kiểm đầy đủ. Các ca khác từ chối role tuple bị thay ở boundary, support bị đổi và graph bị thay. API `junyi_prefix_evidence` đơn giản vẫn giữ để dùng cho bounded call và đối chiếu, production dùng session tái sử dụng.

## Giới hạn

Chưa nối Junyi adapter vào native model hoặc thực thi training graph. Chưa confidence estimator, learned graph, refit90 hoặc calibration. Gói này chứng minh xử lý metadata và prefix trên các ca kiểm xác định. Tính đúng nguồn raw history vẫn dựa trên reader/cache/windowing đã ghim và kiểm ở gói trước. SHA là ràng buộc nhất quán, không chứng nhận chống caller cố ý tạo metadata giả.

Nhánh chính đã rà soát và đóng bundle sau nghiệm thu. Không có GPU/cloud run hoặc thay đổi dataset, checkpoint và artifact lịch sử trong gói này.


## Nghiệm thu bổ sung của nhánh chính

`tests04.log/xml` đạt74tests/11subtests cho toàn gói Junyi mới. `actual-cohort-prefix.json/log` kiểm50window thực, giữ1.405supported/125OOV;377target có ít nhất một parent đã quan sát. Topology giữ835nodes/976edges. Đây là kiểm context, chưa native forward hoặc training graph.
