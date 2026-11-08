# Publisher corpus simulator: kiểm serializer, publication và restart

08/11/2026. Đã thêm [writer riêng](../../src/knowledge_tracing/simulator_corpus_publisher.py) và [kiểm thử](../../tests/shared_kt/test_simulator_corpus_publisher.py). Writer nhận ba `ResearchCollectionResult` đã có, **không gọi collector/environment, model, optimizer hoặc remote**. Actual31kiểm tmpFS đạt; chưa sinh hoặc xuất corpus nghiên cứu thật vào project. Đây là engineering cho shared training inputs, không kết quả RQ, support/diversity đủ nghiên cứu hoặc execution authority.

## API và schema đã thống nhất

`publish_research_corpus(plan, results_by_role, *, corpus_id, expected_sources, expected_protocol_sha256, limits)` dùng ROOT cố định từ vị trí module. Không có `project_root` override hoặc đường dẫn export tùy ý; đích duy nhất `artifacts/simulator/corpora/<corpus_id>` mới, không overwrite/repair/retry partial, không symlink/junction/protected paths. Tests monkeypatch constant vào workspace tạm do chúng sở hữu; đây không là API export production.

Schema prospective do guard và publisher cùng chốt: `CORPUS_SCHEMA_V1.json` SHA `ba4a3d8ca412395b4b3841da010c736f1ceac3d5bd1a67e5de87ef7c7287e578` trong `artifacts/akt/local-tests/akt-research-execution-20261108-01/`. Giữ9model-input files: corpus/bank/plan JSON, ba role JSONL và ba role manifests. Corpus14keys, role entry7keys, shared normalized recipe7keys. JSONL một dòng/learner, canonical UTF-8/LF, giữ nguyên thứ tự events; không oracle fields.

**Sửa gap restart trước run đầu:** plan.json có3keys schema_version/recipe/manifest; recipe lưu đủ5constructor fields namespace/root_seed/development_learners/final_learners/protocol_sha256. Mỗi role manifest16keys, gồm actual `ResearchProvenance` và identity. Sau restart có thể reconstruct bằng constructor thật, so full plan manifest và audit lại observable shard mà không đọc oracle hoặc dựa vào objects chưa persist. Không dùng `object.__new__`. Proposal source trước sửa SHA `75d48e5391ae04e2ea9d3c4404c5392d22c388d1ab232aaa844942b51ea2219f` giữ trong prep; đây là static design correction trước test, không fabricated RED.

Raw role recipe SHA gồm profile metadata nên có thể khác giữa train/selection/calibration. Writer giữ composite này trong provenance/raw receipts và dùng normalized recipe chung chỉ gồm version/policy/events/clock; không ép ba role profile hashes bằng nhau. Raw file SHA bank/plan/JSONL tách khỏi semantic domain/plan/provenance identities.

## Kiểm và ghi trước DONE

Trước mkdir: reconstruct typed plan/bank/provenance/limits; kiểm current source/protocol, nguồn trước=sau của collection receipts, bank/domain/G_env/environment semantics/policy/normalized recipe đồng nhất, role/seed assignments, full learner population, timestamps/global source-row namespaces/counters và observable↔oracle query/outcome alignment. Audit lại role; mỗi role phải đủ84reference coverage. Coverage≥1observed learner/item **không** chứng minh đủ diversity, temperature support hay confidence20learners/edge. Không tự collect bổ sung khi thiếu coverage.

Tất cả JSON bytes được serialize/seal và kiểm per-file/total/oracle byte caps trước mkdir; nguồn và cooperative wall/RSS/freeRAM được kiểm lại. Input nested metadata thay sau sealing không đổi bytes sắp publish. Giới hạn phải do caller khai báo, không có default first-corpus counts hoặc phương pháp persona/horizon. Nếu buffer không đủ memory/byte caps thì STOP trước ghi; không mở streaming framework hoặc tự nâng cap.

Ghi exclusive vào một directory mới, flush/fsync và readback SHA/size của9inputs và oracle sidecars/raw collector receipts/publication inventory. Recheck nguồn, tài nguyên và file population rồi ghi `DONE.json` **cuối cùng**: đúng4keys schema_version/status/corpus_sha256/files_sha256, với đúng9model-input hashes. Oracle lưu riêng trong oracle/; guard không list/open/hash oracle. DONE xác nhận logical publication, không filesystem transaction hoặc power-loss/directory durability guarantee.

Failure giữa write giữ owned partial, cố ghi failure.json và trả exception receipt; không rollback/delete/auto retry. Receipt phân biệt write-body returns với đường dẫn còn partial/unverified. Nếu lỗi sau DONE, giữ cả DONE và failure; guard phải từ chối trạng thái đó. Không suy execution authority từ marker; vẫn cần guard, actual schema re-audit trước model allocation và authorization riêng.

## Bằng chứng thực tế

Chỉ một lượt test `trial01`: **31PASS/0failure/error/skip**, console4,19s; controller **5,014471300004516s≤30s cumulative**. Source/schema13files trước=sau; không có failure trial để giấu hoặc RED giả. Fixture dựng10development learners×84events (8/1/1) và1final metadata identity; **0actual collector/teacher/model/optimizer/remote calls**, không final events, không project corpus publication. Fixture source/protocol/world bindings là giả lập rõ ràng, không source authority của corpus thực.

Các kiểm gồm: schema/DONE9hashes; full public-only restart→typed plan/provenance→actual auditor; actual guard `_corpus` đọc tmpFS và trap mọi oracle open; composite profile recipe khác nhau được nhận đúng; fixedROOT/no arbitrary export; existing/partial/protected/symlink paths; graph/recipe/bank/source/seed/clock/rows/outcome/coverage drift; forced oracle flag/cap mutation; file/total/oracle byte caps trước mkdir; fs readback corruption; source drift trước DONE; caller mutation sau seal;37bytes mid-file partial giữ nguyên, noDONE+failure; post-DONE failure giữ marker nhưng guard từ chối.

Integration chỉ dùng metadata reader `_corpus` với synthetic spec/source-build bindings; **không gọi native preflight, actual runtime/Gate validators hoặc authorization**. Tested guard source SHA `72f5a1e981b63c3edf6ff51013a80c9b5680abe18f98d03e190da0d2ed675e5a`; writer không sửa guard/native/config/authorization. Input JSONL vẫn phải được parse/audit ở execution layer trước lazy model import.

Command thật:

```powershell
.venv\Scripts\python.exe artifacts/akt/local-tests/simulator-corpus-publisher-20261108-01/run_pure.py trial01
```

Logs/XML/receipt và13snapshots nằm trong `artifacts/akt/local-tests/simulator-corpus-publisher-20261108-01/trial01/`; `final-verification.json` đối chiếu XML và SHA. Source writer SHA `6305e6e28be643d1b427a6ab5d38a6c1016f17c4eab9f4ea0d2dc84052d9ff77`; test SHA `3f890563ee346b3196a1ee41fb1ba10cc47ad9bb5c1a4c07f88a2d5432d16fd0`; raw run receipt SHA `30b975c94d8bac16b6335d1f47cec943cc760ea77af230049c9c9d14e32387b0`. Nguồn và tests freeze sau run này, trừ blocking review finding có receipt mới.

## Acceptance còn thiếu trước dữ liệu thật

Root vẫn phải freeze exact corpus allocation/profiles/clock/policy/caps/source version, thực hiện actual collect theo role và review actual provenance/coverage; staged model pipeline phải consume đầy đủ guard/re-audit. Native Gate/kit/runtime phải bao phủ source population mới. Publisher không chứng minh corpus diversity, causal identification, calibrated/fitted model, research training readiness hoặc hoàn tất RQ. Không thay old corpus/protected artifacts, không sửa shared indices/state/Git trong tiểu tác vụ này.
