# Actual tiny A0 selected-only — nguồn chờ ROOT review

## Input thật và mục tiêu

Corpus engineering10×84 đã được ROOT nghiệm thu tại `main-engineering10x84-01/outer-final.json`, SHA `e1745fc0423fd9660218d49a51a57126ac74d40810a2f6c58c8f776bd554c127`. CorpusID `grade10-main-lifecycle-engineering10x84-20261109-01`, corpus SHA `78da1a4fd1708bb1efca723caed4976ed518687eb70b847fbdf780f111191151`, DONE SHA `9b565431267a1e0e6f6fb4c05b42a989b2d533d2de98991e64927149b1c5b710`. Closed evidence tại `research_tracking/runs/akt-main-engineering-corpus10x84-20261109-01/manifest.json`, SHA `9c90a35429503ab146711460a543fea2b61a2e06ddd2a0ad7d287394f1bc6bfc`. Hồ sơ actual17files và840teacher returns là đầu vào đã có, không được generate lại.

Mục tiêu bước sau là kiểm đường đi thật `run_main_selected_candidate` từ actual authorization/guard qua complete epoch, per-epoch selection, chosen checkpoint, fresh best reload và raw export. Đây là integrationfixture mới, không fit research-main9 hoặc thay canonical60. Không có refit90, temperature calibration, external systemfreeze, CUDA hoặc resume. Bản source này chưa được chạy/import/test; config/auth/request/dry vẫn chưa được tạo bởi agent.

## Bốn script và hai giai đoạn tách biệt

1. `prepare_main_tiny_a0_package01.py` cùng `run_prepare_main_tiny_a0_package01.py` là derivative của metadata builder đã kiểm trước, namespace mới. Actual public10 pins được lấy từ accepted17file receipt nêu trên, lọc đúng public9+DONE, không mở oracle. Dùng typed publicreader, GraphTrain80Binding/A0 empty condition từ **corpus mới**, normal specs, genuine private `_metadata`/native preflight/Gate checks. `--prepare-dry` chỉ tạo wrappedPdry có execution_authorityfalse và operational receipts, không actual config/auth/request. Sau ROOT đọc exactdry mới có thể `--materialize` exclusive ba artifacts, namespace operational riêng, giữ partial nếu lỗi. Mỗi mode50worker/60whole, RSS1GiB/free2GiB.
2. `check_main_tiny_selected_a0_01.py` cùng `run_main_tiny_selected_a0_01.py` chỉ chạy sau ROOT cấp actual request/auth/config đã review. Worker tái dựng đúng public dataclasses rồi gọi normal public entry **một lần**. Không preliminary guard, caller guard, fake callback, model factory, manufactured corpus hoặc skip authorization. Factory và core tiếp tục gọi nguyên hàm validators/trainer/checkpoint. Runtime3fdddca8… và Gate indexe8162f6e… giữ riêng với globalpointer, nguồn177 phải current.

Metadata dry dùng genuine `_metadata` private dependency, không tự thay production API hoặc nhận boolean chứng nhận. Nó không được coi actual guard admission/fit. Materialized config/auth là allocation mới, không dùng lại canonical60guard-only auth. A0 stage external graphConditionNone nhưng implementation condition là empty A0 tính thật trên newTRAIN80 provenance. Selected stage source identity vẫn là đúng map177; scratch source pins nằm riêng trong request.

## Recipe và trần công việc

Giữ nguyên simulator-research config seed42, native256/8heads/1block/d_ff1024/final_fc512, dropout.05, context100/target100/max_length200, batch4, lr/betas/eps/weight decay/clip và20epochs/patience3/min_delta.0001. Chỉ allocation mới được đổi cho engineering lifecycle, không thay protocol/hyperparameters.

|Đại lượng tối đa|Giá trị|
|---|---:|
|Learners train/selection/calibration|8/1/1|
|Events train/selection/calibration|672/84/84|
|Train windows/epoch, batches/epoch|8,2|
|Actual Adam/backward/train-forward groups|40|
|Optimized target exposures|13.440|
|Model và Adam constructors|2 và2|
|Epoch validation + final fresh-best prediction passes|21|
|Selection target exposures|1.764|
|Native forward calls, gồm train + selection|61|
|Best checkpoint saves, inspect, fresh restore|≤20,2,1|

E thực tế phụ thuộc early stopping, không dự báo trước loss hoặc selected epoch. First finite epoch có best, patience3 nên successful E thuộc4..20. Với E epochs và S saves, actual train2E/targets672E, selection E+1pass/84(E+1)targets, nativeforward3E+1, freshconstructors2/restore1. Không chấp nhận partial epoch hoặc giảm epochs để fit budget.

## Resource allocation đề xuất đã chọn để ROOT chốt

Native Main wall540s, training300s, worker560s, owned580s gồm cleanup3s, wholeouter600s gồm finalization5s. Giữ helper0dc và hard maximum600 của helper, không nâng hoặc bypass. Host freeRAM≥2GiB, worker RSS≤1GiB; outer preflight disk≥2GiB. Native output≤1.536MiB, checkpoint≤64MiB/file, metadata≤1MiB/file, max_prediction_bytes4MiB. Mỗi save vẫn reserve64+2×1=66MiB theo nguyên source. Retain tối đa20best cần conservative1.320MiB checkpoint envelope, còn216MiB cho journal/JSON/CSV và reserve khác. Đây là quota bảo vệ, chưa là kích thước hoặc runtime đã đo. Nếu actualbytes/quota/time không đủ thì fail, giữ partial, không retry/resume hoặc đổi hyperparameters.

Native540s gồm toàn bộ guard/source/data checks từ factory tới COMPLETE, không chỉNN. Worker/outer còn phải hash outputs và cleanup trong giới hạn riêng. Initial disk floor không bảo đảm disk không đổi giữa lượt; write failure là failure. Dataset nhỏ hơn canonical60 không chứng minh 540s đủ.

## Observer và acceptance không sửa thuật toán

Observer chỉ passthrough methods/functions, giữ original args/returns/exceptions, exact classes/parameter identities. Không global profiler, không thay class, Adam.step hoặc backward. Main stdlib metadata wrappers được cài trước entry; **NN observers chỉ cài khi public entry thật gọi original lazy `_tools` sau actual guard**. Không importTorch/graphmodel sớm để instrument.

Observer ghi started/returned/exception counters và inclusive elapsed cho14targets gồm model/Adam constructors, adapter.step/predict_windows, ResearchGraphNative.forward, CPsave/inspect/restore, revalidate/_auth/_metadata/_main_native_evidence/_corpus và `_tools`. Có42counter fields, không phải42testcases. Returned được ghi ngay sau original return trước metadata postchecks. Lexical training/selection scope restore trong finally; selection targets đếm từ actual NumPy target masks, không suy từ native loss mask hoặc nhãn. Inclusive timings lồng nhau không được cộng. Original bindings được restore trước worker acceptance; monitor stopped phải được xác minh ở worker và outer.

Actual Adam started/body-returned/committed được đối chiếu từ nguyên durable `events.jsonl`, terminal counters và complete epoch receipts. Không thay tracker hook hoặc giả counter qua metadata. Full84prediction/target CSV keys phải exactunique/order-consistent, đúng selection role/raw_selection10 và supported84/unsupported0. Native fullbest reload/parity và sharedinitial-backbone checks giữ nguyên source. Worker kiểm opaque hashes với native COMPLETE inventory, outer kiểm lại toàn bộ native output subtree và bytes; không load thêm checkpoint để tạo “proof” riêng. Có failure override hoặc thiếu Jobcleanup thì không accepted.

## Hiệu chỉnh phạm vi Git so audit trước

Metadata dispatch count N=15+4E+2S trong audit nguồn trước vẫn đúng. **Tổng Git của actual fit còn có20lệnh từ hai backbone constructors**, vì `upstream.load_upstream` gọi genuine verify_upstream ở mỗi lần build. Vì vậy totalGit=10(N+2), không chỉ10N. Successful E4/S1 là350Git; full20/S7..20 là1.110..1.370Git. Worker whitelist đúng10-command cycle và ceiling1.370, không bỏ integrity checks hoặc dự báo thời gian. Cost note58700c99… đã freeze giữ nguyên lịch sử; đoạn này là erratum phạm vi tổng lifecycle, không sửa số actualguard20Git/10,923s.

## ROOT command sau review nguồn

Metadata operation đầu tiên dùng `.venv\Scripts\python.exe -B P/run_prepare_main_tiny_a0_package01.py --prepare-dry --worker-sha256 <exactmetadataworkerSHA> --outer-sha256 <exactmetadataouterSHA> --approval-reference <ROOTconcretePrepReference>`, với exactnative03Git profile được ROOT cấp và không strip. Review dry trước materialization bằng exactdrySHA/review-reference. Actual fit dùng `.venv\Scripts\python.exe -B P/run_main_tiny_selected_a0_01.py --request <actualnewRootRequestRelative> --request-sha256 <actualSHA> --worker-sha256 <exactfitworkerSHA> --outer-sha256 <exactfitouterSHA> --approval-reference <ROOTconcreteFitReference>` sau allocation review riêng. Không có request/auth hoặc dispatch nào được tự tạo/thực hiện ở lượt chuẩn bị source này.

Peer read-only review đã chốt API/call-accounting/lazy installation cho worker3720a519… và outera94a7126…, không chạy hoặc import. Nó không thay actual execution acceptance. Parent review/caps/source pins vẫn là bước tiếp theo. Required9candidates/twoenvironments được giữ trong nghiên cứu, còn output của fixture này phải có scope engineering-only, không dùng làm comparative efficacy/RQ completion.
