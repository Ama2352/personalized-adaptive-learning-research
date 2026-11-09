# Episode continuity có RNG sở hữu riêng theo phiên bản PDF Paper1

Ngày09/11/2026. Kiểm kỹ thuật đã có output xác nhận cho hai API `prepare_seeded_draws` và `run_continuity_episode_seeded`. Recipe `paper1-pdf-keyed-private-random-v1` là lựa chọn triển khai prospective. PDF bản nộp vẫn là nguồn có thẩm quyền theo D37.

## Đường chạy đã triển khai

Mỗi sự kiện có một `random.Random` riêng, lấy seed256bit từ SHA256 của JSON canonical chứa version, root seed, replicate, persona, loại sự kiện và concept. Uniform phản hồi còn có số tương tác đã commit của concept. Graph, policy và vị trí global không đi vào key. Vì vậy các branch dùng chung replicate có thể dùng chung draw ở cùng concept-local count dù thứ tự ghé concept khác nhau. Đây là quy ước coupling tường minh của phiên bản mới.

Input được kiểm trước draws. Khởi tạo gọi `.gauss(0,1)` riêng cho từng concept rồi dùng initializer hiện có áp dụng mean và sigma50 một lần. Tape phản hồi có đúng horizon cho mọi concept, horizon từ1 đến500. Profile và tape được đóng thành tuple/frozen records với content identity. API chuẩn bị ghi provenance Python thực tế và SHA của `random.py` khi được gọi. Module import không đọc provenance. Seeded runner kiểm binding rồi gọi đúng một lần supplied episode hiện có, giữ predict-before-observe và phân tách observable/oracle.

## Bằng chứng thực thi

Một lượt kiểm toàn bộ Paper1 có **85 phương thức đạt, 0 lỗi, 0 failure, 0 skip**, gồm13 phương thức seeded mới và72 hồi quy trước đó. Wrapper đo2,4102863000007346giây dưới cap30giây; unittest ghi1,563giây bên trong. Hai số đo có scope lồng nhau. Receipt xác nhận returncode0, không timeout và không có NumPy, pandas hoặc Torch trong process test. Mười source/test trước và sau có cùng SHA. [Receipt](../runs/paper1-seeded-episode-engineering-20261109-01/result.json), [stdout](../runs/paper1-seeded-episode-engineering-20261109-01/stdout.log), [stderr](../runs/paper1-seeded-episode-engineering-20261109-01/stderr.log).

| Kiểm mới | Phạm vi xác nhận |
|---|---|
| Key và phép lấy mẫu | JSON UTF8 canonical/SHA; namespace persona/seed/replicate/event/concept/local count; gauss chuẩn rồi scale một lần |
| Input và identity | Input sai bị chặn trước RNG; mutation/different domain/runtime bị chặn; nested tapes giữ giá trị riêng |
| State và reuse | Global random state giữ nguyên; đổi thứ tự node hoặc thêm node khác không advance event stream đã có |
| Đường chạy | Seeded wrapper bằng supplied core trên cùng draws, delegation một lần, không redraw khi chạy |
| Coupling và điểm dừng | Fixture branch đảo thứ tự giữ kết quả concept-local, phân biệt tape đã sinh với feedback thực dùng |
| Runtime provenance | Test đối chiếu Python/runtime hiện tại và source `random.py` thực; mô phỏng drift bị từ chối |

Fixture coupling dùng RNG giả trả0 để kiểm cơ chế một cách xác định. Các test khác kiểm private Random thật và provenance thực. Fixture dựng tay không có attestation miền nghiên cứu. Hai inventory chuẩn bị lưu bảy dependency trước/sau, gồm source runtime `random.py`38076bytes, SHA `b8586e6bdd037fcd0e53e9529f0e257afaac5fa62eaf59d5d4ac02829656897e`. Các inventory này được tạo lúc chuẩn bị source, độc lập với inventory10file của lượt test.

## Giới hạn và bước còn lại

85 là số phương thức regression, không phải85 người học hay episode nghiên cứu độc lập. Chưa chạy pilot domain28concept hoặc matrix50seeds. B0, global/unlock policy dispatch và kết luận so sánh graph vẫn ngoài batch này. Bằng chứng hiện tại không tái lập số liệu PDF hay xác nhận historical random draws. Giữ runtime/source identity giúp truy vết và chặn drift, chưa có bằng chứng portability draw-bit giữa các phiên bản Python. Việc một fixture coupling đạt không chứng minh statistical independence hoặc lợi ích học tập.

## Nguồn và trạng thái lưu trữ

- Source mới SHA `7c7ac305cd49fd79f5768173198705be7fa32586114acf5871950c7540dda1b2`; test mới SHA `f97674bc764988271c091a00560bf31f2afba2f951b72819a150ae64a83b48e2`.
- Receipt SHA `aebb792bb319307d7a16aac24699a9ec652ec1e29bd315aa277bda44d8a21de9`; harness SHA `16af2814389c6b161d983e0f0319cf5b619d3c217a7d8223917ee69ef42704eb`.
- Proposal recipe SHA `06a5bf51326c972e24b685c2e35103200f1293a7f4a74f6193b8a9b94705055d`. Pilot dự kiến trong proposal chưa được thực thi.
- PDF Paper1 SHA `984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4`; Spec02 SHA `2c83655f63d973e3d009a5d091bfd2405513b89e00f782b1f68ab2b03268b176`. Các nguồn này chỉ tham chiếu bằng SHA trong bundle.

Bundle dự kiến `paper1-seeded-episode-engineering-20261109-01` giữ hai source mới, harness, ba raw outputs, hai inventory dependency, proposal, báo cáo và hồ sơ copy. Manifest completed sau bước đóng gói mới xác nhận closure. Liên kết trên dùng vị trí báo cáo canonical dự kiến `research_tracking/reports/paper1_seeded_episode_readiness_20261109.md`.
