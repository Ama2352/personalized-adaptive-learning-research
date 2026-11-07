# Lượt fixture builder 02 — 53 pass

Nguồn: `scripts/akt/prepare_synthetic_context.py`, `tests/akt/test_synthetic_context_builder.py`, API thực `config.py`, `context.py`, loader `data.py` và split `splits.py`. Chỉ hai file builder/tests mới thuộc ownership agent; không sửa các module cha.

Lệnh chính: `.venv\Scripts\python.exe -m pytest tests/akt/test_synthetic_context_builder.py -q -p no:cacheprovider --basetemp artifacts/akt/tmp/parallel-synthetic-context-20261108-02 --junitxml artifacts/akt/local-tests/parallel-synthetic-context-20261108-02/tests.xml`; subprocess timeout 60 giây.

Kết quả thực: 53 pass trong 6.50 giây; wrapper 7.92 giây, returncode 0, không timeout. Kiểm Parquet 64 dòng/8 learner/2 exercise bằng loader thật, split 6 train/1 val và fold0 sentinel bị loại; chronology/unique time/source; input membership 5 SHA; tamper; deterministic data bytes hai ID trên runtime hiện tại; exclusive output; cap/type/path/CUDA limits; preserve partial failure. Import guard cấm Torch/Modal/backend/runner trong lúc prepare. Không có optimizer step, model forward/backward hay cấp quyền.

Giới hạn: đây là fixture kỹ thuật local Windows, chưa phải Linux/GPU pass, chưa xác nhận runtime/Gate2/lock, mainworker lifecycle hay protocol nghiên cứu. Bit nhãn dummy không phải RQ simulator truth và không mang nghĩa học tập. Không khẳng định Parquet byte-identical giữa các phiên bản DuckDB.
