# Bổ sung integrity cho notebook báo cáo bằng chứng

Ngày08/11/2026. Bổ sung này cập nhật **builder và working notebook**, không sửa các số liệu, claim, mẫu số hoặc scope nghiên cứu. [Notebook hiện hành](../../notebooks/thesis_evidence_report.ipynb) vẫn là báo cáo chẩn đoán/pilot RQ1–RQ2; không kết quả cuối ba RQ. [Báo cáo v1](thesis_evidence_notebook_20261108.md) và [bundle v1](../runs/thesis-evidence-notebook-20261108-01/manifest.json) giữ nguyên bytes và mô tả snapshot v1. Không dùng kết quả kiểm phần mềm làm hiệu quả mô hình.

## Sửa kiểm SHA trên cùng payload

Builder v1 hash file rồi đọc lại JSON hoặc nạp builder qua `runpy`. Nếu file bị thay giữa hai lần đọc, phần được parse/execute có thể khác bytes vừa kiểm SHA. Đây là lỗ hổng hợp đồng integrity khi có thay đổi đồng thời; không có bằng chứng số liệu v1 đã bị thay hoặc sai.

Builder mới đọc mỗi payload một lần, kiểm SHA và độ dài của chính payload rồi `json.loads(payload)`. Cell bootstrap của notebook đọc byte payload builder, kiểm SHA và `exec(compile(payload,...), namespace)` trên cùng bytes; namespace có `__file__` và `__name__` khác `__main__`, nên không chạy CLI của builder. Giữ nguyên source map28inputs/14claims/104JSONPointers, escaped HTML và kiểm phạm vi đường dẫn trong repository.

Thay working notebook là opt-in qua `--replace-generated-sha256`; chỉ chấp nhận canonical `notebooks/thesis_evidence_report.ipynb` cùng SHA v1 đã review `de3ad54b658ea2e48e95cc1d6637dae48503f2c9d645fb9fc2c4338d116d6089`. Trước ghi, builder xác minh manifest v1 `2100a70da6b8da2547bfeba958187b478a53f5e195e8987b1cdb1f5109eee410` và cả7outputs, lưu backup v1 và inventory bằng exclusive-create, rồi kiểm lại bytes của file đã mở trước khi thay nội dung. Không có flag thì vẫn exclusive-create, không ghi đè. Đây là thay bản sinh ra theo phạm vi được duyệt, không sửa archive lịch sử hoặc cơ chế tự thử lại.

## Kết quả local thực tế

| Lượt | Kiểm/thao tác | Kết quả | Thời gian controller |
|---|---|---|---|
|01|3race canaries trên builder v1|3FAIL,0errors; unittest0.105s|0.488261900s|
|02|3canaries giữ nguyên+9guards/schema/CLI/rerender|12PASS,0errors; unittest0.144s|0.517926500s|
|03|Guarded regeneration, thực thi7cells bằng stdlib|RC0;28inputs/14claims/104pointers|0.315314200s|

Tổng thời gian controller **1.321502600s≤30s** cho cả ba lượt, không reset budget. Logs RED và snapshots nguồn cũ giữ nguyên. Canaries giả lập `read_text` thứhai trả JSON khác sau khi byte payload đã kiểm SHA; canary mã builder chặn đường `runpy` đọc lại và xác minh compiler nhận đúng verified bytes. Không canary nào sửa input/bundle lịch sử. Kiểm guard bao gồm drift SHA/length, nguồn map sai SHA, outside-path, archive output hỏng, flag CLI và canonical-path/SHA sai. Rerender trong kiểm thử cho outputs giống v1.

Sau regenerate, kiểm chỉ đọc xác nhận working notebook có14cells/7code cells với outputs giống hệt v1,7outputs archive v1 vẫn đúng SHA, chỉ working notebook đổi trong lượt03. Source map, báo cáo v1 và manifest v1 giữ nguyên. `replacement-before.json` lưu7output bindings cùng backup trước ghi; `final-verification.json` giữ số liệu và SHA đầy đủ.

Lệnh dùng `.venv` qua controller cộng dồn budget:

```powershell
.venv\Scripts\python.exe artifacts/akt/local-tests/thesis-evidence-notebook-20261108-02/run_integrity.py trial01-red artifacts/akt/local-tests/thesis-evidence-notebook-20261108-02/test_integrity.py
.venv\Scripts\python.exe artifacts/akt/local-tests/thesis-evidence-notebook-20261108-02/run_integrity.py trial02-green artifacts/akt/local-tests/thesis-evidence-notebook-20261108-02/test_validation.py
.venv\Scripts\python.exe artifacts/akt/local-tests/thesis-evidence-notebook-20261108-02/run_integrity.py trial03-regenerate scripts/research/build_thesis_evidence_notebook.py --replace-generated-sha256 de3ad54b658ea2e48e95cc1d6637dae48503f2c9d645fb9fc2c4338d116d6089
```

Builder mới SHA `5f49bb44138087ebd2d783fa6d8bca7d1ec028bcc970ebde2cfd3e0500b94952`; notebook mới SHA `ed1b7cad329d453d535a233ac8effdf4abf7a22d030a011962f9f04486ef090c`. [Bundle bổ sung](../runs/thesis-evidence-notebook-20261108-02/manifest.json) giữ source trước/sau, logs, canaries và copy inventory SHA trước=sau. Manifest `completed` chỉ xác nhận đóng gói, không đổi ba canaries thất bại lịch sử thành PASS.

## Giới hạn

Không kernel Jupyter, nbformat library hoặc visual QA; không cài dependency mới. Notebook vẫn cần kernel có IPython để RunAll trong giao diện notebook; stdlib builder không cần IPython. Không train/model/simulator/Junyi/Holdout/remote, không thêm independent N, CI, p-value hoặc claim nhân quả. Phiên bản này không sửa scientific methodology hoặc kết luận C01–C14. Root quản lý chỉ mục và Git riêng.
