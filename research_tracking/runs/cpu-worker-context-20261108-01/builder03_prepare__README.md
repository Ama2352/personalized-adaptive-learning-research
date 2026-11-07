# Handoff synthetic context ctx0801 — chỉ chuẩn bị

Builder và 53 case đã frozen theo parent. Lượt CLI này dùng `.venv\Scripts\python.exe scripts/akt/prepare_synthetic_context.py --dataset-id ctx0801 --runtime-report artifacts/akt/preflight/runtime-v2.json --lock-file requirements-akt.lock.txt --gate2-report artifacts/akt/preflight/gate2-current.json --mode smoke`, với PYTHONIOENCODING=utf-8, subprocess timeout 60 giây. Kết quả thực: returncode0, 1.54 giây, không timeout.

Output riêng: `artifacts/akt/synthetic/ctx0801/config.json`, `worker-context.json`, `preparation-inventory.json`, marker và 2 Parquet/cm/sm. Config run_id ctx0801, output tương lai experiments/akt/results/ctx0801; output dir chưa tạo. execution_enabled luôn false; không authorization.json hay approved key nào. Chưa chạy worker hoặc model; optimizer_steps0.

Nguồn dữ liệu: tạo mới 8 dummy learner × 8 event, exercises A/B, PRNG seed42; time_done/source_row duy nhất. Tất cả assignments Development; dummy-00 là fold0 sentinel (8 event), outertrain còn7 learner/56 event; existing inner split cho6train/1val. Nhãn correct chỉ là bit dummy kiểm serialization/guard, không phải Grade10/Junyi, RQ simulator truth hay evidence về learning.

Cấu hình smoke hiện hành: context100, targetblock100, maxlen200; d_model32, heads4, blocks1, d_ff64, final_fc32, dropout0, batch4, maxepochs1. Uppercaps train8/val4, targets64 mỗi phía, total128=2×side, steps2, seconds120, wall300, RSS2GiB, RAMfloor1GiB. Caller chỉ giảm uppercaps; total được suy ra; target budget phải đủ ít nhất1target/learner; step1 cần traincap<=4 để đủ1batch. RAMfloor cố định. Mode cuda-smoke chỉ tạo đặc tả khi truyền limits tường minh đúng context schema; không kiểm GPU.

Sidecar schema1 được loader hiện hành load/revalidate thành công; đúng5 input SHA (events, assignments, cm, sm, marker), tách khỏi config/context/preparation inventory. cm/sm là manifest fixture có row/fold/chronology/label provenance, không giả làm manifest corpus frozen. Hash code contract config/context/watchdog/builder được kiểm trước/sau generation.

Ba reference runtime-v2.json/requirements-akt.lock.txt/gate2-current.json do parent cung cấp. Builder không đọc/verify nội dung các reference, không khẳng định Gate18 đã publish hay worker đủ điều kiện. Parent sẽ kiểm identity runtime/source/lock/Gate2 hiện tại rồi tự tạo bounded authorization theo chỉ dẫn người dùng, nếu phù hợp. Không chạy realdata/Holdout/GPU/cloud/Modal; không sửa shared source/index/state hay Git.

Bằng chứng: lượt01 giữ52pass/1CLI-fixturefail; lượt02 53pass6.50s. `handoff-inventory.json` ghi hash source hiện tại, pre-copy SHA từ receipt và post-copy SHA snapshot của cả2lượt, hash mọi output/log/XML/receipt/README liên quan; inventory không tự chứa hash chính nó. Các thư mục pytest tmp giữ nguyên làm provenance của fixtures, không phải corpus huấn luyện.
