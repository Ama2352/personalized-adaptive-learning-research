

## 11. Bổ sung E8 về trường hợp đồ thị đổi đường đi nhưng giữ kết quả cuối

### Từ cùng 172 lượt đến câu hỏi về cấu trúc bộ mô phỏng

Phần 8 đã xác định điều kiện mà controller tự bảo đảm không quay lại chương. Cần kiểm tiếp liệu sự bằng nhau về số lượt và trạng thái cuối, khi hai đồ thị cho đường đi khác nhau, có thể suy ra từ phương trình đang dùng hay phải đo lại trên từng nhóm người học.

Một lượt kiểm tích hợp Paper1 đã lưu cung cấp tình huống cụ thể. Trên cùng một hồ sơ US với seed 42 và cùng profile/tape phản hồi, B1 và GA đều dừng sau 172 phản hồi với 28/28 khái niệm được controller đánh dấu thành thạo. B1 không quay lại chương, còn GA quay lại 2 lần. Latent cuối của từng khái niệm có cùng identity giữa hai nhánh. Đây là một witness engineering của phiên bản prospective, không phải kết quả matrix hoặc khôi phục random draws lịch sử của PDF. Hai nhánh cũng khác cả các cạnh bổ sung và traversal order, nên quan sát này chưa tách riêng cross-edge effect. [E8a]

### Mệnh đề có điều kiện về quỹ đạo của từng khái niệm

Trong source Paper1 đang xét, graph và chapter continuity quyết định khái niệm nào được chọn. Khi khái niệm đã được chọn, item gần estimate nhất được lấy theo estimate và số lần dùng item của chính khái niệm đó. Controller chỉ cập nhật estimate của khái niệm vừa hỏi. Hệ số K phụ thuộc số lượt đã luyện khái niệm ấy. World cũng chỉ đổi latent của khái niệm vừa hỏi, theo quy tắc tăng 12 và cap 1500. Đáp án được sinh từ latent của khái niệm và difficulty item, không từ việc khái niệm khác vừa được học. [E8b]

Giữ cùng bank, trạng thái ban đầu, item tie rule và tape phản hồi theo cặp **khái niệm–số lượt luyện cục bộ**. Không thêm forgetting, thời gian chờ, transfer hoặc cập nhật xuyên khái niệm. Cho phép DAG và thứ tự duyệt khác nhau. Khi đó, tại lần luyện thứ n của một khái niệm, hai nhánh có cùng item, xác suất, đáp án và local state trước/sau. Lập luận đi theo quy nạp. State ban đầu giống nhau. Cùng local state xác định cùng item. Cùng item và uniform cục bộ xác định cùng đáp án và update, nên local state kế tiếp tiếp tục giống nhau.

Nếu cả hai nhánh hoàn thành mọi khái niệm, mỗi khái niệm dừng tại cùng lần đầu estimate đạt 1250. Gọi số lần đó là N_c, bằng 0 nếu đã đạt từ đầu. Khái niệm đạt ngưỡng bị loại khỏi ready và không được cập nhật tiếp. Do đó, tổng số phản hồi của mỗi nhánh bằng Σ_c N_c, và terminal estimate, latent, local item exposures giống nhau. Global interleaving, chapter switches và re-entry vẫn có thể khác. Với finite DAG, ready rỗng tương đương mọi khái niệm đã đạt ngưỡng dưới các quy tắc này. Mệnh đề không giả định mọi tape/horizon đều đủ để hoàn thành. [E8b]

Sự bằng nhau ở witness 172 lượt vì vậy phù hợp với một hệ quả cấu trúc có điều kiện. Thứ tự và re-entry có thể đổi trong khi các quỹ đạo cục bộ hoàn tất vẫn được bảo toàn.

### Finite horizon và cap xác định ranh giới của kết luận

Sáu fixture xác định đã kiểm qua public core, gồm hai DAG complete có đường A→B và A→B→A, trường hợp có đáp án sai, history dài đi qua các mức K và đổi difficulty, cùng các đối chứng finite horizon. Cặp complete giữ exact local prefixes, stopping counts, exposures và final states dù thứ tự khác. Các fixture finite horizon giữ local prefixes chung nhưng có allocation và final states khác khi dừng trước completion. [E8c]

Một phản ví dụ dựng tay dùng hai khái niệm có latent đầu 1498 và 1200, cùng một phản hồi. Nhánh hỏi khái niệm đầu chỉ tăng 2 vì chạm cap. Nhánh bị prerequisite chặn khái niệm đó và hỏi khái niệm còn lại tăng 12. Đây là **tổng latent gain** của fixture, không phải mean mastery, phần trăm học tập hoặc kết quả trên học sinh thật. Nó cho thấy allocation tại finite horizon cùng cap có thể làm endpoint khác nhau. [E8c]

Đối chứng bổ sung kiểm trường hợp không update nào bị cap. Dù allocation và số đáp án đúng khác nhau, mỗi phản hồi vẫn tăng latent đúng 12, nên cùng N phản hồi cho cùng tổng net gain 12N. Như vậy, finite horizon riêng lẻ chưa đủ để suy ra khác biệt tổng gain. Cap cũng không phá mệnh đề complete nếu mỗi khái niệm vẫn nhận cùng N_c. Đây là hai ranh giới khác nhau của cùng implementation.

Sáu fixture mới nằm trong lượt 91 tests đã đạt, gồm cả 85 hồi quy trước đó. Các con số này là đơn vị kiểm implementation, không phải người học hoặc replicate nghiên cứu. Trần 13 episode calls/464 feedback suy từ horizon của fixture không được đổi thành measured interaction ledger. Việc nối E8 không chạy thêm mô hình, sinh đáp án hay tăng cỡ mẫu độc lập. [E8c]

### Phạm vi đóng góp cho RQ1 và RQ2

E8 bổ sung một lời giải thích cho khoảng cách giữa thay đổi lựa chọn và thay đổi kết quả cuối. Trong một simulator có cập nhật độc lập theo khái niệm và được học đến cùng local stopping rule, graph có thể chỉ đổi interleaving. Số lượt hoặc terminal gain bằng nhau trong phạm vi đó không tự đo chất lượng dự báo, độ đúng của mastery hoặc hiệu quả của graph ở môi trường có dynamics khác.

Coupling theo concept/local count là lựa chọn prospective đã được khai báo. Đổi sang tape gắn global step có thể làm responses khác pathwise khi thứ tự đổi, nhưng chưa tự chứng minh marginal-distribution effect nếu transition law và iid noise giữ nguyên. Các world có prerequisite-dependent learning, forgetting/spacing, cross-concept transfer hoặc finite-budget allocation cần được kiểm riêng. Không thêm các cơ chế đó chỉ để tạo effect, không suy Paper1 PDF mâu thuẫn, và không quy các kết luận này sang Paper2 hoặc người học thật. [E8b]

Phần này thu hẹp cách diễn giải một equality đã quan sát. Nó chưa trả lời toàn bộ graph-quality×ability matrix, chưa là kết quả fitted CG-AKT và chưa hoàn tất RQ1/RQ2.

### Nguồn bổ sung E8

- **E8a** dùng [witness domain28](paper1_seeded_domain_smoke_readiness_20261109.md) và [result của hai episode đã lưu](../runs/paper1-seeded-domain-smoke-engineering-20261109-01/scientific__result.json).
- **E8b** dùng [chứng minh điều kiện](paper1_concept_local_invariance_20261109.md), [source primitives đã đóng](../runs/paper1-pdf-primitives-engineering-20261109-01/simulator.py), [supplied episode](../runs/paper1-supplied-episode-engineering-20261109-01/episode.py) và [recipe coupling](../runs/paper1-seeded-episode-engineering-20261109-01/seeded_episode.py).
- **E8c** dùng [sáu fixture đã chạy](../runs/paper1-concept-local-invariance-20261109-01/test_concept_local_invariance.py) và [receipt91tests](../runs/paper1-concept-local-invariance-20261109-01/result.json). Source map phân biệt JSON pointers của measurements, expected values trong assertion đã đạt và các lập luận có điều kiện từ source.
