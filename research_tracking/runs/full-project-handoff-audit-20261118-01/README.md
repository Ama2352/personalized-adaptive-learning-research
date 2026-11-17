# Rà toàn bộ project để bàn giao phần KLTN còn lại · 18/11/2026

## Kết luận

Phương án bàn giao là chuyển source/hồ sơ nghiên cứu, một bộ đầu vào chuẩn và các model/output đã nghiệm thu. Hai thư mục AKT lớn được lấy theo allowlist. Một số file trong đó là đầu vào cần dùng, nhiều phần khác là snapshot lặp, cache tăng tốc hoặc lịch sử đã có bản Drive.

**Bộ đầu ra training đã bàn giao trước đây chưa phải bộ tiếp quản toàn project có thể chạy ngay.** Còn cần chuyển source snapshot đầy đủ, các đầu vào bên dưới và nghiệm thu khôi phục trên máy người nhận. Repo hiện chưa cấu hình remote origin, nên hướng dẫn clone từ remote hiện chưa đủ.

## Đã kiểm những gì

- Quét metadata 336,044 file đọc được, khoảng119.84GB theo đường dẫn. `.pytest_cache` trả PermissionError. Vùng private chỉ đo dung lượng, giữ riêng nội dung.
- Hai vùng AKT đo được `artifacts/akt` 59.94GiB và `experiments/akt` 41.41GiB. FileID trong môi trường kiểm trả0 nên chưa tính lại dung lượng vật lý/hardlink. Tổng folder có thể cộng lặp các hardlink.
- Hash mới toàn allowlist đầu vào 611,790,510byte và CSV gốc 2,668,566,436byte; SHA CSV gốc khớp provenance preprocessing.
- Catalog21.604bản trùng/55,784,079,663byte vẫn khớp source/keeper/size/mtime. Catalog giữ SHA kiểm từ16/11; lượt này chưa hash lại toàn55,78GB.
- Đọc model SUPPORT, source snapshot lồng ZIP, bảy Grade10 MODEL_INDEX, các manifest corpus và source loader. Upstream AKT đúng commit01b7e8d7d7c862cabc9467108e3e7f2555653a88, checkout sạch khi kiểm với safe.directory riêng cho lệnh. Lượt đầu bị Git chặn ownership; không đổi global config.

## Người tiếp tục cần nhận

| Nhóm | Thành phần | Vai trò và hiện trạng |
|---|---|---|
| Source hiện hành | src, scripts, tests, third_party, root locks/AGENTS, notebooks đã rà | Cần source snapshot đầy đủ hoặc Git bundle. Gói SOURCE_PROTOCOLS cũ là tập con; frozen source theo run giữ cho tái lập đúng phiên bản |
| Hồ sơ nghiên cứu/viết | docs, research_tracking, paper1, paper2, ref-papers | Khoảng0,27GB theo metadata, giữ logs, CSV, figure, luận điểm, quyết định và backlog; phân biệt báo cáo hiện hành với lịch sử |
| Đầu vào chuẩn | Allowlist bên dưới | Tổng khoảng0,612GB; trong đó Method24 khoảng69,83MB vừa có gói Drive riêng, khoảng541,96MB còn cần chuyển/restore |
| Model/kết quả đã có | Junyi selected/refit/calibration/outer, Grade10 selected, BKT/GAM và engineering SAKT/GKT | Có trên các thư mục Drive đã nghiệm thu của đợt training-handoff17/11; dùng index và helper nối ZIPpart |
| Simulator traces | experiments/simulator/results | Khoảng18,4MB, cần chuyển để tiếp tục phân tích và trích dẫn log gốc; gói evidence nhỏ cũ chỉ chứa một phần tổng hợp |
| Grade10 selected support | terminal/claim, prediction/target/coverage, logs từng epoch, metadata | Đã phát hiện và bổ sung hồ sơ5run còn nằm trong archive local. A0/A1expert có archive lịch sử Drive riêng |
| Tài khoản/môi trường | Modal/Drive và Python/CUDA | Người nhận tự đăng nhập tài khoản được cấp, dựng .venv/AKT upstream từ lock/provenance; keep secrets ngoài source |

### Đầu vào chuẩn, dung lượng đã đo và hash mới

| Nhóm | Đường dẫn | Dung lượng byte |
|---|---|---:|
|CANONICAL_JUNYI_AND_SPLITS|artifacts/bkt_baseline/derived/canonical + derived manifest/duplicate_lineage + splits|250,227,593|
|GAM_SOURCE_MAP|artifacts/gam_kt/derived/source_map|281,461,663|
|GRADE10_MAIN_CORPUS|artifacts/simulator/corpora/grade10-development-lifecycle01-20261108|6,985,213|
|ROLES_AND_REFIT_INDEX|artifacts/akt/junyi-roles/outer4-research-v1-20261112-01 + refit-inputs|2,922,486|
|EXERCISE_AND_GRAPH_SOURCE|dataset/junyi_Exercise_table.csv + hai relationship_annotation CSV|360,557|
|GRADE10_METHOD24_AND_CONDITIONS|32file Method24/condition/provenance trong artifacts/akt/local-tests theo allowlistV2|69,832,998|

CSV `dataset/junyi_ProblemLog_original.csv` nặng2,669GB nên giữ một bản cho tái lập preprocessing từ gốc. Có canonical/splits đúng SHA thì người nhận có thể tiếp tục phần còn lại trước khi cần chạy preprocessing lại. Các nhãn role/Test trong dữ liệu được quản lý theo frozen assignments; thông tin oracle Grade10 giữ riêng cho simulator/diagnosis.

### Những phần AKT lớn có thể chọn theo nhu cầu

| Vùng | Vai trò | Cách bàn giao |
|---|---|---|
| staged khoảng41,52GB | Nhiều bản input/cache theo từng tranche | Giữ một bản input chuẩn và lineage; chọn keeper thay cho chuyển mọi bản lặp |
| window-cache khoảng4,22GB | Các cache khác nhau của train/selection/refit | Bộ train80 hiện dùng khoảng1,332GB; selection staged02 khoảng0,293GB. Chuyển đúng hai bộ này nếu tiếp tục lượt dùng cùng cache, hoặc dựng lại và kiểm SHA |
| graph-context-cache khoảng1,34GB | Graph feature cache | Tái dựng hoặc chuyển bộ đúng variant/window/phase được request dùng |
| confidence khoảng4,17GB | Confidence, OOF/fit ledger và spool | Confidence/OOF đã có Drive; SQLite rows3,477GB hữu ích khi kiểm/refit surrogate. Khi dùng confidence cố định đã nghiệm thu, consumer đọc confidence artifact |
| results các lượt fit/refit | Checkpoint nhiều epoch, raw exports và logs | Dùng model gọn + các archive Drive đúngrun. Chỉ lấy checkpoint trung gian khi câu hỏi audit/resume cần đến |
| drive-offload-duplicates khoảng10,87GB | Nội dung đại diện cho các đường dẫn trùng | Trạng thái upload thủ công cần nghiệm thu riêng. Bản trùng cần keeper đúng SHA khi thu gọn |
| local-tests/runtime/tmp/Colab bridge | Nghiên cứu thật lẫn fixture, runtime và bằng chứng kỹ thuật | Method24/graph Grade10 khoảng69,83MB trong local-tests là phụ thuộc thật; lấy32file theo allowlist, rồi rà các fixture riêng |

Các cache này có ý nghĩa tiết kiệm thời gian; tính cần thiết phụ thuộc run tiếp theo. Giữ file gốc trong lượt audit này. Danh mục hiện tại phục vụ bàn giao, chưa cấp quyền xóa.

## Bổ sung Grade10 đã thực hiện

Năm archive local tổng495,489,664byte có những member cần cho bước chọn hệ thống. Đã đọc/hash archive trước–sau và gom170member nhỏ thành ZIP1,671,389byte, đọc lại nội dung Drive khớp SHA. [Tải Grade10 selection support](https://drive.google.com/file/d/1w3Tyw-u1Pj4DPRcR8q4aTAW_LGzZaTzB/view?usp=drivesdk).

Model best của bảy điều kiện vẫn dùng bản Grade10 export đã có Drive. GRADE10_SUPPORT01.json ánh xạ đường dẫn checkpoint gốc sang model gọn với SHA. Khi consumer yêu cầu layout cũ, phục hồi best checkpoint đúng đường dẫn sau kiểm SHA và ghi relocation. Intermediate checkpoint vẫn ở archive gốc hoặc lịch sử Drive, chọn tải theo nhu cầu audit. Gói bổ sung chưa chứng nhận cold restore toàn lifecycle trên máy mới.

Phát hiện bổ sung sau truy ngược binding: Method24/learned graph Grade10 thật đang nằm dưới tên local-tests. Đã bổ sung32file khoảng69,83MB gồm OOF, fit ledger, graph, condition, receipts và hai source producer vào REQUIRED_INPUTS02.json. Hash của20artifact mà checkpoint tham chiếu và hai source producer khớp pin lịch sử. InventoryV1 được giữ để thể hiện lý do sửa phạm vi. Bản Drive mới được định vị tại METHOD24_DRIVE02.json.

## Tiêu chí đủ điều kiện chuyển giao công việc

1. Source/hồ sơ nghiên cứu đủ và nhận diện được snapshot theo từng run; phần đang sửa hoặc chưa commit được review riêng.
2. Restore được canonical, splits, roles, corpus/bank/graph và kiểm đủ SHA của allowlist. Dùng đúng model Junyi/Grade10 và đúng source snapshot, giữ split và giới hạn thông tin.
3. Kiểm API/nhập thư viện và kiểm tổng hợp trong .venv mới. AKT upstream cần Git checkout sạch và origin đúng theo verify_upstream; ba file Python/README/LICENSE rời chưa đủ cho guard này.
4. Nạp thử một model qua entrypoint phù hợp, kiểm binding/coverage, thử consumer selected/refit metadata mà chưa cập nhật trọng số hoặc chọn lại cấu hình. Khôi phục layout bằng copy/relocation có kiểm SHA.
5. Truy cập được thư mục gốc Drive và các thư mục model/evidence đang được chỉ mục tham chiếu; xác thực bằng tài khoản người nhận.
6. Người nhận đọc backlog hiện hành và các giới hạn kết luận. Ưu tiên quyết định/vòng kín và đối chứng cốt lõi; mỗi lượt bổ sung có câu hỏi, input, output và budget cụ thể.

**Trạng thái hiện tại là đầu ra đã sao lưu, bàn giao toàn phần còn điều kiện về source/input transfer và cold restore.** Số liệu âm hoặc bất định tiếp tục được giữ. Lượt kiểm này dùng metadata/hash và truyền hồ sơ đã có, chưa chạy model training, GPU hoặc mở lại Test để chọn cấu hình.

Chi tiết theo file trong REQUIRED_INPUTS02.json, Grade10 support/relocation trong GRADE10_SUPPORT01.json, phân loại thư mục trong FOLDER_DECISIONS01.csv, giới hạn scan trong REPOSITORY_INVENTORY01.json. FILES.jsonl lớn là inventory metadata local theo đường dẫn đã ghi trong scan.

[Tải bộ Method24/graph Grade10 đã nghiệm thu trên Drive](https://drive.google.com/file/d/1_K_xuG534vsfjPUgZ4g5Rl_3FV6mU8lj/view?usp=drivesdk) · ZIP13,059,198byte.
