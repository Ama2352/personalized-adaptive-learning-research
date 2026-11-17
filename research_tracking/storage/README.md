# Chỉ mục bàn giao và lưu trữ

- [Bộ bàn giao để tiếp tục KLTN](https://drive.google.com/drive/folders/1T6GseWOnUbbj-eXTcWIELAp2hPemGrLQ): dùng BAT_DAU_TAI_DAY_FINAL và MANIFEST_BAN_GIAO_FINAL ở gốc. Gồm source hiện hành, đầu vào chuẩn, model và kết quả đã nghiệm thu; tải nhóm core/ready theo hướng dẫn.
- [Kho lịch sử/audit ngoài bộ bàn giao](https://drive.google.com/drive/folders/1QoqGGMj6NUW7soLPxSkKDeKknFO_uyw6): các snapshot, output/cache cũ và hồ sơ dọn; chỉ tải khi cần truy vết/tái lập lượt cũ.
- [Catalog226.534đường dẫn đã chuyển lạnh](20261118_STORAGE_INDEX.json.gz): SHA/kích thước, fileID Drive, member/parts và đường dẫn gốc. Đọc bằng scripts/storage/restore_workspace.py; không cần giải nén catalog bằng tay.
- [Hướng dẫn lưu trữ/phục hồi](../../docs/operations/STORAGE_AND_HANDOFF.md) và [bằng chứng đợt dọn](../runs/workspace-cleanup-20261118-01/README.md).

Các model/bảng/manifest lịch sử giữ nguyên bytes. Local tiếp tục giữ đầu vào và model gọn, nguồn chương trình và hồ sơ nghiên cứu; nhiều payload/cache cũ có thể vắng mặt có chủ đích. Trước khi chạy lại request cũ, tra catalog và phục hồi đúng SHA. Không coi lỗi thiếu payload local là lý do đổi protocol hoặc tạo lại số liệu khác.
