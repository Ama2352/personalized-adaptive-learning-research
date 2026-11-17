# Hoàn thiện calibration A2/A3 bằng Colab CPU miễn phí

## Trạng thái nghiệm thu

**Launcher/notebook đã kiểm tổng hợp, full calibration thật trên Colab chưa chạy.** Không tạo App/function/container Modal, không dùng GPU và không tải binary về máy cá nhân trong gói này.

Notebook là `notebooks/akt_colab_response_calibration_cpu.ipynb`. Mở https://colab.research.google.com/ rồi tải notebook này lên, chọn runtime CPU. Người dùng cần thực hiện xác thực Google và Mount Drive Sang trong ô đầu. Hiện phiên agent không có tool Colab thực thi, nên bước này cần người dùng chạy notebook hoặc kết nối lại công cụ có quyền chạy cell.

## Ba ô chạy

1. Xác thực và Mount Drive của Sang. Không đưa credentials/token vào notebook hoặc output.
2. Tải INPUT.zip134.525.060byte đã pin từ Drive vào scratch Colab, kiểm ZIP/plan/member SHA, dựng `.venv` trong project nguồn đã giải nén. Tất cả package cài trong `.venv`, không cài global. Upstream `akt.py` LF được nhúng dưới dạng văn bản mã hóa, SHA khớp source Linux đã nghiệm thu.
3. Tải hai numeric ZIP A2/A3, metadata windowmanifest/admission, kiểm sourceidentity d22, checkpoint/role/encoding/population. Nối numeric với1.621.484target calibration từ15.847người học, audit raw bằng transaction wrapper đã có và fit temperature V1. Sau mỗi stage upload artifact lên Drive, đọc lại SHA phía server. Chạy A2 rồi A3 tuần tự.

Input ZIP chứa nguồn frozen, metadata và bốn export nhưng launcher không nạp weights/Torch. Không có Junyi train, selection, outer hoặc Holdout trong nguồn calibration-only được dùng để nối nhãn. Bộ kiểm frozen tiếp tục xác minh mục đích manifest, partition, target/prefix, coverage và binding.

Phiên bản dependency lấy từ CPU gate đã nghiệm thu, gồm numpy2.5.4, pandas3.0.6, duckdb1.5.6, psutil7.2.2, requests2.34.2, google-auth2.62.1, scikit-learn1.9.1, scipy1.18.1, pyarrow26.0.1. Không cần Torch.

## Nơi lưu và tiếp tục

- Binary trung gian ở scratch Colab dưới đường vật lý tái lập của Volume cũ. `/artifacts` chỉ trỏ một lần tới root đó, giữ guard typedroot của source frozen.
- Raw ZIP/config/COMPLETE và fit temperature/manifest/config/resource/COMPLETE upload trực tiếp từ Colab vào thư mục Drive KLTN đã chốt. Không tải những binary này về ổ D.
- Progress, URI resumable và logs uploader giữ riêng dưới `MyDrive/KLTN_AKT_PRIVATE/calibration-free-cpu-20261117-01`. Notebook kiểm thư mục private là folder MyDrive chưa chia sẻ qua Drive API trước khi lưu URI. Không đưa thư mục này vào gói báo cáo hoặc chia sẻ công khai.
- Nếu mạng ngắt khi upload nhưng scratch còn, giữ state và chạy lại ô cuối. Pending raw/fit có pin SHA từng file. Upload fit được tiếp tục mà không fit lại khi các file đã fit còn nguyên.
- Sau khi raw đã audit và upload đủ, runtime mới có thể tải raw ZIP đã pin từ Drive, kiểm inventory rồi fit V1. Nếu CPU fit bị ngắt giữa thuật toán, chạy lại fitter từ raw. Không có checkpoint giữa các lần tính objective của V1.
- Nếu runtime mất trước khi raw được publish đủ, có thể phải nối/audit raw lại trong tranche mới từ numeric đã lưu. Không chạy lại GPU. Không tuyên bố resume theo từng learner cho tình huống này.

Progress bind toàn request/cache/PredictionBinding/GPUreceipt, nên đổi split, source, checkpoint hoặc budget không âm thầm dùng lại state cũ. Mọi completed publication được đọc lại metadata Drive trước khi bỏ qua công việc đã xong.

## Đã kiểm ở local

`tests07.txt/xml` giữ lượt cuối13ca đạt trong6,35giây sau khi notebook được dựng lại. Chín ca kiểm download Range/SHA, numeric extraction và traversal, pending artifact mutation, Drive readback mutation, path allowlist và source nhúng trong notebook khớp byte với launcher.

Bốn ca còn lại dùng20target tổng hợp,18fitted và2OOV cho A2/A3. Chúng đi qua entrypoint `run_variant`, join/audit thực và fitter V1 thực, metadata assets cùng publisher được thay bằng fixture nhỏ. Kiểm fit-upload bị ngắt rồi tiếp tục không gọi fitter lần nữa, completed state đọc lại publication và thay budget làm state bị từ chối. Đây là kiểm kỹ thuật, không phải kết quả calibration Junyi thật hoặc benchmark độc lập.

Các logs trước được giữ. `tests03` lỗi import khi command thiếu PYTHONPATH, `tests04` phát hiện notebook nhúng source cũ ngay sau một sửa source. Đã sửa môi trường per-process và dựng notebook lại. `tests05/06` đạt. Không cài dependency mới trên máy local.

Máy local đo khoảng3,0GiB RAM khả dụng trong lượt khảo sát. V1 trước đó ước khoảng2,1–2,2GiB cộng reader/metadata, nên launcher này ưu tiên Colab CPU và giữ startup budget4GiB như dự toán kỹ thuật. Chưa đo peakRSS/time full-cohort trên Colab, không trình bày budget đó như điều kiện phương pháp nghiên cứu.

## Đầu ra nghiệm thu thật còn chờ

Mỗi variant cần receipt Drive SHA-verified của raw và fit, đúng1.621.484target,0OOV thực tế, partition và binding khớp A0/A1. Ô cuối in số target, T, raw/calibrated Log Loss và partition để kiểm. Các số này là fit trên calibration, chưa là independent outer evaluation.

Gói backup hai metadata window riêng đã hoàn thành bằng storage API và Drive API, không thuê compute. `../junyi-calibration-real-20261117-01/FREE_CPU_WINDOW_METADATA_DRIVE01.json` giữ IDs/SHA của41.230byte JSON. Lượt đầu backup vướng thiếu trường stat trong uploader plan, đã chuyển sang helper hashes hiện hữu và state02, giữ state cũ.
