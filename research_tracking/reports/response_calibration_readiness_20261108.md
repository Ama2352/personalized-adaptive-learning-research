# Response temperature và reference bank V1: nghiệm thu API

Đã triển khai API dùng cho research-mode theo [protocol21](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md), có39kiểm tra tổng hợp đạt và một đường nối calibration→reference probe→controller→served prediction→observe. Đây là bằng chứng phần mềm; **chưa có calibrator fitted trên checkpoint/corpus nghiên cứu**, chưa đánh giá chất lượng hiệu chuẩn thực nghiệm hoặc hoàn tấtRQ.

## Phạm vi và nguồn

Thêm [response_calibration.py](../../src/knowledge_tracing/response_calibration.py) và [tests](../../tests/shared_kt/test_response_calibration.py); giữ nguyên simulator_bridge/shared/AKT/historical diagnostics. Reuse SimulatorBank,ReferenceSet,OnlineSession.probe_many và identity_hash. Controller do parent sở hữu; trial02 ghim exact controllerSHA `8f4795e3e236c08a33f12bfd9c5047264fef82e7113493ade5c9e37cb35a6cfc`, không sửa controller trong tiểu tác vụ này.

API không gắn toy checkpoint role hay giới hạn corpus nhỏ. Tests dùng observed responses và deterministic backend tổng hợp để kiểm numerical/contract, không neural constructor/training/optimizer/GPU/remote hoặc dữ liệu thật. Không nâng checkpoint engineering thành research-fitted.

## Temperature response

Fit mộtT/checkpoint bằng mean response Log Loss trên đúng partition calibration, T∈[0,05;20], common inputclip1e−6, tối đa200objective evaluations gồm endpoints và rawT1. Scalar solver dùng beta=1/T với convexNLL và golden-section; caller có thể đặt evaluationbudget4..200 rõ ràng. Không đổi weights/epoch/selector/threshold theo nhãn final. Kiểm toán học độc lập dùng empiricalq0,6 và rawp0,9, nghiệmT=log(9)/log(1,5), cùng boundary/clip tests.

PredictionBinding ghim model/checkpoint/vocab/fullsplit/bank/reference/model-source/domain. CalibrationPartition đòi learner disjoint; nếu có seed-family manifest thì đòi đủ family mapping và disjointfamily giữa calibration/excluded. Target keys gồm learner/event/item/full-prehistorySHA; missing/extra/duplicate/query/history khác là lỗicoverage, không âm thầm giảm denominator. Nhãn chỉ nhận rolecalibration. OOV/unsupported giữ rownull và supportreason; insufficient supported predictions và missingoneclass là hai trạng tháiunsupported riêng, T=null/0evaluations, không gọiT1 là calibration thành công. Nonfinite/invalid probability là lỗi, không thay bằng missing support.

JSON roundtrip kiểm schema/recipe/counts/support/source và expectedbinding trước apply. Sourceidentity ghim cả docs21: fresh deployment phải đóng gói đúng file này cùng module, không chỉ thêm module vào kitc934 cũ. Provenance là kiểm nhất quán hợp tác; caller vẫn phải cung cấp actual frozen-predictor/split/partition receipts. Không chống metadata bị caller cố tình giả đồng bộ, không tự chứng minh model đã refit90% hay labels chưa từng được đọc.

## Reference scoring và thứ tự tác động

V1 dùng84actual item IDs,28concepts×1050/1200/1350, weights1/3. Không tạo item1250. Cùng prehistory, probe84queries rồi calibrate response và mean theo concept. Thiếu bất kỳ itemprediction nào → conceptscore/criterionnull, không renormalize. Output có flat calibrateditem probabilities, bankidentity, history/referencehistorySHA bằng nhau và support/missingreasons, nối thẳng vào controlleradapter.

S là expected calibrated reference response correctness; `S≥tau_ref`, tau_ref0,5637150147511514, là common reference criterion từ simulator design. **S không phảiP(K), calibrated latent mastery, latentgain hoặc readiness/action.** Module không nhận theta/future/reference labels và không gọi observe. Backend phải giữ đúng existing frozen OnlineSession contract; kiểmhistory trên fixture không thay cho audit RNG/model thực tế.

Integrationtest dùng28bank: scalarfit→probe→controlleradapter→một servedpredictionticket riêng→observe response→rejectstale snapshot. ReferenceP không thay servedticket; controllertrace vẫn served_probability=null trước servedprediction. Không suy hiệu quả học tập hoặc causal mediation từ đường nối này.

## Bằng chứng và giới hạn

| Lượt | Kết quả thực tế | Controllerelapsed | Scope |
|---|---:|---:|---|
| trial01 |38PASS/0failure/error/skip;pytest0,32s |0,7710530757904053s |Numerical/binding/support/reference |
| controller02preparation |SyntaxError do shellquoting,0tests/0model |0,5084749s bảo thủ |Ghi chú tool-output-derived, không giả rawJUnitfailure |
| trial02 |39PASS/0failure/error/skip;pytest0,36s |0,8206632137298584s |Thêm integration với parentcontroller |

Cumulative bảo thủ2,1001911895202636/30s;0neuralupdates. [Receipt01](../runs/response-calibration-engineering-20261108-01/trial01__receipt.json), [receipt02](../runs/response-calibration-engineering-20261108-01/trial02__receipt.json), [JUnit02](../runs/response-calibration-engineering-20261108-01/trial02__junit.xml) và [ghi chú chi tiết trước integration](../runs/response-calibration-engineering-20261108-01/trial01__readiness.md) được sao byte-exact với pre/postSHA trong bundle. Source moduleSHA `134277e291a768913576c83c593d40419597134fc6f7dd443ee5dd77b414e0aa`; finaltestSHA `235c5381458521f27e5e406a11a52a282ebd27e5e78d22a9bb185590652af1aa`. Không cộng38+39 thành77kiểm tra độc lập.

Tiếp theo cần actual role-aware corpus/refit checkpoint, full calibrationpredictionledger, fittedtemperature export và controller run có coverage/resource acceptance, fresh sourcekit/Gate. Scalar/reference tests không thay actual neural lifecycle, representative querythroughput hoặc finalRQ evidence. Không cập nhật roottracking/Git trong tiểu tác vụ này.
