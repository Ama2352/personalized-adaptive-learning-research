# Hồ sơ audit revision Paper1 — 07/11/2026

Đóng bằng `record_evidence_run` hiện có. Snapshot hai reports đã review, giữ
inventory 33 inputs gốc và kiểm lại source/PDF/AST/Git blobs/archive members chỉ
đọc. Script được lưu để tái chạy **verification**; đây là phiên bản kiểm chứng
và đóng gói audit, không giả nhận là file script đã tồn tại ở lượt khám phá trước.

Không chạy notebook/simulator/model/realdata/Holdout, không GPU/cloud/network,
không Git mutation hoặc sửa paper/notebook/shared state/index. Chỉ copy báo cáo,
script/helper nhỏ và PNG trang3 đã xem; không copy toàn PDF hoặc 14 ZIP. Text
trang2–4, code-cell extract và candidate inventory là dẫn xuất để review.

`source_input_inventory.json` giữ nguyên 33 hashes của audit nguồn. Manifest
ghi hashes của sources hiện tại lúc đóng, còn `audit_verification.json` báo
đối chiếu snapshot cũ/current riêng. `copy_integrity.json` ghi pre/copy/post SHA.
Chỉ PNG trang3 được giữ (534.770 bytes) vì chứa Eq.7–9, Algorithm1 và latent/
50-seed setup; PNG trang2/4 giữ locator/hash trong report JSON, không nhân đôi.

Q01 chỉ thu hẹp local search, **chưa đóng toàn cục**; S01 vẫn cần tác giả/advisor.
Mismatch current notebook không bác bỏ finite tested-run claims của PDF.

Sau closure, chạy từ repo: `.venv\Scripts\python.exe
research_tracking\runs\paper1-revision-audit-20261107-01\verify_paper1_revision_audit.py
--verify-only`. Lệnh chỉ kiểm outputs theo manifest, không scientific validity.
Không thêm/sửa output hoặc manifest sau khi bundle đã đóng.
