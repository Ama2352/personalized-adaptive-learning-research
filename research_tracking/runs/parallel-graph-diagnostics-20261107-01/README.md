# Archive graph prototype và factorial uncertainty — 07/11/2026

Hai loại bằng chứng riêng: graph là kiểm phần mềm synthetic CPU, còn factorial là exploratory post-hoc aggregate analysis. Đây là run đóng gói bằng chứng đã chạy, không thêm model fit, simulator event, GPU/cloud hoặc query raw/Holdout. Không coi status completed là trained CG-AKT/RQ3 hoặc kết luận efficacy.

Graph trial01 giữ nguyên collection failure vì thiếu PYTHONPATH=src; trial02 đạt75cases(42augmentation+33context), không fail/error/skip. Snapshot graph source/tests bind trial02 theo SHA đã handoff. Không có snapshot test source đúng thời điểm trial01; không tuyên bố trial01 dùng cùng source42cases. Graph kernel chưa chọn f/gate architecture, chưa hook native latent/logit, và caller-supplied tensors/session histories vẫn cần end-to-end provenance/isolation review.

Factorial giữ failure01 sai tên metadata key và source lỗi, script sửa, pass02, reproduction và output giống bytes.10seeds/profile,3profiles,10.000joint seed-block draws với seed42. Envelope empirical resampling không là formal population95%CI; không pvalues/significance/final efficacy. PG deficit0/2400 là mechanism không exposed, không proof of equivalence. Inputs chỉ contrasts/summary/coverage cùng báo cáo đã lưu, không reopen raw4cell outcomes/traces; pairing4cells kế thừa từ aggregates/hồ sơ nguồn.

archive_copy_inventory.json ghi SHA trước copy và đối chiếu exact sau copy; manifest ghi source/input và mọi output SHA. Bảy input snapshots giúp truy vết aggregates. Script factorial snapshot vẫn dùng layout repository gốc; bảng source→archived_as trong inventory chỉ rõ mapping, bundle không tự giả làm full standalone runtime. Graph/factorial reports trong bundle là snapshots nguyên bytes, có thể còn đường dẫn local/source lịch sử.

pack_evidence.py là chính mã đóng gói dùng helper record_evidence_run/verify_evidence_bundle hiện có; không sửa framework. Helper tự ghi manifest/README/execution.log và closure hashes. Không sửa bundle sau closure; verify chỉ đọc. *.log cần force-add theo force_add_paths.txt; không sửa .gitattributes để né whitespace ở traceback gốc. Không ghi Git/index/state/tasks trong gói này.
