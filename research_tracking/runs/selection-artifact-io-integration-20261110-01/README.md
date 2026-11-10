# IO artifact trước so sánh mô hình

Trên Windows hiện tại, fixture đã ghi nhận tuple stat(path) và fstat(handle) có cùng device/inode/size/mtime nhưng khác ctime. Lượt diagnostic giữ chín methods/1error; các rejected checks dự kiến cũng có thể xuất hiện trong log quan sát, không coi mọi tuple là lỗi mới.

Bản02 đối chiếu device/inode/size/mtime giữa hai API, đồng thời giữ kiểm đầy đủ stamp trước–sau trong từng API và toàn bộ SHA. Regression xác nhận ctime khác ổn định giữa API được chấp nhận, còn ctime thay đổi trong cùng API vẫn bị từ chối và đóng handle. Không khẳng định nguyên nhân Python/Windows tổng quát ngoài quan sát này.

Candidate02 đạt10methods/0FES. Canonical normal import cùng integration thật đạt10methods/0FES trong2,260giây/20giây. Tám CSV của A0/A1 expert/SAKT/GKT được stream-index, đọc lại từng dòng và rehash cuối; mỗi mô hình khớp đủ84K/y với expectation độc lập đã kiểm. Không copy CSV, không model, metric comparison, chọn winner, freeze hoặc refit. Đây vẫn là corpus engineering nhỏ.

Lỗi candidate01 và code gốc đã đóng ở main-selection-population-integration-20261110-01. Module mới research_selection_io.py được tích hợp. Build187 cần refresh software Gate sau khi ổn định các adapters; Gate183/1913 giữ làm lịch sử. Không tiêu Modal.
