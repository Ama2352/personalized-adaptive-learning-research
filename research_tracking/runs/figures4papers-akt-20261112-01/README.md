# Thử áp dụng figures4papers cho figure KLTN — 12/11/2026

## Kết quả đã đạt

Đã dựng figure từ lịch sử A0 GPU Main60 đã nghiệm thu. Có SVG độc lập, PDF vector, PNG 300 DPI, bảng CSV và script dựng lại. Đã xem trực tiếp PNG, sửa vị trí nhãn AUC để tránh đè đường dữ liệu và giữ cả bản hình đầu. Bản dùng trong báo cáo ở `revision02/`. HTML hiện hành nhúng SVG để mang theo hình khi chia sẻ.

Đây là bổ sung trình bày từ kết quả huấn luyện có sẵn. Nguồn số liệu là `../modal-akt-recovery-20261112-01/main60-a0__fit80__epochs.json`, được đối chiếu với `main60-a0-verification.json`. Tập selection có sáu học viên, dùng chọn epoch. Chưa có so sánh chất lượng A0 với CG-AKT hoặc đánh giá độc lập trong figure này.

## Phần kế thừa từ repo

Đã đọc hướng dẫn, API quy ước, lý thuyết thiết kế, bố cục và LICENSE tại commit `e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15`. Các bản nguồn và URL chính xác nằm trong `upstream-reference.json`. Repo cung cấp script minh họa và hướng dẫn Matplotlib. Những tên helper trong API cần được cài đặt hoặc chuyển thể trong dự án dùng chúng.

Figure thử áp dụng màu xanh `#0F4D92`, nhấn đỏ `#B64342`, trục gọn, chữ vector, đường có marker và xuất nhiều định dạng. Phần đọc log, kiểm danh tính nguồn, giới hạn diễn giải và chú giải được viết cho KLTN. Không cần sao chép các project hình minh họa khác để tạo hình A0.

LICENSE gốc ghi Creative Commons Attribution-NonCommercial 4.0 International. Đã giữ nguyên LICENSE và ghi nguồn Chen Liu trong script. Các bản chuyển thể tiếp theo cần giữ thông tin nguồn và phạm vi giấy phép của phần kế thừa.

## Đánh giá để dùng tiếp

| Phần nghiên cứu | Figure phù hợp | Câu hỏi cần làm rõ |
|---|---|---|
| RQ1 | Các panel nối tiếp xác suất, nhãn thành thạo, tập sẵn sàng và hành động | Đồ thị ngừng tạo khác biệt ở mắt xích nào? |
| RQ2 | Dot plot chênh lệch theo cặp, nhóm theo năng lực, nguồn đồ thị hoặc mức nhiễu | Hiệu ứng đổi dấu và khác nhau giữa điều kiện ra sao? |
| RQ3 | Đường chọn epoch, biểu đồ hiệu chỉnh, panel so sánh A0/A1/A2/A3 trên cùng quần thể | Confidence và gate ảnh hưởng dự báo, quyết định và kết quả học thế nào? |

Mỗi trục giữ đơn vị đo và chiều tốt hơn rõ ràng. Màu đại diện biến thể cần nhất quán trước khi xem kết quả. Chênh lệch âm/dương dùng đường tham chiếu 0. Thanh biểu diễn độ lớn bắt đầu từ 0 khi phù hợp, trục thu hẹp của đường xu hướng giữ nhãn số đầy đủ. Khoảng bất định cần tính theo đơn vị học viên hoặc khối seed của thí nghiệm. Figure A0 hiện tại chỉ có một lượt seed42 nên chưa thêm khoảng bất định.

Chỉ chuyển dần các figure đang phục vụ luận điểm nghiên cứu chính. Các hình cũ và số liệu của chúng vẫn được lưu trong bundle gốc. Khi thay hình cần giữ phiên bản mới, dữ liệu và script tương ứng.

## Dựng lại

Từ `D:\Dev\KLTN`, dùng Python của `.venv` và một thư mục đầu ra mới trong vùng evidence hoặc local-test đã quy định.

```powershell
.\.venv\Scripts\python.exe -B research_tracking/runs/figures4papers-akt-20261112-01/build_figure.py --output-dir artifacts/figure_runtime/figures4papers-20261112-01/reproduction01
```

`build_figure.py` là mã bản đã chỉnh nhãn. `build_figure_revision01.py` giữ mã bản đầu. Script từ chối ghi đè đầu ra đã có. `figure-data.csv` giữ cả native BCE float32 dùng chọn epoch và Log Loss tính từ dự báo xuất ra. Hai đại lượng có sai khác làm tròn nhỏ. Panel chọn epoch dùng đúng đại lượng native của protocol.

## Môi trường và kiểm tra

Matplotlib và dependencies được cài vào `.venv` KLTN. Trước cài đã khóa toàn bộ 145 package đang có. Kiểm sau cài xác nhận cả 145 phiên bản giữ nguyên, `pip check` đạt. `runtime-verification.json` ghi phiên bản plotting, các log cài và render giữ cùng bundle. Cache Matplotlib nằm trong `artifacts/figure_runtime/`. Lượt dựng figure chạy local và không cấp GPU.

Đã kiểm SVG parse được, dữ liệu CSV khớp lịch sử tám epoch, output hashes và 12 SVG trong HTML có ID riêng. Có kiểm trực quan PNG bản sửa. Chưa kiểm bố cục toàn trang HTML trong trình duyệt ở lượt này.

## Nguồn

- [figures4papers](https://github.com/ChenLiu-1996/figures4papers).
- [Hướng dẫn Matplotlib đã ghim](https://github.com/ChenLiu-1996/figures4papers/tree/e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15/scientific-figure-making).
- [LICENSE đã ghim](https://github.com/ChenLiu-1996/figures4papers/blob/e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15/LICENSE).
