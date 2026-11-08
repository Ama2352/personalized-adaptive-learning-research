# Notebook báo cáo bằng chứng đã lưu

Ngày08/11/2026. [Mở notebook](../../notebooks/thesis_evidence_report.ipynb). Có14cells/7code cells với outputs đã được tính bằng `.venv`; không huấn luyện hoặc chạy simulator/Junyi/Holdout/cloud. Đây là báo cáo chẩn đoán/pilot, chưa bản kết quả cuối của ba RQ.

## Nội dung có thể trình GVHD

1. Sơ đồ thứ tự native Paper2: S→M/R→C/B/keys→A→Pserved→interact/update; không đặt Pserved trước selection hoặc gọi là causal funnel.
2. Bảng RQ1: tổng event-pair P/M/R/A thay đổi và conditional P đổi/A giữ, giữ mẫu số1080/964 cùng đơn vị; preview khác served action.
3. C14: first-break native CID ranking trên common observed prefix; post-hoc/current-source, không edge-only hoặc causal learning benefit.
4. RQ2: retention identity có điều kiện, factorial profile/seed-block pilot và metadata Junyi order-only; không causal ability DiD hoặc causal graph benefit.
5. Bảng C01–C14 và đường dẫn source map/JSON Pointers/SHA để truy vết số liệu.

Các bảng lấy số trực tiếp từ artifact có hash, không nhập tay và không mở dữ liệu gốc. Builder kiểm **28inputs,14claims,104pointers** với source map SHA `fbfa712e1eaf04f05fee5a33c577393478ba7f5a766af2a836d4598a2ed73bbc`. Mỗi số có scope/denominator và phần giới hạn. Không đưa số PASS phần mềm thành bằng chứng hiệu quả mô hình.

## Cách tạo và kiểm

[`build_thesis_evidence_notebook.py`](../../scripts/research/build_thesis_evidence_notebook.py) chỉ dùng stdlib, từ chối source map/report/input/manifest/pointer sai hash hoặc giá trị. Ghi notebook bằng exclusive-create; không ghi đè bundle lịch sử. Khi cần cập nhật, tạo tên/version mới và review nguồn trước khi thay bản báo cáo hiện hành.

Actual builder đã thực thi7cells bằng Python. Lượt kiểm riêng thực thi lại cho outputs giống hệt, kiểm JSON notebook subset/cell IDs/counts, escaped JSON Pointer, HTML escaping, source-SHA negative canary và path-outside-repo rejection; **8 kiểm đạt**,0,068679s≤30. Source/builder/notebook giữ nguyên qua lượt kiểm. [Bundle7outputs](../runs/thesis-evidence-notebook-20261108-01/README.md), [manifest](../runs/thesis-evidence-notebook-20261108-01/manifest.json), SHA `2100a70da6b8da2547bfeba958187b478a53f5e195e8987b1cdb1f5109eee410`.

**Giới hạn nghiệm thu:** chưa chạy qua Jupyter kernel/nbformat library và chưa kiểm thị giác viewer. `.venv` hiện chưa có IPython/nbformat/matplotlib; không cài thêm vào môi trường đang dùng chỉ để tạo báo cáo. Có thể mở đọc outputs ngay; RunAll trong notebook cần kernel có IPython. Builder tự chạy bằng `.venv` không cần các thư viện đó. Gói hiện là bảng và sơ đồ thứ tự, **chưa có plot khoa học xuất bản**. Chưa thêm CI/p-values hoặc kết quả train mới.
