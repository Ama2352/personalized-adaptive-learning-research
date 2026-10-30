# GAM-KT với Junyi và giao thức KLTN

## Phạm vi và nguồn implementation

Runner dùng graph-free GAM-KT của Junyi trong notebook `junyi_cycle_corrected_ablation_confirmation.ipynb`, cell 11, thuộc RIVF artifact đã tải. `src/knowledge_tracing/gam_kt/original_junyi.py` giữ nguyên các định nghĩa model, memory, feature hashing, predict và update từ cell này. Parity test nạp trực tiếp cell gốc và so sánh probability, ability (`theta`), memory vector, uncertainty (`pi_task`, `pi_time`), timestamp, số lần quên và outcome history sau từng update. Graph, decay, graph signal và graph adaptation tắt đúng cấu hình Junyi.

Notebook và ZIP nguồn chỉ được đọc. Graph từ `data/simulator_inputs/` không được dùng cho benchmark Junyi.

## Dữ liệu và protocol

- Dùng canonical ProblemLog, `correct`, frozen global user assignments và năm fold đã tạo cho BKT. Không tạo split mới.
- `problem_type` được nối bằng `source_row` một-based của logical CSV record trước dedup. Trước khi dùng, xác minh mỗi Development canonical row qua `user_id`, `exercise`, `time_done`, `correct`; kiểm chứng duplicate lineage và template của duplicate giữ nguyên. Không dựa trên vị trí sau khi dedup.
- Sidecar chỉ lưu các raw record thuộc user Development. `source_row` vẫn đếm trên toàn CSV để giữ đúng khóa canonical. Holdout không được replay hay chấm điểm.
- Timeline theo `(user_id, time_done, source_row)`. Mỗi user bắt đầu state mới; state của user giữ xuyên exercise, còn model lưu state riêng theo exercise. Mỗi event dự đoán trước rồi mới update bằng `correct` hiện tại.
- Mỗi fold difficulty fit bằng bốn fold Development train: global correctness, smoothing alpha=20, chuyển Elo và clipping như source Junyi. Exercise không có trong train dùng global difficulty của fold; mọi prediction fallback phải được ghi nhận.
- Native metrics có thể gồm prediction fallback của thuật toán Junyi; supported-only metrics loại các row đó. Coverage báo riêng fallback/unseen. Không gọi fallback là fitted prediction. Common-row comparison join BKT và GAM-KT theo `source_row`, chỉ trên giao mà BKT có prediction.
- AUC ghi `null` khi chỉ có một nhãn; JSON giữ denominator, prevalence, coverage, nhóm `suggested`/non-`suggested` và support.

## Chạy

Python và các dependency đã pin ở `requirements.txt`; không có dependency mới.

```powershell
$env:PYTHONPATH = 'src'
& '.\venv\Scripts\python.exe' -B -m knowledge_tracing.gam_kt.cli prepare-map
& '.\venv\Scripts\python.exe' -B -m knowledge_tracing.gam_kt.cli pilot --users 2000
& '.\venv\Scripts\python.exe' -B -m knowledge_tracing.gam_kt.cli cv
```

Outputs, checkpoints, DuckDB spill và temporary data nằm trong `artifacts/gam_kt/` hoặc `experiments/gam_kt/results/wsl_cpp/`. Checkpoint gắn hash dữ liệu, assignments, source implementation và shard; mismatch sẽ dừng resume. CV chỉ đọc Development assignments. Không có lệnh holdout trong runner này.

## Readiness trước CV

- Parity gốc: dự đoán và toàn bộ trạng thái online phải khớp exact trên fixture xác định.
- Data mapping: không có source-row thiếu, identity mismatch hoặc lineage lỗi.
- Pilot: Development fold 0, cohort học sinh hash-seeded; đo throughput/RSS và ngoại suy runtime CV. Pilot chỉ quyết định có nên tiếp tục chạy benchmark, không điều chỉnh công thức.
- Full CV chỉ bắt đầu khi các kiểm tra trên pass; sau CV báo mean ± sample SD của năm fold, subgroup và common-row comparison. Holdout không nằm trong phạm vi này.
