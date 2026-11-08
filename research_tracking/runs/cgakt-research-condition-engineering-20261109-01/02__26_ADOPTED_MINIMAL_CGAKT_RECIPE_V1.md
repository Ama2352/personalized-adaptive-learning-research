# CG-AKT tối thiểu: quyết định triển khai V1

09/11/2026 · **ADOPTED_GROUP_IMPLEMENTATION_V1**. Chưa phải kết quả mô hình đã train hoặc quyền chạy GPU.

ROOT chọn phương án theo quyền user đã giao: “Phương pháp nào an toàn và tiết kiệm tiền thì chọn, ko chờ chốt”. Đây là quyết định triển khai của nhóm, không gán thành phê duyệt GVHD. Giữ nguyên đề cương, ba RQ, các baseline, hai môi trường và deliverables của [Protocol21](21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md). Không tự bỏ mô hình hoặc giảm phép so sánh để vừa ngân sách.

## Phương án được chọn và lý do

Chọn nhánh residual D1 trong [draft25](25_MINIMAL_GRAPH_AKT_RESEARCH_RECIPE_DRAFT.md), thay vì thêm một mạng message lớn. Mục tiêu là kiểm được từng thành phần: cạnh khai báo, confidence theo cạnh và gate. Capacity nhỏ giúp giảm chi phí và phân biệt các cơ chế; nó cũng giới hạn loại quan hệ biểu diễn được. Kết quả âm hoặc graph bị vô hiệu là kết quả hợp lệ.

Draft25 được giữ nguyên byte với SHA `7b478d584820351ac3ff118c8856b4afa935f4bf1a4137b6d82ef3037adea080`. Tài liệu này chốt các quyết định còn mở; không biến các đoạn “chưa adopt” trong draft thành bằng chứng đã triển khai. Recipe hiện hành có tên **`cgakt-centered-parentmean-scalar-v1`**; tag engineering cũ và tag draft không phải checkpoint nghiên cứu tương thích.

## Kiến trúc đã chốt

Tại target t, chỉ dùng các đáp án trước t trong **cùng effective causal window** mà AKT sử dụng, bao gồm rollover và OOV reset. Với cạnh cha j→q đã quan sát, message là mean correctness trừ0,5; cạnh chưa quan sát đóng góp0. Đặt a bằng confidence nhân chỉ báo đã quan sát; message tổng là `sum(a*message)/max(1,sum(a))`. Không dùng theta thật, đáp án hiện tại hoặc lịch sử ngoài cửa sổ của baseline.

| Variant | Nhánh graph | Tham số thêm |
|---|---|---:|
| A0 | AKT graph-free |0|
| A1 | Confidence1, gate1 trên declared graph |alpha1|
| A2 | Confidence từ artifact TRAIN được nghiệm thu, gate1 |alpha1|
| A3 | Cùng artifact/graph như A2, gate học được |alpha1 +4weights +1bias|

Logit mới bằng logit AKT cộng `alpha * gate * message`. Alpha là scalar signed khởi tạo0. Gate A3 là sigmoid của Linear4→1, weights/bias khởi tạo0; bốn features đúng draft25: support/(1+support), mean confidence, population variance confidence, observed-parent fraction. Không thêm MLP, regularizer hoặc tuning theo kết quả evaluation.

Graph-off/empty/no observed confidence mass phải đi đúng native path. **Không bypass vì alpha bằng0**: đường gradient đến alpha phải tồn tại. Với mixed batch, inactive slots dùng base logits của cùng forward; không forward lần hai dưới dropout. A3 graph-off chỉ là ablation trên backbone A3; fallback hệ thống phải dẫn tới checkpoint A0 độc lập đã train.

Giữ native AKT geometry, loss, optimizer và hyperparameters hiện hành như mục3 draft25; không chọn cấu hình mới trong quyết định này. Đây chỉ là một candidate method tối thiểu, chưa chứng minh hiệu quả hoặc calibrated mastery.

## Confidence và graph: xử lý thiếu hỗ trợ

Giữ semantics Protocol21/Method24: confidence là **predictive stability trên surrogate TRAIN**, không xác suất cạnh đúng. Không dùng oracle edge labels cho điều kiện deployment-like. Oracle confidence nếu có sau này là control riêng, không trộn vào A2/A3 chính.

Declared graph có thể có cạnh được đánh giá nhưng không đủ support: giữ cạnh cùng unsupported flag/reason và dùng operational weight0. Supported score0 vẫn là trường hợp khác. Không tự bỏ cạnh, điền confidence1 hoặc làm graph thành “đã hỗ trợ” bằng tên gọi. Artifact thiếu bản ghi, sai lineage, duplicate/extra endpoints hoặc chưa complete vẫn bị từ chối.

Rule `SUPPORTED_DAG31` chỉ áp dụng khi nhận **learned graph condition**. Không ép mọi cạnh của expert graph phải đạt support của learned DAG; cũng không nhận learned graph thiếu rule đã freeze như thể được nghiệm thu. A1 fixed-confidence phải giữ declared topology để phép ablation không đồng thời đổi edges.

## Fit, refit và thứ tự chọn hệ thống

1. Graph học được và confidence chỉ fit trên train80. **Giữ nguyên artifact graph/confidence này qua neural refit90**, tránh lặp surrogate fits và đổi topology sau so sánh candidate. Metadata phải nói rõ thành phần graph chưa refit trên90%; không gọi toàn pipeline là refit đầy đủ trên90%.
2. Các variants dùng cùng initial native backbone tensor state, fresh optimizer riêng; không warm-start từ A0 đã train. Branch construction không làm thay RNG stream trước native initialization.
3. Mỗi candidate chạy selected-fit80 rồi xuất raw best-epoch selection10 và **dừng**. Tất cả candidate được chốt phải hoàn tất bước này trước external system-selector freeze và trước mọi main refit.
4. Chỉ sau external freeze mới tạo fresh model/optimizer/encoding90 để refit đúng số epoch đã chọn, rồi calibration10. Không chọn lại winner bằng dữ liệu đã trở thành train.

[A0 runner hiện có](../../src/knowledge_tracing/akt/research_runner.py) là lifecycle pilot đơn-candidate, có refit ngay sau local freeze. Không được gọi nó chín lần rồi coi là main matrix đúng thứ tự. Cần entrypoints selected-only và refit-after-external-freeze, tái dùng epoch/accounting/evaluator hiện có.

Để tránh hiểu khác nhau về “upper95%” trong Protocol21, chốt trước khi xem selection: percentile interval hai phía95%, upper quantile0,975;2.000 learner-cluster bootstrap draws, seed42, learner IDs sắp thứ tự và dùng cùng draws cho mọi eligible candidate. Primary LL vẫn gộp theo response trên common-supported targets; mỗi bootstrap resample cả cụm learner và tính lại trên các response của cụm được lấy, không đổi thành mean learner LL âm thầm. Chọn eligible bằng upper bound<0, rồi mean LL nhỏ nhất, tie theo stable candidate ID; không eligible thì A0. Đây là Dev selector, không final significance; không tune rule bằng kết quả đã xem. Utility bootstrap cũ chỉ được tái dùng nếu đúng estimand này, không mặc nhiên lấy fold-macro mean.

## Checkpoint và kiểm chứng cần thực hiện

Checkpoint phải bind recipe, variant, initial-state identity, graph/confidence train80 lineage, vocab/bank, phase/freeze và nguồn/runtime; lưu backbone+alpha+gate cùng optimizer/RNG/counters theo trạng thái thực tế. Không nhận checkpoint engineering như research checkpoint.

Một nhánh graph có thể không hoạt động trong cả batch; gradient có thể None và Adam state của tham số đó chưa tồn tại. **Không sao chép giả định “mọi parameter step bằng global steps” từ SAKT** sang graph model. Phải kiểm participation/counter hợp lệ và exact restore; không điền state giả cho tham số chưa được cập nhật.

Acceptance trước training: causal/OOV/window parity; graph-off loss/prediction/backbone-gradient parity; alpha0 còn gradient trên fixture có signal; gate có gradient sau alpha khác0; confidence/artifact admission; same-forward inactive slots; strict checkpoint/reload; selected-only terminal và external-freeze admission. Không yêu cầu metric tăng hoặc alpha dương để pass phần mềm.

## Ranh giới thực thi và việc tiếp theo

Quyết định này cho phép triển khai local trong `.venv` theo engineering loop đã được giao. Mỗi native check tiếp theo vẫn cần input/source, số bước và tài nguyên hữu hạn được ROOT review; không phải xin user lại cho routine engineering. Chưa có quyền GPU/Modal, full CV, Holdout hoặc final selection từ tài liệu này.

Ưu tiên: hoàn thiện research graph context/model với cửa sổ thật; tách selected-only/external-freeze refit; nghiệm thu nhỏ; sau đó mới benchmark GPU và quyết định run có mục tiêu nghiên cứu. Không mở thêm nhánh kiến trúc dựa trên kết quả đẹp/xấu của final evaluation. [Hạch toán23](23_TRAINING_MATRIX_ACCOUNTING_V1.md) vẫn giữ toàn bộ model phases; chi phí chưa được đo không được trình bày như dự báo chính xác.
