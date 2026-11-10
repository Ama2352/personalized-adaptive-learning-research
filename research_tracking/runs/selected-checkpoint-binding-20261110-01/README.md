# Liên kết checkpoint tốt nhất trước so sánh mô hình

Ngày10/11/2026, kiểm local `.venv` thực đạt32tests, gồm8ca checkpoint và24ca hồi quy đọc/quần thể/dòng CSV. Lượt02 đọc/hash lại bốn checkpoint A0, A1 expert, SAKT, GKT đã có. Đối chiếu COMPLETE→metadata→state, epoch tốt nhất, encoding, vocabulary, runtime, train80 và identity đầy đủ. Đọc state bằng streaming hash, không tải tensor hoặc tạo model.

## Kết quả và nguồn

Epoch tốt nhất là A0=4/7epochs, A1 expert=4/7, SAKT=1/6, GKT=6/11. Giữ riêng phase train80 của checkpoint và phase selection của claim. Bảng ánh xạ kiến trúc/nguồn đồ thị được tái dùng từ research_main_stage.CANDIDATE_BINDINGS. Artifact gốc vẫn ở experiments/<model>/results/, không sao chép state.pt vào bundle. Result02 ghi từng byte count, inventory nguồn191file, thời gian thực và kiểm hash trước–sau.

Lượt01 có31tests đạt nhưng bị từ chối khi đọc checkpoint A1 thật do validator so A1_EXPERT với tên kiến trúc A1. Nguồn bị từ chối, logs và pins01 được giữ. Lượt02 sửa theo bảng ánh xạ sẵn có và bổ sung regression kiểm kiến trúc/graph source riêng. Không sửa checkpoint hoặc model để vượt kiểm.

## Giới hạn

Đây là rehearsal lớp checkpoint trong file admission. Expected identity của lượt này được snapshot từ metadata thực trước khi kiểm, chưa là request provenance độc lập hoặc accepted-operation receipt đã review. Kiểm byte/hash không chứng minh tensor, optimizer/RNG hoặc lịch sử thực thi. Những bằng chứng đó nằm tại các bundle nghiệm thu producer trước đây và phải được nối riêng. Fixture schema2 chỉ kiểm logic metadata AKT, chưa chạy CUDA.

Chưa đủ admission chín candidate, chưa chọn mô hình/freeze/refit hoặc có kết quả Main60. Gate183 là lịch sử, source191 cần refresh sau khi hoàn tất adapter. Không có NN, Holdout hoặc chi Modal. Hai file báo cáo GVHD giữ nội dung khoa học hiện hành vì gói này không thay kết luận nghiên cứu.
