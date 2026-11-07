# KLTN — Knowledge Tracing

Dự án KLTN về Knowledge Tracing, thông tin tiên quyết và lựa chọn lộ trình học, dùng Junyi Academy và môi trường mô phỏng. Repository khởi đầu từ baseline BKT; phần hướng dẫn chạy bên dưới vẫn dành cho baseline đó.

## Tìm báo cáo và bằng chứng

Bắt đầu tại **[Bản đồ repository và bằng chứng KLTN](docs/REPOSITORY_MAP.md)**: vai trò từng thư mục, kết quả gốc ở đâu, báo cáo nào dùng để viết và cách truy ngược run/hash.

- Kết quả baseline: [BKT](docs/bkt-baseline-results.md), [đối chiếu BKT–GAM-KT](docs/bkt-gam-kt-benchmark.md).
- Phân tích RQ/pilot mới: [research_tracking/reports](research_tracking/reports/); bằng chứng theo run ở [research_tracking/runs](research_tracking/runs/).
- Phạm vi RQ và kế hoạch hiện hành: [research traceability](docs/thesis_recovery/02_RESEARCH_TRACEABILITY.md), [task backlog](docs/thesis_recovery/TASKS.json).

Báo cáo tổng hợp đã thống nhất ở [research_tracking/reports](research_tracking/reports/README.md); output BKT–GAM từ root `reports/` đã chuyển vào đây với hash giữ nguyên. `_context/` giữ ngữ cảnh baseline BKT, không đại diện toàn bộ ba RQ. Nội dung trong `artifacts/` gồm cả đầu vào/source đang sử dụng, không chỉ cache. Quy ước duy trì được ghi trong `AGENTS.md`.

## Bắt đầu

1. Dùng Python 3.13 trên Windows để khớp môi trường đã xác minh.
2. Lấy bộ Junyi ProblemLog theo điều khoản và quyền truy cập của nguồn dữ liệu; dự án không phân phối dữ liệu Junyi.
3. Đặt CSV được cấp quyền tại `dataset/junyi_ProblemLog_original.csv`. Không đưa dữ liệu, file dự đoán, checkpoint hay model đã fit lên Git.
4. Từ thư mục gốc dự án, tạo môi trường và cài các phiên bản đã ghi trong `requirements.txt`:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

5. Chạy kiểm thử đơn vị và xem các lệnh CLI:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests\bkt_baseline -p 'test_*.py' -v
.\.venv\Scripts\bkt-baseline.exe --help
```

`requirements.txt` ghi phiên bản dependency của môi trường Windows đã xác minh và cài pyBKT từ source vendored `third_party/pyBKT`. Môi trường WSL/C++ dùng để tạo kết quả đã báo cáo là môi trường riêng; runner WSL và quy trình chỉ đọc được mô tả trong [runbook](docs/bkt-baseline-runbook.md). Clone mới cần dựng compiler/backend C++ theo hướng dẫn CAHLR/pyBKT trước khi dùng runner đó.

## Cấu trúc

- `src/knowledge_tracing/bkt_baseline/`: tiền xử lý, chia học sinh, adapter pyBKT, huấn luyện và đánh giá.
- `third_party/pyBKT/`: source CAHLR/pyBKT, giữ license upstream và các thay đổi local; xem [provenance](docs/pybkt-provenance.md).
- `scripts/wsl2/`: runner và smoke scripts cho thí nghiệm WSL/C++.
- `tests/bkt_baseline/`: kiểm thử pipeline.
- `_context/`: mục tiêu, quyết định và giao thức nghiên cứu.
- `docs/`: runbook, audit dữ liệu và báo cáo kết quả.
- `experiments/bkt_baseline/relocation_summary.json`: tóm tắt public-safe việc chuyển artifacts; file dữ liệu và kết quả đầy đủ được giữ local.

## Giao thức và kết quả

Mô hình là standard BKT, một model cho mỗi `exercise`, target `correct`, `num_fits=1`, `forgets=False`, `tol=0.005`, `maxiter=100`, seed 42. Development được đánh giá bằng student-disjoint 5-fold CV; holdout Test được đánh giá một lần sau final refit. Xem [báo cáo tiếng Việt](docs/bkt-baseline-results.md) để biết metric, coverage và giới hạn. Báo cáo chỉ chứa số liệu tổng hợp; dữ liệu Junyi và prediction-level outputs không nằm trong repo.

## Phạm vi license

Source CAHLR/pyBKT giữ nguyên `third_party/pyBKT/LICENSE`; các thông báo license kèm Eigen cũng được giữ trong vendor tree. Repository hiện chưa có license cấp quyền tái sử dụng cho phần code của đề tài, vì vậy không được hiểu license MIT của pyBKT là license cho toàn bộ repo. Cần chủ sở hữu chọn license dự án trước khi phát hành công khai.
