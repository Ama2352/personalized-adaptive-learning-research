# RQ2 · Bất định thăm dò trên mười block fresh120

Ngày10/11/2026. Phân tích bổ sung dùng kết quả mô phỏng đã nghiệm thu, không chạy thêm world hoặc mô hình. Dữ liệu đã được xem trước khi chọn phần bổ sung này, nên toàn bộ kết luận giữ mức thăm dò sau kết quả.

## Vì sao cần bổ sung bất định

Fresh120 đã cho thấy tương tác giữa đổi nguồn đồ thị và cơ chế thiếu tiên quyết có cả dấu dương lẫn âm giữa các block. Trung bình dương cần được đọc cùng độ phân tán. Phân tích này lượng hóa bất định trong đúng mười block đã có, thay vì xem120world hoặc14.400response là các quan sát độc lập. [Kết quả mô tả và thiết kế nguồn](rq2_fresh_graph_source_replication_20261110.md).

Mỗi block giữ cùng residual khởi tạo và dãy ngẫu nhiên giữa các điều kiện theo thiết kế đã kiểm. Graph của môi trường và controller cùng giữ expert31. Chỉ nguồn graph của estimator thay giữa expert31 và một learned31 cố định, S/P bật và L tắt. Đây chưa là phân tích nhiều graph học độc lập hoặc bằng chứng xếp hạng chất lượng cạnh nói chung.

## Đại lượng và thuật toán

Y là latent theta cuối trừ nền ban đầu, lấy trung bình trên28 khái niệm sau120 bước. Đơn vị là điểm Elo của simulator. Q là Y_expert trừ Y_learned tại cùng block, mức khởi tạo và λ. K là Q khi λ = 0,55 trừ Q khi λ = 0. Dấu của K diễn tả cách chênh lệch expert–learned thay đổi khi bật cơ chế, chưa phải mức tăng kiến thức tuyệt đối.

Gia đình thăm dò có ba trung bình theo block, gồm K1000, K1150 và K1150−K1000 tính trong cùng block. Mỗi replicate lấy lại mười block có hoàn lại, dùng chung các chỉ số block cho mọi đại lượng. Có đúng10.000 replicates, private seed42, percentile loại7. Mỗi khoảng dùng hai quantile1/120 và119/120, tương ứng mức danh nghĩa98,333333% mỗi khoảng sau điều chỉnh Bonferroni cho ba đại lượng. Mức đồng thời95% của cả nhóm chỉ là danh nghĩa xấp xỉ trong bootstrap này. [Đặc tả đã được Root chấp nhận](../runs/rq2-fresh-block-uncertainty-20261110-01/RQ2_FRESH_BLOCK_UNCERTAINTY_SPEC01.md).

## Kết quả giữ đủ ba đại lượng

Các số trong bảng làm tròn chín chữ số thập phân. Output JSON giữ độ chính xác đã tính.

| Đại lượng | Trung bình · Elo | Khoảng bootstrap Bonferroni · Elo | Block dương / âm / zero | Min đến max quan sát · Elo |
|---|---:|---|---|---|
| K1000 | +0,004495941 | −0,024648567 đến +0,035326957 | 6 / 4 / 0 | −0,069250039 đến +0,095294454 |
| K1150 | +0,024529648 | +0,005767224 đến +0,047247863 | 8 / 2 / 0 | −0,004716494 đến +0,079789844 |
| K1150−K1000 trong block | +0,020033707 | −0,021413109 đến +0,058528690 | 6 / 4 / 0 | −0,090307393 đến +0,106333826 |

Khoảng K1000 chứa0. Khoảng K1150 có cận dưới dương trong phép tính thăm dò đã chọn, đồng thời vẫn có hai block mang K âm. Kết quả này có điều kiện vào mười block, một learned graph và world/controller cố định. Không dùng nó để khẳng định ưu thế graph ổn định hoặc ý nghĩa thực tiễn của độ lớn hiệu ứng. [Ba ước lượng và toàn bộ bootstrap đã lưu](../runs/rq2-fresh-block-uncertainty-20261110-01/summary.json).

Để hỏi tương tác có khác giữa hai mức khởi tạo hay không, phải đọc trực tiếp hàng K1150−K1000. Khoảng của hàng này chứa0. Vì vậy, cận dưới dương của riêng K1150 chưa đủ cho kết luận hai mức năng lực khác nhau. Kết quả không xác lập quy luật năng lực của người học thật hoặc các cơ chế trung gian của lộ trình.

K1300 giữ vai trò đối chứng bất hoạt đã được dự kiến từ nguồn. Mười K bằng0 và20 high controls được kiểm khi admission, nhưng không tạo khoảng hoặc kiểm định cho chúng. Chênh lệch Q ở mức1300 vẫn khác0 trong dữ liệu nguồn. Phân tích hiện tại không biến structural zero thành bằng chứng thống kê về năng lực nói chung.

## Kiểm số học độc lập

Một checker riêng chỉ đọc CSV đã lưu và30K nguồn. Nó không import analyzer/kernel, không tạo Random hoặc lấy mẫu lại. Checker dùng Decimal precision60, tính lại ba trung bình, min/max, dấu của block và cả sáu quantile loại7 từ10.000 dòng. Sai khác tuyệt đối lớn nhất với output binary64 là1,13050×10⁻¹⁶, dưới tolerance số học1×10⁻¹² đã đặt trước phép kiểm. Tolerance này không thay population, đầu khoảng hoặc tiêu chí dấu. Quan hệ giữa ba cột bootstrap được đối chiếu trên toàn bộ10.000 dòng, sai khác lớn nhất1,1×10⁻¹⁷. [Proof và phạm vi kiểm độc lập](../runs/rq2-fresh-block-uncertainty-20261110-01/independent_numeric_review.json).

Checker không tái tạo draw stream hoặc chứng minh lại draw SHA bằng một lần bootstrap mới. Source, thuật toán seed, shared draws và fixture đã được Root review ở bước thực thi. Các input và output giữ SHA trước–sau. Root báo đã kiểm manufactured constants/shared contrasts/type7/private RNG, nhưng không có raw fixture receipt riêng được cung cấp cho bundle này. Không tính lời xác nhận đó thành một tổng test mới.

## Giới hạn và phạm vi nghiệm thu

Mười block là sample nhỏ. Phân phối bootstrap rời rạc và percentile có thể chưa ước lượng tốt phần đuôi.10.000 replicates giúp mô tả phép resample, không tăng số block hoặc tạo coverage chính xác. Điều chỉnh Bonferroni chưa khắc phục lựa chọn estimands sau khi đã xem dữ liệu. Không có p-value hoặc quyết định confirmatory trong báo cáo.

Các khoảng chưa bao gồm độ biến thiên từ train seed, graph học khác, môi trường khác hoặc population người học thật. Không gộp ba block E9. Không ghép loss theo số thứ tự sau khi các lịch sử đã phân kỳ. Chưa suy graph-quality ranking, calibration của confidence, hiệu quả mô hình neural hoặc tác động dạy học trên con người. Các câu hỏi về graph noise/quality và main fitted comparisons vẫn còn.

Phép cached được outer nghiệm thu với returncode0 và error null. Worker ghi0,3979453 giây trước final, outer ghi0,5503073 giây, trong watchdog10 giây. Đây là hai phạm vi đo khác nhau, không cộng chúng. Kiểm Decimal ghi0,2464375 giây trước final trong cap5 giây. Không có failure trong operation cached này. Bundle lưu nguồn, đặc tả, review Root, wrapper, raw logs, output và kiểm độc lập, đồng thời tham chiếu bundle fresh120 gốc qua SHA. [Manifest đóng hồ sơ](../runs/rq2-fresh-block-uncertainty-20261110-01/manifest.json).

Nghiệm thu xác nhận phép tính thăm dò và integrity hồ sơ. Không có mô phỏng, model call hoặc mẫu độc lập bổ sung từ phân tích này. Chưa RQ nào được tuyên bố hoàn tất.
