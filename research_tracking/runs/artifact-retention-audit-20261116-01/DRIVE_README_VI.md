# Sao lưu model và hồ sơ KLTN ngày 16/11/2026

Đợt này gồm sáu ZIP gốc, tổng **471.339.551 byte**, khoảng **471,34 MB**. Các gói 04–06 dùng trực tiếp. Các gói 01–03 được lưu thành bảy phần do giới hạn truyền file 100 MiB, cần ghép trước khi mở ZIP.

| ZIP gốc | Dung lượng MB | Nội dung | Cách lưu trên Drive |
| --- | ---: | --- | --- |
| `01_JUNYI_REFIT_A0_A3.zip` | 108,43 | Bốn model Junyi A0–A3 refit, phục vụ hiệu chỉnh và đánh giá tiếp theo | 2 phần |
| `02_JUNYI_SELECTED_A0_A3.zip` | 113,12 | Bốn model Junyi A0–A3 selected-fit và hồ sơ chọn epoch | 2 phần |
| `03_GRADE10_SELECTED_AND_LEGACY.zip` | 202,34 | Bảy checkpoint Grade10 đã chọn và một A0 Junyi lịch sử | 3 phần |
| `04_CORE_TRAINING_AUDIT.zip` | 6,67 | Log, cấu hình, nghiệm thu, figure và báo cáo training chính | ZIP trực tiếp |
| `05_RETENTION_CATALOGS.zip` | 12,23 | Danh mục kiểm kê, phân loại và tham chiếu bản giữ | ZIP trực tiếp |
| `06_AUDIT_RETENTION_REVIEW.zip` | 28,54 | Checkpoint A3 epoch 4/bước 584 cần giữ audit, metadata và danh mục rà lại | ZIP trực tiếp |

Dung lượng trong bảng dùng MB thập phân, mỗi MB bằng 1.000.000 byte. Tổng trên tính nội dung sáu ZIP gốc, các file hướng dẫn và manifest được lưu kèm.

## Tải và phục hồi các gói 01–03

1. Tải đủ bảy file dưới đây, cùng `DRIVE_PARTS_MANIFEST.json` và `restore_drive_zips.py`, vào **cùng một thư mục local**. Giữ nguyên tên từng file.

   ```text
   01_JUNYI_REFIT_A0_A3.zip.part01
   01_JUNYI_REFIT_A0_A3.zip.part02
   02_JUNYI_SELECTED_A0_A3.zip.part01
   02_JUNYI_SELECTED_A0_A3.zip.part02
   03_GRADE10_SELECTED_AND_LEGACY.zip.part01
   03_GRADE10_SELECTED_AND_LEGACY.zip.part02
   03_GRADE10_SELECTED_AND_LEGACY.zip.part03
   ```

2. Mở PowerShell tại thư mục repository KLTN có `.venv`. Thay `<THU_MUC_DA_TAI>` bằng đường dẫn thư mục vừa tải, rồi chạy lệnh sau.

   ```powershell
   & ".\.venv\Scripts\python.exe" "<THU_MUC_DA_TAI>\restore_drive_zips.py"
   ```

3. Helper kiểm kích thước và SHA-256 từng phần, ghép theo thứ tự manifest, rồi kiểm kích thước và SHA-256 toàn ZIP trước khi xuất ba ZIP gốc vào thư mục tải. Có thể mở và giải nén sau thông báo ghép đúng SHA. Helper giữ nguyên các phần đã tải.

Nếu ZIP đích đã tồn tại nhưng khác pin, helper dừng và giữ nguyên file đó. Nếu ZIP đã đúng pin, helper bỏ qua gói đã có. File `.rebuilding` được giữ khi phục hồi gặp lỗi để kiểm tra nguyên nhân.

## Phạm vi đã kiểm và dung lượng local

Đã đọc lại đủ mười file dữ liệu trên Drive gồm ba ZIP trực tiếp và bảy phần của ba ZIP lớn. Dung lượng và SHA-256 của từng file khớp bản nguồn đã kiểm. Manifest chia phần cùng helper được lưu kèm để phục hồi ba ZIP lớn.

Đã kiểm đọc nối bảy phần local theo đúng thứ tự và đối chiếu SHA-256 khớp ba ZIP gốc. Helper đạt **12 ca kiểm tổng hợp nhỏ trên Windows**, gồm ghép đúng, phần hỏng, sai thứ tự, bảo toàn file đích và kiểm tên đường dẫn. Linux còn chưa được kiểm. Bộ kiểm tổng hợp dùng fixture nhỏ, việc phục hồi ba ZIP nghiên cứu bằng helper còn chưa được thực hiện.

Danh mục lịch sử có khoảng **55,78 GB file trùng ứng viên thu gọn**, kèm điều kiện giữ nội dung và lineage. Phạm vi sao lưu đợt này là model cùng hồ sơ cốt lõi, còn các snapshot lịch sử khác cần xử lý tiếp. Upload đợt này giữ nguyên file local, dung lượng giải phóng từ upload là **0 byte**.
