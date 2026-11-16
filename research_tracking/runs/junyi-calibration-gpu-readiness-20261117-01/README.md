# Sẵn sàng Modal cho suy luận calibration Junyi

Ngày 17/11/2026. Lượt này kiểm source, metadata và API readonly. Không tạo App/container/volume, gọi function trả phí hoặc mở đăng nhập.

## Trạng thái tài khoản và ngân sách

`MODAL_READ_ONLY.json` ghi Modal SDK1.6.3 trả `AuthError`, nội dung lỗi có dấu hiệu token đã hết hạn. Vì bước xác thực chưa qua, lượt này chưa xác nhận workspace từ server hoặc đọc billing hiện tại. Profile cần kiểm là `kltn2016`, file `artifacts/akt/private/modal2016.toml`, workspace kỳ vọng `honguyenminhsang2016` theo hồ sơ đã nghiệm thu.

Hồ sơ `workspace2016-billing-after-a3-02.json` trong bundle refit ghi lần đọc15/11/2026 lúc17:01:36UTC, metered0,22012663USD, billed0USD. Đây là số lịch sử. Credit còn lại hôm nay chưa xác minh được. Ledger `research_tracking/COMPUTE_BUDGET_WORKSPACE2016.json` giữ trần30USD của đợt mới, cận reservation lịch sử0,97USD và dự phòng5USD. Các số này không phải số dư credit mà provider trả về.

Đã kiểm `modal token new --help`, bản1.6.3 hỗ trợ `--profile`, `--expires-in 12h` và `--no-activate`. Root phụ trách mở đăng nhập riêng. Hai lệnh đã dùng cho profile này là như sau.

```powershell
$env:MODAL_CONFIG_PATH = 'D:\Dev\KLTN\artifacts\akt\private\modal2016.toml'
.\.venv\Scripts\python.exe -B -m modal token new --profile kltn2016 --expires-in 12h
```

Sau đăng nhập, kiểm readonly bằng script của bundle và output mới để giữ nguyên biên nhận token hết hạn.

```powershell
.\.venv\Scripts\python.exe -B research_tracking\runs\junyi-calibration-gpu-readiness-20261117-01\check_modal_readonly.py --output research_tracking\runs\junyi-calibration-gpu-readiness-20261117-01\MODAL_READ_ONLY_AFTER_LOGIN.json
```

Script chỉ ghi workspace, expiry nếu server trả về và billing. Token ID, nội dung config, header xác thực và traceback không đưa ra output. Nó không kích hoạt/chuyển profile bền vững.

## Dữ liệu đã có

`research_tracking/runs/junyi-calibration-data-20261117-01/PREPARED.json` xác nhận nguồn calibration10 riêng đã chuẩn bị, gồm15.847người học,1.621.484targets,0duplicate source_row,0invalid và0OOV. Parquet có14.143.412byte, assignments52.569byte. Nguồn không gồm train/selection/outer/Holdout events. Refit90 encoding và graph/confidenceTRAIN80 giữ riêng.

14MB là phần dữ liệu cohort. Snapshot suy luận còn cần source/runtime metadata, encoding/roles/graph và checkpoint của biến thể được gọi. Mỗi refit checkpoint A0–A3 khoảng29MB. Không cần chuyển mọi archive training lịch sử đã sao lưu.

## Những phần có thể tái dùng

- `research_junyi_calibration.read_refit_export_package` và `attach_refit_export` nạp compact model/index/support theo pin, giữ training identity và ghi inference identity riêng.
- `prepare_calibration_population` cùng `export_refit_calibration_predictions` kiểm role, target order, coverage và xuất raw predictions. Caller phải giữ grant, Gate/runtime và manifest nguồn.
- `prediction_batch.prepare_prediction_windows` và `iter_prepared_predictions_batched` hỗ trợ chuẩn bị cửa sổ trước, rồi chấm batch tối đa128. Refit config hiện hành có context100,target_block100,max_length200,batch128,d_model256,threads2.
- `experiments/akt/modal_junyi_staged.py` có input snapshot/CPU preflight, một GPU container, timeout, retries0, watchdog và stop barrier trước download/nén local. `modal_budget_guard.py` kiểm đúng App ownership và xác nhận dừng.

## Blocker thực tế trước gọi GPU

1. Đăng nhập lại và đọc billing/đối chiếu workspace hiện tại trước reservation mới.
2. Runner staged hiện chỉ cho `run_junyi_gpu_stage.py` và `run_junyi_refit_gpu_stage.py`. Worker thứ nhất khóa selected-fit A2/A3, worker thứ hai khóa `purpose=refit90`. Chưa có worker inference-only calibration được allowlist. Đổi purpose trong request không khép khoảng trống này.
3. Cần snapshot/CPU_CHECK đúng source calibration mới, cohort mới, compact export và encoding/graph đã ghim, cùng Gate/runtime hiện hành. Các Gate của training cũ không tự chứng nhận source inference vừa thay.
4. Cần đo RAM population/temperature fitter và giải quyết materialization nếu vượt máy local. Corpus Parquet nhỏ không đảm bảo object target/key/provenance của fitter cũng nhỏ.
5. Cần kiểm CUDA parity, mask/coverage và tốc độ của inference producer mới trước chạy toàn cohort. Kết quả train/refit trước đó không phải benchmark của producer calibration này.

Để giữ CPU ngoài thời gian thuê GPU, chuẩn bị đọc dữ liệu/cửa sổ/context trước. Chỉ chuyển batch đã chuẩn bị vào numerical worker, xuất raw probabilities và marker bền vững, sau đó dừng GPU. Fit temperature, scoring, đóng gói và download chạy ở stageCPU. Wrapper training hiện hành còn hash output inventory trong `gpu_compute` sau numerical process, nên cần tách phần đó khi dùng cho inference nếu output lớn. I/O, truyền tensor và nạp checkpoint vẫn cần đo trên worker thực, không hứa GPU utilization từ thiết kế tĩnh.

## Pilot đề xuất, chưa thực thi

Đầu tiên chọn cố định tối đa256cửa sổ calibration, tương ứng tối đa25.600target với target_block100, khóa exacttarget/prefix identity trước khi chấm. Đây là pilot kỹ thuật, không fit nhiệt độ nghiên cứu hoặc chọn biến thể dựa trên số liệu pilot. Chạy A0 trước, rồi một graph variant A3 trên cùng mẫu để nhận diện chi phí context. Mọi prediction phải có ID/thứ tự/label/coverage và checksum, so parity với producer đã kiểm theo tolerance được khai báo trước.

Lưu CPU preparation time riêng, model-load/host transfer time, CUDA forward time có synchronize, scored targets/sec end-to-end, NVML utilization/VRAM và chi phí provider. Chọn GPU theo chi phí mỗi target cùng sai số số học đã kiểm. Thời gian đầy đủ chỉ được tính sau benchmark bằng `N/R + overhead`, với N=1.621.484 cho mỗi model và báo riêng4model.

`PROPOSED_RESOURCE_ENVELOPE.json` tái tính cận resource của repo cho2CPU/8GiB, child270s,function300s,watchdog390s, active-function budget. Cận CPU preflight cộng GPU function/startup lần lượt khoảng0,132USD trênT4,0,153USD trênL4 và0,468USD trênH100. Đây là cận của hai function theo công thức repo, chưa là dự toán toàn lifecycle hoặc quyền thực thi. Image build, lưu trữ và egress cần đối soát theo cách provider tính thực tế.

Giá GPU trong code khớp [Modal pricing](https://modal.com/pricing) đọc trong lượt này, T4 là0,000164USD/s,L4 là0,000222USD/s,H100 là0,001097USD/s. Cận CPU/RAM của repo bảo thủ hơn giá list. [Timeout docs](https://modal.com/docs/guide/timeouts) ghi timeout tính theo từng lần thực thi, vì vậy retries0 và server timeout phải được giữ cùng watchdog để giới hạn lượt chạy. [Resource docs](https://modal.com/docs/guide/resources) giải thích CPU/RAM của container.

## Nguồn và giới hạn

Các source đã đọc gồm `modal_junyi_staged.py`, `modal_junyi_refit.py`, hai numerical workers, `modal_budget_guard.py`, `research_junyi_calibration.py`, `prediction_batch.py`, receipt workspace2016 và ledger hiện hành. Chưa nạp model, đọc raw Junyi, đo throughput, fit calibration, dùng GPU hoặc chi credit trong lượt readiness này.


## Kiểm lại sau đăng nhập

Người dùng đã xác nhận đăng nhập. `MODAL_READ_ONLY_AFTER_LOGIN.json` xác minh đúng workspace honguyenminhsang2016, token hợp lệ, expiry2026-11-17T06:28:57Z. Billing đọc lúc2026-11-16T18:29:49UTC trả metered0,12045316USD, billed0USD và adjustmentCredits−0,12USD. Summary này không trả số dư credit hiện tại. Số metered có thể điều chỉnh so với receipt cũ, nên không suy số credit còn lại từ billed0 hoặc lấy số30trừ trực tiếp.

SDK tự phát cảnh báo expiry có token ID vào output, dù code chỉ in JSON đã lọc. Đã thêm filter cảnh báo theo prefix cho các lượt kiểm sau. Token secret không được đọc/in, các JSON công khai không chứa token ID. Chi tiết schema và giới hạn ở `SDK_SCHEMA_AND_OUTPUT_REVIEW.json`. Root đang điều phối credential Drive cho cloudCPU, nhánh này chưa tạo Secret hoặc gửi OAuth credentials lên cloud.

Đối với uploader cloudCPU, phần credential tối thiểu cần để refresh là OAuth client ID/client secret, refresh token và token URI cố địnhGoogle. Chỉ mount Secret vào CPU uploader, giữ ngoài image/source snapshot, output và logs. Token local hiện có quyềnDrive đầy đủ đã được người dùng cấp, chưa phải credential chỉ giới hạn một folder. Muốn chuyển sang scope drive.file cần flow cấp quyền mới và chứng minh quyền với folder/file có sẵn qua app hoặc picker. Phạm vi thư mục trong uploader là giới hạn logic của code, không thu hẹp OAuth scope của token. Việc đưa credential vào Modal Secret do root điều phối theo quyền được cấp.
