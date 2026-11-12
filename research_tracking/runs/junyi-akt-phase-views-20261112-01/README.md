# Junyi — ranh giới dữ liệu và cohort trước training

## Đã hoàn thành

Ngày 12/11/2026, nối role80/10/10 đã ghim vào reader, vocabulary và window hiện có. Vocabulary chỉ học từ train của đúng phase. Selection dùng vocabulary80; calibration phải dùng vocabulary90 sau refit. View từ chối learner ngoài role, fold4, role chồng lấn và encoding sai phase.

Cache kỹ thuật giữ đúng thứ tự thời gian, source row, OOV và SHA đầu vào. Không sửa dataset gốc hoặc artifacts BKT. Tests chuyển vào `tests/akt/` để bộ Gate Linux hiện có tự thu thập. `test-relocation.json` giữ đối chiếu trước/sau chuyển.

`tests04.log/xml` xác nhận **52 tests và81 subtests đạt**, gồm hồi quy CUDA config. Hai lần lỗi setup trước giữ nguyên trong `tests01–03`: thiếu quyền thư mục TEMP được giải quyết bằng thư mục test riêng trong repository. Đây là kiểm dữ liệu/cấu hình, chưa thực thi mô hình CUDA.

## Hai cohort và lý do mở rộng

- Cohort30, 24train/3selection/3calibration, tối đa300event/learner. Selection chỉ2/27target có support. Đã dừng trước GPU. `cohort-audit.json` giữ kết quả và nguồn phiên bản đầu trong hai file `*_attempt01.py`.
- Cohort320, 256train/32selection/32calibration, cùng cách chọn IDhash độc lập outcome. Train11.833events,315windows,79batch/epoch; selection1.530events,1.405supported và125OOV. `cohort-audit02.json` cùng `cohort-prepare02.log` giữ số liệu và identity.
- Dữ liệu phái sinh đặt tại `artifacts/akt/junyi-cohorts/`, không commit raw events. Mở rộng cohort nhằm kiểm đầy đủ lifecycle và độ phủ, chưa chọn cấu hình theo điểm mô hình.

## Giới hạn và bước tiếp

Chưa training Junyi, chưa lựa epoch, refit, calibration, đánh giá outer fold hoặc Holdout. Cohort320 phục vụ engineering, không đại diện toàn Junyi. Full nguồn hiện tại cần Gate Linux mới trước lượt CUDA. Lượt một epoch cần lưu model/Adam/RNG/counters, xuất toàn bộ1.530target kể cả OOV, kiểm fresh reload và độ bền checkpoint. Ngân sách mới phải được chấp thuận trước thực thi trả phí.

`manifest.json` ghim nguồn và bằng chứng. Bundle đóng sau nghiệm thu gói này, công việc training lưu bundle kế tiếp.
