# Notebook bằng chứng KLTN — snapshot08/11

Notebook báo cáo đã có outputs thực:7code cells/14cells, đọc28inputs kiểm14claims và104JSONPointers của source map C14. Chạy lại các cell bằng .venv/stdlib cho outputs giống hệt; tám kiểm integrity/schema-subset đạt. Không train/simulator rerun, thêm quan sát, mở Holdout, network hoặc cài thư viện.

Đây là report snapshot/pilot diagnostics, không kết quả cuối của RQ1–RQ3. Có bảng RQ1, first-break explanation, retention identity, factorial và Junyi order-only cùng source/limits. Sơ đồ nguồn dùng chuỗi S→M/R→C/B/keys→A→Pserved→interact/update, không causal funnel từ Pserved. Các tables là output từ artifact có SHA, không gõ tay số liệu.

Notebook nguồn ở notebooks/thesis_evidence_report.ipynb. Outputs được tạo bằng actual local Python cell execution; **chưa QA bằng Jupyter kernel hoặc kiểm thị giác trên viewer**, không gọi đây là nbformat-package validation. Để đọc outputs không cần install; để RunAll bằng notebook kernel cần IPython trong môi trường đã chọn. Builder không cài packages. Plot khoa học/ảnh xuất bản chưa có trong gói này.

Snapshot source map SHAfbfa712e1eaf04f05fee5a33c577393478ba7f5a766af2a836d4598a2ed73bbc. Nếu đổi inputs/builder cần review/rebuild phiên bản mới; không sửa bundle đã đóng. File validation lưu source hashes, các canary và giới hạn; inventory trước/sau copy khớp.
