# Pipeline refit A0–A3 trên Junyi

## Phạm vi

Tiếp nối hồ sơ selected-fit đã niêm phong tại `../junyi-a3-selected-20261114-01/`. Đợt này hoàn thiện đường refit trên TRAIN90, giữ epoch9 của từng biến thể, seed42 và cùng recipe batch128. Confidence và topology tiếp tục giữ bản fit TRAIN80 theo Recipe26. Encoding và cache refit được dựng riêng từ hợp train/selection. Calibration và outer evaluation giữ ngoài tập tối ưu neural.

Epoch plan đóng băng số epoch của nhóm bốn biến thể expert trên fold4. Mỗi biến thể tiếp tục có kết quả riêng để so sánh. Plan giữ trạng thái chưa chọn mô hình thắng chung của hệ thống. Các baseline, learned-graph và thí nghiệm khác trong đề cương tiếp tục được theo dõi ở TASKS.

## Cách triển khai

- Tái dùng `train_epoch`, sampler, Adam và checkpoint/RNG hiện có.
- Model refit khởi tạo mới trên encoding90. Checkpoint selected chỉ cung cấp provenance và số epoch.
- Mở phase refit/calibration của adapter đồ thị qua lineage TRAIN80 riêng, giữ confidence theo tên cạnh. Cache90 phải khớp encoding90 và phase90.
- Tách chuẩn bị encoding/window/context cache trên CPU. Entrypoint chạy thật cần grant, Gate source mới, runtime CUDA và ngân sách của lượt chạy.
- Lưu checkpoint từng epoch và checkpoint partial cùng sampler để nối lại. Mỗi tranche có giới hạn thời gian, giữ phần chưa hoàn tất.

## Tình trạng hiện tại

Đang triển khai và kiểm local. `STATE.json` là điểm tiếp tục. Chưa training refit dữ liệu thật, chưa dùng thêm Modal. Kiểm native CPU dùng fixture tổng hợp và ghi rõ phần admission CUDA được mock. CUDA/Gate trên source mới cần nghiệm thu riêng trước thuê GPU.

## Mốc kiểm local đầu tiên

`tests04.log` đạt 78 ca, gồm hồi quy graph/adapter selected và kiểm refit tổng hợp mới. Với cả A0–A3, chạy liên tục và chạy gián đoạn/nối lại cho model, Adam, RNG Python/NumPy/Torch giống hệt nhau trên CPU. Đường refit giữ đủ target từng epoch và từ chối train trên phase calibration. Có kiểm lineage confidence TRAIN80 khi encoding chuyển sang90. Các fixture admission CUDA được mock riêng, math backbone và trainer chạy native thực trên dữ liệu tổng hợp.

Giữ các lượt chưa đạt. Lượt01 thiếu PYTHONPATH khi collection. Lượt02 bị Git chặn ownership dependency. Lượt03 phát hiện source-row0 trong fixture mới và thông báo lỗi phase chưa tương thích test cũ. Đã sửa fixture sang source-row dương, giữ thông báo có train80 và dùng safe.directory chỉ cho đúng dependency trong tiến trình kiểm. Checkout upstream vẫn được verify commit/remote/content, không thay Git global.

`epoch-plan.json` cùng receipt đã kiểm trực tiếp bốn gói model trên D và xác nhận 9 epoch mỗi model. Refit gồm 142.621 người học và 14.947.674 target mỗi epoch. Tập calibration và outer fold4 giữ riêng. Cache90 và kiểm entrypoint/grant còn tiếp tục.

## Tiến độ tiếp nối sau cache CPU

- `prepared-refit-matrix.json` và `input-check-a0.json` đến `input-check-a3.json` xác nhận bốn đầu vào thật khớp. Cache90 có261.111window,14.947.674target,0OOV. Encoding90 có717exercise.
- `context-a1.receipt.json`, `context-a2.receipt.json`, `context-a3.receipt.json` ghi thời gian CPU tương ứng286,34/313,76/392,96giây, không thuê GPU. Cache lớn nằm trong `artifacts/akt/graph-context-cache/full-refit90-20261114-01/`.
- `tests08.log`60ca, `tests09.log`81ca, `tests10.log`85ca đều đạt. Các suite có chồng lặp, không cộng thành tổng test duy nhất. Native CPU tổng hợp xác nhận continuous/resume model/Adam/RNG. Admission CUDA trong fixture được mock.
- `refit-request-a*.json`/`worker-a*.json` ghim epoch/config/cache/lineage, chưa chứa grant/Gate/runtime dùng thực thi. Request mặc định chỉ kiểm khai báo. `scripts/akt/prepare_junyi_refit_stage.py` kiểm CPU và đóng snapshot. `experiments/akt/modal_junyi_refit.py` dùng lại budget guard/stop barrier của selected pipeline. `scripts/akt/run_junyi_refit_gpu_stage.py` nối runtime/grant đúng nguồn trước gọi numerical runner.
- `scripts/akt/export_junyi_refit_model.py` chỉ nhận checkpoint đã hoàn tất, kiểm model/Adam/RNG/identity/SHA rồi xuất bốn file trênD. Chưa có model refit thật để xuất.
- `linux01/` giữ nguồn/worker/controller Gate mới. `source-gate01.log` là log dispatchCPU có cap0,15USD, không GPU. Đọc STATE trước tiếp tục.

## Điểm vào thực thi kế tiếp

Sau Gate PASS và App dừng, chạy `prepare_stage_requests.py` để ghim inventory snapshot bốn biến thể. Đóng snapshot cần đủ dung lượngD, tái dùng cache; tránh tạo bốn bản cache lớn nếu chưa cần. Mỗi lượt GPU cần execution request có cap/timeouts và allocation trong ledger. Full config chừa1.600giây mỗi tranche, tự lưu partial nếu chưa đủ9epoch; nối lại cùng config và logical run, không tăng epoch đã chọn.

Trước full refit phải kiểm CUDA trên nguồn refit mới và dự toán đủ bốn biến thể cùng calibration/đánh giá. Hiệu năng selected H100 không tự động là benchmark refit. Confidence vẫn fitTRAIN80. A0 chọn epoch lịch sử bằng validationbatch1; mới replaycheckpoint9batch128, ranking toàn12epoch chưa kiểm lại. Phạm vi này là bốn biến thể expert/fold4; các baseline, learned graph và đề cương rộng hơn tiếp tục theo backlog chung.

## Gate Linux lần01 và xử lý

`source-gate01.log`/`linux01/` và artifactZIP trong output Modal giữ lỗi fixture packaging thiếu `modal_junyi_refit.py`. Có2ca fail, các process khác đạt; không phát hành Gate PASS. Đã bổ sung fixture và danh sách bắt buộc, local `tests11.log`14ca đạt. Lần02 có sourceZIP/Gate riêng, không thay file lịch sử. CPU App01 xác nhận dừng; cap0,15USD đóng bảo thủ, chi thực riêng chưa tách từ metering. Lần02 tiếp tục cap0,15USD.

## Nghiệm thu Linux và snapshot

Lần02 đạt2.660ca,0fail/0error/0skip, giữ đủ ba process isolation. `linux02/result.json`/`gate2-current.json`, logs và JUnitXML giữ bằng chứng. Source/Gate build trùng packet, artifactZIP đã kiểm SHA, CPU App đã xác nhận dừng. Hai lượtCPU đóng cap bảo thủ tổng0,30USD; chi thực riêng chưa tách chắc chắn từ metering. `billing-after.json` giữ snapshot provider, không coi reservation là tiền thực đã dùng.

`stage-inputs-a0.json` đến `stage-inputs-a3.json` đã inventory toàn bộ input. Đã đóng và kiểm snapshotA0 thật tại `artifacts/akt/staged/junyi-a0-refit-20261114-01`, có1.123file input local trước source/Gate, khoảng1,73GB. `snapshot-a0.receipt.json` là nghiệm thu local. Ba biến thể còn lại có spec nhưng chưa nhân bản snapshot lớn; tạo khi cần để tiết kiệm ổD.

Trạng thái hiện tại READY_FOR_BOUNDED_CUDA_VERIFICATION. Cài đặt/trainer/refit IO đã kiểm CPU/Linux, chưa có CUDA numerical proof của entrypoint refit mới. Chưa model refit Junyi thật hoặc calibration. Không coi Gate PASS là hoàn tất36epoch hoặc kết luậnRQ3. Có cận lịch sử bảo thủ27,3585USD và reserve2,50USD trong ledger; tổng29,8585USD trước allocation mới. Phải đo và đối soát lại phần còn lại, không mở fullH100 theo ước tính36×3phút mà chưa đủ dự toán.

### Lệnh đóng snapshot khi cần

Tại rootKLTN, dùng `.venv/Scripts/python.exe -B scripts/akt/prepare_junyi_refit_stage.py --request research_tracking/runs/junyi-refit-pipeline-20261114-01/stage-inputs-a1.json --snapshot artifacts/akt/staged/junyi-a1-refit-20261114-01`. Tương tựA2/A3. Môi trường kiểm cần scoped safe.directory đúng checkout upstream như các log tests. Lệnh này chỉ localCPU. Không chạy lại `prepare_source_gate*.py`, `build_contexts.py` hoặc `finish_requests.py` vào output đã có.

GPUcontroller là `experiments/akt/modal_junyi_refit.py --snapshot <snapshot> --request <execution-request> --run`; execution-request phải có allocation đã admission, GPU/timeouts/pricecap hợp lệ và image đã kiểm. Chưa tạo execution-request fullrefit vì chưa nghiệm thu CUDA/cost90. Giữ config/plan9epoch, resume từ checkpoint/COMPLETE đã tải và kiểm inventory. Export hoàn tất dùng `scripts/akt/export_junyi_refit_model.py --request <refit-request-aN.json> --output experiments/akt/results/<export-run-mới>`; checkpoint/Adam/RNG được kiểm trước/sau copy. Calibration/eval là bước sau refit riêng.

## Báo cáo GVHD chốt ngày14/11

Đã tạo đợt `supervisor_reports/2026-11-14/01_tien_do/` với HTML tự chứa và Markdown. Đối chiếu các phát hiện cốt lõi12/11 và trạng thái nghiệm thu14/11; giữ figure A3 gốc. `report-20261114-qa.json` giữ nguồn/SHA, kiểm3bảng/8section, anchor và ảnh liên quan. Đã xem ảnh desktop1280 và khung hẹp640 bằng Edge headless. Ảnh390 thử bị cắt, giữ diagnostic; chưa nghiệm thu viewport390. MCP không truy cập đượcfile/localhost, đã đóngtab và tắt server8769. Không chạy thí nghiệm/training mới.

## Tiếp tục H100 theo yêu cầu người dùng

Đã đối soát mốc metering sau các App cũ và giữ1USD biên trễ, reserve cuối1,50USD, trần30USD. Tranche600giây, cap1,25USD, epoch vẫn9. `budget-reconciliation-refit01.json` giữ thay đổi dự phòng do agent chọn. Lần01 bị chặn local vì selected-index metadata nằm trong snapshot vùngresults; chưa gọiApp/GPU. `input-relocation-*-02.json` kiểmSHAtrước/sau copy metadata sangartifacts/refit-inputs, không sửaindexcũ. Bốn snapshotbounded02 đã kiểmCPUđạt. Lần02 đangupload/Appkhởi tạo, chưadispatchGPU theo lần kiểm gần nhất. `advance_refit.py` chỉnghiệmthu/lập request/resume vàpromote, khôngtựgọi cloud; fixture đã kiểm chọncheckpointpartialmớinhất và chặnngânsách.

## Hậu xử lý local tiết kiệm mạng và ổD

Sau khi H100 dừng, collector mới tái dùng output bất biến trùngSHA/bytes trong cùng receipt hoặc receipt trước. Dùng hardlink trên cùng ổD để giữ mọi vị trí artifact mà tránh nhân bản vật lý; có fallbackcopy và kiểmSHA. Input snapshots vẫn copyđộc lập, không hardlinksource/dataset/configs. `tests14.log`/`tests15.log`41ca mỗi lượt có chồng lặp; `host-io-dedup-check.json`/`host-io-link-check.json` kiểm3output chỉ2remote reads, tất cả byte giữ nguyên và samefile thật. Đây là tối ưu local sau stop; numerical source/Gate2667 và identity checkpoint giữ nguyên. Các rawoutputs đã nghiệm thu phải tiếp tục giữ bất biến.
