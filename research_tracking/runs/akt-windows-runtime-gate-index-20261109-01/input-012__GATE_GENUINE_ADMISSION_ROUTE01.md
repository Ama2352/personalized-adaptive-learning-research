# Đường admission bằng Gate native đã accepted

Rà source ngày09/11/2026. Điều kiện đầu vào là một lượt Gate mới có native report PASS và outer ACCEPTED, nguồn/lock/runtime/JUnit identities còn nguyên. Lượt Gate04 bị từ chối được giữ theo kết quả riêng. Kết quả Gate05 sẽ do ROOT chốt từ receipt thật.

## Đường ngắn nhất hiện được public API hỗ trợ

Tạo **một index mới, exclusive và bất biến trong `artifacts/akt/preflight/`**, trỏ đúng report/log của lượt native đã được ROOT chấp nhận. Sau khi public reader và runtime preflight kiểm tra thành công, bind đường dẫn và SHA của index đó vào `ResearchRuntimeEvidence`. Guard main hiện có nhận index theo tham số. Tên `gate2-current.json` là default của public reader, còn `gate_pointer` của main guard chỉ yêu cầu parent đúng preflight và đường dẫn vật lý hợp lệ.

Native `refresh_gate2.py` dòng305–307 định nghĩa index năm trường dưới đây. Các SHA phải lấy từ raw actual files của lượt accepted. JSON bên dưới là mô tả schema để triển khai, các chuỗi góc nhọn chờ ROOT cung cấp actual identities.

```json
{
  "schema_version": 1,
  "evidence_file": "<actual native report basename gate2-*.json>",
  "evidence_sha256": "<actual unchanged report SHA256>",
  "test_log_file": "<actual native merged log basename gate2-tests-*.log>",
  "test_log_sha256": "<actual unchanged merged log SHA256>"
}
```

Tên index đề xuất là `gate2-reference-win-current-gate-20261109-05.json`. Publisher metadata phải kiểm tra tên chưa tồn tại và giữ inventory SHA trước/sau cho report/log/JUnit/outer/packet/current sources/lock/runtime. Index là bản ghi dẫn chiếu bằng chứng thật theo format native. Receipt publisher ghi provenance của index và exact outer acceptance đã review.

## Các bước ROOT có thể review để triển khai

1. Chốt actual outer terminal ACCEPTED, RC0, Job0, resource/time accepted và expected-vs-executed JUnit identities. Hash lại report/log/JUnit và các source/lock/runtime bindings. Đây là điều kiện admission đối với index của lượt mới.
2. Ghi bytes index một lần bằng exclusive create trong preflight. Giữ raw bytes và SHA của index vào output vận hành. Nếu validation thất bại, giữ index như pending/rejected metadata cùng failure receipt và dừng trước khi tạo execution authorization.
3. Gọi public `authorization.preflight(config, project_root=ROOT, runtime_report_path=<actual runtime>, lock_file=<actual lock>)` và `authorization.require_gate2_evidence(config, project_root=ROOT, gate2_report=<new immutable index>, lock_file=<actual lock>)` bằng cấu hình/source context đã review. Chỉ nhận output nếu runtime/source/current build/lock khớp actual Gate. Index/report/log và source maps được hash lại sau reader.
4. Dùng typed `ResearchRuntimeEvidence` tám trường hiện có. `gate_pointer` là relative POSIX của index mới, `gate_pointer_sha256` là SHA raw index. Hai trường `gate_report_sha256`/`gate_log_sha256` lấy từ actual report/log và phải trùng output public reader. Bốn trường runtime/lock dùng actual paths và SHA tương ứng.
5. Actual main driver tiếp tục qua public `require_main_selected_authorization`. Closed authorization, config/spec/source/public corpus/phase/caps vẫn được kiểm tra tại đây. Index chỉ cung cấp software-evidence identity trong chuỗi admission.

Publisher có thể là controller metadata nhỏ trong prep, dùng lại safe-path/exclusive-write/hash pattern đã review. Consumer có sẵn hỗ trợ đường này. Không cần sửa production API để thêm chế độ publish-only hoặc chạy lại `refresh()` chỉ để đổi index. Sau khi ROOT chấp nhận đường này, bước tiếp theo là source-only publisher có exact actual file pins.

## Điều kiện đường dẫn và hashes trong source

| Source | Dòng | Hợp đồng liên quan | SHA256 tại lần đọc |
|---|---|---|---|
| `src/knowledge_tracing/akt/authorization.py` |126–175|Reader nhận `gate2_report` bất kỳ. Schema1, report/log basename cùng parent, SHA raw files, finite elapsed, PASS, source commit, lock, exact current build map, suite và positive count0FES|`bd6be914e3b5049927ba6358ee4872097a46469fede9ad1b71ee63df951ac7f0`|
| `src/knowledge_tracing/akt/research_execution.py` |52–62|Relative POSIX path, physical root, từng component từ chối symlink/junction|`5ea3d7283f6d8da6eab712d4e4fedb48cd41717f99cd3ae51fb7b8651b16c7b6`|
| Cùng source |128–142|`ResearchRuntimeEvidence` giữ runtime/lock/index paths và hashes, report/log hashes|Cùng SHA ở trên|
| `src/knowledge_tracing/akt/research_main_execution.py` |117–134|Index và runtime parent phải là `artifacts/akt/preflight`; hash lại từng file, genuine native preflight/reader và exact evidence receipts|`902018762fde6433a9bd9e33ce770df0057f6b0623327b8ff6b798e1faf4d881`|
| Cùng source |337–340|Public `require_main_selected_authorization` kiểm tra closed authorization và actual metadata|Cùng SHA ở trên|
| `scripts/akt/refresh_gate2.py` |288–331|Native optional publication tạo năm trường, public reader kiểm tra temp index trước atomic replace, runtime budget và rollback khi timeout|`8689c5b4737f4eae00459f4a3bc85c22206f58974274304fa4411e36f9acc055`|

Public reader có default currentpointer nhưng việc truyền path rõ ràng ở dòng126–127 và mainguard129 là cơ chế có sẵn. Guard main không bắt basename index phải là currentpointer. Truyền raw native report thay index sẽ thiếu `evidence_file`/`test_log_file` và bị reader từ chối.

## Khi cần cập nhật default currentpointer

`scripts/akt/refresh_gate2.py` có `--publish-current` nhưng gọi `refresh()` và chạy lại suite. Repository hiện chỉ có script này trong `scripts/` cho Gate publication. Prep đã có `promote_current_gate03_pointer01.py`, SHA720df7aa6169e3178117ed08cfbbd4db86184d18c745ff1d5a875f31bfa43f36. Đây là controller lịch sử đã ghim report03/1418/source154 và oldpointer7ecd. Nó cho thấy pattern public reader validation, beforebytes, optimistic comparison, atomic rename, conditional rollback và postreader. Một revision mới cần actual Gate mới và oldpointer hiện hành được ROOT review, rồi mới được dùng.

Currentpointer được đọc ở lần audit này có SHA9e768aadcf084482a2eeb9be814fc399100dd1a507eaa89afbbae87100365cd6, trỏ Gate03 lịch sử154. Nếu ROOT chọn global promotion sau này, trước mutation phải giữ exact bytes/SHA này và kiểm tra lại ngay trước atomic replace. So sánh rồi rename cần sole-writer window, chưa phải atomic cross-process CAS. Rollback chỉ có thể thay lại khi pointer còn đúng bytes của candidate do chính lượt đó vừa ghi. Đường immutable explicit index ở trên tránh nhu cầu đổi default pointer cho một main-driver packet.

Genuine reader vẫn có thể dừng admission khi source đổi sau Gate, lock khác, report/log hashes khác, elapsed sai, runtime/prefix/origins sai hoặc process Git profile không còn đúng. Các điều kiện này cần xử lý bằng bằng chứng thực của stage tương ứng. Tại thời điểm lập kế hoạch này, actual accepted Gate05 và index mới chờ ROOT xác nhận.
