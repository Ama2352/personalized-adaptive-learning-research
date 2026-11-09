# RQ1 · Hai đối chứng năng lực được chốt trước panel mới

**SOURCE-ONLY. Chưa chạy hai control hoặc cấp native allocation.** Root chọn trước mức1300 và1150 tại block21010, graph full, λ0, S/P bật và L tắt. Mục tiêu là đối chiếu initialization và khả năng xuất hiện các lớp/ngưỡng giữa ba lịch sử, giữ cùng criterion. Không chọn lại cell theo kết quả panel.

## ID và provenance đã xác minh

| Vai trò | Cell | Năng lực nền | Native origin | Trạng thái |
|---|---|---:|---|---|
| Đối chứng thấp đã có | F041 | 1000 | Parent02 | Panel đã nghiệm thu, không tự rerun |
| Control cao đã chốt | F001 | 1300 | Parent02 | Chưa có native panel này |
| Control trung gian đã chốt | F081 | 1150 | Recovery03 | Chưa có native panel này |

Saved plan gốc caf38156 ghi F045 là block21011, mức1000. Vì vậy F045 không phù hợp yêu cầu cùng block21010/mức1150. F081 mới đúng tuple, xác nhận cả plan và actual initial snapshot. Đây là sửa định danh theo điều kiện Root đã chọn, không đổi điều kiện dựa vào outcome.

Whitelist tham chiếu giữ đúng ba cell trên. Danh sách thực thi bổ sung chỉ có F001 và F081. F041 được dẫn qua bundle đã đóng `rq1-f041-native-panel-20261110-01`, manifest3d5dc69ee4ab9f83c1e29cedc31603cd8a8ab321d37c50f5dd207c1f5362d345. Không dùng generic entry để tự chạy lại nó.

Parent02 và Recovery03 là hai origin dữ liệu khác nhau. F001 là một trong61 cell parent hoàn tất đã được accepted recovery kiểm và tái dùng. F081 thuộc59 cell child hoàn tất. Không áp điều kiện committed-parent61 cho F081 hoặc đọc nhầm oracle từ parent02. Recovery manifest deff815a và acceptance đã đóng tiếp tục là entry chứng minh primary120 đầy đủ. Giữ parent operation failure nguyên trạng.

## Initialization và điều có thể hỏi

Ba initial snapshot đều có đủ28 environment base/theta/last_seen và cùng nonedge policy initial SHA1b3057bf6f694835739d670702876908caa654cea05c7aa0428ddcf2650372fa. Native policy vẫn khởi tạo θ1200 và π_task1 cho mọi concept. Không đưa actual base hoặc oracle theta vào model initialization.

Initializer nguồn dùng cùng residual đã center, chuẩn hóa max-absolute và scale60 rồi cộng mức nền. Với ba mức ở đây, bounds trước dữ liệu là940–1060,1090–1210 và1240–1360. Bounds là hệ quả của recipe, chưa phải min/max đo trên panel. Hai mức thấp/trung gian đều dưới criterion1250 tại initialization. Band của mức1300 đi qua ngưỡng1250. Không gán số positive/negative thực tế cho control chưa chạy từ các bounds này.

F041 đã có3360TN và zero θ-gate opportunity, nên chưa kiểm classifier hoặc cổng π. Hai control bổ sung sẽ ghi toàn bộ lớp/ngưỡng, kể cả nếu kết quả vẫn chỉ có một lớp hoặc zero suppression. Không tăng horizon, chọn concept, đổi π/θ threshold hoặc thêm cell để ép support.

## Entry và acceptance giữ nguyên

Mỗi control dùng đúng một fresh native policy, chỉ original public bank/model defaults và historical query/time/currentY.120 select/predict/update phải khớp original action/P/endpoint. Ghi3360 first-pass M observations từ getter có sẵn, không thêm getter của policy. Native pretruth panel và parity được đóng trước evaluator.

Evaluator decode actual initial float_hex, dùng3360 pure theta_at source calls. So fullvars SHA tại mọi120 presteps, chỉ cập nhật theo learning_gain/theta_before/timestamp đã ghi, rồi kiểm full final environment và28 endpoint. Không world constructor/interact/persona generator/newRNG/response hoặc NN. Đáp án và oracle tương lai không đi vào predict hoặc policy features. Canonical recorder b54b giữ nguyên, không cast native values để qua validation.

Tổng bổ sung tối đa hai policy builders,240 select/predict/update,6720 theta_at và6720 native concept-time rows. Giữ riêng actual F041120updates đã chạy, không reset hoặc gộp vào counter của operation mới. Cả ba lịch sử thuộc **một block**, không phải ba block độc lập hoặc10080người học. So queried với all28 trong từng history trước, rồi trình bày khác biệt support/readout giữa các điều kiện khởi tạo. Không ghép loss theo ordinal sau khi histories khác câu hỏi, không causal graph/teaching claim hoặc S04 calibration.

Mỗi operation vẫn whole60/worker50/owned55 gồm cleanup3, familyRSS512MiB/free1536MiB/admit2GiB. Tổng envelope bổ sung whole≤120giây, worker≤100giây, Root dispatch từng control sau review và đo RAM. Không tự retry hoặc tự chạy case khác sau lỗi. Đây là protective cap, chưa runtime forecast hoặc native grant.

Output khoa học mới nằm riêng `experiments/gam_kt/results/rq1-ability-panel-f001-20261110-01` và `rq1-ability-panel-f081-20261110-01`. Không sửa hoặc di chuyển F041 hoặc parent/child traces. Input oracle mỗi origin đều dưới4MiB, observables dưới2MiB, endpoints dưới1MiB. Same byte/row/output caps của F041 được giữ.

## Patch map tối thiểu trước implementation

Derive worker/outer mới từ source F041 đã thật sự chạy, giữ sampler/owned helper/metadata bootstrap/reader/recorder/state reconstruction và predicate nguyên byte khi có thể. Chỉ thêm `--cell-id` allowlist F001/F081, tra origin/initial/source seals từ whitelist, chọn output độc quyền, thay filter cell và thông báo scope. Giữ F041 trong reference-only case map.

Provenance của F081 cần nhánh admission child59 dựa vào accepted recovery inventory, thay cho check F041 nằm trong committed-parent61. Vì vậy đây không phải phép đổi tên chuỗi đơn thuần. Worker/outer derivative chưa được viết trong handoff này để Root review nhánh origin trước, tránh tạo một wrapper âm thầm thừa nhận dữ liệu sai parent. Không đổi canonical source hoặc source F041 đã đóng.

`rq1_ability_panel_case_whitelist02.json` giữ exact cell metadata, initial/full28-state SHA, raw input pins và output paths. File đó là source proposal, không authorization. Root chọn grant cụ thể trước khi tạo/running package mới. Không có panel outcome của F001/F081 được tính trong lượt chuẩn bị này.
