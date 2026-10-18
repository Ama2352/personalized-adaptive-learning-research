# Runbook baseline BKT chuẩn — Junyi Academy

## Môi trường hiện tại

- Project Python cài editable trong `venv/` trên Windows; package mới là `knowledge_tracing.bkt_baseline`.
- CAHLR/pyBKT pin ở 1.4.3, local dependency trong `third_party/pyBKT/`. Source C++ và bản vá được ghi tại `docs/pybkt-provenance.md`.
- Windows smoke/test dùng môi trường Python cục bộ. WSL2 runner tự tìm project root theo vị trí script; mặc định dùng môi trường ở `/opt/junyi-bkt/venv/`, có thể đổi bằng biến `JUNYI_BKT_VENV`. Distro và đường dẫn môi trường không nằm trong Git.
- Kết quả WSL đã chuyển tới `experiments/bkt_baseline/results/wsl_cpp/`; bản map public-safe ở `experiments/bkt_baseline/relocation_summary.json`. Manifest đầy đủ chỉ được giữ local.

## Lệnh kiểm tra an toàn

Chạy từ thư mục gốc repository trong working tree hiện tại:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests\bkt_baseline -p 'test_*.py' -v
.\venv\Scripts\bkt-baseline.exe --help
.\venv\Scripts\python.exe -c "from knowledge_tracing.bkt_baseline.config import PROJECT_ROOT, DEFAULT_CSV, DEFAULT_ARTIFACTS; print(PROJECT_ROOT, DEFAULT_CSV, DEFAULT_ARTIFACTS)"
bash -n scripts/wsl2/run_cpp_cv.sh
bash -n scripts/wsl2/run_cpp_final_fit.sh
```

Import-only smoke của backend WSL (không fit hoặc predict):

```powershell
wsl.exe -d JunyiBKT-Ubuntu -- bash -lc 'PROJECT_ROOT=/path/to/KLTN; JUNYI_BKT_VENV=/path/to/wsl-venv; PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PROJECT_ROOT/src" "$JUNYI_BKT_VENV/bin/python" -c "import importlib.util; print(importlib.util.find_spec(\"pyBKT.fit.E_step\").origin)"'
```

## Pipeline Windows

Các lệnh CLI hiện tại:

```powershell
.\venv\Scripts\bkt-baseline.exe verify-runtime
.\venv\Scripts\bkt-baseline.exe preprocess
.\venv\Scripts\bkt-baseline.exe split
.\venv\Scripts\bkt-baseline.exe pilot
.\venv\Scripts\bkt-baseline.exe cv
.\venv\Scripts\bkt-baseline.exe final-fit
.\venv\Scripts\bkt-baseline.exe test
.\venv\Scripts\bkt-baseline.exe report
```

Mỗi lệnh ghi vào `artifacts/bkt_baseline/`. `preprocess` yêu cầu ít nhất 12 GB trống; các giai đoạn sau dùng preflight hiện có. Pipeline yêu cầu pilot trước CV, CV trước final-fit, final-fit trước Test. Test chỉ được chạy sau khi người dùng cho phép; không dùng Test để tuning.

Lệnh `report` tạo snapshot Windows tại `docs/bkt-baseline-artifact-report.md` hoặc đường dẫn do `--output` chỉ định. Mặc định này không ghi đè `docs/bkt-baseline-results.md`, là báo cáo chuẩn đã đối chiếu với run WSL hoàn tất.

## Runner WSL2

- `scripts/wsl2/cpp_integration_smoke.py`: smoke tích hợp; tạo file trong thư mục smoke.
- `scripts/wsl2/run_cpp_cv.sh`: bắt đầu hoặc resume CV Development vào `results/wsl_cpp/cv_cpp/`.
- `scripts/wsl2/run_cpp_final_fit.sh`: fit mới trên toàn Development vào `results/wsl_cpp/final_cpp/`.
- `scripts/wsl2/run_cpp_test_eval.py`: holdout Test một lần vào `results/wsl_cpp/test_cpp/`.
- `scripts/wsl2/verify_cpp_final_fit.py`: verifier có thể ghi manifest/final JSON; không dùng khi chỉ cần kiểm tra hash.

Các runner CV/refit/Test có khả năng ghi hoặc resume vào thư mục kết quả đã có. Không chạy lại trong refactor hay chỉ để xem kết quả. Bản báo cáo hiện tại đọc JSON artifacts đã lưu; để kiểm tra chỉ đọc, dùng `docs/bkt-baseline-results.md`. Artifacts và manifests lịch sử được giữ local, không phân phối trong repo public.

## Nguồn dữ liệu và outputs

- CSV gốc: `dataset/junyi_ProblemLog_original.csv`.
- Dữ liệu canonical, lineage và assignments: `artifacts/bkt_baseline/`.
- CV/refit/Test WSL: `experiments/bkt_baseline/results/wsl_cpp/`.
- Kết quả tiếng Việt: `docs/bkt-baseline-results.md`.

Không sửa CSV gốc. Model/prediction artifact, split, config, metric, seed hoặc checkpoint chỉ đổi theo quyết định nghiên cứu rõ ràng. Khi di chuyển result, cập nhật inventory và xác minh SHA-256; không sửa nội dung manifests lịch sử.
