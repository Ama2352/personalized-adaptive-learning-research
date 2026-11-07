# P2 SAKT checkpoint: bind đúng payload deserialize — 08/11/2026

Run ID giữ ngày07/11 của batch. Đây là follow-up engineering, không sửa bundle
sakt-inference-engineering-20261107-01 (37outputs/source87snapshot). Review trước
chỉ static đã phát hiện stat/hashpath/loadpath/posthash có thể đọc A→B→A.

Giữ2regressions fail-before/7,88s và full89pass-after/7,33s (37core+52adapter),
exact source/test snapshots/logs/XML/run/pre-postSHA của từng attempt. Không
collection errors/skips; mọi invocation dưới120s,0optimizer/GPU/realdata/cloud.
Archive không chạy lại tests/model. Final adapter chỉ đổi bounded singlepayload
maxbytes+1, SHA payload, torch.load(BytesIO(payload),weights_only=True,map_location=cpu).
Bounded postpath guard là consistency check, không security basis cho A→B→A.

Rawstate_dict/config/vocab/domain/frozen conventions giữ; random/unverified scores
không thành fitted/OnlineSession/trainer/calibration. Byte cap là serialized bytes,
không peakRAM/decompression attestation. Negative-control fixtures không mặc nhiên
loadable/finite.54 .pt files chỉ inventory/hash, không copy binaries.

Platform agent đã review read-only patch/tests/logs, không rerun/edit và không
còn blocking issue trong phạm vi P2. reviewer_note.json ghi đúng giới hạn đó;
không là scientific approval/Gate16/SAKT efficacy. Core/shared/AKT không sửa.

archive_copy_inventory_before.json lập trước copy; archive_copy_inventory.json
đối chiếu source pre/post/destination. Previous37output manifest+README được
snapshot và verify output-only trước/sau closure. Parent cần review/index/Git
riêng; không sửa shared indexes/state/tasks hoặc chạy paid/fullCV trong gói.
Report/script còn dùng repository paths gốc; bundle không là standalone runtime.
Không thêm/sửa outputs sau closure; helper verify chỉ đọc SHA outputs.
