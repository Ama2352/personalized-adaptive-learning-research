# GKT research data — cầu dữ liệu và normal import đã kiểm

Ngày09/11/2026. Phạm vi engineering, không kết quả nghiên cứu RQ3 hoặc baseline đã fitted. Canonical dự kiến `research_tracking/reports/gkt_research_data_readiness_20261109.md`. Bundle dự kiến `gkt-research-data-engineering-20261109-01`; chỉ coi đã đóng khi manifest thực và verify thành công. Báo cáo candidate này không tự cấp quyền closure/training.

## Thành phần đã hoàn thiện

`gkt/research_data.py` nối PublicResearchCorpus đã được reader audit với bốn phase select_train80/raw_selection10/refit_union90/calibration_predict. Tái dùng ResearchPhaseData, encoding/support, canonical scoring targets và observable-prefix-chain-v1 hiện có. View không giữ whole corpus; vẫn giữ phase có nhãn đúng vai trò để trusted orchestrator tách predictor/loss. Không đọc oracle, final events hoặc source paths từ payload.

Phân biệt registry công khai84items→28concept với item vocabulary chỉ từ optimization. Mỗi concept có ba difficulty1050/1200/1350, node order và expert DAG bind bank-domain/topology SHA/TRAIN80 shard. Refit dùng encoding90 mới cùng freeze; graph giữ TRAIN80 lineage. Metadata graph không chứng minh file đã nạp hoặc graph đã fit.

Iterator giữ mọi target/query/learner/source_row/global_rank và canonical history hash. Predictor nhận full observable past, current label chỉ đi vào training wrapper hoặc truth sidecar. Current response được thêm vào past sau record hiện tại. OOV item giữ null eligibility; các target sau còn thiếu history tiếp tục unsupported_history, không reset rồi chấm như full-prefix. Expanded-prefix cost O(sum rank) có cap trước first yield, chưa benchmark throughput.

Không chọn recurrence/hyperparameters, thêm difficulty embedding hoặc gỡ giới hạn toy GKT cũ. Cùng concept/state có thể dùng chung node response cho ba item theo contract được disclose; data bridge chưa chứng minh model/reference parity.

## Vì sao cần sửa package initializer

`gkt/__init__.py` trước đây import core ngay, kéo Torch khi gọi normal data import. Sau Root review, chỉ đổi package dispatch. Hai config exports giữ eagerly, năm core exports được nạp/cached khi dùng, đúng danh sách bảy tên public cũ. Unknown name vẫn AttributeError. Core/config/numerical equations giữ SHA cũ.

Ba unit cases bổ sung kiểm exact __all__/config identity, unknown name và lazy cache với temporary explicit core stub có restore. Đây là kiểm package dispatch, không native kernel proof. Data import đã qua normal `knowledge_tracing.gkt.research_data`; không tạo package/sys.modules giả để né dependency.

## Ba lượt kiểm được giữ đúng lịch sử

| Lượt | Kết quả actual | Outer stored elapsed | Giới hạn |
|---|---|---|---|
| Candidate01 |17methods,16PASS/1ERROR,0FAIL/skip |4,383052825927734s |30swhole/24sowned/20sworker,cleanup3s |
| Candidate02 |17methods,17PASS/0FES |2,330407900037244s |Cùng caps |
| Canonical normal03 |20methods,20PASS/0FES |2,543837999983225s |Cùng caps |

Lỗi01 nằm ở test bank sai, public validator đã từ chối ngay trong fixture trước assertRaises cũ. Derivative02 đặt assertRaisesRegex quanh genuine boundary, không tạo corpus giả để lách guard. Module data1650 không đổi giữa các lượt. Không đổi16PASS/1ERROR thành17PASS hoặc cộng các lượt lặp thành54cases độc lập. Bộ canonical hiện có17data cases và3package cases.

Root báo terminal tương ứng khoảng4,4s/2,3605s/2,5726s, khác scope với stored outer durations. Không cộng nested worker/owned/outer thành tổng runtime. Cả ba lượt đã terminal, Job active0 và cleanup accepted, source trước/sau khớp. Actual normal03 có29source/history/config pins ổn định, family peak61.083.648bytes, min available2.506.932.224bytes, monitor stopped và platform display fixture đã restore. Caps là RSS512MiB/free1536MiB; prelaunch floor2GiB giữ nguyên.

Wrapper dùng genuine Windows owned Job, no-Torch/model/cloud/process/network/protected-data audit, monitor sampled0,1s và guard mỗi case. NumPy là data dependency, không claim stdlib-only import graph. Display metadata fixture lấy actual WinAPI version để không tạo metadata subprocess. No model/optimizer/teacher/actual corpus publication trong cả ba lượt. Sampled monitor và cooperative Python timer không phải OS RAM quota tổng quát; native owned deadline/cleanup là bằng chứng riêng.

[Raw01](../runs/gkt-research-data-engineering-20261109-01/attempt01__outer_final.json), [raw02](../runs/gkt-research-data-engineering-20261109-01/attempt02__outer_final.json), [raw03](../runs/gkt-research-data-engineering-20261109-01/attempt03__outer_final.json) giữ counters/counts, resource và source maps. Logs từng lượt được giữ cùng namespace trong bundle, không rerun để làm evidence.

## Apply và provenance

Root áp ba payload bằng helper04 dùng atomic replacement cho initializer cũ. Trước mutation có inventory SHA và raw snapshot initializer90c9; hai file canonical mới ghi độc quyền, đọc lại tất cả. Receipt apply chỉ nói applied/not runtime tested; kết quả normal03 sau đó mới chứng minh đường public import. Helper03 source-only cũ và preparer tạo helper04 được giữ để truy vết thay đổi write semantics.

Ba canonical SHA hiện hành là data `1650509a3e0baaf91504355e67d4c1857ac2e020071d8f7463ea53887ac65873`, tests `e426e42e82c34319ed04214c2248656b08c94e60eaf52579188a22650de41b89`, initializer `80fd45e6176831f00be7496b1549d3a98485d6b1addd26113130e3c1fcd7fd3f`. Core4663/config8785 chỉ tham chiếu SHA, không nhân đôi dependency/runtime/corpus. [Apply receipt](../runs/gkt-research-data-engineering-20261109-01/apply04__receipt.json), [review độc lập](../runs/gkt-research-data-engineering-20261109-01/independent_review01.md).

## Giới hạn quan trọng cho exporter tiếp theo

Shared sidecar có trường thật `ResearchScoringTarget.trained_item`, chỉ nói current item có trong train vocabulary. Sau OOV, current item có thể trained_item=true nhưng input.eligible=false vì unsupported_history. Exporter/metric phải dùng actual eligibility/support_reason của input, giữ toàn population và null. Không đổi item-support thành fitted-valid mask hoặc latent mastery.

Fixtures dùng đúng typed PublicResearchCorpus nhưng observable dựng tay, fake SHA được ghi rõ metadata-only.10Development learners8/1/1×4events, bank28/84 nhưng chỉ hai items được TRAIN quan sát. Chúng không qua disk reader/publication, chưa đủ84support cho research run, không chứng minh trained vocabulary hoặc fitted checkpoint.

GKT research epoch/optimizer/checkpoint, selected-only export, external freeze→fresh refit/calibration và fitted OnlineSession còn thiếu. Current adapter/trainer engineering caps giữ nguyên. Main matrix chín điều kiện, Junyi mapping, model efficacy và RQ3 chưa hoàn tất từ gói này. Không có lý do cập nhật human report như một phát hiện nghiên cứu mới.
