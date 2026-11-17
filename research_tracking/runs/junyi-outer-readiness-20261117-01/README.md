# Readiness outer Junyi ngày17/11

Gói mở ghi audit chỉ đọc và kiểm tổng hợp để chuẩn bị đánh giá Developmentfold4 sau refit/calibration. Không có training, Holdout, GPU hoặc CPUcloud. Báo cáo chính tại `research_tracking/reports/JUNYI_OUTER_EXECUTION_READINESS_20261117.md`.

## Kết quả

-3kiểm tổng hợp đạt,1XFAIL strict ghi lỗi cache từ chối OOVfold4. Đường native batched giữ OOVnull đã kiểm với adapter giả, chưa kiểmweights/CUDA thật.
- Hai đếm metadata không tạo kết quả. Lần1 monitor vượt timeout90s tới367,90s,peakRSS152,57MB. Lần2 chặnWindowsJob128MiB, dừng6,06s khiOpenBLASkhôngcấpRAM,activeprocess sau terminate=0. Khôngretry.
- Count không truy vấn correctness. OOV144của BKT và4.137.050row lịch sử chỉ là metadata đối chiếu, chưa thay countsneural outer.

## Tái lập kiểm tổng hợp

PowerShell tại repository, đặt `$env:PYTHONPATH='D:\Dev\KLTN\src'`, chạy `.\.venv\Scripts\python.exe -B -m pytest tests/akt/test_outer_frozen_cache_readiness.py -q -p no:cacheprovider -rx`. Log đạt ở `synthetic-regression03.txt`. `synthetic-regression01.txt` giữ lỗi collection thiếuPYTHONPATH ban đầu.

Hai scriptcount chỉ giữ phục vụ audit failure, không tự chạy lại. `MANIFEST.json` ghim các file nhỏ và source liên quan, không sửa nguồn KT frozen. Không cófigure vì chưa có số liệu outer mới.
