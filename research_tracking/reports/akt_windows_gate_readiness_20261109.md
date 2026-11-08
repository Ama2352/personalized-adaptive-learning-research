# Windows CPU software Gate hiện hành — 09/11/2026

FullGate03 đã được nhận với **1.418 test PASS, 0 failure/error/skip**, đúng toàn bộ
node IDs của collection09, trên **154 source files và69 test modules**. Native
suite355,0576142s/580; outer receipt358,7608751s/630; owned launcher gồm cleanup
356,8031714s. Đây là software Gate synthetic trên Windows CPU, không kết quả
nghiên cứu hoặc chứng nhận Linux/CUDA. Không promote `gate2-current.json`.

Bằng chứng chính: [native report](../../artifacts/akt/preflight/gate2-evidence-win-current-gate-20261109-03.json),
[merged JUnit](../../artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-03.xml),
[outer receipt](../../artifacts/akt/local-tests/akt-research-runner-20261108-01/win-current-gate-20261109-03-outer/result.json).
SHA native report`5a0bc5ed6fa2f0d799710f03fb17612ea0b5dbb14ce6414410f98dbfd54c85e8`;
outer`fef18bdbd45ccb9eb6a42f11da0c26bc50fc54ab4d503edbf13024562accb45e`.

## Population được chốt trước khi chạy

Collection dùng ba tiến trình mới, chỉ import/collect, không test bodies. Sau
mỗi thay đổi source, ROOT chốt hash mới và collection lại; expected count không
lấy từ một báo cáo PASS. FullGate đối chiếu classname/name JUnit của từng nhóm
và merged với chính installed pytest mapper đã pin, kể cả parameter IDs.

| Pha | Kết quả thực tế | Stored outer elapsed |
|---|---|---:|
| Collection06 | Reject trước pytest: opaque hash startup `.pth` bị checkpoint suffix guard chặn |2,639326s/60|
| Collection07 | Accepted population1417=19+271+1127; không GatePASS |39,475048s/60|
| FullGate01 | Failed:19ERROR fixture setup nhóm stdlib, chưa test bodies |5,725125s/630|
| Focused basetemp01 |77PASS/0FES; actual TempPathFactory/filesystem, publisher subprocess/report fake |8,231253s/60|
| Collection08 | Accepted population1418=19+271+1128, sau thêm một regression |38,717284s/60|
| FullGate02 |1415PASS+3FAIL/0ERROR/0SKIP; toàn bộ1418 IDs đã được chạy |291,582001s/630|
| Focused scratch02 |77PASS/0FES trên source sửa layout, không thêm cases |6,461477s/60|
| Collection09 | Accepted population1418, hash hiện hành |42,553559s/60|
| FullGate03 |1418PASS/0failure/error/skip; outer accepted |358,760875s/630|

Các elapsed trong bảng lấy từ từng final/result JSON; không thay bằng thời gian
terminal/GUI hoặc thời gian pytest. Mỗi lượt có review/cap riêng và giữ failure;
không cộng số lần chạy thành independent experimental N hoặc chọn positive subset.

## Hai lỗi Gate và phạm vi sửa

FullGate01 thiếu UUID intermediate directory: refresh chỉ mkdir parent chung,
trong khi pytest TempPathFactory tạo basetemp leaf bằng mkdir(parents=False).
Fix tạo UUID root độc quyền, reject alias parents, giữ ba group leaves. Regression
thực sự gọi installed TempPathFactory.getbasetemp/mktemp, ghi/đọc payload và kiểm
marker của cả ba nhóm còn nguyên; trước API có thể recursively delete một path,
test yêu cầu leaf mới, absent và thuộc fresh owned fake project.

FullGate02 đi hết1418 IDs. Hai CLI recovery cases và một pilot lifecycle case
lỗi DuckDB COPY `.pending/<uuid>-00000.parquet.tmp`; đường dẫn262/262/264 ký tự,
parents211/211/213 ký tự tồn tại khi kiểm bằng PowerShell/.NET. Python source
mkdir trước COPY, nhưng không có live Python/DuckDB threshold probe trong lần
điều tra. [Population postmortem](../../artifacts/akt/local-tests/akt-research-runner-20261108-01/windows_current_gate02_population_postmortem.json)
và script đi kèm xác nhận exact IDs/0E/0S, không tạo merged XML hoặc PASS giả.

Fix chỉ rút scratch ancestor từ `gate2-<run_id>-<uuid32>` thành
`gate2-<uuid32>` dài38 ký tự. Với actual run ID, tiết kiệm29 ký tự; không đổi CLI
run IDs, durable report/log/XML names, prediction layout/serializer, targets hoặc
test coverage. Regression dùng valid run ID80 ký tự, kiểm bounded scratchprefix
và artifact names vẫn giữ full ID. FullGate03 sau sourcefreeze/recollection mới
đã PASS, phù hợp với chẩn đoán path inflation; chưa chứng minh mọi native library
có cùng MAX_PATH threshold hoặc toàn bộ path dài tùy ý đều được hỗ trợ.

## Source/runtime/ownership

Nguồn nền154files đã được ROOT đối chiếu raw Git commit`2c337d4` với inventory
bacc6…; [raw Git proof](../../artifacts/akt/local-tests/akt-research-runner-20261108-01/gate_frozen154_raw_git01.json).
Sau đó chỉ hai members thay đổi: `scripts/akt/refresh_gate2.py` và
`tests/akt/test_gate2_refresh.py`. Hai cặp before snapshots giữ nguyên byte;
current hashes lần lượt`9608ddfe1450b2d78699d5ec95d26b8cd65d4439fcc7bda209f698b2e4a7f9ef`
và`255c07a3a1af2d458c8586bd206a3151baadeae76d1fa0a2ce3362409da8d5df`.
Freeze03`b0030c112a9ea72c8aecdf7d86675ea575f47c962f7800f36ee581648051ae6b`
và collection09`17c8df38435c74bc2718b544c7dbd33c9d9cd7ef46e360de3b7018aaf8e2c476`
gắn với Gate03 packet`7e6fe2342eb402b5ec0927ee8f1e13a5326b558ed0df71d5ae8a2c5e5c750015`.
Current154 raw-Git verification sau commit hai fixes là bước ROOT làm riêng;
proof2c337d4 không được relabel thành proof current commit.

Native dùng exact `.venv/Scripts/python.exe`, runtime preflight hợp lệ và
Windows lock SHA`3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a`.
Không cần old Gate pointer để admission tạo Gate mới. Namespace `scripts` có
ROOT đứng đầu và installed pywin32 namespace hợp lệ; project children phải đúng
ROOT. Provenance pywin32 so bytes15files với installed RECORD, không wheel/network
attestation; không thực thi các script namespace. Guard checkpoint không bị bỏ:
startup `.pth` được outer opaque-hash, inner giữ nguyên suffix guard.

Reuse Windows owned worker helper nguyên byte: actual waiting worker thuộc exact
Job trước GO, cleanup cả descendants, Jobactive0/Popen handle closed. Caps đã
chọn chặt hơn historical maximum: native580s, owned≤600s gồm cleanup3s, active≤597s,
outer630s; available admission4GiB, floor1GiB, mỗi observed worker/descendant≤3GiB.
Gate03 quan sát peak520.663.040B, min available4.487.327.744B,2522 samples.
Polling/late rejection là cooperative; không hard OS RAM quota hay whole-host
orphan/syscall attestation. Source/lock/runtime/collection bindings được recheck.

## Cách đọc bằng chứng và giới hạn

Collection07/08/09 là import/identity evidence; focused77 là software regression;
fullGate03 là full software-suite acceptance trong population nêu trên. Full suite
có các toy lifecycle/model cases theo source đã review, không claim0optimizer cho
cả1418 tests và không coi chúng là research fits. Không rerun corpus/teacher,
Junyi/Holdout benchmark, GRAPH04 driver hoặc Method24 fit trong việc đóng archive.
Gate chỉ gồm `tests/akt` và `tests/shared_kt`; new SAKT checkpoint source/tests
ngoài154/69 không được chứng nhận bởi Gate này. Không suy RQ completed, efficacy,
selected/refit/resume lifecycle, Linux/CUDA/image/Modal readiness từ kết quả này.

Các failures collection01–05 giữ trong [bundle lịch sử](../runs/gate-collection-engineering-20261109-01/README.md),
manifest SHA`aa3d46e5bc6898480503c90cc07a7e027e7735d616284ddafd4c91111c901d7d`;
không copy lại hoặc sửa oldbundle. Archive mới dự kiến
`akt-windows-gate-readiness-20261109-01` chỉ chứa raw nhỏ06–09, full01–03,
focused hai revisions, source overlays/controllers/receipts và copy inventory
SHA trước/sau; không154source copies, `.venv`, models, corpus, ZIP hay privateRPC.
ROOT review và đóng archive riêng; không chạy lại test khi archive.

Native03 mặc định không publish. Pointer bytes trước/sau không đổi; promotion
là thao tác ROOT review riêng, không được suy là đã xảy ra từ native/outer PASS.
