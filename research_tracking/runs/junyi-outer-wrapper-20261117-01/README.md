# Wrapper native outer Junyi ngày17/11

Đây là gói follow-up tách riêng bundle readiness đã đóng. Mã mới ở `scripts/akt/free_outer_evaluation.py`, không sửa nguồn KT frozen, model, calibrator hoặc dữ liệu. Không đọc labelsouter thật, không nạpTorch/weights, không chạy cloud/GPU.

## Hợp đồng đã cài

`admit_outer` nhận predictor đã attach bằng API hiện có, fullviewouterfold4, refit90encoding, pin nguồn inference đang chạy và hai domainSHA riêng. Graphadapter phải đã ở outerphase. Calibrator được giữ nguyên binding đã fit, chỉ chấp nhận khi7fieldmodel/source/encoding/split/bank/reference/checkpoint khớp rawpredictor, domaincalibration ghim độc lập.

`iter_outer_predictions` nhận factory có thể đọc lại cùng nguồn đã ghim, expectedtargets và capevent/learner. Tái dùng nativebatch128, kiểm mỗi row identity gồm learner/exercise/time/source_row/correct/suggested/fold bằng luồng đối chiếu độc lập. Giữ OOVnull và reason, không loại row hoặc thay xác suất giả. Receipt chỉCOMPLETE sau khi tiêu thụ toàn bộ đúng count. Lỗi hoặc đóng stream sớm giữINCOMPLETE. Caller phải xuất staging và chỉpublishkhiCOMPLETE, kèmchecksumDrive.

Source nhập native consumer nên CPU đọc/encode/join vẫn xảy ra. Wrapper này đóng hợp đồng đối chiếu và fallback native, **chưa nghiệm thu hiệu năng hoặc tách CPU/H100**. Không triển khai nguyên iterator cùng readerSQL trong H100 rồi gọi đó là tối ưu. CPUlocal/Colab phải chuẩn bị và ghim inputs trước, H100chỉnumeric, CPUlocal/Colab nối labels/applytemperature/metrics. Hiện wrapper còn cần nối numeric receipt nếu dùng đường numeric tách biệt. Không nhận `Bounded engineering cohort cache` choouter.

## Kiểm chứng

- `red01.txt` ghi7error đúng do chưa có sourcewrapper.
- `green01.txt` ghi7PASS ban đầu.
- `green02.txt` ghi11PASSwrapper và3PASS/1XFAILstrictcacheboundary, tổng14PASS/1XFAIL trong3,49s.
- Tests dùng adapter giả và monkeypatch boundary để tập trung wrapper. Chưa chứng minh4checkpoint nghiên cứu thực nạp được hoặc CUDAparity. Kiểmmodel thực vẫn phải dùngassert_boundarygốc.
- Importfreshprocess được ghi ở `IMPORT01.json`, xác nhận không importTorch. Manifest ghim source/test/logs/protocol.

Tái lập bằng PowerShell đặt `$env:PYTHONPATH='D:\Dev\KLTN\src'`, dùng `.\.venv\Scripts\python.exe -B -m pytest tests/akt/test_free_outer_evaluation.py tests/akt/test_outer_frozen_cache_readiness.py -q -p no:cacheprovider -rx`.

## Phạm vi thống kê đã đối chiếu

Protocol21 phầnestimandF1 quy địnhLL/Brier, pairedlearnerbootstrap2.000lượt vàHolmfamilycontrast×condition×primaryendpointfreeze trước run. Recipe26 phầnselector chốtseed42, thứ tựlearner vàupperquantile0,975 cho chọn hệ thốngDevelopment, đồng thời ghi rõ **không là finalsignificance**. Hai tài liệu này chưa cung cấp familycardinality/p-valuerecipe cụ thể cho outer4variantsraw/calibrated. Gói này không tự chọn test hoặc family mới. Phải hoàn thiện requestthốngkê từ quyết định đượcchấp thuận trước khi xem kết quảouter.

## Còn thiếu trước thực thi

Nguồn/counts/OOV thựcouter,4temperatuređãnghiệmthu, wrappernumericCPU/H100 và Drivepublishtransaction, requestfamily/p-valuerecipe và budget. [Readiness hiện hành](../../reports/JUNYI_OUTER_EXECUTION_READINESS_20261117.md) giữ các blocker chi tiết. Chưa có metricouter hoặc kết luậnRQmới.
