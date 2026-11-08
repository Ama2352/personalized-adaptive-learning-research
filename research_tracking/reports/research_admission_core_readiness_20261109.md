# GRAPH12/13 — core đối chiếu chín candidate trước system selector

**Đã làm được:** một core thuần nhận metadata và các dòng chế tạo của đủ chín candidate, kiểm cùng query/nhãn/full population, lập coverage và sufficient statistics trên U chung. Tám ca kiểm đã PASS, không gọi mô hình hoặc đọc dữ liệu nghiên cứu. **Chưa làm:** xác minh chín terminal thật trên đĩa, tạo system winner/external freeze hoặc cho phép refit.

## Từ phần đã có đến khoảng trống này

[Kernel chọn ứng viên](research_selection_kernel_readiness_20261109.md) đã tính response-pooled LL và shared learner bootstrap trên statistics được cung cấp. Nó không tự biết statistics có thực sự đến từ cùng selection population và đủ chín candidate hay không. Runner hiện hành vẫn là A0 pilot: export raw best80 rồi local freeze và auto-refit; terminal đó không được đổi nhãn thành main selected-only receipt.

Core mới tách bước kiểm consistency: nhận đủ A0, A1/A2/A3 với EXPERT/LEARNED, SAKT và GKT; sau đó mới nhận từng nhóm chín dòng. Nó kiểm model-neutral key, nhãn, phase/encoding riêng mỗi model, support/null/reasons và coverage đã khai báo. U là intersection của A0+A1/A3 theo rule hiện hành; A2/SAKT/GKT vẫn bắt buộc có đủ full rows và coverage, không bị bỏ khỏi allocation hoặc tự làm đổi U.

Mỗi học viên chỉ buffer năm loss lists rồi dùng fsum một lần, tạo đúng typed statistics cho kernel đã có. Không giữ chín bảng đầy đủ, không chạy lại bootstrap/LL implementation khác và không tạo winner. U rỗng là inconclusive/rejected, không fallbackA0 để che lỗi đầu vào.

## Kết quả kỹ thuật thực tế

| Kiểm tra | Bằng chứng |
|---|---|
| Cold import | CPython3.13.5 trong `.venv`; không NumPy/pandas/Torch/sklearn/scipy. |
| Tám unittest |8PASS,0failure/error/skip; log unittest0.089s. |
| Bounded execution | Controller lưu prewrite1.064003000035882s với whole cap30s; owned receipt0.8420593738555908s, cleanupJob0. Hai thời gian có phạm vi khác nhau, không cộng thành throughput. |
| Nguồn và phạm vi | Source SHA trước/sau khớp; raw SystemExit thực tế int0; guard không có forbidden attempt.0model/optimizer/actual corpus rows. |

Fixtures chỉ có4keys chế tạo,3learner IDs và9candidate IDs. Các ca kiểm full/common/per-learner coverage/noauthority; stage/pilot/refit/calibration/foreign-domain/missingGKT; duplicate và state poison; query/label/phase/encoding mismatch; expectedF digest chống missing/sharedwronglabel/reordering; emptyU/coverage mismatch; initial-backbone claim/resource caps; clock quá hạn sau tạo result. Đây là số ca phần mềm, không số lần tái lập hay learner nghiên cứu mới.

Nguồn đối chiếu sau closure: [module](../runs/research-admission-core-engineering-20261109-01/source__research_admission.py), [tests](../runs/research-admission-core-engineering-20261109-01/test__research_admission.py), [verdict](../runs/research-admission-core-engineering-20261109-01/capture__final.json), [raw log](../runs/research-admission-core-engineering-20261109-01/owned__stderr.log), [hợp đồng và gap map](../runs/research-admission-core-engineering-20261109-01/MAIN_NINE_ADMISSION_REVIEW01.md).

## Ranh giới quan trọng trước dùng cho main research

Result luôn ghi `NOT_FILE_ADMISSION_STATISTICS_ONLY`; các cờ verified artifact bytes, admitted nine terminal files và external freeze authority đềuFalse. SHA-shaped fields và declared selected-only status chỉ là claims. Core không kiểm file có tồn tại, status có đúng thực tế, checkpoint có fitted hoặc quyền sử dụng dữ liệu/runtime. Actual main selected-only producer và trusted disk driver vẫn còn thiếu; không có chín candidate research mới từ lượt này.

CanonicalK có learner/item/timestamp/source_row/global_rank/history scheme/hash/origin role; phase/encoding hashes là provenance riêng, không thêm vào cross-model join. **Thứ tự sortedK là statistical view, không logged chronology.** Raw exports giữ thứ tự tương tác; driver sau này phải tạo deterministic sorted view riêng cho phép đối chiếu, không reorder huấn luyện hoặc sửa prefix history. Full expectedK/y digest phải đến từ selection universe đã được trusted caller xác minh trước, không lấy từ chính chín exports cần xét. SHA population cũ có scheme khác vẫn giữ riêng, không relabel.

Trusted disk stage còn phải kiểm actual bytes/sizes/JSON/CSV schema, nguồn/runtime/caps, closed terminal authority, complete epoch/checkpoint/init lineage, absence failure và đủ9barrier. Chỉ sau core→kernel statistics mới publish external freeze thực; mọi main refit kiểm freeze đó trước constructor. Calibration không được dùng để optimize/select; việc public reader audit ba roles trước allocation vẫn được phép theo Protocol22. Không reader rewrite, không mở oracle/final/Holdout và không cấp quyền GPU/paid execution.

Báo cáo này chuẩn bị trước archive closure. Manifest/index xác nhận bundle đã đóng; archive integrity không đồng nghĩa main selection, runtime/fullGate hoặc RQ đã hoàn tất.
