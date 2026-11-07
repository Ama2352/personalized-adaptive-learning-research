# SAKT frozen inference: kiểm kỹ thuật CPU — 07/11/2026

Archive hai targeted trials đã chạy, không thực thi thêm tests/model/trainer,
optimizer, GPU, realdata/Holdout, cloud hoặc Git mutation. Trial01 có82pass
(37core+45adapter), trial02 có87pass (37core+50adapter); cả hai khôngfail/error/skip,
dưới120s. Exact adapter/test snapshots và run/log/JUnit được giữ riêng từng lượt,
không gán final test source cho trial01. Final source/tests/report và dependencies
nhỏ được snapshot; không sửa shared/core/config/tensors/__init__ trong gói.

Random weights chỉ là engineering fixtures. Own typed scores có provenance,
không OnlineScore fitted. fit và complete OnlineSession backend từ chối vì chưa
trainer/selected-fit provenance. Caller phải khai báo cold policy/geometry;
không adoption S04/S05/mastery/calibration hoặc nghiệm thu fitted baseline.
Metadata equality/hash không xác thực training/split hoặc origin của từng input.

checkpoint_inventory.json giữ đường dẫn/size/SHA của95 .pt random/negative-control
fixtures, không copy checkpoint binaries. Không checkpoint nào là selected fitted
model. Bản kê không giả mọi negative fixture là loadable/finite. Không xóa nguồn
tmp trong lúc còn cần truy vết/resume. Bundle không là standalone full runtime.

archive_copy_inventory_before.json được lập trước copy; archive_copy_inventory.json
ghi source pre/post và destination SHA. Manifest ghi sources/outputs. pack_evidence.py
là đúng mã đóng gói được chạy; source→archived_as cho phép tra các đường dẫn repo
còn nằm trong script/report snapshots. Tái chạy tests cần project .venv/dependencies
và output ID mới theo run.json; không chạy lại packer vào bundle đã đóng.

Gate16 native AKT/shared đang được xử lý riêng, không dùng nó nghiệm thu SAKT.
Actual CUDA của AKT không nghiệm thu adapter CPU mới; không Gate4/full training/RQ
efficacy từ87cases. Không thay indexes/state/tasks/Git. Sau closure chỉ gọi helper
verify_evidence_bundle để kiểm output SHA, không ghi thêm output vào bundle.
