# Mức sẵn sàng của observer định danh trên một lịch sử CPU09

Ngày09/11/2026. Đây là bằng chứng engineering cho observer passthrough, chưa là phân tích độ đúng của mastery. Lượt được chấp nhận chỉ dùng một lịch sử cũ dài120event, key `[21000,"PG",false,false]`, chạy estimator hai lần theo thứ tự observer OFF rồi ON. Không sinh world/teacher, đáp án mới, neural fit hoặc optimizer step.

## Kết quả actual03

Outer03 ghi `ACCEPTED_ONE_HISTORY_TARGETED_OBSERVER_OPERATIONAL_PILOT`. Toàn bộ120readouts OFF/ON bằng nhau theo equality của artifact. Mỗi readout giữ query/selection, timestamp, prediction, θ_est, π_task/π_time lưu sẵn và sau decay, các gate và native M. Initial state fingerprint cùng là `f6b64156fbdbd07800fd9086aa555e437a20fe58f459de8ac7521e2336797ac7`; final fingerprint cùng là `e44d4f12343f25693c2fac90cf538111f02581bb01240d1dccb26f82cfb4e205`.

| Phạm vi đếm | Started | Returned |
|---|---|---|
| Hai lần dựng estimator, OFF và ON | 2 | 2 |
| select, predict, update, native_capture, từng loại trên hai lượt | 240 mỗi loại | 240 mỗi loại |
| Observer ON, __init__ | 1 | 1 |
| Observer ON, select/predict/update, từng loại | 120 mỗi loại | 120 mỗi loại |
| Observer ON, _decayed_pi | 360 | 360 |

360 là số lần gọi helper được quan sát trong lượt ON, không phải360event độc lập. Các wrapper chỉ bao năm method đã khai báo, không có global profiler hoặc tuyên bố quan sát mọi lần rút RNG. Artifact ghi không có instance attribute thêm, class attributes đã khôi phục, observer không còn live, pending attributes rỗng, raised/cleanup errors rỗng. Năm synthetic checks trước native kiểm passthrough và exception gốc, khôi phục attribute presence, bất biến stream, rollback khi install dở và xử lý nhiều cleanup failures.

Source/input map38entries trùng trước/sau ở worker và outer, đồng thời hai map đồng nhất theo key/value. Sáu project modules được compile từ pinned source với tên/package thật, không dùng project pyc loader. Worker không truyền oracle cho policy. Strict cache loader có đọc/kiểm numeric truth fields như validation có sẵn, nhưng không thực hiện threshold truth classification, confusion matrix hoặc mastery accuracy analysis.

## Thời gian, tài nguyên và cleanup

Outer đo11,450630500039551giây tới trước publication receipt, trong cap60giây. Owned helper đo10,648705959320068giây qua cleanup/posthash; worker ghi9,905331799993291giây trước receipt riêng. Ba số thuộc scope khác nhau, không cộng lại thành runtime. Caps được giữ là whole60/owned57/worker53, cleanup reserve3, RSS1GiB và available RAM floor2GiB.

Monitor outer có100samples, trong đó95child-family samples, family peak RSS được quan sát165277696bytes và minimum available RAM được quan sát2345738240bytes. Đây là sampling scope parent/live descendants, không continuous hard RSS proof. Monitor đã dừng, không terminate Job vì overrun. Helper ghi returncode0, cleanup accepted, Job active sau cleanup0 và Popen handle đã đóng. Outer ghi environment restored.

Loop OFF mất1,064232999982778giây, loop ON mất1,1814745999872684giây. OFF luôn chạy trước ON trong đúng một cặp này. Các thời gian chỉ mô tả lượt kiểm, chưa cho phép kết luận overhead nhân quả, tốc độ toàn bộ120worlds hoặc lợi thế so với global profiler trong một phép benchmark được cân bằng.

## Các lần từ chối được giữ nguyên

- **Prelaunch RAM refusal trước native02.** Controller từ chối trước khi tạo output/dispatch worker. Snapshot follow-up sau từ chối là1955803136bytes khả dụng; không trình bày nó như số đo tại đúng thời điểm điều kiện bị fail. Không có estimator replay từ lần từ chối này.
- **Native02.** Audit bắt đúng `.venv/Lib/site-packages/tzdata/zoneinfo/UTC` trong dateutil import. Failure ghi một denial, phase `native_import_and_full_cache_validation`, direct started/returned đều rỗng. Outer giữ verdict rejected, elapsed3,26400259998627giây, environment restored. Owned receipt ghi returncode1 nhưng cleanup accepted và Job0. Đây là thiếu entitlement cho runtime data, không là sai số mastery hoặc lỗi mô hình.
- **Native03.** Review04 cho phép đúng file UTC111bytes SHA `fddce1e648a1732ac29afd9a16151b2973cdf082e7ec0c690f7e42be6b598b93`, giữ model/input/caps và không mở allowlist cả thư mục. Sau review, operation mới đạt các điều kiện nêu trên.
- **Native01 đã đóng riêng.** Bundle `rq1-cpu09-targeted-observer-attempt-20261109-01`, manifest SHA `75b9df64ec07f73c09f2b88f51f9f7c51391cb1a12c4140b5ba91430e278db3e`, giữ34outputs lịch sử. Bundle mới chỉ tham chiếu SHA, không nhân đôi failure01 hoặc các snapshot lặp. Lane replay global-profiler năm lần thất bại cũ không được mở lại bởi lượt này.

## Được phép kết luận và phần còn thiếu

Observer định danh đã giữ nguyên đầy đủ readout và endpoint state trên một lịch sử PG/gOFF120event được chọn trước. Đây là cơ sở kỹ thuật để chuẩn bị replay có kiểm soát tiếp, chưa là bằng chứng cho toàn bộ120streams, ba persona hoặc mọi graph/mechanism condition. Có0mẫu độc lập mới. Không suy ra native M đúng/sai so với world, calibration của θ/π, causal graph benefit hoặc learning benefit.

Current sources được chấp nhận gồm worker03 SHA `1c84c3271556d2aa7b5d0ae709122504c2a4a008e8e9c4aa524d0345a10f5baf`, outer03 SHA `89d654a26e0c6120c88fd10820330c702cb6a8525d332973f560d6124deac130` và contract03 SHA `0280db8bfcaf844f2646a2c60c2f7cdac3808ba54e6c94ea476b815dcb5bdb90`. Actual worker result SHA `3641869970dd612569f2849d919f616abce8196e0892c71d1d612457198922c6`, actual outer final SHA `96ed606befb8205083db3caf3a325368483d609492ba709d0aabd4798486904d`.

Bundle đích `rq1-cpu09-observer-readiness-20261109-01` giữ raw03, failure02/refusal, reviews, nguồn current, contract02, UTC111bytes và copy inventory. Original GZip, runtime/dependencies và snapshot lặp chỉ tham chiếu hash. Báo cáo này được chuẩn bị trước closure; manifest completed mới xác nhận bundle đã đóng. Không có lượt chạy bổ sung trong quá trình viết hoặc đóng gói.
