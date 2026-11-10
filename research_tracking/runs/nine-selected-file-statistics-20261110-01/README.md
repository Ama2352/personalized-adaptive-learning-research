# Tích hợp chín bộ file selected-only vào thống kê chung

Ngày10/11/2026,67tests thực đạt gồm8ca file-integration mới và59ca hồi quy. Lượt01 đạt66ca. Sau review thêm kiểm deadline sau result construction và bắt đường dẫn source_inventory đúng canonical, lượt02 đạt67ca. Giữ nguồn/tests01 và cả hai logs, không cộng thành133ca độc lập.

## Đường xử lý đã kiểm

Request ghim SHA→đủ9ID→source refs→metadata ba producer→18CSV index→nhóm9dòng K/y→accumulator→thống kê. Request chỉ cho cached statistics. Tất cả reads có byte/file/row/index/time limits, hash trước–sau và đóng handle. Không giữ body của9bảng trong RAM, không điền xác suất thiếu hoặc thay bootstrap/loss đã chốt.

Fixture độc lập lưu ở artifacts/akt/local-tests/akt-research-runner-20261108-01/nine-selected-files02/manufactured-fixture/. fixture-inventory.json trong bundle ghim từng file gốc; code dựng fixture nằm trong test được copy. State.pt của fixture chỉ là văn bản, không phải model hoặc checkpoint huấn luyện. Bằng chứng này không sử dụng dataset thật hoặc Holdout.

Fixture có4target của3learner, một OOV của A3 expert khiến quần thể chung còn3target với2learner đóng góp và1learner không đóng góp. Có36row checks,72index entries. Kernel frozen2000draws nhận thống kê này và trả A0 khi các loss đều bằng nhau. RNG global nguyên. Đây là kết quả biết trước của fixture, không phải lựa chọn mô hình KLTN.

## Các lỗi được kiểm

Thiếu candidate bị từ chối trước đọc artifact, shared-backbone sai, key khác, cả9bảng cùng nhãn sai, common population rỗng, row budget không đủ, file đổi bytes, scope refit, source bị đổi cuối lượt và deadline vượt ngay sau dựng result. Không trả winner từ kết quả dở dang. Origin/history/phase/encoding và null reasons tiếp tục do các adapter/accumulator đã chốt kiểm.

## Giới hạn

API trả thống kê và inventory đã đọc, giữ operation/freeze/refit=false. MainAdmissionStatistics giữ nguyên cờ NOT_FILE_ADMISSION. Chưa kiểm absence late-failure markers ở publication mới, chưa pin request so sánh độc lập hoặc nghiệm thu đủ9actual Main fits. Không ghi freeze, không nối main refit, không Junyi producer và không chạy model. Bốn run engineering thật đã đối chiếu riêng ở các bundle trước không thay cho9Main conditions.

Source195 làm Gate cũ stale. Cần đóng lớp publication/operation admission và refresh Gate trên source ổn định trước dùng training. Gói này hoàn thiện đường đọc/thống kê phần mềm, không thay kết luận RQ hoặc hai file báo cáo GVHD.
