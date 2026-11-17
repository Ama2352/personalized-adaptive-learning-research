# SAKT/GKT — nghiệm thu đường đánh giá cached selected CSV, 17/11/2026

## Đối chiếu đề cương và mục tiêu gói

Đã đọc trực tiếp PDF đề cương được cung cấp, SHA 941e9c43e5bbd29075051debf6cdf81256c65b89e612d001e1a5377474b4836a, trang 2–5. Đề cương yêu cầu SAKT/GKT làm comparator hiện đại, đánh giá cùng luồng bằng AUC, Log Loss, Brier và ECE, cùng nguyên tắc learner-disjoint và dự báo trước cập nhật. Sprint 2 yêu cầu chuẩn hóa các model. Sprint 5 và 6 cần thực nghiệm, diễn giải và báo cáo. PROPOSAL_REQUIREMENTS.json giữ định vị nguồn.

Protocol 21 giữ SAKT/GKT ở cả Grade10 và Junyi, selection 80/10/10 rồi refit 90/calibration 10. Recipe 29 và 30 hiện chỉ đặc tả Grade10 CPU. Gói này hoàn thiện bước đọc các CSV đã có để tính và kiểm metric/coverage. Model inference, training và lựa chọn epoch vẫn dùng producer hiện hành.

## Thành phần hiện có được kiểm

| Thành phần | Source và trạng thái đã xác nhận |
|---|---|
| SAKT selected-fit/prediction | src/knowledge_tracing/sakt/research_runner.py, research_training.py, research_data.py; producer giữ causal sliding last 100 past + query, target terminal, OOV/null và best checkpoint reload parity |
| GKT selected-fit/prediction | src/knowledge_tracing/gkt/research_runner.py, research_training.py, research_data.py; static expert 28 concept, full-prefix, BN/dropout, predictor trước observe và explicit unsupported-history |
| SAKT engineering đã lưu | experiments/sakt/results/sakt-selected-engineering10x84-20261110-03;8 learner train / 1 learner selection / 1 learner calibration,672 train và 84 selection targets;6 epochs, chọn epoch 1 |
| GKT engineering đã lưu | experiments/gkt/results/gkt-selected-engineering10x84-20261110-01; cùng cohort/split;11 epochs, chọn epoch 6 |
| Checkpoint đã lưu | Đã đọc kiểm SHA blob SAKT 3.787.412 bytes và GKT 359.203 bytes so với selected claim. Không deserialize weights nghiên cứu trong lượt kiểm metadata này |
| Phần chưa có kết quả trong gói | Main Grade10 comparator fits, SAKT/GKT Junyi, refit 90, response calibration và independent evaluation của hai comparator |

EXISTING_ARTIFACTS.json giữ đường checkpoint, metadata và SHA. Các lượt engineering nhỏ xác minh vòng đời phần mềm. Chưa đủ thay bằng chứng main experiment hoặc kết luận RQ.

## Code mới và entrypoint

- src/knowledge_tracing/research_baseline_evaluation.py cung cấp evaluate_cached_selected_baseline.
- scripts/evaluate_selected_baseline.py cung cấp CLI nhận request đã pin và xuất JSON nhỏ trong một research run.
- Tái dùng BoundedArtifactReader, normalize_selected_row, SelectedCandidateClaim, SelectionPopulation và ResearchSplitPlan. Metrics gọi trực tiếp GAM-KT _metrics, cùng phép tính đã đối chiếu với BKT.

Consumer nhận exact FileRefs của claim/predictions/targets/coverage, independent selection population đã dựng từ public reader và split plan đã frozen. Code kiểm SHA/size theo claim, scope raw_selection10, encoding/phase, đầy đủ keys và labels/prefix digest, learner IDs theo plan, global ranks liên tục và chronology thực theo rank. OOV/unsupported vẫn có trong mẫu số coverage và giữ null. Không gán xác suất 0,5 cho unsupported.

Metric trả theo supported population gồm AUC, response-pooled Log Loss, Brier, ECE 15 equal-width, Accuracy 0,5 và class counts. Khi thiếu lớp hoặc thiếu supported targets, metric không xác định giữ null. full_metrics chỉ có khi toàn bộ target được scored. Output giữ native epoch objective riêng, có source SHA và package versions của reporting metric.

File JSON còn giữ các input refs, declared checkpoint SHA, full learner/target counts và flags chưa có full-nine admission/freeze/refit. Consumer không deserialize checkpoint hoặc cấp quyền lựa chọn mô hình. Admission đủ chín candidate vẫn dùng research_selected_files/research_admission hiện hành. Junyi bị từ chối ở consumer này vì domain/mapping của baseline chưa được qualify.

## Kiểm thử thực tế của gói

| Lượt | Kết quả và ý nghĩa |
|---|---|
| tests02 |76 ca đạt trong 5,89 giây; consumer/CLI synthetic, SAKT/GKT selected-runner guards. Kiểm key, label, prefix, phase, OOV, ranks, claim/file/count mismatch, split khác, one-class/zero-support và metric parity với BKT |
| native-causal-tests01 |4 ca đạt trong 5,79 giây; SAKT causal/peer independence/modes/OOV, GKT manual predict→observe/full-prefix/future-label/OOV |
| native-checkpoint-tests01 |SAKT roundtrip đạt. GKT bị guard test yêu cầu 2 GiB free sau Torch import. Giữ nguyên failure log |
| native-checkpoint-tests02 |GKT restore BN/dropout/Adam/RNG và next epoch đạt trong 10,34 giây, process tree peak 299.417.600 bytes. Fixture reserve đổi thành 256 MiB, vẫn giữ RSS 1 GiB vàdeadline 60 giây |
| cli01 |CLI thật chạy bằng .venv, đọc input CSV tổng hợp đã pin và xuất SYNTHETIC_CLI_METRICS01.json;10 full targets / 4 supported, không dùng dữ liệu Junyi |

Fixture GKT checkpoint thay đúng resource reserve cho handmade 8 learners × 4 events. Numerical model/optimizer recipe không thay. NATIVE_RESOURCE01 chỉ đo launcher nên peak đó không đại diện Torch process; NATIVE_RESOURCE02 đo process tree đúng. Không suy GPU hay full-data throughput từ các lượt này.

Các fixture/checkpoint synthetic mới nằm trong artifacts/akt/runtime/baseline-*-tests-20261117-* theo test root hiện có. Chỉ bản input CSV/JSON nhỏ để tái lập CLI được sao chép vào synthetic-inputs của bundle, kèm inventory trước/sau SHA. Không tạo hoặc tải model nghiên cứu lớn.

## Chạy lại ví dụ CPU

Dùng terminal ở D:/Dev/KLTN và .venv đã có. Output mới phải dùng tên mới nếu file đã tồn tại.

```powershell
.\.venv\Scripts\python.exe -B scripts/evaluate_selected_baseline.py --request research_tracking/runs/baseline-evaluation-readiness-20261117-01/SYNTHETIC_REQUEST.json --request-sha256 f2d2a8a52fd35ec383018f44c1a7802547a48eec9923f830aedf0845e907b94f --output research_tracking/runs/baseline-evaluation-readiness-20261117-01/SYNTHETIC_CLI_METRICS02.json
```

Đối với model nghiên cứu, caller cần chuẩn bị SelectionPopulation bằng prepare_selection_population từ public selection role đã audit, khai báo plan namespace/seed/counts đúng source và pin bốn artifacts. Metadata plan không chứa final events. Request chỉ chấp nhận selected-only raw phase. Calibration/outer cần consumer theo phase được version riêng, không đổi nhãn các CSV selection.

## Phần cần làm tiếp theo để đủ đề cương

| Task | Inputs và nghiệm thu | GPU |
|---|---|---|
| SG01 — Main Grade10 selection | Public corpus/roles và resource allocation của cohort chính; source/runtime/recipe 29/30 đã pin; chạy producer hiện hành, best reload khớp và đủ target/OOV artifacts | Không bắt buộc; CPU recipe hiện hành |
| SG02 — Cached metric verification | Gói SG01, independent SelectionPopulation và plan; chạy CLI này, giữ input pins/coverage/common target keys; đủ chín candidate mới đi qua gate lựa chọn hệ thống | Không cần |
| SG03 — Baseline refit 90 lifecycle | External selection freeze của đủ candidate; fresh initialization, same frozen epochs và optimization 90%, checkpoint origin/BN/RNG/reload hợp lệ | Cần dự toán tài nguyên riêng |
| SG04 — Calibration và independent evaluation | Refit checkpoint, calibration 10 tách biệt, reference bank/source bindings; nối calibration/online adapter đã nghiệm thu và independent final/outer targets | CPU fit T; inference tùy domain |
| SG05 — Junyi domain qualification | Mapping exercise/tag/node, vocabulary train-only, learner roles outer fold4 và native memory/window recipe rõ; compatibility tests trước fit, không chuyển Grade10 embeddings sang Junyi | Chỉ quyết định sau bounded benchmark |
| SG06 — Junyi selected/refit/calibrated comparison | SG05 và frozen request/định mức; shared target population với AKT/GAM, báo cả full và common coverage, learner-level inference | Dự toán sau SG05 |

Historical BKT 5fold dùng lượng dữ liệu train khác refit 90 của protocol 21. Giá trị metric cùng công thức có thể trình bày đúng phạm vi, nhưng kiểm định graph contribution cần information-matched contrasts theo protocol. Gói này không bổ sung full CV hoặc đọc Holdout.
