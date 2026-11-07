# Đối chiếu BKT và GAM-KT trên Development CV

## Phạm vi và nguồn

Đối chiếu chỉ dùng predictions Development của 5 fold đã lưu:

- `experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/`
- `experiments/gam_kt/results/wsl_cpp/cv/`

Không đọc Holdout, không chạy lại CV và không thay đổi artifact cũ. BKT giữ protocol đã đóng băng; GAM-KT là pipeline graph-free, difficulty fit trên phần train của từng fold và replay dự đoán trước khi cập nhật đáp án hiện tại. `suggested` chỉ dùng phân nhóm.

## Đối chiếu độ phủ và dòng dữ liệu

Ghép từng fold bằng `source_row`. Cả 5 fold có cùng số dòng giữa hai hệ thống; không có trùng `source_row`, không lệch `user_id`, `exercise`, `correct`, `suggested` hoặc train support. Mỗi row BKT/GAM đại diện cùng một interaction Development. GAM-KT gắn cờ 194 dòng fallback (34, 16, 0, 0, 144 theo fold); các dòng đó không được tính là dự đoán fitted và bị loại khỏi common-row metrics. BKT cũng không có fitted prediction cho đúng các dòng này.

| Fold | Tổng dòng ghép | Common fitted rows | Fallback GAM-KT |
|---:|---:|---:|---:|
| 0 | 4,198,649 | 4,198,615 | 34 |
| 1 | 4,061,255 | 4,061,239 | 16 |
| 2 | 4,182,390 | 4,182,390 | 0 |
| 3 | 4,126,864 | 4,126,864 | 0 |
| 4 | 4,137,050 | 4,136,906 | 144 |
| **Tổng** | **20,706,208** | **20,706,014** | **194** |

Coverage common fitted là 20,706,014 / 20,706,208 (99.9991%). Mỗi fold gồm 39,616–39,617 learner; bootstrap dùng toàn bộ dòng fitted của learner khi learner được lấy mẫu.

## Kết quả common-row

Giá trị là trung bình 5 fold ± sample SD. Chênh lệch có dấu được tính `GAM-KT − BKT`; AUC/Log Loss/Brier/ECE thấp hơn hoặc cao hơn tùy metric, Accuracy cao hơn là tốt hơn. ECE dùng 15 bin đều, khoảng `[k/15,(k+1)/15)` và p=1 nằm bin cuối; Accuracy dùng ngưỡng p≥0.5.

| Metric | BKT | GAM-KT | GAM-KT − BKT |
|---|---:|---:|---:|
| AUC | 0.783413 ± 0.001158 | 0.774866 ± 0.001064 | −0.008547 |
| Log Loss | 0.375607 ± 0.001575 | 0.394881 ± 0.001407 | +0.019273 |
| Brier | 0.115105 ± 0.000576 | 0.120372 ± 0.000575 | +0.005266 |
| ECE | 0.002241 ± 0.000719 | 0.055542 ± 0.000673 | +0.053301 |
| Accuracy | 0.847416 ± 0.000748 | 0.841453 ± 0.001029 | −0.005963 |

BKT tốt hơn trên cả năm metric trong từng fold. GAM-KT thấp hơn khoảng 0.60 điểm phần trăm accuracy và ECE của GAM-KT lớn hơn rõ rệt, cho thấy xác suất dự đoán kém calibration trên common rows. Không diễn giải ECE dưới dạng phần trăm thay đổi vì ECE BKT rất gần 0.

## Paired cluster bootstrap

Bootstrap lấy learner có hoàn lại độc lập bên trong từng fold, tính metric chênh lệch trên các interaction của learner được lấy, sau đó lấy trung bình không trọng số của 5 fold. Báo cáo percentile CI 95%, 1.000 lần lặp, seed 20261030. Đây là CI có điều kiện trên năm split/model fit hiện có; nó mô tả biến thiên lấy mẫu learner, không bao gồm bất định từ việc fit lại mô hình hay tạo split mới.

| Metric chênh lệch | Ước lượng GAM-KT − BKT | CI 95% |
|---|---:|---:|
| Log Loss | +0.019273 | [+0.018780, +0.019730] |
| Brier | +0.005266 | [+0.005096, +0.005413] |
| ECE | +0.053301 | [+0.052170, +0.053826] |
| Accuracy | −0.005963 | [−0.006201, −0.005702] |

AUC được tính chính xác trên từng fold và nằm trong bảng common-row; paired cluster CI cho AUC chưa tính vì cần tính lại AUC trên hàng triệu interaction ở mỗi mẫu bootstrap. Không thay bằng metric xấp xỉ hoặc estimand khác. Các CI trên không chứa 0 và cùng chiều với kết quả ở cả năm fold. Do kích thước dữ liệu lớn, mức độ ổn định này không tự chứng minh rằng khác biệt có ý nghĩa thực tiễn ngoài protocol và quần thể Development đang xét.

## Tái lập bootstrap

```powershell
$bootstrapReport = 'research_tracking/reports/paired_cluster_bootstrap_bkt_gam_RECHECK_NEW_RUN_ID.json'
if (Test-Path -LiteralPath $bootstrapReport) { throw 'Output already exists; choose a new run ID' }
.\.venv\Scripts\python.exe scripts/bootstrap_bkt_gam_cv.py --replicates 1000 --seed 20261030 --output $bootstrapReport
```

Thay `NEW_RUN_ID` bằng ID mới trước khi chạy trong phạm vi được duyệt. Script chỉ đọc Parquet predictions theo fold đã lưu, kiểm tra join/alignment/coverage, tổng hợp sufficient statistics theo learner trong DuckDB rồi bootstrap. Nó không nạp toàn bộ bảng predictions vào RAM. JSON mới dùng output riêng trong `research_tracking/reports/`, không ghi đè [JSON lịch sử](../research_tracking/reports/paired_cluster_bootstrap_bkt_gam.json) hoặc artifacts CV cũ. JSON lịch sử chỉ được chuyển vị trí ngày07/11, không tính lại; xem [relocation manifest](../research_tracking/reports/report_relocation_20261107.json).
