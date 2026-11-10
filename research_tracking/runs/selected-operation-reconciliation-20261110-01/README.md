# Đối chiếu hồ sơ thực thi bốn lượt CPU đã nghiệm thu

Ngày10/11/2026,43tests thực đạt, gồm4ca operation mới và39ca hồi quy. Controller được phân biệt bằng exact profile A0/A1 expert/SAKT/GKT. Không chấp nhận một status có tiền tố chung. Kiểm nested/standalone outer-owned-worker, request/worker SHA, mã thoát và Job0, cleanup/khôi phục môi trường, source/input/runtime trước–sau, thời gian, tài nguyên lấy mẫu và toàn bộ bảng kê native.

Lượt04 đã đọc/hash 116native files, tổng222853565bytes, từ bốn run gốc. Đối chiếu lại input trước–sau, không tải tensor, không chạy model và không sao chép checkpoint vào bundle. Result04 giữ đầy đủ refs và số lượng từng run. Reconciliation dùng vector nguồn đã pin trong receipt lịch sử, chưa thay request độc lập của lượt so sánh mô hình tương lai.

## Lỗi được giữ và phạm vi đã sửa

Lượt03 có43tests đạt nhưng actual A0 bị KeyError ở trường đo RAM. Controller A0 cũ chỉ ghi peak_rss_bytes/min_available_ram_bytes và áp trần worker1GiB, khác ba controller mới đo worker/family2GiB. Bản04 kiểm đúng hai schema và các trần nguồn đã quy định, thêm assertion hồi quy trần A0. Giữ rejected source/tests và logs03. Không suy diễn A0 đã đo RSS toàn Job.

## Giới hạn và việc tiếp theo

Các bằng chứng fit gốc không thay đổi. Đây là đối chiếu lịch sử trên corpus engineering, chưa nâng thành Main60 hoặc thêm researchN. Adapter chỉ hỗ trợ bốn controller đã đọc nguồn, các controller A2/A3 và matrix chính cần review riêng. Không tự suy rộng approval.

Chưa pin request nine-file độc lập hoặc kiểm absence của late-failure markers tại thời điểm publication mới. Chưa kết nối đủ9candidate/accumulator/kernel, chưa chọn winner/refit. Claim identity trong rehearsal metadata vẫn lấy từ snapshot đầu vào. Gate source193 vẫn stale sau sửa module, cần refresh sau tích hợp ổn định. Không có Holdout/Modal hoặc thay kết luận khoa học trong hai file báo cáo GVHD.
