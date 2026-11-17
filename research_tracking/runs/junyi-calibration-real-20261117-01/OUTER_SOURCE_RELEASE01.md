# Sourcepacket outer và biên nhận A2

Ngày17/11, dựng một nguồn mới tại `artifacts/akt/local-calibration/20261117/outer-source-guard-release/source`. Gồm161filecode/tài liệu nguồn,2.028.325byte, nhỏ hơn cap4GiB của gói. Không sao chép dữ liệucanonical, modelweights, venv hoặc dependencybinary. SOURCEfrozenD22cũ được đọc lại77SHA và giữ nguyên. Không đụng tiến trình A2/A3CPU đang chạy từ nguồn cũ.

Trước khi sao chép, `OUTER_SOURCE_COPY_PLAN01.json` ghi đủinventory nguồn/đích/size/SHA. `OUTER_SOURCE_COPY_ACCEPTANCE01.json` xác nhận copy đúngbyte. Gói lấy toàn bộ159Pythonfile của srcfrozen, Protocol21 và upstreamAKTLF. Chỉ windowcacheguard lấy bản mới đã duyệt.

Driver `prepare_outer_guard_source01.py --prepare` chỉ dựng đích mới, từ chối ghi đè. Chạy driver không có `--prepare` tạo process mới, đưa newsource/src đứng đầu sys.path trước importKT, dùng ROOT.venv. Log `OUTER_SOURCE_VERIFY01.txt` xác nhận77runtimefiles thật khớp map release, identity `7c72414eedf9507d514430aed4734f0a192ab14914a4984b17fdfcbfebd39123`, không mock và không importTorch.

Biên nhận `A2_OUTER_SOURCE_COMPATIBILITY01.json` đã có checkpointSHA từmodelindex và calibrationidentity từ `LOCAL_A2_FIT_ACCEPTANCE100.json`. Temperaturepayload được parse/validate bằng implementation gốc, identity khớp nghiệm thuDrive. Validatorcompatibility đã đọc sourcemap thực và exactguardpatchproof. `A2_OUTER_SOURCE_ACTUAL_VERIFY01.json` giữ pins của inputacceptance/modelindex/wrapper và provenance hai nguồnD22→7c.

Nghiệm thu này chỉ xác nhận **sourcefiles và A2metadata pins**. Không nạpweights, không gọi predictoradmission, không kiểm CUDA/numericalparity, không đọc outerlabels hoặc chạy cloud. Còn cần receipts cácvariantkhác, model/parityadmission thật, CPUoutercache/graphcache/counts và H100numeric theo request/budget. ReceiptSHA chuẩn hóa nội dungJSON trong provenance có thể khácSHA nguyênbytefileprettyJSON, cảhai được ghi theo đúngnghĩa.
