# RQ1 — tách scalar P và vector S đã lưu

Chỉ phân tích lại pilot fixed-stream có sẵn; không thêm quan sát, không chạy mô hình/simulator. S là mastery_score nguồn, không ground-truth mastery hay xác suất đã hiệu chỉnh. M giữ boolean is_mastered thật; A chỉ concept preview. Không nested funnel/causal mediation, không chốt S04/S05.

analysis.json có pooled/seed/profile quantities và đối chiếu loss/Brier với18aggregates cũ; event_flags.csv giữ mẫu số và cases để trích dẫn. Reproduce helper từ repository root bằng .venv; run_id exclusive nên muốn chạy lại phải chọn ID mới trong bản sao nguồn, không ghi đè bundle này.
