# Kết quả baseline standard BKT — Junyi Academy

Số liệu trong báo cáo được đọc trực tiếp từ artifacts CV, final refit và holdout Test tại `experiments/bkt_baseline/results/wsl_cpp/`. Các artifact gốc đã giữ nguyên hash qua lần di chuyển; bản tóm tắt public-safe của inventory nằm ở `experiments/bkt_baseline/relocation_summary.json`. Artifacts và manifest đầy đủ được giữ local, không phân phối trong repo.

## Giao thức cố định

Sử dụng CAHLR/pyBKT 1.4.3 C++ đã vá; fit một standard BKT cho mỗi `exercise`, target là `correct`, `forgets=False`, `num_fits=1`, `tol=0.005`, `maxiter=100`, seed 42. Thứ tự tuần tự là `time_done`, rồi `source_row` để xử lý timestamp tie xác định.

Dữ liệu gốc có 25.925.992 dòng. Tiền xử lý tạo 25.924.553 dòng canonical, loại 1.439 dòng trùng chính xác trong bản phái sinh và giữ lineage. Assignment toàn cục chia 198.084 học sinh Development và 49.522 Test; 5 fold Development có 39.616–39.617 học sinh/fold. Học sinh không giao giữa Development/Test hoặc các fold.

Dự đoán là one-step-ahead: phản hồi của tương tác hiện tại không dùng để tạo dự đoán cùng tương tác đó; sau dự đoán mới được dùng để cập nhật state cho tương tác sau của cùng học sinh và exercise. `suggested` chỉ dùng phân nhóm. Exercise không xuất hiện trong train được tính là unseen, nhận giá trị prediction null, bị loại khỏi denominator của metric BKT và vẫn được tính vào coverage; không dùng xác suất fallback thay thế.

## Cross-validation 5 fold trong Development

Các giá trị là trung bình ± độ lệch chuẩn mẫu giữa 5 fold, đọc từ `cv_cpp/cv/cv.json`.

| Metric | Mean ± SD |
|---|---:|
| AUC-ROC | 0,783413 ± 0,001158 |
| Log Loss | 0,375607 ± 0,001575 |
| Brier Score | 0,115105 ± 0,000576 |
| ECE (15 bin) | 0,002241 ± 0,000719 |
| Accuracy (0,5) | 0,847416 ± 0,000748 |

Trong tổng 20.706.208 dòng validation qua các fold, 20.706.014 dòng có fitted BKT prediction (coverage 99,9991%); 194 dòng thuộc skill chưa có model trong fold đó. CV hoàn tất với wall time đo được 44.479,2 giây (12 giờ 21 phút), peak RSS 1.262.989.312 byte. Wall time bao gồm các lần resume và đọc/ghi checkpoint.

Tóm tắt subgroup CV theo fold:

| Nhóm | Dòng / coverage | AUC | Log Loss | Brier | ECE | Accuracy |
|---|---:|---:|---:|---:|---:|---:|
| suggested | 4.257.233 / 100% | 0,811594 ± 0,082122 | 0,147152 ± 0,001199 | 0,026547 ± 0,000313 | 0,129975 ± 0,000958 | 0,991852 ± 0,000485 |
| non-suggested | 16.448.975 / 99,9988% | 0,780346 ± 0,001398 | 0,434728 ± 0,001872 | 0,138023 ± 0,000664 | 0,035152 ± 0,000899 | 0,810038 ± 0,000890 |

`suggested` có tỷ lệ `correct=1` gần như tuyệt đối nên AUC theo fold dao động mạnh; không diễn giải đây như so sánh chất lượng ổn định giữa hai nhóm.

## Refit cuối trên toàn Development

Fresh refit dùng 198.084 học sinh và 20.706.208 tương tác Development, tạo đủ 720/720 model exercise. Có 709 model dừng theo tolerance và 11 chạm `maxiter=100`; không có likelihood hay parameter không hữu hạn. Không dùng holdout Test trong fit (`holdout_test_used=false`).

- Wall time đo được: 10.161,8 giây (2 giờ 49 phút).
- Peak RSS: 691.073.024 byte.
- Số vòng EM trung bình: 23,31; min 3, max 100.
- 11 model đạt iteration limit được giữ nguyên theo quyết định đã chốt.

## Holdout Test — đánh giá một lần

Test có 5.218.345 tương tác từ 49.522 học sinh. Hai exercise không có model Development là `skip_counting_by_10s` và `subtraction_within_20`, gồm tổng cộng 9 tương tác của 1 học sinh; các dòng đó không nhận fitted BKT prediction và không vào metric. Coverage là 5.218.336 / 5.218.345 = 99,9998275%. Tỷ lệ `correct=1` trên toàn Test là 82,825685%.

| Metric | Test | Denominator |
|---|---:|---:|
| AUC-ROC | 0,785340 | 5.218.336 quan sát (3.873.542.820.199 cặp dương/âm) |
| Log Loss | 0,374117 | 5.218.336 |
| Brier Score | 0,114671 | 5.218.336 |
| ECE (15 bin) | 0,002303 | 5.218.336 |
| Accuracy (0,5) | 0,847644 | 5.218.336 |

### Test theo `suggested`

| Nhóm | Dòng / scored / coverage | Tỷ lệ correct=1 | AUC | Log Loss | Brier | ECE | Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| suggested | 1.069.815 / 1.069.815 / 100% | 99,999626% | 0,633181 | 0,147144 | 0,026586 | 0,129938 | 0,992191 |
| non-suggested | 4.148.530 / 4.148.521 / 99,999783% | 78,396902% | 0,782688 | 0,432649 | 0,137386 | 0,035254 | 0,810369 |

Mỗi metric trong một nhóm dùng toàn bộ scored rows của nhóm: 1.069.815 và 4.148.521 tương ứng. AUC suggested chỉ có 4 nhãn âm, vì vậy giá trị này rất nhạy với các ít trường hợp sai. Chênh lệch các metric giữa suggested và non-suggested bị ảnh hưởng mạnh bởi khác biệt prevalence; không phải tác động nhân quả của gợi ý.

### Coverage theo support skill

Support được xác định từ số học sinh Development của từng exercise.

| Support Development | Exercise Test | Dòng Test | Scored | Coverage |
|---|---:|---:|---:|---:|
| Unseen | 2 | 9 | 0 | 0% |
| 1–9 học sinh | 8 | 126 | 126 | 100% |
| 10–49 | 45 | 2.958 | 2.958 | 100% |
| 50–99 | 62 | 12.965 | 12.965 | 100% |
| 100–999 | 279 | 330.363 | 330.363 | 100% |
| ≥1.000 | 315 | 4.871.924 | 4.871.924 | 100% |

## So sánh CV với Test

| Metric | CV mean ± SD | Test | Test − CV mean |
|---|---:|---:|---:|
| AUC-ROC | 0,783413 ± 0,001158 | 0,785340 | +0,001927 |
| Log Loss | 0,375607 ± 0,001575 | 0,374117 | −0,001490 |
| Brier Score | 0,115105 ± 0,000576 | 0,114671 | −0,000434 |
| ECE | 0,002241 ± 0,000719 | 0,002303 | +0,000062 |
| Accuracy | 0,847416 ± 0,000748 | 0,847644 | +0,000228 |

Test nằm gần các trung bình CV ở cả năm metric; đây là đối chiếu mô tả trên split đã khóa, không phải cơ sở để điều chỉnh lại mô hình. Final refit và Test đều dùng cùng source patch, backend hash, assignment và cấu hình ghi trong manifests.

## Giới hạn

11 model final refit chạm iteration limit nên chưa đạt tiêu chí dừng theo tolerance; các model vẫn được giữ nguyên theo quyết định đã chốt. Metric suggested chịu mất cân bằng lớp rất lớn. Metric hiếm có support nhỏ và có thể không ổn định. Test đã được xem một lần và không được tái dùng để tuning.
