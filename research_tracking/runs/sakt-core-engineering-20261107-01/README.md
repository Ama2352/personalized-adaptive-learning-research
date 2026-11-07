# SAKT core: bundle kiểm kỹ thuật CPU — 07/11/2026

Bundle này archive kết quả đã chạy, không thực thi thêm model/tests, optimizer, trainer, realdata, Holdout, Development benchmark, GPU hoặc cloud. Scope là paper-equation SAKT một block, CPU synthetic, 0 optimizer steps. Weights ngẫu nhiên chỉ dùng kiểm phần mềm; status completed không là complete baseline evaluation, research efficacy, hoặc model fitted.

Nguồn chính: arXiv:1907.06837v1 và author repo shalini1194/SAKT commit98510c58e49fc2cd8ae05412d1f3bb1b9b5053a0. Có khác biệt paper/code; implementation theo phương trình bài báo, không claim parity TensorFlow/checkpoint của tác giả. Không vendor/execute code tác giả. Attention trên history không tự là prerequisite graph.

Intermediate trial01 có35pass/25.58s; final trial02 có37pass/3.30s; cả hai0failure/error/skipped. Source/tests snapshot bind final37cases. Hai kiểm order/all-padding-backward được thêm sau trial01; không có snapshot riêng của source35cases. Giữ cả logs/XML nguyên bytes. Report/source snapshots còn có đường dẫn repository gốc; inventory ánh xạ source→archived_as. Bundle không tự giả làm full standalone runtime/kit.

Conventions explicit nhưng pending protocol: head width/capacity, norm/dropout, canonical rank position trong window (khác absolute left-padded TF slots), context/window budget và first-target policy. Cold score query-only hữu hạn/has_history=false chưa được chốt tính metric. API chỉ nhận current item và shifted prior_responses, chưa là SequenceKTModel hoặc simulator adapter. Trainer/epoch selection/refit/export/resume/calibration/domain/checkpoint binding chưa triển khai; không ghép vào AKT training loop hoặc claim apples-to-apples comparison.

Gate15 hiện ghi462pass cho tests/akt và tests/shared_kt; KHÔNG gồm tests/sakt. Kitv12 KHÔNG chứa package/tests SAKT. gate15_evidence_snapshot.json và kit_v12_bundle_manifest_snapshot.json cùng membership check chỉ chứng minh phạm vi packaging hiện hành, không nghiệm thu SAKT trên Colab/Linux/CUDA. Parent đang xử lý GPU evidence riêng; bundle này không mở rộng scope đó.

archive_copy_inventory_before.json được lập trước copy; archive_copy_inventory.json lưu SHA trước/sau và exact_match. Original handoff inventory16files được kiểm lại. manifest.json và record_evidence_run ghi source/input/output SHA; verify_evidence_bundle chạy sau closure chỉ đọc. Không sửa bundle sau đóng; parent cần review/index/map/commit riêng. Force-add chỉ3logs liệt kê trong force_add_paths.txt; không ghi Git/index/state/tasks trong gói này.
