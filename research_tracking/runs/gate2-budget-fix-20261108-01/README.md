# Sửa ngân sách Gate2 — evidence đóng ngày08/11/2026

Gói operational bugfix targetedPASS, không là full Gate chấp nhận source mới,
không training acceptance/efficacy, không adoption S04/S05. Archive chỉ copy/hash/XML;
0tests/model/optimizer/GPU/data/cloud chạy trong lúc đóng gói.

## Bằng chứng giữ lại

4source/test trước sửa khớp buildSHA của Gate20; actual RED01:44tests19PASS25FAIL.
Final02:47PASS0fail/error/skip, gồm3invalid-clock cases thêm sauRED.
Controllers10.797052+9.366551=20.163603s<60s,0optimizer/fit ở targetedGate tests.
Fake successful child/nonemptyJUnit nhưng1084s>540 phải giữ pointer nguyên byte,
ghi reportREJECTED_RESOURCE_BOUND độc quyền rồiTimeoutError; reader từ chối cả
resourcefields đãrehash. Timeout1..600/default300 và schema1 giữ nguyên.
OMP/MKL/OpenBLAS2 là childsoftwareCI bound, không scientific model default.

[Report nguyên byte](gate2_elapsed_budget_fix_report.md),
[verification](archive_verification.json), [before](archive_copy_inventory_before.json),
[after](archive_copy_inventory.json), [binding](source_binding_comparison.json),
[docs chính thức](official_primary_sources.json), [links](selected_links.json),
[ignored paths](force_add_paths.json), [whitespace](raw_whitespace_inventory.json).
Report snapshot giữ relative links theo canonical report directory; không rewrite.

## Gate20 và trạng thái lúc snapshot

Gate20 original SHA9d86b215bd936f04880bcd9bc775f2016784f279572109c39c017d46375fe351
bất biến.724functionalPASS nhưng1083.995106s>540: ngân sách không đạt.
Giữ report/log/XML, auditrejection, helperrevocation snapshot và pointers trước/sau.
Currentpointer tại closure trỏ rejection; actualreader từ chối. Gate21/source mới
chưa được gói này chấp nhận. Snapshot pointer có thời điểm; không tự cập nhật
khi parent phát hành Gate mới. Không rerun scriptrevocation đã lưu: đây chỉ là
historical source snapshot và nó có sideeffects ngoài phạm vi archive này.

## Exact refit diagnosis và giới hạn

Giữ1testsynthetic refit chạy riêng:1PASS/8.452sJUnit7.896stest,
12.055534scontroller<45s, threadenv2/actualintraop2interop12, CUDAfalse.
Không gọi lượt đó là0optimizer: testrefit gốc có tiny training/recovery updates.
Archive không chạy lại và không copy/load .pt/Parquet hoặc pytest temp dirs.
G18/G19 cùngtest1.682/3.087s với4selectedcodeSHA giốngG20; G20test922.520s.
Không xác định nguyên nhân: query10KernelPower42/107timestamps bịAccessDenied;
không escalation. Sleep/suspendUNKNOWN. OfficialWait/QPC semantics là cơ chế
có thể phù hợp, không là causal evidence. ClockgapUTC không xác nhận sleep.
Rawmetadata có trailerliteralbackslash-n giữbyteexact; normalized companion
bỏ đúng2ký tự vớiSHA/provenance. Không fake failure/model rerun vì lỗi format.
Initial metadata-only helperimportpathmiss được ghi ở finalverification.

Postelapsedguard chặn falsePASS sau khi child hoàn tất, không hardinterrupt
tronghostsleep/OSblocking call. Không trừ elapsed theo sleep suy đoán.
No rootindex/state/Git/source changes trong archive; helperverification chỉ
integrity, không validity nghiên cứu. Giữ rawfailure whitespace nguyên byte.
Không sửa bundle sau closure. Tái lập dùng runpath mới, .venv và cap rõ ràng;
nguồn snapshot cần repo/runtime tương thích, không standalone executable kit.
