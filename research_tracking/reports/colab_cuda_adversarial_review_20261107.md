# Phản biện độc lập nghiệm thu GPU — 07/11/2026

Reviewer agent kiểm chỉ đọc, không chạy lại model/GPU/cloud hoặc load checkpoint để tính lại state delta. Không tìm thấy mâu thuẫn làm mất actual CUDA synthetic PASS. Hai báo cáo đều giữ `gate4_pass=false`. Các phát hiện sau chặn suy luận từ probe sang full training.

| Mức | Phát hiện và bằng chứng | Điều chỉnh kế hoạch |
|---|---|---|
| P1 | `src/knowledge_tracing/akt/authorization.py:102` kiểm executable Windows; `scripts/akt/check_runtime.py:107` kiểm package origins trong venv; `config.py:132,146` khóa smoke/pilot vào CPU. Notebook kế thừa system-site-packages. | GPU06 thiết kế runtime identity/Linux mode và bounded CUDA phase riêng. Giữ guards Windows, không nới checks để hợp thức hóa một probe khác entrypoint. |
| P1 | Runtime Colab chỉ pin dependency DuckDB; freeze không là hash lock/image digest. | Chuẩn bị Linux/CUDA image, wheel hashes/install report và origins/driver/CUDA/cuDNN manifest. Không dùng lock Windows CPU hoặc lock SDK Modal để train. |
| P1 | `scripts/akt/synthetic_device_probe.py:58` materialize fixture hai learners, train một batch, dự đoán cùng learners. Coverage đúng không là independent model evaluation. | Synthetic Parquet phải đi qua main selection/refit/validation/export worker với learner partitions và cap trước real-data pilot. |
| P1 | Recovery là fresh-process trong cùng runtime, ngắt tại committed optimizer boundary. | Modal-specific durability cần commit→container mới→reload, certificate/hash/failpoints, budget và permission riêng. Chưa hard-kill/preemption/Volume proof. |
| P2 | Lifecycle timer synchronize tổng một bước; không chứa tensorization/model construction. Phase timers chưa đủ synchronization để dự báo từng thành phần CUDA. | Benchmark có warmup, nhiều bước trong cap, length/padding đại diện và train/validation/export/checkpoint/loader overhead riêng. Không ngoại suy400/0,916 sang full Junyi hoặc ngân sách. |
| P1 trước chi phí | `docs/akt-modal-setup.md` còn thiếu launcher thực thi single GPU/container, retry0 và workload/timeout caps; thông tin credits là user-reported. | Exact run spec, readback khả dụng và controls thực thi trước paid launch.30USD free/net0 vẫn binding; Colab PASS không cấp quyền chi Modal. |

## Kiểm độc lập đã đạt

- RESULT_MANIFEST:44outputs,45files kể cả manifest, không file ngoài inventory; mọi SHA khớp. Lifecycle inventory5files và recovery inventory19files khớp.
- Kit139file hashes, notebook embedded ZIP,26lifecycle build hashes và104recovery build hashes khớp; upstream identities bằng nhau.
- Hai Parquet dự đoán có400source rows duy nhất1..400, đúng learner/exercise/label identities;400fitted,0fallback,0invalid probability. Không phải accuracy benchmark.
- JSON recovery có17unique targets=7interrupted+10resumed,3PIDs khác nhau; sampler/RNG-draw/prediction JSON exact. Max state delta dựa probe đã chạy và report/source binding, reviewer không tính lại từ `.pt`.
- Colab505CPUcases có thêm GAM tests; Gate15462cases chỉ AKT/shared. Không gộp hai số hoặc cộng thành một suite độc lập.

## Verdict và batch kế tiếp

**PASS cho bounded synthetic CUDA contracts; NOT READY cho real-data/paid/full research execution.** Correction đã đưa vào `TASKS.json::GPU06`, current investigation state và báo cáo nghiệm thu. Next batch cục bộ: platform-aware runtime manifest/schema, negative controls giữ existing guards, bounded GPU-phase design và synthetic fullworker fixture. Không tự đổi split/selection/mastery methodology hoặc launch Modal. S04/S05, exact Paper1 revision và baseline pipelines còn riêng; không được coi các phản biện kỹ thuật này là toàn bộ blockers nghiên cứu.

Nguồn chính: [nghiệm thu](colab_cuda_acceptance_20261107.md), artifacts gốc `experiments/akt/results/colab-actual-cuda-20261107-01/`, source kitv12 và các file/line nêu trên. Line refs là snapshot source đã kiểm, không thay immutable source hashes trong evidence bundle.
