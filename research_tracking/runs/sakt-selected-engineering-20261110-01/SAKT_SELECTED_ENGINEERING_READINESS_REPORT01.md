# SAKT — selected-only producer đã hoàn tất trên corpus engineering10

## Lượt được nghiệm thu

Actual operational retry05 chạy native run `sakt-selected-engineering10x84-20261110-03` đã được nghiệm thu với trạng thái `ACCEPTED_ACTUAL_SAKT_SELECTED_ONLY_ENGINEERING`. Outer lưu85,17786180000985giây trên cap600; terminal Root ghi85,1825653giây. Worker lưu81,62196999997832giây. Đây là producer CPU selected-only thật trên corpus8train/1selection/1calibration, không phải kết quả đầy đủ của baseline nghiên cứu trên Main60 hoặc Junyi.

Recipe30 giữ d_model200,5head,head_dim40, context100/max_length101, dropout0,2, Adam0,001 ordinary CPU, batch128, clip1, seed42, max50, patience5 và min_delta0,0001. Hai constructor thực tế đều có312.401parameters và cùng cấu hình. Không đổi hyperparameter để vượt hạn mức.

Lượt thực tế dừng sau6epoch complete, chọn best epoch1. Mỗi epoch có672train targets và6Adam updates. Tổng36updates/4.032train-target exposures,7selection passes/588prediction targets,43forwards,2model constructors và2Adam constructors. Có1checkpoint save,1restore,1torch.save và1torch.load. Fresh reload cho full84selection targets đã hoàn tất.

Nguồn actual ở `sakt-selected-fit05/result.json`, `observer.json`, `resources.json`, `actual-completion-check.json`, `outer-final.json`, owned receipt và native `selected-terminal.json`. Counter journal ghi36reserved/body-returned/completed và4.032targets. Các weakref release checks đều đạt trước fresh reload và trước final prediction.

## Kiểm reporting và resource

Best checkpoint xuất đủ84target,58positive/26negative, không OOV/unsupported. Canonical reporting có AUC0,5835543766578251, LL0,642004883399649, Brier0,21759474709791066, ECE15 khoảng0,10718469889391037 và accuracy0,6904761904761905. Native FP32 BCE selection objective riêng là0,6420048475265503. Một selection learner dùng trong engineering không hỗ trợ kết luận baseline tổng quát hoặc so sánh learning benefit.

Actual monitor lấy724samples toàn bộ ownedJob, peak family838.565.888byte, peak worker826.572.800byte và minimumfree3.890.266.112byte. Observer, environment, queryhandle và monitor đã được xác nhận khôi phục/đóng; ownedJob0. Current source/input/runtime trước–sau khớp, CUDA chưa khởi tạo. Cap worker/family2GiB, free2GiB và canonical preallocation4GiB giữ nguyên.

## Failure và chi phí vật lý được giữ riêng

| Lượt | Điều đã thực sự diễn ra |
|---|---|
| fit02/native run01 | Dependency closure thiếu `gam_kt/__init__.py`, từ chối trước model/Adam/update. Canonical SOURCE_NAMES đã được sửa và current cold35subset62 thực sự đạt trước dry mới. |
| fit03/native run02 | Producer COMPLETE6epoch/best1/36updates/4.032targets và xuất84selection; finally của wrapper lỗi vì biến `keys` bị tuple/CSV-lambda dùng trùng. Overall wrapper REJECTED. Không có final resource/observer receipt để hồi dựng peak hoặc nghiệm thu toàn lượt. |
| fit04/native run03 | Canonical preallocation4GiB từ chối trước lazyTorch/model/update. Source finally fix đã ghi được result/resources/observer và Job0. Native output chưa được tạo. |
| request preparer05 | Metadata KeyError vì giả định có field `claim` trong result. Derivative06 dùng schema thật `native_outputs == {}` cùng actual zero-counters/native-absent; không thay auth/spec. |
| fit05/native run03 | Một operational retry được Root duyệt, shell cha nhẹ hơn dùng cmd.exe, cùng .venv/auth/spec/caps/recipe. Toàn producer và wrapper đã được nghiệm thu. |

Các materializer failures do truncated SHA và thiếu role parent, dry import-hook failure, cùng các source derivatives và raw receipts được lưu. Hai AST-extracted regression tests cho local-name collision đã thực sự đạt; raw unittest log ghi0,026giây. Không rerun các test hoặc mô hình trong lúc lưu bundle.

Tổng chi phí vật lý của hai lượt có training là72Adam updates và8.064train-target exposures. Fit02 và fit04 có0update. Lượt failed-fit03 đã dùng27,31116247177124giây native training; stored outer109,21849632263184giây được giữ riêng với terminal khoảng109,2234giây. Không reset các khoản này khi chạy retry.

Root light-admission02 lưu ba mẫu4.703.780.864/4.702.580.736/4.699.283.456byte. Field headroom bổ sung là128MiB; cả ba mẫu thực tế cũng vượt mức256MiB từng đề xuất. Canonical preallocation4GiB không đổi. Phối hợp tiến trình chỉ nhằm giảm overhead lúc admission.

## Đối chiếu cache giữa producer COMPLETE cũ và lượt accepted

`verify_sakt_selected_cached01.py` đã đối chiếu E1–E6 theo epoch/seed/progress/selection metrics/objective/population/prediction SHA. Tất cả khớp chính xác. Ba exports predictions/targets/coverage khớp nguyên bytes. Predictions có SHA `f15341ad8d376726f76cd69cbe34353abaed378ec53471975a8738c42c1e7bd7` ở cả hai run. Initial-model state SHA khai báo trong claim cũng khớp.

Checkpoint serialized bytes khác SHA/kích thước giữa hai run và được giữ ở native paths. Lượt kiểm cache chỉ hash bytes để làm binary references, không `torch.load` và không suy diễn tensor equality. Nó không phục hồi telemetry đã mất của fit03 hoặc tăng số mẫu độc lập.

## Giới hạn còn lại

Current cold62 gồm35SAKT và27GKT metadata cases, không phải35case mới ngoài62. Component epoch22/checkpoint33 giữ source math riêng đã nghiệm thu trước đó. Gói này thêm positive normal-entry selected-only proof trên engineering10. Chưa có selected fit Main60/full matrix, external system freeze, fresh refit90, calibration10/Tfit, public producer resume, Junyi result hoặc actual CUDA run. Modal/cloud spend bằng0.
