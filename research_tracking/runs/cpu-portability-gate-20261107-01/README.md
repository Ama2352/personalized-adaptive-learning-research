# Archive CPU portability, Gate15 và notebookv12 — 07/11/2026

Đây là evidence archive, không chạy lại Gate/model/tests/probes/cloud. Platform trial01 giữ collection failure thiếu PYTHONPATH; trial02 và03 đều21pass, trong đó02 có29deselected,03 chọn node IDs tường minh không deselect. Source test_runner/test_runtime snapshots khớp report và Gate15buildhash; production runner/check_runtime snapshots cũng khớp Gate15. Giữ nguyên failure/log/XML bytes.

Gate15 actual local Windows CPU462pass0fail/error/skip294.17s; reportsha7e15832f72632dd07f676ef277a8ad49d3f4a71ef35c8f40099492f5b9071f16. Report/log/XML/pointer-before/current-at-archive được snapshot; current pointer sau này có thể đổi. Không coi Gate15 là actual Linux/Colab/CUDA acceptance.

Notebookv12 snapshot khớp harness e75004d19a500ad562d7e7a11656158fae4cb74c8fc74c8fd389214e566616a7; embeddedZIPddb35b8e... và139source files được kiểm exacthash không execution. Notebook đã clear outputs. Harness20cases dùng local extraction/export thật nhưng GPU/setup/CPU guards mocked; dependency probe4cases cũng mocked. Không đọc log CONNECTED_GPU/MOCK_GPU như actual GPU. Snapshot scripts tại archive, prior resultJSON không bind scriptSHA riêng.

DuckDB actual rawconnector receipt khớp contrastJSON: cùngPython/source one-row COPY TO ? trong isolatedvenv,1.3.2ParserException và1.5.6PASS; localAPIproof1.5.6PASS. Scope chỉ one-row API compatibility, không đầy đủ model/realdata/Colab suite. Requestcode giữ cách chạy, không có credentials/private config trong allowlist archive.

RQ12synthesis là snapshot aggregate/descriptive evidence, không confirmatory graph benefit hoặc final efficacy. Tự kiểm21selectedoutputSHA; arithmetic bảng chain, closedloop gain/action disagreement/retention, factorial mean/contrast/coverage và common-population fractions/identity.42inputinventory giữ nguyên lịch sử, không rehash/assert currentmutable indexes hoặc nguồn runtime vẫn như lúc synthesis. Các giới hạn posthoc/pilot/lowcoverage trong reportJSON/MD giữ nguyên; không tự thông qua S04/S05.

archive_copy_inventory.json có SHA trước/sau từng copy. archive_validation.json ghi phạm vi kiểm; manifest hash mọi output và sources đã chọn. BUNDLE_MANIFEST_v12.json chỉ manifest lấy từ ZIP nhúng, không thêm ZIP trùng lặp. pack_evidence.py giữ đúng mã đóng gói dùng helpers có sẵn. Không sửa bundle sau closure. force_add_paths.txt liệt kê các logs bị ignore; không sửa .gitattributes hoặc Git/index/state/tasks trong gói này.
