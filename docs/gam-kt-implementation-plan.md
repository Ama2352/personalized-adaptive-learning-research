# Kế hoạch triển khai GAM-KT

Kế hoạch dùng nguyên graph-free Junyi implementation và frozen BKT data protocol. Mọi output đi riêng khỏi BKT/RIVF; không chạy Holdout Test và không commit tự động.

| Hạng mục | Thiết kế/kiểm chứng | Trạng thái |
|---|---|---|
| Provenance và model adapter | Giữ định nghĩa từ notebook cell 11; hash ZIP/notebook/builder/cell; graph và decay tắt | Hoàn tất |
| Parity gốc | So sánh p, theta, memory, uncertainty và state sau update với cell gốc | Hoàn tất |
| ProblemLog mapping | Stream CSV; Development sidecar theo `source_row`; so identity với canonical và kiểm duplicate lineage | Hoàn tất |
| Frozen split | Đọc assignments BKT; xác minh hash, số user/fold; không tạo split mới | Hoàn tất |
| Difficulty | Fit global/exercise difficulty trên bốn fold train, alpha=20; unseen dùng global và gắn cờ | Hoàn tất |
| Online replay | Query theo user/time/source row; state reset giữa user; predict rồi update | Hoàn tất |
| Metrics | Native và supported-only; coverage/fallback; suggested; AUC undefined; common-row với BKT | Hoàn tất |
| Tests/smoke | Mapping, dedup, ordering, assignment, replay semantics, metric, checkpoint, parity | Hoàn tất trước CV |
| Pilot | Fold 0, 2.000 user hash-seeded; throughput/RSS và runtime extrapolation | Hoàn tất; xem `results/wsl_cpp/pilot/pilot.json` |
| 5-fold Development CV | Checkpoint riêng; aggregate mean/sample SD; native, supported-only, subgroup và common-row metrics | Hoàn tất; 5/5 fold |
| Holdout Test | Không thuộc phạm vi; cần yêu cầu/phê duyệt riêng sau review CV | Chưa chạy |

## Cổng trước CV

CV chỉ được bắt đầu khi model parity exact, mapping/lineage không có mismatch, assignment hash đúng, tests pass, pilot cho thấy throughput hữu dụng và dung lượng/RAM đáp ứng. Nếu lỗi non-finite xuất hiện, fold dừng và checkpoint giữ các user hoàn chỉnh trước lỗi.

## Kết quả đã chạy

- Pilot fold 0: 2.000 user, 216.677 interactions, 3.320 interactions/giây, peak RSS 2.820.398.104 byte. Ngoại suy replay-only đã được sửa để tính mỗi Development interaction một lần; thời gian thực full CV là 7.835,8 giây.
- Full CV: 198.084 Development users, 20.706.208 validation interactions, 5/5 fold; peak RSS 3.043.356.672 byte. CV outputs ở `experiments/gam_kt/results/wsl_cpp/cv/`.
- Native metrics bao gồm 194 fallback rows trên 20.706.208 rows; supported-only/common-row metrics loại các row đó. Holdout Test chưa được đánh giá.
