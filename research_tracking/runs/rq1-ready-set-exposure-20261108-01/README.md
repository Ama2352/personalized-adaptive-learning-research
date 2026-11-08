# RQ1 — footprint của ngoại lệ exposure trong ready set

Hậu kiểm cache đã nghiệm thu riêng:3240rows/27trajectories, exactR order,0native/model/optimizer/newN. Không causal mediation, calibration, policy intervention hoặc lợi ích học tập.

[Summary](summary.json), [event flags](event_membership_flags.csv), [validation](validation.json), [caller terminal](owned__final.json), [receipt](owned__receipt.json), [plan](plan.md). `report_snapshot.md` giữ nguyên bytes bản report tại closure; original relative links của snapshot thuộc vị trí canonical report, không bị viết lại để giả provenance. Xem báo cáo canonical ở ../../reports/rq1_ready_set_exposure_results_20261108.md.

Bốn inputs gốc tham chiếu trong source_references.json thuộc ../rq1-closed-loop-reconstruction-20261108-02/. Không nhân đôi gzip/source snapshot/edges; toàn125outputs của bundle nguồn được hash-verify trước/sau copy. Optional review files chỉ được copy opaque; sự có mặt không tự là peer-review PASS.

500root events tách khỏi prerequisite denominator;2740nonroot=2041exposure+699strict. Các con số mô tả quỹ đạo đã phân kỳ, không paired effects. Originala585missing, current-source reconstruction.

execution.log là log đóng gói, không nguyên log analyzer. owned__stdout/stderr và source root_outer.py giữ riêng proof execution. Không chép .pt/Parquet/privateRPC/base64/ZIP/dataset; không rerun. Helper chuẩn ghi Git HEAD bằng read-only rev-parse khi closure, không add/commit/push.
