# Recipe SAKT nghiên cứu V1

10/11/2026. ROOT chọn recipe đầu tiên trước fit theo quyền người dùng đã giao về phương án an toàn và tiết kiệm. ID `sakt-paper-equation-d200-h5-hd40-c100-v1`. Quyết định chốt cấu hình để triển khai, không cấp quyền chạy hoặc thay hyperparameters của mô hình hiện có.

SAKT là comparator bắt buộc trong đủ chín điều kiện neural của protocol21. Selected-fit80 và raw-selection10 đi trước external system freeze, rồi mới fresh-refit90 và response-calibration10. Recipe đầu này dùng Grade10 simulator, CPU FP32. Junyi và CUDA cần allocation, data mapping và device acceptance riêng.

## Cấu hình đã chọn

| Thành phần | V1 |
|---|---|
| Core | Một block `sakt/model.py` paper-equation hiện có |
| Exercise unit | Item, vocabulary chỉ từ optimization phase |
| Registry | Bank84 items/28concepts, không coi registry là fitted vocabulary |
| Embedding | d_model200 |
| Attention |5heads, head_dim40, total projection width200 |
| FFN |200→200→200, ReLU, residual và post-layernorm như core |
| Dropout |0,2 tại các vị trí core hiện có |
| LayerNorm epsilon |1e-5 |
| Geometry | Last100 past interactions cộng current query, max_length101 |
| Target | Sliding target_block1, chỉ terminal target vào loss |
| Padding và position |Left padding, window_relative_interaction_rank |
| Cold và OOV |Known cold query-only; unsupported giữ null và reason |
| Adam |lr0,001, betas0,9/0,999, eps1e-8, weight_decay0 |
| Adam options |AMSGrad/foreach/fused/maximize/capturable/differentiable=false |
| Batch |128 terminal targets, last batch giữ nguyên số còn lại |
| Gradient |Clip norm1, reject nonfinite |
| Initialization |Fresh seed42 trong CPU fork_rng |
| Epoch sampling |epoch_seed=42+epoch−1, seeded_permutation hiện có |
| Maximum epochs |50 |
| Stopping |patience5, min_delta0,0001, earliest tie theo EarlyStopping hiện có |
| Epoch criterion |`native_torch_bce_float32_exported_supported_mean_v1` |

Training giữ mean masked BCE-with-logits của primitive SAKT. Chọn epoch bằng native BCE mean trên đúng exported float32 raw probabilities và float32 labels sau prediction, cùng supported population. Canonical reporting AUC/LL/Brier/ECE15/Accuracy0,5 được báo riêng cùng full coverage. Shared system-selector LL và Tfit clip1e-6 có vai trò khác, không thay thế criterion của epoch.

## Nguồn và lựa chọn của nhóm

Paper SAKT v1 trình bày attention, FFN và residual/normalization ở §2. Phần thực nghiệm thử dimensions50/100/150/200, Adam0,001, batch thường128 và dropout0,2. Ablation dùng d200 và mặc định5heads. Nhóm chọn một cấu hình trước outcome, không lặp search đó. [Primary SAKT PDF, trang4 và6](https://arxiv.org/pdf/1907.06837v1)

Head_dim40 là convention đã chọn của nhóm để cố định tổng projection width bằng d_model. Core cho phép head width độc lập, còn cách viết WO trong phương trình có thể được đọc theo full width d cho từng head. Nhóm không thử head_dim200 rồi chọn bằng kết quả. Nguồn tác giả đã được đối chiếu ở commit98510c58e49fc2cd8ae05412d1f3bb1b9b5053a0, nhưng local core không là port TensorFlow. [Provenance và khác biệt implementation](../../research_tracking/reports/sakt_core_readiness_20261107.md)

Các lựa chọn epsilon, clipping, Adam flags, epoch seed schedule và max50/patience5/min_delta0,0001 là cấu hình hữu hạn của khóa luận. Geometry100past+query101, overlapping terminal-only target windows và learned valid-window positions khác partition subsequences của paper. Batch128 terminal targets không đồng nghĩa128 learner subsequences. Không tuyên bố author-code/checkpoint parity hoặc tái lập số liệu của bài.

SAKT có capacity và lịch sử hữu hiệu khác AKT/GKT. Delta giữa các kiến trúc không là edge-only effect. Tại actual vocabulary N84, phép đếm từ source cho312.401parameters; actual registered count phải kiểm khi allocation tương ứng được duyệt.

## Ranh giới thực thi

`sakt/research_data`, `research_training` và `research_checkpoint` được tái dùng. Toy trainer/caps và historical artifacts giữ nguyên. Engineering8/1/1 cùng tiny numerical fixtures có scope riêng, không chuyển metadata thành actual main fit.

Chỉ producer có closed SAKT authorization, genuine source/runtime/Gate/input bindings và resource caps đã review mới được tạo model. Không dùng A0 grant hoặc metadata stage làm quyền chạy. Full maximum work phải được reserve trước run. Dừng do RAM/time/partial epoch giữ failure và counters, không gọi selected-only complete hoặc tự hạ dimensions/epochs để fit budget.

Chưa tự mở refit/calibration từ selected-only terminal. Comparator SAKT vẫn cần raw best-epoch artifacts trong admission đủ chín điều kiện. Fitted online adapter, fresh-process lifecycle resume, Junyi và GPU readiness là các acceptance riêng.

## Hồ sơ quyết định

- Protocol21/22/23 giữ nguyên source và information boundaries.
- Proposal trước adoption ở `artifacts/akt/local-tests/akt-research-runner-20261108-01/SAKT07_NUMERICAL_SELECTED_PRODUCER_PROPOSAL01.md`, SHA f8691d5e2200085964050eab7cf8b09c6df671b7692a049519e4724a5e6fcca4.
- ROOT đã chọn recipe trên trước fit. Tài liệu này không ghi một kết quả fitted hoặc thay các bản báo cáo lịch sử.
