# Admission nguồn guard outer, ngày17/11

Root duyệt release cụ thể D22→D22chỉthayguardfold. Mã mới chỉ ở `scripts/akt/free_outer_evaluation.py`, ngoài nguồnKT. Không sửa4model/calibrator, SOURCEfrozen, metadata hoặc bindings cũ. Không chạy dữ liệuouter/GPU/cloud. CPUcalibration hiện hành tiếp tục dùng SOURCEfrozen riêng.

## API và điều kiện nhận

`build_compatibility_receipt(old_files,new_files,checkpoint_sha256=None,calibration_identity=None)` chỉ nhận đúng77filemap có identityD22vàrelease7c72414e. Map phải khác đúng1filewindowcache, SHA trước/sau cố định. Hàm kiểm fileguard thực tế và phép thay ngược đúng một chuỗiđiềukiện để phục hồi nguyênSHAoldguard, không chỉ dựa AST. Thiếu bất kỳ variantpin nào thì receipt là `DRAFT_MISSING_VARIANT_PINS`, validator từ chối.

`validate_compatibility` nhận receipt đủpins, checkpointSHA/calibratoridentity thực được tính từ predictor/calibrator. Chỉ nhận chuyển nguồn `d22f6d2e3d6bb4a6c2d7f72da748e55c5c647ce8b41a7ab46b25c82290a4c96c` → `7c72414eedf9507d514430aed4734f0a192ab14914a4984b17fdfcbfebd39123`. Đọc lại77file source runtime, phải khớp toàn bộ newmap. Nguồncheckout cóupstreamCRLF (`a841100f...`) bị từ chối; không dùng ASTequality làm quyền nhận source khác.

`admit_outer(...,compatibility=None)` và `iter_outer_predictions(...,compatibility=None)` giữ strictdefault. Khi có receipt hợp lệ, chỉ trườngmodel_source được đối chiếu qua release đãchốt. Sáu trườngmodel/checkpoint/vocab/split/bank/reference vẫn phải trùng tuyệt đối. Domaincalibration vàouter riêng, fullouterrole/refitencoding/graphphase và currentruntimeidentity vẫn kiểm như cũ. Admissionreceipt ghi cả hai nguồn và SHAcompatibilityreceipt. Consumer gọi `iter_calibrated_predictions` bằng **calibration.binding cũ**, không chỉnh lại temperature hoặc payload.

## Kiểm đã chạy

- `red01.txt` giữ8error trước đổi fixture sang wrappermộtfile.
- `red02.txt` giữ8FAIL do chưa có cácAPIcompatibility.
- `green01.txt` có19PASS nhưng thời gian1517,26giây. Hostexec bị timeout/replaced, root cũng ghi nhận độ trễ scheduling ở tác vụ độc lập. Chưa xác định nguyên nhân, không coi đây là benchmarkCPU củawrapper.
- `green02.txt` có23PASS,13,71giây theo pytest, gồm validrelease/sameprobability/OOVnull, bảo toànpayloadcalibrator, defaultstrictreject, extraSourceDelta/runtime/checkpoint/calibrator/roles/domainnegative vàdraftmissingpins. Đây là kiểm tổng hợp; runtimefullmap đượcmonkeypatch trong case hợp lệ để mô phỏng bundle7c chưa được dựng. Không tuyên bố đã nghiệm thu bundle thực hoặc CUDAparity.

Theo yêu cầu root sau đó đã dừng kiểm thêm. Root sẽ freshverify sourcefreeze này khi tài nguyên ổn định. Mã giữ nguyên nguồnKTidentity sau guardrelease vì chỉ đổi script ngoàiKT.

## Điểm tiếp tục

`COMPATIBILITY_DRAFT01.json` chỉ giữ sourcemap vàpinsnull, **không cấp quyền dùng model thật**. Chưa có4pervariantreceipt hoàn chỉnh trong gói. Root cần dựng sourcebundle mới từfrozenD22 +guardmodulemới, xác minhidentity7c thực, đọc lại4calibratoridentity/4checkpointSHA đã nghiệm thu rồi dựng từngreceipt. Sauđó nghiệm thu model/numericalparity/binding thực và outerCPUcache/graphcache. Không dùng sourcecheckoutCRLF hoặc fakeD22alias.

Wrapper vẫn là nativefallback/CPUcontract; numericCPU/H100split cần được nối riêng bằng cache hợp lệ sau guardfix. Thống kêfinalfamily/p-value vẫn theo request đãfreeze trước khi xemoutermetrics. Chưa chạyouterlabels hoặc sinh kết quảRQmới.
