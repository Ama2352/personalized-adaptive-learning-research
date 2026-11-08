# Hiệu chuẩn response và reference bank V1

## Kết quả kỹ thuật

Đã thêm API research-mode theo mục2/6 của docs21, không nới giới hạn hay đổi role của trainer engineering. Một lượt local tổng hợp đạt **38PASS,0failure/error/skip**; stdout pytest0,32s, JUnit suite0,172s, controller0,7710530757904053s trong ngân sách30s. Không gọi neural constructor, optimizer neural, dữ liệu thật, GPU hoặc remote. Có fit scalar temperature bằng nhãn response tổng hợp; đây không phải fit mô hình KT hay empirical calibration trên corpus nghiên cứu.

Nguồn mới `src/knowledge_tracing/response_calibration.py` SHA `134277e291a768913576c83c593d40419597134fc6f7dd443ee5dd77b414e0aa`; tests `tests/shared_kt/test_response_calibration.py` SHA `a233257fafa275037bd3148910ad28d44319d40bee605bd1e1faf8b3aaaac1fc`. Cả bốn input snapshot trước/sau giống nhau. Receipt `trial01/receipt.json` SHA `2a8107a92c2acf94d3165ec3a073574ca0daa465059bfffafcbdb5d20cd59f6f`; JUnit `trial01/junit.xml` SHA `65c22c0c909363bc7f2ae471e4b74978af3bd97c5f71f45619031f369dbb2155`. Chưa có failure trong lượt này, không tạo giả red/fail.

## API và numerical contract

`PredictionBinding` ghim model ID/checkpoint bytes/vocab/full split/bank/reference/model-source/domain SHA. `CalibrationPartition` khai báo calibration learners và toàn bộ learners bị loại khỏi calibration; nếu manifest có seed-family thì phải truyền đủ mapping và kiểm hai phía không giao family. `CalibrationTarget` chỉ nhận binary observed labels thuộc role calibration, p hữu hạn hoặc null kèm support reason. Không có latent/theta/final-reference-label input.

`fit_temperature(targets, binding=..., partition=..., expected_target_keys=..., max_evaluations=200)` đối chiếu toàn bộ expected keys `(learner,event,item,full-prehistory SHA)`, không âm thầm bỏ row mất prediction. Duplicate event/query, thiếu/thừa target, learner sai role và history/query khác là lỗi. Dòng OOV/unsupported còn trong full denominator; class support tính trên những dòng có p. Không có supported predictions hoặc thiếu một trong hai nhãn thì trả unsupported riêng, T=null,0objective evaluations; không dùngT1 làm calibration thành công. NaN/Inf/probability bất hợp lệ là lỗi, không được đổi thành missing support.

Fit một positiveT trong[0,05;20], common input clip1e-6, response mean Log Loss. Golden-section trên beta=1/T tận dụng convex scalar NLL; tổng objective evaluations tính cả hai endpoints và rawT1, không vượt caller budget4..200. Mỗi learner/event vẫn là một response target, không mặc định là đơn vị inference độc lập. Không có pvalue/CI/selection theo final labels. Đối chứng toán học kiểm nghiệm q=0,6 và rawp=0,9 cho nghiệmT=log(9)/log(1,5), không sao chép solver trong test.

`TemperatureCalibration.to_payload/from_payload` là JSON values, không pickle/callable. Khôi phục kiểm schema/recipe/counts/support/T/source và expected binding trước calibrated evaluation. Identity module hiện ghim bytes của module, simulator_bridge và docs21; **kit deploy tiếp theo phải có cả docs21 đúng SHA**, không chỉ chép module mới vào kit cũ. Đây là fail-closed dependency, chưa chạy Colab.

## Reference wiring vào controller

`reference_bank_v1(bank)` dùng đúng84actual item IDs của28concept, mỗi concept đúng difficulty1050/1200/1350, weights1/3. Không tạo item1250, không có API thay threshold theo labels. `score_reference_bank(session, calibration=..., binding=..., timestamp=..., source_row=...)` gọi `OnlineSession.probe_many` trên cùng prehistory, không observe. Nó trả `history_sha256`, `reference_history_sha256` bằng nhau, `bank_identity`, flat `item_calibrated_probabilities`, per-concept `score/reference_criterion`, raw/calibrated item responses, support counts và missing reasons.

Thiếu một trong ba prediction → score concept và criterion null, không renormalize hai item còn lại. `tau_ref=0,5637150147511514` là mean response tại theta1250 theo simulator design. ScoreS là calibrated expected response trên reference bank, criterion là common reference decision; **không phảiP(K), calibrated latent mastery hoặc ready/action**. Controller đọc output này và tự làm policy; module không phụ thuộc controller và không đổi historical probe helper.

## Giới hạn nghiệm thu và việc nối tiếp

Fixture có đủ28×3references nhưng backend deterministic tổng hợp; không tuyên bố checkpoint KT đã fitted vì fixture dùng tên `fitted` của existing OnlineScore contract. Tests chứng minh algebra/binding/support/null/history immutability trên fixture, không nghiệm thu actual model/corpus hoặc calibration quality.

Provenance là kiểm nhất quán hợp tác. Split/source/checkpoint SHA được caller cung cấp; module không mở model/dataset để chứng minh checkpoint đã refit90%, nhãn được predictor giấu đúng thời điểm, manifest chứa đầy đủ learner/family, hay backend không dùng RNG. Upstream lifecycle/collector phải xuất predictor identity, actual split/family manifest và full-target prediction ledger trước fit. Không gọi wrapper này để promotion toy checkpoint thành research-fitted role.

Chưa có corpus calibration thật, trainer research/refit wiring, calibrated backend/session wrapper, controller integration run, fitted calibrator export trên research checkpoint, query-throughput/resource acceptance hoặc fresh source Gate. Không sửa nguồn AKT/shared, historical artifacts, materializer03, root tracking hay Git. Newsource/tests phải nằm trong fresh kit/Gate sau root review; kitc934 và các Gate cũ vẫn giữ lịch sử.
