# Tra cứu thành quả, mã nguồn và bằng chứng

Các link dưới đây tính theo checkout repository. `tai_lieu/` chứa bản đọc kèm; run gốc giữ log và nguồn đóng băng. Không đổi nội dung run đã đóng để làm đẹp báo cáo.

| ID | Đã thực hiện / đã xử lý | File kết quả trong gói | Nguồn và quá trình thực hiện gốc | Chưa xử lý / giới hạn |
|---|---|---|---|---|
| E01 — RQ1 | Tách so sánh full–empty trong cùng enabled package khỏi so sánh cả graph package | [Phân tích](tai_lieu/02_chuoi_du_bao_quyet_dinh.md) | Theo các link nguồn trong phân tích;963P khác/943giữ preview khác số964/944 của full–graph-free lịch sử | Chưa individual-edge quality/learning benefit |
| E02 — RQ1/RQ2 | Can thiệp lượng lịch sử;54 controls khớp trước 108 arms | [Phân tích](tai_lieu/03_can_thiep_lich_su.md), [control JSON](tai_lieu/lich_su_control.json) | [Run](../../../runs/rq1-history-availability-20261108-02/README.md), [worker](../../../runs/rq1-history-availability-20261108-02/source__history_availability_worker02.py), [log](../../../runs/rq1-history-availability-20261108-02/execution.log), [144 summary rows](../../../runs/rq1-history-availability-20261108-02/analysis__summary.json) | Whole-policy history, preview chưa served action; không thêm seed độc lập |
| E03 — RQ2 | Tách scalar ability khỏi residual trong thiết kế mới;36worlds/4.320 tương tác | [Phân tích](tai_lieu/04_nang_luc_va_tien_quyet.md), [summary](tai_lieu/nang_luc_summary.json) | [Run](../../../runs/rq2-controlled-ability-prerequisite-20261108-01/README.md), [plan](../../../runs/rq2-controlled-ability-prerequisite-20261108-01/plan.json), [outcomes](../../../runs/rq2-controlled-ability-prerequisite-20261108-01/native__outcomes.json), [log](../../../runs/rq2-controlled-ability-prerequisite-20261108-01/execution.log) | Kết quả nhỏ, hữu hạn; high penalty-neutral là dự kiến từ thiết kế; không kết luận năng lực con người |
| E04 — RQ2 | Phân biệt retention metric tuyến tính với soft-mastery phi tuyến | [Phân tích](tai_lieu/05_retention.md) | Công thức/fixture và manifest được dẫn ngay trong phân tích | Phản ví dụ trạng thái dựng sẵn chưa chứng minh reachable trajectory |
| E05 — RQ2 | Kiểm nhiễu logged practice order Junyi | [Phân tích](tai_lieu/06_dieu_kien_va_junyi.md) | Các cohort, controls và common-population run được dẫn trong phân tích | Không đọc correctness/Holdout cho order-only; chưa causal instructional result |
| E06 — dữ liệu RQ3 | Đã sinh và kiểm corpus 60 người học/12.600 tương tác | [Phân tích](tai_lieu/07_corpus.md), [manifest](tai_lieu/corpus_manifest.json) | [Run](../../../runs/development-corpus-native-20261108-01/README.md), [corpus](../../../../artifacts/simulator/corpora/grade10-development-lifecycle01-20261108/), [collector](../../../../scripts/research/collect_development_corpus.py) | Không fitted model/optimizer/finalevents. Một câu “dự kiến” trong báo cáo nguồn là snapshot trước đóng gói; manifest48 outputs xác nhận closure |
| E07 — phương pháp | Chọn protocol Development, train/selection/calibration riêng, fresh refit | [Protocol](tai_lieu/08_protocol_development.md) | [Lifecycle contract](../../../../docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md) | Contract không tự chứng minh trainer đã chạy; không quyền fullCV/paid/Holdout |
| E08 — tổng hợp nền | Baseline BKT/GAM Development và các module kiểm kỹ thuật | [Báo cáo kỹ thuật revision6](tai_lieu/01_bao_cao_ky_thuat_chi_tiet.md), [JSON nguồn](tai_lieu/bao_cao_revision6.json) | Các aggregate Development được ghim trong JSON, không truy cập lại Test/Holdout | Supported population khác, không diễn giải thắng–thua paired công bằng |

## Cách trích trong luận văn

Ví dụ: “Trong chẩn đoán E02,54đối chứng đầy đủ lịch sử khớp kết quả gốc trước can thiệp; xem `rq1-history-availability-20261108-02`, `native__control_parity.json` và `analysis__summary.json`.” Khi trích thêm bảng/biểu đồ notebook, ghi ID E tương ứng và phạm vi pilot; không dùng số tests hay SHA làm số mẫu nghiên cứu.

## Đọc log như thế nào?

`execution.log` chỉ ghi thao tác đóng gói, không thay log thực nghiệm. Với E02/E03, mở `native__run.json` và `native__worker_run.json` trong cùng run để xem workload/trạng thái; với E02 thêm `native__case_ledger.jsonl`. `manifest.json` dùng đối chiếu nguồn/output SHA. Các thất bại trước đó vẫn giữ riêng; phiên thành công không biến các lần thất bại thành PASS.

## Những gì gói báo cáo không chứa

Không dataset gốc, không checkpoint lớn, không dự báo Holdout. Các source đang viết chưa test không được sao chép như thành quả đã nghiệm thu. Notebook báo cáo chỉ đọc số liệu đã lưu; chạy notebook không phải tái chạy thí nghiệm gốc.
