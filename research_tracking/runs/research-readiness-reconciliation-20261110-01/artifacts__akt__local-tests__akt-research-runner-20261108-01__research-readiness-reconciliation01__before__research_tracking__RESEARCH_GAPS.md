# Khoảng trống và rủi ro nghiên cứu

Ưu tiên theo ảnh hưởng đến việc trả lời RQ, không theo độ khó triển khai.

| ID | Ưu tiên | Gap | Tác động | Evidence | Bước được khuyến nghị |
|---|---|---|---|---|---|
| GAP-01 | P0 | Không có graph-on/off hoặc graph quality experiment | RQ1/RQ2/RQ3 chưa có evidence trực tiếp. | Chỉ BKT/GAM graph-free; Junyi candidate prerequisite metadata. | Chốt graph provenance/semantics, variants/noise/coverage/confidence và paired protocol. |
| GAP-02 | P0 | AKT Development benchmark chưa hoàn tất; pilot failed | Thiếu attention baseline tương đương cho RQ3. | Gate2/smoke pass; pilot14-02 failed trước validation/export. | Điều tra progress replace; run mới cần ID/config/auth riêng và output hoàn chỉnh. |
| GAP-03 | P0 | Không tìm thấy Grade 10 simulator/prior graph artifact | Không xác minh closed-loop outcomes hoặc prior results. | Junyi data và RIVF source tree; không thấy simulator runs/config. | Xác nhận vị trí/nguồn/quyền; ghi fingerprint/provenance. |
| GAP-04 | P1 | Thiếu mastery threshold, decision và policy analyses | RQ1 mechanism chưa tách prediction→decision→policy. | Chỉ predictive metrics. | Đăng ký threshold từ Development, sensitivity, decision flips, policy outcome. |
| GAP-05 | P1 | Graph edges/KC mapping/ground truth chưa xác thực | Không rõ structural prior semantic validity. | Catalog prerequisites; chưa thấy explicit KC mapping/gold validation. | Chốt node/edge meaning, annotation source, confidence. |
| GAP-06 | P1 | AKT persistence error và partial output | Không thể dùng partial training làm run result. | PermissionError, 32 batches, 7,346 targets, epoch incomplete. | Remediation trong run mới; giữ cũ; không tuyên bố metrics. |
| GAP-07 | P1 | Không có nhiều seeds/refits; bootstrap scope hẹp | Fold SD/learner CI không bao quát training variability. | Một frozen fit/fold; 1,000 learner draws. | Chọn paired design/seeds và inference unit theo estimand; xác định Holm family. |
| GAP-08 | P1 | Thiếu cold-start/history/profile strata | Không kiểm tra điều kiện hiệu quả learner. | Overall/subgroup suggested không phải learner profile analysis. | Đăng ký history/proficiency strata trước khi xem kết quả. |
| GAP-09 | P2 | BKT final có 11/720 fits chạm maxiter | Một phần fit không đạt tolerance. | Final report/json ghi 11 maxiter, không non-finite. | Giữ record lịch sử; sensitivity chỉ theo protocol được duyệt. |
| GAP-10 | P2 | Thiếu paired AUC CI và multiplicity plan trong BKT–GAM | Inference không đồng đều trên metric family. | Bootstrap JSON chỉ LL/Brier/ECE/Accuracy. | Không claim AUC significance; preregister correction cho analysis mới. |
| GAP-11 | P2 | Data/output local-only; global ignore inaccessible | Portability và discovery độc lập hạn chế. | Dataset/BKT/GAM/AKT outputs ignored; permission denied global exclude. | Duy trì safe manifest/fingerprint và reproduction notes, không phát tán raw data. |
| GAP-12 | P2 | Proposal/advisor decisions không có trong repo | Sprint/RQ mapping dựa trên user spec, chưa xác nhận thesis text. | _context không có registered proposal. | Tham chiếu proposal được phép; không tự tạo wording lịch sử. |
