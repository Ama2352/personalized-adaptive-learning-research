# Kiểm AKT tổng hợp trên Colab

Mục đích là kiểm CUDA, causal inputs, artifact publish và checkpoint reload trên Linux GPU bằng nguồn hiện tại. Notebook là `notebooks/akt_colab_synthetic.ipynb`. Bundle chứa allowlist Python source/tests và probe tổng hợp, có SHA-256 từng file. Source AKT upstream được clone riêng và checkout đúng commit đã pinned.

## Chuẩn bị local

```powershell
python scripts/akt/build_colab_bundle.py --output artifacts/akt/colab/akt-synthetic-20261107.zip
```

Lệnh từ chối ghi đè bundle. Khi source đổi, tạo tên bundle mới. Source hashes và dependencies của mỗi run nằm trong report. Bundle gồm source hiện tại trong working tree, bao gồm các file chưa track, vì vậy dùng manifest hash để xác định chính xác snapshot. Không đưa dataset, credentials hoặc historical prediction/model artifacts vào bundle.

## Chạy notebook

Mở notebook trong Colab bằng Upload notebook, chọn GPU runtime, chạy tuần tự các cells. Upload bundle do lệnh trên tạo. Notebook kiểm hash trước extract, clone upstream pinned và cài các dependency còn thiếu. PyTorch do runtime cung cấp, ghi lại pip freeze và CUDA/GPU identity. Môi trường này là kiểm tương thích thăm dò, phải pin image và xác minh lại khi chuyển Modal.

Cell kiểm CPU chạy suite AKT/shared tổng hợp trước, subprocess timeout300giây. Test `test_native_akt_import_cpu` được deselect rõ vì kiểm `.venv` và lockfile CPU Windows local, không tương ứng runtime Colab. Probe thay thế ghi runtime/source/dependency identity thực. Các synthetic tests còn lại giữ nguyên, bundle gồm ba config fixtures và runtime checker. Cell GPU chạy duy nhất một synthetic epoch, một optimizer step,400targets, H/T100, d256 và các defaults kiến trúc hiện tại. Timeout600giây. Nếu thiếu GPU hoặc test lỗi, dừng và giữ log. Notebook không tự retry, không tự mount Drive hoặc đọc Junyi. Cài dependency chỉ cần những package còn thiếu, không dùng Windows CPU lockfile trên Linux.

Notebook yêu cầu người dùng ở giao diện Colab chọn runtime, upload bundle và tải output. Chưa có remote runtime nào được kết nối trong phiên local. Có thể điều khiển notebook hiện có sau khi được cấp link/quyền và runtime sẵn sàng, tùy công cụ truy cập.

## Nghiệm thu

Report có `status=passed_synthetic`, `cuda_lifecycle=true`, finite gradient/update,400prediction rows, checkpoint reload prediction parity tolerance1e-6, current/future-label invariance và output SHA inventory. GPU timings dùng đồng bộ đầu/cuối optimizer step, substep telemetry cũ chỉ mang tính chẩn đoán. Probe không ước lượng throughput full-fold từ một step.

`mid_epoch_resume_verified=false` và `gate4_pass=false` được xuất rõ. Resume giữa epoch và complete real-data pilot vẫn là task kế tiếp. Checkpoint format cũ giữ compatibility, checkpoint chỉ nhận synthetic epoch đã hoàn tất trong probe này. Tải ZIP kết quả ra khỏi runtime trước khi runtime mất. Output chứa synthetic IDs.

Colab GPU/time availability thay đổi và runtime có thể bị thu hồi. Chỉ dùng giao diện notebook tiêu chuẩn cho kiểm tương tác. Nguồn chính thức được đọc ngày07/11/2026 tại https://research.google.com/colaboratory/faq.html.
