# Corpus Development đầu tiên: hợp đồng trước chạy — 08/11/2026

**Đã chọn profile; chưa sinh corpus, chưa train.** [Cấu hình](../../experiments/akt/configs/simulator-research-corpus01.json) chỉ phục vụ pilot vòng đời một candidate A0 và shared data plumbing. [Kiểm metadata](first_development_corpus_plan_20261108.json) đã tái dựng actual split plan/profile counts bằng `.venv`, không import collector/model. Không thay thế evidence matrix chính, không chọn model thắng từ refit/calibration. Protocol nguồn: [S04-A/S05-B đã adopt](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md); main-matrix phải freeze selector từ raw-selection của toàn bộ candidates trước bất kỳ main refit/calibration.

## Quy mô và lý do

60 learner Development, chia cố định48train/6selection/6calibration, mỗi learner210interactions; tổng12.600teacher calls. Trong từng role, ordinal learner modulo3 gán PG/PY/PYH:16/16/16 trong train và2/2/2 trong mỗi role còn lại. Đây là số learner nhỏ cho lifecycle, chưa cho inference cuối cùng hoặc nhận diện confidence vững chắc. 210events cho phép kiểm cửa sổ context100 qua hai rollover, history>50 và reference-item coverage; không lựa chọn sau khi xem accuracy/outcomes.

150final IDs chỉ là metadata dành riêng trong namespace mới, tương ứng khả năng50/profile ở bước sau. **Không sinh/mở final events, không chốt final evaluation cohort hoặc kích hoạt final experiment.** IDs phát sinh độc lập theo role; số metadata không phải bằng chứng learner diversity/independence.

Logging chọn đều84items bằng RNG behavior riêng, không dùng graph/oracle/mastery/prediction để chọn bài. Teacher Paper2 vẫn có graph/dynamics gốc, vì vậy đây không là graph-free world hoặc unbiased sample đại diện Junyi. Clock UTC bắt đầu01/01/2026, gap6giờ; event đầu ở start+6giờ, event cuối ở start+52,5ngày, khoảng cách event đầu→cuối52,25ngày. Native forgetting trong khi sinh không đổi. Later variants dùng cùng frozen observable corpus; không chuyển checkpoint/vocabulary từ Junyi.

## Điều kiện trước dispatch

1. Reader public-only có test receipt hợp lệ và xác nhận restart typed plan/provenance từ9inputs+DONE, không oracle.
2. Owned Windows worker/redirector được nhận diện, actual-worker Job membership trước GO; timeout/normal-exit cleanup được kiểm. Không bỏ guard vì PID mismatch.
3. Freeze driver/plan/source/runtime SHA, profile map/plan manifest, expected role counts và output fresh; đọc lại trước chạy. Chỉ `.venv`, không cài global. Publisher/collector hiện có không tự cấp quyền outer dispatch.
4. Cumulative whole operation≤120s,1worker, RSS≤512MiB/freeRAM≥1GiB; publication≤30s nằm trong120s, không cộng thành150s. Thời gian import/validation/cleanup cũng tính. Role cooperative budgets phải lấy từ thời gian còn lại, không reset120s cho mỗi role.0automatic retry/teacher budget tối đa12.600attempts kể cả thất bại.

## Artifact và kiểm nhận

Giữ source/plan/profile inventory trước=sau; per-role attempt/returned event counters; raw stderr/traceback, outer PID/Job cleanup/resource receipt. Public output tại `artifacts/simulator/corpora/grade10-development-lifecycle01-20261108/`: corpus/bank/plan,3role JSONL+3manifests,DONE cuối; oracle sidecars riêng, không đi qua model reader. Record byteSHA/size trước khi sao chép evidence rồi kiểm lại tại run bundle mới trong `research_tracking/runs/`; không sửa corpus/runs đã đóng.

Kiểm đủ48/6/6learners×210events, disjoint IDs/source rows, chronology và đúng84items trong từng role; typed reader roundtrip hashes/bank/recipe/provenance. Thống kê **chỉ structural exposure**: số train learners quan sát từng item/concept và co-observed concept pair. Báo thiếu support20 nếu có; không đổi seed/policy sau xem labels/trueedges để đạt threshold. Support20 là điều kiện phương pháp confidence, không cần graph-free A0 dừng nếu corpus hợp lệ; mọi thay đổi confidence model cần ghi phiên bản riêng.

DONE là logical completion, chưa acceptance nếu outer timeout/cleanup unknown, source drift, sai count, thiếu84items hoặc roundtrip fail. Giữ failure/partial bundle và chẩn đoán; không tự mở rộng/rerun. Không nhận kết quả model tốt là điều kiện thành công corpus.

## Sau corpus

Thực hiện single-candidate A0 selected-fit/raw-selection→freeze epoch→fresh refit90→calibration10 và prediction/controller exports dưới bounded execution riêng. CPU pilot hiện chưa có runtime đo; số batch/optimizer steps chỉ workload arithmetic, không forecast. GPU/Modal không thuộc cấu hình này. Sau đo cost/throughput mới lập từng lượt GPU review với $30free-credit-only; không fallback trả phí tự động.
