# Full cached native mastery replay CPU09 — dừng bởi RAM floor

Ngày09/11/2026. ROOT đã thực chạy operation mới, verdict actual là `REJECTED_KEEP_NEW_FULL_OPERATION_NO_RETRY`. Monitor dừng owned Job khi RAM khả dụng xuống dưới floor2GiB. Chưa có kết quả native-mastery/truth mới. Ba source đã chạy giữ nguyên; không retry allocation này hoặc hạ floor. Việc hoàn tất archive không đổi verdict native bị từ chối.

## Câu hỏi và phạm vi đã chốt

Operation dự kiến kiểm native mastery ở queried concept trên toàn bộ cache CPU09 cũ, sau khi đủ select/query/P parity với hành vi gốc. Dùng nguyên `matched_replay` và `attach_truth_and_group`, không sửa phương trình GAM hoặc simulator. Trần dự trữ là120fresh policies và14.400events, từ10seed blocks ×3profiles ×4arms ×120steps. Đây không phải số đã hoàn tất. Graph-on bật parent signal và parent adaptation, local pathway tắt; environment/controller graph giữ nguyên. Các trajectories dùng lại có thể khác history/query giữa arms, không là một phép paired current-query effect.

Native M dùng `theta_est>=1250 && stored_pi_task<=.55`. Truth của evaluator là latent `theta_before>=1250` tại queried concept trước update. Đây là hai quy tắc threshold khác nhau, không là xác suất thành thạo đã calibrated. Không chấm truth cả28concept ở mỗi event, không có teacher/world/response/optimizer mới hoặc independentN mới. Không CI, p-value, causal ability hay learning-benefit claim.

## Admission phải hoàn tất trước truth analysis

- Strict reader kiểm full120histories/14.400rows, CRC và source/input SHA, rồi project public fields sang model. Stored truth chỉ ở validation/evaluator, không vào policy features.
- Genuine replay phải khớp mọi selected query/difficulty và P bits, cùng source clock6h/72h. Timestamps là source-derived, không được gọi là logged timestamp field.
- Mỗi policy phải hoàn tất120updates, đủ targeted-method counts và restore original class-method presence/value trước policy kế và trước truth. Toàn operation dự kiến120constructors,14.400select/predict/capture/update và43.200nested `_decayed_pi` calls.
- Pretruth readouts được đóng/fsync/hash trước evaluator. JSONL lossless arrays có19columns cố định, outer khôi phục row dict để kiểm genuine identity SHA. Sau đó mới gọi nguyên `attach_truth_and_group`.
- Truth sidecar chỉ có5key fields, `theta_before`, `sourceTrueM`; không xuất thêm một bản huge evaluated rows. Toàn136groups và zero cells phải khớp independent recount của outer.

## Terminal actual — failure RAM

| Thành phần | Actual evidence |
|---|---|
| ROOT terminal/outer verdict | REJECTED_KEEP_NEW_FULL_OPERATION_NO_RETRY |
| Outer trước finalwrite |9.802556500013452s |
| ROOT stdout sau finalwrite |9.804927600023802s, không cộng thời gian lồng nhau |
| Owned elapsed/returncode |9.478363037109375s /1 |
| Resource sampling |84samples,84có child |
| Observed family peak |171565056B, dưới cap1GiB |
| Observed minimum available RAM |2104508416B, dưới floor2147483648B |
| Monitor/cleanup |Job bị terminate, monitor dừng, cleanup accepted/Job active0/Popen handle đóng/environment khôi phục |

Allocation giữ whole300s/worker270s/owned285s có cleanup reserve5s, RSS1GiB/freeRAM2GiB. Resource error là `actual family RSS/freeRAM caps`; các extrema cho thấy RAM khả dụng đã dưới floor trong khi family peak vẫn dưới cap. Helper accepted=false và returncode1 đi cùng controlled Job termination, không phải cleanup failure. Actual one-history targeted observer03 vẫn là tiền đề vận hành riêng, không thay full-grid admission. Lane5full-native failures cũ vẫn STOPPED; targeted01/02 failures và prelaunch RAM refusal giữ nguyên.

Worker output chỉ có `pure_checks.json`, `native_metadata.json`, `reservation.json`. Năm inline checks đã qua. Reservation đã fsync trước factory với trần120constructors/14.400calls mỗi thao tác. Actual constructors/updates sau hard termination là **UNKNOWN**, không vượt reservation. Không suy0calls từ thiếu file và không suy đã hoàn tất một trajectory. Không có readouts/parity/truth/groups hoặc worker result/failure receipt cuối; không có scientific subset được admit.

Outer `validation=null`, `outputs={}`, `source_input_after={}` vì dừng trước successful artifact/source postchecks. ROOT đã thực hiện kiểm độc lập sau termination, xác nhận50current/historical input SHA không đổi, cùng Job0/envrestoration/monitorstop. Proof này chỉ chứng minh integrity sau failure, không thay successful worker postcheck hoặc parity. Giữ cả `verify_cpu09_full_ram_stop01.py` và `cpu09_full_ram_stop_postcheck01.json`. Không có confusion counts, calibration/CI/p-value/learning-benefit result, newN0.

## Vị trí và đóng gói

Scientific output directory của operation mới là `experiments/gam_kt/results/rq1-cpu09-native-mastery-20261109-01/`. Theo thiết kế, hai JSONL nếu được tạo sẽ giữ ở đó với SHA/bytes và không copy vào small bundle. Lần này không tạo hai file đó. Pretruth cap8MiB, truth sidecar4MiB, metadata1MiB/file; riêng outer memory journal2MiB/3300samples. Tổng artifacts của operation tối đa16MiB. Outer/owned transient logs nằm trong prep hiện có.

Bundle nhỏ dự kiến `research_tracking/runs/rq1-cpu09-native-mastery-20261109-01/`, giữ3actual inner files, all outer/owned terminal logs, frozen3sources, Rootreview và independent source-postcheck. Không có scientific JSONL trong lần bị dừng. Originalcache/dependencies chỉreferenceSHA. Actual outer SHA được ghim khi tạo dry; archive completed chỉ xác nhận lưu failure, không chuyển verdict thành PASS. Không replay, resource diagnostic hoặc chỉnh nguồn khi closure. ROOT review exactdry trước khi đóng.
