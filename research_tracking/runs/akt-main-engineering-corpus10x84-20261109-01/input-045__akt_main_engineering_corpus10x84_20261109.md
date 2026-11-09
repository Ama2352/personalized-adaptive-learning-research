# Corpus tích hợp Main10×84 được sinh và đọc lại từ nguồn thật

## Kết quả và mục đích

ROOT đã chạy một lượt collector cho corpus riêng `grade10-main-lifecycle-engineering10x84-20261109-01`. Outer được chấp nhận ở9,4790097000s trong budget70s, worker8,1647062000s trong60s. Actual840attempts đều return, chia672train+84selection+84calibration. Final events0, model calls0 và optimizer calls0. Owned Job đã cleanup thành công, còn0process, handle đóng, returncode0 và denied attempts rỗng.

Fixture này kiểm đường đi genuine collect → publish → public reader restart trước khi dùng cho tích hợp Main lifecycle. Corpus canonical60×210 được giữ riêng. Kết quả này chưa là selected fit hoặc hiệu quả dự đoán/học tập của A0–A3.

| Role | Learners sinh events | Events mỗi learner | Actual attempts/returns | Incorrect/correct |
|---|---:|---:|---:|---:|
| Train | 8 | 84 | 672/672 | 180/492 |
| Selection | 1 | 84 | 84/84 | 26/58 |
| Calibration | 1 | 84 | 84/84 | 22/62 |
| Final metadata | 1 | 0 | 0/0 | Không sinh nhãn |

Không đổi seed/persona hay lấy lại mẫu theo class counts. Chúng là số đếm dữ liệu của fixture, chưa là model metrics hoặc bằng chứng calibration.

## Điều đã được kiểm bằng nguồn và actual receipts

Plan thật dùng Development10, final metadata1, seed42 và namespace riêng. ProfilesPG được truyền vào environment/provenance. Original recipe `cyclic_items_seeded_offset` lấy một offset từ behavior RNG rồi đi trọn84items. Native collector xác nhận bank28concepts×3difficulties1050/1200/1350. Public restart kiểm mỗi learner có đủ84distinct item IDs, exact trajectories giống ResearchCollectionResult gốc, không lấy subset thuận lợi.

Clock giữ `1767225600+(rank+1)×21600` UTC. Source-row dùng ordinal learner của toàn plan×1.000.000+rank+1, không đánh lại theo từng role. Worker xác nhận đủ840source-row duy nhất và timestamps theo công thức. Outcome/learning/behavior dùng original collector và RNG channels của nguồn Paper2. Không dựng teacher returns hoặc ResearchCollectionResult bằng fixture thay thế.

Genuine publisher ghi schema17files, DONE cuối sau source/readback checks. Public reader nạp public9+DONE và xác nhận role/provenance/plan/bank/source hashes. Public-reader semantic identity là `03d168afdde03af27f322946c3655e75324bef235543624caf3d9372e2bd2683`. Outer kiểm SHA/size của cả17files. Chỉ mở oracle bytes để kiểm integrity, không parse oracle để tạo features hoặc nhận định kết quả. Tác vụ collect/publish có quyền tạo và readback oracle sidecars của fixture mới theo API gốc.

## Prerequisites, tài nguyên và kiểm pure tách biệt

Collector đã gọi genuine CPU schema2 preflight và explicit native Gate05 reader, với10read-onlyGit provenance commands. Nguồn13collector cùng6extra orchestration/helper/publisher/reader giữ nguyên trước/sau, request SHA giữ nguyên. Source Gate177/runtime/index đã được chấp nhận trước đó và được tham chiếu trong receipts. Các artifact lớn của Gate không nhân đôi vào bundle này.

Worker ghi14resource snapshots, peak RSS/peak-wset quan sát95.625.216B và free RAM nhỏ nhất3.866.382.336B. Allocation là RSS512MiB/free2GiB, worker60s, owned65s gồm cleanup3, whole outer70s gồm finalization5. Native collector/publisher còn kiểm tài nguyên ở operator/event. Đây là telemetry hợp tác và owned timeout cleanup, không hard allocation quota hoặc đo mọi transient peak. Profile launcher bên ngoài ghi9,6366801000s, scope khác outer9,4790097000s.

ROOT profile launcher cấp exact Win03 child Git environment, chỉ loại GH_PAGER/GIT_PAGER đã review. Parent environment giữ nguyên. Không thay global Git, dependencies hoặc scientific recipe. Pandas/NumPy và UTC timestamps là dependencies thật của collector. Không có Torch/model/solver imports trong actual collector path được phép.

Trước collection, ROOT chạy riêng9unittest methods với21subtests manufactured metadata. Actual pure outer1,4813979000s/30, worker0,5302945000s/15. Validator20attempts/1return/19raises và failure_accounting7/2/5 đúng dự kiến. Observers phục hồi,0FES/expectedFailure/unexpectedSuccess, Job0. Pure check không đọc corpus hoặc gọi teacher và không tự chứng minh actual840calls. Actual collection có allocation và receipt riêng.

## Artifact identities và giới hạn tiếp theo

| Artifact | SHA-256 |
|---|---|
| Actual collector outer | e1745fc0423fd9660218d49a51a57126ac74d40810a2f6c58c8f776bd554c127 |
| ROOT request | b99e6825b2b0c03316b6e4c167c682f820432c3b01a611c2199270e848eabe60 |
| corpus.json | 78da1a4fd1708bb1efca723caed4976ed518687eb70b847fbdf780f111191151 |
| DONE.json | 9b565431267a1e0e6f6fb4c05b42a989b2d533d2de98991e64927149b1c5b710 |
| Pure9 outer | 3ea41b137ec9672ce7e66f184a5c0409c575e16a63303461b25e33f35ab9261b |

Publication receipt liệt kê17canonical files tổng629.991B. ROOT dự kiến commit exact synthetic bytes riêng. Bundle `akt-main-engineering-corpus10x84-20261109-01` chỉ giữ orchestration sources, sourcefreeze/request, reviews, pure/raw owned receipts, actual publication/readback evidence và SHA inventory trước/sau copy.17corpus files được tham chiếu bằng size/SHA và hash opaque, không chép oracle hoặc canonical corpus vào bundle. Wording review cũ dùng “extra_sources rowlist” được làm rõ trong handoff. Freeze thực có collection_sources13/extra_dependencies4/owned_sources4, builder chọn exact13/6maps và từ chối duplicate.

DONE hoặc published bytes riêng lẻ chưa đủ thay actual outer acceptance. Lần này actual collect/publication/restart đã được chấp nhận, còn actual selected-only A0 cần config/auth/guard và workload riêng trên corpus mới. Không dùng guard-only authorization của canonical60 cho fixture này. Chưa có selected epoch, optimizer fit, checkpoint/best export, refit90, calibration, main matrix, CUDA/cloud hoặc RQ completion trong bằng chứng này. Fixture allPG/cyclic84 không thay allocation nghiên cứu đã chọn.
