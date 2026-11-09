# Review plan cho kiểm bất biến concept-local của Paper1

Ngày09/11/2026. Chỉ chuẩn bị một file unittest candidate dưới P. Chưa import, chạy Python/test/mô phỏng/Git hoặc sửa production. Phối hợp với nhánh proof của rq12, không sửa tracking/báo cáo đang được nhánh đó sở hữu.

## Mệnh đề mà fixtures đối chiếu

Với cùng initial estimate/latent của từng concept, bank và item tie rule, tape phản hồi theo local visit count, cập nhật selected-only, dynamic K theo local count và world không quên/time/cross-concept effect, trạng thái tại local visit n không phụ thuộc global interleaving. Item exposure cũng là local vì mỗi item chỉ thuộc một concept. Một cặp records được so đầy đủ sau khi bỏ duy nhất global step, gồm item/difficulty, P, Y, estimate trước/sau, local count, item exposure, p_true và latent trước/sau.

Nếu hai DAG episodes đều hoàn tất ALL_ESTIMATED_MASTERED, mỗi concept dừng tại cùng first local threshold, nên stopping N, tổng tương tác, final estimated/latent và local prefixes bằng nhau. Global order, chapter switches/re-entry vẫn có thể khác. Không giả định mọi tape/horizon đều dẫn tới hoàn tất. DAG chỉ bảo đảm ready rỗng tương ứng mọi concept đã mastered theo estimate dưới source này.

Nội dung này là hệ quả có điều kiện của simulator, không kết luận graph cải thiện/hại/trung tính trên người học. Không coi SHA-keyed draws là bằng chứng statistical independence. Trường hợp có cap vẫn giữ invariance khi cùng local N. Công thức tổng gain12N chỉ áp dụng khi không có update bị clip, không được áp cho initial trên cap hoặc mọi allocation tại finite H.

## Sáu phương thức nhỏ đã chuẩn bị

1. Hai DAG trên3nodes cùng profile/u0 đều hoàn tất. So exact local prefix, first stopping threshold, per-item exposure, final states và tổng T. Graph rỗng cho chapter blocks A→B, một cạnh b→a2 cho A→B→A. Không đặt golden TableI/PDF matrix.
2. Đưa wrong response thật từ supplied uniform.999 vào local tapes, rồi u0. So cả hai complete runs, không đồng nhất tổng đúng với latent gain.
3. Truncate cùng fixture ởH4. Hai allocation/final states khác nhau nhưng mọi shared local prefix vẫn exact. Có assertion overlap dương để tránh so sánh rỗng.
4. H1, initial latent a1498/b1200, estimates1200. Empty graph chọn a, b→a giữ a ngoài ready và chọn b. Literal cap cho tổng latent gain2 và12 với cùng một feedback. Đây là counterexample về finite allocation/cap, không counterexample phá mệnh đề complete.
5. H2 với latent1200/1300, không update nào chạm cap. Hai allocation và tổng Y khác nhau, tổng latent gain vẫn12×2 cho mỗi run. Test ghi rõ từng oracle increment bằng12.
6. Một concept có6wrong uniforms trước u0, bắt thay item difficulty và đi qua local N≥15. So singleton episode với hai complete interleavings, giữ nguyên item/count/estimate/latent chain.

Candidate chỉ gọi API public `initialize_profile`, `run_continuity_episode_supplied`, `Paper1PdfController.ready_set` và các representations hiện có. Không monkeypatch, tự viết update loop, sửa class/private state, giả attestation train hoặc dùng oracle để chọn. Bank dựng tay tối đa3nodes/9items, nhãn môi trường unverified, không đọc canonical CSV hoặc artifacts nghiên cứu.

## Allocation kiểm đề nghị để Root xem

Sáu unittest methods,13 supplied episode calls và thêm một controller chỉ đọc ready, không thêm world feedback cho controller đó. Horizon lớn nhất90, tổng upper bound từ horizon là464feedback nếu mọi run dùng hết cap. Không có NN/optimizer/torch/data loader. Fixtures là đơn vị kiểm quy tắc, không13người học hoặc empirical study mới.

Root có thể dùng wrapper stdlib hiện có với cap30giây và PYTHONPATH trỏ src. Command riêng cho candidate là `.venv/Scripts/python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/test_paper1_concept_local_invariance_candidate01.py -v`. Chưa dispatch. Nếu sau review chuyển vào tests/paper1_pdf, cần inventory copy và giữ exact source pin, không tự mở rộng test scope hoặc matrix.

## Source pins trước khi chuẩn bị

- Candidate unittest SHA `dfa6b07572a76fcf53e48d7815f957bda40c00755ea44cb3d5fc705f2767104f`.
- `episode.py` SHA `e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471`.
- `simulator.py` SHA `b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f`.
- `simulator_bridge.py` SHA `b29105acd8de84b060ca27573bb7f7cf8e85599a4596e50e4a21ab63c82329d2`.
- Cơ sở episode/seeded đã có regression, không cần import test modules để lấy fixtures hoặc tự rerun85 trong lượt chuẩn bị này. Bundle domain28 đã đóng là bối cảnh độc lập, không được mở sửa.
