# Tái lập bảng thống kê Paper2 từ outcome đã lưu

## Mục tiêu thuộc đề cương

Đã đọc PDF đề cương trong paper2, đặc biệt trang5 yêu cầu tái lập kết quả hai công trình ở Sprint1 và bootstrap/kiểm định/hiệu chỉnh Holm ở Sprint5. Gói này thực hiện một phần tái lập thống kê của Paper2, giúp xác nhận nền số liệu mà RQ1/RQ2 phát triển tiếp. Không thay RQ, thiết kế thí nghiệm hay family thống kê.

Nguồn là frozen simulator outputs của `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/`. Hai phase mỗi phase có600dòng model×profile×seed, gồm4model×3profile×50seed. Dùng đúng family45hypotheses fixed-replay và72hypotheses closed-loop, không chia lại family theo profile hoặc comparator. Không đọc dữ liệu Junyi confirmation/Holdout.

Manifest lịch sử ghi300bước fixed-replay và500bước closed-loop. Các dòng ở đây thuộc phép chạy lịch sử đó. Fresh120 của chương trình chẩn đoán RQ2 được giữ ở bundle riêng và không gộp vào các family này.

## Đã tự tính lại và đã kế thừa

| Thành phần | Phạm vi thực hiện |
| --- | --- |
| Mean mỗi model và mean paired delta | Tính lại từ600seedrows/phase cho toàn117hypotheses, ghép đúng seed1000–1049 theo profile |
| Family, n và mapping bảng combined | Tái dùng verifier gốc của Paper2 để kiểm45/72hypotheses,50pairedseeds và bảng combined117dòng |
| Holm adjusted p và rejection | Tái dùng verifier gốc, thêm tính Decimal độc lập từ p-value đã lưu để đối chiếu toàn family |
| Wilcoxon p-value | Kế thừa raw p-value frozen, không chạy lại signed-rank test |
| Bootstrap CI95% | Kế thừa CI từ3.000pairedseedbootstrap draws lịch sử, không sinh draws mới |
| Simulator/model | Không sinh event, rerun trajectory hoặc fit model |

`ACCEPTANCE.json` xác nhận117dòng khớp. Verifier gốc thực hiện1.676checks trong phạm vi các hàm được gọi. Sai số tuyệt đối lớn nhất của model mean là5,329×10⁻¹⁵, paired delta2,220×10⁻¹⁶ và Holm p2,776×10⁻¹⁷. Tất cả thấp hơn tolerance mean/delta1×10⁻¹² và Holm5×10⁻¹³ đã khai báo trong source trước execution. Source input SHA trước/sau trùng nhau. Phần tính lại dùng CPU khoảng0,0865giây, không gồm dựng figure.

13hồi quy tổng hợp đạt trong0,08giây. Có kiểm exactpairing, duplicate/missing/nonfinite/foreignseed, Holm ties/cap/zero và khác biệt quyết định khi dùng đúng family45 hoặc72. Kiểm thử không dùng source dataset hay checkpoint.

## Kết quả có thể trình bày

Contrast chính là Graph-GAM-KT trừ GAM-KT, tức cả gói context/adaptation. Mỗi hồ sơ có50seed ghép cặp. Các pHolm dưới đây đã tính lại, các CI trong figure giữ từ nguồn.

| Hồ sơ | Δ Log Loss cùng luồng | pHolm family45 | Δ mean learning gain | Δ retention theta gain |
| --- | ---: | ---: | ---: | ---: |
| Năng lực cao | −0,000255888 | 0,413548 | +0,007455 | −0,006615 |
| Năng lực thấp | −0,003194533 | 7,994×10⁻¹⁴ | +0,026815 | +0,037761 |
| Yếu hàm số | −0,001692390 | 3,197×10⁻¹³ | −0,015907 | −0,009136 |

Log Loss thấp hơn ở cả ba mean, nhưng chỉ Low và Function-weak qua Holm. Cả sáu contrast của hai outcome gain chính ở ba profile có pHolm bằng1 trong family72. Kết quả tái lập được khoảng cách giữa lợi ích dự báo và bằng chứng outcome học tập của Paper2. Các contrast chưa chứng minh tương đương hoặc riêng tác động của cạnh tiên quyết. Chưa phải bảng đánh giá AKT/CG-AKT hiện hành.

`mean_learning_gain` theo source Paper2 là gain trung bình mỗi lần luyện. `retention_theta_gain` là gain theta trung bình còn lại tại snapshot14ngày. Đây là hai outcome khác nhau, không suy tỷ lệ scalar43,17% giữa hai cột. Phân tích redundancy retention trong RQ2 áp dụng net mean-theta gain cuối và sau14ngày theo cùng readout.

## Figure và bảng

- `ALL_117_RECONCILED.csv` giữ đầy đủ117dòng, p/CI nguồn và các mean/delta/Holm đã tính lại.
- `PRIMARY_PACKAGE_CONTRAST.csv` có39contrast Graph-GAM-KT−GAM-KT.
- `FIGURE_DATA.csv` giữ9dòng của ba panel LL, learning gain, retention gain.
- `paper2-prediction-outcome-v01.svg` là figure độc lập, PNG là bản kiểm trực quan. Đã mở PNG, nhãn và khoảng không chồng nhau.
- `FIGURE_METADATA.json`, `build_figure.py` giữ cách dựng. CI95% trong figure chưa điều chỉnh đa kiểm định. Điểm tô dùng quyết định Holm trên p-value, vì vậy CI không cắt0 và điểm chưa qua Holm có thể cùng xuất hiện.

## Dựng lại và giới hạn

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/shared_kt/test_paper2_statistical_reconstruction.py -q -p no:cacheprovider --basetemp=artifacts/akt/runtime/paper2-statistical-tests-20261117-02
.\.venv\Scripts\python.exe -B research_tracking/runs/paper2-statistical-reproduction-20261117-01/reproduce_statistics.py
.\.venv\Scripts\python.exe -B research_tracking/runs/paper2-statistical-reproduction-20261117-01/build_figure.py
```

Source từ chối ghi đè output đã có. Khi tái dựng, sao source sang workspace runtime riêng và đặt HERE đúng output mới, giữ ROOT trỏ repository và PAPER trỏ source frozen. Không chạy đè bundle đã đóng.

Gói này hoàn thiện phần đối chiếu bảng số học và Holm từ kết quả lịch sử. Tái chạy simulator, signed-rank và bootstrap vẫn ngoài phạm vi đã thực hiện. RQ1/RQ2 còn đòi chẩn đoán/fitted independent evaluation theo báo cáo tổng hợp. Không có model mới, dữ liệu người học mới, test độc lập mới hoặc tuyên bố hoàn tất RQ.
