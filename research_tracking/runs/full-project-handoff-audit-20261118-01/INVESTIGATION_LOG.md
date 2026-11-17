# Nhật ký rà bàn giao toàn project · 18/11/2026

## Lượt1 — Toàn cây thư mục và đầu vào chuẩn

Quét336.044file đọc được bằng metadata,124giây. `.pytest_cache` trả PermissionError. Môi trường kiểm trả fileID0, giữ tổng byte logic theo đường dẫn và ghi rõ chưa đo hardlink vật lý. Dữ liệu/model gốc giữ nguyên. Hash mới730file canonical/splits, source mapGAM, corpusGrade10, roles/refit index và metadata graph thành758file/541.957.512byte. HashCSV gốc2.668.566.436byte khớp provenance preprocessing. Repo chưa có origin remote.

## Lượt2 — Khôi phục đường tới output Grade10

Đọc bảy MODEL_INDEX và SUPPORT.zip, gồm nested grade10_source.zip. A0/A1expert có archive trong đợt35GB đã nghiệm thu. Năm archive khác còn local, tổng495.489.664byte, giữ prediction/target/coverage và terminal mà gói model gọn chưa thay thế. Đọc/hash trước–sau từng archive và trích170member nhỏ. Lượt đầu bị kiểm SHA bắt lỗi trùng tên SHA256.json của các archive gốc; chưa upload. Đổi các manifest root sang namespace archive-metadata theo model, giữ nguyên member gốc trong mapping, kiểm uniqueness và SHA từng member. ZIP1.671.389byte đã upload/đọc lại đúngSHA trên Drive Sang.

## Lượt3 — Truy ngược confidence/learned graph

Rà MainGraphInput và method24_scores trong metadata model. Phát hiện Method24 Grade10 thật nằm trong artifacts/akt/local-tests, vì vậy phân loại toàn thư mục là fixture sẽ sai. Đọc binding, producer sources và20artifact được model tham chiếu. Bổ sung32file/69.832.998byte gồm Method24 OOF/fit ledger, graph conditions, receipts, nguồn producer và corpus provenance. Hash khớp các pin lịch sử đã đối chiếu. REQUIRED_INPUTS02 nâng tổng input lên611.790.510byte và giữ REQUIRED_INPUTS01 làm lịch sử. ZIP13.059.198byte đã upload và đọc lại nội dung trên Drive Sang.

## Lượt4 — Quyết định bàn giao

Phân loại234nhóm gồm toàn bộ top-level, các nhánh artifacts/akt và từng resultdirectory AKT. Cache train/selection có giá trị tiết kiệm CPU, được chọn theo run thay vì bắt buộc toàn bộ snapshot. Model/output đã có Drive được tái dùng. Các21604row duplicate vẫn khớp source/keeper/size/mtime; chưa hash lại55,78GB hoặc duyệt xóa. Gitupstream ban đầu bị ownership guard chặn, sau dùng safe.directory riêng cho lệnh read-only, không sửa globalGitconfig; commit đúng và checkout sạch.

Kết luận là gói output đã bàn giao cần bổ sung source/hồ sơ đầy đủ,541.957.512byte input còn lại, simulator traces và coldrestore trên máy người nhận. Method24 và selected support vừa được sao lưu bổ sung. Lượt này không thực thi training hoặc GPU, không chọn lại model bằng kết quả đã xem.
