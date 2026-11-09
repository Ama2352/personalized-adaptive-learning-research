# Trạng thái phép kiểm RQ2 trên các trạng thái khởi đầu mới

## Vì sao cần phép kiểm này

Thí nghiệm đã nghiệm thu trước đó dùng lại ba khối seed và phải tái dựng một phần trạng thái khởi đầu từ nguồn. Kết quả cho thấy thay đồ thị có thể đổi lộ trình qua đường ước lượng và chọn bài, kể cả khi cơ chế phạt thiếu tiên quyết đang bất hoạt. Để kiểm độ ổn định của phát hiện này, nhóm thiết kế thêm phép đối chứng với mười khối seed mới, lưu trực tiếp trạng thái ban đầu và dãy số ngẫu nhiên dùng chung. [Kết quả đã nghiệm thu](rq2_learned_graph_source_ability_results_20261109.md).

Thiết kế mới có 120 ca, kết hợp hai nguồn đồ thị, hai mức tác động của cơ chế tiên quyết và ba mức năng lực. Đồ thị của môi trường và bộ điều khiển được giữ cố định. Mỗi ca dự kiến có 120 tương tác. Thiết kế và giới hạn tài nguyên được lưu trước khi chạy. [Hồ sơ thiết kế và lượt chạy](../runs/rq2-fresh-graph-source-attempt02-20261109-01/README.md).

## Đã thực hiện đến đâu

Lượt chạy nguồn02 dừng sau khoảng 56 giây khi RAM trống của hệ thống giảm dưới ngưỡng 1,5 GiB. Bộ giám sát đã kết thúc lượt chạy và xác nhận các tiến trình thuộc lượt này đều đã đóng. Đỉnh RAM đo được của nhóm tiến trình khoảng 119 MiB, nên nguyên nhân dừng được ghi nhận là RAM trống hệ thống giảm. [Log kết thúc](../runs/rq2-fresh-graph-source-attempt02-20261109-01/outer_final.json).

Đã đối chiếu trực tiếp các file gốc và xác nhận những phần sau.

- 61 ca có đủ 120 tương tác, trạng thái cuối và bản ghi hoàn tất.
- Ca F062 có 30 tương tác, chưa có trạng thái cuối hoặc bản ghi hoàn tất.
- Tổng cộng có 7.350 tương tác và 7.350 lượt cập nhật trạng thái mô hình trực tuyến được ghi nhận.
- Mười bộ trạng thái khởi đầu và dãy ngẫu nhiên đã được sinh và lưu. Toàn bộ 72 file đầu ra giữ nguyên nội dung sau khi đối chiếu.
- Nguồn và đầu vào được ghim trước, sau và tại thời điểm kiểm đều khớp. [Kết quả đối chiếu độc lập](../runs/rq2-fresh-graph-source-attempt02-20261109-01/prefix_verification.json).

Phần chạy được chứa đủ 20 cặp đối chứng năng lực cao đã định trước. Nhật ký của hai mức cơ chế tiên quyết khớp nhau trong cả 20 cặp, phù hợp với điều kiện cơ chế đó bất hoạt. Phạm vi này dùng để kiểm cơ chế của phần dữ liệu đã có. Toàn bộ phép so sánh 120 ca, 60 chênh lệch nguồn đồ thị và 30 tương phản điều kiện vẫn chưa được nghiệm thu. [Hồ sơ đối chứng](../runs/rq2-fresh-graph-source-attempt02-20261109-01/prefix_verification.json).

## Bước tiếp theo và điều kiện nghiệm thu

Giữ nguyên 61 ca hoàn tất cùng toàn bộ file của lượt dừng. Phương án tiếp nối đang được review để dùng lại các trạng thái và dãy ngẫu nhiên đã lưu, chạy lại riêng F062 từ đầu và đối chiếu chính xác 30 tương tác cũ trước khi sử dụng phần tiếp theo. Chi phí chạy lặp phải được cộng riêng vào tổng công việc thực tế. Phương án trong bundle là snapshot đề xuất ban đầu, chưa được triển khai hoặc chạy. Mọi điều chỉnh giới hạn phải có bản review nối tiếp, giữ nguyên lịch sử đề xuất. [Đề xuất ban đầu](../runs/rq2-fresh-graph-source-attempt02-20261109-01/continuation_proposal.md).

Chỉ cập nhật kết luận nghiên cứu sau khi có đủ quần thể đã định trước, ghép đúng nguồn gốc dữ liệu, đối chiếu các cặp và nghiệm thu log tài nguyên. Phần đã chạy được giữ để phục hồi và kiểm tra, chưa dùng để lựa chọn một tập con thuận lợi cho kết luận.

## Lưu trữ và giới hạn

Bundle bằng chứng giữ 39 đầu ra nhỏ, gồm thiết kế, mã nguồn các phiên bản, log, kết quả kiểm và trạng thái ngẫu nhiên dùng chung. Nhật ký tương tác lớn cùng các trạng thái khởi đầu tiếp tục nằm trong `experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02/`. Chỉ mục nguồn ghi vị trí, dung lượng và SHA-256 của chúng. Bản kiểm độc lập đầu tiên có lỗi đếm số trường metadata, lỗi cùng bản sửa đều được lưu. [Chỉ mục nguồn và dữ liệu](../runs/rq2-fresh-graph-source-attempt02-20261109-01/reference_sources.json).

Bộ đo mới lấy các thành viên của Windows Job do lượt chạy sở hữu. Probe riêng đã xác nhận mỗi lần lấy mẫu có một tiến trình thuộc Job nằm ngoài cây con của worker. Vì vậy số đo worker và cây con trong hồ sơ cũ cần được đọc đúng phạm vi. Kết quả số học đã nghiệm thu trước đó được bảo toàn. [Bằng chứng kiểm bộ đo](../runs/owned-job-family-query-engineering-20261109-01/README.md).
