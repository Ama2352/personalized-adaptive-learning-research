# SAKT research data và lazy public exports — engineering

Hai lượt kiểm actual Windows CPU độc lập: **20 data fixtures PASS** và **3 native export/math fixtures PASS**, không failure/error/skip. Không full SAKT suite hoặc full software Gate.

Data stage: outer 3.282903433s/cap60s; child 2.831698700s. Import đúng package public, NumPy được phép, Torch bị chặn;0model/solver/corpus thật. Scope gồm bốn roles/phases, optimization-only vocabulary, freeze/refit lineage, full-target OOV/cold accounting, masks/local positions, label-prefix/peer isolation và read-only arrays.

Lazy exports stage: outer 6.049573421s/cap30s; child 5.398070300s. Actual Torch2.7.1+cpu, **2 tiny constructors/8 forwards**,0optimizer/solver, CUDA chưa initialized. So public exports với class/function thật và chạy ba phép kiểm core hiện có. Không thể mô tả cả bundle là0model calls; xem ERRATUM.json. Child heavy_modules_loaded=[] ở stage này chỉ kiểm danh sách trainer/AKT model cụ thể, không nói Torch vắng mặt.

Docstring lịch sử của run_sakt_lazy_exports01.py còn nói45giây/không model; code và actual receipts mới là authority: outer30s, owned27s,2constructors/8forwards. Giữ nguyên controller/raw receipt; erratum bổ sung giải thích, không thay lịch sử hoặc verdict.

Observed peak RSS lần lượt 54734848B và 202465280B; RAM available đầu/cuối ghi trong validated_summary.json. Đây là Windows peak/snapshot, không continuous RAM monitor hoặc hard OS quota. Hai owned Job receipts đều xác nhận membership trướcGO, cleanupaccepted, active0 và Popen handleclosed. Allocations60/30s tách biệt; không suy9,33s là thời gian train hoặc throughput.

View nhận corpus qua InitVar, sau kiểm tra chỉ giữ SHA provenance/read limits và shards của phase đã chọn; TRAIN view không giữ selection/calibration labels. Initial initializer và bản WIP còn giữ full corpus được snapshot trước static fix; chúng chưa được chạy test, không dựng RED giả. Hand-off19/20cases chỉ là kế hoạch tại thời điểm viết; XML actual mới quyết định counts. Both first-target policies query_only/unsupported và padding vẫn explicit; không tuyên bố protocol21 bắt buộc một cold policy.

Không sửa old toy caps/engineering checkpoint roles/fitted validators. Chưa research trainer selection→refit→calibration, selected-fit checkpoint/OnlineSession, Junyi adapter, CUDA, actual corpus fit, scientific efficacy hoặc RQ completion. SHA/seals kiểm consistency hợp tác; không source-origin/disk-byte attestation độc lập. Iterator dừng sớm không phải full-population acceptance.

Raw logs/JSON/XML được giữ byte-exact; copy_inventory.json gắn đường dẫn gốc và SHA trước/sau. execution.log chỉ là lần đóng gói, không phải phép chạy test mới. Existing owned helper xem ../windows-owned-worker-engineering-20261108-01/README.md; bundle này không chạy lại helper/test/model.
