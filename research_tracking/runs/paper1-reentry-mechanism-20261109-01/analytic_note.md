# Điều kiện đủ để không quay lại chương theo PDF Paper1

Ngày09/11/2026. Phân tích đại số và cấu trúc nguồn, không chạy simulator, import, test hay Git. D37 xác định PDF bản nộp là tài liệu có thẩm quyền. Ghi chú này giải thích cơ chế và giới hạn của một mệnh đề tổng quát, không tái lập các con số PDF.

## 1. Nguồn và phạm vi

- PDF `paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf`, SHA256 `984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4`. Trang2 Eq.(3) xác định ready, Eq.(6) chỉ cập nhật khái niệm được chọn. Trang3 Eq.(8)–(9) là continuity filter, IV.A xác định khởi tạo và định nghĩa re-entry. Trang3–4 báo cáo zero re-entry trong các run đã thử.
- Bản trích5trang `docs/thesis_recovery/evidence/paper1.txt`, SHA256 `b6d2d4a518a0b40f27c695bdde3ca624ce16ee976cb59151b15b85cee11eda85`.
- `src/knowledge_tracing/paper1_pdf/simulator.py`, SHA256 `b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f`. Dòng144–156 là ready và chọn chương, dòng181–186 là update selected-only và ghi chương đã chọn. Dòng109–116 của `tests/paper1_pdf/test_simulator.py` có fixture A→B→A trên domain tự tạo. Đây là nguồn kiểm thử lịch sử, không phải lượt chạy mới của ghi chú này.
- Receipt do Root chạy `artifacts/akt/local-tests/akt-research-runner-20261108-01/paper1_pdf_domain_actual_load01.json`, SHA256 `f84223382f5c6a37c6fafc5281aa29d5b0414137d5061c9aec3dfa712a9988a6`. Metadata là domain ứng viên prospective28concept/84item, B1 gồm25cạnh và GA gồm31cạnh, không xác nhận historical PDF input identity.
- Năm input và raw SHA nằm trong receipt trên. Hai graph lần lượt là `edges_baseline.csv` SHA `9d795fb88d00e5c2ec1d3b2215bb93038a944354c3c4709b6b0aa9d66906c39d` và `edges.csv` SHA `ecd910d8df52f8790997391de657ea0f9e8357446212c168b73e500d0facc2fb`, trong `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/`. Active chapter map chỉ gồm28node, tám key ngoài domain được giữ riêng trong receipt.

## 2. Mệnh đề B1 và chứng minh

Đặt M_t = {v | θ_v,t ≥ τ}, U_t = V \ M_t và V_C là các node của chương C. Giả thiết như sau.

1. Graph hữu hạn, DAG và mọi cạnh đều nội chương.
2. Ready đúng Eq.(3), tức chỉ gồm node chưa mastered có mọi parent đã mastered.
3. Khi chương hiện tại còn node ready, selector chỉ chọn trong chương đó theo Eq.(9).
4. Chỉ node được chọn mới được cập nhật. Không có forgetting, reset hoặc thay đổi graph/chapter mapping trong run.

**Bổ đề1. M_t tăng theo quan hệ bao hàm.** Node thuộc M_t không nằm trong ready, do đó không thể được chọn hoặc cập nhật. Những node này giữ nguyên θ. Node chưa mastered có thể tăng hoặc giảm Elo, nhưng việc đó không loại một node cũ khỏi M_t. Vì thế không cần giả sử toàn bộ các giá trị Elo tăng đơn điệu. Tính hấp thụ của mastered set phát sinh từ ready và selected-only update.

**Bổ đề2. Nếu V_C \ M_t khác rỗng thì chương C còn ít nhất một node ready.** Xét DAG cảm sinh trên các node chưa mastered của C và chọn một source v của DAG đó. Parent của v không thể là node chưa mastered khác trong C. Không có parent ngoài C. Vì vậy mọi parent của v đều thuộc M_t, nên v ready.

**Kết luận.** Sau khi chọn vào C, continuity buộc giữ C chừng nào còn node chưa mastered của C. Selector chỉ rời C sau khi toàn bộ C đã mastered. Theo bổ đề1, C sẽ không bao giờ có node ready nữa. Mỗi chương xuất hiện trong nhiều nhất một khối liên tiếp của chuỗi tương tác đã commit, nên chapter re-entry bằng0 cho mọi chuỗi đáp án và mọi tiền tố ngân sách hữu hạn.

Mệnh đề không đòi hỏi eventual mastery. Nếu một chương không học xong trước giới hạn, run có thể kết thúc tại đó và vẫn không re-entry. Mệnh đề không phụ thuộc lowest-Elo tie order, item tie order, latent profile hoặc độ chính xác của response predictor. Với ba chương, số switch không vượt2 trong điều kiện này, nhưng không buộc bằng2.

## 3. Điều kiện đủ rộng hơn cho graph có cạnh liên chương

Một điều kiện đủ là khi lần đầu chọn vào C, **mọi parent ngoài C của mọi node thuộc C đều đã mastered**. Do M_t tăng, các parent này sẽ giữ mastered. Chứng minh source trong DAG cảm sinh của bổ đề2 lại áp dụng, nên C được xử lý thành một khối duy nhất. Một topology có gateway bắt buộc trước mọi entry vào chương có thể bảo đảm điều kiện này.

Điều kiện này đủ nhưng không cần thiết cho từng đường chạy. Có thể parent ngoài chương ban đầu chưa mastered nhưng run dừng sớm hoặc thứ tự lựa chọn thực tế vẫn không quay lại. Chapter-level DAG một chiều đơn thuần cũng chưa đủ. Node đầu chương có thể ready trước gateway nằm giữa chương, khiến chương được bắt đầu rồi phải tạm rời.

## 4. GA31 prospective không có bảo đảm gateway đó

Gọi A là Mệnh đề và tập hợp, B là Bất phương trình bậc2một ẩn, C là Hàm số bậc2và đồ thị. Ba cạnh liên chương trong input ứng viên là các cạnh sau.

| Cạnh | Chương | Vị trí chặn |
|---|---|---|
| ThucHienPhepToanTrenTapHop → GiaiDuocBatPhuongTrinhBacHai | A→B | Giữa chuỗi B, sau GiaiBatPhuongTrinhBacHaiMotAn |
| GiaiThichDinhLyVeDau → VeDoThiParabolCuaHamSoBacHai | B→C | Gần cuối C |
| XacDinhTinhDungSaiCuaMenhDe → VeDoThiParabolCuaHamSoBacHai | A→C | Cùng node gần cuối C |

B vẫn có root `BatPhuongTrinhBacHaiMotAn` không cần parent A. C vẫn có root `HamSoBacHaiVaDoThi` không cần parent A hoặc B. Do đó B/C có thể được bắt đầu trước khi foreign prerequisites của toàn chương được đáp ứng. Mastered set tăng và graph không có cycle vẫn không loại trừ việc re-entry.

Có hệ quả cụ thể cho **lựa chọn tie order prospective đang được triển khai**. `domain.py` dòng81 tạo lexicographic topological order riêng cho mỗi graph, và dòng171–172 trả về cả hai order. Nếu dùng order này với controller primitives và khởi tạo toàn bộ estimate1200 theo US/UW của PDF, ba root đầu chương đều ready, cùng Elo, và root B có tên đứng trước root C rồi root A. Controller sẽ bắt đầu ở B. Khi các node B có thể học trước foreign prerequisite đã mastered, node B còn lại bị chặn bởi A chưa được thực hành, nên phải rời B trước khi B hoàn tất. Bất kỳ phần tiếp diễn nào hoàn tất toàn bộ graph sau đó đều phải quay lại B. Với khởi tạo FW, root C có estimate1050 nên C bắt đầu trước và có thể bị chặn gần cuối bởi A/B chưa mastered theo cùng lập luận.

Đây là suy luận cấu trúc về API/input ứng viên và tie-order đã khai báo, chưa là trace mới hoặc kết quả500bước. Một run có thể hết ngân sách trước lúc bị chặn hoặc trước lúc quay lại. Không dùng hệ quả này để sửa hoặc phủ nhận kết quả finite-run trong PDF. Prospective reuse chưa xác nhận historical bytes hoặc historical fixed traversal order của các run PDF.

Để thấy tồn tại continuation hoàn tất về mặt thuật toán, có thể xét nhánh mọi đáp án đều đúng. Khi một node chưa mastered được chọn, K≥16 và P≤elo_probability(1250,1050)<1, nên mỗi update tăng ít nhất một hằng số dương. Mỗi node sẽ vượt τ sau hữu hạn lần chọn. DAG luôn có ready node nếu còn node chưa mastered. Nhánh này hoàn tất graph sau một số bước hữu hạn, nhưng không chứng minh nó nằm trong ngân sách500, cũng không đưa ra xác suất hoặc tần suất re-entry.

## 5. Phản ví dụ nhỏ và trường hợp mất giả thiết

Fixture nguồn hiện có dùng a1 thuộc A, b1 thuộc B và a2 thuộc A, với a1→b1→a2. Estimate ban đầu a1=b1=1249, a2=1200. Đáp án đúng đưa a1 vượt τ, b1 được mở rồi vượt τ, sau đó a2 được mở. Chuỗi chương A→B→A có một re-entry dù continuity luôn được tuân thủ. Đây là phản ví dụ tổng quát có cạnh liên chương, không phải graph GA31 và không phải run PDF.

Nếu bỏ continuity, ngay cả graph toàn cạnh nội chương cũng có thể xen kẽ chương theo global lowest-Elo. Nếu cho forgetting hoặc cập nhật các node đã mastered, chương đã hoàn tất có thể mở lại. Nếu graph có cycle hoặc sửa ready để cho phép action ngoài ready, bổ đề source/ứng dụng Eq.(3) không còn đủ. Các trường hợp này phải giữ tách khỏi hợp đồng primitives hiện hành.

## 6. Ý nghĩa nghiên cứu và kiểm chứng tối thiểu có thể làm sau

Zero re-entry của B1 trong hợp đồng trên có lời giải thích bằng invariant của controller và topology. Nó không xác nhận graph phức tạp hơn học tốt hơn hoặc concept mastery ước lượng là mastery thật. GA cần diễn giải finite-run theo topology, entry order, trạng thái và ngân sách cụ thể. Kết quả PDF về continuity vẫn là kết quả được kế thừa, còn chứng minh điều kiện đủ này làm rõ phạm vi cơ chế.

Các fixtures bổ sung nếu Root muốn kiểm chứng sau, chưa được viết/chạy ở đây.

- DAG nội chương có nhiều nhánh và estimate ban đầu gồm cả node đã mastered và chưa mastered. Đáp án sai làm Elo chưa mastered giảm, nhưng mỗi chương vẫn chỉ xuất hiện một khối.
- Gateway ngoại chương đã mastered trước entry. Chương có cạnh ngoài nhưng vẫn được hoàn tất thành một khối.
- Gateway giữa chương chưa mastered. Kiểm trạng thái ready trước/sau khi chương tạm cạn, rồi mở lại sau chương parent.
- GA31 prospective với root B hoặc root C được chọn đầu theo hai kiểu khởi tạo đã nêu. Kiểm structural stall/foreign prerequisite bằng state khai báo, giữ riêng câu hỏi eventual completion và giới hạn500bước. Không cần seed search hoặc chạy ma trận để kiểm mệnh đề logic này.

Không có execution mới, tỷ lệ thực nghiệm mới, inference quần thể hay tuyên bố lợi ích học tập trong ghi chú này.
