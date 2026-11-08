# Addendum trước implementation: relocation metadata nguyên byte

08/11/2026; áp dụng cho contract `GPU_HOST_HIDDEN_AUDIT_CONTRACT01.md`, không sửa contract/bundle cũ.

Discovery raw nằm **ngoài project ROOT** tại `/content/KLTN_GPU10_DISCOVERY_20261108_01/...`; acceptance là receipt **dẫn xuất local** từ RPC đã kiểm. Hidden auditor không giả các locator đó là file gốc sinh trong ROOT.

Một preparer riêng, không auto-run audit, sẽ copy exact bytes vào thư mục mới độc quyền `ROOT/artifacts/akt/gpu10-hidden-inputs/<attempt>/`. Không rewrite nội dung/path trong raw discovery/profile/acceptance, không overwrite stage cũ. Inventory relocation schema1/role `EXACT_BYTE_DISCOVERY_RELOCATION_NOT_EXECUTION` ghi từng label, original locator, origin kind, destination ROOT-relative, bytes, SHA trước/sau; CLI audit pin SHA inventory này. Label bắt buộc: baseline, fresh, launcher, acceptance, profile; optional startup_manifest. Acceptance giữ `LOCAL_DERIVED_RECEIPT_FROM_VERIFIED_RPC`; fresh raw giữ `REMOTE_DISCOVERY_ARTIFACT`; baseline vẫn CPU baseline. Metadata-only copies không chứng minh install hoặc mới chạy trên GPU host.

Controller chỉ đọc copies đã pin và ghi locator/provenance vào output. Fresh bắt buộc là **operation mới sau manual GPU selection**, wrapper/approval/attempt có nhãn generic GPU-host riêng; không relabel CPU raw `b003...`, launcher hoặc acceptance cũ. Source02/profile0944 chỉ reuse khi actual ABI/source/package fingerprints còn khớp. Không có fresh proof hoặc gặp cold/partial/unknown startup thì STOP trước target child. Input-copy preparer nằm ngoài batch controller/test hiện tại, không có implicit phase transition.

Startup-hook facts root đang thu trên currentCPU chỉ là baseline để review actual bytes; không gọi chúng là fresh GPU-host audit. Original locator và scope phải giữ nguyên khi copy. Không tự lấy hash/body từ Windows hoặc ký ức để cho phép hook.
