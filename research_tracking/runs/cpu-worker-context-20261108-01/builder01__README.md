# Lượt fixture builder 01 — có lỗi được giữ lại

Nguồn: snapshot hai file trong `source/`; SHA trước copy nằm trong `run.json` và được đối chiếu lại ở handoff inventory lượt 03. Chỉ chạy DuckDB/CPU dummy, không model/worker/GPU/realdata.

Lệnh chính: `.venv\Scripts\python.exe -m pytest tests/akt/test_synthetic_context_builder.py -q --basetemp artifacts/akt/tmp/parallel-synthetic-context-20261108-01 --junitxml artifacts/akt/local-tests/parallel-synthetic-context-20261108-01/tests.xml`; subprocess timeout 60 giây.

Kết quả thực: 52 pass, 1 fail, 2 warning cache, 5.62 giây pytest; wrapper 6.90 giây. Failure CLI fixture do argument root mặc định giữ giá trị import thay vì root đã monkeypatch. Bản sửa truyền PROJECT_ROOT tường minh từ CLI đến API; không nới guard. Lượt 02 kiểm lại toàn bộ 53 case. Không xóa payload dở dang và không tái sử dụng ID fixture lỗi.
