# SAKT: cầu nối dữ liệu nghiên cứu đã kiểm tra

## Mục đích đối với luận văn

SAKT là mô hình so sánh trong đề cương. Trước khi huấn luyện, mô hình phải nhận đúng lịch sử người học, chỉ dùng dữ liệu được phép cho từng giai đoạn và dự báo trước khi thấy đáp án hiện tại. Batch này bổ sung phần chuyển corpus mô phỏng sang dữ liệu SAKT; chưa tạo kết quả so sánh mô hình.

Implementation: `src/knowledge_tracing/sakt/research_data.py`, public initializer `src/knowledge_tracing/sakt/__init__.py`; kiểm thử tại `tests/sakt/test_research_data.py`. Phần dữ liệu tái sử dụng hợp đồng role/phase và encoding chung, không gọi mô hình AKT. View của một phase chỉ giữ các shard được chọn; corpus đầy đủ chỉ đi qua bước kiểm tra ban đầu, không nằm lại trong đối tượng dùng để tối ưu. Nhờ đó TRAIN view không giữ nhãn selection/calibration.

## Bằng chứng thực thi

| Lượt kiểm | Kết quả | Phạm vi thực sự |
|---|---|---|
| Cầu nối dữ liệu | 20 PASS, không fail/error/skip; 3,283 giây trong trần60 giây | Bốn phase, vocabulary từ optimization, lineage refit/freeze, mask, thứ tự/prefix, OOV và cold targets; dữ liệu tự dựng, không mô hình |
| Tương thích public exports | 3 PASS, không fail/error/skip; 6,050 giây trong trần30 giây | Torch CPU thật, 2 mô hình rất nhỏ được khởi tạo, 8 lượt forward; không optimizer hoặc corpus thật |

Cả hai tiến trình đã được xác nhận nằm trong owned Job trước khi chạy, kết thúc với active process0 và đóng handle. Peak RSS quan sát được lần lượt54.734.848B và202.465.280B; đây không phải bảo đảm RAM liên tục hoặc throughput huấn luyện. Không CUDA, Holdout, full CV hay chi Modal.

Bằng chứng gốc nằm trong [bundle có manifest, logs và nguồn đã chạy](../runs/sakt-research-data-engineering-20261108-01/README.md). `copy_inventory.json` kiểm SHA trước/sau copy; `ERRATUM.json` giải thích trường `model_calls=0` bị hardcode sai trong receipt của lượt tương thích và docstring cũ ghi sai phạm vi. Raw receipt giữ nguyên; số thực thi đúng là2 constructors/8 forwards,0 optimizer. Không cộng kiểm kỹ thuật này vào số người học hoặc bằng chứng hiệu quả của RQ.

## Phần còn lại

Chưa có research trainer SAKT hoàn chỉnh theo chuỗi selection → freeze → refit → calibration, checkpoint fitted được nghiệm thu hoặc OnlineSession phục vụ bộ chọn bài. Chính sách cold target vẫn phải khai báo rõ (`query_only` hoặc `unsupported`); không mặc định protocol21 đã chọn một chính sách. Batch này không thay caps của fixture cũ và không biến checkpoint kỹ thuật thành checkpoint nghiên cứu. Bước tiếp theo là nối cầu dữ liệu này vào lifecycle có cùng ranh giới thông tin với các mô hình còn lại, trước mọi lượt huấn luyện chính.
