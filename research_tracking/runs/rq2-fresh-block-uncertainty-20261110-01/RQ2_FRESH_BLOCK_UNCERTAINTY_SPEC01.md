# RQ2 · Bất định theo block của fresh120

**PROPOSED. Chờ Root review và chấp nhận đặc tả trước khi tính.** Đây là phân tích thăm dò sau khi các kết quả fresh120 đã được xem. Việc đóng băng thuật toán trước phép tính mới không biến các estimands này thành giả thuyết confirmatory đã đăng ký trước dữ liệu.

## Câu hỏi và population

Phép kiểm đã nghiệm thu có mười block21010–21019, ba mức năng lực nền1000/1150/1300, hai nguồn graph expert/learned và hai mức cơ chế0/0,55. Mỗi block giữ đủ các điều kiện ghép cặp, cùng nguồn residual và uniforms theo thiết kế đã kiểm. Chỉ một learned graph cố định được dùng. Graph môi trường và controller vẫn expert31, S/P bật và L tắt.

Y là tăng latent theta trung bình trên28 khái niệm sau120 bước, đơn vị Elo của simulator. Q(a,λ) là Y_expert trừ Y_learned trong cùng block, mức năng lực và λ. K(a) là Q(a,0,55) trừ Q(a,0). Không thay định nghĩa Y hoặc ghép sai số dự báo trên các lịch sử đã phân kỳ.

Gia đình thăm dò cố định gồm đúng ba estimands, mỗi estimand là trung bình của mười giá trị block.

| ID | Giá trị trong block | Diễn giải hữu hạn |
|---|---|---|
| K1000 | K(1000) | Tương tác đổi nguồn graph với cơ chế ở mức1000 |
| K1150 | K(1150) | Tương tác tương ứng ở mức1150 |
| K1150_minus_K1000 | K(1150) − K(1000) | Tương tác trên khác nhau bao nhiêu giữa hai mức khởi tạo |

Dấu dương của K không có nghĩa mọi người học đều tăng kiến thức hoặc graph chuyên gia tốt hơn trong mọi điều kiện. Chênh lệch giữa hai K là tương tác có điều kiện vào thiết kế simulator và nguồn graph này. Không suy quan hệ năng lực của con người. Không thêm estimand sau khi thấy interval.

K1300 giữ nguyên là đối chứng bất hoạt theo nguồn. Script kiểm đủ mười zero và20 high controls để admission, không tạo CI, p-value hoặc kiểm định cho đối chứng này. Ba block E9 không được đọc hay pooling.

## Thuật toán đã chọn trước phép tính mới

1. Đọc đúng manifest recovery đã đóng và bảy JSON nhỏ được ghim. Kiểm đủ120 outcomes,60 Q,30 K,20 high controls, phép trừ binary64 nguyên nguồn và coupled identities. Không đọc raw trace, current labels, oracle vector, dataset hoặc checkpoint.
2. Sắp block theo21010 đến21019. Vector của mỗi block có ba phần tử đúng thứ tự bảng. Phần tử thứ ba được trừ trong block trước lấy trung bình. Điểm ước lượng dùng `math.fsum` trên mười phần tử chia10. Không round trước bootstrap.
3. Tạo một `random.Random(42)` riêng, thuật toán CPython MT19937. Với mỗi replicate, gọi `randrange(10)` đúng mười lần để lấy mười block có hoàn lại. Dùng cùng mười chỉ số cho cả ba estimands. Có đúng10.000 replicates,100.000 lần randrange. Không redraw, đổi seed hoặc dừng theo dấu kết quả. Caller global RNG phải nguyên trạng.
4. SHA của draw stream được cập nhật bằng mười byte unsigned theo thứ tự chỉ số0–9 trong mỗi replicate, replicate0–9999. Các điều kiện của block đi cùng nhau thông qua vector được tính từ toàn bộ các điều kiện, không lấy mẫu120worlds hoặc14.400response riêng lẻ.
5. Interval là percentile bootstrap hai phía, dùng helper public `linear_percentile` loại7 đã kiểm trong `research_selection.py`. Chỉ tái sử dụng percentile, không gọi system selector hoặc bootstrap2.000 của module đó. Probability hai đầu là1/120 và119/120. Mỗi interval có mức danh nghĩa98,333333%, tương ứng Bonferroni cho gia đình ba estimands với mức đồng thời danh nghĩa95%.

Bonferroni chỉ điều chỉnh xác suất danh nghĩa của từng interval. Với percentile bootstrap trên n=10 và lựa chọn estimands sau khi đã thấy dữ liệu, không được tuyên bố coverage chính xác95% hoặc kiểm soát sai số confirmatory đã chứng minh. Không có p-value hoặc quyết định chấp nhận/bác bỏ giả thuyết trong output.

Bootstrap ở n=10 có phân phối rời rạc từ các tổ hợp block. Tăng số replicates chỉ giảm nhiễu Monte Carlo của phép resample, không tạo thêm block độc lập hoặc khắc phục sample nhỏ. Interval chưa bao gồm variance do train seed, graph học khác, môi trường khác, learner population thật hoặc lựa chọn phương pháp. Các trường hợp âm và zero đều giữ nguyên. Không pooling E9 và không thay thế yêu cầu graph-quality/noise còn thiếu.

## Implementation và ranh giới nghiệm thu

Script `analyze_rq2_fresh_block_uncertainty01.py` SHA `21dce940bf8c3ddd9114eccde5952c5bbcaea86f90b88e462f8fa89d39463938` chỉ dùng stdlib và helper percentile có source pin. Hai CLI bắt buộc là `--expected-source-sha` và `--expected-plan-sha`, do Root bind trước dispatch. Các SHA là khóa kiểm integrity, không tự cấp quyền chạy.

Output mới độc quyền ở `P/rq2-fresh-block-uncertainty01`. Dự kiến có `summary.json`, `bootstrap_means.csv` giữ đủ10.000 vector và `result.json` giữ readback SHA/size, pre/post nguồn, algorithm và ledger. Tối đa1MiB mỗi output. Không ghi lên bundle cũ, không vẽ hình hoặc tự xuất bản báo cáo khoa học.

Nguồn/input tối đa64KiB mỗi file. Tổng workload là10.000 shared draws,300.000 giá trị block được cộng và sáu percentile trên các vector10.000 phần tử. Cap đề xuất toàn operation10giây. Script kiểm cooperative cap7giây gồm đọc/tính/ghi/readback/sourcepost, phần còn lại dành cho startup/cleanup/outer finalization do Root bind. Đây không phải runtime forecast hoặc hard-kill của script. Root cần watchdog thực, terminalRC0, output hashes và sourcepost trước acceptance. Nếu cap không đủ thì giữ failure, không giảm số draws hoặc tự retry.

Trước actual cached operation, Root có thể kiểm manufactured constants và vector tương phản cùng helper type7 để xác nhận cách ghép block/quantile/private RNG. Lượt chuẩn bị này chưa import, chạy fixture hoặc tính thống kê. Cold NumPy/Pandas/Torch và không network/process được kiểm ở main. Không có world/model/response mới. Cấu hình phương pháp chính và required baselines giữ nguyên.

## Inputs đóng băng

Root input nằm trong `research_tracking/runs/rq2-fresh-graph-recovery-20261110-01`. Tiền tố `N` dưới đây là `experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03/` bên trong bundle.

| File | SHA-256 |
|---|---|
| manifest.json | `deff815a7360ab9d0ffcaf06e986ff2fc14ed07aa0ab8366880ade34445df11e` |
| acceptance.json | `56068d889137658244b4595c0289b78da15a995fe84d2a62f97579aca6f0b7b3` |
| N/summary.json | `73538ef1c229dd5b9a17af781fc13bdb810efd58fe1196bd70d8d95d31d74a7d` |
| N/outcomes.json | `35f6603726f21d717e1da8e75ada8369584fcdcbbacbf3d170981e027dd662fa` |
| N/graph_source_contrasts.json | `645b395c81eedea3d42a7ebfb6521e1be0c14aeafa70eb3412468100f22de330` |
| N/conditional_lambda_contrasts.json | `f48f5ec7f6683d8285288a5bffa05e46be2365d244aa83990c6797b43a721a38` |
| N/high_controls.json | `026adf45ff9022cd5928b237e90c371daffff62b6bb287ae881ddf468987668c` |
| N/admission.json | `9693f81685367cc3c12c4a23be757b8b64f56c68098ac3f65cd6994272a36868` |
| src/knowledge_tracing/research_selection.py | `0e3cf12d15626a76000c6cdc04779ac769806aae2a5e52f769d4c70f3580a348` |

Báo cáo nguồn `research_tracking/reports/rq2_fresh_graph_source_replication_20261110.md` SHA `f9860a76c191504adb514e41185929fd74f07a8137f7ec1f60e60b2b6b5d85d2` và thesis E11 đã trình bày thống kê mô tả. Đặc tả này bổ sung cách lượng hóa bất định thăm dò, không sửa những hồ sơ đó. `P` là `artifacts/akt/local-tests/akt-research-runner-20261108-01`.
