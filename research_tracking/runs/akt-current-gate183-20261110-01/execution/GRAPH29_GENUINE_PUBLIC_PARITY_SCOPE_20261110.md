# GRAPH29 — phạm vi parity qua public producer

Ngày 10/11/2026. Đây là kết quả đọc nguồn và đề xuất để ROOT duyệt. Chưa tạo harness, authorization, Gate, corpus hoặc chạy mô hình trong lượt này.

## Bằng chứng hiện có và ranh giới

ROOT thông báo cold299 và native18 hiện hành đã đạt. Chúng kiểm metadata, low-level checkpoint và hai ca EarlyStopping thật. Chưa có bằng chứng actual public producer chạy control liên tục rồi pause/restore/export theo GRAPH29. Hai mức này phải được giữ riêng.

`research_selected_runner.py` dòng 223–239 dựng guard thật bên trong entrypoint. API không nhận model factory, corpus, callback cấp quyền hoặc guard do caller tạo. `research_main_execution.py` dòng 211–263, 389–422 và 510–555 kiểm runtime/source/Gate, authorization đóng và public corpus reader thật. Không thể nâng fixture `manufactured_parent` hoặc mocked reader thành bằng chứng public lifecycle.

Đầu vào nhỏ nhất đã có bằng chứng thực trong lane này là corpus `grade10-main-lifecycle-engineering10x84-20261109-01`. Mười public files được reader mở, gồm 8 train learners ×84 =672 targets, một selection learner ×84 và một calibration learner ×84. Collector/publication đã hoàn tất trước đây. Lượt parity đề xuất tái dùng nguyên bytes, không gọi teacher, collector, oracle hoặc dữ liệu Junyi/Holdout.

## Entry và workload đề xuất

1. Control độc lập gọi `run_main_selected_candidate` ở dòng 405, không pause policy.
2. Parent mới gọi cùng public entry với `SelectedPausePolicy`. Sau terminal của owned Job và cleanup, outer gọi `research_selected_resume.seal_pause_terminal` dòng 358 để nối actual worker/request/ready/GO/receipt bằng SHA và ownership đã ghi.
3. Child ở process mới gọi `run_main_selected_resume` dòng 410 với `SelectedResumeRequest` và authorization riêng. Child dùng fresh output, khôi phục latest, replay stopper/history rồi tiếp tục epoch kế tiếp. Khi hoàn tất, producer tự dựng fresh best-reload và xuất raw selection.

A0 là phạm vi nhỏ nhất để kiểm producer lifecycle. A1 expert có thể kiểm thêm nhánh graph với actual pinned topology, cùng geometry. A2/A3 cần Method24 artifact thật gắn đúng TRAIN80 của corpus này. Không dùng scores của corpus khác. Phép kiểm A0 không nghiệm thu riêng A1/A2/A3 hoặc toàn bộ ma trận chín điều kiện.

Giữ config khoa học của tiny public pilot đã có. Các giá trị là d_model256, d_ff1024, final_fc512, một block/tám heads, context100/target_block100, batch4, dropout0,05, Adam lr0,0001, seed42, patience3, min_delta0,0001 và max_epochs20. Không cắt geometry hoặc ép chạy hai epoch để tạo PASS. Seed và initialization được producer đặt thật trong `_construct` dòng 114–134. Không warm-start control từ parent.

Chạy control trước để nhận số epoch thực E và lịch sử validation. Chọn p là epoch không phải best nhưng còn tiếp tục được, p<E và stale_epochs<3, nhằm kiểm latest khác best. Đây là lựa chọn vị trí ngắt trong kiểm kỹ thuật, không điều chỉnh phương pháp theo kết quả nghiên cứu. Nếu không tồn tại p như vậy, giữ thiếu coverage này. Pause ở E1 đơn giản hơn nhưng chưa chứng minh latest/best tách nhau.

### Trần tĩnh để ROOT xét trước dispatch

Với corpus84 sự kiện/learner, mỗi learner tạo một target window vì84<100. Mỗi epoch có hai train batches/672 targets và một selection batch/84 targets. Các con số sau là tính từ nguồn, chưa là ledger actual của phép kiểm mới.

| Tổng control và lineage parent→child | Công thức |
| --- | --- |
| Adapter/backbone và Adam constructors | 5 mỗi loại, control2 + parent1 + child2 |
| Adam steps, backward, clip, train forward | 4E mỗi loại |
| Training target exposures | 1344E |
| Selection forwards kể cả hai final best exports | 2(E+1) |
| Selection target evaluations | 168(E+1) |
| Architecture forwards tổng | 6E+2 |

Nếu E≤20 thì tối đa80 optimizer steps,26.880 training exposures,3.528 selection evaluations và122 forwards. Không cộng chúng thành mẫu độc lập. Mỗi lineage được guard giới hạn ba constructors. Checkpoint saves bằng hai lần số lần best cải thiện, cộng một latest bổ sung khi p không phải best. Ba restore operations thật gồm control-best, child-latest và child-best. Copy inherited-best là sao chép bytes được kiểm SHA, không thêm neural call.

Existing pilot allocation là300s training/540s wall cho một run hoặc toàn lineage parent→child. Control là allocation độc lập. Những số này không chứng minh workload mới sẽ vừa cap. ROOT cần duyệt allocation mới, bộ đếm actual và admission RAM trước chạy. Không dùng kết quả unit tests để tự mở giới hạn.

## Các phép so sánh bắt buộc

- Initial backbone/model SHA giống nhau trước restore. Cùng public inputs, encoding, graph condition, seed và semantic config. Projection hiện chỉ bỏ run_id/output_dir và derived stage config SHA.
- Đối chiếu từng epoch objective, prediction semantic SHA, selection loss, completed target/optimizer counters và stopper history/best/stale. So sánh riêng những trường thời gian và đường dẫn vốn khác nhau.
- Tại pause phải có latest ở p, best đúng lịch sử, sealed terminal/request/owned receipt khớp và không failure/postwrite rejection. Retained bytes, parent wall/training và các counters không được reset trong child.
- Sau resume, so sánh exact model tensors, Adam moments/participation, owned RNG và best epoch với control. Producer đã kiểm final raw prediction semantic SHA với best-epoch history trước export.
- So sánh semantic rows của predictions.csv/targets.csv và coverage đủ84 selection targets, kể cả null/OOV accounting. Không yêu cầu toàn terminal JSON giống bytes vì output paths, authorization, lineage và timing khác nhau.

Intentional complete-epoch pause là phạm vi này. Unexpected crash, partial-epoch replay, external freeze, refit90, calibration fit, hệ thống thắng hoặc quyền trả phí/GPU vẫn nằm ngoài phép kiểm.

## Gate hiện hành và đường refresh thật

`authorization.gate2_build_hashes` dòng96–113 quét source/test paths thực. `require_gate2_evidence` dòng126–175 yêu cầu exact build map, lock SHA, upstream commit, PASS và0 failures/errors/skips. Main guard còn đòi genuine schema2 runtime đúng CPU, physical same-root .venv, Git profile/EOL proof và exact evidence hashes. Vì source AKT đã đổi từ Gate05 cũ, không thể đổi nhãn index cũ thành current hoặc ghép cold299/native18 thay full Gate.

Entrypoint production là `.venv/Scripts/python.exe -B scripts/akt/refresh_gate2.py --run-id <NEW_ROOT_REVIEWED_ID> --timeout-seconds 580 --lock-file <ABS_REQUIREMENTS_AKT_LOCK>`. Không thêm `--publish-current` trong bước kiểm đầu tiên. Native writer dùng đúng ba fresh groups từ `test_partition` dòng37–56, chạy mọi module của `tests/akt` và `tests/shared_kt`, không `-k` hoặc deselect. Đây là software/constructed-fixture suite, không selected fit, corpus collection, CV hoặc Task14/Holdout. Không nên gọi trực tiếp command ngoài owned wrapper đã duyệt vì wrapper mới quản lý descendant cleanup, resource samples và exact collected-vs-JUnit population.

Đường reuse ngắn nhất là derivative mới của `windows_current_gate_worker02.py` và `windows_current_gate_outer03.py` trong prep. Giữ helper owned0dc, genuine refresh writer, native580/owned600 gồm cleanup3/outer630, admission4GiB, free floor1GiB và peak mỗi process3GiB theo profile Gate đã chốt. Không sửa các lượt cũ. Cần làm mới các đầu vào sau trước khi ROOT cấp dispatch.

1. Freeze source/build map và ordered partition hiện hành từ các hàm production. Không dùng lại số177/81/1748 hoặc suy case count từ AST. Source ngoài Gate map vẫn được main source inventories và các proof chuyên biệt ghim riêng. Gate suite này không tự bao phủ toàn bộ tests/gkt.
2. ROOT chạy collect-only ở ba fresh groups, với imports cần thiết được khai báo,0 test bodies, source/runtime trước–sau. Packet mới phải nối actual accepted collection/owned receipts, ordered nodeIDs và mapping JUnit, cùng controller/helper/runtime utility pins. Collection không là Gate PASS.
3. ROOT duyệt profile body counters và thư viện thực sự import của full population trước full dispatch. Không cộng máy móc native18/cold299/model fixtures thành global counter do fixture sharing và cached modules. Không chạy collection hoặc full suite nếu source vẫn đang thay đổi.
4. Chạy full Gate qua owned derivative, kiểm exact group/merged physical JUnit identities,0FES, current source/lock/upstream trước–sau, deadline/resource/cleanup Job0 và pointer cũ nguyên bytes. Không dùng lại kết quả cũ cho các nguồn đã đổi.
5. Chỉ sau actual accepted outer mới tạo một index năm trường mới tại `artifacts/akt/preflight/`, trỏ nguyên report/log thật và SHA của chúng. Reuse ý tưởng `publish_gate05_main_index01.py`, nhưng bỏ các tên/pins/count177 đã cũ bằng các input ROOT ghim thật. Index candidate phải đi qua public `require_gate2_evidence` và genuine preflight. Không cần chạy lại suite chỉ để lập index. Giữ global pointer cũ nguyên bytes trừ khi ROOT duyệt promotion riêng.

Không cần tái collect corpus10×84 hay teacher840 lần. Runtime schema2 cũ có thể được tái dùng nếu genuine preflight hiện hành xác minh nó vẫn khớp cùng source upstream/lock/runtime/device/interpreter. Nếu không khớp mới chạy lại `scripts/akt/check_runtime.py` CPU bằng owned wrapper và output exclusive. Không tạo proof thay cho kiểm thật.

Main tiny metadata builder `prepare_main_tiny_a0_package01.py` dòng97–108 hiện ghim cứng Gate177/schema2/index05; không thể dùng nguyên file đó. Được reuse typed construction, real public reader, condition builder và actual `_metadata` planning dependency của nó sau khi có Gate/index mới. Cần metadata prepare-dry mới, ROOT review rồi materialize config/auth/request mới, với các decision main-selected/pause/resume riêng. Đây là engineering authorization đóng cho corpus fixture, không fit grant từ note này.

## Pins của nguồn đã đọc

| Path tương đối repository | SHA-256 |
| --- | --- |
| src/knowledge_tracing/akt/research_main_execution.py | 0c27b05312c723e34c0590ddec00009e849687cd2a1c5c303c5f93723ca64e77 |
| src/knowledge_tracing/akt/research_selected_runner.py | b2b045d4673ff6cbc8e4e4ade8e5599806e52e501f5c8612e894ff636c2f7a46 |
| src/knowledge_tracing/akt/research_selected_resume.py | 49f74a87a5fa6f11b923c102389695c2c582257d7a782d9cf32caab819cf70d1 |
| src/knowledge_tracing/akt/authorization.py | f35dc9f14a9edf7d1cacf82085db67a11e2c1ca540fe9121a60a14d2f0785027 |
| scripts/akt/refresh_gate2.py | ed87ee74589087b66b434137f67388b64efb4160c41c33ff423ffc41bcc9e157 |
| scripts/akt/check_runtime.py | 4f5be1c58db40cd8875865275bb50f0b8171dc781615d4ce9f862ca598c1f795 |
| artifacts/akt/local-tests/akt-research-runner-20261108-01/prepare_main_tiny_a0_package01.py | 05d30f2e5e408de7156b464ee0f7d566d049213ea3a8e54da2fbaed56a1f9249 |

Pins là bằng chứng đọc nguồn ở thời điểm này, không là actual current Gate hoặc quyền dispatch. Không chạy imports, tests, mô hình, Git hay chỉnh canonical trong lượt phân tích.
