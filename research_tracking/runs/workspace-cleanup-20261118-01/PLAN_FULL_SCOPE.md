# Kế hoạch hoàn tất bàn giao và thu gọn repository

Người dùng18/11 yêu cầu thực hiện đến hoàn tất: Drive đủ bộ bàn giao; lưu riêng tài nguyên lịch sử ngoài bàn giao; local không còn hàng chụcGB output/cache; sắp xếp gọn và commit. Đây là phạm vi mở rộng của đợt dọn, được ghi riêng thay vì sửa protocol nghiên cứu.

## Thiết kế thực hiện

- Hai nơi Drive: KLTN_BAN_GIAO_DAY_DU_20261118 giữ đúng tài nguyên để tiếp tục; KLTN_LUU_TRU_LICH_SU_20261118 là thư mục ngang cấp, giữ lịch sử/audit và các gói lưu lạnh còn lại. Không đặt thư mục lưu lạnh ngoài bàn giao bên trong thư mục bàn giao.
- Local giữ source/config/docs/reports/figures, input/model gọn còn cần, manifest và chỉ mục phục hồi. Output/cache lớn được chuyển lạnh đúng byte, giữ đường dẫn lịch sử trong relocation. Không thay protocol/metric, không chạy training hay dùng Test để chọn cấu hình.
- Giữ dataset/, artifacts/bkt_baseline/, venv/, .venv/ và .wsl/ trong lượt này; các vùng này tổng cộng khoảng vàiGB mỗi nhóm, không là nguồn hàng chụcGB đang xử lý. Chỉ đọc để kiểm kê. Không đưa credentials/private lên Drive.
- Cấu trúc khoa học hiện có src/scripts/tests/docs/research_tracking/experiments/artifacts đã phân vai. Gom bằng chỉ mục và landing README, không tùy tiện chuyển frozen bundles/pipeline chỉ để đổi tên. Các snapshot nặng đã lưu lạnh có index/relocation và cách dựng lại.

## Công việc và tiêu chí

- [ ] Hoàn tất gói dedup hiện hành, kiểm Drive SHA, gỡ allowlist sau nghiệm thu và kiểm805đầu vào/model cùng manifest.
- [ ] Lập inventory phần nặng còn lại của artifacts/akt và experiments/akt, phân loại giữ local/bàn giao/lịch sử/cache vô giá trị; hash từng file trước chuyển. Dùng bản Drive hiện có khi cùng SHA; upload phần chưa có, gói theo vai trò/dung lượng có thể phục hồi.
- [ ] Tách thư mục Drive lịch sử khỏi bàn giao, giữ đủ tài nguyên ready và nguồn RQ, tạo manifest/hướng dẫn bàn giao phiên bản cuối theo vị trí mới. Metadata/size/SHA/ancestry đọc lại tất cả asset; kiểm790đầu vào và15model từ inventory/cold restore đã nghiệm thu, kiểm source cuối có commit.
- [ ] Gỡ local từng file nặng đã nghiệm thu, ghi log/relocation. Gỡ cache xác định được và empty directories của allowlist, giữ lỗi và phần chưa đủ chứng cứ. Đo logical/unique/free-space, không cộng hardlink thành dung lượng đã giải phóng.
- [ ] Cập nhật README, docs/REPOSITORY_MAP.md, chỉ mục báo cáo và hướng dẫn phục hồi. Không sửa manifest/model/prediction lịch sử. Không tạo top-level tương đương reports/results.
- [ ] Chạy smoke/import phù hợp, kiểm link/manifest/SHA và hồi quy công cụ phục hồi đã có; review git diff/secret/large-file. Commit riêng phần dọn/bàn giao, giữ thay đổi notebook có trước và không push. Đưa Git bundle của commit cuối lên Drive, kiểm lại.

## Bằng chứng bắt buộc

Inventory SHA trước/sau, Drive receipts/checksum, relocation theo path, nhật ký gỡ và lỗi, tổng dung lượng còn lại, kiểm imports/restore, commitID và readback bundle cuối. Các failure trước đó giữ trong bundle; không xóa bản chưa đủ backup hoặc thay ACL để ép dọn.
