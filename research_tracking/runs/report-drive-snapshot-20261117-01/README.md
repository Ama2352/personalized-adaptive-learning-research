# Snapshot báo cáo và bằng chứng nghiên cứu trên Drive

Ngày 17/11/2026. Gói lưu báo cáo và nguồn nghiên cứu nhỏ, tách khỏi thư mục dự báo số/model. Không dùng Modal compute, không tải model/checkpoint, không tạo ZIP trên ổ đĩa local.

## Vị trí đã nghiệm thu

- [Thư mục báo cáo trên Drive Sang](https://drive.google.com/drive/folders/12cPMtllz-A_Qck_RntemvALISvdT5cWF).
- [Báo cáo HTML tự chứa](https://drive.google.com/file/d/1Ds7wxdNwfO52-EjHYWL8dWMh_rkePIRg/view?usp=drivesdk).
- [Báo cáo Markdown](https://drive.google.com/file/d/1oGiq6gIOHSUtytiUHnoIrafg8vTw1Ai7/view?usp=drivesdk).
- [ZIP bằng chứng và bản báo cáo](https://drive.google.com/file/d/1YzJTvIeo0oVu0r_KStHv8Gpo62jmAMPb/view?usp=drivesdk).

Thư mục con `research-reports-20261117` nằm trong thư mục gốc người dùng đã cung cấp. API đã kiểm đúng tài khoản Sang, thư mục cha và quyền thêm file. Giữ nguyên quyền chia sẻ hiện có.

## Nội dung và kiểm

39 file nguồn, tổng 736.732 byte, được đóng ZIP trong RAM thành 403.797 byte. Các nhóm gồm hai báo cáo hiện hành, tái lập thống kê Paper2 v2, proof retention native, bản thảo kết quả/thảo luận cùng hồ sơ kiểm, bảng đếm mốc công khai, các tài liệu/figure được liên kết trực tiếp và đề cương PDF. `INVENTORY.json` ghi SHA-256 từng file, đường dẫn gốc và các liên kết local đã phân giải. Mục `SNAPSHOT_INVENTORY.json` trong ZIP giữ cùng inventory.

Hai báo cáo được upload riêng với MIME phù hợp. ZIP dùng transport stream resumable hiện có. Sau upload, cả ba file được đọc lại metadata bằng GET riêng và toàn bộ nội dung qua media stream vào bộ nhớ để kiểm số byte/SHA độc lập. `DRIVE_READBACK.json` ghi cả ba nghiệm thu. File HTML giữ nguyên SVG/PDF nhúng đã được QA07 kiểm.

`QA.json` đối chiếu receipt với kế hoạch, inventory và file nguồn hiện có. Không có credentials, dataset hoặc model binary trong allowlist. State chứa URI resumable giữ riêng ở vùng private, nằm ngoài bundle và ZIP.

## Giới hạn và lịch sử thao tác

Lượt prepare đầu từ chối đuôi `.log` trong gói thống kê. Sau khi xác nhận đó là worker log thống kê cục bộ, allowlist được bổ sung đúng loại log này. Lượt prepare và upload tiếp theo đạt giới hạn 5 MiB. Đây là snapshot một lần; ZIP có timestamp ở entry inventory, nên dựng gói mới ở thời điểm khác có thể thay SHA archive dù các member nguồn giữ nguyên. Receipt đã nghiệm thu gắn đúng SHA của ZIP thực tế trên Drive. Khi tạo snapshot báo cáo mới cần dùng phiên/tên mới và kiểm lại, giữ nguyên snapshot hiện tại.

Gói chỉ bao gồm nguồn đã liệt kê, phục vụ đọc báo cáo và truy vết thành quả mới. Các thí nghiệm, checkpoint và corpus đầy đủ tiếp tục theo chỉ mục artifact hiện hành. Snapshot không tăng số mẫu hoặc xác nhận thêm kết luận RQ.
