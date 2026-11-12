# Frontier thành thạo nghiêm ngặt trên cùng trạng thái lịch sử

## Câu hỏi và phát hiện

Phân tích tiếp nối footprint ngoại lệ đủ6lần chọn của controller Paper2. Khi giữ nguyên trạng thái mô hình tại mỗi bước nhưng yêu cầu mọi parent thực sự được mô hình đánh dấu mastered, tập bài đủ điều kiện thay đổi bao nhiêu? Đây là chẩn đoán readiness, chưa tính lại hành động hoặc kết quả học.

Trong3.240snapshot đã lưu, frontier thay đổi ở2.557snapshot. Có18.520lượt thành viên bị loại khỏi tổng30.572lượt thành viên của frontier gốc, còn12.052lượt thành viên strict. Một concept xuất hiện ở nhiều thời điểm được tính nhiều lần. Frontier strict vẫn có ít nhất một concept ở cả3.240snapshot. Vì vậy, thiếu bài strict không giải thích việc dùng ngoại lệ ở các trạng thái đang quan sát.

| Estimator | Snapshot | Snapshot frontier đổi | Thành viên gốc | Thành viên strict | Served concept ngoài strict |
|---|---|---|---|---|---|
| Không đồ thị |1.080|844|10.256|4.005|687|
| Gói đồ thị đầy đủ |1.080|869|10.060|4.042|667|
| Gói với estimator graph rỗng |1.080|844|10.256|4.005|687|
| **Tổng** |**3.240**|**2.557**|**30.572**|**12.052**|**2.041**|

Các2.041served concept ngoài strict khớp exact các hành động sử dụng ngoại lệ exposure trong phân tích trước. Tổng này được xác nhận lại qua bảng cờ từng event đã đóng, không tạo thêm2.041bằng chứng độc lập. Các khác biệt giữa estimator rows mô tả những lịch sử đã phân kỳ. Không lấy chúng làm paired causal contrasts.

## Thiết kế và giới hạn

Đầu vào là current-source diagnostic reconstruction của27quỹ đạo,3seedfamilies20000–20002×3profile×3variant, mỗi quỹ đạo120bước. Đọc M28 ghi trước selection bookkeeping và graph controller31cạnh. Đếm visits từ served prefix trong từng quỹ đạo, tăng sau snapshot hiện tại. Baseline frontier cho phép parent mastered hoặc visits≥6. Strict frontier chỉ giữ concept chưa mastered và mọi parent mastered. Các roots tuân theo điều kiện parent rỗng. Không áp fallback mới và không gọi getter, policy, mô hình, môi trường hoặc RNG.

Baseline dựng lại khớp cả thứ tự và thành viên ready_set ở3.240/3.240snapshot. Cờ served outside strict khớp3.240/3.240event flags cũ. Graph và input SHA được kiểm trước và sau. Đọc streaming23.810.358byte giải nén từ gzip848.299byte, giữ từng dòng giới hạn64KiB. Lượt thành công hoàn tất khoảng0,387giây với peakRSS28.053.504byte, dưới cap60giây/256MiB.

Trace chỉ giữ mastery_score của balanced candidates thực tế và thiếu fullscorevector ở3.240/3.240snapshot. Lọc/rebalance strict có thể làm xuất hiện ứng viên chưa có score. Vì thế phân tích không dựng chosen action hoặc question mới. Frontier strict không rỗng cho biết tồn tại bài thỏa mastery ở trạng thái này. Chưa biết bộ lọc anti-repeat, escape và xếp hạng sẽ chọn bài nào. Không suy2.041hành động counterfactual chắc chắn khác dưới toàn bộ selector gốc.

Đây là thay rule trên từng trạng thái lịch sử giữ nguyên. Nếu áp dụng rule qua nhiều bước, trạng thái tiếp theo sẽ phân kỳ và các số trên không còn là trajectory counterfactual. Không suy kết quả học, calibration, causal mediation, lợi ích/hại của bỏ ngoại lệ hoặc kết luận graph đã bị vô hiệu hóa. Đơn vị độc lập vẫn là3seedfamilies được tái sử dụng, newindependentN=0.

## Hồ sơ và tái dựng

- `analyze.py` là analyzer stdlib, chạy bằng `.venv\Scripts\python.exe -B research_tracking/runs/rq1-strict-readiness-shadow-20261112-01/analyze.py`. Output dùng exclusivecreate, muốn tái dựng cần chỉ định vị trí mới trong bản sao script thay vì ghi đè bằng chứng.
- `inputs.json` giữ input paths, bytes và SHA. Nguồn immutable ở bundle reconstruction08/11 và ready-exposure08/11, không sao chép gzip hoặc sửa closedbundle.
- `events.csv` giữ3.240hàng với identity và số đếm eligibility, không nhãn outcome hay probability.
- `summary.json` giữ40groups gồm pooled/variant/profile/trajectory, counters và telemetry.
- `execution02.log` giữ stdout của lượt thành công.
- `failure01.log` và `failed01-source.json` giữ lỗi đọc UTF-8 BOM trước khi xử lý CSV. Sửa reader sang utf-8-sig, giữ nguyên mọi byte đầu vào. Lượt lỗi dừng trước khi đọc trace hoặc ghi event output.
- `independent-check.json` đối chiếu riêng từCSVoutput và bảng cờ exposure nguồn, không gọi analyzer hoặc đọc lại gzip.
- `manifest.json` kiểm inventory các file nhỏ của bundle. Bundle để mở chờ Root review và tích hợp báo cáo.

Kết quả bổ sung câu trả lời RQ1 ở mắt xích mastery→readiness. Việc áp dụng strict-only controller vào benchmark chính vẫn cần thiết kế và quyết định phương pháp riêng.

## Figure phục vụ báo cáo

`strict-readiness-shadow.svg`, `.pdf` và `.png` thể hiện cùng một stacked-bar figure cho ba estimator. Phần xanh là lượt concept–snapshot thỏa strict mastery, phần đỏ là lượt chỉ được mở nhờ ngoại lệ exposure. Tổng ở cuối thanh là số membership gốc. Không dùng chiều dài thanh để so hiệu quả học giữa các estimator có lịch sử khác nhau.

Dữ liệu figure ở `figure-data.csv`, dựng trực tiếp từ `summary.json` bằng `build_figure.py`. Chạy trong `.venv` với matplotlib đã có, không cài global hoặc import Torch. Dùng palette và quy ước trục/xuất vector figures4papers đã áp dụng trong repository, tham khảo Chen Liu, commit `e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15`. Phần đọc dữ liệu và bố cục figure được viết riêng cho KLTN.

Đã mở PNG để kiểm trực quan. Nhãn số nằm trong từng đoạn thanh, tổng nằm ngoài thanh, legend tách khỏi plot và ba dòng chú thích tách khỏi trục. Không thấy chữ/số bị chồng hoặc cắt. `figure-review.json` lưu phạm vi kiểm và danh tính dữ liệu/hình. Figure chỉ trình bày phân tích eligibility đã có, không thêm thí nghiệm.

## Nghiệm thu Root12/11

Root đã kiểmSHA toàn bộ18file trong inventory mở, đọc analyzer, đối chiếu độc lập3.240event keys và các tổng từCSV, xem PNG. Chấp nhận kết luận eligibility-only trong phạm vi current-source reconstruction. Giữ0newN và0counterfactualaction. Các nguồn thiếu fullscorevector được ghi rõ. Bundle được đóng sau cập nhật báo cáo, không dùng kết quả này để tự thay controller chính.
