# Kiểm tích hợp domain28 cho episode Paper1 prospective

Ngày09/11/2026. Một operation đã hoàn tất với đúng một logical profile US, seed42 và replicate `paper1-rng-smoke01`. Hai continuity episodes dùng B1 và GA với cùng profile/tape đã chuẩn bị. Đây là bằng chứng nối domain và simulator của phiên bản prospective, chưa là matrix nghiên cứu hoặc tái lập số liệu lịch sử PDF.

## Input và thông tin được giữ cố định

Domain loader đọc đúng năm CSV đã ghim SHA từ bộ input Paper2 được chọn làm dữ liệu prospective. Kiểm28concepts,84items, B1 có25cạnh nội chương và GA có31cạnh gồm28nội chương/3liên chương, B1 là tập con GA. Tám chapter keys ngoài28concepts được trả riêng. Mỗi graph giữ traversal order topological lexicographic của chính nó. Vì GA thêm ba cạnh nội chương cùng ba cạnh liên chương, so sánh hai branch chưa tách riêng cross-edge effect.

Chuẩn bị một lần28normal events và14.000uniform events theo recipe `paper1-pdf-keyed-private-random-v1`, horizon500. Hai branch dùng cùng immutable draws có identity `f0a02428c9ec3fa7948ff14eeae899c1b44c6de4e7edf29955b31f4fa0a088c8`. Profile identity là `3fca887b45a916c6a6849bc66fca9cc082403452759f2bd8af6ae67b8976f662`. Keys phản hồi theo concept-local count, không global step hoặc graph/policy. Runtime provenance ghi CPython3.13.5 và source `random.py` thực. Bộ85regression với13seeded cases là prerequisite đã chạy trước, không được chạy lại trong operation này.

Controller dùng estimate trước phản hồi, world dùng latent riêng để sinh đáp án và tăng selected latent12 theo cap literal của core. Trace observable và oracle sidecar có đường dẫn riêng nhưng ghép bằng event/item/concept identity. Không có neural model, optimizer, training corpus hoặc GPU. Hai trajectories có thể khác thứ tự nên shared draws không biến chúng thành một fixed observable stream.

## Kết quả operation đã nghiệm thu

| Branch | Feedback đã commit | Chapter switches | Chapter re-entry | Estimated mastered | Kết thúc |
|---|---:|---:|---:|---:|---|
| B1 continuity | 172 | 2 | 0 | 28/28 | ALL_ESTIMATED_MASTERED |
| GA continuity | 172 | 4 | 2 | 28/28 | ALL_ESTIMATED_MASTERED |

Cả hai kết thúc trước horizon500, `budget_exhausted=False`. Tổng344feedback mới được sinh trong operation,172mỗi branch. Bộ đếm thực ghi2controller,2world,2episode,1prepare,14.028keyed Random events,344respond/observe và346selection calls có return. Hai terminal selection checks không tạo thêm feedback. Không chạy đảo thứ tự branch hoặc thêm policy episode để củng cố kết quả.

Final latent SHA của hai branch cùng bằng `b62b8c760f53fa489a79f9c8baa2c992e1221748c9a99e1edcd8470c73895ac3`. Đây là đối chiếu identity trong trường hợp coupling đã khai báo. Estimated mastery28/28 không được đổi tên thành latent mastery accuracy hoặc hiệu quả giáo dục.

GA có hai re-entry trong witness này được giữ nguyên. Tiêu chí nghiệm thu không đòi GAzero hoặc graph nào tốt hơn. Kết quả không phủ định số liệu của PDF trên các lượt đã báo, vì phiên bản này có input reuse, traversal và private-RNG recipe prospective với provenance riêng. Một US/seed không cho phép suy thứ hạng graph, độ ổn định theo persona/seed hoặc lợi ích học tập. Các ablation plain lowest-Elo/cross-unlock, B0 và matrix50seeds chưa chạy trong operation này.

## Kiểm tính toàn vẹn và tài nguyên

Outer đã kiểm đủ10scientific outputs, manifest COMPLETE-last, toàn observable/oracle event identities, full core/branch/profile/graph SHA và source33pins trước=sau. Worker phục hồi các observer bindings và giữ nguyên global RNG. Scientific frameworks không được import. Owned helper hoàn tất returncode0, cleanup đạt, Job active cuối bằng0 và handle đã đóng. Monitor ghi18samples,16samples có child, family high-water72.155.136bytes và RAM khả dụng nhỏ nhất2.028.568.576bytes, dưới RSS256MiB và trên floor512MiB đã cấp. Đây là quan sát lấy mẫu, không hard continuous quota.

Thời gian trong receipt có các scope lồng nhau. Worker ghi0,77114020002773giây dưới cap26, owned helper ghi1,00959849357605giây trong tối đa30giây gồm cleanup3, outer trước receipt ghi1,15433220000705giây dưới cap35. Không cộng các thời gian này. Các số trên không là benchmark throughput cho matrix hoặc mô hình KT.

Nguồn khoa học gốc tiếp tục ở `experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/`. Vùng `experiments/simulator/results` được Root chọn cho simulator dùng chung, tách output theo model KT. Bundle nhỏ dự kiến `paper1-seeded-domain-smoke-engineering-20261109-01` giữ10outputs, raw owned/outer, source entrypoints, allocation và review. Nó chỉ tham chiếu33source/input/runtimepins, không copy bank CSV, PDF hoặc thư viện runtime. Bản báo cáo này không tự xác nhận archive đã đóng.

## Pins kiểm lại

- Worker `94b2c034237fdc977efb1df5ef58d16ac8ac57c6e2eaf6836a7b7ea7ba810833`, outer `d63df355455f37f351da676e6efa51c7939956d4d8b4b29c78e936d3b3ecc13f`, allocation `a4c0d87f3dfe86a4a9688aafe6f21e1711eb2cbee1014db432880a3f34811942`.
- Outer actual `bea520db3612a5fb5b611c85ab80eacf29b3259eb046c94d02ca23a6eb6a3201`; scientific manifest `1364da669043bcfc70f9e1bfb81a20550bd2a7990e5315a08b334665623f6f30`.
- PDF Paper1 vẫn là nguồn có thẩm quyền theo D37, SHA `984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4`. Bộ CSV được tái dùng có identity prospective, không gán byte identity lịch sử của PDF.

[Result và traces đã đóng theo scientific manifest](../../experiments/simulator/results/paper1-seeded-domain-smoke-20261109-01/result.json). Liên kết dùng vị trí canonical dự kiến `research_tracking/reports/paper1_seeded_domain_smoke_readiness_20261109.md`.
