# Handoff source-only pure9 và request builder

Chưa import/chạy/test hoặc tạo actual request trong lượt chuẩn bị này. Collector121386, outera728, test6be436 và freeze6f44 giữ nguyên. ROOT phải review code và external SHA trước dispatch.

## Pure9 hữu hạn

`check_main_engineering10x84_pure01.py` có worker/outer trong một file, dùng helper0dc nguyên bản. Owned GO diễn ra trước argparse trong worker. Chín methods thật được nạp từ test source đã ghim, không nạp domain modules. Chỉ hai helper metadata trên `tests.worker` được observe pass-through và restore. Counts dưới đây là workload dự kiến suy từ source, chưa là kết quả chạy.

| Helper | Attempts | Body returns | Raises được negative fixtures xử lý |
|---|---:|---:|---:|
| validate_contract | 20 | 1 | 19 |
| failure_accounting | 7 | 2 | 5 |

Exact9method names nằm trong packet, kèm21subtests. Không nhận expectedFailure, unexpectedSuccess, skip hoặc partial population. Import NumPy/Pandas/knowledge_tracing/model/solver bị từ chối, corpus/protected/cache dữ liệu bị chặn. Windows metadata phase cho actual literal cmd/ver tối đa3, đóng trước fixture bodies. Parent environment được khôi phục, TEMP của child nằm trong output mới. Source5/runtime4 hashes được kiểm trước/sau. Không dùng global monkeypatch hoặc fake namespace để vượt guard.

Whole30s, owned18s gồm cleanup3, worker15s. RSS1GiB/free2GiB được kiểm admission và monitor. Actual unit/logs/Job0 và postwrite-time đều cần đạt. Các zero-work assertions là source/import/data boundaries, chưa phải observer neural body. Không actual teacher/corpus hoặc Root request được tạo bởi tests.

ROOT entrypoint sau review dùng repository .venv, controllerSHA và packetSHA ngoài command. Output mới nằm ở `main-engineering10x84-pure01` và `main-engineering10x84-pure01-owned`. Không retry hoặc xóa historical outputs.

## Request builder tách riêng

`prepare_main_engineering10x84_request01.py` là source-only metadata helper, không nằm trong9test cases. Mặc định chỉ kiểm metadata và in digest dự kiến, chưa ghi request. Chỉ `--write-reviewed-request --review-reference <ROOT-review>` mới ghi exclusive `main_engineering10x84_request01.ROOT.json` sau actual source/runtime/index pre/post hashes và validate_contract thật. Các tham số bắt buộc còn có builder SHA, freeze SHA6f44 và approval reference. Không dispatch child, native collector, Git, model hoặc authorization.

Làm rõ tên field của source-freeze6f44 để tránh đọc nhầm wording trong review trước. Freeze có `collection_sources`13, `extra_dependencies`4 và `owned_sources`4. Request nhận collection map13 và extra map6. Extra map lấy dependencies4 cộng đúng collector/outer2 từ owned_sources. Test/contract còn lại chỉ là nguồn review. Builder từ chối duplicate rows và kiểm actual bytes. Constants được lấy từ source worker đã pin, giữ float time caps. Không tự chép constructed request với fake SHA từ test fixture.

ROOT cần source review riêng cho builder trước lần gọi metadata, và phải duyệt explicit request SHA/operation/resource cho native collection sau đó. Pure9 success nếu có không chứng minh request builder,840actual teacher calls hoặc corpus17publication đã chạy.
