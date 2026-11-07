# Giao diện simulator–KT và kiểm tương thích AKT

## Phạm vi và nguồn

Gói này triển khai lớp nối kỹ thuật, chưa đổi scientific protocol hoặc controller Paper1/2. Nguồn metadata: `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/{nodes,question_bank}.csv`. Đã kiểm28concept và84item, mỗi concept có ba item. CSV và notebook gốc giữ nguyên. Không chạy lại toàn bộ papers, không Junyi/Holdout hoặc GPU.

Giao diện chung ở `src/knowledge_tracing/simulator_bridge.py`; backend AKT ở `src/knowledge_tracing/akt/online.py`; đặc tả và test history ở `docs/thesis_recovery/18_SIMULATOR_KT_INTERFACE.md`.

## Kết quả kỹ thuật

| Thành phần | Hành vi đã kiểm | Bằng chứng |
|---|---|---|
|Domain và vocabulary|Không dùng numeric indices để gán checkpoint Junyi sang Grade10; kiểm environment/item-bank/vocabulary/recipe/SHA|Unit native loader và integration rejections|
|Predict-before-update|Candidate query không nhận current outcome/latent theta; observe chỉ nhận ticket cùng learner/history/revision|Session contract tests|
|Reference probes|Các item được hỏi riêng từ cùng history, không trở thành practice events; thiếu item trả score None, không âm thầm đổi denominator|Contract/native tests và reference_probes.json|
|Global windowing|Online tái hiện offline anchors, cold start, OOV barrier, block boundaries và partial windows|Native H3/T2 và H100/T100205-event fixtures, tolerance abs1e-6 CPU|
|Frozen inference|Observe chỉ đổi history; model state/Torch RNG giữ nguyên; phát hiện optimizer update hoặc binding drift thông thường|Native tests và interface_result.json|
|Session isolation|Reset về cold state, snapshot JSON roundtrip, ticket cũ vô hiệu, learner khác không bị ảnh hưởng|Hai integration runs và unit tests|

Hai run `cpu-sim-kt-interface-20261107-01` và `...-02` train đúng168synthetic targets,1epoch,1optimizer update, d16 trên CPU. Labels tạo bằng quy tắc arithmetic; đây không phải training dataset do môi trường học sinh sinh ra. Elapsed tương ứng11.99s/11.07s, gồm lifecycle/probes. Không dùng các thời gian này dự toán d256 full training hoặc closed-loop GPU.

Run02 thêm canonical immutable metadata và binding guards sau review. Frozen native state SHA trùng run01; các reference scores cold/after8 cũng trùng chính xác. Checkpoint file SHA và history fingerprints khác vì checkpoint chứa telemetry khác và history gắn checkpoint identity. Phép so toàn bộ JSON ban đầu bị từ chối; phép so đúng tách state/scores khỏi provenance, lưu ở `docs/thesis_recovery/evidence/20261107-sim-repeat-proof.json`. Không sửa outputs run01/02.

Checkpoint fixture ở `experiments/akt/results/<run-id>/synthetic-final.pt`; hash/provenance trong evidence bundle. Không chép checkpoint hoặc interaction data lớn vào research_tracking. Workload và RAM caps là engineering fixture riêng, không thay Task14 pilot/GPU acceptance. Checkpoint không được trình bày là AKT benchmark đã chọn trên Development.

## Bug đã tìm và sửa

Export cũ gọi `adapter.predict` trên window đã được cắt theo global geometry. H3/T2 là cấu hình hợp lệ nhưng bị re-anchor lần2, làm3/11predictions khác direct sequence prediction; maxabs0.00178698. `predict_window` chấm trực tiếp window và được dùng chung cho online/export. Lưu failing regression `sim-parity-02.log` và passing suite `sim-export-04.log`36tests/24.80s. FakeAdapter fixture được cập nhật interface; giữ cả log25pass10fail trước cập nhật.

Kiểm H100/T100 với205events và OOV cho legacy-window/direct-window parity trong abs1e-6. Không suy mọi historical result bị lỗi; không sửa historical predictions hoặc chạy lại benchmark. Bản sửa này cần được ghi khi diễn giải run tương lai dùng window geometry khác.

## Giới hạn kiến trúc có ý nghĩa nghiên cứu

AKT NonRasch nguồn nhận item IDs và QA history, dùng khoảng cách vị trí tương tác. Timestamp của bridge chỉ kiểm chronology; không đưa elapsed calendar time hoặc raw numeric difficulty vào neural model. Test hỏi cùng item/history ở1giây và14ngày cho score giống nhau. Đây là thuộc tính model gốc, không phải bug của simulator hoặc lý do tự thêm time feature.

Vì vậy retention phải đo từ latent environment ở thời điểm đánh giá, tách khỏi reference correctness mà KT dự đoán. Model-score không đổi sau14ngày không chứng minh learner retention không đổi. Native Paper2 forgetting và temporal GAM là semantics khác; không ép chúng tương đương hoặc tự thay model. Item difficulty metadata nằm trong bank identity, còn AKT học khác biệt item qua embedding.

## Điều đã giải quyết và điều còn chờ

Đã có cách nối A0 graph-free AKT với history simulator mà không trộn Junyi vocabulary, current labels, oracle hoặc learner states. Có thể dùng fixture này làm nền cho graph-free/fixed/confidence/gated variants và causal-chain traces.

Reference weights1/3 của integration chỉ là fixture, không phải primary mastery definition đã được duyệt. S04 vẫn cần chốt reference population/weights, calibration trên simulator Development, threshold và mapping vào controller. S05 cần model×environment allocation. Simulator training trajectories phải có learner-disjoint train/selection/calibration/final seed families, coverage và diversity được kiểm trước train thật. BKT/GAM/SAKT/GKT phải có adapter/semantics phù hợp, không tự coi BKT P(K), Elo và p(correct) là cùng đại lượng.

RQ1/RQ2 có thêm source-level/engineering evidence về đường từ prediction sang state query và giới hạn thời gian. RQ3 chưa có phương pháp CG-AKT được train/evaluate hoặc learning-benefit evidence từ gói này. Không tự nâng overall thesis readiness lên READY.
