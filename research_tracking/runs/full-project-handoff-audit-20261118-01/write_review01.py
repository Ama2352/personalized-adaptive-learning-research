"""Tổng hợp quyết định bàn giao theo vai trò, từ metadata và input SHA đã kiểm."""
from pathlib import Path
import csv
import json

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent


def main():
    scan=json.loads((B/'REPOSITORY_INVENTORY01.json').read_text(encoding='utf-8'))
    inputs=json.loads((B/'REQUIRED_INPUTS02.json').read_text(encoding='utf-8'))
    duplicates=json.loads((B/'DUPLICATE_REVIEW01.json').read_text(encoding='utf-8'))
    support=json.loads((B/'GRADE10_SUPPORT01.json').read_text(encoding='utf-8'))
    receipt=json.loads((B/'GRADE10_SUPPORT_DRIVE01.json').read_text(encoding='utf-8'))
    method24=json.loads((B/'METHOD24_DRIVE02.json').read_text(encoding='utf-8'))
    choices={
        '[root files]':('SOURCE','AGENTS, README, pyproject, locks và cấu hình Git','Chuyển source snapshot hiện hành'),
        '_context':('CONTEXT','Protocol BKT ban đầu','Giữ cùng source, ưu tiên Protocol21/Recipe26 cho phạm vi toàn luận văn'),
        'src':('SOURCE','Cài đặt KT, simulator, demo','Chuyển source hiện hành'),
        'scripts':('SOURCE','Entrypoints preprocessing/training/calibration/evaluation','Chuyển source hiện hành'),
        'tests':('SOURCE','Kiểm hồi quy và semantics','Chuyển source hiện hành'),
        'docs':('RESEARCH','Đề cương, protocol, provenance, kế hoạch','Chuyển cùng source; giữ cả hồ sơ lịch sử'),
        'research_tracking':('RESEARCH','Bằng chứng RQ, figure, báo cáo và trạng thái','Chuyển toàn hồ sơ nghiên cứu đã rà; phần local chưa commit cần review'),
        'experiments':('OUTPUT','Cấu hình và kết quả theo model','Tái dùng model/output Drive; bổ sung trace simulator và Grade10 support'),
        'dataset':('INPUT','CSV gốc và metadata graph','Raw2,67GB giữ cho tái lập từ gốc; metadata nhỏ nằm trong allowlist'),
        'artifacts':('MIXED','Canonical, splits, corpus, graph và cache/runtime','Chuyển allowlist đầu vào; các nhóm cache chọn theo nhu cầu'),
        'paper1':('RESEARCH','PDF chính thức và notebook tiền kết quả','Đã có trong gói legacy; giữ PDF làm chuẩn'),
        'paper2':('RESEARCH','Source và frozen results Paper2','Đã có trong gói legacy; giữ cấu trúc package'),
        'ref-papers':('WRITING','Tài liệu tham khảo','Chuyển khi bàn giao viết luận văn'),
        'notebooks':('SOURCE','Notebook kiểm kỹ thuật/calibration','Giữ source sau rà outputs/quyền truy cập'),
        'third_party':('SOURCE','pyBKT vendored và license/patch','Chuyển cùng source, giữ provenance'),
        '.git':('SOURCE_HISTORY','Lịch sử source; chưa cấu hình remote origin','Chuẩn bị Git bundle hoặc source snapshot đầy đủ; giữ frozen snapshots theo run'),
        '.venv':('REBUILD_ENV','Môi trường Python local','Người nhận dựng môi trường từ lock'),
        'venv':('REBUILD_ENV','Môi trường cũ','Giữ local; người nhận dùng .venv mới'),
        '.wsl':('REBUILD_ENV','Ubuntu/WSL lịch sử BKT','Dựng lại theo runbook khi cần tái lập backend BKT'),
        '.superpowers':('OPERATIONAL','Ghi chú điều phối agent','Tham khảo khi cần; kế hoạch nghiên cứu nằm ở docs/tracking'),
        '.playwright-mcp':('OPERATIONAL','Ảnh/log kiểm giao diện','Giữ figure bằng chứng đã gom theo run; runtime dựng lại'),
        '.pytest_cache':('REBUILD_CACHE','Cache pytest không đọc được trong lượt này','Dựng lại bằng kiểm thử; ghi rõ giới hạn truy cập'),
    }
    rows=[]
    for name in sorted(set(choices)|{k for k in scan['groups'] if '/' not in k}):
        role,purpose,action=choices.get(name,('REVIEW','Chưa phân loại','Giữ và rà trước bàn giao'))
        stats=scan['groups'].get(name,dict(bytes=None,files=None))
        rows.append(dict(path=name,role=role,bytes=stats['bytes'],files=stats['files'],purpose=purpose,action=action))
    akt_roles={
        'staged':('DUPLICATE_SNAPSHOTS','Các snapshot input/cache lặp theo tranche','Chuyển một bản input theo allowlist và giữ manifest; rà lại keeper trước dọn'),
        'window-cache':('OPTIONAL_CACHE','Cửa sổ đã mã hóa cho train/refit/selection','Chọn một bộ đúng manifest nếu cần tiết kiệm CPU chuẩn bị'),
        'graph-context-cache':('OPTIONAL_CACHE','Graph context định trước, phụ thuộc window/condition','Tái dựng từ graph/encoding/window đúng SHA hoặc chuyển đúng bộ sẽ dùng'),
        'confidence':('CONFIDENCE_AND_CACHE','confidence cuối, OOF/fit ledger và SQLite spool','Kết quả confidence/OOF đã có Drive; SQLite3,48GB là lựa chọn tăng tốc/audit sâu'),
        'junyi-cohorts':('OPTIONAL_CACHE','Canonical con đã ghép/sắp cho từng phase','Bộ selected-full03 khoảng140,76MB hữu ích, có thể dựng từ canonical/splits'),
        'junyi-roles':('REQUIRED_INPUT','Phân vai người học outerfold4','Nằm trong allowlist bắt buộc'),
        'refit-inputs':('REQUIRED_METADATA','Index selected-fit đóng epoch plan','Nằm trong allowlist bắt buộc'),
        'local-calibration':('DERIVED_AND_OUTPUT','Cache/calibration/outer tạm, frozen source và output','Dùng output/source đã kiểm Drive; đầu vào chuẩn trong allowlist'),
        'dependencies':('REBUILD_DEPENDENCY','AKT upstream checkout và bridge tools','Clone đúng commit; verify_upstream cần Git checkout sạch và origin đúng'),
        'private':('ACCOUNT_PRIVATE','Token, state upload và runtime bridge cá nhân','Người nhận tự đăng nhập tài khoản được cấp; giữ riêng vùng này'),
        'local-tests':('RESEARCH_INPUT_AND_TEST_FIXTURES','Có Method24/graph Grade10 thật lẫn fixture và logs','Giữ32file Method24/condition theo allowlist; fixture tổng hợp rà riêng'),
        'test-temp':('REBUILD_TEST_FIXTURES','Dữ liệu nhị phân pytest','Dựng lại theo tests; chưa đánh dấu xóa qua audit này'),
        'runtime':('MIXED_RUNTIME','Helper, kết quả kiểm và môi trường thử','Chọn source/log được run tham chiếu; runtime/binary fixture dựng lại'),
        'colab':('COLD_RECOVERY','Gói recovery/source và kết quả môi trường cũ','Dùng bản Drive đã nghiệm thu khi tái lập lượt cũ'),
        'staged-archives':('COLD_INPUT_ARCHIVE','Các gói input lặp phục vụ chuyển cloud','Chọn một bản hoặc dựng từ đầu vào chuẩn'),
        'modal':('OPERATIONAL','Source packets, requests và log Modal','Giữ request/log/source được run chính tham chiếu'),
        'pip-cache':('REBUILD_CACHE','Gói cài dependency','Dựng lại từ lock'),
        'tmp':('REVIEW_TEMP','Tạm thời và fixture còn lẫn','Giữ metadata; rà theo file trước mọi thao tác dọn'),
    }
    for path,stats in scan['groups'].items():
        if path.startswith('artifacts/akt/') and path.count('/')==2:
            name=path.rsplit('/',1)[1]
            role,purpose,action=akt_roles.get(name,('REBUILD_TEST_OR_REVIEW','Các lượt kiểm kỹ thuật cũ','Giữ evidence theo run; rà riêng khi muốn dọn'))
            rows.append(dict(path=path,role=role,bytes=stats['bytes'],files=stats['files'],purpose=purpose,action=action))
        if path.startswith('experiments/akt/results/') and path.count('/')==3:
            name=path.rsplit('/',1)[1]
            role,purpose,action=('RUN_HISTORY','Output theo run, có thể gồm checkpoint trung gian','Tra run trong Drive receipts và giữ phần cần audit; model hiện hành dùng export đã kiểm')
            if name.startswith('model-export-'):
                role,purpose,action=('MODEL_EXPORT_OR_RECOVERY','Export model hiện hành hoặc recovery lịch sử','Tra MODEL_INDEX/phase; dùng current selected/refit, giữ recovery theo lịch sử')
            if name.startswith('modal-main60-'):
                role,purpose,action=('GRADE10_SELECTED_HISTORY','Output selected-fit Grade10','Best model có Drive; support5run vừa bổ sung, A0/A1expert lấy archive lịch sử')
            if name.startswith('drive-offload-duplicates'):
                role,purpose,action=('DUPLICATE_OFFLOAD_PENDING_REVIEW','Nội dung đại diện nhiều bản trùng','Giữ trạng thái upload thủ công riêng; kiểm remote trước thu gọn')
            if name.startswith('artifact-offload'):
                role,purpose,action=('RETENTION_AND_ARCHIVE_INDEX','Catalog SHA/keeper và ZIP đã có Drive','Người nhận lấy catalog từ gói05/06; giữ lineage nếu thu gọn')
            rows.append(dict(path=path,role=role,bytes=stats['bytes'],files=stats['files'],purpose=purpose,action=action))
    with (B/'FOLDER_DECISIONS01.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['path','role','bytes','files','purpose','action']);writer.writeheader();writer.writerows(rows)
    local_archives=[r for r in support['models'] if r['archive_status'].startswith('LOCAL_')]
    md=f'''# Rà toàn bộ project để bàn giao phần KLTN còn lại · 18/11/2026

## Kết luận

Phương án bàn giao là chuyển source/hồ sơ nghiên cứu, một bộ đầu vào chuẩn và các model/output đã nghiệm thu. Hai thư mục AKT lớn được lấy theo allowlist. Một số file trong đó là đầu vào cần dùng, nhiều phần khác là snapshot lặp, cache tăng tốc hoặc lịch sử đã có bản Drive.

**Bộ đầu ra training đã bàn giao trước đây chưa phải bộ tiếp quản toàn project có thể chạy ngay.** Còn cần chuyển source snapshot đầy đủ, các đầu vào bên dưới và nghiệm thu khôi phục trên máy người nhận. Repo hiện chưa cấu hình remote origin, nên hướng dẫn clone từ remote hiện chưa đủ.

## Đã kiểm những gì

- Quét metadata {scan['scanned_files']:,} file đọc được, khoảng{sum(v['bytes'] for k,v in scan['groups'].items() if '/' not in k)/1e9:.2f}GB theo đường dẫn. `.pytest_cache` trả PermissionError. Vùng private chỉ đo dung lượng, giữ riêng nội dung.
- Hai vùng AKT đo được `artifacts/akt` {scan['groups']['artifacts/akt']['bytes']/1024**3:.2f}GiB và `experiments/akt` {scan['groups']['experiments/akt']['bytes']/1024**3:.2f}GiB. FileID trong môi trường kiểm trả0 nên chưa tính lại dung lượng vật lý/hardlink. Tổng folder có thể cộng lặp các hardlink.
- Hash mới toàn allowlist đầu vào {inputs['total_bytes']:,}byte và CSV gốc {inputs['raw_provenance']['bytes']:,}byte; SHA CSV gốc khớp provenance preprocessing.
- Catalog21.604bản trùng/{duplicates['bytes']['catalog_bytes']:,}byte vẫn khớp source/keeper/size/mtime. Catalog giữ SHA kiểm từ16/11; lượt này chưa hash lại toàn55,78GB.
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
'''
    for group in inputs['groups']:
        prefixes=sorted({row['path'].rsplit('/',1)[0] for row in group['files']})
        label={
            'CANONICAL_JUNYI_AND_SPLITS':'artifacts/bkt_baseline/derived/canonical + derived manifest/duplicate_lineage + splits',
            'GAM_SOURCE_MAP':'artifacts/gam_kt/derived/source_map',
            'GRADE10_MAIN_CORPUS':'artifacts/simulator/corpora/grade10-development-lifecycle01-20261108',
            'ROLES_AND_REFIT_INDEX':'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01 + refit-inputs',
            'EXERCISE_AND_GRAPH_SOURCE':'dataset/junyi_Exercise_table.csv + hai relationship_annotation CSV',
            'GRADE10_METHOD24_AND_CONDITIONS':'32file Method24/condition/provenance trong artifacts/akt/local-tests theo allowlistV2'}[group['name']]
        md+=f"|{group['name']}|{label}|{group['bytes']:,}|\n"
    md+='''
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

'''
    md+=f"Năm archive local tổng{sum(r['bytes'] for r in local_archives):,}byte có những member cần cho bước chọn hệ thống. Đã đọc/hash archive trước–sau và gom170member nhỏ thành ZIP{receipt['bytes']:,}byte, đọc lại nội dung Drive khớp SHA. [Tải Grade10 selection support]({receipt['url']}).\n\n"
    md+='''Model best của bảy điều kiện vẫn dùng bản Grade10 export đã có Drive. GRADE10_SUPPORT01.json ánh xạ đường dẫn checkpoint gốc sang model gọn với SHA. Khi consumer yêu cầu layout cũ, phục hồi best checkpoint đúng đường dẫn sau kiểm SHA và ghi relocation. Intermediate checkpoint vẫn ở archive gốc hoặc lịch sử Drive, chọn tải theo nhu cầu audit. Gói bổ sung chưa chứng nhận cold restore toàn lifecycle trên máy mới.

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
'''
    md+=f"\n[Tải bộ Method24/graph Grade10 đã nghiệm thu trên Drive]({method24['url']}) · ZIP{method24['bytes']:,}byte.\n"
    (B/'README.md').write_text(md,encoding='utf-8')
    state=dict(status='FULL_WORK_HANDOFF_CONDITIONAL_PENDING_SOURCE_INPUT_TRANSFER_AND_COLD_RESTORE',
        as_of='2026-11-18',repository_files_scanned=scan['scanned_files'],input_bytes=inputs['total_bytes'],
        raw_bytes=inputs['raw_provenance']['bytes'],grade10_support_drive=receipt,
        method24_drive=method24,
        next=['Chuyển source snapshot đầy đủ và hồ sơ nghiên cứu','Chuyển/restore541957512byte đầu vào còn lại và dùng gói Method24 đã sao lưu',
              'Chuyển simulator traces và ghi nhận working changes','Kiểm cold restore trong .venv của người nhận'],
        original_files_modified=False,full_training_executed=False,cloud_compute=False,
        limits=scan['limits'],evidence_files=['REPOSITORY_INVENTORY01.json','REQUIRED_INPUTS02.json','DUPLICATE_REVIEW01.json',
            'CODE_AND_LOCAL_WORK01.json','GRADE10_SUPPORT01.json','GRADE10_SUPPORT_DRIVE01.json','FOLDER_DECISIONS01.csv'])
    (B/'STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('FULL_PROJECT_HANDOFF_REVIEW_WRITTEN',len(rows),'folder decisions',flush=True)


if __name__=='__main__':
    main()
