# Đặc tả phân tích lại bằng chứng đã lưu

Ngày 17/11/2026. Phạm vi là tổng hợp hậu nghiệm phục vụ phần giải thích RQ1–RQ2. Các aggregate, báo cáo và một phần số liệu đã được đọc trước khi lập đặc tả này.

## Câu hỏi cần làm rõ

RQ1 cần phân biệt đồng biến giữa các biến của một snapshot với một chuỗi trung gian nhân quả. Tính lại bảng chéo ready/gợi ý, mastery/gợi ý và served probability/gợi ý từ 1.080 dòng pilot graph package. Đối chiếu số nguyên với joint PMRA và conditional tables đã nghiệm thu. Dựng một SVG bảng chéo để người đọc hiểu vì sao 964/90/60/22 là các số đo riêng.

RQ2 cần nhìn chênh lệch đồ thị khi núm tiên quyết tắt, khi bật và phần chênh lệch bổ sung. Tính lại Q tại hai mức lambda, K trong cùng block và số vị trí đổi câu của mỗi ability/lambda từ các file nhỏ của fresh120. Giữ 10 block 21010–21019, một learned graph cố định và world/controller expert. Tính mô tả, không tạo CI, p-value, bootstrap hoặc giả thuyết xác nhận mới.

## Đầu vào và kiểm

Đọc CSV/JSON đã lưu của transitions và fresh120, xác nhận SHA theo manifest đã có. Đối chiếu đủ khóa, 10 block, 3 ability, 2 lambda, hai graph sources và latent/uniform identity ghép cặp. Q tính lại từ 120 outcome, K từ Q, tổng vị trí khác từ 60 trajectory pairs. Dùng Decimal độc lập để kiểm số học các trung bình binary64, tolerance tuyệt đối 1e-12 theo cùng thang Elo. Kiểm nguồn trước/sau và lưu số file/byte đã đọc.

Không nạp mô hình, dataset Junyi hoặc Holdout, không gọi simulator, RNG, GPU hay cloud. Python dùng `.venv`. Output nhỏ nằm trong bundle này. Báo cáo Markdown mới theo phạm vi được root giao, mục lục và báo cáo GVHD do root/agent báo cáo tích hợp.

## Câu hỏi bổ sung sau khi đọc aggregate

Các tổng số vị trí đổi câu expert/learned ở lambda0 và lambda0,55 bằng nhau tại cả ba mức ability. Tổng bằng nhau chưa chứng minh hai lịch sử giống nhau. Trước khi diễn giải, đối chiếu trực tiếp các tuple query/correct/probability của 60 cặp cùng graph, block và ability giữa hai mức lambda từ observables đã lưu. Dùng parent61complete + child59complete, loại 30 dòng partial F062 ở parent. Giữ hash và ledger khôi phục. Mục đích là phân biệt đổi latent outcome với đổi lịch sử quan sát/hoạt động trong horizon120 đã chạy. Đây là câu hỏi hậu nghiệm mới, vẫn chỉ đọc cached traces tổng hợp của simulator.

## Giới hạn kết luận

Đây là làm rõ và kiểm chéo những phép chạy đã có. Các vị trí thời gian có tương quan. Pilot có9cụm seed–hồ sơ trong3seedfamilies, phụ thuộc giữa hồ sơ cùng family cần được giữ. Fresh120 dùng10pairedseedblocks theo thiết kế gốc. Tỷ lệ mô tả theo snapshot/vị trí không làm tăng số đơn vị độc lập. Sau khi trajectory phân kỳ, cùng số thứ tự không bảo đảm cùng target hoặc lịch sử, vì vậy không tính paired predictive loss giữa các trajectory này. Kết quả chưa khép calibration, fitted modern-model comparison, matched-null Junyi hoặc vòng kín chính của RQ1–RQ3.
