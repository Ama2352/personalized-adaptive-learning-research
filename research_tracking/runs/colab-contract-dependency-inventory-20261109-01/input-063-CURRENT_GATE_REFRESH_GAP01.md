# Làm mới software Gate sau batch graph — source review09/11/2026

Không import Python/test/native, không chạy collection/build/upload, không đổi
Gate/pointer/authorization. Các con số filesystem dưới là snapshot trong lúc
`research_main_execution.py` còn WIP; không phải final freeze hoặc collected count.

## Gate đang trỏ tới đâu và vì sao đã stale?

`artifacts/akt/preflight/gate2-current.json` SHA9e768aad…365cd6 trỏ report
`gate2-evidence-win-current-gate-20261109-03.json` SHA5a0bc5ed…4c85e8:
actual1418PASS=stdlib19+no-torch271+remaining1128,69test modules/154build paths.
Giữ nguyên bằng chứng này; không dùng nó chứng nhận source mới.

Đọc đúng membership của `authorization.py:96–113` bằng filesystem enumeration+
SHA, không import hàm: lúc review có174paths/79test modules, **20added/0changed/
0removed** so với154oldpaths. Tất cả154bytes cũ còn nguyên. Membership mới tự
làm reader `authorization.py:162–169` bác vì `build_hashes` phải bằng cả map hiện
hành, không chỉ subset hoặc Git HEAD.174/79 chưa là population cuối; source/test
producer đang viết có thể tăng tiếp. Local builder patch được ROOT cho phép sau
snapshot này cũng sẽ làm hai oldpaths đổi (builder và focused test); phải chốt
lại toàn map sau mọi freeze.

20paths mới gồm graphcondition/context/model/checkpoint/online/mainstage,
main_execution(WIP), sharedadmission/selection, script query-decision overlap và
10test modules tương ứng (graphoptimizer chỉ có test mới, không module sản phẩm
riêng). `research_selected_runner.py` chưa tồn tại tại thời điểm enumeration;
không tính trước nó hoặc test tương lai. Không cộng các con số PASS của bundle
riêng thành expected fullGate count.

## Những component mới cần đi vào population

|Nhóm đã freeze|Source revision đang đọc|Tác động Gate / compute cần phân biệt|
|---|---|---|
|Condition/context|6678f04c /8bfe0dca; tests2fdd512c/d54b188c|NumPy data/index, không constructor NN; import aliases đã sửa không reload|
|Graph model|77e365e4; test579359ff|Module fixture A3 native,25cases ở lượt riêng;8forward/5logicalbackward chỉ là inventory lượt riêng|
|Actual Adam|test5bdc3e53|Một testcase/3batches;3actualAdamsteps trên adapter riêng, không phải3testcases|
|Checkpoint|f40b47e6; test332c48af|Pure metadata và native fixture chung; manifest119outputs ghi native16cases/2adapters/2Adam/4updates, không16models|
|Dynamic query evidence|c44ad90a; testd9dc5e62|35NumPy cases ở lượt riêng; chưa dynamicmodel/backend|
|Admission/selection|b8601da0/0e3cf12d|Pure metadata/statistics; không fileadmission/freeze authority|
|Main stage|77b7dbfd; test68f1e029|Pure14methods, epochvalidation mỗi epoch; NO_EXECUTION_AUTHORITY|
|Overlap cached join|script/test mới|Pure manufactured inputs ở test; không mở actual1.080rows khi Gate chạy|

Native module fixtures, imported helper factories và autouse imports có thể được
chia sẻ/cached trong cùng remainingprocess. **Không cộng cơ học standalone1+
1+2constructors hoặc8+3+6forward làm global hardcap.** Collection chỉ xác định
node IDs/fixtures, không đo body count. Nếu ROOT thêm global NN accounting cho
fullGate thì phải audit fixture graph trên population đã collect và bound cả
setup failure/parameterization; giữ actual phase/counter ledger riêng. Existing
fullGate outer chủ yếu bound thời gian/RAM/ownership, không có global8/5/0cap.
Không gắn cap pure0hoặc standalone3Adamsteps vào toàn remainingprocess.

## Batch refresh tối thiểu, một lần sau source freeze

1. Chờ main_execution/selected_runner và test owner kết thúc review+bounded
   checks; chốt source/config/dependencyclosure. Không làm Gate giữa các WIP rồi
   lập tức invalidate. Tạo packet freeze MỚI, không dùng
   `prepare_current_freeze03.py:25–28` vì nó chỉ cho154/69 và exact2oldchanges.
   Native `gate2_build_hashes`/`test_partition` đã tự lấy file mới; không cần sửa
   production glob hoặc chia lại groups chỉ để cập nhật count.
2. ROOT thực collection mới của cả3freshgroups theo canonical partition, whole60s
   như review trước (nếu không fit: retain/STOP, không autoretry rộng hơn).
   Reuse worker09 flow: GO trước domain imports, profile/testbody/constructor/
   solver/backward/step/data/CUDA guards vẫn0, `--collect-only -p no:terminal`,
   ROOT-first real scripts namespace và actual pinned pywin32 namespace proof.
   Imports execute tops; không gọi đó là0Python execution. Fresh result phải có
   node IDs exact/groupunion/moduleorigins/sourcebefore=after/cleanup0.
3. Derivative controller/descriptor mới trong prep hiện có: worker01
   `load_collection:59–60` hardcodes154/69 nên phải bind **ROOT-finalized source/
   module population** mới, không suy count từ test PASS. Các map và exactnodeIDs
   vẫn bắt buộc. `windows_current_gate_outer01.py:20` trỏ worker01;
   `prepare_windows_current_gate_packet02.py:13–14` trỏ cả oldpair. Chỉ cần new
   derivatives cập nhật path/pin/population này, reuse nguyên helper0dc, native
   refresh command và JUnit mapper; không copy Kernel/Job infrastructure.
   Preserve các scripts/packets/receipts07–09/oldGate03 bất biến.
4. Producer packet dùng actual accepted collection/result/source refs và external
   ROOT SHA; map installed `_pytest.junitxml.mangle_test_address`+
   `bin_xml_escape`, reject collisions, pin mapping utility byteSHA và group+
   merged IDs. `expected_native_counts` ở packet cũ là **JUnit case counts**,
   không NNoperationcounts. Không dùng1418 hoặc đoán một count17xx mới.
5. Sau review/preflight actual4GiB free, ROOT chạy đúng một fullGate invocation:
   native580/owned≤600 gồmcleanup3/outer630,1GiBfree floor/3GiB perprocess.
   Không tự tăng cap nếu chưa fit. Giữ3freshnativepytestprocesses với toàn modules,
   không -k/deselect. Không rerun riêng các unchangedgroups hoặc old77regression
   trước fullGate khi chưa có failure/sourcechange mới: canonical fullGate đã
   chạy chúng một lần. Không chạy lại GRAPH10/CP standalone native chỉ để lấy
   counters nếu source đã freeze và evidence riêng còn khớp.
6. Outer kiểm exact executedJUnitpopulation/group/merged0FES, fullsource/lock/
   upstream/currentruntime/resources/Job0/envrestoration/postwall. Default vẫn
   **NO publish-current**; actualreport được validate độc lập, không yêu cầu
   oldGate phải accept trước Gate mới. Pointer promotion là bước ROOT review/CAS
   riêng sau accepted outputs; không override oldreader hoặc thay số trong report.

Current runtime có thể reuse nếu native `preflight` vẫn thực sự chấp nhận đúng
upstream/lock/interpreter/prefix/origins và host; buildmap đổi không tự làm Torch
ABI đổi. Fresh RAM admission luôn đo mới, không dùng available_ram trong report
cũ làm current fact. Không đòi20Gitcommands cho mỗi object: source loader cached
có thể hợp lệ trong shared process nếu source/HEAD/rawbytes/context khớp; record
fresh-vs-cached target identity, không substitute fake loader để vượt provenance.

## Packaging và Linux là acceptance khác

`build_colab_bundle.py:17–34` rglob mọi source nên đã lấy module mới nhưng hiện
không lấy docs21/26. `research_graph_condition.py:24,56–63` đọc actualrecipe26;
`research_graph_checkpoint.py:112+` đọc actualprotocol21. Thiếu chúng sẽ làm
newLinuxkit fail trước intended cases dù Python files có đủ. ROOT cho phép local
builder-only patch sau review: fixed21/22/23/26 vàEXPERIMENT_ALLOCATION, không thêm
arbitrarydocs/private/auth/data.21+26 là dependency hiện hành;22/23/allocation
đóng closure cho stage/main-driver saufreeze. Focused tests chỉ inventory/closure/
notebook-strip provenance, không ZIP build/upload hoặc training.

Bundle builder lấy nestedSAKT/GKT source nhưng Gate chỉ chạy tests/akt và
tests/shared_kt; bundle membership không chứng minh SAKT/GKT suites được chạy.
Notebook stripping phải giữ original→copy SHA/transform metadata. Linux host
cần actual materialization map/lock/origins/runtime report đúngplatform và fresh
softwareGate, không dùng WindowsPASS thayLinux/CUDA acceptance. SOURCE EXPORT
auto-review denial trước đây vẫn binding: note/localbuilderchange không cấp quyền
build-upload, remote, hardwarechange, Modal hoặc chi phí.

## Blockers trước expensive GPU readiness

Final WIP/source/test freeze; dependency-complete local packaging; acceptedfresh
collection+reviewed newpacket/controller; actual fullWindowsGate under existing
resources; nếu chuyểnhost thì actualLinuxruntime/materialization/Gate riêng.
SoftwareGate chỉ software; GPUport/device/actualCUDA/throughput/cost vẫn cần đúng
stage của chúng. Không đưa các prerequisites giả như repeatedoldtests, all-model
freshGitloading hay objectSHA-only authority vào đường găng.

Source đọc: authorization bd6be914…ac7f0; refresh9608ddfe…7f9ef;
currentpointer9e768aad…365cd6; oldreport5a0bc5ed…4c85e8. Đây là read-only gap note,
không runnable packet, allocation, newPASS hoặc cập nhật root tracking.

## Bổ sung local patch theo ROOT review, chưa execution

Đã thêm đúng5fixed public contract paths vào builder, giữ bytecopy và toàn bộ
notebook transform algorithm nguyên. Builder4fdb7e95…94aabb/test29f3ccea…699295;
snapshot oldbuilder97418862…95ef4/oldtest3b7207c8…00396 và before/copy/afterSHA
tại `colab-contract-docs-before01`. Không nested AGENTS ở scripts/, scripts/akt/,
tests/, tests/akt/ trong lần kiểm tra. Test source dự kiến8nodes (old1 +closure1
+synthetic inventory1 +5missing-doc parameters), chưa collect/run. ROOT nên dùng
short fresh basetemp để synthetic Paper2 paths dưới Windows path limit. Tests
chỉ gọi `bundle_contents()` local và synthetic tmpFS, không main()/ZIP writer;
giữ assertion3notebook transforms/sourcecells/rawhash và no arbitrary docs.
Không có ZIP, upload, source export, test hoặc Git mutation từ agent. Vì vậy
174/79 và20added/0changed ở đầu note chỉ là **pre-patch snapshot**, không final
Gate recipe; cả hai known oldpath changes này phải vào freeze tiếp theo.
