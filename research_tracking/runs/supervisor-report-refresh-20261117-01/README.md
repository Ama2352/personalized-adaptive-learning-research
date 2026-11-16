# Cập nhật diễn giải báo cáo GVHD ngày 17/11

## Phạm vi

Đã cập nhật hai file đọc trong đợt báo cáo hiện hành `research_tracking/supervisor_reports/2026-11-16/01_tien_do/`. Ngày hiển thị là 17/11, số liệu nghiên cứu đến 16/11. Lượt này đối chiếu nguồn nhỏ và diễn giải lại kết quả có sẵn. Không sinh kết quả training, calibration hoặc đánh giá mô hình mới.

## Nội dung đã làm rõ

- Bắt đầu từ kết luận PDF Paper 1 về đồ thị/chính sách và PDF Paper 2 về dự báo/kết quả vòng kín/cấu hình tắt gói bổ sung trên phần phát triển Junyi.
- Thêm diễn tiến kế thừa paper → chẩn đoán 07–12/11 → xây mô hình 12–16/11 → đánh giá cần khép.
- Ghi điều kiện của re-entry bằng 0 và giới hạn tỷ lệ duy trì 43,17% đối với tăng điểm năng lực trung bình.
- Kiểm lại bảng đồng biến dự báo/quyết định. Trong 964 cặp đổi xác suất có 944 giữ gợi ý, trong 22 cặp đổi gợi ý có 17 giữ ready. Bảng bốn số đo được ghi rõ đếm riêng, không vẽ phễu hoặc nhận dạng trung gian nhân quả.
- Kiểm lại ba đối chứng Junyi trên cùng 239 người học chỉ đổi chỉ số quan sát ở 1, 7 và 1 người, giải thích vì sao phép thay đồ thị cần kiểm độ mạnh đầu vào.
- Phân biệt 12 vòng chọn bản, vòng được chọn 9 và học lại 9 vòng của bốn biến thể Junyi. Mô hình Grade10 được huấn luyện riêng theo danh mục bài riêng.
- Giữ trạng thái hiệu chỉnh/đánh giá độc lập/vòng kín còn thiếu. Sprint 4 làm rõ lựa chọn cấu hình hệ thống so với việc đã chọn vòng học.

## Bằng chứng và kiểm tra

`BEFORE.json` giữ pin hai file trước sửa. `NUMERIC_RECHECK.json` giữ các phép đếm tính lại từ PMRA joint table và common-population aggregate. `MANIFEST.json` giữ SHA nguồn nhỏ và hai output hiện tại. `QA.json` xác nhận tag HTML cân bằng, ID/anchor hợp lệ, token số liệu/ngày thống nhất giữa hai định dạng, đủ mục RQ/diễn tiến/sprint và HTML không chứa mã SHA hoặc script/iframe.

Chưa render bằng trình duyệt, do đó chỉ nghiệm thu static/source đối với trang HTML. Không mở Holdout, nạp checkpoint lớn hoặc chạy lại thí nghiệm. Các kiểm kỹ thuật calibration của nhánh song song cần giữ mức bằng chứng engineering khi root tích hợp.

## Bổ sung sau kiểm độc lập RQ2

Đã nhận `SECONDARY_CHECK.json` và `SOURCE_MECHANISM_CHECK.json` từ nhánh `rq12-existing-evidence-20261117-01`. Ở mức khởi tạo1150, cả20cặp bật/tắt phạt giữ cùng toàn bộ chuỗi query/correct/KT probability trong120bước, trong khi latent gain giảm20/20cặp. Đã thêm một đoạn ngắn ở RQ2 để giới hạn cách đọc K dương. Mức1300 có cả observable lẫn latent gain giữ nguyên, được giữ riêng khi kiểm và không gộp vào claim gain thay đổi. Báo cáo ghi giới hạn10block,120bước,một learned graph cố định và chỉ các trường đã lưu.

Đã đọc thêm source `interact` trong notebook Paper2 bằng AST, cùng hàm can thiệp hiện hành. Núm lambda thay multiplier của learning gain. Không thực thi notebook hoặc simulator.

RQ1 được sửa heading thành đối chiếu khác biệt dự báo/gợi ý, và nói rõ served probability được tính sau selection trong Paper2. Nhờ đó bảng đồng biến giữ đúng phase, tránh suy như phân rã trung gian nhân quả.

Đã chèn SVG bảng2x2 `rq1-ready-preview-v01.svg` của nhánh RQ12. HTML giữ SVG inline tự chứa, Markdown trỏ bản SVG độc lập. CSV/JSON/script dựng lại nằm trong bundle nguồn, không ghi đè figure lịch sử. Đã xem PNG nguồn, chữ và số rõ ràng. HTML thêm fallback font cho SVG. Lượt này chưa kiểm toàn trang bằng browser.

`MANIFEST02.json` và `QA02.json` là nghiệm thu hiện hành sau bổ sung. Root nên commit bundle RQ12 chứa figure trước hoặc cùng report để liên kết SVG trong Markdown có nguồn được theo dõi đầy đủ.

## Tích hợp

Không commit ở nhánh agent để root rà và commit riêng. Không sửa uploader, source model, index báo cáo hoặc bản đồ repository. Các nguồn lịch sử tiếp tục giữ nguyên. Khi có đánh giá độc lập/calibration/vòng kín mới được nghiệm thu, root cập nhật tiếp hai file báo cáo.


## Chốt diễn tiến ngày17/11

Đã thêm mốc17/11 vào timeline của cả hai báo cáo, mô tả việc kiểm chéo quyết định và lịch sử quan sát đã lưu. Mốc ghi rõ đây là phân tích lại thí nghiệm cũ và giới hạn kết luận gain đổi/chuỗi quan sát giữ nguyên ở mức1150. `QA03.json` và `MANIFEST03.json` là nghiệm thu hiện hành. SHA đầu vào và bản SVG độc lập giữ nguyên. Kiểm `git diff --check` đạt trên đúng hai file báo cáo cùng bundle ghi chú của nhánh này, không suy kết quả ấy cho toàn repository hoặc mọi SVG được sinh. Chưa mở browser.
