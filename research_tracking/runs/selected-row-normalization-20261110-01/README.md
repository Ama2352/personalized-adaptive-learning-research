# Chuẩn hóa đầu ra selected-only trước so sánh mô hình

## Đã kiểm

Ngày10/11/2026, `.venv` local chạy24tests thực đạt, gồm8ca mới và16ca hồi quy IO/quần thể. Kiểm trường khai báo, khóa đầy đủ, nhãn, phase, encoding, geometry AKT, lý do không dự đoán của SAKT/GKT và xác suất hữu hạn. Fixtures bao phủ cả chín ID, null/OOV, cold-unsupported và unsupported-history. Không điền xác suất thay cho null.

Bốn khai báo JSON và336dòng từ A0, A1 expert, SAKT, GKT trên corpus engineering đã được đọc qua bộ IO bounded. Mỗi mô hình có84dòng, khớp K/y với expectation độc lập đã kiểm trước đó, giữ nguyên xác suất binary64 và nguồn trước–sau. `result.json` giữ thời gian thực, inventory nguồn189file và SHA input/output. `stderr.log` có24tên tests và kết quả thực.

## Nguồn và giới hạn

Exports gốc nằm tại các run riêng trong `experiments/akt/results/`, `experiments/sakt/results/`, `experiments/gkt/results/`, đường dẫn cụ thể trong result. Không sao chép checkpoint hoặc sửa artifacts gốc. Expectation đến từ bundle `main-selection-population-integration-20261110-01`, bộ IO từ `selection-artifact-io-integration-20261110-01`.

Đây là nghiệm thu phần mềm với corpus engineering, chưa là kết quả Main60 hoặc chứng minh hiệu quả RQ3. Giải mã claim chỉ kiểm khai báo, chưa xác minh toàn bộ metadata/operation receipts, admission đủ chín mô hình, chọn winner hoặc cấp quyền refit. Gate183 giữ làm lịch sử, source189 cần refresh Gate sau khi hoàn tất các adapters. Không chạy model, truy cập Holdout hoặc dùng Modal. Lệnh launcher thử qua cmd bị lỗi quoting trước khi chạy Python, đã chuyển sang launcher file có timeout30giây, không có NN hoặc file đầu ra từ lệnh lỗi.
