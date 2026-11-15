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

## A0refit đã nghiệm thu và báo cáo15/11

Hai đợt05/06 hoàn tất9epoch, mỗi epoch2.040Adamstep/14.947.674target; tổng18.360step/134.529.066target. Tensorfinite/checkpoint/Adam/RNG/SHA được kiểm và xuất bốnfile tại `experiments/akt/results/model-export-a0-refit-20261114-01/`. `refit-report-20261115-state.json` và `figures/a0-refit-training-time-v01.*` giữ số liệu chuẩn. Báo cáo hiện hành chuyển sangđợt15/11, giữ14/11 nguyên trạng. A1 đã vàooptimizer, backbonekhởi tạo khớpA0(`a1-live-progress01-001.json`); A1/A2/A3chưađượctínhrefitcomplete khi chỉđangchạy. Cóhai lỗiGPUpreinit đãgiữlogvàbảnCPUchẩnđoánVolume, allocatorresearch16GiB; SourceGate2667/local92 đã đạt. Loop26355tiếptụctrongscope9×4/cap30USD, dừnglỗihoặcbudget đểROOTreview.

## 15/11 — A1 hoàn tất refit, tiếp tục A2 trong ngân sách

A1 hoàn tất 9 epoch qua bốn đợt có checkpoint/resume. Đã dừng các App, tải đủ artifact và xuất gói model tại `experiments/akt/results/model-export-a1-refit-20261114-01/`. `exports-verified-a0-a1.json` kiểm SHA của model và SUPPORT, số target/step từng epoch, cùng split, encoding, window, khởi tạo backbone và cấu hình tính toán của A0/A1. A1 trung bình 221,35 giây/epoch, A0 128,78 giây/epoch, cùng TRAIN90. Chưa hiệu chỉnh hay đánh giá độc lập.

`budget-reserve-refit02.json` và `budget-reserve-refit03.json` giữ quyết định tái phân bổ dự phòng nội bộ do agent đặt. Còn 0,25 USD dự phòng riêng và 1 USD biên trễ trong cận lịch sử. Giữ nguyên trần 30 USD toàn KLTN và cap 1,25 USD mỗi đợt. Snapshot `billing-during-refit-20261115-03.json` lúc 01:44 ghi nhận 26,49 USD credit đã dùng, số liệu có thể cập nhật chậm. A2 bắt đầu theo snapshot04. Chưa khẳng định đủ tiền hoàn tất A3, phải đối soát trước mỗi đợt. Hai báo cáo 15/11 đã bổ sung A1 hoàn tất và phần còn thiếu.

## 15/11 lúc 02:38 — A2 còn phần đuôi, chờ đối soát chi phí

A2 đã nghiệm thu 7 epoch đầy đủ và checkpoint epoch 8 tại batch 2.007/2.040. Còn 33 batch rồi epoch 9, tổng 2.073 bước optimizer. Ba App H100 đã dừng, artifact tải và kiểm đầy đủ trên D. `a2-final-timebox-plan01.json` giữ checkpoint/SHA, số bước còn lại và request dự kiến cho đợt cuối. Cận ngân sách hiện tại chưa cho phép cấp phát, chờ hóa đơn đủ giờ lúc 03:00. Không giữ GPU trong thời gian chờ.

Đã kiểm 85 ca local ở `tests-final-timebox05.log`. Cơ chế đợt cuối chỉ rút deadline controller xuống child 360 giây, function 400 giây, watchdog 440 giây và cap 0,70 USD. Chỉ nhận checkpoint đã tải, đã đóng marker và đã dừng App, nằm trong epoch cuối hoặc tối đa 40 batch cuối của epoch 8 trên đúng TRAIN90. Worker/config/identity mô hình giữ nguyên. Nếu quá hạn thì dừng, giữ checkpoint và yêu cầu kiểm lại, không tự tính hoàn tất hay tự chạy lại. `final-timebox-real-check01.json` kiểm cấu trúc checkpoint A1 thật, bản kế hoạch A2 kiểm đúng checkpoint thật trên D. Đây là kiểm admission local, chưa phải một lượt CUDA cho cơ chế này.

Lượt pytest đầu thiếu tiến triển đã giữ chẩn đoán. Lượt 02 ghi 33 ca đạt và 44 lỗi setup do không có quyền vào Temp ổ C. Chuyển thư mục tạm sang D giải quyết lỗi môi trường. Lượt 04 đạt 77 ca, lượt 05 đạt 85 ca sau bổ sung trường hợp phần đuôi epoch 8. Các bộ test có chồng lặp. Hóa đơn đủ giờ được đối soát ở `billing-reconciliation-apps-20261115-02.json`, các thay đổi dự phòng nội bộ ở `budget-delay-margin-refit04.json` và `budget-delay-margin-refit05.json`. Dự phòng riêng hiện 0,20 USD, giữ buffer từng App và cận tài nguyên của các lượt chưa có hóa đơn đủ giờ.

## 15/11 sau 03:12 — A2 refit đã nghiệm thu, A3 chờ ngân sách

Đối soát đủ giờ trong `billing-reconciliation-apps-20261115-03.json` cho phép đợt cuối cap 0,70 USD, cận toàn dự án trước chạy 29,96073511 USD. Worker A2 hoàn tất 9/9 epoch trong 318,16 giây của đợt cuối, function GPU 345,88 giây, App được xác nhận dừng trong 409,02 giây. Đã tải và kiểm 187 artifact, archive 1.834.074.014 byte, không chạy lại epoch từ đầu. Toàn bộ 9 epoch giữ đủ 14.947.674 target và 2.040 bước mỗi epoch.

Gói bốn file A2 tại `experiments/akt/results/model-export-a2-refit-20261114-01/` đã kiểm tensor/model/Adam/RNG và xuất trên D. `exports-verified-a0-a1-a2.json` kiểm model/SUPPORT SHA, số bước, target, split, mã hóa, cửa sổ, backbone khởi tạo và cấu hình tính toán chung cho ba phiên bản. Trung bình A0 128,78, A1 221,35 và A2 230,53 giây/epoch. Figure mới ở `figures/refit-epoch-time-a0-a1-a2-v01.*`, giữ figure A0 cũ. `resource-summary-a0-a1-20261115-01.json` giữ telemetry và hóa đơn đủ giờ của A0/A1, chưa bao gồm A2.

`refit-remaining-budget-review.json` ghi snapshot credit còn khoảng 1,12 USD lúc 03:12, có thể trễ. Cận lịch sử sau đóng đợt cuối 29,61748021 USD, dự phòng riêng 0,20 USD, cận cấp thêm một tranche A3 tiêu chuẩn vượt 30 USD. Mọi App refit đã dừng theo `billing-app-status-20261115-05.json`. Chưa khởi chạy A3 refit, giữ snapshot04 cùng confidence/cache TRAIN80 và plan 9 epoch. Model selected-fit A3 đã có ở run trước. Hiệu chỉnh và đánh giá độc lập của các model refit chưa thực hiện. Bundle vẫn mở cho phần A3 còn thiếu, đọc STATE trước tiếp tục.

`final-timebox-cuda-check01.json` ghi nghiệm thu đợt cuối trên H100 thật. Đã kiểm hai khung báo cáo desktop và hẹp, giữ ảnh phiên bản mới tại `report15-a2-v02-*.png` và biên bản `report-refit15-final-qa04.json`. Edge headless đã thoát, không giữ máy chủ preview. STATE hiện hành đã rút gọn để đọc nhanh, toàn bộ state trước đó giữ nguyên byte tại `STATE_checkpoint_A2_refit_20261115.json` với SHA trong state mới. Bundle còn mở, manifest là ảnh chụp tại thời điểm chốt A0–A2.

## 15/11 buổi trưa — A3 bắt đầu refit bằng credit hiện tại

Đã đăng nhập lại profile `kltn` sau khi token cũ hết hạn, xác nhận workspace `honguyenminhsang2005`. Colab MCP đã kiểm kết nối qua Edge rồi đóng bridge, chưa chạy cell hoặc chuyển dữ liệu. Lượt gọi local đầu thiếu request sau một điều kiện kiểm sai danh sách App rỗng, đã giữ `a3-initial-local-failure01.log`, chưa cấp GPU ở lượt đó.

`a3-short-config-comparison01.json` xác nhận 27 trường training và mọi cờ số học giữ nguyên, vẫn plan 9 epoch. Giới hạn mỗi đợt giảm xuống max wall 300 giây và max train 280 giây. Trần VRAM 12 GiB cao hơn đỉnh đã đo 5.789 MiB, chuẩn bị cho việc tiếp tục T4 bằng cùng profile. Confidence TRAIN80 và cache TRAIN90 giữ đúng nguồn đã nghiệm thu. Snapshot mới kiểm CPU đạt tại `a3-short-snapshot01.json`. `a3-live-identity01.json` xác nhận identity H100 khớp A0 ở data/plan/Gate/backbone và recipe số học. Trần VRAM là giới hạn tài nguyên được protocol cho phép khác nhau.

Lượt `modal-junyi-a3-refit-h100-20261115-01` hoàn tất epoch 1 với đủ 14.947.674 target, 2.040 bước, thời gian epoch 218,08 giây, rồi lưu tại epoch 2 bước 703. GPU function 317,27 giây, App đã dừng trước tải artifact. `a3-checkpoint-verified01.json` kiểm SHA, tensor model/Adam hữu hạn, RNG và sampler/trainer state trên CPU. Còn tiếp tục đến đủ 9 epoch. Snapshot billing sau lượt đầu ghi 29,25 USD credit đã dùng, billed 0.

`tests-credit-basis01.log` đạt 94 ca local, có chồng lặp với các bộ trước. Host admission hỗ trợ ledger khai báo cơ sở free credit thực tiêu thụ, giữ raw billing và một cent biên làm tròn. Storage/egress được miễn phí được loại khỏi chi tiêu credit. Ledger cũ mặc định tiếp tục dùng gross. Chế độ credit mới từ chối billed dương và giữ trần 30 USD. Việc đổi cơ sở ledger chỉ thực hiện sau đối soát App đã dừng và hóa đơn đủ giờ.

`a3-portable-source01.json` giữ gói nguồn/cache 603.557.811 byte và SHA trong `artifacts/akt/staged-archives/`, chưa upload. Gói phục vụ chuyển nguồn GPU khi cần. Checkpoint được quản lý riêng theo outputs của run.


## 15/11 — A3 tiếp tục qua hai lượt H100, chuyển nguồn GPU

Đã nghiệm thu checkpoint lượt02, đủ2/9epoch và epoch3 bước1.254/2.040. Model, Adam, RNG và sampler đã tải/kiểm trên D theo `a3-checkpoint-verified02.json`. Hai App đã dừng. Credit quan sát còn0,32USD, chưa đủ cận lượt H100 kế tiếp. Người dùng đã duyệt chuyển gói recovery683MB chứa source/cache TRAIN90/checkpoint sang Colab T4. `a3-colab-t4-discovery01.json` xác nhận Tesla T4 với15GiB VRAM. Chưa training trên Colab, chưa đo thời gian toàn epoch T4.

Gói phục hồi tại `experiments/akt/results/model-export-a3-refit-recovery-20261115-02/`, giữ index từng member. `package_a3_recovery.py` dựng lại gói, `colab_a3_bootstrap.py` kiểm toàn bộ SHA và giải vào đúng `/opt/kltn`. Giữ nguyên Gate/source/config số học. A3 dùng trần VRAM12GiB đã chốt trước lượt H100 đầu để dùng được T4. Chuyển thiết bị phải ghi rõ, tính tương đương số học xuyên GPU còn cần kiểm thực tế. Đây là checkpoint học dở, model refit9epoch còn thiếu.

Notebook vận hành `notebooks/akt_colab_a3_refit_resume.ipynb` giữ trình tự upload, SHA từng member, venv cô lập theo lock và khởi chạy một tranche tối đa600giây. `colab_a3_tranche.py` gọi worker gốc trong snapshot, giữ khóa tránh chạy trùng và dừng nhóm tiến trình con khi lỗi/timeout. Bốn kiểm mock local đạt theo `a3-colab-controller-tests01.json`; chưa coi mock là xác nhận CUDA. Mọi lần tiếp tục phải nghiệm thu vị trí sampler/checkpoint và sao lưu về D.

Kiểm exports có chế độ `--portable-memory-cap` tạo bằng chứng phiên bản riêng, áp dụng đúng chính sách có sẵn trong comparison_contract về trần VRAM. Bản strict vẫn kiểm đạt A0–A2 và giữ bằng chứng cũ. Bốn kiểm local xác nhận chỉ loại max_vram_bytes, giữ mọi cờ số học. Chưa có export A3 cuối. `exports-verified-a0-a1-a2-portable-memory-cap-v1.json` và `a3-portable-comparison-check01.json` giữ output kiểm. Không suy ra bitwise-equivalence xuyên H100/T4.
