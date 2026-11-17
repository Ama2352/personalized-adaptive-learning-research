# Runner calibration CPU bằng access token Drive ngắn hạn

## Phạm vi đã được người dùng chấp thuận

Chỉ access token và thời điểm hết hạn được chuyển vào own CPU Colab. Refresh token, client secret và client ID giữ trên D. Runner từ chối file token có thêm các trường credential dài hạn. Không dùng Mount Drive hoặc ADC trong VM.

`scripts/akt/colab_calibration_token_runner.py` chạy một variant A2 hoặc A3 theo CLI rõ ràng. Root cấp access token mới trước mỗi variant, có thể cập nhật file qua HTTP nếu lượt chạy kéo dài. `refresh_handler` chỉ đọc file access token mới, không tự làm OAuth bằng secret trong VM. Token phải còn hơn3phút tại lúc đọc để tránh gửi job với token sắp hết hạn.

## Source và inputs

`build_payload.py` trích chính source/config từ notebook CPU đã kiểm, đối chiếu byte source helper với repo trước khi ghi payload. `PAYLOAD.json`109.331byte có SHA `6fa3012a6d2f321d12d4ae42be2c1fb4ee2e832f26f45459cdb2c51e8e652647`. Payload chỉ chứa source văn bản, config, IDs/SHA Drive và upstream source mã hóa, không có credential hoặc binary dataset/model.

Runner kiểm payload SHA, tải INPUT.zip từ Drive vào scratch Colab, kiểm member pins rồi tạo `.venv` trong project nguồn. Chín dependency dùng cùng version của CPU gate đã chốt, pip cache đặt trong project. Bước prepared yêu cầu đúng `.venv`, đúng versions, source identity d22 và không có Torch được import.

Numeric A2/A3, window manifest/admission và calibration-only data được dùng nguyên như pipeline trước. Tái sử dụng `free_cpu_calibration.run_variant`, transactional audit và fitter V1. Không đổi split, graph/confidence, target, OOV hoặc thuật toán calibration.

## Artifact và tiếp tục

Raw và fit tiếp tục dùng uploader cũ, gửi trực tiếp từ Colab sang Drive KLTN và đọc lại SHA. Progress JSON, URI resumable và uploader state nhỏ được snapshot vào folder MyDrive `KLTN_AKT_PRIVATE` phải chưa chia sẻ. Snapshot ZIP có allowlist chỉ progress A2/A3 và `.sessions/*/state.json`, không lấy file access token. Runtime mới có thể lấy snapshot mới nhất, kiểm Drive SHA và phục hồi state.

Hook ghi checkpoint hoạt động ngoài frozen KT, sau khi helper atomic_json đã ghi progress hoặc `.sessions/*/state.json`. Nó chụp cả chuyển stage raw/fit và offset/URI sau từng lượt ghi uploader state. Hàm snapshot dùng HTTP trực tiếp nên không gọi vòng lại hook. File access token phải nằm ngoài state root và ngoài allowlist ZIP. Phép tính V1 giữ source frozen. Khi raw đã publish và verified, có thể tiếp tục fit từ raw Drive. Fit-upload bị ngắt vẫn tiếp tục upload nếu scratch fit còn đúng pin. Nếu runtime mất trước raw checkpoint, phải nối/audit lại từ numeric đã lưu, không cần GPU.

File `STATUS_A2.json` hoặc `STATUS_A3.json` trong `/content/kltn-free-cpu-tools` ghi phase, PID và target count để root đọc qua HTTP. Không có token hoặc proxy URI trong status. Full result có receipt artifacts trên Drive.

Runner xóa file access token ở finally và đăng ký cleanup khi process thoát. Root vẫn cần kiểm file đã mất qua HTTP sau lượt chạy, dọn nếu có lần renew đến muộn hoặc process bị kill cứng. Secret access file phải đặt canonical dưới `/content`; không đưa vào notebook/log hoặc source payload.

## Cách gọi ở Colab

Root tải script, payload và token access-only bằng HTTP proxy riêng. Gọi script qua Python trong Colab, truyền `--payload`, `--payload-sha256`, `--token-file` và `--variant A2` hoặc `A3`. Runner tự bootstrap rồi gọi subprocess trong project `.venv`. `--prepared` chỉ dành cho subprocess đã dựng đúng runtime.

Token JSON có đúng hai key `access_token` và `expiry`, expiry dạng RFC3339 UTC. Không truyền token trên command line. Không chạy runner trên Windows vì binary inputs chỉ được tạo ở scratch Colab.

## Kiểm kỹ thuật và giới hạn

9kiểm thử offline đạt tại `tests05.txt/xml`, gồm renewal bằng file access-only, từ chối credential dài hạn, token hết hạn, folder state bị chia sẻ, snapshot roundtrip, loại access file, path traversal và offset-state trigger. `../colab-cli-cpu-session-20261117-01/tests10.txt/xml` còn kiểm kết hợp20ca CLI/runner. Tests không gọi Drive hoặc tạo compute thật.

Pipeline `run_variant` đã có kiểm tổng hợp riêng A2/A3 với20target/18fitted/2OOV cùng retry fit-upload không refit. Runner token-only này chưa được chạy full-cohort trên Colab. Root cần nghiệm thu dependency/source, token cleanup, snapshot Drive và số1.621.484target/0OOV trước khi đánh dấu calibration thật hoàn tất. Không coi các tests này là kết quả RQ hoặc independent outer evaluation.
