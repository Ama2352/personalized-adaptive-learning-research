# Bàn giao, bố cục repository và phục hồi dữ liệu nặng

## Hai nơi trên Drive

[Bàn giao KLTN](https://drive.google.com/drive/folders/1T6GseWOnUbbj-eXTcWIELAp2hPemGrLQ) chứa source/cấu hình hiện hành, corpus/split/graph chuẩn, model, calibration, dự đoán và kết quả dùng để tiếp tục. Bắt đầu từ BAT_DAU_TAI_DAY_FINAL.md hoặc HTML và MANIFEST_BAN_GIAO_FINAL.json. Hướng dẫn và helper tại gốc được kiểm cùng manifest; thông tin đăng nhập được người nhận tự cấp.

[Lưu trữ lịch sử KLTN](https://drive.google.com/drive/folders/1QoqGGMj6NUW7soLPxSkKDeKknFO_uyw6) là thư mục ngang cấp, giữ lịch sử/audit, snapshot staging, cache và output cũ đã chuyển lạnh. Không cần tải cả kho này để bắt đầu công việc.

Junyi A0–A3 expert đã đủ selection/refit/calibration/outer fold4; Grade10 và các comparator còn việc theo báo cáo hiện hành. Lưu trữ đúng và commit source không thay mức bằng chứng hoặc tự hoàn tất baRQ.

## Bố cục local theo vai trò

| Vùng | Vai trò |
|---|---|
| src/, scripts/, tests/, third_party/ | Mã, entrypoint, kiểm thử và dependency vendored |
| docs/, _context/ | Protocol, runbook và ngữ cảnh; docs/operations giữ vận hành bàn giao/lưu trữ |
| research_tracking/reports/ | Phân tích và bảng diễn giải cho luận văn |
| research_tracking/runs/ | Bằng chứng theo run; giữ failure và giới hạn |
| research_tracking/storage/ | Chỉ mục Drive và catalog phục hồi nén |
| experiments/<model>/ | Config/runbook và output theo run; payload lớn có thể đã chuyển lạnh |
| artifacts/<model>/ | Input/cache/dependency theo pipeline; giữ đầu vào chuẩn, phục hồi cache cũ khi cần |
| paper1/, paper2/, ref-papers/ | Nguồn nghiên cứu và tài liệu kế thừa; chuyển qua bộ source Drive trong phạm vi được phép |
| dataset/, .venv/, venv/, .wsl/ | Dữ liệu gốc và môi trường được bảo vệ, không thuộc đợt xóa |

Giữ vị trí pipeline và frozen manifests để không làm mất lineage. Không chuyển source/paper/frozen bundle chỉ để đổi tên thư mục. Các snapshot/cache trùng và thư mục rỗng đã được thu gọn; scripts/storage gom công cụ phục hồi, research_tracking/storage gom locator dùng chung.

## Phục hồi đúng một file cũ

Tra catalog để biết gói cần tải:

```powershell
.\.venv\Scripts\python.exe -B scripts/storage/restore_workspace.py --manifest research_tracking/storage/20261118_STORAGE_INDEX.json.gz --path "artifacts/akt/confidence/full-train80-20261114-02/rows.sqlite"
```

Lệnh chỉ đọc và in fileID/tên/SHA/link Drive. Tải đúng gói hoặc các phần được liệt kê vào một thư mục download. Có thể đặt tên `FILE_ID--TEN_FILE` để tránh các archive cùng tên. Sau đó:

```powershell
.\.venv\Scripts\python.exe -B scripts/storage/restore_workspace.py --manifest research_tracking/storage/20261118_STORAGE_INDEX.json.gz --path "artifacts/akt/confidence/full-train80-20261114-02/rows.sqlite" --downloads D:/Nhan_KLTN/goi --root D:/Nhan_KLTN/thu_phuc_hoi
```

Helper kiểm SHA toàn gói/parts rồi đúng member, giới hạn kích thước đã pin, từ chối đường dẫn thoát root và từ chối ghi đè file khác nội dung. Mặc định không tải hoặc phục hồi hàng loạt. Khi đã kiểm thư mục thử, có thể dùng root của workspace cần phục hồi.

Corpus/model gọn còn local và các asset ready có manifest bàn giao riêng, không mặc định có trong catalog cold. Dependency/runtime của người nhận dựng từ lock và upstream commit theo runbook, không sao chép .venv hoặc credentials của chủ repo.

## Kiểm chứng và giới hạn

[Bundle dọn](../../research_tracking/runs/workspace-cleanup-20261118-01/README.md) giữ inventory trước/sau, SHA, biên nhận Drive và nhật ký gỡ.790đầu vào chuẩn và15model chính được kiểm hash sau dọn. Bộ nguồn/input/model đã có kiểm cold restore; công cụ cold restore mới có kiểm thử và đọc lại một gói thật từ Drive. Điều đó không thay kiểm cài runtime, import và smoke trên máy người nhận.

Một số fixture test cố ý chặn quyền truy cập được giữ và ghi giới hạn, không đổi ACL. Các inventory/log thao tác lớn giữ đầy đủ trên Drive và local nhưng không đưa raw vào Git; Git giữ summary, mã và catalog nén có SHA. Không xóa nguồn chưa có chứng cứ phục hồi, không sửa manifest/model/prediction lịch sử để hợp với bố cục mới.
