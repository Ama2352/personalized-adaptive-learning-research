# Rà soát khoa học bản thảo cơ chế RQ1 ngày 09/11/2026

## Phạm vi và kết luận review

Đối tượng được đọc là `THESIS_RQ1_MECHANISMS_DRAFT_20261109.md` SHA `d01ac8e05cdeea70917227cb8f7b812fc46414c7a2bafb59ef722b8fd6f024cb` và `.sources.json` SHA `b1cde425a8994ea2cb9f365572fbfed029883614c424aece0378ac3f3530ddbf`, cùng ba bundle E1/E2/E3 đã đóng. Đối chiếu filesystem xác nhận cả chín SHA được khai báo trong sources.json. Các summary và independent crosscheck được đọc trực tiếp bằng công cụ đọc JSON. Số model calls, Python imports, test runs và thay đổi Git của reviewer đều bằng 0.

Các bảng, đơn vị và giới hạn suy luận chính khớp nguồn. Có một điểm P2 về cách mô tả quan hệ R→C cần làm rõ trước khi dùng đoạn này như lời giải thích đầy đủ của controller. Các nhận xét còn lại là P3 về độ rõ của văn bản đọc độc lập. Phạm vi nghiệm thu là đối chiếu nội dung draft với ba bundle, chưa bao quát toàn bộ RQ1 hoặc tính mới so với toàn bộ tài liệu nghiên cứu.

## P2 cần sửa câu mô tả R/C tại dòng 41

Cụm “tập khái niệm được phép chọn R” kết hợp với cách gọi các bước tiếp theo là lọc có thể khiến người đọc hiểu R là hard constraint và C luôn là tập con của R. Source E2 `analyze_fixed_controller_candidates02.py` dòng 82–91 có nhánh `escape_all_nodes`. Khi anti-repeat trong R hết lựa chọn, nhánh này dựng alternatives từ toàn bộ nodes đáp ứng điều kiện prerequisite rồi thay candidates bằng alternatives. Vì vậy source chỉ đảm bảo `CID ∈ B ⊆ C` tại dòng 101. Quan hệ `C ⊆ R` cần điều kiện bổ sung.

Sửa tối thiểu được đề nghị cho đoạn 41 như sau.

> Sau phân loại thành thạo, controller tính tập sẵn sàng ban đầu R theo điều kiện tiên quyết. Quy tắc tránh lặp có thể giữ hoặc thu hẹp tập này, còn nhánh thoát bế tắc có thể thay tập ứng viên bằng các khái niệm phù hợp lấy từ toàn bộ đồ thị, tạo thành C. Bộ lọc cân bằng số lượt luyện tiếp tục tạo B, rồi quy tắc xếp hạng chọn khái niệm thắng trong B.

Đề nghị này giữ nguyên các số đếm và phép tái dựng đã nghiệm thu. Review xác nhận khả năng của nhánh source, chưa đếm thêm tần suất CID ngoài R trong cohort. Những câu về bốn snapshot C khác/B giống và 51 snapshot B khác/cùng người thắng vẫn phù hợp với E2.

## Các điểm khoa học đã đối chiếu

- E1 `/groups/0` và `native_mastery_gates_crosscheck01.json` xác nhận 30.240 cặp khái niệm–thời điểm, chữ ký 000=26.722, 010=3.428 và 101=90. Ở 010, cả hai theta-gate false và chỉ empty qua pi-gate. Ở 101, cả hai pi-gate true và full qua theta-gate. Draft diễn giải phép AND đúng nguồn. Cách đếm 90 bất đồng M-set và 90 bất đồng concept-pair chỉ được đồng nhất cho cohort hiện tại. Câu ở dòng 37 giữ rõ sự lặp cùng khái niệm theo thời gian.
- E2 `/groups/0/joint_MRCBcid` có 973/17/30/4/51/5 theo đúng sáu chữ ký trình bày. `/groups/0/B_CID_cells` xác nhận 51 tập B khác/cùng CID và 17 cùng B/khác CID. C/B được tái dựng theo source, còn ready membership và CID đối chiếu cache. Dòng 19 đã thể hiện đúng khác biệt giữa dữ liệu ghi trực tiếp và kết quả tái dựng.
- E3 `/code_order` là Query-M, raw criterion, CID. `/groups/pooled/cells` và independent_crosscheck cùng cho 1033/20/20/2/5/0/0/0. Bảng hai chiều trong draft gộp Query-M nên ô 1.038 gồm 1.033+5. Hai tập 22 chỉ giao hai snapshot. Cả năm Query-M disagreements nằm ở ô 100, tách khỏi CID disagreements trong population đã ghép.
- Full–empty thay estimator-edge input trong cùng graph package, giữ controller graph. Câu tại dòng 15 phân biệt đúng với graph-free. Draft giữ điều kiện lịch sử query/y chung và preview ở dòng 21, phù hợp fixed-stream contrast.
- P_query, native score trên virtual concept feature và native M có các định nghĩa khác nhau. M dùng theta/pi qua phép AND. Dòng 27 tránh suy P_query là đầu vào trực tiếp của M cùng bước. Dòng 68 giữ khác biệt Query-M của một khái niệm với M-set của 28 khái niệm.
- Giới hạn về repeated snapshots, ba reused seed blocks, raw reference chưa temperature-calibrated và kết quả học tập chưa đo được đều hiện diện trong văn bản. Các kết luận cơ học gắn với snapshot và implementation, thay vì chuyển các chữ ký đồng thời thành ước lượng mediation.

## P3 cho bản đọc độc lập

1. Dòng 57 nên ghi ngay ba difficulty 1050/1200/1350 và tiêu chí `mean(P_raw) ≥ 0.5637150147511514`, kèm tên định nghĩa tham chiếu V1. Worker E1 dòng 28 và 66 cố định chính các giá trị này. Cách viết hiện tại để người đọc phải mở E1 mới biết boolean nào được đếm thành 22. Điều này là bổ sung định nghĩa đo, giữ nguyên ngưỡng và kết quả.
2. Dòng 51 gọi “năm đầu ra boolean” chưa chính xác về kiểu đại lượng. M-set/R/C/B là các tập và CID là định danh, còn năm cờ bất đồng mới là boolean. Đề nghị dùng “973 cặp có cả năm chỉ báo bất đồng bằng 0”. Phần còn lại của đoạn đã giữ rõ rằng score số bên trong có thể khác.
3. PG/PY/PYH, native score và fingerprint xuất hiện trước định nghĩa tiếng Việt. Nếu chương được đọc riêng, nên thêm một câu giải nghĩa hồ sơ theo source và dùng “dấu kiểm trạng thái đầu/cuối” cho fingerprint. Đây là đề nghị diễn đạt, review chưa mở lại nguồn profile để tự gán tên mới.

## Các SHA nguồn của review

Các đường dẫn tính từ repository root. Review chỉ tạo note này trong vùng prep.

| Nguồn | SHA-256 |
|---|---|
| `research_tracking/runs/rq1-prediction-mastery-trace-20261109-01/manifest.json` | `a45099f30ab6d4e239275fae6e40cf174b2dcac615fcb55a6e2b9d79f0c35ae3` |
| `research_tracking/reports/rq1_native_mastery_reference_diagnostic_20261109.md` | `5a3783d5fef1ea4e371b0fdce1fa19616d3bf04b503fe593e0607aa6afa21d27` |
| `research_tracking/runs/rq1-fixed-controller-candidates-20261109-01/manifest.json` | `cf1861ddc02105af92b64e4356ca2a816c55940e50e82415523092f27999665a` |
| `research_tracking/reports/rq1_fixed_controller_candidates_20261109.md` | `7bb2ac5a82138e48c8786077acd06ec81db742093e8d2e801566de4fd2abe747` |
| `research_tracking/runs/rq1-query-decision-overlap-20261109-01/manifest.json` | `27dff481c4f5288e26f455f75f9d8c73bcf89747e9cd8506cd9666d57c52c188` |
| `research_tracking/reports/rq1_query_decision_overlap_20261109.md` | `616cecb88a0d4d52ab0786f06baeba181001c3b07371719f0eaad73a18740de5` |
| `research_tracking/runs/rq1-prediction-mastery-trace-20261109-01/native_mastery_gates_crosscheck01.json` | `ca428a9c466a3e2a41700383e754e45e4494bbd5b90e7521dc891c69797cc573` |
| `research_tracking/runs/rq1-fixed-controller-candidates-20261109-01/event_flags.json` | `1cf3ba08a6d5aff1f25d1cdd91f1aefa5fdd9578a3c1c17c7625fe7a0097942b` |
| `research_tracking/runs/rq1-query-decision-overlap-20261109-01/summary.json` | `00baac6f2dc9aaeee0d924f1a61fa0cbc63809bf1919af1a9a161363538291dc` |
| `research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md` | `d01ac8e05cdeea70917227cb8f7b812fc46414c7a2bafb59ef722b8fd6f024cb` |
| `research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.sources.json` | `b1cde425a8994ea2cb9f365572fbded029883614c424aece0378ac3f3530ddbf` |
| `research_tracking/runs/rq1-prediction-mastery-trace-20261109-01/summary.json` | `625095a6421b050f0592e9aecfa4767690ed863d3a5489a414a7b614fb3dde38` |
| `research_tracking/runs/rq1-fixed-controller-candidates-20261109-01/summary.json` | `b74ed4cddc318053ebf4219ba2fae4ce39080c4ebe93750a06d68aa3ae9aeb57` |
| `research_tracking/runs/rq1-fixed-controller-candidates-20261109-01/analyze_fixed_controller_candidates02.py` | `56630668fbfe7175f3ae3c643f4bffa2a7e53213983778875ae349c1a08cbd8f` |
| `research_tracking/runs/rq1-query-decision-overlap-20261109-01/independent_crosscheck.json` | `f159485942353100ef6aefd2d9d64e333ffecb7b15b27c8d2c6bee68e5aaf604` |
| `research_tracking/runs/rq1-prediction-mastery-trace-20261109-01/prediction_mastery_trace_worker03.py` | `fc067d67ebc9018722aa66367fc186fe4a10e0f0b112475372f8024d4d74d631` |
