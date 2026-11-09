# RQ1 — khả thi ghép native mastery với truth đã lưu

09/11/2026. Audit source/receipts nhỏ bằng PowerShell. Không Python/import/GAM/world/test/Git, không giải nén cache hoặc đọc oracle rows, chưa tính bất kỳ truth metric nào.

## Kết luận cho đúng hai quần thể được hỏi

**Không ghép trực tiếp RQDIAG12 với CPU09.** RQDIAG12 là18 policies/2160 ticks từ9 fixed histories seed20000–20002×PG/PY/PYH. CPU09 là120 world histories seed21000–21009×3 profiles×2graph-switches×2mechanisms. Seed sets không giao nhau theo manifests/source, nên không có trajectory identity chung được chứng nhận. Cùng notebook/bank không tạo cùng learner/history.

Trace native fixed-history dùng key `(seed,profile,event_id,variant)`, query có concept/question/difficulty/timestamp_iso/ns, state trước update gồm theta_est/pi_task/predicates28concepts, P và frozen estimator-state SHA. CPU09 key là `(seed,profile,graph_on,mechanism_on,step)` cùng concept/question/prediction/y/theta_before/p_true và gap fields. CPU09 không lưu global timestamp trực tiếp. Clock được dựng từ nguồn.

Ba khác biệt bổ sung chặn việc bỏ seed rồi ghép theo query hoặc ordinalstep:

- Fixed runner chọn randomitem ngoại sinh, preview select trên deepcopy, rồi update/bookkeeping theo logged query. CPU09 select thật rồi world phản hồi, history giữa arms có thể phân kỳ.
- Fixed clock tăng6h mỗi step. CPU09 nghỉ72h ở positive step chia hết28, còn lại6h. Cùng qid/t thứ tự không đảm bảo cùng pre-update state.
- Fixed full/empty bật native graphpackage, thay estimator edges và giữ local pathway. CPU09 dùng PathwayPolicy S=P on/off, L=False và world λ0/.55. Không có mapping variant→arm tương đương đã được chứng minh.

Các vị trí nguồn là fixed `historical_runner.py:44–88`, accepted `prediction_mastery_trace_worker03.py:25–27,72–109,369–407`, CPU09 `manifest.json:8–40`, current `run_approved_cpu_pilots.py:34–85` và `simulator_pathways.py:6–35`. Current CPU producer SHA55e8 khác recorded source SHAaea2 trong historical manifest, nên không gọi current wholefile là exact historical source. Geometry và treatment ở đây được kiểm chéo với chính manifest đã đóng.

## Một nhánh cache hẹp KHÁC đã có đủ native readout

Closed `research_tracking/runs/rq1-cpu09-observer-readiness-20261109-01/` chứa pilot03 đã accepted. `03__on.json` lưu120readouts của key `[21000,"PG",false,false]`, có step, selected fulltuple, prediction, timestamp, theta_est, stored/decayed pi, native_M và hai gates. `03__off.json` giữ cùng readouts/initial/final fullstate, là observer-OFF control. OFF/ON ở đây là instrumentation, không hai graph conditions.

Source pilot03`:526–583` dùng strict CPU09 reader+fullgrid validation rồi immutable observable projection, one fresh policy mỗi pass. Cả120selected tuples và queryP bits phải khớp cache trước capture/update. `capture_native` đọc nativeM trước currentY update, `replay_rq1_cpu09_native_mastery01.py::capture_native` kiểm literal theta>=1250 AND storedpi<=.55. Outer closed status là ACCEPTED_ONE_HISTORY_TARGETED_OBSERVER_OPERATIONAL_PILOT, errors rỗng. Full120worlds/truth accuracy vẫn chưa được claim.

**Có thể đề xuất cached-only ghép 120 rows riêng từ pilot03**, không cần GAM calls mới. Chọn bản ON đúng một lần, OFF chỉ đối chiếu integrity, không nhân đôi population. Khóa ghép gồm fixed key21000/PG/gOFF/λ0 +step; xác nhận concept/question/difficulty qua bank và exact queryP, clock/source SHA và toàn prefix120query/y được pilot admission. Nguồn truth là CPU09 `theta_before>=1250` đúng queried concept trước learning. `p_true` là xác suất sinh đáp án theo câu hỏi, không tự là mastery truth.

Ngưỡng đã kiểm trực tiếp từ notebook nguồn SHA353f487a…8280f. Cell3 dòng33 đặt `MASTERY_ELO = 1250.0`. Cell13 dòng50–52 đặt native M bằng `state.theta >= MASTERY_ELO and state.pi_task <= 0.55`. Cell9 dòng45/74 lưu `theta_before` từ `theta_at` trước learning, cell19 dòng61 dùng cùng `>= MASTERY_ELO` cho latent mastery. Replay helper dòng14–15,65–78 giữ đúng hai ngưỡng. Đối chiếu dùng số finite binary64 đã lưu và phép so inclusive nguyên bản, không làm tròn, epsilon hoặc binning. Dùng stored pi cho native M, không thay bằng decayed pi.

Target đề xuất là bảng agreement giữa native M và **tiêu chí latent của simulator tại theta1250**, trên concept đang được hỏi. Không tạo response-mastery probability hoặc truth về con người. Cần kiểm lại ba predicate fields trong mỗi native row từ theta_est/stored pi, nhưng không gọi policy. Timestamp phải bằng clock CPU09 bắt đầu UTC2026-01-01 và cumulative6h/72h, không chỉ ghép bằng step.

Acceptance trước một analysis mới gồm actual closed hashes/Job0/sourcepost, OFF/ON parity, strict original14400row/CRC/grid admission, exact120selected queries/P/clock và120unique ordered keys. Sau đó giữ đủ bảng2×2 nativeM/source-defined trueM kể cả zero cells. Chưa có counts truth trong audit này. Không cần và không nên lấy nativeM từ failed full01/02 hay partial native05.

Outer03 đã kiểm lại qua metadata nhỏ với receipt accepted/cleanup=true, Job0, environment restored và source_input_before bằng source_input_after. Outputs map của outer ghim đúng ON/OFF SHA và sizes ở bảng dưới. Analyzer tương lai chỉ parse các JSON/gzip đã ghim, dùng existing strict reader/validate_trace nguồn8590381c…6f1311, rồi lấy đúng một key đã chọn trước. Có thể đặt một operation stdlib tối đa10giây, compressed1MiB/decoded8MiB/line8192B, output nhỏ. Đây chỉ là scope đề xuất, chưa chuẩn bị hoặc chạy analyzer.

Đơn vị là120 correlated queried-concept/time rows của **một** history, một seed thuộc PG, gOFF/λ0. Chọn history trước cho operational pilot, không chọn theo accuracy. Không graph comparison, không population accuracy/calibration, không CI/pvalue/newN, không chứng minh uncertainty gate là lỗi và không hoàn tất RQDIAG23. Một Root-reviewed cached-analysis scope mới vẫn cần chốt trước khi đọc oracle labels. Nếu cần kết luận đa profile/arms/10seed như RQDIAG23, native readouts cùng14.400CPU09rows vẫn thiếu.

## Pins đủ quyết định bước tiếp

| Input nhỏ hoặc pointer | SHA-256 |
| --- | --- |
| CPU09 manifest | 371985977d32ddd1f3b95c3bab9858d20e4e463b2284b057f1b94db78c5f5cee |
| RQDIAG12 manifest | a45099f30ab6d4e239275fae6e40cf174b2dcac615fcb55a6e2b9d79f0c35ae3 |
| observer-readiness manifest | de9c9b9b938765ec95229a22d4df5c3f6cbbd1a5ab13ef1c21c5079ea134dfa4 |
| observer bundle03__on.json | a8b9c6479127d1f96dc84ac97f237242c8f25327c3d9dbe32cf40147481ad737 |
| observer bundle03__off.json | 3c3c82c4cc8a2a1f383f53597f7ea2530fca0a65930aaba9528402bedd4fa2a5 |
| observer bundle03-outer__final.json | 96ed606befb8205083db3caf3a325368483d609492ba709d0aabd4798486904d |
| observer bundle03__result.json | 3641869970dd612569f2849d919f616abce8196e0892c71d1d612457198922c6 |
| observer bundlepilot_rq1_cpu09_targeted_observer03.py | 1c84c3271556d2aa7b5d0ae709122504c2a4a008e8e9c4aa524d0345a10f5baf |
| CPU09 traces.jsonl.gz pointer, không mở ở audit này | 2a136fbf627cfa59170deec54c10ae562c2f8214eb00970ce41b96c43d065dcc |
| P/replay_rq1_cpu09_native_mastery01.py | 337677c160f56da0d1454785cb18cbe5eae6ac9019db76a6b59a9eb187e0ebad |
| Question bank đã ghim ở cả hai nguồn | fb5924ac0d19049ef1a5be23352592e30dfa3a4bde3e3fa07f10979fe0887e4d |

Native/readout JSON nhỏ đã đọc chỉ để xác nhận schema/header, không tổng hợp scientific rows. Báo cáo `rq1_native_mastery_reference_diagnostic_20261109.md` và prior feasibility02 cũng nêu rõ fixed9 khác CPU09. Khuyến nghị quyết định là giữ NO_DIRECT_JOIN cho RQDIAG12, chỉ chọn nhánh120 nếu ROOT chấp nhận giá trị của một limited descriptive witness. Không ép witness thay bằng chứng đầy đủ còn thiếu.
