# RQ2: validation và report snapshot — 08/11/2026

Archive nhỏ giữ source/report và các kiểm đã chạy. Primary analysis run
rq2-conditions-evidence-20261108-01 bất biến, verified6outputs. Không chạy lại
model/simulator/tests/analysis ở archive này; không raw Junyi/correctness/Holdout,
outcomes/traces hoặc graph generation. Không thêm independent empirical samples.

27 synthetic tests pass0.37s. Primary arithmetic0.129116s đọc13selectedinputs có
SHA đối chiếu selected manifests. Reproduction PYTHONHASHSEED17 khớp rawbytes/SHA.
Run/control receipts ghi commands/timeouts60s; không có failed targeted attempt
trong workflow đã lưu. Source snapshots pre/post tests giống nhau, copies exact.

Findings mới: paired profile moderation PYH-PY có5seed dương/5âm và LOO đổi dấu,
không causal ability effect. Junyi removed/added/shared decomposition tách đúng
corrected976edges/raw979edges và same-learner exposure; pooledrate của control2
tăng dù numerator giảm do denominator giảm. Fixed/common learner estimands và
attrition khác; không quality/equivalence/instructional-effect inference.

archive_copy_inventory_before.json lập trước copy; archive_copy_inventory.json
đối chiếu source/destination SHA. Report/script snapshots giữ links repository
gốc; inventory chỉ rõ mapping, không giả bundle là standalone runtime.
record_evidence_run/verify_evidence_bundle đóng và kiểm output hashes; từ closure
chỉ đọc. *.log cần force-add theo force_add_paths.txt. Không sửa rootindex/state
hoặc Git. Đây là validation của một stored reanalysis, không thí nghiệm thứ hai.
