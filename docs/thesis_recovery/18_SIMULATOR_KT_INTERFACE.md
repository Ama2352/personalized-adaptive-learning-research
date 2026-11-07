# Hợp đồng nối KT với simulator — engineering CPU

Ngày07/11/2026. Tiếp REC01–REC06; giữ source/results Paper1/2, không train Junyi/GPU/Holdout. Đây là interface prototype cho thiết kế06, chưa thay controller hay chốt scientific protocol S04/S05.

## Các quyết định đủ bằng chứng để cài đặt

Paper2 có28concepts và84items, mỗi concept có item1050/1200/1350. AKT hiện mã hóa exercise và cửa sổ global target anchors, không nhận difficulty liên tục. Junyi vocabulary khác; checkpoint không có simulator-domain identity phải bị từ chối, không ánh xạ numeric indices giữa datasets.

Một session chỉ có một learner, một checkpoint/domain và lịch sử response quan sát được. Truy vấn candidate/reference item nhận item/time/source-row, không nhận current outcome hoặc latent theta. `observe` nhận outcome sau prediction, kiểm ticket cùng session/generation/history. Truy vấn không commit; nhiều reference queries tại cùng bước là counterfactual queries riêng, không phải fictitious practice events. Reset vô hiệu ticket cũ. Snapshot chỉ có history/provenance, không chứa simulator oracle.

Online prediction phải tái hiện đúng offline AKT global-block/context/OOV barrier semantics. Không cắt recent history rồi re-anchor block tại0. Không dùng unseen exercise như fitted prediction. History cap là budget explicit của session; không silent truncation. Weights frozen khi closed loop, update chỉ history.

Reference bank và weights phải khai báo rõ. Prototype trả `mean_reference_correctness`, coverage và missing items, không trả P(K) hoặc tự chọn mastery threshold. Thiếu reference item thì score None, không tự renormalize sang bank khác. Dùng84existing items là một lựa chọn draft, không sinh difficulty1250 giả vì chưa có exercise được train cho nó. Calibrator/threshold/action-controller mapping vẫn S04, cần protocol trước experiment kết luận.

## Gói và nghiệm thu

| ID | Mục tiêu | Nghiệm thu |
|---|---|---|
|SIM01|Item/domain/session/ticket/reference contract chung|Reject cross-domain, stale/foreign ticket, duplicate chronology, labels/oracle fields; queries pure; reset/snapshot isolation|
|SIM02|AKT next-item inference + checkpoint binding|Offline parity ở cold start, block boundary, OOV và partial block; checkpoint SHA/domain/recipe/vocab checked; model weights/RNG/mode không đổi|
|SIM03|Integration proof trên Paper2 item bank và native AKT|Bounded synthetic-trained fixture;84item/28concept mapping; probes không commit; no real-data training hoặc learning-benefit claim|
|SIM04|Persist source/log/hash/task state|Vietnamese report, immutable bundle, source-bound Gate2 refresh sau stable code, commit từng gói verified|

Không nối protocol vào run full experiment hoặc gọi native Paper2 `is_mastered` bằng score mới. Không tái sử dụng Junyi checkpoint cho Grade10. Không chọn reference weights/ngưỡng dựa trên Holdout hoặc final simulator seeds. Các tests chỉ chứng minh semantics phần mềm; diversity/coverage của training trajectories và calibration vẫn cần thí nghiệm riêng đã duyệt.

## SIM01/SIM02 — Kiểm chứng đầu

Pure contract10tests pass. Actual AKT fixture train8events, tối đa2updates; không random weights giả làm fitted model, không báo predictive/learning metric. Loader kiểm SHA, complete/selected role, training domain, vocabulary và inference recipe; giữ Torch RNG khi tạo container model. Online/OOV/block-boundary/history/reset/probe tests và model/export regression36passed24.80s (`evidence/20261107-sim-export-04.log`). CPU online/offline tolerance abs1e-6, không suy tolerance CUDA.

Phát hiện bug export: `iter_predictions` gọi `adapter.predict` trên window đã có geometry, làm re-anchor lần2. Fixture H3/T2 cho3/11predictions khác, maxabs0.00178698 (`sim-parity-02.log`). Thêm `predict_window` chấm trực tiếp, online và export cùng dùng. Đây là software bug ở cấu hình hợp lệ, không đổi hyperparameters/selection protocol. Fixture H100/T100 với205events vàOOV xác minh old-local-window và direct-window parity abs1e-6, cùng online boundaries. Không suy tất cả run cũ hỏng hoặc sửa historical predictions.

Lưu failures: `sim-online-01`14pass1fail do test setup dùng strict shared vocabulary cho OOV; sửa fixture encoding, không nới shared API. `sim-export-03`25pass10fail do FakeAdapter chưa cập nhật interface mới; đổi fixture sang `predict_window`, không fallback production sang re-anchor cũ. Logs giữ nguyên. Gate2 full build còn cần refresh sau SIM03 ổn định.

## SIM03 và review

Hai Paper2 bank integration runs train168synthetic targets/1epoch/1update, đủ28concept/84items. Run01/02 đạt lifecycle trong11.99s/11.07s; không là KT benchmark hoặc predictor of learning gain. Run02 dùng canonical immutable difficulty/weights và binding checks đã harden, frozen model state/reference scores trùng run01. Full checkpoint SHA khác do telemetry, nên history fingerprints khác là đúng. Xem report `research_tracking/reports/simulator_kt_interface_20261107.md` và repeat-proof JSON.

Review thêm direct-probe binding drift và nested reference mutability; sửa trước final gate.19native/contract tests passed19.86s (`sim-binding-05.log`), gồm timestamp-gap invariance của original AKT. Query timestamp không là elapsed-time feature: không dùng KT score14ngày làm retained latent mastery. Đây là architecture limitation, không phải bug cần sửa model. S04/S05 và simulator-training-data validation vẫn chờ protocol.

## SIM05 — Batch các counterfactual queries độc lập

Thêm `predict_windows`/`predict_many`/`probe_many`, mỗi candidate giữ riêng window từ cùng history. Chỉ dùng batch_size đã cấu hình, không đổi optimizer/training population. Backend không hỗ trợ batch được fallback tuần tự. Không concatenate reference items thành fake interactions, không commit ticket/history khi probe. Backend/session hiện sử dụng tuần tự trong một worker; không chạy training đồng thời trên model object đang inference.

Targeted41tests pass29.45s, kiểm OOV ở giữa query list, permutation, padding/variable-window length, wrong coverage, query cap và unchanged history. Run `cpu-sim-kt-interface-20261107-03-batch` cùng168synthetic training targets:84cold reference queries giảm native forward calls84→42 với batchcap2; maxabs probability delta5.96e-8 (<CPU tolerance1e-6). Cold probe CPU0.815s→0.393s trong fixture d16; cả lifecycle9.59s. Không ngoại suy d256/GPU/full-fold cost từ các timing này. Final source-bound Gate2-10 còn đang kiểm.

Batch tolerance không bảo đảm boolean mastery giống hệt nếu score nằm sát ngưỡng trong mức sai số số học. Protocol sau phải ghi inference batching/numerical convention và phân tích near-threshold sensitivity; không tự đổi threshold ở đây. Không cache score qua `observe`: global attention có thể đổi mọi candidate probabilities, không chỉ concept vừa practice.

## Nghiệm thu cuối

Gate2-10 đạt296passed,0failed,0errors,0skipped,292.02s. Source/lock/upstream trước–sau không đổi, current pointer verified. Report SHA256a7416bd1ab431fa650712ec63bb9ad77a096a5f0ec5f56abf56084505fcd0f46. Archive `research_tracking/runs/cpu-sim-kt-batch-gate-20261107-01` giữ source/test logs/proofs; archive gate09 giữ snapshot trước batching. Suite gần cap300s: gói tests sau cần dự toán resource/test budget, không skip tests để lấy PASS.

SIM01–SIM05 hoàn tất trong phạm vi engineering CPU. Source bank và artifacts lịch sử giữ nguyên; không hoàn tất calibration/mastery/controller hoặc CG-AKT research bằng các tests này. Kitv9 ZIP125files đã kiểm integrity, chưa chạy actual Colab/CUDA. Next: simulated training-data/split contract và graph-context information-boundary fixtures, trước khi generate/train/evaluate theo protocol đã duyệt.
