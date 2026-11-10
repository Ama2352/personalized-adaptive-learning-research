# Kiểm môi trường Linux cô lập cho AKT — 10/11/2026

## Trạng thái

ĐÃ NGHIỆM THU môi trường Linux cô lập và Gate CPU đầy đủ. Đạt 1.993/1.993 ca, không failure/error/skip/deselection, trên 198 file nguồn và 92 module. Modal sử dụng 0 USD. Các đoạn diễn tiến bên dưới giữ trạng thái tại thời điểm quan sát.

## Mục tiêu và nguồn

Bộ kiểm tích hợp trước đã đạt 1.992 ca nhưng loại riêng một ca kiểm môi trường cô lập. Hồ sơ nguồn nằm ở `research_tracking/runs/akt-colab-integration-20261110-01/`. Lượt này dùng cùng 279 thành viên gói nguồn, inventory Gate 198 file và 92 module. Không thay mô hình, cấu hình nghiên cứu hoặc dữ liệu.

Đích riêng trên Colab là `/content/kltn-isolated-cpu-20261110-01`. Môi trường `.venv` mới không kế thừa thư viện hệ thống. Lock Linux/CUDA gồm 44 wheel đã ghim URL, phiên bản và SHA-256. Việc cài chạy CPU, không cấp GPU.

## Diễn tiến đã quan sát

1. Đã kiểm AST của bộ theo dõi tài nguyên tái sử dụng, nguồn và input ZIP. Xem `static-review.json` và `inputs.json`.
2. Truyền gói theo phần độc lập, kiểm SHA và CRC trước giải nén. Một số yêu cầu notebook không thực thi và gây NameError ở phần nối tiếp. Chưa có cài dependency trong các lượt truyền lỗi đó.
3. Lượt chuẩn bị đầu dừng vì bản upstream vượt cap sao chép 64 MiB. Đo thực tế 93.951.280 byte, rồi tiếp tục cùng thư mục với cap 128 MiB, không xóa nguồn lịch sử. Xem `prepare_remote.py` và `prepare_resume.py`.
4. Đã xác nhận tạo venv rỗng, không kế thừa package. Khởi chạy đúng một lượt cài, PID 34772. Log cuối nhận được đang tải wheel Torch. `monitor-last.json` là quan sát tại thời điểm đó, không phải kết quả hiện tại.
5. Cầu nối hết phiên trước khi thu kết quả cuối. Đã mở cầu nối mới, cần đọc `result.json` và logs ở đúng thư mục cũ trước mọi quyết định tiếp theo.

## Giới hạn thực thi

Cài tối đa 600 giây, riêng pip 500 giây, workspace 20 GiB, disk trống tối thiểu 30 GiB, log 32 MiB. Không tự retry nếu lỗi. Chỉ cài vào venv Colab riêng. Không chuyển Junyi, token hoặc checkpoint lịch sử lên Colab.

`gate_controller.py` đã chuẩn bị cho Gate CPU đầy đủ, chỉ chạy sau khi môi trường đạt 44 package, đúng origins/hash, pip check thành công và package hệ thống không thay đổi. Đây mới là mã chuẩn bị, chưa có kết quả thực thi.

## Điều kiện nghiệm thu tiếp theo

Thu kết quả và log cài về máy, kiểm nguồn/lock/package origins. Sau đó chạy Gate hiện hành không loại ca kiểm môi trường, thu JUnit và log trước khi kết luận. CUDA, recovery, throughput và training nghiên cứu chính là những mốc tiếp theo riêng biệt.

Checkpoint mô hình không phát sinh từ bước cài môi trường này. Các checkpoint engineering trước giữ nguyên vị trí theo run trong `experiments/akt/results/`.

## Tiếp tục trên runtime mới

Probe sau kết nối xác nhận không có thư mục `kltn*` trong `/content`, Python 3.13.18 và không có GPU. Không thu được kết quả cuối của lượt cài đầu. Chỉ những log đã tải về mới được tính là bằng chứng.

Đã chuyển lại cùng 279 thành viên source bằng 32 phần, xác nhận từng phần và SHA/CRC toàn archive. Mã chuẩn bị riêng dùng root `...-02`, không ghi đè lượt đầu. PID 4239 đã chạy tạo venv, clone và kiểm commit upstream thành công, sau đó bắt đầu cài đúng lock 44 wheel. Chưa có kết quả nghiệm thu. Xem `recovery02-inputs.json`, `recovery02-source-manifest.json`, `recovery02_controller.py` và `reconnect-observations.json`.

Sau cài đạt, controller mới chạy Gate đầy đủ. Không tự lặp lại bootstrap, cài hoặc Gate khi chưa đọc kết quả cụ thể. Ưu tiên hiện hành là bằng chứng cốt lõi của bốn biến thể AKT. Các mở rộng demo, simulator và quét cấu hình tạm hoãn.

## Kết quả cuối đã tải về và kiểm độc lập

| Hạng mục | Kết quả |
|---|---|
| Cài môi trường | 44 package đúng phiên bản, URL và wheel SHA, trong 262,587 giây |
| Cô lập | Mọi distribution thuộc venv, package hệ thống trước–sau không đổi |
| Runtime | Python 3.13.18, Torch 2.7.1+cu126, NumPy 2.5.4, CPU |
| Gate đầy đủ | 1.993 đạt, 0 failure/error/skip/deselection, 92 module |
| Nguồn | 198 file Gate, mã mô hình và tests khớp local |
| Thời gian Gate | 219,115 giây theo report production, 222,124 giây theo controller bao ngoài |
| Tài nguyên cài | Peak workspace 8.978.632.704 byte, dưới cap 20 GiB |
| Training chính/CUDA | Chưa chạy |

`verify_received.py` kiểm CRC, SHA từng thành viên, 44 wheel identities, JUnit từng nhóm và 1.993 IDs không trùng, source và con trỏ Gate. Ba notebook trong gói nguồn chỉ xóa outputs/metadata trên bản sao, không sửa notebook gốc. Việc đối chiếu hash tính đúng phép biến đổi này. Lượt đầu của trình kiểm local dùng nhầm tên trường `test_log_file` trong report, bị KeyError; đã sửa sang trường của con trỏ production và kiểm lại thành công. Không sửa report remote.

`remote/` giữ kết quả cài, audit origins, runtime, Gate JSON, log và JUnit. Hai archive đầy đủ giữ tại `experiments/akt/results/colab-isolated-cpu-20261110-01/install-logs.zip` và `final-logs.zip`, đi kèm receipt. `install-verification.json`, `verification.json` và hai inventory archive liên kết bản đã nhận.

Lượt cài đầu vẫn chưa có kết quả cuối. Lượt phục hồi trên runtime mới đã thành công riêng, không được dùng để suy ngược lượt đầu thành công. Không thay con trỏ Gate Windows local bằng bằng chứng Linux. Gate này xác nhận phần mềm CPU; chưa xác nhận CUDA, phục hồi lỗi GPU, tốc độ training, Main fitted artifacts hoặc ưu thế CG-AKT.

## Bước kế tiếp đã thu hẹp theo ưu tiên cốt lõi

1. Dùng T4 miễn phí để kiểm CUDA, training nhỏ, checkpoint/resume và xuất dự báo trên source/recipe đã đóng.
2. Đo thời gian thực để chốt lượt nghiên cứu graph-free, fixed-graph, confidence và confidence+gate trên cùng quần thể, split và khởi tạo.
3. Giữ checkpoint/optimizer/RNG/counters, dự báo có ID/nhãn/thứ tự, cấu hình graph/confidence/gate và log tài nguyên cho từng lượt. Đánh giá kết quả âm bình đẳng.
4. Kết nối so sánh dự báo với lựa chọn bài và kết quả học để trả lời ba RQ. Tạm hoãn các mở rộng demo, simulator và quét cấu hình rộng.

Chưa phát sinh checkpoint mô hình chính từ bước cài/Gate này. Các checkpoint engineering đã có vẫn giữ nguyên theo run tại `experiments/akt/results/`.
