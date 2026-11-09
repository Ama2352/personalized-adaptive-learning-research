# Review tĩnh độc lập collector engineering10×84

## Verdict và nguồn

Scoped static PASS. Chưa thấy deterministic mismatch giữa worker/outer và API collect, publish hoặc public reader hiện hành. Review chỉ đọc source, định nghĩa type, metadata đường dẫn và SHA. Không import Python, chạy test/native/Git, đọc dataset, giải mã corpus hoặc tạo ROOT request/auth. Khả năng hoàn tất840native calls trong budget60s chưa được đo bởi review này.

| Nguồn frozen | SHA-256 |
|---|---|
| collect_main_engineering10x84_01.py | 121386eef563fb88ac04e7c66849f169cf8de548fffaaee8c38be6c86f045e77 |
| run_main_engineering10x84_01.py | a728ac14a6be6c42efb8123a6f368d8ebd51436c3b40656e474097c13450abab |
| test_main_engineering10x84_contract01.py | 6be4364871d004651d58c6b0ea53016164c97dee50df1590158e160db7a5a072 |
| main_engineering10x84_source_freeze01.json | 6f44f24f573f4c668eb3a34af87f189ad7d4f1e7db83afd987cfd0d1f43c7b8c |

Các SHA được kiểm lại sau review, không sửa bốn file trên.

## API, dữ liệu và accounting

Worker dòng233 gọi nguyên bản `collect_research_role` với ResearchSplitPlan/Recipe/Limits thật. Limits6fields khớp source. Plan Development10 chia8/1/1, final1 chỉ là metadata. ProfilesPG được truyền vào đúng environment/provenance của từng role. Không dựng ResearchCollectionResult hoặc thay teacher outcomes. Recipe cyclic chọn offset một lần rồi `(offset+rank)%84`, nên84ranks bao phủ toàn bank84. Native collector tự xác nhận28concepts và ba difficulty1050/1200/1350. Worker kiểm lại actual item IDs từng learner sau public restart, cùng ordinal toàn plan×1.000.000+rank+1 và timestamp1767225600+(rank+1)×21600.

Ba reservations672/84/84 tổng840 phù hợp workload. Counter tăng ngay trước genuine environment.interact rồi tăng returns sau body trong native source. Worker chỉ đánh dấu completed khi manifest thật xác nhận exact attempts=returns và coverage. Exception có receipt dùng actual partial attempts, còn hardkill/thiếu active receipt giữ UNKNOWN với lower bound từ completed roles. Failure sau khi đã hoàn tất role không làm mất actual calls của role đó. Một số failure sớm trước durable reservation chỉ có owned/raw logs và bị outer từ chối, không được suy ra success hay zero work từ việc thiếu failure.json.

Publish dòng241 dùng đúng CorpusPublicationLimits7fields và ShardLimits3fields. Reader dòng246 dùng đúng CorpusReadLimits7fields, whole event cap840 và role cap8 phù hợp cả ba roles. PublicRoleData.trajectories, audit/reference_complete/class_counts, bank.item_ids và publication.payload/files đều tồn tại với schema đang dùng. Outer kiểm đúng17files gồm public9+DONE và7oracle sidecars. Việc outer mở oracle bytes để hash/size là kiểm integrity. Public reader được tách phase và chỉ mở public10, không parse oracle để làm features. DONE không đủ thay outer acceptance.

## Prerequisites và runtime guard

Worker gọi genuine authorization.preflight và require_gate2_evidence với explicit schema2 runtime và indexGate05, rồi kiểm đúng SHA. Gate reader vẫn so lock/upstream/source map hiện hành. Không dùng dictionary field PASS làm quyền chạy. Request13collection sources khớp source_inventory của original collector, cộng6extra orchestration/helper/publisher/reader sources. Pre/post pins và request bytes được kiểm lại. Các production177files được genuine Gate reader kiểm ở prerequisite, không phải một source snapshot mới do fixture tự cấp.

Pandas/NumPy là dependency thật của collector và Paper2 loader. Audit không cấm pandas hoặc UTC datetime imports. Original recipe tạo pandas timestamp bằng `to_datetime(..., unit='s', utc=True)` và giữ native environment path. Không có generic project-PYC write guard gây nhầm dependency import thành model execution trong worker này. Outer cung cấp PYTHONDONTWRITEBYTECODE trước child launch. Không nên tự thêm các hạn chế không thuộc scope rồi gọi những import hợp lệ là scientific failure.

Windows metadata là phase thật, exactSystemRoot cmd/ver tối đa3, sau đó chỉ exact10read-only Git commands trong prerequisite phase. Torch/solver/cloud/network/undeclared processes và protected paths bị chặn. Đây là audit hợp tác của tác vụ. Outer cần đúng Win03 process environment được ROOT launcher review, không tự strip thêm credentials hoặc đổi global Git. Các output parent hiện quan sát là thư mục thường. Fixed paths và public publisher alias guards không tạo một chứng minh tổng quát về mọi filesystem race.

Worker60s, owned65 gồm cleanup3, outer70 gồm finalization5 là các deadline riêng đã nêu rõ. Worker dùng remaining global time cho từng native operation, rồi kiểm resource/time sau role, publisher, reader và cuối lượt. Collector/publisher cũng có event/operator resource checks. RAM/RSS là quan sát hợp tác, không hard allocation quota. Success cần RC0, owned cleanup/Job0 và complete worker result. Bất kỳ cap failure hoặc partial publication phải giữ failure, không retry hoặc tự tăng budget.

## Schema đề nghị cho ROOT request builder

Chỉ mô tả schema ở đây, chưa tạo request. Root-owned builder nên đọc và hash source-freeze6f44 cùng actual files, chuyển hai rowlists `collection_sources` và `extra_sources` thành map `path → sha256`, từ chối duplicate paths trước chuyển. Không dùng rowlist trực tiếp vì validate_contract đòi dict. Chỉ chọn đúng13collection/6extra paths, không gộp test/contract rows trong freeze vào hai map này.

Request phải có đúng14keys sau.

`schema_version`, `purpose`, `approval_reference`, `plan_recipe`, `collection_recipe`, `profile`, `generated_roles`, `limits`, `collection_sources`, `extra_sources`, `runtime_report`, `runtime_sha256`, `gate_index`, `gate_index_sha256`.

Các values phải khớp frozen PLAN/RECIPE/LIMITS của source. Giữ JSON float cho worker_seconds60.0, outer_seconds70.0, owned_seconds65.0, cleanup_seconds3.0 và finalization_seconds5.0 vì validator so canonical JSON chính xác. `profile='PG'`, generated_roles theo thứ tự train/selection/calibration, purpose `GENUINE_10X84_ENGINEERING_CORPUS_NOT_RESEARCH_ALLOCATION`. Approval string của request phải bằng CLI operation reference. Runtime/index dùng exact paths/SHA đã frozen. ROOT ghi request exclusive dưới P rồi external-SHA-bind khi dispatch. Request consistency và sourcefreeze metadata không tự cấp dispatch authority.

## Giới hạn bằng chứng

Test source có9unittest methods và manufactured request/receipt fixtures. Chúng chỉ kiểm schema, reservation accounting và cyclic algebra, chưa chứng minh actual native/publisher17files, RNG parity, feasible duration hoặc lifecycle. AllPG/cyclic84 là engineering fixture rõ ràng, không thay canonical60×210, không là9research candidates hoặc evidence về prediction/learning efficacy. Sau accepted collection vẫn phải có config/auth/guard/lifecycle allocation riêng cho corpus mới. Không suy fitted/selected/refit/calibration/CUDA readiness từ review này.
