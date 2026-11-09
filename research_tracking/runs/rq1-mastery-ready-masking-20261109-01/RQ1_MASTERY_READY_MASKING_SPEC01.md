# RQ1 — đặc tả cached mastery→readiness, chưa thực chạy

Ngày09/11/2026. Chỉ chuẩn bị hợp đồng phân tích, không chạy mô hình, đọc oracle, tạo response hoặc suy kết quả mới. Mục tiêu là giải thích bằng phép tính theo source tại sao khác biệt native mastery có thể bị điều kiện readiness che. Không thay nhánh native-M/truth CPU09 chưa hoàn tất.

## Nguồn và quần thể cố định

- `research_tracking/runs/rq1-prediction-mastery-trace-20261109-01/manifest.json`, SHA `a45099f30ab6d4e239275fae6e40cf174b2dcac615fcb55a6e2b9d79f0c35ae3`. Dùng đúng18`native__trace-*.jsonl.gz` đã đóng và `native__worker_run.json` SHA `891a69a3546599782e530d04c3fa29b53fd832f130399404fe159a5fcab2b178`. Lấy node order28 từ worker receipt; SHA/bytes từng gzip từ manifest và trajectory receipts. Mỗi row có `native_state=[theta,pi_task,T,U,M]` cho28concepts trước current update, query/P/full-preview/legacy SHA và3rawrefs.
- `research_tracking/runs/rq1-fixed-controller-candidates-20261109-01/manifest.json`, SHA `cf1861ddc02105af92b64e4356ca2a816c55940e50e82415523092f27999665a`; `event_flags.json` SHA `1cf3ba08a6d5aff1f25d1cdd91f1aefa5fdd9578a3c1c17c7625fe7a0097942b`. Có past visits/recent/chapter, actual-source R/C/B/CID và branch flags. Source `analyze_fixed_controller_candidates02.py` SHA `56630668fbfe7175f3ae3c643f4bffa2a7e53213983778875ae349c1a08cbd8f`, dòng55–103 chứa literal readiness/fallback/selector.
- Historical fixed-stream bundle `rq1-fixed-edge-set-contrast-20261108-01`, manifest SHA `906d1698482b78708cf16ce9453a8ed866e7dc0ef47cf0b8dca81c2d89b7b044`. Giữ query/legacy gzip và domain28/31edges theo source references cũ. Controller dùng full31edges ở cả hai arms, không dùng empty estimator edges làm controller graph. Runner gốc đã phục hồi từ Git e4e6a262…, khác nhánh closed-loop thiếu original runner.

Ghép đúng1.080keys `(seed,profile,event_id)` của20000–20002×PG/PY/PYH×120, hai arms full/empty. Giữ2.160arm rows và30.240paired concept snapshots. Không lấy9chuỗi hoặc các snapshots lặp làm independent learners.

## Phép tính đã định trước

Với mỗi arm/concept tại pre-update snapshot, tính `T=(theta>=1250)`, `U=(pi_task<=.55)`, `M=T AND U`; kiểm cả28stored predicates. Dựng visits chỉ từ toàn bộ logged-query prefix, không dùng preview hoặc y. Đối chiếu stored past visits trước khi tính tiếp.

Tách readiness frontier thành `I(c)=NOT M(c)`, `E(p)=M(p) OR visits(p)>=6`, `A(c)=ALL parent E(p)`, `F(c)=I(c) AND A(c)`. Roots có A=true do tập parent rỗng và phải tách khi thống kê parent conditions. Giữ nguyên hai source fallback all-mastered/minimum-unresolved; không tự thay bằng strict-only controller.

1. Trên toàn30.240paired concept snapshots, giữ8ô `(I_full≠I_empty,A_full≠A_empty,F_full≠F_empty)`, kể cả0. Ô001 phải bằng0 bởi AND. Không gọi F là returned R nếu source đang ở fallback.
2. Trên tất cả parent-opportunities mà parent M khác giữa arms, chia visits≥6 và visits<6. Với visits≥6, hai E phải cùngtrue. Với visits<6, E phải theo M. Giữ thêm child A giống/khác và I/F giống/khác để phân biệt exposure masking, parent khác còn chặn và self-mastered exclusion. Đây là các predicate quan sát cùng snapshot, không phép can thiệp hybrid hoặc attribution nhân quả duy nhất.
3. Đối chiếu với known90M-set events,60R-changed và30M-changed/R-same. Xuất decomposition theo concept/parent và16groups cố định pooled/profiles/seeds/9trajectories, không chỉ chọn nhóm có masking. Không ép các parent-opportunities cộng thành90events hoặc60R events vì một snapshot có thể có nhiều parent/child.

## Admission và outputs tối thiểu

Trước mọi thống kê mới, phải kiểm source/input SHA trước–sau,18gzip CRC/footer đủ120rows mỗi file, không trùng/thiếu key, query/P/full-preview/legacy identities, node order và28M. Tái dựng đủ2.160returned R cùng source branch, rồi kiểm C/B/CID khớp bundle controller. Mismatch thì STOP, không drop row, sửa hidden state hoặc nới tolerance. R legacy chỉ được kiểm membership, không gọi thứ tự frozenset là logged order.

Đề xuất một cached operation stdlib-only whole≤10s, bao gồm cleanup/final checks, không Popen/network/native imports trong analyzer. Giữ bounded gzip/line/row caps theo inputs đã nghiệm thu. Outputs nhỏ gồm summary toàn16groups/allzero cells, flags có keys và predicate reasons, validation SHA/counts. Không tạo một bản sao18gzip hoặc mở CPU09 truth cache.

## Câu kết luận có thể và chưa thể đạt

Có thể định lượng ngoại lệ exposure và các phép AND/self-exclusion che bất đồng mastery trong chính fixed controller đã lưu. Đây là follow-up khác footprint2.041served exposure của closed-loop, không suy số đó sang mẫu này. Không gọi M đúng/sai, score calibrated, hypothetical served action, causal mediation, edge quality hoặc learning benefit. Không CI/p-value/new independent N. Full native-M/truth vẫn cần một operation toàn grid được nghiệm thu riêng.
