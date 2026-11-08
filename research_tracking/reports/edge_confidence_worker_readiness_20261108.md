# Worker độ tin cậy cạnh — kiểm kỹ thuật ngày 08/11/2026

Mục tiêu là chuẩn bị cách ước lượng mức hỗ trợ của từng quan hệ từ dữ liệu huấn luyện, để CG-AKT không phải tin mọi cạnh như nhau. Kết quả ở đây chỉ nghiệm thu dây nối và các trường hợp từ chối của worker. Chưa có cạnh được fit hoặc đồ thị học được để báo cáo chất lượng.

## Đã sửa và kiểm

Worker nhận đúng launch manifest tuyệt đối do bộ quản lý tiến trình sở hữu phát hành, nhưng vẫn từ chối đường dẫn bất kỳ. Danh sách nguồn được ghim thêm initializer của gói AKT thực sự bị import, thành 11 Python sources. Không đổi recipe, số fit, solver, partition hay cap của lượt fit dự kiến.

Lượt pure đầu giới hạn 45 giây bị dừng: nhật ký chỉ đủ 7 case hoàn chỉnh, không có JUnit cuối; không gọi toàn suite là PASS. Sau khi xem thời gian setup thực, một allocation phần mềm riêng 150 giây được ghi trước lượt hai; nguồn và 21 case giữ nguyên. Lượt hai thực sự qua 21 case, không failure/error/skip; outer 37,260902643 giây. Đây không phải 28 case độc lập hoặc kết quả nghiên cứu cạnh.

Sau kiểm, source trước/sau khớp; không import NumPy/pandas/sklearn/SciPy/Torch, không tạo tiến trình từ test, môi trường test được khôi phục. Windows owned Job đã thu hồi đúng tiến trình của lượt chạy, còn 0 tiến trình và đóng handles. Fallback thông tin Windows chỉ ở fixture, không là chứng nhận runtime thật.

## Phần chưa nghiệm thu

Chưa import/fit solver thật, chưa đọc corpus trong lượt này, chưa chạy 2.352 fit slots hoặc xuất 272.160 dòng OOF. Chưa chứng minh hoàn tất trong active 110/outer 120 giây hoặc RAM 512 MiB. Allocation 150 giây chỉ dành kiểm phần mềm và không thay cap fit. Cần request/nguồn/runtime/resource được chốt và duyệt đúng lượt trước native fit. Mức hỗ trợ dự kiến là độ ổn định dự báo có điều kiện, không phải xác suất cạnh là thật.

[Nguồn, nhật ký cả lượt thất bại và thành công](../runs/edge-confidence-worker-engineering-20261108-01/README.md). Không có training AKT, Holdout, full CV, GPU hoặc chi Modal.
