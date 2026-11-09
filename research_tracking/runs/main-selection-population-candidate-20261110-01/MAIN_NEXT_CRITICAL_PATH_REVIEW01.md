# Main · ba bước tiếp theo sau positive GKT

10/11/2026. Review tĩnh, không import, chạy test, model, corpus hoặc Git. Đọc metadata và nguồn hiện hành. Positive GKT là dependency cần Root nghiệm thu riêng, không được giả định từ source producer hoặc metadata27.

## Điểm xuất phát đã có bằng chứng

- AKT public selected-only đã đạt trên engineering10×84. Public intentional pause ở epoch5 rồi resume đã khớp bảy epoch, raw exports và bestepoch4. Chưa có unexpected-fault recovery hoặc CUDA. Nguồn hiện hành có cả fresh và resume entry tại `akt/research_selected_runner.py:406–413`. Bằng chứng tại `research_tracking/runs/akt-public-selected-resume-20261110-01/`.
- SAKT selected engineering đã đạt sáu epoch, 36 cập nhật, 4032 optimized-target exposures và full84 raw-selection sau fresh reload. Đây là corpus engineering, chưa là Main60. Nguồn `sakt/research_runner.py:279–396`, bằng chứng `research_tracking/runs/sakt-selected-engineering-20261110-01/`.
- GKT có model11/trainer8/checkpoint28 thực thi đạt, producer27 metadata đạt. Nguồn producer đã có `run_gkt_selected_fit` tại `gkt/research_runner.py:328`, dùng recipe29, full prefix và checkpoint riêng. Main native positive còn cần terminal thực của Root. Đọc các bundle `gkt-research-model-trainer-20261110-01/`, `gkt-research-checkpoint-20261110-01/` và `neural-selected-producer-metadata62-20261110-01/`.
- Main60 public reader đã kiểm 48/6/6 learner ×210 events, đủ 84 items, train10080 và selection/calibration1260 targets. AKT có144 train windows và18 selection windows. Sáu graph conditions đã bind qua factories và hai Method24 loader thật, nhưng không tạo NN. Xem `research_tracking/runs/simulator-main60-data-preflight-20261110-01/` và `main60-graph-condition-binding-20261110-01/`.

Không cần fit lại Method24 hoặc tạo corpus khác để mở bước Main60. Condition train48 hiện có không chuyển được sang train8 của engineering corpus. `_scores` kiểm các lineage tại `akt/research_graph_condition.py:197–210`.

## 1. Mở Main60 selected-only bằng một graph candidate thật, giữ công việc có thể tiếp tục

**Khuyến nghị đầu tiên sau GKT positive** là chuẩn bị một allocation Main60 hữu hạn và đi qua public entry với một A3 condition đã bind, ưu tiên expert để giữ topology nguồn dễ kiểm. Dùng `MainSelectedExecutionSpec`, `_actual_condition` và `run_main_selected_candidate`, không tạo vòng train thứ hai. Các entry tại `akt/research_main_execution.py:288–346,424–469,510–559` và `akt/research_selected_runner.py:223–383` đã có đủ factories, collate/index, native train epoch, participation tracker, graph checkpoint và fresh best reload.

Đây là ranh giới chưa được positive public A0 kiểm. Sáu condition có metadata đúng chưa chứng minh native A3 training, gate participation, actual graph checkpoint và raw export cùng hoạt động trong public lifecycle. Không cần thêm một bộ toy architecture checks để thay ranh giới này.

Phạm vi hữu hạn đề nghị là một complete-epoch pause trên chính allocation dự kiến, sau đó chỉ resume khi đủ ngân sách đã chốt. Giữ nguyên maximum20epochs/patience3, initialization, optimizer và dữ liệu. API pause hiện cho CPU và cùng original allocation, không giới hạn tên candidate là A0, nhưng actual public evidence mới chỉ có A0. Không tự suy A3 pause/resume đã qua native. Nếu chưa đủ nguồn lực cho allocation Main60 hợp lệ, dừng tại thiết kế và ghi thiếu, không giảm maximum epochs để tạo vẻ hoàn thành.

Với geometry đã kiểm, một epoch AKT là36 Adam steps và10080 optimized targets. Trần selected của mỗi A-condition là720 steps/201600 exposures. Đây là đếm công việc, chưa là runtime forecast. Mỗi candidate cần cấu hình output đủ checkpoint64MiB cộng metadata reserve, aggregate quota, graph-input cap ít nhất160MiB khi dùng loader và resource/Gate/runtime/auth thật. Revalidation đọc/hash graph artifacts ở mỗi boundary, nên phải ghi thời gian inclusive của các boundary bằng observer hẹp đã có. Không gán toàn overhead cho Git hoặc bỏ hash checks để vừa cap.

Acceptance phải có actual authorization/source/data/condition, cùng backbone initialization giữa bảy A-candidates, đúng train80 và raw-selection10, counters khớp, checkpoint/BN/Adam/RNG theo loại model và terminal sạch. Nếu pause, phải có latest/best, cumulative quota cùng launch lineage thật. Không nhận partial epoch hoặc mock guard. Đầu ra này là phần đầu có thể tiếp tục của selected stage, chưa là main winner hoặc refit.

## 2. Hoàn thiện disk admission và external freeze trước khi dùng chín selected outputs

Đây là bước triển khai CPU không cần model mới và có thể làm song song với lượt selected đã được cấp quyền. Tạo adapter đọc artifact thật và freeze consumer nhỏ, dùng lại `MainAdmissionAccumulator` cùng `research_selection`. Không thay kernel thống kê hoặc tạo authority bằng typed claim.

Khoảng trống chính xác nằm tại `research_admission.py:243–260`, kết quả mặc định `artifact_bytes_verified=False`, `nine_terminal_files_admitted=False`, `external_freeze_authority=False`. `akt/research_main_stage.py:198–207` luôn từ chối refit và calibration vì chưa có external file verifier. Pure8 của kernel và pure8 admission không lấp được gap này.

Adapter cần verify COMPLETE, actual terminal/claim/checkpoint, raw predictions/targets/coverage, source/runtime/corpus/split/config và đầy đủ chín ID. Chuẩn hóa schema exports của ba producer vào canonical statistical keys, giữ original exports theo chronology. Sorting cho phép join không được làm đổi thứ tự dữ liệu huấn luyện. Kiểm same K/y/full1260 population và common-U của đúng A0+A1/A3 eligible. A2, SAKT và GKT vẫn là comparison rows bắt buộc. Không thay U theo từng cặp hoặc nhận thiếu candidate để có winner.

Sau đó chạy kernel đã có với2000 shared learner-cluster draws, seed42, pooled response LL, type7 upper0,975, strict upper<0 và stable ID tie. Freeze artifact đóng phải bind tất cả chín terminals, populations, source và selector recipe. Consumer kiểm lại đúng artifact trước constructor refit. Freeze thống kê hoặc một SHA-shaped token không tự cấp quyền execution. Các fixture có thể dùng export nhỏ manufactured để kiểm missing/duplicate/tampered/stale/null-support, không thêm NN.

## 3. Nối fresh refit90 → calibration10, rồi mới nghiệm thu fitted online bridge

Main selected entry hiện kết thúc với `refit_calibration_performed=False`, không thiếu do quên gọi một hàm. Refit-after-external-freeze là entry chưa có. Có thể tái dùng phase, epoch, checkpoint và Tfit primitives từ `akt/research_runner.py:533–597`, nhưng runner này tự local-freeze và refit ngay một candidate. Không gọi nó chín lần để thay thứ tự main.

Entry mới phải tiêu thụ freeze đã admit đủ chín candidates, tạo fresh encoding90/model/optimizer với đúng selected epoch từng candidate, giữ graph/confidence train80 frozen, rồi đóng checkpoint weights cuối trước calibration prediction/Tfit. Không chọn lại winner sau refit hoặc Tfit. SAKT/GKT cần counterpart theo native trainer/checkpoint của chính chúng, không nới toy caps hoặc đọc calibration để mở vocabulary. Theo tài liệu23, đủ một môi trường vẫn là9selected và9refit phases, chưa gồm calibration/inference. Chọn chỉ refit winner sẽ đổi phạm vi bằng chứng và cần quyết định có phiên bản trước khi áp dụng.

Online chưa là prerequisite để bắt đầu selected training, nhưng là prerequisite để biến fitted checkpoints thành closed-loop RQ outcomes. `response_calibration.score_reference_bank:267` yêu cầu `OnlineSession`, rồi `reference_controller.select_from_reference_snapshot:65` mới thực hiện choice. `akt/research_graph_online.py:108` hiện chỉ tạo evidence động, chưa native fitted backend. `akt/online.py:155–158` vẫn dựng AKTAdapter graph-free. `sakt/adapter.py:175–176` từ chối fitted OnlineSession bridge và GKT adapter hiện là engineering loader. Không gắn các selected checkpoint vào những loader cũ bằng cách đổi tên role.

Acceptance tiếp theo nên dùng một fitted checkpoint có provenance,84 counterfactual probes trên cùng prehistory, history/RNG không đổi, đủ item support, calibrated response binding, controller ties và predict-served-before-observe. Đo throughput84probes riêng trước forecast H_dev30. Không dùng dataset targets/s hoặc graph-off A3 làm independent A0 fallback.

## Các giả định cần chặn

1. Tiny A0/SAKT và future positive GKT dùng corpus engineering không điền được ba ô Main60. Domain/split/source/graph/train support phải cùng main allocation.
2. Toàn bộ public reader được audit ba roles theo protocol22. Ranh giới khoa học là calibration không ảnh hưởng optimization/epoch/winner, không phải cấm deserialize mọi calibration metadata/labels trong trusted orchestrator.
3. Một số header của state và doc27 là snapshot cũ. Dùng các mục actual ngày10/11 cùng receipts cụ thể, không lấy header Gate177 stale để phủ nhận Gate183, hoặc ngược lại lấy Gate183 làm current cho mọi source thay đổi sau đó. Entry phải revalidate build/source thực tế.
4. Recipe28 là hợp đồng CUDA đã chọn, chưa actual CUDA acceptance. SAKT/GKT producer đang CPU-only. Không suy đủ9conditions sẽ chạy CUDA cùng một interface. Junyi chưa được MainSelectedExecutionSpec nhận, nên hai môi trường vẫn còn phần riêng.
5. Không tăng ngân sách cloud, giảm epoch, bỏ baseline hoặc thay guard integrity để có PASS. Local CPU có quyền engineering thường lệ, còn từng native allocation cần Root review exact inputs/caps. FullCV/Holdout/paid run vẫn tách biệt.

## Kết luận điều phối

Sau GKT positive, ưu tiên một public graph-selected boundary trên Main60 với work có thể tiếp tục, đồng thời hoàn thiện disk admission/freeze bằng CPU thuần. Refit/calibration đi sau freeze; online bridge đi sau fitted checkpoint. Ba việc này mở đúng chuỗi bằng chứng Main, không cần thêm corpus, architecture hoặc simulator diagnostics để thay thế.

Nguồn phương pháp là Protocol21, Accounting23, Recipe26, AllocationV1 cùng Recipe29/30 và CUDA28. Các giới hạn final horizon, một training seed, hai môi trường và required models còn nguyên. Review này không cấp quyền chạy hoặc nghiệm thu scientific fit.

## SHA snapshot của lượt đọc

Các SHA mô tả nguồn tại lúc review, chưa là verdict test hoặc quyền thực thi.

| File | SHA-256 |
|---|---|
| docs/thesis_recovery/TASKS.json | 17c51f3c97b102b55840710c083c5b64d33ba39f32a3729b2136657d14bc5667 |
| docs/thesis_recovery/INVESTIGATION_STATE.json | 5487a04061f0a904add930aca34162f3fc2fdd207835ea029939bee219f3faaa |
| docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md | c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6 |
| docs/thesis_recovery/23_TRAINING_MATRIX_ACCOUNTING_V1.md | 6f9e5adc2f075cb9c0c43ebbf1852e2365dd1baf5ff7c59dd8630561b3d72567 |
| docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md | 13a81ad6a5173e1f215e3df01f3917fcbc1cce128c87c93985b57af76faa353a |
| docs/thesis_recovery/28_CUDA_EXECUTION_PROFILE_V1.md | 57940d5991f90c9c306c2ab442729766489513703153407fe26646b21d963dd0 |
| src/knowledge_tracing/akt/research_main_execution.py | 0c27b05312c723e34c0590ddec00009e849687cd2a1c5c303c5f93723ca64e77 |
| src/knowledge_tracing/akt/research_main_stage.py | 77b7dbfd75f715f3a4179286cd742780581151dc39c39748213c9c55c25b13c1 |
| src/knowledge_tracing/akt/research_selected_runner.py | b2b045d4673ff6cbc8e4e4ade8e5599806e52e501f5c8612e894ff636c2f7a46 |
| src/knowledge_tracing/akt/research_selected_resume.py | 49f74a87a5fa6f11b923c102389695c2c582257d7a782d9cf32caab819cf70d1 |
| src/knowledge_tracing/research_admission.py | b8601da03a972834cfd2f5596ea6a6b9c5759437796b4f4b65720f7abc1a92f2 |
| src/knowledge_tracing/research_selection.py | 0e3cf12d15626a76000c6cdc04779ac769806aae2a5e52f769d4c70f3580a348 |
| src/knowledge_tracing/gkt/research_runner.py | 173fbf7cea845a649da4a79f92394883210de239743e4f8f6c687e0730530d30 |
| src/knowledge_tracing/sakt/research_runner.py | 2d6ec4f6f0be78013c610964479ee085d9effecace83259ba525bd066ae8de7f |
| src/knowledge_tracing/response_calibration.py | c7849654eff35862e61602a4f95e401ed88b9070a77832e05d6a7173e72ebacb |
| src/knowledge_tracing/reference_controller.py | a955a076e41f5baf54e18dfe994d95503a9613824157e83a7a0062667a4024df |
| src/knowledge_tracing/akt/research_graph_online.py | c44ad90a699e76ce3bcf2e0cc7264a7f9d87f6639ee59f8033d51a87ef1b2c88 |
