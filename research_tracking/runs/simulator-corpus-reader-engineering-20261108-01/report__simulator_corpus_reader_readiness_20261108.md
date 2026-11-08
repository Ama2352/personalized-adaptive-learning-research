# Reader corpus public — engineering với fixture, chưa actual corpus

08/11/2026. **47 tests PASS trong lượt04**, source reader/tests giữ nguyên qua cả bốn lượt; không sinh/đọc actual research corpus, không teacher/model/optimizer/Torch hoặc GPU. [Reader](../../src/knowledge_tracing/simulator_corpus_reader.py) là bước BATCH3A dùng chung cho các model, không phụ thuộc AKT execution guard hoặc publisher ở production import. Root đã đọc toàn source/tests; việc kiểm thử do root chạy, không gán thêm independent-agent execution.

API `read_public_research_corpus(corpus_id, expected_corpus_sha256, expected_done_sha256, limits)` dùng fixed root `artifacts/simulator/corpora/<id>/`, không root override. Nó chỉ mở chín public inputs và DONE; không đọc oracle/, final events hoặc các source paths ghi trong inventory. Stream/read limits hữu hạn cho bytes/file/line, learner, events và wall; kiểm exact JSON schema, duplicate keys/nonfinite, payload chỉ observable, raw SHA/DONE/no failure trước–sau và alias symlink/junction.

Reader tái dựng actual `ResearchSplitPlan` từ stored recipe, `SimulatorBank`, `ResearchProvenance`, `ObservableTrajectory`; reuse auditor hiện có để kiểm roles/seed families, bank/query, logging policy, clock, global source rows và support. Kết quả bất biến giữ full target population/class counts/reference support; metadata accessor trả bản sao mới. Thiếu84item support hoặc two-class là flags rõ ràng, không calibrated/fitted success. Higher research entry vẫn phải kiểm current source/runtime/Gate/authorization/admission/resource trước reader/model; reader chỉ kiểm internal source bindings, không tự mở source inventory hoặc cấp quyền thực thi.

## Bốn lượt được giữ nguyên

| Lượt | Bằng chứng thực tế | Time charge/phạm vi |
|---|---|---|
| 01 | Timeout, không JUnit/counts; stdout42dấu progress không phải42PASS. Windows redirector làm timeoutshim không đủ chứng minh descendant termination; root scan exact argv về sau không thấy process. Giữ trạng thái UNKNOWN. | 28,01250386238098s |
| 02 |1collectionerror; JUnit38B chỉ declaration. `finally ET.parse` không guard làm mất receipt/trace gốc. Nguyên nhân collection02 không recover được. | Root toolwall1,5539638s |
| 03 | Trace gốc đã persist: pandas `platform.machine→uname→win32_ver→_syscmd_ver` yêu cầu metadata shell, audit chặn trước launch; JUnit `platform.node` cùng fallback.2denied events, không có valid test counts/JUnit. Không dùng03 để retro-prove nguyên nhân02. | Root toolwall1,4964003s, controller0,9869718999834731s |
| 04 |47tests,0failure/error/skip,12pins trước=sau;0denied process event/noTorch. | Controller18,043351400003303s; JUnit17,614s |

Lượt04 giữ audit hook chặn `subprocess.Popen`, nhưng thay **duy nhất fallback metadata trong test process** `platform._syscmd_ver` bằng version lấy thực tế từ `sys.getwindowsversion().platform_version`: `(10,0,26100)`. Tuple trả về giữ system/release của caller, version`10.0.26100`; không invent marketing OS/architecture, không patch model/data/clocks hoặc sửa file thư viện. Function và uname cache được restore trong `finally`. Fixture provenance ghim actual `platform.py` SHA`e398f1c9a6581395534242c9d256997ba8921602bb50f21d63ea5999cd800482`. Đây là test-only metadata fixture, **không actual runtime/Gate proof**.

Fixture corpus được publisher tạo trong temp từ observables viết tay:8/1/1learners,84events mỗi learner, nguồn và RAM kiểm bằng mocks có nhãn; native teacher bị chặn. Reader production validators/audits vẫn chạy thật. Tests gồm typed restart/immutable identity, public-only I/O, external SHA/DONE/failure, forged role/query/clock/row/provenance, JSON lỗi, unsupported references/classes, mọi byte/event cap, source mutation trước–sau và alias/wall rejection. Không suy suitability của corpus research chưa tạo từ fixture này.

## Ngân sách và giới hạn thời gian

Root đã cho tăng cumulative test cap30→90s, giữ nguyên chi phí cũ, không reset ledger. Charge ghi được là28,01250386238098+1,5539638+1,4964003+18,043351400003303 = **49,10621936238428/90s**. Ba lượt02–04 gọi `pytest.main` trong cùng actual `.venv` process; Timer55s ở03/04 phụ thuộc GIL, không hard OS quota. Controller04 có posthash/parse timing và receipt đã publish; root poll cùng session18689 đến terminalRC0. **Whole external duration04 không được ghi**: first-yield/poll wait có gap, không cộng các phần đó để giả whole outer time. Receipt04 có câu outer check cần thiết như contract; archive không biến nó thành chứng chỉ outer-wall đã đo. Không rerun chỉ để sửa timing evidence.

Lỗi framework02 và metadata03 được sửa trong controller mới, không sửa production reader/test hoặc nới data/method guards. Chưa chạy current full Gate, actual corpus publication/roundtrip, training hoặc actual runtime admission. Bước sau là worker/corpus operation trong normal environment với ownedJob, guard/source/resource và full actual input checks; không mang fixture metadata này làm runtime authority.

Bằng chứng portable: [47JUnit](../runs/simulator-corpus-reader-engineering-20261108-01/trial04__junit.xml), [receipt04](../runs/simulator-corpus-reader-engineering-20261108-01/trial04__receipt.json), [timing/terminal scope](../runs/simulator-corpus-reader-engineering-20261108-01/reader04-root-observation.json), [copy inventory](../runs/simulator-corpus-reader-engineering-20261108-01/copy_inventory.json). Bundle giữ tất cả controller/failed raw logs/XML/snapshots trước–sau; không sửa sau closure.
