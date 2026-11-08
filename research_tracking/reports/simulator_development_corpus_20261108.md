# Corpus Development simulator đầu tiên — kiểm chứng native, chưa fit mô hình

Ngày 08/11/2026. Đây là bằng chứng tạo và đọc corpus observable theo [protocol Development](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md), không phải kết quả prediction, calibration hoặc trả lời hoàn tất RQ. Một lượt native do ROOT thực thi đã được chấp nhận; lần kiểm độc lập chỉ đọc/hash metadata và dữ liệu public, không gọi lại teacher/model.

## Nguồn và trạng thái

- Corpus canonical: [grade10-development-lifecycle01-20261108](../../artifacts/simulator/corpora/grade10-development-lifecycle01-20261108/), đúng **17 file, 6.985.213 bytes**. Các bytes canonical giữ nguyên; bundle bằng chứng chỉ tham chiếu chúng qua inventory SHA, không nhân đôi corpus.
- [Receipt outer](../../artifacts/akt/local-tests/development-corpus-20261108-01/run.json): SHA-256 `08a8975399b2c63474dd4db5d3dfd213024bfe451d21dce749ae025a78fb42de`, trạng thái `ACCEPTED_FIRST_DEVELOPMENT_CORPUS_NOT_MODEL_FITTED`.
- [Config](../../experiments/akt/configs/simulator-research-corpus01.json): `8e7800482cea61a5f3ab66e4909de996fda57bcc059dd2751c2e4177dbfa263e`; [request](../../artifacts/akt/local-tests/development-corpus-20261108-01/request01.json): `52a183e9022ff33937276e5e37f21d362ac06dfb2c2808ea7462df017dfea005`.
- Outer đã thực thi [run_native01.py](../../artifacts/akt/local-tests/development-corpus-20261108-01/run_native01.py), SHA `2445629d194337fa7d325b09b1f01f359f0ea5d5eef8750753d29d46ca2a3a1c`. Request ghim 13 nguồn collection và 4 nguồn worker/Job/publisher/reader. Kiểm độc lập xác nhận cả **17 nguồn hiện tại** bằng SHA đã dự trù và receipt thực thi; snapshots trong bundle ghi rõ thời điểm là sau run, không giả là snapshot lấy tại lúc native bắt đầu.

`corpus.json` có SHA `555ed695c7c7121af474edb542fa3eef664b340162ced46cdfc001a5d7a4ad72`; `DONE.json` có SHA `66232663868baafd2f012b4d79afad373e2fd5e831d30622153163b94e1b733f`. DONE là dấu hoàn tất logic của publisher. Acceptance còn cần result outer, terminal RC0, không failure, resource/time checks, Job cleanup và inventory; không suy thành công chỉ từ DONE.

## Dữ liệu thực tế đã tạo

Recipe đã ghi dùng `uniform_items`, seed gốc 42 và namespace riêng. Mỗi learner có 210 events; 60 learner Development được phân vai tách biệt. Profile PG/PY/PYH có 16 learner/profile ở train và 2 learner/profile ở mỗi vai selection/calibration.

| Vai | Learner | Events | Nhãn 0 | Nhãn 1 | Items được quan sát |
|---|---:|---:|---:|---:|---:|
| Train | 48 | 10.080 | 5.041 | 5.039 | 84 |
| Selection | 6 | 1.260 | 665 | 595 | 84 |
| Calibration | 6 | 1.260 | 626 | 634 | 84 |
| Tổng Development | 60 | 12.600 | 6.332 | 6.268 | 84 trong mỗi vai |

Đây là **12.600 actual teacher attempts và 12.600 returns**, khác counts chế tạo trong kiểm orchestration trước đó. Không có final events, model calls hay Modal spend. 150 learner final trong plan chỉ là metadata phân vai; chưa tạo/đọc final events. Một namespace/seed và world nguồn cố định không tạo thêm independent experimental N; 12.600 events không phải 12.600 đơn vị độc lập cho suy luận.

Typed QA xác nhận toàn bộ learner thuộc đúng assignment, không giao learner giữa ba vai, đủ 210 events/learner. Timestamp event thứ `rank+1` bằng `1767225600 + (rank+1)×21600`; tức logical time tăng 6 giờ. `source_row` bằng `assignment_ordinal×1.000.000 + rank+1`, có 12.600 giá trị duy nhất. Không tái tạo hay sửa event sau khi kiểm.

## Kiểm độc lập và giới hạn thông tin

[Script kiểm/đóng metadata](../../artifacts/akt/local-tests/development-corpus-20261108-01/inspect_and_archive01.py) có chế độ `--inspect-only` chỉ đọc. Lượt độc lập đã chạy bằng `.venv\Scripts\python.exe -B`, RC0, tool wall 1,0445302 giây. Audit quan sát reader chỉ mở **9 model-input files + DONE**, tổng 1.507.656 bytes, cấm subprocess trong pha QA và cấm import NumPy/pandas/Torch/collector/publisher/native source. Reader identity khớp actual worker:

`f28048781fa10f53f456b213ddfcc2c66344c84033dee6f08524b56cc4a568da`.

Chín đầu vào là `corpus.json`, `bank.json`, `plan.json`, ba role JSONL và ba role manifest. Plan/provenance/recipe/source identities được reader typed tái dựng và đối chiếu; không dùng object chưa persist để vượt kiểm restart. Bảy file canonical dưới `oracle/` chỉ được stream hash như bytes opaque để so inventory, **không parse nội dung oracle**. Kiểm hash17 và source17 trước/sau giữ nguyên. Không đưa oracle vào model reader, không lấy latent mastery làm prediction score.

Đối chiếu độc lập từ lịch sử observable train cho thấy tối thiểu 38 learner/item, 47 learner/concept. Với tất cả 28×27 = 756 ordered distinct-concept pairs, tối thiểu 45 learner có một event parent **strictly trước** event child; cả 756 pairs đạt ít nhất 20 learner. Đây là coverage theo learner và thứ tự, chưa là confidence OOF, bằng chứng causal prerequisite, calibration, graph discovery hoặc đảm bảo estimator xác định tốt. Hai lớp trong mỗi vai là điều kiện hỗ trợ, chưa là metric chất lượng mô hình. Xem thêm [QA của ROOT](../../artifacts/akt/local-tests/development-corpus-20261108-01/structural_support01.json); kiểm độc lập tính lại các minima từ public trajectories.

**Đính chính phạm vi truy cập, không đổi số liệu:** QA của ROOT ban đầu ghi `oracle_opened=false`, nhưng vòng hash17 đã mở bảy file oracle để tính SHA opaque. [Erratum](../../artifacts/akt/local-tests/development-corpus-20261108-01/structural_support01_access_erratum.json) thay thế riêng diễn đạt này, ghim SHA QA cũ `8fb38076ea85a3fba93ef5e06807fa18c5c528f0f45cd85fd2643c37c8ee31fb`. Bytes QA gốc vẫn được giữ cùng erratum trong bundle. Không parse oracle JSON, không dùng oracle làm support features/model; không có thay đổi counts, leakage hay experiment failure từ đính chính này. Bổ sung trước closure chỉ đổi danh sách snapshot và ghi chú, không chạy lại data/test/native.

## Owner, cleanup và thời gian

[Job receipt](../../artifacts/akt/local-tests/development-corpus-20261108-01/owned_launch_receipt.json) khớp actual worker PID 7348, venv shim PID 35760 và parent owner PID 40140 qua creation times/handles, nonce, ready/GO binding, argv/source identities. Actual worker được xác nhận trong owned Job trước GO; worker/result owner khớp launcher. Receipt ghi RC0, không cleanup errors, Job active sau cleanup bằng 0 và Popen handle đã đóng. Đây là bằng chứng cho Job của lượt này, không là khẳng định toàn máy không còn process khác.

Các đồng hồ có ranh giới khác nhau và đều dưới cap 120 giây:

| Ranh giới | Giây |
|---|---:|
| Worker | 8,119466200005263 |
| Owned helper gồm cleanup | 8,553166151046753 |
| Outer receipt đã lưu | 8,765300299972296 |
| Outer terminal sau finalization | 8,767507299955469 |
| Tool wall | 9,2608469 |
| ROOT quan sát dispatch → terminal | 9,464 |

Nguồn của hai dòng cuối là [ROOT tool capture](../../artifacts/akt/local-tests/development-corpus-20261108-01/root_dispatch_observation.json); đó là normalized capture, không giả là raw stdout bytes. Stored receipt và terminal elapsed không bị chỉnh cho giống nhau.

## Bằng chứng lưu và việc còn thiếu

Bundle metadata dự kiến `research_tracking/runs/development-corpus-native-20261108-01/` dùng recorder/verify hiện có, giữ nguồn, request/config, operator/Job logs, QA và copy inventory SHA trước/sau. README giải thích đặt trong bundle; không thêm file thứ 18 vào canonical corpus. ROOT thực thi closure và Git riêng; report này không tự tuyên bố bundle đã đóng trước receipt closure.

Corpus này cung cấp đầu vào Development đã kiểm cấu trúc/provenance. Chưa có neural fit, epoch selection/refit, response calibrator fitted, confidence OOF, learned graph hoặc đánh giá final150/RQ efficacy từ lượt này. Không suy lợi ích học tập, khả năng tổng quát hay thời gian/chi phí train từ tốc độ collection. Kiểm native worker/publisher/reader là một stage; lần chạy mô hình kế tiếp cần review và ngân sách riêng.
