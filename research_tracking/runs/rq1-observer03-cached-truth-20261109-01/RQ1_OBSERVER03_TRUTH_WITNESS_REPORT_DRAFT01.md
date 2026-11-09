# RQ1 — đối chiếu quyết định thành thạo tại các câu được chọn trong một lịch sử PG

**Bản draft kỹ thuật ngày 09/11/2026.** Phân tích mô tả từ bằng chứng đã lưu, chưa xuất bản canonical. Một lịch sử được dùng lại, không có người học, thế giới hay mô hình mới. Nguồn mới hiện ở vùng chuẩn bị P và cần được ghim vào bundle trước khi công bố.

## Vì sao cần phép đối chiếu này?

Trong pipeline Paper2, dự báo trả lời đúng, trạng thái ước lượng và kết luận thành thạo phục vụ những vai trò khác nhau. Xác suất trả lời đúng còn phụ thuộc câu hỏi và các thành phần memory/context. Kết luận thành thạo native lại yêu cầu đồng thời theta ước lượng đạt 1250 và stored pi_task không vượt 0,55. Vì vậy dự báo tốt hoặc thay đổi xác suất chưa tự chứng minh kết luận thành thạo khớp năng lực của thế giới mô phỏng.

Phép kiểm RQ1 này đặt một câu hỏi hẹp. Tại chính khái niệm đang được hệ thống đưa ra luyện tập, trước khi dùng đáp án hiện tại để cập nhật, kết luận native M có trùng tiêu chí latent theta_before≥1250 của simulator hay không? Đây là tiêu chí do thế giới mô phỏng định nghĩa. Nó chưa là thước đo thành thạo của người học thật hoặc độ calibration của một xác suất.

## Quần thể và cách ghép

History được chọn trước từ pilot observer03, với seed 21000, profile PG, hai cờ graph_on=False và mechanism_on=False. Nhánh này tắt signal/parent adaptation và local adaptation của estimator. Controller vẫn dùng đồ thị 31 cạnh cùng quy tắc prerequisite/exposure. Tên gOFF trong pilot không mô tả một controller hoàn toàn graph-free.

Trong cặp đối chứng này, ON/OFF chỉ việc bật/tắt observer; cấu hình graph_on=False giữ nguyên ở cả hai. Phân tích dùng 120 readout ON một lần. OFF chỉ kiểm cùng readout khoa học và initial/final state, không tăng thành 240 mẫu. Trước khi lấy history này, strict reader kiểm toàn bộ gzip gốc tới EOF/CRC, đủ 14.400 rows của 120 histories và đúng manifest/grid. Con số 14.400 là phạm vi kiểm nguồn cache, không phải số native readout được đối chiếu latent trong kết quả dưới đây.

Khóa ghép gồm seed/profile/hai cờ/step 0–119 và đầy đủ concept/question/difficulty qua bank. P phải trùng từng bit, timestamp phải đúng clock nguồn UTC với bước 6 giờ và các khoảng 72 giờ. Native readout được capture sau select/predict và trước update(y). Stored pi dùng cho gate được giữ riêng với decayed pi. Các predicate được tính lại bằng so sánh inclusive binary64, không làm tròn hoặc thêm epsilon trước phân loại.

## Kết quả tại 120 lượt đang được phục vụ

Bảng giữ cả những ô bằng0. Đơn vị là khái niệm–thời điểm của câu được chọn, với một history lặp theo thời gian.

| Kết luận native M | Latent chưa đạt 1250 | Latent đạt 1250 |
|---|---:|---:|
| Chưa công nhận thành thạo |0|120|
| Công nhận thành thạo |0|0|

Bảng chỉ dùng theta_gate, bỏ riêng chốt stored pi khỏi predicate trên cùng các trạng thái đã lưu, cũng có 120 hàng ở ô estimatorFalse/latentTrue. Có 0 hàng theta đã đạt nhưng pi chặn thêm, ở cả nhóm latentTrue và latentFalse. Như vậy trong 120 dòng này, theta ước lượng chưa đạt mốc đã đủ làm M=false. Kết quả không quy phần bất đồng này cho chốt uncertainty. Pi vẫn ảnh hưởng predict, update và mastery_score, nên con số 0 không chứng minh uncertainty vô tác dụng đối với toàn bộ quỹ đạo.

Crosscheck độc lập xác nhận history phục vụ 22 khái niệm khác nhau và cả 22 đã latent-positive ở lần thực hành đầu tiên. First-visit analysis là kiểm cơ chế sau khi xem kết quả, không thêm một xác nhận độc lập. Ví dụ step 0 có theta_est = 1200 và theta_before ≈ 1381,46, trước cập nhật đầu tiên. Số làm tròn này chỉ minh họa; phép phân loại dùng giá trị binary64 nguyên bản.

## Vì sao phải đọc cùng bộ chọn bài và khởi tạo?

Selector ưu tiên những khái niệm mà chính estimator chưa công nhận thành thạo. Trong nguồn Paper2, ready_set bắt đầu từ unmastered. Nhánh ready bình thường và nhánh fallback theo số prerequisite chưa giải quyết đều chỉ lấy từ tập này khi chưa all-mastered. Sau đó selector cân bằng số lượt và ưu tiên mastery_score thấp; chapter chỉ là một khóa phá hòa. Do đó các state xuất hiện trong bảng đã chịu điều kiện chọn bài. Không thể gọi 120 bất đồng này là độ chính xác toàn cục bằng0 hoặc suy ra sensitivity/specificity trên mọi state.

Cũng không có định lý mọi câu được chọn đều M=false. Khi all-mastered, ready_set trả toàn bộ nodes. Spaced-review escape còn có thể chọn một khái niệm đã mastered bên ngoài frontier nếu các prerequisite đủ điều kiện. Hơn nữa, unmastered có thể là theta≥1250 nhưng pi>0,55. Selector không bắt buộc theta_gate=false. Theta_gate=false cả 120 là kết quả thực của các state đã được chọn trong history này.

Mặt latent-positive chịu ảnh hưởng của initialization. PG có mức trung bình nguồn 1400 cùng nhiễu global/chapter/node và tương quan theo graph; nhãn PG không bảo đảm mọi khái niệm ở mọi seed đều vượt1250. Estimator lại khởi đầu theta 1200 chung cho các profile. Trong history đang xét, cả 22 khái niệm được phục vụ đều đã vượt ngưỡng latent ở lần đầu xuất hiện, trong khi theta_est lần đầu vẫn là prior 1200.

Nguồn world chỉ cập nhật khái niệm đang được thực hành. Trước lần đầu đó, theta_before bằng base của khái niệm. Về sau theta_at bằng base cộng phần gain không âm đã decay, với cap 1600 lớn hơn miền base tối đa 1500. Vì thế năng lực latent không giảm dưới base trong recipe này. Kết hợp 22 first-visits đã positive, tập 22 khái niệm được phục vụ vốn đã thuộc lớp latent-positive từ đầu. Bảng không quan sát một quá trình world chuyển từ chưa thành thạo sang thành thạo trong 120 lượt này. Sáu khái niệm còn lại trong domain 28 không được suy trạng thái từ bảng này.

Native theta cũng là một thành phần của biểu diễn cùng memory/features. Cùng đơn vị Elo chưa làm nó đồng nhất với tham số latent của world. Witness cho thấy kết luận native và tiêu chí latent không thể thay thế nhau một cách mặc nhiên tại các câu đang được chọn; chưa đánh giá toàn bộ chất lượng trạng thái hay lợi ích học tập.

## Bằng chứng còn cần và ưu tiên tiếp theo

Chạy lại native readout cho toàn bộ 14.400 câu đã được phục vụ có thể mở rộng mô tả theo profile/arm. Tuy nhiên, mỗi nhánh vẫn tự chọn câu từ trạng thái của nó. Phép mở rộng query-only này có giá trị hạn chế nếu câu hỏi chính là chất lượng toàn bộ trạng thái hoặc mastery classification độc lập với selector. Nó không tự giải quyết điều kiện chọn mẫu vừa thấy, và chưa cần blind rerun chỉ để tăng số hàng.

Hướng kiểm phù hợp hơn trong main research là một panel concept–time cố định, được ấn định độc lập với M/mastery_score, có cùng native theta/pi/M và latent world theta tại đúng các thời điểm đó. Có thể cân nhắc toàn bộ 28 khái niệm ở một số mốc khóa trước, giữ full coverage và báo riêng kết quả tại served queries. Việc có latent vector tương ứng phải có nguồn hoặc reconstruction đã kiểm, không giả định current 120 readouts chứa sẵn truth cho unserved concepts.

Đây là đề xuất cần review trong hợp đồng nghiên cứu chính, chưa là thay đổi phương pháp đã được phê duyệt. Không đổi threshold, selector, profile, cơ chế học hoặc các RQ từ witness này. Độ calibration của quyết định/reference criterion và chất lượng trạng thái tổng quát vẫn mở. Không có graph comparison, learning-gain effect, suy luận người học thật hoặc RQ completion từ kết quả này.

## Dẫn số liệu và nhánh nguồn

P là `artifacts/akt/local-tests/akt-research-runner-20261108-01`. Các JSON pointers dưới đây chỉ dữ liệu đã nghiệm thu, draft này không chạy script hoặc tổng hợp lại cache.

| Phát biểu | Artifact và JSON pointer |
|---|---|
| Một history, 120 queried rows | `observer03-truth-cached02/summary.json` `/history_count`, `/queried_concept_time_rows` |
| NativeMFalse/latentTrue=120; các ô khác0 | Cùng file, `/native_M_by_latent/01`, `/native_M_by_latent/00`, `/native_M_by_latent/10`, `/native_M_by_latent/11` |
| Theta-only cùng 120 bất đồng | Cùng file, `/theta_gate_by_latent/01` |
| Pi không chặn thêm sau theta-gate | Cùng file, `/uncertainty_suppression_by_latent/latent_true`, `/uncertainty_suppression_by_latent/latent_false` |
|22 served concepts, 22 first-visits đã positive | `observer03_truth120_independent_crosscheck01.json` `/first_visit_analysis/observed_concepts`, `/first_visit_analysis/latent_positive_first_visits` |
| First-visit scope là post-hoc | Cùng crosscheck, `/first_visit_analysis/kind` |
| Ví dụ step 0 | `observer03-truth-cached02/joined120.json` `/0/theta_est`, `/0/simulator_theta_before` |
|14.400 cache rows/120 histories admit trước summary | `observer03-truth-cached02/validation.json` `/cache_rows`, `/cache_histories`, `/status` |
| ON một lần, OFF integrity | Cùng validation, `/ON_used_once`, `/OFF_integrity_only` |
|0 new model/world và new independent N = 0 | `observer03-truth-cached02-owned/final.json` `/actual_model_calls`, `/actual_world_calls`, `/new_independent_N` |

Nguồn thuật toán là notebook Paper2 SHA353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f. Codecell 11 (chỉ số JSON từ 0) chứa CoverageAwareSelectorMixin.ready_set/select. Codecell 13 chứa MemoryState/GAMKTPolicy.is_mastered/mastery_score/predict/update. Cell chứa persona_base_abilities và LatentStudentEnvironment xác định prior PG, concept-local update và theta_at≥base. `paper2_reference.py:60–96` giữ controller namespace và selector class; `simulator_pathways.py:7–39` tách S/P/L. Pilot `pilot_rq1_cpu09_targeted_observer03.py:546–564` dùng S=P=L=False và predict→capture→update. Analyzer `analyze_observer03_cached_truth01.py:59–113,118–139,145–203` kiểm OFF/ON, join/predicates và summary sau full cache admission.

Các SHA chính đã đối chiếu gồm joined120 `051787b3bde6283b3586cc484a204dce97f00c49f80283c7943a44cfd4a02928`, summary `34efc4b3710ebaa31d37c8f4d90dd99abafb34492608c5aad30e792fa8144fae`, validation `df69c3037c89b801ccdababcdccc893099c6c62ffac5ffbd021cfec471ac3667`, actual outer `32042e63144f36cec7acff18e30b62657fe528a4bbf137de608227cf0a25cebe`, independent crosscheck `c7fe8ef08411f78e5f971040d98b271b08ba15937a3adcb6ffd37fd622c64676`.

Actual cached02 hoàn tất trong outer stored 0,9906307999626733 giây, giữ Job0/source-input before–after. Lượt cached01 trước đó dừng vì bộ đo tạo retained ctypes types; failure/probe/fix và các pure runs được lưu riêng. Crosscheck độc lập ban đầu dừng do header CSV UTF-8 BOM, source trước sửa được giữ và dữ liệu canonical không đổi; số trong draft lấy từ crosscheck verified sau sửa. Những hồ sơ vận hành này không tăng quần thể hoặc làm bằng chứng học tập. Bundle mới do ROOT đóng sau review; draft không tự điền manifest chưa có.