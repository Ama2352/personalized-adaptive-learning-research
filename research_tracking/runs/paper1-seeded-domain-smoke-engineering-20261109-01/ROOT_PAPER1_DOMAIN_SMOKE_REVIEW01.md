# Kiểm tích hợp prospective domain28 của Paper1

Lượt goal trước có tiến triển thực, đã đóng bằng chứng masking44, QA19 và bản thảo E7 với15outputs, kiểm117raw Git files và commit dc3287a/1ccaffc. Không coi đây là hoàn thành các RQ.

Root đã đọc worker94b2c034…, controllerd63df355… và allocationa4c0d87f… cùng domain loader, trace schema, sampler và admission. Lượt này chỉ kiểm nối implementation PDF với bộ dữ liệu prospective đã ghim từ Paper2. Nguồn PDF Paper1 vẫn là chuẩn hành vi. Input reuse chưa là dữ liệu hoặc kết quả tái lập lịch sử của PDF.

Giới hạn cố định là một profile US, seed42, replicate paper1-rng-smoke01, horizon500. Chỉ prepare một bộ28normal và14.000uniform events, rồi hai continuity episodes B1/GA dùng cùng bộ draws bất biến. Tối đa1.000feedback và1.002selection calls. Hai closed-loop trajectories có thể khác lịch sử, không trở thành một fixed stream. Không chạy matrix nghiên cứu hoặc suy ưu thế graph từ hai lượt.

Root chọn dùng experiments/simulator/results cho trace của simulator dùng chung, tách khỏi output của từng model KT. Đây là thư mục con của experiments có vai trò riêng. Launcher chỉ tạo parent sau admission, output run phải mới hoàn toàn. Sau lượt thực tế cần ghi README tại experiments/simulator và cập nhật bản đồ repository.

Caps giữ nguyên35giây toàn bộ, owned30, worker26, cleanup3, sampled parent-plus-descendant RSS256MiB và RAM khả dụng ít nhất512MiB. Root quan sát RAM khả dụng2.331.140.096bytes trước review. Số này không thay thế admission hoặc monitor khi chạy. Các nguồn/runtime33pins, prereq85tests, CRC/identity source và source-before/after cần khớp. Worker chỉ dùng standard library, không import model/data framework.

Nghiệm thu phải đọc đủ10outputs, xác nhận28concepts/84items/25và31edges, toàn trace identity, counters, global RNG và methods phục hồi, finite probabilities, monitor sạch và Job0. Không dùng ranking hoặc số lần quay lại chương mong muốn làm tiêu chí đạt. Nếu thất bại, giữ partial evidence và tìm nguyên nhân trước mọi allocation mới. Không chạy lại tự động.
