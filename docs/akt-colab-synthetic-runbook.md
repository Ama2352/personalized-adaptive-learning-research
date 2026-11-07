# Kiểm AKT tổng hợp trên Colab

Mục đích là kiểm CUDA, causal inputs, artifact publish và checkpoint reload trên Linux GPU bằng nguồn hiện tại. Notebook là `notebooks/akt_colab_synthetic.ipynb`. Bundle chứa allowlist Python source/tests và probe tổng hợp, có SHA-256 từng file. Source AKT upstream được clone riêng và checkout đúng commit đã pinned.

Chỉ thị user07/11: **local → Colab free → Modal**. Các kiểm CUDA tổng hợp dùng chung ưu tiên Colab trước, không tự dùng credits Modal để debug khi chưa thử được gói Colab đã chuẩn bị. Không có runtime Colab được kết nối hiện tại. Colab pass không thay kiểm riêng image/Volume/cancel/recovery của Modal; lượt đó phải nhỏ và có allocation riêng. Nếu Colab chưa có GPU/quota, tiếp tục việc local, không tự chuyển sang tiêu Modal credits.

## Chuẩn bị local

```powershell
.\.venv\Scripts\python.exe -B scripts/akt/build_colab_bundle.py --output artifacts/akt/colab/akt-synthetic-local-check.zip
```

Lệnh từ chối ghi đè bundle. Khi source đổi, tạo tên bundle mới. Source hashes và dependencies của mỗi run nằm trong report. Bundle gồm source hiện tại trong working tree, vì vậy dùng manifest hash để xác định chính xác snapshot. Schema2 dùng scope source_and_bounded_test_fixtures, gồm script dependencies và các simulator CSV nhỏ cần cho tests. Notebook nguồn Paper1/2 được sao dưới dạng source-only, bỏ outputs/execution metadata trong bản copy. Source cells giữ nguyên, original SHA và transform ghi trong manifest. Notebook gốc giữ nguyên trên repo. Junyi interactions, CV/refit predictions và checkpoint nằm ngoài allowlist.

## Chạy notebook

Mở notebook trong Colab bằng Upload notebook. Các kiểm CPU thông thường tiếp tục chạy local; trong Colab chạy portability precheck trước GPU probe. Chọn GPU runtime khi bắt đầu gói kiểm nhỏ và ngắt runtime sau khi tải kết quả. Đổi runtime type có thể làm mất state/files; nếu đổi, chạy lại từ đầu/upload lại, không giả định ROOT/.venv còn. Notebook kiểm schema và bắt buộc manifest có recovery probe (kitv11 trở lên), kiểm hash trước extract, clone upstream pinned và tạo ROOT/.venv với system-site-packages để kế thừa PyTorch runtime. Các package còn thiếu chỉ được cài bằng interpreter của venv này. CPU/GPU subprocess dùng cùng interpreter đó. PyTorch/runtime identity được ghi trong output, cần pin image và xác minh lại khi chuyển Modal.

Cell kiểm CPU chạy AKT/shared/GAM, subprocess timeout600giây và CUDA_VISIBLE_DEVICES rỗng trong riêng workerCPU. Tăng từ300vì suite local hiện mất khoảng375giây; đây là CPU software budget, không tăng GPU workload. JUnit phải có tests>0, khôngfail/error/skip; exit0 riêng chưa đủ. Hai integration tests được loại rõ bằng tên. `test_native_akt_import_cpu` cần local venv/Windows lock; `test_actual_frozen_assignments_are_unchanged_and_student_disjoint` cần assignments thật không thuộc portable kit. Probe thay thế ghi runtime/source/dependency identity thực. Các tests còn lại dùng source/fixtures trong bundle. Cell GPU yêu cầu CPU_PORTABILITY_OK và recheck hashes nguồn, giữ visibility GPU của runtime, chạy một synthetic epoch, một optimizer step,400targets, H/T100, d256 và defaults kiến trúc hiện tại, timeout600giây. Nếu thiếu GPU hoặc test lỗi, dừng và giữ log. Cell cuối tải output kể cả failure để lưu bằng chứng.

Kit hiện tại là `artifacts/akt/colab/akt-synthetic-20261107-v11.zip`, **137files**, SHA256 `0d4d59a973b4909b26837f795ead499f3b0da6375db3dd6f58096c57530a9f09`. Có thêm recovery probe và tests; giữ v10 nguyên bytes như snapshot cũ. Đã kiểm CRC, từng file SHA và source parity; đây chưa là isolated Linux/CUDA execution. Notebook nằm ngoài ZIP allowlist: dùng bản notebook hiện tại cùng v11. Kết quả software gate mới nhất và giới hạn nằm trong `research_tracking/reports/colab_recovery_readiness_20261107.md`.

Lịch sử: local isolated extraction kiểm AKT/shared240passed1deselected trênv5; manifest so v6 chứng minh mọi file AKT/shared và dependency giống v5, chỉ đổi test_core của GAM. GAM trênv6 đạt31passed1deselected. v4 có missing host fixtures, v5 còn GAM test phụ thuộc assignments thật, giữ logs và ZIP cũ để truy nguồn. V7 bổ sung recovery CLI, synthetic fixture và common-population diagnostic source/tests.

Notebook yêu cầu người dùng ở giao diện Colab chọn runtime, upload bundle và tải output. Chưa có remote runtime nào được kết nối trong phiên local. Phiên này không có công cụ nối trực tiếp runtime Colab. Người dùng chạy notebook qua giao diện chuẩn và tải ZIP kết quả về; chỉ gửi URL notebook chưa cung cấp một kênh thực thi cho agent.

## Nghiệm thu

Report có `status=passed_synthetic`, `cuda_lifecycle=true`, finite gradient/update,400prediction rows, checkpoint reload prediction parity tolerance1e-6, current/future-label invariance và output SHA inventory. GPU timings dùng đồng bộ đầu/cuối optimizer step, substep telemetry cũ chỉ mang tính chẩn đoán. Probe không ước lượng throughput full-fold từ một step.

Report lifecycle giữ `mid_epoch_resume_verified=false` và `gate4_pass=false`, không đổi ý nghĩa kết quả cũ. Cell recovery riêng chỉ chạy sau CPU và CUDA lifecycle đạt, recheck source SHA rồi gọi:

```text
.venv/bin/python -B scripts/akt/synthetic_recovery_probe.py --device cuda --output-dir experiments/akt/results/colab-synthetic-recovery-cuda
```

Probe dùng production `train_epoch`, mô hình nhỏ d32/dropout0.2, fixture17targets/H2T2/batch2. Ba tiến trình chạy continuous5updates, interrupt sau committed step2 rồi resume3updates; tổng10updates thực tế. Timeout mỗi worker60s, controller180s, notebook240s. Kiểm exact target ledger, RNG/sampler và checkpoint nguồn bất biến; model/Adam/predictions CUDA dùng atol=rtol1e-5 khai báo trước. Không tự nới tolerance hoặc retry. Report riêng chỉ ghi `cuda_mid_epoch_resume_verified=true` khi actual CUDA đạt; Gate4 vẫn false. Local CPU probe đã đạt exact equality qua ba tiến trình, không là xác nhận CUDA. Không chứng minh hard-kill/preemption, image hay Volume Modal. Nếu lỗi, tải log/report/checkpoint rồi dừng để phân loại; không chuyển sang Modal tự động. Complete real-data pilot và throughput vẫn chưa thực hiện. Tải ZIP kết quả ra khỏi runtime trước khi runtime mất. Output chứa synthetic IDs.

Colab GPU/time availability thay đổi và runtime có thể bị thu hồi. Chỉ dùng giao diện notebook tiêu chuẩn cho kiểm tương tác. Nguồn chính thức được đọc ngày07/11/2026 tại https://research.google.com/colaboratory/faq.html.
