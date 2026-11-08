# GRAPH13 — kernel thống kê chọn ứng viên trên population chung

**Kết luận:** kernel thống kê đã vượt8ca kiểm bằng dữ liệu chế tạo. Chưa chọn mô hình từ prediction nghiên cứu, chưa xác nhận đủ chín candidate, chưa tạo external freeze hoặc chạy refit. Đây là bằng chứng phần mềm phục vụ bước lựa chọn trong Protocol21/Recipe26, không là kết quả cải thiện RQ3.

## Kernel thực hiện điều gì?

Caller cung cấp mỗi học viên một số dòng U và năm tổng log loss trên **cùng U chung** của A0, A1_EXPERT, A1_LEARNED, A3_EXPERT, A3_LEARNED. Kernel kiểm đúng năm model/count, cộng loss theo số câu trả lời, rồi bootstrap2.000 lần học viên với RNG riêng seed42. Các mô hình dùng chung draws; mỗi draw vẫn lấy tổng loss chia tổng số dòng được lấy mẫu, không lấy trung bình LL của từng học viên.

Graph eligible khi cận trên type7.975 của ΔLL(graph−A0) thật sự `<0`. Sau đó chọn point LL nhỏ nhất, tie bằng ID; không có eligible thì đề xuất A0. Không epsilon hoặc làm tròn eligibility. Học viên không có dòng U được báo coverage riêng; U toàn cục rỗng bị reject thay vì sinh quyết định A0. Trường hợp một học viên được đánh dấu kết luận conditional, không chứng minh nhiều seed độc lập.

Đầu vào là sufficient statistics đã được caller chứng nhận, nên kernel **không thể tự kiểm query keys, nhãn, domain hay nguồn checkpoint**. Cả chín candidate (A0; A1/A2/A3 mỗi loại có EXPERT và LEARNED; SAKT; GKT) vẫn phải hoàn tất selected-only admission ở lớp ngoài trước bất kỳ main refit của environment. A2/SAKT/GKT là comparison bắt buộc, không bị loại khỏi đề tài do không thuộc eligible set của rule này. Return luôn là `STATISTICS_ONLY_NO_EXTERNAL_FREEZE`, không phải giấy chấp thuận thực nghiệm.

Nguồn và hợp đồng: [kernel đã chạy](../runs/research-selection-kernel-engineering-20261109-01/source__research_selection.py), [tám ca kiểm](../runs/research-selection-kernel-engineering-20261109-01/test__research_selection.py), [hợp đồng selector](../runs/research-selection-kernel-engineering-20261109-01/MAIN_SELECTOR_CONTRACT01.md).

## Bằng chứng được giữ riêng theo lần

| Bằng chứng | Kết quả thực tế | Giới hạn |
|---|---|---|
| Sáu fixture LL đối chiếu evaluator GAM/sklearn hiện hành | Formula parity accepted; sai khác tuyệt đối lớn nhất1.1102230246251565e−16≤1e−12; outer3.497635099978652s/10 | Dữ liệu chế tạo; dùng NumPy/pandas/sklearn ở lượt đối chiếu này, không NN. Receipt là regular subprocess reaped, không ownedJob/RSS-quota certificate. |
| Pure01 |8cases đã chạy:7PASS,1FAIL duy nhất tại type7`.025`: `.7500000000000001` khác exact`.75` | Không lỗi LL/kernel được phát hiện từ failure này. Final01 giữ REJECTED/counts=null; worker-result01 vẫn giữ source_after. |
| Pure02 |8PASS,0failure/error/skip; unittest0.135s; controller prewrite0.9181739999912679s/30; owned process accepted/cleanupJob0 | Chỉ thay tolerance fixture type7 sang absolute1e−14 và chuẩn hóa mã thoát controller. Kernel toán học không đổi. Không benchmark thời gian chọn mô hình thật. |

Lần02 ghi **raw SystemExit thực tế là int0**, normalized0. Controller có thêm hỗ trợ bool/None để tương thích unittest; không có chứng cứ rằng bool đã gây failure01. Giữ nguồn và raw01, không gắn PASS02 cho test cũ. Allocation02 cộng thời gian01 đã charge0.8424742s; ceiling cộng dồn30.8424742s, không xóa lần fail. Trường prewrite và thời gian owned chỉ mô tả đúng phạm vi đo, không là wholeterminal timing mới suy ra.

Xem [LL parity gốc](../runs/research-selection-kernel-engineering-20261109-01/reporting-loss-parity01.json), [stderr01](../runs/research-selection-kernel-engineering-20261109-01/pure01_owned__stderr.log), [verdict02](../runs/research-selection-kernel-engineering-20261109-01/pure02_capture__final.json), [mã thoát02](../runs/research-selection-kernel-engineering-20261109-01/pure02_capture__worker-result.json).

## Tám ca kiểm có ý nghĩa gì?

Các ca kiểm bao phủ: sáu known-answer LL và type7; weighted LL khác cluster-macro với draws chung biết trước; eligible strictnegative kể cả chênh lệch gần zero/tie/one-learner/zero-support coverage; equal hoặc worse về A0; RNG global và input-order không đổi; dữ liệu sai/thiếu/NaN/bool/duplicate bị reject; resource preflight dừng trước RNG; hết giờ sau quantile cuối không được trả false-complete. Không cộng số test thành số học viên hay số lần tái lập nghiên cứu.

Loss từng dòng tạo `(1−p,p)` rồi clip binary64 epsilon trước log, không thêm clip1e−6. Tổng loss đã làm tròn theo học viên có thể khác bit cuối so với cộng trực tiếp toàn bộ dòng/sklearn mean; tolerance fixture1e−12 chỉ kiểm công thức, không đổi response-pooled estimand hay eligibility. Draw SHA ghi đúng thứ tự learner/draw đã dùng; không phải chứng cứ identity dữ liệu đầu vào.

## Phần còn thiếu trước main selection/refit

Lớp tích hợp phải đọc exports và terminal thật, kiểm toàn bộ universe/nhãn/phase/domain, dựng đúng U chung, xác nhận đủ chín candidate và lineage selected epoch/checkpoint. External freeze có authority riêng phải xảy ra trước tất cả main refits. Calibration10 không được dùng để chọn epoch/hyperparameter/candidate/winner; việc public reader audit schema trước đó được phép theo Protocol22. Kernel này không thay reader, không đọc corpus/oracle/final, không fit/calibrate hoặc mở quyền chi GPU.

Các cap count/index/work/time là fail-closed/cooperative trong kernel; không chứng nhận hard interruption hay peakRAM. Pure02 có owned process cleanup riêng, không biến thành runtime/fullGate/main-research acceptance. Bundle giữ snapshots, logs, pre/postSHA và copy inventory. Snapshot báo cáo được chuẩn bị trước closure; việc bundle đã đóng phải đối chiếu manifest và chỉ mục hiện hành, không suy từ tên file.

