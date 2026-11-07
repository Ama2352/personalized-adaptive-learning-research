# Kiểm AKT tổng hợp trên Colab

Mục đích là kiểm CUDA, causal inputs, artifact publish và checkpoint reload trên Linux GPU bằng nguồn hiện tại. Notebook là `notebooks/akt_colab_synthetic.ipynb`. Bundle chứa allowlist Python source/tests và probe tổng hợp, có SHA-256 từng file. Source AKT upstream được clone riêng và checkout đúng commit đã pinned.

## Chuẩn bị local

```powershell
.\.venv\Scripts\python.exe -B scripts/akt/build_colab_bundle.py --output artifacts/akt/colab/akt-synthetic-local-check.zip
```

Lệnh từ chối ghi đè bundle. Khi source đổi, tạo tên bundle mới. Source hashes và dependencies của mỗi run nằm trong report. Bundle gồm source hiện tại trong working tree, vì vậy dùng manifest hash để xác định chính xác snapshot. Schema2 dùng scope source_and_bounded_test_fixtures, gồm script dependencies và các simulator CSV nhỏ cần cho tests. Notebook nguồn Paper1/2 được sao dưới dạng source-only, bỏ outputs/execution metadata trong bản copy. Source cells giữ nguyên, original SHA và transform ghi trong manifest. Notebook gốc giữ nguyên trên repo. Junyi interactions, CV/refit predictions và checkpoint nằm ngoài allowlist.

## Chạy notebook

Mở notebook trong Colab bằng Upload notebook. Có thể chạy các cell chuẩn bị/CPU trước, rồi chọn GPU runtime khi cần CUDA probe. Upload bundle do lệnh trên tạo. Notebook nhận cả schema1 cũ và schema2 mới, kiểm hash trước extract, clone upstream pinned và tạo ROOT/.venv với system-site-packages để kế thừa PyTorch runtime. Các package còn thiếu chỉ được cài bằng interpreter của venv này. CPU/GPU subprocess dùng cùng interpreter đó. PyTorch/runtime identity được ghi trong output, cần pin image và xác minh lại khi chuyển Modal.

Cell kiểm CPU chạy AKT/shared/GAM, subprocess timeout300giây và CUDA_VISIBLE_DEVICES rỗng trong riêng workerCPU. Hai integration tests được loại rõ bằng tên. `test_native_akt_import_cpu` cần local venv/Windows lock; `test_actual_frozen_assignments_are_unchanged_and_student_disjoint` cần assignments thật không thuộc portable kit. Probe thay thế ghi runtime/source/dependency identity thực. Các tests còn lại dùng source/fixtures trong bundle. Cell GPU giữ visibility GPU của runtime, chạy một synthetic epoch, một optimizer step,400targets, H/T100, d256 và defaults kiến trúc hiện tại, timeout600giây. Nếu thiếu GPU hoặc test lỗi, dừng và giữ log. Cell cuối tải output để lưu bằng chứng.

Kit mới nhất đã build là artifacts/akt/colab/akt-synthetic-20261107-v7.zip,120files, SHA256018888bbee3718f0c9ce9222ae079315aefca67d176e4d2be8ec49d78f69c9cc. Đã kiểm ZIP hashes/allowlist, chưa chạy isolated extraction suite v7 hoặc actual Colab/Linux/CUDA. Main source Gate2 local đạt274passed; GAM riêng45passed. Không gán hai kết quả này thành remote/portable execution.

Lịch sử: local isolated extraction kiểm AKT/shared240passed1deselected trênv5; manifest so v6 chứng minh mọi file AKT/shared và dependency giống v5, chỉ đổi test_core của GAM. GAM trênv6 đạt31passed1deselected. v4 có missing host fixtures, v5 còn GAM test phụ thuộc assignments thật, giữ logs và ZIP cũ để truy nguồn. V7 bổ sung recovery CLI, synthetic fixture và common-population diagnostic source/tests.

Notebook yêu cầu người dùng ở giao diện Colab chọn runtime, upload bundle và tải output. Chưa có remote runtime nào được kết nối trong phiên local. Có thể điều khiển notebook hiện có sau khi được cấp link/quyền và runtime sẵn sàng, tùy công cụ truy cập.

## Nghiệm thu

Report có `status=passed_synthetic`, `cuda_lifecycle=true`, finite gradient/update,400prediction rows, checkpoint reload prediction parity tolerance1e-6, current/future-label invariance và output SHA inventory. GPU timings dùng đồng bộ đầu/cuối optimizer step, substep telemetry cũ chỉ mang tính chẩn đoán. Probe không ước lượng throughput full-fold từ một step.

`mid_epoch_resume_verified=false` và `gate4_pass=false` được xuất rõ. Resume giữa epoch và complete real-data pilot vẫn là task kế tiếp. Checkpoint format cũ giữ compatibility, checkpoint chỉ nhận synthetic epoch đã hoàn tất trong probe này. Tải ZIP kết quả ra khỏi runtime trước khi runtime mất. Output chứa synthetic IDs.

Colab GPU/time availability thay đổi và runtime có thể bị thu hồi. Chỉ dùng giao diện notebook tiêu chuẩn cho kiểm tương tác. Nguồn chính thức được đọc ngày07/11/2026 tại https://research.google.com/colaboratory/faq.html.
