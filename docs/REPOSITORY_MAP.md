# Bản đồ repository và bằng chứng cho báo cáo KLTN

## 16/11 — Uploader lịch sử AKT có lưu tiến độ

[Hướng dẫn và bằng chứng](../research_tracking/runs/drive-history-upload-20261116-01/README.md) định vị uploader tại `scripts/akt/drive_resumable_upload.py`, kế hoạch 37 file / 35,15 GB, state/token riêng trên D và 29 ca offline đạt. Đã đăng nhập Sang và kiểm probe Drive thật, ngắt rồi tiếp tục đúng byte 262.144, checksum khớp. Upload lịch sử 35,15 GB đang chạy; trạng thái và biên nhận theo bundle.

## Báo cáo theo RQ và sprint hiện hành ngày 16/11/2026

[HTML tự chứa, ba trang A4](../research_tracking/supervisor_reports/2026-11-16/01_tien_do/BAO_CAO_NGHIEN_CUU.html) và [Markdown đồng bộ](../research_tracking/supervisor_reports/2026-11-16/01_tien_do/BAO_CAO.md) trình bày riêng thành quả/số liệu/phần còn thiếu của ba RQ và đối chiếu sáu sprint theo đề cương. Đợt15/11 giữ báo cáo diễn tiến. Kiểm bản mới nằm trong bundle refit, các file `report-rq-sprints-20261116-*`. Các file `report-summary-20261116-*` giữ nghiệm thu bản một trang trước khi mở rộng.

## 16/11 — Danh mục giữ/lưu trữ/unused và gói upload

Thư mục [drive-offload-history-20261116-01](../experiments/akt/results/drive-offload-history-20261116-01/) gom35ZIP lịch sử bằng hardlink, tổng35,15GB, chia bốn nhóm có thể chọn upload. Đây là archive lịch sử có thể chồng lặp member với gói dedup. `COLD_ARCHIVE_FOLDER_STATE.json` lưu ánh xạ và trạng thái chờ upload, chưa dọn nguồn.

Người dùng tự upload gói [drive-offload-duplicates-20261116-01](../experiments/akt/results/drive-offload-duplicates-20261116-01/), khoảng10,88GB, gồm CONTENT dùng hardlink, ánh xạ21.604đường dẫn và metadata869file. Gói đã kiểm đủSHA2.219nội dung. `MANUAL_OFFLOAD_STATE.json` trong bundle audit lưu trạng thái chờ upload. Dung lượng dọn thực cần kiểm file identity/nlink và đo riêng, tổng55,78GB là logic.

Đã sao lưu đợt đầu sáu ZIP model/audit lên [Drive KLTN](https://drive.google.com/drive/folders/1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7), tổng 471,34 MB. Ba ZIP lớn ở dạng bảy phần, kèm manifest/helper/hướng dẫn. `DRIVE_UPLOAD_RECEIPT01.json` trong bundle lưu trữ xác nhận metadata và SHA đọc lại của đủ 13 file. Bản gốc cùng các phần chia còn trên D, danh mục lịch sử 55,78 GB tiếp tục có điều kiện bảo toàn riêng.

Rà lại giá trị audit trong [báo cáo lưu trữ hiện hành](../research_tracking/reports/ARTIFACT_RETENTION_20261116.md) đã chuyển checkpoint A3 epoch 4/bước 584 sang giữ audit. Danh mục quyết định mới là `RETENTION_REVIEW02.csv`, ghi điều kiện bảo toàn nội dung và lineage cho mọi bản trùng/phần upload. `UNUSED.csv` giữ kết luận lịch sử. Gói 06 giữ checkpoint duy nhất và hồ sơ rà lại. Chưa dọn file gốc.

[Báo cáo lưu trữ](../research_tracking/reports/ARTIFACT_RETENTION_20261116.md) và [hồ sơ kiểm](../research_tracking/runs/artifact-retention-audit-20261116-01/README.md) định vị checkpoint/artifact theo phần việc KLTN còn lại. `experiments/akt/results/artifact-offload-20261116-01/` giữ CSV theo file, các bản giữ/SHA và nămZIP upload khoảng442,8MB. Bản gốc giữ nguyên. UNUSED là danh mục ứng viên thu gọn, các snapshot/bundle đã đóng tiếp tục cần lineage khi xử lý.

## 16/11 — A0–A3 expert Junyi đã hoàn tất refit TRAIN90

[Nghiệm thu A3 cuối](../research_tracking/runs/junyi-refit-pipeline-20261114-01/a3-final-acceptance01.json) xác nhận đủ9epoch, mỗi epoch14.947.674target/2.040step, model/Adam hữu hạn và RNG. Model gọn ở `experiments/akt/results/model-export-a3-refit-20261114-01/`. [Đối chiếu bốn model](../research_tracking/runs/junyi-refit-pipeline-20261114-01/exports-verified-a0-a1-a2-a3-portable-memory-cap-v1.json) kiểm identity chung và chỉ tách trần VRAM theo hợp đồng. A3 nối H100/L4/T4/H100, thời gian cần báo riêng. Mọi App workspace mới đã stopped/tasks0. Hai báo cáo trong đợt15/11 đã nối tiếp kết quả16/11. Hiệu chỉnh và đánh giá độc lập còn thiếu. Các mục bên dưới giữ diễn tiến lịch sử.

## Báo cáo GVHD hiện hành — cập nhật15/11

Cập nhật16/11. A0–A3 đã xuất model refit đầy đủ theo [snapshot nghiệm thu](../research_tracking/runs/junyi-refit-pipeline-20261114-01/a3-training-export-snapshot-20261116.json). [Hồ sơ dung lượng](../research_tracking/reports/DISK_USAGE_CLEANUP_20261116.md) ghi đợt dọn37fixture pytest cũ đã được người dùng duyệt, giải phóng7,24GB. Inventory và archive log giữ tại artifacts/akt/runtime theo receipt. Các đoạn dưới là mốc lịch sử.

Cập nhật tiếp theo trong ngày15/11. A3 đã khôi phục và chạy thật trên Colab Tesla T4, Drive cá nhân đã kiểm bản sao sau4epoch và checkpoint epoch5/bước1.202. Checkpoint T4 đầu và11file liên quan đã tải vềD/kiểmSHA. Chuỗi tiếp tục có giới hạn tới9epoch, sao lưu Drive mỗi lượt. Đọc `STATE.json` và `a3-t4-monitor-progress02.json` trong [bundle refit](../research_tracking/runs/junyi-refit-pipeline-20261114-01/README.md) trước tiếp tục. Hai báo cáo GVHD đã cập nhật. Đoạn dưới ghi trạng thái trước lượt T4.

[HTML](../research_tracking/supervisor_reports/2026-11-15/01_tien_do/BAO_CAO_NGHIEN_CUU.html) và [Markdown](../research_tracking/supervisor_reports/2026-11-15/01_tien_do/BAO_CAO.md) nối tiếp ngày 14/11. A0, A1, A2 đã hoàn tất refit 9 epoch mỗi model và xuất gói model trên D. Có figure SVG/PNG/CSV so thời gian cùng TRAIN90, cùng 134.529.066 target qua 9 epoch mỗi model. A3 refit đã nghiệm thu đủ3/9epoch trên D. Các App Modal đã dừng, credit quan sát còn0,18USD. Đang chuyển Colab theo yêu cầu mới nhất, chờ ZIP gói06 trong Drive cá nhân đã mount. Hiệu chỉnh và đánh giá độc lập còn thiếu. Bundle refit giữ `STATE.json`, `exports-verified-a0-a1-a2.json` và `refit-remaining-budget-review.json`. Mọi App H100 của đợt này đã dừng. Các mục bên dưới lưu diễn tiến lịch sử.


## Báo cáo GVHD hiện hành — chốt ngày14/11

[Báo cáo HTML](../research_tracking/supervisor_reports/2026-11-14/01_tien_do/BAO_CAO_NGHIEN_CUU.html) và [Markdown](../research_tracking/supervisor_reports/2026-11-14/01_tien_do/BAO_CAO.md) là hai file đọc của bản chốt mới, có tiến độ từngRQ, mạch nghiên cứu và phần còn thiếu. Đợt10/11 giữ lịch sử. QA theo `report-20261114-qa.json` trong bundle refit, hình gốc vẫn theo runA3.


## 14/11 — Hoàn thiện pipeline refit A0–A3 trên local

[Hồ sơ refit](../research_tracking/runs/junyi-refit-pipeline-20261114-01/README.md) giữ epoch plan thật9×4,19ca refit mới và78ca hồi quy trước đó, có chồng lặp. Model/Adam/RNG của bốn biến thể khớp khi kiểm continuous/resume trên CPU tổng hợp. Đã dựng encoding90, window/context cache cho142.621người học/14.947.674target; bốn đầu vào thật kiểm đạt. 85ca local đạt, Gate Linux2.660ca PASS, snapshotA0 đã đóng/kiểm trênD. CUDA refit còn chờ. Entrypoint ghim grant/Gate/runtime và khóa đúng topology/confidence TRAIN80 qua selected index. Đọc STATE trước tiếp tục. Chưa refit dữ liệu thật; Modal chỉ có lượt kiểm CPU nguồn mới.

## 14/11 — A3 hoàn tất selected-fit, đủ A0–A3 expert trên Junyi

[Hồ sơ A3](../research_tracking/runs/junyi-a3-selected-20261114-01/README.md) giữ A3 đã hoàn tất 12 epoch, chọn epoch 9, học đủ TRAIN80 13.347.331 target mỗi epoch. Đã kiểm đủ 1.600.343 dự đoán selection, target/order/probability identity, 0 OOV, checkpoint/Adam/RNG và gói model bốn file trên D. Log Loss native selection 0.35357115. A0–A3 expert đã hoàn tất selected-fit, đánh giá độc lập và các bước cuối còn chờ. Model chính tại `experiments/akt/results/model-export-a3-batch128-20261114-01/`. Đã có figure và hai báo cáo GVHD cập nhật. Đọc STATE/CLOSEOUT_MANIFEST trước công việc tiếp theo.


## 14/11 — A3 đã kiểm snapshot và bắt đầu lượt training có giới hạn

[Hồ sơ A3](../research_tracking/runs/junyi-a3-selected-20261114-01/README.md) giữ đối chiếu cấu hình A0–A2, snapshot03, cache/confidence TRAIN80 và đối soát ngân sách. Một lượt H100 tối đa2,60USD được cấp trong trần toàn KLTN30USD, dự phòng cuối3USD. `STATE.json` giữ tiến độ và điểm tiếp tục. Kết quả training chỉ được nghiệm thu sau kiểm checkpoint/prediction/inventory và xác nhận GPU dừng.

## 14/11 — A2 Junyi hoàn tất selected-fit, model đã xuất trên D

[Hồ sơ A2 và confidence](../research_tracking/runs/junyi-confidence-completion-20261114-01/README.md) giữ confidence TRAIN80, cache thật, Gate Linux 2.615 ca và snapshot03. A2 đã hoàn tất 12 epoch, chọn epoch 9, kiểm đủ 1.600.343 dự đoán theo target/thứ tự thời gian và xuất gói bốn file tại `experiments/akt/results/model-export-a2-batch128-20261114-01/`. Lượt cuối có 210 artifact đã tải D/kiểm, cả hai H100 đã dừng. Có SVG/PNG/CSV và báo cáo GVHD cập nhật. Trung bình mẫu NVML hai lượt 32,23%, mục tiêu 50% chưa đạt. STATE giữ phần còn thiếu gồm A3, refit/calibration/đánh giá độc lập và đối soát dự toán trước khoản GPU tiếp theo.

## 14/11 — Tiếp tục confidence thật và selection đầy đủ

[Hồ sơ](../research_tracking/runs/junyi-confidence-completion-20261114-01/README.md) giữ confidence thật đã hoàn tất 736 child/976 cạnh, corpus 13.347.331 target và cache selection 1.600.343 target khớp A0. Đang build cache graph thật trên CPU. STATE là điểm tiếp tục. Gate Linux02 đạt 2.614 ca sau khi ghim fixture CPU xác định; giữ failure01. Cả hai App đã dừng, tổng reservation 0,30 USD đóng theo cận bảo thủ. Chưa training chính A2/A3.


## 14/11 — Cache A2/A3 và resume đã kiểm trên T4 qua MCP

[Hồ sơ](../research_tracking/runs/junyi-gpu-boundary-t4-20261114-01/README.md) giữ 102 ca hồi quy local, 39 ca hợp đồng cache mở rộng và parity/resume thực tế A2/A3 trên T4. Sai lệch dự đoán bằng 0; tốc độ cache A2 giảm 4,7%, A3 gần như ngang nhau trong phép đo ngắn. Confidence fixture kỹ thuật; training chính và stop barrier Modal thật còn chờ. Trạng thái tải artifact/trả runtime ghi ở STATE, 0 USD Modal.


## 14/11 — Confidence TRAIN80, tạm dừng có lưu tiến độ

[Hồ sơ](../research_tracking/runs/junyi-confidence-train80-20261114-01/README.md) giữ checkpoint đủ số record/target nhưng corpus chưa niêm phong, chưa fit child. Gate Linux2590ca trước cache mới, cache A2/A3 local38ca. Selection wiring mới chưa kiểm, chưa training A2/A3. STATE giữ đường dẫn tiếp tục và các blocker.


## 14/11 — Tách CPU local và GPU cho A2/A3

[Hồ sơ](../research_tracking/runs/junyi-local-gpu-separation-20261113-01/README.md) giữ 71 ca local đạt, đối chiếu 27 trường với A0/A1 thật, stop barrier trước download/nén và checkpoint recovery. Chưa fit confidence thật, kiểm Linux/CUDA hay training A2/A3. Đợt này 0 USD Modal.


## 13/11 — Chuẩn bị A2/A3 và chuyển kiểm dữ liệu sang CPU

[Hồ sơ](../research_tracking/runs/junyi-a2-a3-preparation-20261113-01/README.md) giữ339ca CPU, A2/A3 compact có confidence/gate, handoff toàn TRAIN80 lượt cuối kiểm285,31giây CPU/nhận3,13giây. Chưa training A2/A3,0USD Modal. Orchestration staged, confidence thật và CUDA còn chờ.


## 13/11 — Xuất gọn A1 Junyi và giới hạn so sánh A0

[Hồ sơ xuất model](../research_tracking/runs/akt-model-export-20261113-01/README.md) giữ gói bốn file trên D, một .pt epoch 9, kiểm CPU load/Adam/RNG/SHA đạt. Cấu hình học và tập target A0–A1 khớp. A0 chọn epoch bằng validation batch 1, chỉ epoch 9 đã replay batch 128; ranking toàn 12 epoch còn chờ. Refit/calibration/đánh giá độc lập còn chờ.


## 13/11 — A1 hoàn tất chọn checkpoint Junyi với dữ liệu so sánh đã kiểm

[Hồ sơ](../research_tracking/runs/junyi-a1-selection-cache-20261113-01/README.md) giữ Gate2.528ca, parity checkpoint thật CPU/CUDA, A1 Junyi selected-fit hoàn tất12epoch/chọn9 theo min_delta0,0001, reload/prediction khớp. Train mới182–206giây/epoch, GPU gần đây35–38%. Mọi checkpoint/predictions/logs đã tảiD, H100 dừng. Refit/calibration/đánh giá độc lập và A2/A3 Junyi còn chờ.

## 13/11 — cache A1 đã tích hợp và kiểm T4

[Hồ sơ cache A1](../research_tracking/runs/junyi-a1-graph-cache-20261113-01/README.md) giữ 62 ca local đạt, parity T4 drift 0, 100 bước kiểm kỹ thuật, throughput tăng 1,84% và GPU 70,8% trong đoạn đo. Cache giữ tùy chọn vì chênh lệch thời gian còn nhỏ. Có rà 14 bước cache của epoch, artifact đã tải về D và T4 đã trả, 0 USD Modal. Cache toàn TRAIN80, migration source2 và producer CUDA còn chờ.


## 13/11 — Junyi thật trênT4, chuỗi dài và cache

[Hồ sơ](../research_tracking/runs/junyi-a1-real-t4-20261113-01/README.md) giữ parity dữ liệu thật,32step A1 sauwarmup GPU69,7%, input preloaded75,4%, traceCPU/CUDA và prototypecachecontext1,65×. Mức48,5% đoạn ngắn được giữ. Modelbenchmark28,9MB đã tảiD/kiểm799chunk vànạpCPU. T4đãtrả,0USDModal. Full training/source2migration/cacheproduction cònchờ.

## 13/11 — A1 compact đã nối adapter và kiểm cả bước học T4

[Hồ sơ](../research_tracking/runs/junyi-a1-compact-adapter-20261113-01/README.md) giữ 69 ca local, parity T4 drift0, collate+8step 13,79→3,39 giây và GPU mẫu 15→76%. Source cuối đã nối factory, migration checkpoint source2/full producer/H100 còn chờ. 0 USD Modal.

## 13/11 — thử context A1 dạng mảng trên CPU

[Hồ sơ](../research_tracking/runs/junyi-a1-compact-context-20261113-01/README.md) giữ đối chiếu 128 window TRAIN80/5.527 target, message FP32 và mask khớp, kiểm future response và role đạt. Riêng context/checksum giảm 0,826→0,251 giây, 3,29 lần. Prototype chưa nối trainer/cache/GPU.

## 13/11 — A1 giảm chuyển đổi evidence và kiểm T4

[Hồ sơ](../research_tracking/runs/junyi-a1-fastpath-t4-20261113-01/README.md) giữ phép kiểm GPU 28,62 giây, drift0 ở hai alpha, 19 ca Colab và 74 ca local. Chuỗi sáu bước giảm 6,20→4,93 giây, GPU mẫu 26,5→37,8%. Full producer/resume còn chờ, 0 USD Modal.

## 13/11 — A1 H100 và validation A0 thực

[Hồ sơ](../research_tracking/runs/junyi-a1-selected-20261113-01/README.md) có Gate Linux 2.336 ca, A0 checkpoint9 full-selection batch128 đạt Log Loss bằng giá trị cũ; A1 đã train đủ epoch1, validation còn chờ; checkpoint/logs đã lưu D, H100 dừng. GPU training trung bình4,98%, cần xử lý nút thắt CPU trước chạy tiếp.

## 13/11 — kiểm checkpoint A0 thật

Kiểm tiếp bằng checkpoint A0 epoch 9 thật trên CPU với 3.538 target tổng hợp đã xác nhận nạp đúng trọng số, target/thứ tự khớp và model không đổi. Sai lệch xác suất lớn nhất 0,0000224 vượt ngưỡng kiểm đã đặt, dù chênh lệch Log Loss chỉ khoảng 0,0000000218. Giữ nguyên ngưỡng kiểm, chưa nghiệm thu batch128 cho training chính. Cần đối chiếu checkpoint này trên CUDA và selection Junyi thật. Lượt kiểm dùng 0 USD Modal.

[Hồ sơ](../research_tracking/runs/junyi-a0-checkpoint-parity-20261113-01/README.md)


## 13/11 — validation theo batch

[Hồ sơ](../research_tracking/runs/junyi-validation-batch-20261113-01/README.md) giữ 126 ca Linux đạt, hai phép kiểm T4, log và figure. Trên 12.800 target tổng hợp có tín hiệu đồ thị, A0 tăng tốc 3,88 lần, A1 2,01 lần. Chưa kiểm lại toàn selection bằng checkpoint A0. Không train epoch, không dùng Modal.

## 13/11 — confidence Junyi theo native window

[Hồ sơ CPU](../research_tracking/runs/junyi-confidence-core-20261113-01/README.md) giữ kiểm717exercise, crossfit solver thật, ledger và unsupported null trên dữ liệu tổng hợp. Worker/artifact/model A2/A3 còn chờ.


## 13/11 — guard so sánh đã nối vào producer

[Hồ sơ](../research_tracking/runs/junyi-comparison-admission-20261113-01/README.md) có77ca CPU đạt và kiểm SQL độc lập1.600.343selection targets khớp A0. Confidence Junyi và kiểm source Linux tiếp theo còn chờ.


## 13/11 — kiểm Junyi trước các biến thể AKT

[Hồ sơ kiểm](../research_tracking/runs/junyi-comparison-preflight-20261113-01/README.md) có audit split/vocabulary, hợp đồng so sánh và kết quả T4 A0/A1 batch128 cùng checkpoint đã tải về D. A2/A3 Junyi và ràng buộc entrypoint còn cần hoàn thiện trước training chính.


## Chốt 13/11 — A0 H100 hoàn tất chọn checkpoint

[A0 H100 hoàn tất](../research_tracking/runs/junyi-a0-h100-batch128-20261112-01/README.md) có 12 epoch, selected 9, 1.600.343 dự báo đã kiểm, model xuất về D và cả ba App đã dừng. [Báo cáo training riêng](../research_tracking/supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html). Các mốc bên dưới giữ theo thời điểm lịch sử.


## 12/11 lúc23giờ00 — A0 H100 batch128 có5epoch

[Bundle đang hoạt động](../research_tracking/runs/junyi-a0-h100-batch128-20261112-01/README.md) đã nghiệm thu5epoch,20checkpoint, archive532MB và0GPU cuối đợt1. Đợt2 nối từepoch6, không benchmark riêng. Source mới đạt2.234caCPU, batch128 cóprotocol riêng.


## 12/11 — hai tiến trìnhT4 chưa tăng tổng thông lượng

[Kiểm song song](../research_tracking/runs/junyi-concurrent-gpu-20261112-01/README.md) đã nghiệm thu45,49giây lần lượt và45,74giây đồng thời, GPU87,9%→99,9%, bốn checkpoint khớp. Không tiếp nhận chạy hai tiến trình làm tăng tốcT4. H100 chưa chạy.


## 12/11 — bộ model xuất gọn trênD

[Bộ model](../experiments/akt/results/model-export-20261112-01/README.md) có8file.pt đại diện, MODEL_INDEX và SUPPORT.zip, khoảng221MB. [Kiểm xuất](../research_tracking/runs/akt-model-export-20261112-01/README.md) đạt8/8SHA/schema/vocabulary trênCPU. H100 đang chờ. Grade10 selected-fit80 và Junyi best-so-far được ghi riêng.


## 12/11 lúc20giờ59 — batch32 đã đo GPU87,5%, H100 đang chờ

[Bundle batch32](../research_tracking/runs/junyi-batch32-utilization-20261112-01/README.md) giữ115mẫu GPU/VRAM,CSV,SVG và checkpoint. GPU-Util87,5%,19.792target/giây, checkpoint/resume khớp. Main A0 chưa đổi batch, H100 chưa chạy và được người dùng yêu cầu chờ.


## 12/11 lúc20giờ07 — đóng đợt đo GPU và đối soát ngân sách

[A0 đã nghiệm thu sáu epoch](../research_tracking/runs/junyi-main-selected-20261112-01/execution06-verification.json), archive đã kiểm và dừng App được xác nhận độc lập. [Đợt tối ưu](../research_tracking/runs/junyi-step-sync-20261112-01/README.md) có hai phương án đo CUDA chưa đạt tiêu chí tiếp nhận, một cache candidate chỉ đạt CPU trước timeout. Step chính đã khôi phục. [Đối soát và dự toán](../research_tracking/reports/AKT_GPU_UTILIZATION_AUDIT_20261112.md) ghi credits3,24USD, billed0USD, snapshot container rỗng. Chưa xác nhận tối ưu toàn GPU, cần tính lại chi phí cả ma trận trước training dài.


## 12/11 — ưu tiên xác nhận tối ưu GPU

[Bundle kiểm đồng bộ CPU–GPU](../research_tracking/runs/junyi-step-sync-20261112-01/README.md) giữ bản trước/candidate, đối chiếu CPU chính xác và thiết kế ba cặp đo T4. Đợi A0 execution06 có archive đã kiểm và App đã dừng mới chạy một profile tối đa0,20USD. Candidate chưa nghiệm thu CUDA, chưa áp dụng vào source04 hiện hành. [Số đo nền GPU](../research_tracking/reports/AKT_GPU_UTILIZATION_AUDIT_20261112.md) cho thấy GPU43,9%, chưa đủ kết luận tối ưu.


## Hiện hành 12/11 — A0 Junyi có ba epoch hoàn tất, RQ1/RQ2 có phân tích mới

[A0 full TRAIN80](../research_tracking/runs/junyi-main-selected-20261112-01/README.md) đã giữ checkpoint46000 sau Modal preemption, tiếp tục cùng logical run và hoàn tất ba epoch. Archive execution03 đã đối chiếu SHA và App đã dừng. Execution04 đang tiếp tục từ epoch4 bước15.016, giữ nguyên source04 và batch4. Bộ tiếp tục hữu hạn sau04 ở `research_tracking/runs/junyi-main-selected-20261112-01/bounded-continuation-after04-state.json`, chỉ gồm05/06, tổng dự phòng1,70USD đã phân bổ. Đọc state trước mọi launch để tránh chạy trùng. [Bảng training](../research_tracking/reports/AKT_TRAINING_STATUS_20261112.md) ghi số epoch, thời gian và phần còn lại. [Throughput/cache](../research_tracking/runs/junyi-throughput-20261112-01/README.md) có số đo thực và figure. [Producer A1](../research_tracking/runs/junyi-a1-selection-20261112-01/README.md) đã qua Gate CPU2.226, còn GPU fit. Nguồn A0 source04 và nhánh A1 source07 được ghim riêng.


[Phát hiện RQ1/RQ2](../research_tracking/reports/RQ12_CORE_FINDINGS_20261112.md) đã bổ sung đối chứng mở bài trên3.240trạng thái và phân tích exposure không dùng nhãn trên13.347.331target TRAIN. Có source, CSV, figure và kiểm độc lập. Calibration, đối chứng dự báo và closed-loop chính còn mở.

## 12/11 — dữ liệu chính và context A1 Junyi

[Cachefull](../research_tracking/runs/junyi-selected-cache-20261112-01/README.md) đãkiểm đủ13.347.331train/1.600.343selection,717exercise/0selectionOOV. [A1prefix](../research_tracking/runs/junyi-graph-prefix-20261112-01/README.md) chỉ dùngpastwindow,74tests/11subtests đạt. Mainproducer/refit/calibration/nativegraphadapter vẫn đang chờ nối; chưa uploadcachefull.

## 12/11 — AKT đã hoàn tất một epoch Junyi trên A10

[Hồ sơ Junyi](../research_tracking/runs/junyi-akt-cuda-engineering-20261112-01/README.md) nghiệm thu11.833train/79updates,1.530selection/125OOV, checkpoint nạp lại khớp vàđọc lại3file từVolume. Gate Linux2.037ca đạt. CóSVG/PDF/PNG/CSV vàreportGVHD cập nhật. Chưa main Junyi selected/refit/calibration hoặc graph variants.

## 12/11 — Junyi đã nối phase dữ liệu và cache kỹ thuật

[Hồ sơ kiểm](../research_tracking/runs/junyi-akt-phase-views-20261112-01/README.md) đạt52tests/81subtests. Cohort320 giữ11.833train/1.530selection,1.405supported/125OOV. Chưa neural training Junyi; producerCUDA/Gate nguồn mới đang chuẩn bị.

## 12/11 — đủ A0–A3 selected GPU trên Grade10

[Đợt sáu graph fits](../research_tracking/runs/modal-akt-graph-selected-20261112-01/README.md) đã nghiệm thu cả expert/learned, cùng A0 thành7selectedcheckpoints và30epochcheckpoints đã lưu. TổngModal≈0,641USD, Appđãdừng. CófigureSVG/PDF/PNG vàdữ liệu. Junyi80/10/10 metadata đãtạo/7tests đạt, producerCUDA vàGate mới còn thiếu.

## 12/11 — Main60 A0 đã training CUDA và kiểm kết quả

AKT không đồ thị hoàn tất8epoch/best5/288updates và1260dự báo selection trên corpus60học viên Grade10. Đã tải năm checkpoint/archive124MB và kiểm độc lập. Chưa so sánh graph, refit/calibration hoặc Junyi. Bằng chứng `research_tracking/runs/modal-akt-recovery-20261112-01/main60-a0-verification.json`.

## 12/11 — checkpoint CUDA và lưu trữ Modal đã nghiệm thu

Đã đạt Gate CPU1.994ca/198nguồn/92module trên image Modal. Pilot GPU A0/A3 đã đạt16Adam updates trên dữ liệu giả, bốn checkpoint và cùng kết quả model/Adam/RNG/counters/predictions giữa liên tục và phục hồi. Đã tải archive96,8MB và đọc lại bốn checkpoint từ Volumev2 để đối chiếu độc lập. Sửa runner để native checkpoint ở filesystem cục bộ, durable copy từng pha có SHA và sync; source model/hyperparameter giữ nguyên. Actual A0 GPU lifecycle engineering10x84 đang kiểm tiếp. Main60/Junyi, full workflow/preemption recovery và throughput đại diện còn thiếu. [Hồ sơ](../research_tracking/runs/modal-akt-recovery-20261112-01/README.md).


## 12/11 — pilot Modal đã thực thi tới kiểm runtime, phục hồi checkpoint còn bị chặn

Đã tạo entrypoint Modal riêng, xác nhận nhận NVIDIA L4 ở canary, và kiểm môi trường CUDA thực trong các lượt pilot. Volume đã lưu và tải được ba archive lỗi, mỗi archive được đối chiếu CRC/SHA. Các lỗi chuyển đường dẫn và output từ Colab đã sửa. Lượt tiếp theo bị chặn trước batch đầu bởi cap RSS 2 GiB, đo thực tế khoảng 4 GiB; cap mới 6 GiB chưa được nghiệm thu vì lượt07 hết hạn chờ 600 giây. Mọi App của lượt kiểm đã dừng. Billing đọc gần nhất ghi tổng kỳ khoảng 0,02056 USD, net billed 0 USD sau credits/allowance. Chưa có checkpoint GPU phục hồi đạt hoặc training nghiên cứu chính. [Hồ sơ vận hành](../research_tracking/runs/modal-quick-preflight-20261111-01/README.md).


## 10/11 — bốn biến thể AKT đã qua CUDA smoke trên T4

T4 miễn phí đã chạy A0–A3 theo recipe CUDA, tổng 8 Adam updates/192 target giả/24 dự báo, chung initial backbone, nguồn nguyên và số học hữu hạn. Đã tải và kiểm log cùng 44 package. Chưa checkpoint/restore, throughput đại diện hoặc Main fit. Modal 0 USD. [Hồ sơ](../research_tracking/runs/akt-colab-t4-current-20261110-01/README.md).


## 10/11 — đã nghiệm thu Gate CPU cô lập cho AKT

Môi trường Linux cô lập đã nghiệm thu 44 package, Gate CPU đạt 1.993/1.993 ca trên 198 file nguồn và 92 module, không loại ca. Đã tải về, kiểm CRC/SHA, JUnit và nguồn. CUDA/recovery/throughput và training nghiên cứu chính còn thiếu. Modal 0 USD. [Bằng chứng](../research_tracking/runs/akt-colab-isolated-cpu-20261110-01/README.md).


## 10/11 — đã kiểm tích hợp trên Colab CPU

Colab CPU đã đạt1.992ca trên92module trong294,935giây,0failure/error/skip; tách riêng1ca kiểm môi trường cô lập. Đã sửa gói thiếu cấu hình, bỏ phụ thuộc snapshot chưa tracked và làm kiểm timestamp xác định. Reader/model production giữ nguyên; inventory198file, chưa full Gate/CUDA/training chính. [Bằng chứng](../research_tracking/runs/akt-colab-integration-20261110-01/README.md).


## 10/11 — checkpoint A0 đã nối vào dự báo tuần tự

Đã nối checkpoint nghiên cứu A0 vào dự báo tuần tự bằng loader tái dùng backend hiện có. Colab đạt22/22ca, gồm12mới và10hồi quy; checkpoint fixture48targets/2updates cho6dự báo khớp wrapper trong1e-6. Giữ lượt lỗi fixture, chưa final fitted/refit/calibration hoặc closed-loop chính. [Bằng chứng](../research_tracking/runs/akt-a0-online-colab-20261110-01/README.md).


## 10/11 — AKT đã kiểm trực tiếp trên Colab CPU

Đã chuyển được lượt kiểm AKT sang Colab CPU có đủ RAM. Baseline đạt67/67, research core đạt113/113, không lỗi/bỏ qua; đã tải logs và JUnit về, kiểm CRC/SHA. Runtime kế thừa qua venv được ghi rõ; chưa full Gate, CUDA hoặc Main training. Modal0USD. [Bằng chứng](../research_tracking/runs/colab-current-cpu-20261110-01/README.md).


## Ưu tiên hiện hành — nghiên cứu cốt lõi trong7ngày

[Roadmap08](thesis_recovery/08_CRITICAL_PATH_ROADMAP.md) và TASKS.json đã ưu tiên evidence RQ1/RQ2, GPU tối thiểu, actual A0–A3/baselines, closed-loop và viết. Gói kỹ thuật78tests đã chốt, không mở rộng infrastructure khi chưa có thí nghiệm bị chặn.


## 10/11 — chốt gói review thống kê, chuyển ưu tiên sang nghiên cứu

[Hồ sơ78tests](../research_tracking/runs/nine-review-publication-20261110-01/README.md) giữ input/output hashes, lỗi muộn và quota. Đây là fixtures, chưa Main freeze. Dừng mở rộng tổng quát khi chưa có thí nghiệm bị chặn.


## 10/11 — sổ khoảng trống và tiến độ đã đối chiếu lại

[Hồ sơ audit](../research_tracking/runs/research-readiness-reconciliation-20261110-01/README.md) xác nhận3PDF chuẩn,14gap hiện hành và cập nhật8parent tasks. Giữ178IDs,11SVG và17tables. Không có kết quả nghiên cứu mới; hai file GVHD đã làm rõ trạng thái chuẩn bị.


## 10/11 — Gate195 đã ghim nguồn, collection bị chặn RAM

[Hồ sơ vận hành](../research_tracking/runs/gate195-preparation-20261110-01/README.md) xác nhận195sources/91modules. Collection13 dừng tại fresh4GiB trước GO, chưa có IDs/tests/PASS mới. Giữ derivative AST và failure để tiếp tục khi đủ điều kiện.


## 10/11 — reader đủ quy mô1.260target giả

[Hồ sơ kiểm](../research_tracking/runs/nine-file-scaling-20261110-01/README.md) đạt71tests, reader11,807giây/45giây và peak57.769.984bytes. Giữ timeout cũ, cap18handle được đo riêng. Đây là đọc artifact, chưa là GPU training throughput.


## 10/11 — chín bộ file đã ghép vào thống kê chung

[Hồ sơ kiểm](../research_tracking/runs/nine-selected-file-statistics-20261110-01/README.md) đạt67tests trên dữ liệu giả, nối reader/metadata/CSV/accumulator/kernel2000draws. Chưa actual Main admission hoặc lựa chọn mô hình. Source195 cần refresh Gate.


## 10/11 — đối chiếu hồ sơ thực thi bốn lượt CPU

[Hồ sơ kiểm](../research_tracking/runs/selected-operation-reconciliation-20261110-01/README.md) đạt43tests và hash lại116nativefiles. Giữ riêng schema tài nguyên A0 cũ. Chưa admission matrix chính hoặc chọn winner.


## 10/11 — metadata ba pipeline đã nối với checkpoint

[Hồ sơ kiểm](../research_tracking/runs/selected-producer-metadata-20261110-01/README.md) đạt39tests và4producer engineering, gồm nguồn thực trước–sau. Chưa review operation receipts/request độc lập hoặc admission đủ9. Source193 cần refresh Gate.


## 10/11 — liên kết checkpoint trước so sánh mô hình

[Hồ sơ kiểm](../research_tracking/runs/selected-checkpoint-binding-20261110-01/README.md) đạt32tests và đọc/hash4checkpoint thật, giữ failure do ánh xạ tên kiến trúc. Chưa admission provenance/chín candidate. Source191 cần refresh Gate.


## 10/11 — chuẩn hóa đầu ra trước so sánh mô hình

[Chuẩn hóa selected rows](../research_tracking/runs/selected-row-normalization-20261110-01/README.md) đạt24tests và336dòng của4môhình trên corpus engineering, khớp quần thể độc lập. Chưa kiểm đủ metadata/chín candidate hoặc chọn winner. Gate cần refresh trên source189.


## 10/11 — AKT đồ thị cố định và GKT qua trọn lượt kiểm CPU

[A1 expert](../research_tracking/runs/a1-expert-selected-engineering-20261110-01/README.md) đạt7epoch/best4 và [GKT](../research_tracking/runs/gkt-selected-engineering-20261110-01/README.md) đạt11epoch/best6, đều nạp lại và xuất đủ84dự báo. Giữ nguyên cấu hình đã chốt, corpus kiểm kỹ thuật riêng và source provenance. [Bộ theo dõi RAM](../research_tracking/runs/owned-job-resource-exit-guard-20261110-01/README.md) có9canaries và hai probe, giữ lỗi cũ và chỉ bỏ qua exact handle đã xác nhận kết thúc. Các mốc này chưa là Main60, Junyi, refit/calibration hoặc CUDA. Báo cáo hiện hành đã cập nhật và kiểm desktop/mobile.

## 10/11 — hồ sơ CPU SAKT và tái dùng đồ thị đã đóng

[SAKT selected CPU](../research_tracking/runs/sakt-selected-engineering-20261110-01/README.md) có full84exports sau6epochs/best1. Giữ failure và72physicalupdates của cả hai lượt đã train. [Main60 sáu cấu hình](../research_tracking/runs/main60-graph-condition-binding-20261110-01/README.md) tái dùng Method24 đã fit, không thêm solver hoặc NN. [Notebook CPU](../notebooks/README.md) có gói nguồn/dữ liệu đã kiểm trên Windows, chưa chạy Colab/Linux. Main neural matrix, refit/calibration và CUDA còn chờ.

## 10/11 — Gate hiện hành và demo đã qua kiểm thực tế

[Gate183/1913](../research_tracking/runs/akt-current-gate183-20261110-01/README.md) đã đạt toàn bộ1913ca vàpublicindex riêng, globalpointer cũ giữ nguyên. [Demo fresh120](../research_tracking/runs/demo-fresh120-viewer-20261110-01/README.md) đạt113HTTPtests vàJS/desktop/mobile. [E11](../research_tracking/runs/thesis-rq2-e11-writing-20261110-01/README.md) đã nối fresh120 vào bảnthảo, prefix59562bytes nguyên vàreviewđộclậpđạt. Actualpubliccontrol AKT đãE7/best4, parentpause5/resume đang chuẩn bị. RecipeSAKT30 chốt trướcfit; producer mới chưanghiệmthu. Các mốc này chưađóngRQ3/CUDA hoặcquyềnchiModal.
## 10/11 — checkpoint GKT đã qua kiểm thực thi

[Bundle checkpoint28](../research_tracking/runs/gkt-research-checkpoint-20261110-01/README.md) giữ nguồn, logs và control/restored epoch khớp model, BN, Adam, RNG cùng counters. 28 ca đều đạt, source/runtime ổn định và Job0. Phạm vi là complete-epoch cùng process và budget origin. Research producer, adaptor và fitted baseline còn thiếu. Hai file báo cáo hiện hành10/11 đã cập nhật mốc này.

## Cập nhật10/11 — đối chứng đủ120ca và nghiệm thu CPU

[Báo cáo hiện hành10/11](../research_tracking/supervisor_reports/2026-11-10/01_tien_do/BAO_CAO_NGHIEN_CUU.html) có Chặng15 và bảng fresh10blocks, giữ đợt09/11. [Recovery](../research_tracking/runs/rq2-fresh-graph-recovery-20261110-01/README.md) đã đủprimary120/14400, physical121/14430 gồm replay30. K1000 có6dương/4âm, K1150 có8dương/2âm, K1300zero10 là đối chứngbất hoạt. [AKT native18](../research_tracking/runs/akt-cpu-checkpoint-current-20261110-01/README.md) và [GKT model11/trainer8](../research_tracking/runs/gkt-research-model-trainer-20261110-01/README.md) đều0FES/Job0. Publicproducerresume/CGAKTresearchfit/CUDA và suy luận thống kê vẫn còn riêng. Không chiModal.

## 10/11 — E10 nối chẩn đoán thành thạo vào bản thảo

[Bundle viết E10](../research_tracking/runs/thesis-rq1-e10-writing-20261110-01/README.md) giữ before/after, source map và prefix52432bytes nguyên.120lượt hỏi trên22khái niệm của một lịch sử được làm rõ trong technicalreport và hai fileGVHD. Không thêmN/modelcall. Fullselectedreplay RQDIAG23 giữ chưa hoàn tất nhưng xuốngP2 vì mở rộng cùng mẫu policy-chọn chưa giải quyết selectionconditioning. Ưu tiên review estimand/panel và actualRQ2recovery khiRAMđủ. Không áp dụng phương pháp mới.

## 09/11 — Chặng14 đã nghiệm thu desktop và mobile

Lượt capture mới tắt smooth scrolling trong browser, Root đã đọc hai ảnh viewport390. Bảng không đè số, không tràn ngang. WRITE06 đã đóng. [Ảnh và QA](../research_tracking/runs/supervisor-witness-mobile-qa-20261109-02/README.md) giữ nguyên bản và nguồnHTML tham chiếu. Preview/tab riêng đã đóng, không tăng mẫu nghiên cứu.

## 09/11 — AKT current cold299 đã đạt

Collection05 timeout và cleanup Job0 được giữ. Sau khi tắt preview, collection06 đạt299IDs/0body, tests06 đạt299bodies/0FES trong67,76s, peak59.211.776B/minfree2.556.534.784B. Source/runtime trước–sau khớp và ownedJob0. [Bundle kiểm](../research_tracking/runs/akt-resume-metadata-and-report-qa-20261109-01/README.md) giữ rawlogs, failures và hai screenshot gốc. Chặng14 desktop đã xem, mobile cówidth390/document375/table335 nhưng capture lệch và mấtbrowserhandle, chưa đóng WRITE06. Hai previewservers đã terminal, tab riêng không còn. GKTguard second moment âm đã áp dụng và AST, chưa native. Currentcold299 không cấp native/CUDA/GPUfit authorization.

## 09/11 — đối chiếu thành thạo và quần thể do selector chọn

[Phân tích đã xuất bản](../research_tracking/reports/rq1_on_policy_mastery_witness_20261109.md) dùng120readouts của một lịch sử.22concept được phục vụ đã đạt tiêu chí latent từfirstvisit. Cả120thetaước lượng dưới ngưỡng trên các câu policy chọn, nên cần đọc cùng selectionconditioning và initialization. Chặng14 đã cập nhật trong hai fileGVHD,11SVG nguyên byte. StaticQA đạt, visualQA còn chờ.

## Cập nhật 09/11 — phép xác nhận RQ2 mới đang dở dang

[Trạng thái phép kiểm mới](../research_tracking/reports/rq2_fresh_replication_readiness_20261109.md) ghi nhận 61/120 ca hoàn tất và 30 tương tác của ca tiếp theo trước khi dừng do RAM trống hệ thống. [Bundle failure](../research_tracking/runs/rq2-fresh-graph-source-attempt02-20261109-01/README.md) giữ 39 đầu ra nhỏ và tham chiếu 72 file gốc. Chưa nghiệm thu toàn bộ 120 ca hoặc bổ sung kết luận chính từ tập con này.

[Probe bộ đo RAM](../research_tracking/runs/owned-job-family-query-engineering-20261109-01/README.md) đã kiểm sáu lần lấy mẫu toàn bộ owned Job và đóng 15 đầu ra. GKT model/trainer đã áp dụng ở mức kiểm cú pháp, kiểm mô hình thật còn chờ RAM trống 4 GiB. GRAPH29 resume có bản nguồn đang review, chưa áp dụng. Các mốc đã nghiệm thu dưới đây được giữ nguyên.

## Mốc09/11 — learned graph trong đối chứng năng lực đã có kết quả

[E9 bản thảo luận văn](../research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md) đã xuất bản từ learned19, giữ43.799bytes E1–E8. [Writing11](../research_tracking/runs/thesis-rq1-e9-writing-20261109-01/README.md) giữ before/after và map112nguồn, Root kiểm66JSONpointers/hai phép cộng. Viết không thêm model call hoặc mẫu độc lập.

[Phân tích nguồn đồ thị](../research_tracking/reports/rq2_learned_graph_source_ability_results_20261109.md) / [bundle32](../research_tracking/runs/rq2-learned-graph-ability-20261109-01/README.md). Đã nghiệm thu19worlds,2280adaptive updates,18Q/9K và exact sentinel trước18ca mới. Cả18cặp đổi chuỗi bài,1409/2160vị trí khác câu hỏi. Khi cơ chế thiếu tiên quyết bất hoạt ở mức1300, K bằng0 nhưng Q khác0 và đổi dấu theo block. Kết quả tách thêm đường tác động ngoài cơ chế phạt. Ba block dùng lại/newN0 và initial-source reconstruction là giới hạn bắt buộc, chưa hoàn tất RQ.

[Bản GVHD Chặng13](../research_tracking/supervisor_reports/2026-11-09/01_tien_do/BAO_CAO_NGHIEN_CUU.html) đã cập nhật hai file. [Hồ sơ QA27](../research_tracking/runs/supervisor-learned-graph-update-20261109-01/README.md) giữ before/after, screenshot gốc và lỗi preview.11SVG cũ nguyên byte, bảng mới có nhóm mobile. Root đã xem desktop và component bảng mobile, đo full-document sizing, đóng tab/server do agent mở. Kiểm trình bày không tăng mẫu nghiên cứu.

## Mốc09/11 — AKT metadata hiện hành221 và38 đã đạt

[MainC221](../research_tracking/reports/akt_main_cuda_metadata_readiness_20261109.md) và [checkpointB38](../research_tracking/reports/akt_cuda_checkpoint_metadata_readiness_20261109.md) đã có actual JUnit0FES, nguồn/runtime trước–sau ổn định và owned cleanup. Hai bundle giữ78 và47outputs, gồm cả failure trước đó. Đây là kiểm hợp đồng phần mềm với opaque fixtures, chưa là chạy mô hình hoặc CUDA. Mốc này thay trạng thái MainC chưa đạt ở các bản ghi lịch sử dưới đây. Native CPU theo nguồn hiện hành cần RAM4GiB trước launch, current Gate vẫn stale, full producer resume còn thiếu.

[Recipe GKT29](thesis_recovery/29_GKT_RESEARCH_NUMERICAL_RECIPE_V1.md) được chốt trước fit theo D42, giữ batch normalization và dropout cùng các khác biệt batch4/full-prefix được công bố. Data bridge đã kiểm20ca, model candidate đang review source và chưa native. Required baselines tiếp tục giữ đủ theo đề cương.

## Mốc09/11 — GKT data bridge20ca, E8 đã xuất bản, MainC11–13 chưa có test PASS

[GKT data bridge](../research_tracking/reports/gkt_research_data_readiness_20261109.md) / [bundle58](../research_tracking/runs/gkt-research-data-engineering-20261109-01/README.md). Canonical data/lazy initializer đã áp dụng, normal import20/0FES (17data+3package); giữ01fixtureERROR và02PASS riêng. Chưa research28 model/trainer/checkpoint/export/adaptor hoặc fitted baseline. GKT08 và SAKT07 là việc chưa bắt đầu, cần ROOT review finite recipe/actual guarded producer, giữ old toy caps và đủ9model conditions.

[E8 bản thảo luận văn](../research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md) / [writing18](../research_tracking/runs/thesis-rq1-e8-writing-20261109-01/README.md). Prose mới về conditional concept-local invariance đã xuất bản, giữ35807byte E1–E7,94source/22pointers. Hai nhánh complete có cùng local stopping states dù interleaving khác; finiteH/cap2vs12 là fixture dựng tay. Writing không chạy thêm model hoặc tăngN, không RQ completion.

[MainC11–13 operational45](../research_tracking/runs/akt-main-batchc-metadata-attempts-11-13-20261109-01/README.md). Collection12/13 cùng221IDs,0bodies, không442PASS. Tests12/13NO_GO trướcchild. ROOT adopt profile metadata worker128MiB/free floor1536MiB/admission1664MiB từ review hữu hạn. Footprint08 đã đi qua221bodies nhưng168PASS/53FAIL, chưa footprint của221PASS. Giữ nguyên native/GPU floors, Gate STALE/MainC chưaverified/nativepending, không tựretry hoặc fit grant.

[Raw Git proof119](thesis_recovery/evidence/figure_lineage_mainc0610_raw_git_20261109.json) và [Raw Git proof84](thesis_recovery/evidence/gkt_data_e8_raw_git_20261109.json). Hai proof actual cho6141+119+84=6344, latest verified0c4ad897. 84paths gồm78bundle files và6canonical ở GKT/E8, là kiểm lưu trữ, không tăngN hoặc RQ%. MainC45 chưa cộngrawGit. Các source closures tiếp tục tách mức với bằng chứng khoa học. Goal ACTIVE, không chi cloud/Holdout mới. Các mốc cũ bên dưới giữ nguyên theo thời điểm.

## Bổ sung09/11 — lưu figure có nguồn và hồ sơ MainC06–10

[11SVG độc lập](../research_tracking/runs/supervisor-figures-20261109-01/figure_index.md) đi cùng [Nguồn số liệu và mã dựng hình](../research_tracking/runs/supervisor-figure-data-lineage-20261109-01/README.md). Đã kiểm27nguồn,54giá trị biểu đồ và11SVG nguyên byte; giữ năm phiên bản mã dựng. Đây là kiểm lưu trữ và nguồn số liệu. Khả năng dựng lại trọn vẹn vẫn chưa kiểm.

[Hồ sơ MainC06–10](../research_tracking/reports/akt_main_batchc_metadata_attempts_06_10_20261109.md) giữ98outputs gồm lỗi và các lượt dừng. Collection10 đã kiểm warmup thật, nhưng tests10 chưa khởi động vì RAM. MainC chưa nghiệm thu đầy đủ, Gate hiện hành vẫn stale. Các mốc dưới đây là diễn tiến lịch sử.

## Mốc09/11 — Paper1 có proof điều kiện; MainC8 đã áp dụng, kiểm còn pending

[Proof Paper1](../research_tracking/reports/paper1_concept_local_invariance_20261109.md) và [bundle17](../research_tracking/runs/paper1-concept-local-invariance-20261109-01/README.md). Khi cùng bank/init/local tape và update concept-local, nếu cả hai DAG branches hoàn thành thì local stopping counts, terminal states và tổng feedback giống nhau; order/re-entry có thể khác. Actual91tests/0FES gồm6fixture mới kiểm cả wrongY/finiteH/cap/no-cap. 13episodes/464feedback là trần tĩnh, không measuredledger hoặc sample nghiên cứu.

[Witness domain28](../research_tracking/reports/paper1_seeded_domain_smoke_readiness_20261109.md) và [bundle28](../research_tracking/runs/paper1-seeded-domain-smoke-engineering-20261109-01/README.md) là operation riêng, một US42/twoepisodes/344feedback,172mỗi branch, estimated28/28/reentry0vs2 và cùng latent cuối. Không matrix, historical-draw reproduction hoặc graph efficacy.

[MainC01–05](../research_tracking/reports/akt_main_batchc_metadata_attempts_20261109.md) và [bundle65](../research_tracking/runs/akt-main-batchc-metadata-attempts-20261109-01/README.md) giữ failures sau khi MainC8 đã áp dụng.01–04 chưa tới test body, countsNULL;05NO_GO trướclaunch, chưa child/Job. Đây là snapshot lịch sử. Tiếp theo collection07/08 đã accepted cùng221IDs. Tests07chạy85bodies rồi harness Path.open collision, JUnit86cases/0failures/1internalerror. Tests08chạy đủ221bodies,168PASS/53FAIL/0error/0skip; ROOT đối chiếu cả53trace đi qua inspect_runtime→platform.platform→_syscmd_ver→NUL bị harness chặn. Không kết luận53production defects hoặc MainC đã verified. Warmup platform09 mới chuẩn bị, 09NO_GO RAM trướclaunch nên chưa runtime kiểm. Metadata/native/CUDA pending, current Gate STALE. [backlog](thesis_recovery/TASKS.json) thêm GRAPH29 cho complete-epoch producer resume, hiện FEATURE_GAP/NOT_STARTED. Lowlevel checkpoint đã có counters/RNG/modes; public producer vẫn fresh-output và resume_supported=False. Không bịa loader RNG cho deterministic iterator, không fit/GPU grant từ contract.

Bản đọc GVHD hiện có Chặng12, giữ11SVG/11bảng, [QA Chặng12](../research_tracking/runs/supervisor-concept-local-update-20261109-01/README.md) đã đóng28outputs. ROOT đã xem desktop1280/mobile390 và đóng tab riêng, không preview server/request mới; QA trình bày không tăng researchN. Các mốc cũ bên dưới giữ nguyên theo thời điểm. Counter5999/latest117b giữ nguyên chờ ROOT raw-Git verify các bundle mới.

Đối chiếu ngày07/11/2026 từ cây thư mục, entrypoints trong `src/`/`scripts/`, README và manifest hiện có. Tài liệu này là điểm bắt đầu để tìm nội dung; không thay thế protocol hoặc kết quả gốc. Không di chuyển/xóa artifact trong lần lập mục lục này.

## Khi viết báo cáo, mở gì trước?

**Để xem tiến độ với GVHD:** mở [báo cáo theo ngày](../research_tracking/supervisor_reports/README.md). Bản hiện hành09/11 giữ đúng một bản tóm tắt và một HTML độc lập với mười một biểu đồ; đi từ ngữ cảnh hai paper qua tiến độ và diễn tiến nghiên cứu đến phần chưa chứng minh. Bản08/11 và notebook trước chuyển đổi được bảo toàn trong lịch sử. `research_tracking/reports/` tiếp tục giữ phân tích chuyên sâu; `runs/` giữ bằng chứng gốc.

| Cần viết/kiểm tra | Đọc bản diễn giải | Đối chiếu bằng chứng gốc |
|---|---|---|
| Kết quả baseline BKT | [BKT results](bkt-baseline-results.md) | [BKT Development CV](../experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/); vị trí refit/Test lịch sử xem README của [BKT experiments](../experiments/bkt_baseline/README.md) |
| So sánh BKT–GAM-KT | [Bản ngắn](bkt-gam-kt-benchmark.md), [bản nghiên cứu chi tiết](research/bkt-gam-kt-baseline-benchmark-report.md) | [BKT CV](../experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json), [GAM CV](../experiments/gam_kt/results/wsl_cpp/cv/cv.json), [bootstrap JSON](../research_tracking/reports/paired_cluster_bootstrap_bkt_gam.json) |
| RQ1/RQ2: prediction → decision, graph package, retention/re-entry | [Chẩn đoán nguồn](../research_tracking/reports/cpu_rq12_20261107.md), [factorial/pilot](../research_tracking/reports/cpu_pilots_20261107.md) | [Các run CPU](../research_tracking/runs/); đặc biệt [factorial](../research_tracking/runs/cpu-factorial-20261107-01/) và [closed-loop diagnostic](../research_tracking/runs/cpu-closedloop-20261107-01/) |
| RQ2: thứ tự Junyi và graph controls | [Matched controls](../research_tracking/reports/cpu_matched_controls_20261107.md), [common population](../research_tracking/reports/cpu_common_population_20261107.md) | [Cohort mở rộng](../research_tracking/runs/cpu-junyi-controls-20261107-02-expanded/), [common-population run](../research_tracking/runs/cpu-junyi-common-20261107-01/) |
| Kỹ thuật AKT: recovery, simulator interface, batching | [Recovery log](thesis_recovery/17_AKT_RECOVERY_ENGINEERING_LOG.md), [báo cáo interface](../research_tracking/reports/simulator_kt_interface_20261107.md) | [Recovery proof](../research_tracking/runs/cpu-akt-recovery-20261107-01/), [interface/batch gate](../research_tracking/runs/cpu-sim-kt-batch-gate-20261107-01/) |
| Collector/KT simulator và semantic domain | [DATA05–07](../research_tracking/reports/simulator_collection_runner_20261107.md), [hợp đồng](thesis_recovery/19_SIMULATOR_DATA_AND_GRAPH_BOUNDARIES.md) | [Gate401/source/parity](../research_tracking/runs/cpu-sim-collector-gate-20261107-01/) — engineering fixture, chưa full corpus/trainer |
| Colab GPU trong VS Code | [Notebook một file](../notebooks/akt_colab_synthetic.ipynb), [hướng dẫn](akt-colab-synthetic-runbook.md) | Nhúng kitv11, không upload nguồn; kiểm local/mock, chưa actual GPU |
| Modal, credentials local và ngân sách30USD/tháng | [Hướng dẫn kết nối](akt-modal-setup.md), [costplan](thesis_recovery/07_GPU_TRAINING_AND_COST_PLAN.md) | [Local SDK proof](../research_tracking/runs/cpu-modal-client-20261107-01/) — chưa auth/GPU/cloudspend |
| Đề cương/RQ, kế hoạch và phần còn thiếu | [Truy vết yêu cầu](thesis_recovery/02_RESEARCH_TRACEABILITY.md), [experiment matrix](thesis_recovery/05_EXPERIMENT_MATRIX.md), [backlog](thesis_recovery/TASKS.json) | Đây là quản lý/thiết kế nghiên cứu; không dùng làm bằng chứng một thí nghiệm đã thành công |
| CG-AKT: thiết kế hiện hành để triển khai | [Recipe26 đã chọn](thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md), giữ [draft25](thesis_recovery/25_MINIMAL_GRAPH_AKT_RESEARCH_RECIPE_DRAFT.md) để đối chiếu | Quyết định nhóm về per-edge confidence/gate; chưa model fitted hoặc quyền chi GPU |

Baseline prediction, pilot chẩn đoán và kiểm thử phần mềm là ba loại bằng chứng khác nhau. Các tests AKT hoặc fixture train168targets không chứng minh CG-AKT cải thiện học tập. Các phân tích Junyi order chưa chứng minh lợi ích nhân quả của graph. Chưa có báo cáo kết quả đầy đủ trả lời cả ba RQ hoặc bản luận văn hoàn chỉnh trong những đường dẫn này.

Các báo cáo có ngày cũ là snapshot lịch sử. Ví dụ bản benchmark30/10 từng ghi chưa tìm thấy proposal; điều đó không mô tả inventory hiện tại. Dùng tài liệu truy vết yêu cầu ở trên cho phạm vi KLTN hiện hành, không lấy mục tiêu baseline trong `_context/` làm toàn bộ đề tài.

## Vai trò của từng thư mục

| Thư mục | Lưu gì? | Còn dùng không? |
|---|---|---|
| `research_tracking/` | Chỉ mục tiến độ, claim→evidence, hạn chế khoa học, diễn giải các đợt nghiên cứu và bundles bằng chứng | **Đang dùng**; điểm tra cứu nghiên cứu hiện hành |
| `research_tracking/reports/` | Markdown phân tích/audit theo chủ đề, JSON kiểm integrity/coverage/portability và một số draft protocol | **Đang dùng**; không phải mọi file là kết quả thực nghiệm hoặc chương luận văn |
| `research_tracking/runs/` | Một thư mục/run ID: README, manifest, log, kết quả nhỏ và SHA của nguồn/outputs | **Đang dùng**; bằng chứng có thể đối chiếu khi viết; có cả pilot, replay, reconstruction và archive kiểm thử |
| `reports/` ở gốc — vị trí cũ | Đã chuyển JSON bootstrap vào research_tracking/reports; folder cũ đã bỏ sau khi rỗng | Xem [relocation manifest](../research_tracking/reports/report_relocation_20261107.json); không tạo lại |
| `docs/` | Hướng dẫn chạy, protocol/data semantics, provenance, báo cáo baseline và thiết kế | **Đang dùng**; phần viết cho người đọc, không phải toàn bộ là kết quả |
| `docs/thesis_recovery/` | Kế hoạch tổng thể, audit, kiến trúc, quyết định, backlog và state để tiếp tục engineering/research | **Đang dùng**; phương án đề xuất không tự thành methodology đã được duyệt |
| `docs/thesis_recovery/evidence/` | Bản trích tài liệu/audit và các log kiểm kỹ thuật từ quá trình điều tra | **Giữ lịch sử**; với đợt đã đóng gói, ưu tiên trích run bundle có manifest thay vì tìm giữa mọi log rời |
| `_context/` | Mục tiêu, quyết định và evaluation protocol của **baseline BKT ban đầu** | **Còn giá trị tham chiếu/ràng buộc BKT**; không là dashboard hoặc protocol chung mới cho RQ1–RQ3 |
| `artifacts/` | Dữ liệu phái sinh/splits, sidecar, source phụ thuộc, runtime/gate evidence, kit Colab, cùng cache/temp | **Đang được code sử dụng**; không thể coi toàn bộ là cache để xóa |
| `experiments/` | Config/authorization và kết quả đầy đủ theo model/run: metrics, models, checkpoints, predictions, logs | **Đang dùng**; nhiều kết quả gốc nằm ở đây, phần lớn giữ local |
| `notebooks/` | Notebook kiểm synthetic CPU/CUDA và [notebook báo cáo bằng chứng](../notebooks/thesis_evidence_report.ipynb) | **Đang dùng cho runtime và trình bày kết quả đã lưu**; notebook báo cáo là chẩn đoán/pilot RQ1–RQ2, chưa kết quả cuối của cả luận văn |
| `scripts/` | Entry points chạy/audit/build/verify; xem nhóm bên dưới | **Đang dùng**; script không tự là kết quả đã chạy |
| `src/` và `tests/` | Implementation và kiểm thử tương ứng | **Đang dùng**; kết quả test cần log/manifest đi kèm |
| `paper1/`, `paper2/` | Source/artifacts/PDF từ nghiên cứu trước; một số notebook và simulator inputs vẫn là dependency của adapter/audit | **Đang được tái sử dụng**; không chuyển cả hai sang archive hoặc chỉnh source lịch sử |
| `ref-papers/` | Tài liệu tham khảo | Tham chiếu học thuật, không phải kết quả của nhóm |
| `third_party/` | Dependency vendored, gồm pyBKT đã vá và provenance/license | Dependency, không phải dữ liệu hoặc báo cáo |

Không có cơ sở để bỏ nguyên một trong sáu thư mục `_context`, `artifacts`, `experiments`, `notebooks`, `scripts`, `research_tracking`. Việc chỉ dùng ở giai đoạn tái lập/historical cũng là một vai trò cần giữ.

## Những chỗ trong artifacts đang quan trọng

| Đường dẫn | Công dụng đã đối chiếu |
|---|---|
| [artifacts/bkt_baseline/derived/canonical](../artifacts/bkt_baseline/derived/canonical/) | Interaction data đã xử lý; được pipeline KT/diagnostic dùng làm đầu vào |
| [artifacts/bkt_baseline/splits](../artifacts/bkt_baseline/splits/) | Learner assignments/split identity dùng chung; không tự chia lại hoặc xóa |
| [artifacts/gam_kt/derived/source_map](../artifacts/gam_kt/derived/source_map/) | Sidecar phục vụ GAM-KT và đối chiếu lineage |
| [artifacts/akt/dependencies/upstream](../artifacts/akt/dependencies/upstream/) | Source AKT ghim commit, được wrapper load trực tiếp; không là cache tải xuống có thể bỏ tùy ý |
| [artifacts/akt/preflight](../artifacts/akt/preflight/) | Runtime/source/software gate reports và logs. `gate2-current.json` trỏ evidence hiện hành, phải kiểm cả hashes trước execution |
| [artifacts/akt/colab](../artifacts/akt/colab/) | Các kit ZIP source/fixture và kiểm portability; build ZIP không đồng nghĩa đã chạy Colab |
| [artifacts/akt/local-tests](../artifacts/akt/local-tests/), [tmp](../artifacts/akt/tmp/), [pip-cache](../artifacts/akt/pip-cache/) | File làm việc/test/cache; ứng viên dọn có kiểm soát **sau** khi xác định file cần tái lập và đã lưu inventory/evidence |

Một số kết quả BKT đã được relocation sang `experiments/bkt_baseline/results/wsl_cpp/`. Vì vậy không lấy tên `artifacts/` để suy rằng mọi kết quả BKT chính thức đều còn ở đó. Xem [relocation summary](../experiments/bkt_baseline/relocation_summary.json); không di chuyển lần nữa chỉ để đồng nhất tên thư mục.

## Scripts và notebooks được dùng ở đâu?

- [scripts/research](../scripts/research/): source/simulator diagnostics, bounded CPU pilots, Junyi controls và simulator–KT interface fixture.
- [scripts/akt](../scripts/akt/): kiểm runtime, refresh Gate2, đóng gói source Colab và synthetic device probe.
- [scripts/wsl2](../scripts/wsl2/): runner/reproduction của BKT C++ trên WSL. Có script đánh giá Test lịch sử; không chạy lại chỉ để xem báo cáo.
- [scripts/bootstrap_bkt_gam_cv.py](../scripts/bootstrap_bkt_gam_cv.py): thống kê paired learner bootstrap trên predictions Development đã lưu; JSON bootstrap đã lưu tại research_tracking/reports. Script nhận `--output`; lần tái lập mới cần output riêng, không ghi đè JSON lịch sử hoặc tạo lại root reports.
- [notebooks/akt_colab_synthetic.ipynb](../notebooks/akt_colab_synthetic.ipynb): giao diện chạy kiểm trên Colab; log/outputs sau execution mới là bằng chứng. Notebook nguồn Paper1/2 nằm trong hai thư mục paper riêng, không phải root `notebooks/`.
- [notebooks/thesis_evidence_report.ipynb](../notebooks/thesis_evidence_report.ipynb): bảng/sơ đồ cơ chế và nguồn C01–C14 từ artifact đã đóng, có outputs và kiểm28inputs/104pointers. Builder stdlib chỉ đọc bằng chứng; không rerun research. Chưa Jupyter-kernel/visual QA; xem [nghiệm thu](../research_tracking/reports/thesis_evidence_notebook_20261108.md).
  Bản working đã có [bổ sung single-payload integrity](../research_tracking/reports/thesis_evidence_notebook_integrity_20261108.md); snapshot v1 và v2 giữ riêng trong bundles, số liệu không đổi.

Một số script nằm bên trong run archives là bản lịch sử, có thể chứa đường dẫn cũ. Ưu tiên entrypoints tại `scripts/` và runbook hiện hành, không tự chạy script bất kỳ trong folder kết quả.

## Đọc một bundle và trích vào KLTN

Ví dụ [cpu-junyi-common-20261107-01](../research_tracking/runs/cpu-junyi-common-20261107-01/):

1. Đọc `README.md` để biết câu hỏi, dữ liệu, phạm vi và giới hạn.
2. Đọc `manifest.json` để lấy run ID, loại run, nguồn/input SHA và outputs SHA.
3. Đọc `common_population.json` để đối chiếu số liệu; đọc [báo cáo diễn giải](../research_tracking/reports/cpu_common_population_20261107.md) để hiểu estimand/coverage.
4. Khi viết: dẫn bảng/kết luận của báo cáo, ghi run ID và phiên bản/source hash trong phụ lục tái lập. Không đưa mọi debug log vào thân luận văn.

Ví dụ câu diễn giải phù hợp: “Trong pilot giới hạn này, graph controls chỉ thay đổi prior-order score của một số ít learner; kết quả chưa đủ kết luận graph trung tính.” Không đổi thành “graph không giúp học” vì pilot này không đo causal instructional benefit.

`runs/` hiện có20bundles với196outputs được kiểm hash trong Git tại [báo cáo kiểm chứng](../research_tracking/reports/git_evidence_verification_simulator_20261107.json). Đây **không phải20thí nghiệm khoa học độc lập**: có replay, phiên bản kiểm thử và archive. Trạng thái `completed` không tự chứng minh giả thuyết nghiên cứu đúng. Số lượng là snapshot ngày07/11, không phải chỉ tiêu hoàn thành.

## Quy ước lưu tiếp theo

- Bản phân tích/bảng diễn giải mới: `research_tracking/reports/`; cập nhật [mục lục phân loại](../research_tracking/reports/README.md).
- Bằng chứng một lượt chạy nhỏ: `research_tracking/runs/<run-id>/`, có README/manifest/hash; run cũ giữ bất biến.
- Models/checkpoints/predictions/logs lớn: output theo run trong `experiments/<model>/results/`; bundle chỉ tham chiếu đường dẫn/hash và kết quả nhỏ cần review.
- Đầu vào phái sinh, source phụ thuộc và runtime working files: `artifacts/<model>/` theo vai trò rõ ràng.
- Protocol/runbook/thiết kế: `docs/`; kế hoạch và state liên tục của đợt recovery ở `docs/thesis_recovery/`.
- Không mở thêm các thư mục top-level kiểu `reports_new`, `results_latest` hoặc `final_v2` để lưu cùng loại nội dung. Root reports đã được hợp nhất; quy ước này cũng được ghi trong AGENTS.md để các vòng engineering tiếp theo duy trì.

## Thư mục môi trường/công cụ

`.venv/` là Python environment đang sử dụng. `venv/`, `dataset/`, `artifacts/bkt_baseline/` và `.wsl/JunyiBKT-Ubuntu/` là các vùng được AGENTS bảo vệ; không dọn khi chưa có yêu cầu rõ. `.pytest_cache/`/`__pycache__/` là cache, không là evidence. `.superpowers/` là metadata công cụ hỗ trợ; `docs/superpowers/` giữ specs/plans của các giai đoạn trước. Không dùng những kế hoạch đó thay thế [backlog hiện hành](thesis_recovery/TASKS.json). Đây không phải một đợt kiểm toán để xác nhận mọi file cache hoặc metadata đều có thể xóa.

Nguồn đối chiếu chính: [AKT config](../src/knowledge_tracing/akt/config.py), [authorization](../src/knowledge_tracing/akt/authorization.py), [GAM runner](../src/knowledge_tracing/gam_kt/runner.py), [Paper2 reference loader](../src/knowledge_tracing/paper2_reference.py), các README experiments và manifests trong research_tracking/runs. Chỉ kiểm mục lục/nguồn và báo cáo đã lưu; không chạy lại thí nghiệm hoặc mở prediction-level Holdout trong lần này.

## Đợt sắp xếp07/11

Chỉ di chuyển JSON bootstrap về nơi thống nhất, cập nhật locator/index, ghi quy ước trong AGENTS và bỏ root reports sau khi xác nhận rỗng. .pytest_cache giữ nguyên vì quyền truy cập bị chặn, chưa xác minh nội dung; không thay ACL hoặc retry xóa. Trước/sau có inventory SHA; nội dung thống kê và bundles/manifests/models/predictions cũ giữ nguyên. Không dọn artifacts/akt/local-tests hoặc tmp vì một số file còn được evidence/resume inventory tham chiếu.

## Điểm vào mới sau batch CPU/CUDA07/11

- [AKT actual CUDA acceptance](../research_tracking/reports/colab_cuda_acceptance_20261107.md) và [phản biện GPU](../research_tracking/reports/colab_cuda_adversarial_review_20261107.md): CPU505pass, synthetic400target lifecycle và fresh-process recovery; chưa full training/Gate4. Checkpoint/binary giữ tại `experiments/akt/results/colab-actual-cuda-20261107-01/`, summaries/logs/SHA trong run bundle theo chỉ mục.
- [RQ1/RQ2 synthesis](../research_tracking/reports/rq12_evidence_synthesis_20261107.md) và [factorial uncertainty](../research_tracking/reports/factorial_pilot_uncertainty_20261107.md): tổng hợp aggregates/exploratory post-hoc, không rerun toàn paper hoặc confirmatory efficacy.
- [Paper1 revision reconciliation](../research_tracking/reports/paper1_revision_reconciliation_20261107.md): exact source revision chưa tìm thấy trong phạm vi local; không sửa lịch sử để ép khớp PDF.
- [Graph kernel](../src/knowledge_tracing/graph_augmentation.py) cùng [báo cáo](../research_tracking/reports/graph_gate_prototype_20261107.md): độc lập, chưa CG-AKT trained. [SAKT core](../src/knowledge_tracing/sakt/) cùng [readiness](../research_tracking/reports/sakt_core_readiness_20261107.md):37CPUtests, chưa trainer/benchmark; không nằm trong kitv12/Gate15.

Các mục count/inventory phía trên là snapshots có ngày, không tự cập nhật khi thêm run. Current deliverable status ở `research_tracking/RESEARCH_PROGRESS.md` và `docs/thesis_recovery/INVESTIGATION_STATE.json`; run manifests đã đóng luôn bất biến.

## Runtime/worker batch tiếp theo

[Hợp đồng20](thesis_recovery/20_LINUX_CUDA_WORKER_CONTRACT.md), [runtime report](../research_tracking/reports/akt_linux_runtime_contract_20261107.md), [worker report](../research_tracking/reports/akt_main_worker_lifecycle_20261107.md) và [SAKT inference report](../research_tracking/reports/sakt_adapter_readiness_20261107.md) là các điểm vào mới. Logs/failures/source snapshots nằm trong ba run có tên theo mục đích ở EVIDENCE_INDEX; không tạo thêm root reports hoặc chuyển historical artifacts. Gate17 nativeCPU513cases và SAKT89cases là suites riêng; Linux/CUDA main-worker execution chưa được xác nhận.

## Báo cáo GVHD hiện hành09/11

Mở [tóm tắt GVHD](../research_tracking/supervisor_reports/2026-11-09/01_tien_do/BAO_CAO.md) và [báo cáo minh họa](../research_tracking/supervisor_reports/2026-11-09/01_tien_do/BAO_CAO_NGHIEN_CUU.html). Báo cáo đi từ ngữ cảnh hai paper qua tiến độ và mười một chặng đến phần còn phải chứng minh. Chặng mới nhất giải thích30thời điểm khác nhãn thành thạo mà giữ tập sẵn sàng ban đầu, giữ rõ các điều kiện chồng lấp. Các chặng trước kiểm điểm tổng hợp trên cùng dòng dữ liệu và điều kiện không quay lại chương. Mỗi ngày giữ đúng hai file đọc, còn log và hồ sơ kiểm chứng dùng các chỉ mục bằng chứng. [RQ1 transitions](../research_tracking/reports/rq1_transition_evidence_20261108.md), [RQ1 cross-ready](../research_tracking/reports/rq1_cross_ready_membership_20261109.md) và [RQ2 conditions](../research_tracking/reports/rq2_conditions_evidence_20261108.md) có scripts tái tính và bundles theo run.

## Điểm vào engineering08/11

[Context CPU acceptance](../research_tracking/reports/akt_worker_context_readiness_20261108.md), [GKT partial kernel](../research_tracking/reports/gkt_core_readiness_20261108.md), [demo read-only](../research_tracking/reports/demo_readiness_20261108.md) và [bản thảo phương pháp](../research_tracking/reports/THESIS_METHODS_RQ12_DRAFT_20261108.md) dùng cấu trúc hiện hành. Source demo ở src/research_demo, không thêm top-level app/results folder. Bundles mới giữ raw logs/source/receipts; checkpoint/prediction lớn của CPU toy run giữ experiments/akt/results/ctx0801, scratch/dependency metadata ở artifacts/akt. Không dọn hoặc di chuyển protected/historical paths.


## Mô phỏng theo PDF Paper1

`src/knowledge_tracing/paper1_pdf/` giữ các quy tắc world/Elo/controller phiên bản riêng theo PDF chuẩn. `tests/paper1_pdf/` kiểm bằng fixture dựng tay. `domain.py` đọc bộ CSV ứng viên đã pin, giữ metadata đầu vào và tách chapter keys ngoài domain. Source Paper1 lịch sử giữ nguyên. [Phạm vi đã kiểm và phần còn thiếu](../research_tracking/reports/paper1_pdf_primitives_readiness_20261109.md).

`episode.py` nối profile US/UW/FW với controller/world và tape cấp sẵn, có trace observable/oracle riêng và horizon tối đa500. Mốc supplied core đạt72ca, gồm18episode cases. [Readiness lịch sử](../research_tracking/reports/paper1_supplied_episode_readiness_20261109.md). Bộ kiểm hiện hành sau seeded runner đạt85ca, còn matrix policy nghiên cứu chưa chạy.

## Chuẩn bị CUDA cho core nghiên cứu

Profile có phiên bản nằm trong [quyết định28](thesis_recovery/28_CUDA_EXECUTION_PROFILE_V1.md). Source tiếp tục ở `src/knowledge_tracing/akt/`, bằng chứng metadata/CPU của batchA dùng [report](../research_tracking/reports/cgakt_cuda_core_cpu_readiness_20261109.md) và bundle theo run. Checkpoint CUDA schema2, Main wiring và các lượt kiểm trên GPU thực tế được theo dõi riêng trong kế hoạch GPU.

### Bổ sung RNG-owned Paper1 ngày09/11

[Seeded episode](../src/knowledge_tracing/paper1_pdf/seeded_episode.py) tái dùng supplied core, có85tests/13ca mới. [Báo cáo](../research_tracking/reports/paper1_seeded_episode_readiness_20261109.md) và [bundle](../research_tracking/runs/paper1-seeded-episode-engineering-20261109-01/) giữ raw và provenance. Chưa chạy matrix nghiên cứu.

## Figure phục vụ luận văn

[Mục lục11SVG độc lập](../research_tracking/runs/supervisor-figures-20261109-01/figure_index.md) giữ hình nguyên byte từ bản HTML đã QA, kèm chú thích và nguồn xuất. Đây là bộ hình của snapshot chặng11. Các figure mới hoặc sửa tiếp tục lưu phiên bản theo run, cùng dữ liệu hoặc tham chiếu số liệu và cách dựng. Ảnh chụp gốc giữ trong bundle QA, không render hoặc copy lại vào mọi bộ hình.

### Prospective domain28 đã kiểm tích hợp

[Báo cáo](../research_tracking/reports/paper1_seeded_domain_smoke_readiness_20261109.md) và [bundle28](../research_tracking/runs/paper1-seeded-domain-smoke-engineering-20261109-01/README.md) giữ actual hai episode US/seed42. Output gốc ở experiments/simulator/results theo [vai trò](../experiments/simulator/README.md). Đã có344feedback,172mỗi nhánh, không matrix nghiên cứu hoặc suy ưu thế graph.

## 10/11 — bất định theo mười block RQ2

[Phân tích thăm dò](../research_tracking/reports/rq2_fresh_block_uncertainty_20261110.md) giữ đúng mười block, ba so sánh và10.000 shared draws. KhoảngK1150 phía dương, nhưng khoảng hiệuK1150−K1000 chứa0 nên chưa tách rõ khác biệt giữa hai mức khởi tạo. [Bundle](../research_tracking/runs/rq2-fresh-block-uncertainty-20261110-01/README.md) giữ CSV và kiểm Decimal độc lập. Phân tích hậu nghiệm, mức bao phủ xấp xỉ và một learned graph cố định. Hai báo cáo đã có Chặng16,11SVG cũ nguyên byte, bảng15 đạt desktop/mobile. Không thêm world/modelcall hoặc chi Modal.

## 10/11 — source producer và dữ liệu main đã kiểm rõ phạm vi

[Cold62](../research_tracking/runs/neural-selected-producer-metadata62-20261110-01/README.md) gồm35SAKT/27GKT,0FES, khôngNN. GKT đã có selected producer source, còn nativepositive. SAKT sửa mandatorypackageinit sau lỗi trướcconstructor, không thay toán học. [Corpus60](../research_tracking/runs/simulator-main60-data-preflight-20261110-01/README.md) đạt learnerdisjoint48/6/6 vàwindowcoverage10080/1260, chưa throughputGPU. [F041](../research_tracking/runs/rq1-f041-native-panel-20261110-01/README.md) có3360readouts toàn28concept, một lịch sử thấp đềuTN và0positiveclass, chưa đánh giá được nhận diện thành thạo. Không đóngRQ hoặc dùng Modal.

## 10/11 — tập đích chuẩn trước so sánh mô hình

Module src/knowledge_tracing/research_population.py đã tích hợp và kiểm sáu tests cùng tập selection Main1260targets/6learners. Hash84targets engineering khớp export A0. Bundle research_tracking/runs/main-selection-population-integration-20261110-01 giữ cả lỗi driver và candidate IO chưa đạt. Build185 cần refresh Gate; Gate183/1913 là snapshot đã nghiệm thu trước thay đổi này. Chưa chọn winner hoặc cấp quyền refit.

## 10/11 — đọc artifact cho selector

src/knowledge_tracing/research_selection_io.py cung cấp FileRef, giới hạn đọc, JSON/CSV nghiêm ngặt và offset index.10tests cùng8CSV đã đạt, xem research_tracking/runs/selection-artifact-io-integration-20261110-01. Đây chưa là external freeze; build187 cần refresh Gate.

## 12/11 — nghiệm thu phục hồi Junyi và đường dự đoán chính

[Hồ sơ chẩn đoán](../research_tracking/runs/junyi-numerical-diagnostic-20261112-01/README.md) giữ checkpoint và đối chiếu CUDA liên tục/phục hồi đạt, nguồn CPU04 đạt 2.218 ca. Batch prediction vượt ngưỡng nên producer chính dùng đường tuần tự. Full cache TRAIN80 đã tạo, full neural fit Junyi còn phải thực hiện. Ledger COMPUTE_BUDGET.json ghi trần 30 USD cho toàn KLTN.
