# Chạy lại Wilcoxon và bootstrap Paper2 từ seed outcomes

## Phần vừa hoàn thiện

Gói01 đã tính lại mean, paired delta và Holm, còn dùng raw p-value/CI từ artifact. Followup02 chạy nguyên bốn functions thống kê của notebook Paper2 để tính lại cả Wilcoxon, rank-biserial,3.000paired-seed bootstrap CI và Holm cho117hypotheses. Không chạy cell sinh simulator, model, dữ liệu Junyi hoặc Holdout.

**Kết quả thực tế** — toàn117hypotheses khớp chính xác giá trị float đã lưu cho cả10trường số, tổng1.170so sánh. Sai số tuyệt đối lớn nhất bằng0. Cờ quyết định Holm không khác ở bất kỳ dòng nào. Điều này hoàn thiện phần tái lập thống kê còn thiếu của gói01.

Phạm vi kết luận là tái tính thống kê từ outcomes lịch sử. Chưa tái chạy trajectory/model để kiểm việc sinh outcomes. RQ1/RQ2 vẫn còn các thí nghiệm chính đã ghi trong báo cáo tổng hợp. Kết quả thuộc Sprint1 về tái lập và phần công cụ thống kê Sprint5 theo đề cương được kiểm ở gói01.

## Nguồn và thủ tục được giữ nguyên

Notebook canonical nằm trong `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb`.

- Cell3 cung cấp GLOBAL_SEED20260721, thứ tự profile PG/PY/PYH và full bootstrap3.000draws.
- Cell21 cung cấp nguyên `bootstrap_mean_ci`, `rank_biserial`, `holm_adjust` và `paired_tests`.
- Source được đọc bằng AST, chỉ compile bốn FunctionDef. Cell import/config/simulator và các câu lệnh cuối cell21 không được thực thi.
- Bootstrap dùng `np.random.default_rng(seed)`, mỗi draw chọn lại50paired deltas có hoàn lại rồi tính mean, lấy quantile0,025/0,975. Seed từng hypothesis giữ công thức `GLOBAL_SEED + persona_index*1000 + comparison_index*100 + metric_index`.
- Wilcoxon giữ `zero_method='wilcox'`, `alternative='two-sided'`, giữ nguyên việc source không truyền `method`. Nhánh allclose-zero cũng giữ nguyên.
- Family giữ45fixed-replay và72closed-loop. Không reset Holm theo profile, comparator hoặc outcome.
- Đọc CSV bằng float round-trip chuẩn Python trước dựng DataFrame. Kiểm đủ600dòng và exact50seed1000–1049 cho từng model/profile, tất cả metric hữu hạn. Hàm gốc vẫn chứa dropna, nhưng đầu vào đầy đủ không bị rút mẫu.

Nguồn outcomes, notebook, protocol, requirement và verifier được pin SHA trước/sau. Source function AST cũng có fingerprint riêng trong RESULT.json. Không sửa source Paper2 hoặc bundle01 để làm phép chạy khớp.

## Runtime và tài nguyên

| Mục | Đã đo |
| --- | --- |
| Python local |3.13.5 trong `.venv` repository |
| NumPy / pandas / SciPy |2.5.4 /3.0.6 /1.18.1 |
| Hypotheses |117, mỗi dòng50pairedseeds |
| Bootstrap draws đã tính lại |117×3.000=351.000resamples |
| Worker runtime |5,257giây |
| Parent wall time |5,570giây |
| Peak tổng RSS process tree |147.390.464byte,140,5625MiB |
| Hard cap |180giây,256MiB |
| Exit / stop reason |0 / không có |

Số resample là thao tác thống kê trên cùng50seed mỗi profile, không làm tăng số đơn vị nghiên cứu độc lập. Root watchdog dùng psutil giám sát process con, lưu log và resource receipt. Không có GPU, Modal hoặc cài dependency mới.

Historical requirements không pin phiên bản thư viện. File verification_environment nói rõ chỉ mô tả môi trường kiểm metadata, không tái dựng full experiment environment. Vì vậy không khẳng định đã khôi phục môi trường lịch sử. Runtime hiện tại vẫn tái hiện đúng tất cả số thống kê trên tập outcome đã lưu, kể cả p/CI. Không thay version, thuật toán hoặc tolerance sau khi nhìn kết quả.

So sánh giữ tolerance gốc của verifier Paper2,1e−12 cho trường thông thường và5e−13 riêng Holm. Kết quả thực tế khớp exactfloat nên không cần dựa vào việc nới tolerance.

## File và kiểm thử

- `attempt01/RECOMPUTED_117.csv` giữ bảng tính mới đầy đủ.
- `attempt01/COMPARISON_117.csv` giữ frozen/recomputed/absolute-error và cờ tolerance theo từng trường.
- `attempt01/RESULT.json` giữ procedure, runtime versions, source pins và kết quả117dòng.
- `attempt01/RESOURCE_RECEIPT.json`, `worker.log` và `execution01.txt` giữ bằng chứng thực thi.
- `tests01.txt` ghi3testsCLI/AST đạt trong0,10giây, `tests02.txt` kiểm lại source CLI cuối đạt3/3trong0,08giây. Kiểm nguyên recipe/metric order/Wilcoxon options, normal entrypoint tạo output mới và từ chối đường dẫn ngoài phạm vi hoặc output đã tồn tại.

Không tạo figure mới vì toàn bộ số liệu khớp bảng/figure01. SVG `../paper2-statistical-reproduction-20261117-01/paper2-prediction-outcome-v01.svg` tiếp tục dùng được. Nhãn provenance trên figure mô tả cách bản01 được dựng từ frozen data. Followup02 bổ sung chứng cứ p/CI đã được tính lại.

## Chạy lại với output mới

```powershell
.\.venv\Scripts\python.exe -B research_tracking/runs/paper2-statistical-reproduction-20261117-02/reproduce_original_inference.py --output research_tracking/runs/paper2-statistical-reproduction-20261117-03/attempt01
```

CLI tạo một attempt directory mới, không sửa HERE và không ghi đè attempt01. Chỉ parent được dùng như entrypoint bình thường. Cờ worker dành cho process con do parent giám sát. Sau khi bundle được đóng, các phép tái kiểm mới cần output theo run/phiên bản mới để giữ nguyên evidence đã nghiệm thu.
