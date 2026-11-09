# SAKT07 — đề xuất selected-only engineering10×84

Bản nguồn ngày10/11, chưa gọi public reader hoặc identity factory và chưa ghi authorization. Root thực hiện từng bước sau review. Corpus và recipe cố định, không có search hoặc thay cấu hình để vừa ngân sách.

## Mục đích và nguồn đã có

Chạy positive normal entry SAKT trên đúng corpus đã xuất bản `grade10-main-lifecycle-engineering10x84-20261109-01`. Đây là phép kiểm lifecycle engineering8train/1selection/1calibration, tổng840events. Train có672targets, selection84, calibration84. Calibration chỉ đi qua canonical provenance audit, không tham gia tối ưu hoặc chọn epoch. Không dùng claim engineering này để thay comparator fitted của main matrix/full corpus.

Giữ recipe30 d200/h5/head40,100past+query101,dropout0,2/epsilon1e-5, ordinary Adam0,001, batch128terminaltargets, clip1, seed42/epoch42+e−1, max50/patience5/delta0,0001. Epoch criterion là native Torch BCE mean từ cùng exportedfloat32P/y trên supported selection population. Reporting dùng evaluator hiện có và coverage đầy đủ. Không đổi architecture, model mathematics, protocols21/22/26/30 hoặc source Main/Gate.

Metadata05 đã được Root nghiệm thu34ca và Job0. Epoch22/checkpoint33 là các phép kiểm primitive có thật, không chứng minh producer d200 đã chạy. Bản positive này phải đi qua SAKT closed authorization riêng và actual public reader, không dùng grant A0 hoặc metadata stage làm quyền NN.

## Trình tự hữu hạn

1. Root review ba source/packet trong P rồi thực hiện metadata dry trong owned process. Dry dùng canonical reader để kiểm cả ba Development roles và gọi thật `prepare_sakt_selected_identity`, kiểm current Gate183, runtime schema2, actual22/33 và các source/input pins. Chỉ ghi proposal/result dưới P, không gọi authorization factory, model, optimizer hoặc runner. Reader đã tự thực hiện `_Read.verify_after()` trước khi trả kết quả, dry kiểm thêm public result integrity và raw input hashes sau cùng.
2. Root đọc actual dry và SHA trước khi cho materialize. Bước materialize sẽ xác nhận lại current sources/Gate/public bytes, rồi tạo exclusive SAKT auth và request đã review. Mã materialize/fit driver chưa có trong gói này. Không tự cấp quyền từ output dry hoặc approval string của metadata worker.
3. Root review request/authorization và workload observer trước positive normal entry `run_sakt_selected_fit` một lần trong owned worker. Chạy tuần tự sau AKT parent/resume, admission RAM đủ. Tôn trọng early stopping thật, giữ failure/counters khi không đạt. Không tự retry, giảm dimensions/batch/history/epoch hoặc tăng cap.

## Hạn mức NN đề xuất, chưa phải đo thực tế

| Phạm vi | Giới hạn |
| --- | --- |
| Outer toàn bộ |600s |
| Owned gồm cleanup |580s, cleanup3s |
| Worker |560s |
| Entry toàn bộ từ admission |540s |
| Training cộng dồn |300s |
| Worker peak và live owned-Job family RSS |2GiB mỗi scope, đề xuất chưa đo |
| Free RAM đang chạy |2GiB |
| Prelaunch NN |Ít nhất4GiB |
| CPU |FP32,2threads |
| Outputs toàn run |512MiB |
| Checkpoint / tensor state |8MiB /8MiB |
| Metadata mỗi leaf |1MiB |
| Source/runtime file mỗi leaf |8MiB |

Cần đo actual family bằng exact owned Job PID query, không gán worker RSS thành family. Token chỉ kiểm worker/free RAM. Owned helper cung cấp deadline/cleanup, không gọi đó là hard RSS quota. Proposal2GiB dựa vào shape boundB128×L101, chưa có số đo d200. Corpus84events giới hạn lịch sử thực tế ở83past+query84, vẫn giữ config101. Nếu thiếu RAM, dừng trước model. Nếu budget bị vượt sau cập nhật, giữ ledger và failure. Không mở paid/cloud/CUDA từ gói này.

Worst-case E50 có6batches/epoch với672targets và lastbatch32. Reserve300Adamsteps/33.600optimizedtargets. Selection có E+1pass, tối đa51pass/4.284fullrows, bao gồm best-reload parity. Hai model và hai Adam được tạo tuần tự, fit objects được release trước fresh reload. Với Eactual và S epochs cải thiện, plannedforward=7E+1≤351, backward/clip/Adam=6E≤300, save=S≤E≤50, load/strictmodelrestore/optimizerrestore mỗi loại1. Đây là planned caps, actual journal và observer phải ghi started/returned/exceptions riêng. Không patch global profiler, Adam.step hoặc backward để đếm.

Checkpoint chỉ lưu epoch cải thiện, epoch khác có SHA null. Giữ đủ full prediction rows và null unsupported, không thay denominator hoặc biến unsupported thành0. Fresh best reload dùng đúng selected epoch spec, cả fullselection semantic predictionSHA phải khớp. Không tạo system winner, systemfreeze, refit90 hoặc Tfit trong selected-only.

## Input và file roles

Corpus rawSHA78da1a4fd1708bb1efca723caed4976ed518687eb70b847fbdf780f111191151. Bank rawSHA4ef02907ee9071ba2ed6b4bba4d4dab728d390e9bbff8218a4e39bbb32f48034. Fixed9public files +DONE tổng119.817bytes theo file sizes đã đọc, không mở oracle/ hoặc originaldataset/Holdout. Raw plan SHA và logical split SHA là hai identity riêng.

Current Gate index `artifacts/akt/preflight/gate2-main183-win-current-gate-20261110-07.json`, SHA dd8bd24f6a71e57e6206e56dc9c101648558e8dc7b5779abe015c221ea828fd0. Runtime schema2 `runtime-schema2-main177-20261109-01.json`, SHA3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b. Actual metadata05 outer có SHA0d8c7e83179b7b50416150530dfa41096715e4d501a6d89701484231880aed99. Packet ghim cả sáu JSON outer/child/owned của22/33 và original lock. Corpus producer dependencies giữ raw source bytes, không strip notebook hoặc sửa provenance.

Dry chỉ được ghi `P/sakt-selected-positive-package01/` và owned receipt riêng. Hạn mức dry60whole/57owned/50worker/cleanup3, worker RSS256MiB/free1GiB/admit1280MiB. Đây là inspection stdlib, không kiểm đủ prelaunch NN4GiB và không là NN allocation.

Future run ID `sakt-selected-engineering10x84-20261110-01`. Future auth `experiments/sakt/authorizations/<run-id>.json` và model/checkpoints/predictions `experiments/sakt/results/<run-id>/`. Root sẽ tạo request nhỏ riêng dưới P sau dry. Actual run chỉ được ghi các path riêng này cùng owned/temporary output đã review, không ghi corpus, nguồn, dependencies/runtime hoặc historical results. Quyền materialize chưa được cấp bằng tài liệu này.

## Bàn giao nguồn

- `prepare_sakt_selected_positive01.py` chỉ dry genuine metadata. Không có materialize flag hoặc call đến runner.
- `run_prepare_sakt_selected_positive01.py` kiểm external pins, admission và actual owned cleanup, kiểm dry payload/source/public bytes trước–sau.
- `sakt_selected_positive01_packet.json` là source-only proposal206source/22input/4runtimepins. Các con số trong caps không phải output thực thi.

Root có thể review rồi chạy outer dry với các SHA được bàn giao riêng. Không có actual dry, NN model, authorization hoặc future result trong lượt chuẩn bị này. Typed producer vẫn chờ positive normal-entry acceptance.