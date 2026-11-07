# SAKT: lõi nhân quả kiểm trên CPU, chưa có pipeline benchmark

Ngày 07/11/2026. Trạng thái: **CORE_VERIFIED_CPU_SYNTHETIC; ADAPTER/TRAINER_NOT_IMPLEMENTED**. Có package mới `src/knowledge_tracing/sakt/` và tests độc lập `tests/sakt/`. Không thay AKT, GAM, shared modules, builder nguồn, notebook hoặc test platform đã bàn giao. Đây là bằng chứng kỹ thuật với weights khởi tạo ngẫu nhiên, **0 optimizer steps**, chưa là mô hình fitted, kết quả dự báo hoặc bằng chứng lợi ích học tập.

## Phạm vi đề cương và nguồn gốc

[Truy vết yêu cầu](../../docs/thesis_recovery/02_RESEARCH_TRACEABILITY.md) giữ SAKT trong comparator set E10 và yêu cầu learner split/predict-before-update. [Hợp đồng simulator–KT](../../docs/thesis_recovery/18_SIMULATOR_KT_INTERFACE.md) yêu cầu domain/checkpoint binding, query trước observe và không trộn model-score với latent mastery. Lõi mới chưa thực hiện toàn bộ hai hợp đồng này.

Nguồn chính đã đọc trực tiếp:

- Pandey, Shalini; Karypis, George. [A Self-Attentive model for Knowledge Tracing, arXiv:1907.06837v1](https://arxiv.org/pdf/1907.06837v1), §2, phương trình (1)–(6): exercise query, embedding interaction `e+r×E`, learned position, scaled dot-product multihead attention, FFN ReLU, residual/layernorm và scalar sigmoid.
- Repository tác giả [shalini1194/SAKT](https://github.com/shalini1194/SAKT), commit [98510c58e49fc2cd8ae05412d1f3bb1b9b5053a0](https://github.com/shalini1194/SAKT/commit/98510c58e49fc2cd8ae05412d1f3bb1b9b5053a0), ngày 06/12/2019; đọc [model.py](https://github.com/shalini1194/SAKT/blob/98510c58e49fc2cd8ae05412d1f3bb1b9b5053a0/2019-EDM/model.py) và [modules.py](https://github.com/shalini1194/SAKT/blob/98510c58e49fc2cd8ae05412d1f3bb1b9b5053a0/2019-EDM/modules.py). Mã TensorFlow dùng Q/K/V có ReLU, chia width theo heads, không có learned WO sau ghép heads, normalized queries, nhiều bước normalize và head logits theo skill rồi gather.

Chọn implementation độc lập theo phương trình bài báo; không port/copy/chạy TensorFlow hoặc nạp checkpoint tác giả. Vì paper và code có khác biệt, không tuyên bố numeric/checkpoint parity với mã tác giả. Không dùng blog, DeepWiki hoặc implementation bên thứ ba làm authority. [Metadata nguồn](../../artifacts/akt/local-tests/parallel-sakt-20261107-02/primary-source-provenance.json) lưu commit, URLs và lựa chọn chưa chốt.

## Lõi đã cài đặt và các lựa chọn công khai

| Thành phần | Hành vi local |
|---|---|
| Config | Bắt buộc caller cung cấp `num_items`, `max_length`, `d_model`, `num_heads`, `head_dim`, `dropout`, `layer_norm_eps`; không có bộ hyperparameters benchmark mặc định. |
| Kiến trúc | Một attention block; Q/K/V linear không bias; ghép heads qua learned WO; residual từ exercise query rồi post-layernorm; FFN `d→d→d` với ReLU và residual/post-layernorm; scalar logit và sigmoid. |
| Head width | `head_dim` explicit. Smoke dùng head_dim bằng d_model; không âm thầm giả định d_model/num_heads hoặc adopt cấu hình TensorFlow. Final capacity/search budget phải được freeze riêng. |
| Position | Learned embedding theo **rank interaction hợp lệ trong window**, không theo số padding của batch. Giữ prediction tương đương khi đóng cùng sequence thành left/right padding. Đây là convention engineering, khác absolute padded slot của mã TensorFlow; chưa chốt geometry benchmark. |
| Dropout | Trên history embedding, attention weights, attention output và FFN; eval tắt dropout. Vị trí/rate phải được ghi khi freeze variant, chưa có training methodology được chọn. |
| Output | `logits`, `probabilities`, attention trước dropout, `valid_mask`, `has_history`. Output padding bằng 0 là sentinel hữu hạn; phải dùng valid_mask, không coi padding là fitted prediction. |

Model chỉ có attention trên lịch sử quan sát; không nhận prerequisite graph, edge list, concept hierarchy hoặc oracle. Attention weights biểu diễn mức liên hệ model học trong history, không tự trở thành graph tiên quyết hoặc causal prerequisite evidence.

## API và ranh giới thời gian

`SAKTCore.forward(SAKTInputs)` nhận ba tensors `[B,T]`: item IDs 1..N (padding 0), `prior_responses[t]=r[t-1]` và boolean valid mask. Không có tham số current targets, loss hoặc optimizer. Prior phải bằng -1 tại event đầu và padding; các vị trí còn lại chỉ nhận 0/1. Validator chặn OOV, response sai giá trị, dtype/shape/mask không khớp, internal padding gaps và sequence vượt cap.

Slot key `j` chứa `(e[j-1],r[j-1])`. Inclusive triangle trên slot `j≤t` vì vậy chỉ đọc các **event `j-1<t`** khi dự đoán event `t`; không dịch hai lần hoặc bỏ interaction gần nhất. First target không có historical key: attention chính xác bằng 0, score hữu hạn từ query và các lớp tiếp theo, `has_history=False`. Softmax dùng finite masked logits rồi zero/renormalize các weights hợp lệ; hàng all-masked không phát sinh NaN.

`collate_sequences` tái sử dụng đúng kiểu `CausalSequenceInputs` của shared contract. Mỗi phần tử phải là một learner/window, có offsets `[0,length]` và shifted prior hợp lệ; IDs shared 0..N-1 được chuyển sang IDs tensor 1..N. Caller chỉ định padding side/device/cap, không truyền target labels. Collator giữ thứ tự đã chuẩn bị và không sort, fit vocabulary hoặc cắt history ngầm. `StableVocabulary`/`build_causal_sequence_inputs` được dùng trong test tích hợp để kiểm chuyển ID/prior. Không tái sử dụng tensorizer/window/training loop của AKT vì geometry và semantics chưa được chốt tương đương.

`max_length` local là số query/event slots, có cả first target không history; do đó một sequence dài T dùng tối đa T-1 historical interactions. Không được lấy tên config này để mặc định context budget ngang một model khác. Caller chịu trách nhiệm vocabulary train-only, chronology, context/window boundaries và metadata trước collator; chưa có loader/export identity contract đầy đủ.

## Kiểm tra thực tế

CPU local Windows 11 build 26200, Python 3.13.5, torch `2.7.1+cpu`, numpy `2.5.4`, pytest `9.1.1`, interpreter `.venv/Scripts/python.exe`. Fixtures chính: 6 items, T≤12, d_model=8, 2 heads, head_dim=8, eps=1e-5, seed 42; dropout 0 và 0.2 cho backward. Fixture phương trình dùng d=2/head=1. Tất cả chỉ smoke dimensions, không là final protocol, không đo predictive accuracy hay throughput.

| Nhóm kiểm | Điều đã xác nhận |
|---|---|
| Ranh giới labels | Đổi current/future responses không đổi current/earlier logits; đổi future items không đổi các logits trước đó. |
| Positive controls | History response, current item và thứ tự hai past interactions có thể đổi prediction cùng target; model không chỉ trả hằng số. |
| Mask/gradient | Không attention tới current/future interaction; interaction gần nhất vẫn được đọc. Gradient từ target t chỉ đi tới historical interaction activations, không tới current/future activations. |
| Padding/cold | First target/all-padding hữu hạn với zero attention. All-padding backward gradient hữu hạn và chính xác bằng 0; thay padding embeddings không biến padding thành history. |
| Batch isolation | Singleton/batched/permuted, cả left/right padding, cho logits tương đương abs1e-6 trên valid rows. Đổi learner khác không đổi peer prediction. Đây là kiểm eval; không hứa sample-wise dropout RNG giống nhau giữa train batches. |
| Phương trình | Fixture một past value `(1,3)`, projection identity, FFN zero cho kết quả khớp phép tính LN hai lần và sigmoid độc lập trong abs1e-6. |
| Backward | Synthetic masked BCE backward hữu hạn ở dropout 0/0.2; state_dict không đổi trước/sau; không tạo optimizer hoặc gọi optimizer.step. |
| Input contract | Shared input→tensor giữ IDs/prior; invalid dimensions, NaN config, OOV, unshifted first response, invalid binary, gaps, multi-learner/overlength/empty bị từ chối. |

| Lượt | Kết quả | Evidence |
|---|---|---|
| `parallel-sakt-20261107-01` | **35 passed**, 25.58s; bản trung gian trước hai kiểm order/all-padding-backward bổ sung. | [log](../../artifacts/akt/local-tests/parallel-sakt-20261107-01/pytest.log), [JUnit](../../artifacts/akt/local-tests/parallel-sakt-20261107-01/pytest.xml) |
| `parallel-sakt-20261107-02` | **37 passed**, 3.30s; JUnit 37 tests, 0 failures/errors/skipped; không deselect. Đây là source cuối của gói. | [log](../../artifacts/akt/local-tests/parallel-sakt-20261107-02/pytest.log), [JUnit](../../artifacts/akt/local-tests/parallel-sakt-20261107-02/pytest.xml) |

Mỗi lượt dưới 120 giây. Lệnh cuối chạy từ repository root; thư mục output được tạo mới và từ chối nếu đã tồn tại:

```powershell
$env:PYTHONPATH = 'src'
& .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=artifacts/akt/local-tests/parallel-sakt-20261107-02/pytest-temp --junitxml=artifacts/akt/local-tests/parallel-sakt-20261107-02/pytest.xml tests/sakt *> artifacts/akt/local-tests/parallel-sakt-20261107-02/pytest.log
```

Lượt 01 dùng cùng lệnh với output/basetemp đổi sang `parallel-sakt-20261107-01`. Exit code hai lượt đều 0. Kiểm whitespace trên cả 6 Python files mới trả `trailing_whitespace=[]`; imports đã được thực thi khi pytest thu thập/chạy tests.

[Inventory SHA-256 trước archive](../../artifacts/akt/local-tests/parallel-sakt-20261107-02/source-and-evidence-sha256.json) giữ 6 source/test files hiện tại, shared input contract, tài liệu tham chiếu, lock và logs/JUnit/provenance. Source inventory thuộc bản cuối 37 cases, không tuyên bố source trung gian 35 cases giống bản cuối. Chưa chuyển artifact trong tiểu tác vụ; parent cần so SHA sau archive và hash thêm báo cáo này vào manifest tổng hợp.

## Những gì chưa hoàn tất

Lõi **chưa implement `SequenceKTModel.fit/predict` hoặc simulator backend/session**. Còn thiếu loader theo domain/frozen split, train-only vocabulary/support, explicit OOV/fallback policy, window target accounting, criterion tính first target, training optimizer/stopping/budget, epoch selection/refit, checkpoint identity/resume, prediction export/alignment, calibration và mapping score→mastery/controller. Cold query-only score hiện là engineering behavior của core, chưa được quyết định sẽ fit/score như thế nào trong E10.

Cần freeze rõ paper-equation variant so với author-code variant, head width/capacity, norm/dropout, window/context/position geometry và denominator chung trước khi gọi apples-to-apples evaluation. Adapter phải có learner/domain/checkpoint binding và pure query-before-observe, không ghép tạm model vào AKT training loop hoặc dùng numeric IDs để chuyển checkpoint giữa Junyi và simulator.

Chỉ kiểm local Windows/CPU; chưa actual Linux/Colab, CUDA, training run, experiment metrics, epoch lựa chọn hoặc full Gate2. Package mới chưa nằm trong AKT Gate2 suite/sourcekit hiện hành; không dùng 37 tests này để tự đổi trạng thái Gate2/GPU readiness hoặc overall thesis readiness. Không dùng realdata, Holdout, Development benchmark, GPU, cloud hay cài dependencies. Không Git add/commit/push. Parent review, cập nhật repository map/report index và archive/manifest/commit theo gói riêng.
