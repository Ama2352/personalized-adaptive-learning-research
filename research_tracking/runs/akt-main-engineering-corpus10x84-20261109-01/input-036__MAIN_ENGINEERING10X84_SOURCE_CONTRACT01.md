# Corpus tích hợp thật10×84 — nguồn chờ ROOT review

Đây là implementation chuẩn bị từ `MAIN_SELECTED_GENUINE_CORPUS_PLAN01.md` SHA3487dea3b663c336dd4a187568f754f7cd7d62d98e5d8f721cafec64cca2f857. Không chạy/import/test hoặc tạo request/corpus/auth trong nhánh này. Worker, outer và chín pure tests nằm trong prep, không thay177nguồn hoặc test discovery hiện hành. Canonical60×210 không được đọc như đầu vào hay thay thế.

## Công việc hữu hạn

`ResearchSplitPlan` thật dùng namespace/corpusID `grade10-main-lifecycle-engineering10x84-20261109-01`, seed42,10Development và1finalmetadata. Split đúng8train/1selection/1calibration/1finalmetadata. ProfilePG cho cả10learner chỉ truyền vào environment/provenance, không thêm profile/oracle vào observable rows. Native recipe giữ `cyclic_items_seeded_offset`,84events/learner, start1767225600/gap21600UTC. Source-row giữ ordinal của toàn plan×1.000.000+rank+1, không đánh lại thứ tự riêng từng role.

Worker chỉ gọi nguyên bản `collect_research_role` ba lần với các giới hạn672/84/84. Native function tạo `ResearchCollectionResult`; wrapper không dựng object hoặc điền teacher returns giả. Sau đó gọi `publish_research_corpus` và `read_public_research_corpus` thật. Native sources, validators, RNG channels và schema đóng không bị thay đổi. Không có epoch/trainer/model/optimizer/GPU calls.

840teacher attempts được reserve bền vững trước native work, không reset khi lỗi. Mỗi role có started receipt và collection manifest được fsync. Counter của role chỉ được coi complete sau manifest nguồn xác nhận exact attempts=returns. Nếu hardkill khi role đang hoạt động thì actual count còn UNKNOWN≤840, có lower bound từ các role đã hoàn tất; không ghi0 hoặc tự retry. Exception có genuine collector receipt cho phép lưu actual partial counters. DONE hoặc published files không tự là acceptance.

## Admission và giới hạn đề xuất

Request schema đóng trong `validate_contract` là consistency check, không quyền chạy. ROOT phải chốt source/request SHA và operation reference trước owned dispatch. Request chưa được sinh. Runtime schema2 thật3fdddca8… và indexGate05riênge8162f6e… được bind exactpaths/SHA. Worker gọi genuine `authorization.preflight` và `require_gate2_evidence` trên config phasepreflight, với current source/lock/runtime, trước collector import. Không dùng booleans thay actual validators. ProfileGit native03 phải được ROOT cấp đúng trong process environment; outer không strip/sửa Git variables, không network hoặc fetch.

Protective allocation đang **đề xuất để review**, không dự báo runtime. Worker60giây, owned tối đa65giây gồm cleanup3, wholeouter70giây gồm finalization5. RSS512MiB/free2GiB được kiểm trước và sau heavy imports, các role, publisher, reader và finalization. Native collector/publisher tiếp tục kiểm tài nguyên theo operator/event. Checks hợp tác không chứng minh mọi transient peak, owned Job bảo vệ timeout/cleanup. Publication file≤8MiB, total≤16MiB, oracle≤12MiB. Một lượt, failure giữ partials.

Warm metadata dùng actual `platform.uname`/`platform.processor` trước NumPy/pandas, chỉ exactSystemRoot `cmd /c "ver"` tối đa3lần, đóng phase bằng finally. Sau đó chỉ10exactread-only Git commands trong prerequisite phase. Denied attempts kể cả bị bắt exception làm verdict thất bại. Các importTorch/solver/cloud, protected data và mọi corpus ngoài namespace mới bị chặn. Reader phase chỉ được đọc public10 của namespace mới. Đây là guard tác vụ cụ thể, không blanket filesystem sandbox.

## Expected artifacts và acceptance

Prep receipts gồm reservation, actualmetadata, prerequisites, plan/profiles,3started+3collection receipts, publication, worker/outer result và owned launch/log/cleanup. Failure thêm rawfailure.log/failure.json và giữ mọi phần đã ghi. Corpus success giữ existing schema17files gồm public9+DONE và7oracle sidecars/inventory. Collector và publisher được phép tạo/readback oracle của **fixture mới**; publicreader chỉ đọc public10. Outer kiểm SHA/size cả17files dưới dạng bytes, không parse oracle để tạo features hoặc tính kết quả nghiên cứu.

Acceptance cần exact840attempts/returns, no final events, role counts8/1/1, toàn10learner đủ84distinct actualbank items, giữ toàn840global source-rows/timestamps, observable trajectories đọc lại exact với result gốc, đúng domain/plan/provenance/source. Source trước/sau và requestSHA không đổi,0caught forbidden attempts, complete publication/publicreader và ownedJob0. Classcounts được ghi thực tế, không resample khi labels không thuận lợi. Các nguồn13collector cùng6extra orchestration/publisher/reader/helper phải được rootreview và hash trước/sau. Core sources177 còn được genuine Gate reader kiểm.

Chín pure methods chế tạo kiểm schema/no-final/namespace/policy, exactsource allowlist, digest/cap types, prerequisite identity và reservation/failure accounting cùng cyclic84 algebra. Không kiểm được actual teacher, RNG equivalence, valid output17 hoặc lifecycle. ROOT có thể chạy pure batch riêng trước quyết định native. Expected workload native840chỉ được thực thi sau source/request/resource review; không có automatic dispatch trong helper.

Sau collection, actual selected-only A0 vẫn cần config/auth/guard riêng cho corpus mới, frozen20epochs/patience3 và tối đa40Adam/13.440optimizedtarget exposures. Các bước này chưa có trong worker collector. Integrationfixture không thay allocation60research, không tính vào chín actual research candidates, hai môi trường hay RQ efficacy/completion.
