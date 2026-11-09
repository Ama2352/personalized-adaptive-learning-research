# A0 selected-only đã hoàn tất trên fixture engineering10×84

## Kết quả kiểm tích hợp

Public `run_main_selected_candidate` đã chạy thật trên corpus engineering riêng gồm8train/1selection/1calibration, mỗi learner84events. Corpus này được collector nguồn thật tạo và nghiệm thu trước trong bundle [corpus10×84](../runs/akt-main-engineering-corpus10x84-20261109-01/README.md). Lượt fit dùng lại public inputs, không gọi teacher hoặc sinh corpus mới. Canonical60×210 tiếp tục giữ riêng.

Profile fit02 và outer ghi trạng thái accepted. Từ allocation tối đa20epochs/patience3, runner thực hiện7complete epochs, chọn epoch4, lưu4best checkpoints rồi nạp lại best bằng fresh model và fresh Adam. Frozen native256/8heads/context100/target100/batch4/dropout.05 và optimizer recipe được giữ nguyên. Đây là bằng chứng đường đi integration qua actual authorization, train, validation, checkpoint và export. [Native terminal](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/native__selected-terminal.json), [worker/outer receipt](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/fit__outer-final.json)

|Đại lượng thực tế|Kết quả|
|---|---:|
|Complete epochs / selected epoch|7 / 4|
|Train windows mỗi epoch / Adam bodies tổng|8 / 14|
|Optimized target exposures|4.704 =672×7|
|Model constructors / Adam constructors|2 / 2|
|Native forward calls|22 =14train+8selection|
|Selection passes / target exposures|8 / 672 =84×8|
|Best saves / inspect / fresh restore|4 / 2 / 1|
|Final raw selection targets / supported / OOV|84 / 84 / 0|
|Full metadata dispatches / Git processes|51 / 530|

Các target exposures lặp lại cùng dữ liệu qua nhiều epoch/pass. Selection là một learner với84events theo thời gian, không phải672quan sát độc lập. Native tracker journal xác nhận14reserved/body-returned/committed Adam bodies và4.704targets. Observer được cài ở lazy `_tools` sau guard thật, gọi nguyên hàm gốc; không dùng global profiler hoặc sửa Adam.step/backward. Actual NumPy target masks cung cấp selection exposure counter. Cuối lượt các bindings được restore, monitor đã dừng, owned cleanup accepted và Job còn0process. [Observer](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/fit__observer.json), [durable journal](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/native__events.jsonl)

## Metric của fixture và lựa chọn epoch

Native BCE trên selection được dùng cho early stopping theo source đã chốt. Reporting log loss được tính bằng evaluator hiện có trên raw exported probabilities. Hai số có khác biệt làm tròn FP32/binary64 nhỏ, được giữ đúng loại. Cả bảy epoch đều lưu trong evidence.

|Epoch|Train targets|Adam bodies|Native selection BCE|Reporting selection LL|Selected epoch sau lượt|
|---|---:|---:|---:|---:|---:|
|1|672|2|0.662691057|0.662691081|1|
|2|672|2|0.642104566|0.642104518|2|
|3|672|2|0.630183816|0.630183796|3|
|4|672|2|0.626658499|0.626658424|4|
|5|672|2|0.630687475|0.630687525|4|
|6|672|2|0.637939334|0.637939311|4|
|7|672|2|0.645283639|0.645283667|4|

Nguồn đầy đủ là [epoch history](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/native__fit80__epochs.json). Sau fresh best reload, raw predictions và full84keys khớp best epoch theo kiểm source. Final selection reporting LL0.6266584235253608, Brier0.21710220642114064, AUC0.4323607427055703, accuracy0.6904761904761905 và ECE0.022965482303074422. Nhãn có58positive/26negative, prevalence0.6904761904761905. [Coverage/metrics](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/native__selection__coverage.json), [raw predictions](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/native__selection__predictions.csv), [targets](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/native__selection__targets.csv)

Các metric trên chỉ mô tả fixture đã dùng để chọn epoch. Chưa có đối chiếu mô hình hoặc đánh giá độc lập, và calibration role không được dùng để fit temperature hoặc chọn epoch. Không dùng bảng này làm bằng chứng efficacy, lợi ích học tập, comparative RQ hoặc final generalization. Chưa chạy chín candidates/hai môi trường, system selection, refit90 hoặc lifecycle resume từ kết quả này.

## Thời gian, tài nguyên và failure đã giữ

Metadata prepare và materialize được thực hiện thành hai owned operations riêng, outer lần lượt3,8037622giây và4,0551597giây. Chúng tạo package/config/auth mới cho corpus10×84, không tái dùng guard-only canonical60 authorization. Profile fit01 sau đó dừng trước owned worker ở `psutil.disk_usage(WindowsPath)`, TypeError yêu cầu `str`, elapsed0,334675giây. Không có NN work trong lượt prelaunch này theo source/control-flow và review ROOT. [Raw stderr01](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/profile_fit01__stderr.log)

Derivative outer02 chỉ chuyển disk API argument sang `str(R)`, request02 thêm scratch controller pin. Original01, rawfailure, derivative source/inventory và cả hai request được giữ. ConfigSHA `f51560d8a50fa7866022fe4ece7bdaa367aa4fad28be14f6cb5bb2bf854bbcc8` và authSHA `fde4d2e08b03891b6e088ff6d83ac5d37fce0ceaab7e208acace0c341f94486b` không đổi. Lượt actualmodel duy nhất là profile fit02, không retrain hoặc reset work đã thực hiện ở01. [Derivative inventory](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/tiny_disk_path_fix02_inventory.json)

Fit02 profile launcher ghi161,4746751giây, outer receipt161,3789760giây, worker158,8369354giây. Đây là các clock bao nhau ở các thời điểm khác nhau, không cộng chúng. Caps vẫn training300/main540/worker560/owned580/outer600giây. Peak worker550.121.472bytes, minimum available RAM2.820.173.824bytes. Observer ghi revalidate72,4665378giây inclusive và `_metadata`70,3041981giây inclusive lồng trong các calls đó; không cộng các timings lồng nhau hoặc quy toàn bộ overhead cho Git. Bản đo này cũng chưa dự báo chi phí full research hoặc GPU.

Mỗi checkpoint payload trong bốn best epochs có26.949.689bytes. Best epoch4 SHA `5e88afd62634a39a3c9b84626c7a5714288faa11f7ea7bdbd9187a8b7d0fc663`; binaries giữ nguyên tại native run trong `experiments/akt/results/`, bundle chỉ giữ SHA/size references cùng metadata/COMPLETE. Corpus17files cũng chỉ tham chiếu SHA. Không mở lại weights hoặc parse oracle để làm báo cáo.

## Closure và bước tiếp theo

Run bằng chứng là `akt-main-tiny-a0-selected-engineering-20261109-01`. Trạng thái closure được xác nhận bằng [manifest của run](../runs/akt-main-tiny-a0-selected-engineering-20261109-01/manifest.json), sau khi ROOT review exact dry inventory và archiver đối chiếu SHA trước/copy/sau. Các link snapshot trong báo cáo này dùng đúng aliases của archiver và tồn tại khi closure hoàn tất. Trước thời điểm đó, báo cáo vẫn mô tả actual fit đã accepted; source handoff hoặc câu chữ trong báo cáo không tự xác nhận bundle đã đóng.

Actual integration đã đi qua selected-only success path với normal API và nguồn177 hiện hành. Bước nghiên cứu tiếp theo vẫn cần main candidate allocations, external freeze và các baseline/environment integrations đã yêu cầu. Model/checkpoint của fixture này giữ scope engineering-only. CPU success không cấp CUDA readiness hoặc quyền chi cloud; resume hiện chưa được hỗ trợ.
