# Nối đối chiếu A0 vào entrypoint Junyi

Ngày 13/11/2026. Đợt này nối hợp đồng đã kiểm ở `../junyi-comparison-preflight-20261113-01/` vào luồng selected thực của AKT và kiểm độc lập từng target selection. Đây là bằng chứng kỹ thuật, chưa có fit Junyi A1–A3 mới.

## Thay đổi đã hoàn tất

`src/knowledge_tracing/akt/research_junyi_selection.py` yêu cầu tham chiếu A0 có external SHA khi chạy graph với purpose main_selected. SHA tham chiếu được gắn vào prepared_inputs của grant, run identity, checkpoint identity và terminal. Main có tham chiếu còn đọc lại cache và kiểm toàn vẹn qua load_full_selected_cache trước model construction.

Sau khi đo khởi tạo backbone, producer tạo descriptor từ config/profile và hash các file thật, so với tham chiếu trước khi tạo optimizer. Kiểm tra gồm roles, encoding/receipt, cache manifest, target counts, cửa sổ, batch, optimizer, early stopping và cờ số học. Mỗi validation phải khớp selection population digest của A0. Sai population sẽ giữ checkpoint trước validation và dừng trước xuất checkpoint selected của epoch đó. Đổi tham chiếu khi resume bị chặn bởi run identity.

A0 entrypoint cũ tiếp tục nhận các lời gọi hiện có. CLI A0 có thêm cặp comparison-reference và comparison-reference-sha256. Engineering graph nhỏ vẫn dùng grant bounded riêng. Trần VRAM được xem là tài nguyên của thiết bị, có thể khác T4/H100, còn FP32, deterministic flags, TF32 và công thức đào tạo phải khớp. Thay đổi này khắc phục việc hợp đồng cũ coi trần VRAM như thành phần số học.

## Kết quả kiểm

`tests04.log/xml` ghi 77 ca đạt trong 11,46giây. Các ca mới đi qua producer thật với native Linear/Adam/checkpoint CPU và mock vòng train/evaluate theo harness có sẵn. Kiểm reference thiếu/sai pin, recheck cache main trước model, mismatch config/data/init trước optimizer, target mismatch sau validation, checkpoint/terminal binding và đổi reference khi resume. Đây là kiểm orchestration CPU, chưa CUDA source mới hoặc full training.

Giữ tests01 với lỗi Windows từ chối tạo hardlink checkpoint sau19ca đạt. Các lượt02–04 được chạy với quyền tạo hardlink trong thư mục test D. Không sửa thuật toán checkpoint để né lỗi quyền.

`selection-population.json` ghi lượt SQL độc lập trên toàn bộ selection10 của cache đã ghim. Đã kiểm1.600.343target/15.847learner/0OOV, cùng đúng digest A0 H100. Khóa đối chiếu gồm source_row, user_id, exercise, time_done, correct, suggested, fold và thứ tự user/time/source_row. Truy vấn dùng CPU1thread, memory256MB, timer90giây và spill trong artifacts/akt/tmp. Đã kiểm hash hai file cache trước và sau. Thời gian đo12,17giây. Không fit model, không mở calibration hoặc Holdout rows.

## Công việc tiếp theo

1. Confidence Junyi cần adapter riêng cho717exercise và native-window history. edge_confidence.py hiện ràng buộc PreparedEdgeConfidence cho tối đa28concept,48learner,10.080events. Không đổi caps mô phỏng để gọi đó là triển khai Junyi.
2. Giữ định nghĩa confidence là conditional predictive stability từ learner-disjoint crossfit trên train80, điều kiện unsupported phải giữ reason và operational weight0. Reuse solver/scoring Method24 khi semantics khớp, ghi riêng cách chia fold có thể mở rộng và định dạng dữ liệu Junyi.
3. label_free_fold_assignments của Method24 băm cả danh sách learner trong mỗi khóa rank. Suy luận từ source cho thấy chi phí hash tăng bậc hai theo số learner. Đây là giới hạn quy mô source, chưa có benchmark full Junyi. Adapter cần fingerprint tập learner một lần và thuật toán chia fold có phiên bản riêng.
4. Không giữ717bộ đếm cho từng hàng của13,35triệu target. Chuẩn bị theo native window và các parent cần dùng, spool theo child để giới hạn RAM, giữ đúng target masks và predict-before-update.
5. A2/A3 Junyi cần artifact confidence thật, context/adapter/producer cùng kiểm T4. Source mới của gói admission cũng cần được đóng gói và kiểm Linux phù hợp trước main GPU.
6. Dự toán phải bao gồm expert/learned, fit/refit/calibration và inference theo protocol hiện hành. Budget còn lại lấy từ ledger đã đối soát, các quy tắc giảm epoch/bỏ refit được đề xuất trong hội thoại chưa được áp dụng.

Mọi checkpoint và kết quả H100 trước giữ nguyên. Gói này dùng CPU local, chi Modal tăng0. Trạng thái sau gói là MAIN_A1_COMPARISON_GUARD_IMPLEMENTED_CPU_VERIFIED / CONFIDENCE_JUNYI_PENDING.
