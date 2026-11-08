# RQ1: tái dựng các bước lọc ứng viên để giải thích lựa chọn khái niệm

## Kết quả chính và phạm vi

Trên cùng **1.080 snapshot pairs** của phép so full–empty đã lưu, có thể tái dựng quy tắc chọn bài mà không chạy lại mô hình. Cả **2.160 ready memberships và2.160CID** của hai nhánh đều khớp nguồn/cache. Kết quả phân biệt ba tình huống:4cặp có khác biệt ở tập ứng viên bị bộ lọc cân bằng loại khỏi tập cuối;51cặp có tập cuối khác nhau nhưng vẫn cùng khái niệm thắng;17cặp đổi khái niệm thắng trong cùng tập cuối. Đây là **giải thích quyết định CID theo source**, không C/B được observer ghi trực tiếp, không causal mediation hoặc lợi ích học tập.

Nguồn fixed runner đã phục hồi từ Git `e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a`. Không gán hạn chế thiếu runner của nhánh closed-loop khác sang fixed-stream này. Không thêm learner, seed, trajectory, model call hoặc independentN. Bundle mới dự kiến `rq1-fixed-controller-candidates-20261109-01`; báo cáo freeze trước closure, manifest/chỉ mục sau đóng mới xác nhận integrity archive. Các đường dẫn bundle mới dưới đây được chuẩn bị theo copy aliases và chỉ materialize khi ROOT đóng gói.

## Vì sao phép đo mới làm rõ hơn bảng R/preview?

[Cross-ready trước](rq1_cross_ready_membership_20261109.md) chỉ xác nhận55lầnRđổi/previewgiữ và17lầnpreviewđổi khiM/Rgiữ. R là tập cho phép đã ghi, chưa là tập ứng viên thực sự được xếp hạng. Source tiếp tục lọc anti-repeat/escape thành **C**, rồi chỉ giữ candidates có visits≤minvisits+1 thành **B**. Khái niệm được chọn bằng khóa `(native S, chapter tie, visits, CID)` trên B; sau đó mới chọn question/difficulty.

Cache có28native S scores, mastered booleans, R, previewCID và query prefix. Original bookkeeping chỉ tăng theo **logged query CID sau snapshot**, không theo preview; vì vậy visits/recent/current chapter có thể tái dựng chính xác từ quá khứ chung, không dùng y hiện tại/tương lai. Native S chỉ đọc estimator state/features và không đọc selector bookkeeping, nên score đã lưu đủ cho khóa CID trên deepcopy trước bookkeeping. Không gọi `select`, `mastery_score`, `predict`, `update` hoặc teacher thêm lần nào.

Controller graph vẫn là graph đầy đủ ở cả hai nhánh; empty chỉ là estimator edge set. Analyzer tái dựng cả frontier, all-mastered/min-deficit fallbacks, anti-repeat/escape, visits balance và thứ tự ties theo source. R trong legacy là frozenset nên **chỉ kiểm observed membership**, không tuyên bố observed-order parity. CID phải khớp cả legacy action lẫn sidecar preview ở toàn2160snapshots; không điền hidden state nếu mismatch.

## Bảng toàn bộ tình huống, không phễu nhân quả

| B — tập cuối sau lọc | CID giữ nguyên | CID thay đổi | Tổng |
|---|---:|---:|---:|
|Giữ nguyên|1.007|17|1.024|
|Thay đổi|51|5|56|
|**Tổng**|**1.058**|**22**|**1.080**|

Đây là B×CID, khác bảng R×full-preview1003/17/55/5 trước đó; không sửa hoặc thay số của bảng cũ. Toàn bộ22full-preview changes cũng có CID thay đổi; item/difficulty-only changes=0trong mẫu này. Không vì vậy nhận dạng được quy tắc chọn question/difficulty từ S; phép tái dựng chỉ chấm CID.

Chữ ký theo thứ tự **M/R/C/B/CID**:

| Chữ ký | Số cặp | Diễn giải mô tả |
|---|---:|---|
|00000|973|Cả năm đầu ra giữ nguyên|
|00001|17|M/R/C/B giữ, CID đổi|
|10000|30|M đổi, các đầu ra còn lại giữ|
|11100|4|M/R/C đổi, B và CID giữ|
|11110|51|M/R/C/B đổi, CID giữ|
|11111|5|Cả năm đầu ra đổi|
|26chữ ký còn lại|0|Giữ đầy đủ zero cells trong summary|

- Trong60cặpRkhác nhau, C cũng khác ở cả60; **Rchanges/Csame=0** không có nghĩa anti-repeat chưa từng được sử dụng trong từng nhánh.
- Trong60cặpCkhác,4cặp cho B giống nhau sau quy tắc cân bằng visits. Đây là vị trí loại khác biệt membership ở phép xử lý tập cụ thể, không một ước lượng tác động giáo dục của bộ lọc.
- Trong56cặpBkhác,51cặp vẫn có cùng CID là native minimum trong cả hai tập. Pool thay đổi chưa đủ đổi người thắng.
- 17cặpBgiống nhau nhưng CIDkhác có cùng visits/chapter tie context và exact native minimum ở mỗi nhánh. Khóa dựa S giải thích **lựa chọn CID tại snapshot**; không dùng nhãn “score-only causal effect”, không quy chênh lệch S về một pathway graph riêng hoặc P của câu hỏi hiện tại.

## Tất cả quỹ đạo và các trường hợp âm

| Seed/profile —120cặp mỗi hàng | Rđổi | Cđổi | Bđổi | CIDđổi | Cđổi/Bgiữ | Bđổi/CIDgiữ | Bgiữ/CIDđổi |
|---|---:|---:|---:|---:|---:|---:|---:|
|20000/PG|0|0|0|0|0|0|0|
|20000/PY|0|0|0|0|0|0|0|
|20000/PYH|0|0|0|0|0|0|0|
|20001/PG|0|0|0|15|0|0|15|
|20001/PY|0|0|0|2|0|0|2|
|20001/PYH|0|0|0|0|0|0|0|
|20002/PG|56|56|56|5|0|51|0|
|20002/PY|0|0|0|0|0|0|0|
|20002/PYH|4|4|0|0|4|0|0|

Profile totals: PG có51common-winner và15same-B/CID-change; PY có2same-B/CID-change; PYH có4balance-filtered cases. Không biến các profile thành causal ability effects.16nhóm gồm pooled,3profiles,3seedblocks và9trajectories giữ tất cả512MRCBCIDcells cùng64B×CIDcells, kể cả0. Ba seed families được tái sử dụng; snapshot pairs không là người học độc lập và không có p-value/CI mới.

## Lần bị từ chối và điều chỉnh chapter mapping

Cached01 dừng trước outputs tại guard yêu cầu chapter keys bằng đúng nodes. Loader nguồn thực tế giữ full chapter dict, sau đó lookup trực tiếp các node; bảng có28nodes,36unique chapter IDs, **0missing/8unused extra IDs**, không phải dữ liệu thiếu chương. Revision02 giữ cả36entries, native last-wins và coverage certificate, không thêm chương hoặc bỏ node. Không sửa dữ liệu hoặc các ngưỡng/ranking rules. Lần rejected01 và nguồn trước sửa được giữ riêng.

Pure14 đã chạy trực tiếp và qua owned capture trên source01; đó là cùng14methods, không28trường hợp nghiên cứu. Revision02 có18methods (14regression+4chapter-mapping cases), không tự thừa kế PASS cũ. ROOT nghiệm thu pure18 trong1,2792085s/10 và cached02 trong2,3624581s/10. Outer finals lưu elapsed trước receipt lần lượt1,2501702000154182s và2,33650909998687s; các ranh giới đo được phân biệt, không dựng raw terminal log. Owned cleanup accepted/Job0; không model/native/simulator/optimizer/newN. Kiểm thử phần mềm và lỗi admission không được đếm vào population khoa học.

## Chưa nhận dạng được

S không phải correctness probability của actual logged query, cũng chưa là calibrated mastery. GAM mastery boolean dùng `theta>=1250` và `pi_task<=0,55`; S dùng virtual concept feature tại1250, còn query P phụ thuộc question/difficulty và time-decayed uncertainty. Nhãn y của actual query không là nhãn của virtual reference. Không fit calibrator hoặc tự lấy ngưỡng P để giải thích M.

Phép tái dựng không thực hiện hybrid-pool/score interventions, không nhận dạng causal mediation, tác động giảng dạy, chất lượng từng cạnh hay lợi ích học tập. Graph edge-set contrast vẫn bao gồm các hệ quả state/update trong cùng enabled package, không direct-logit-only. Quyết định chỉ là preview, không served action. Các source-local conclusions có điều kiện vào implementation và fixed observed prefix hiện tại; không dùng cho ordinal paired comparisons sau closed-loop divergence.

## Nguồn đối chiếu

- [Full–empty immutable inputs](../runs/rq1-fixed-edge-set-contrast-20261108-01/manifest.json), manifest906d16…b044; [cross-ready](../runs/rq1-cross-ready-membership-20261109-01/manifest.json), manifest057a96…0919. Gzip/parity/source inputs được tham chiếu SHA, không copy lại vào bundle mới.
- [Summary mới](../runs/rq1-fixed-controller-candidates-20261109-01/summary.json) SHA `b74ed4cddc318053ebf4219ba2fae4ce39080c4ebe93750a06d68aa3ae9aeb57`; [event flags](../runs/rq1-fixed-controller-candidates-20261109-01/event_flags.json) SHA `1cf3ba08a6d5aff1f25d1cdd91f1aefa5fdd9578a3c1c17c7625fe7a0097942b`; [validation](../runs/rq1-fixed-controller-candidates-20261109-01/validation.json) SHA `dc71a69af1c703295a2db2791c3a78cde6c476b6165277916a21b43dafd861b9`.
- Source02 SHA566306…bd8f, testsde14d6…e55f, contractb6e27f…ef50; [caller receipt](../runs/rq1-fixed-controller-candidates-20261109-01/fixed-controller-cached02-outer__final.json) SHA `4808c8261094353ac5496bd37ae6353568a93542f05af2040f6157a753e88427` và [pure18 receipt](../runs/rq1-fixed-controller-candidates-20261109-01/fixed-controller-pure18-capture02__final.json) SHA `941efc0b6c00feae6c0f0d2978e5d6f1d103684d20df4450ed50f46c5864d603`. Source01/admission failure/old14captures và chapter-correction snapshots giữ cùng gói, không sửa raw.

Giá trị bổ sung cho RQ1 là nhận diện **quy tắc lọc và lựa chọn CID nào đủ giải thích các snapshot cụ thể**. Nó thu hẹp chỗ cần đo tiếp, không hoàn tất RQ1 hoặc chứng minh CG-AKT có lợi.
