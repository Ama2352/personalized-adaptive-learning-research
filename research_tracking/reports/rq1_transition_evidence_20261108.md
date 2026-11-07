# RQ1: thay đổi dự báo có đi cùng thay đổi quyết định? — 08/11/2026

## Kết quả chính cho GVHD

Trong **1.080 paired snapshots của fixed stream đã lưu**, full graph package có964lần scalar p(correct) của bài đang được hỏi khác graph-free. Trong964snapshots đó, **944lần concept action preview giữ nguyên,20lần khác**. Khi p của bài đang hỏi bằng nhau, vẫn có2/116snapshots khác concept preview. Vì vậy thay đổi một dự báo không đồng nghĩa thay đổi quyết định, và scalar p đang hỏi không đại diện toàn bộ trạng thái mà policy dùng để chọn action.

Đây là phân tích mô tả post-hoc từ **stored synthetic traces**, không chạy lại simulator/train/model, không Junyi/Holdout/GPU. Các tỷ lệ là **đồng biến có điều kiện tại cùng snapshot trước update**, không chứng minh một chuỗi tác động nhân quả prediction→mastery→ready→action. Để kết luận mediation cần thiết kế/interventions trên trạng thái và các pathways được kiểm soát; bảng này chưa làm điều đó.

Bằng chứng mới: [run `cpu-rq1-transitions-20261108-01`](../runs/cpu-rq1-transitions-20261108-01/README.md), [JSON phân tích](../runs/cpu-rq1-transitions-20261108-01/analysis.json), [bảng conditional CSV](../runs/cpu-rq1-transitions-20261108-01/conditional_tables.csv). Run đã đóng,12outputs được verify SHA; không sửa output sau closure.

## Dữ liệu và điều kiện join

| Nguồn immutable | Trace thực sự lưu | Phần phân tích được |
|---|---|---|
|`cpu-rq12-20261107-03/traces.jsonl.gz`|variant, learner_id=`seed-profile`, event_id, label, scalar probability,28mastery scores, explicit mastered concepts, ready set, concept preview|Join theo(learner_id,event_id) giữa các variants; đủ P/M/R/A ở cùng pre-update snapshot.|
|`cpu-closedloop-20261107-01/traces.jsonl.gz`|seed/profile/variant/step, concept/question/time, prediction và outcome; có oracle diagnostics tách nghĩa|Đủ kiểm actual served concept/question divergence theo cùng timestep. **Thiếu explicit mastered decisions và ready set**, nên full chain unavailable.|

Các manifests nguồn cho3seeds20000–20002,120steps/profile; profiles đọc từ stored comparison/outcome records làPG/PY/PYH. Fixed trace có3.240rows=3variants×9seed-profile trajectories×120steps; mỗi comparison có1.080paired events. Có9trajectory clusters, nhưng profiles cùng seed có thể phụ thuộc qua cách sinh/RNG: không xem9trajectories hoặc1.080events là independent inferential samples. Không p-value, CI hoặc significance/heterogeneity test.

Analyzer chặn duplicate/missing event identity, label hoặc concept mismatch, thiếu explicit mastery semantics và oracle field bị đưa nhầm vào fixed schema. Grid seed/profile/step phải khớp manifest.18hàng aggregate(9clusters×2comparisons) được reconcile **exact** với `comparisons.json`; helper comparator hiện hành SHA phải khớp helper SHA trong source manifest cũ. Toàn bộ output hashes của hai input bundles được verify trước phân tích;10selected input paths/SHA nằm trong JSON mới.

**Giới hạn identity cần giữ:** fixed trace không lưu current item/question/timestamp, cũng không lưu question/difficulty mà preview selector trả về. Hồ sơ/source run khai báo shared stream, và paired labels/keys khớp; từ trace riêng không thể independently audit toàn bộ query identity. Do đó “A giữ” ở báo cáo này chỉ có nghĩa **concept preview giữ**, không chứng minh mọi item-level action giữ. Không tự tái dựng trường thiếu bằng chạy simulator lại hoặc suy từ aggregate.

## Đơn vị và định nghĩa

P là khác nhau của **một scalar p(correct) cho current logged query**, theo exact float inequality như comparator nguồn; không là vector dự báo của28concepts. M là **ít nhất một explicit `is_mastered` decision khác** trong28concepts, lấy từ trường`mastered` đã lưu. Không dùng threshold p(correct) hoặc threshold mastery score để thay native decision. R là ready-set membership khác; A là concept action preview khác, được nguồn lấy trên bản sao policy để giữ stream cố định.

P/M/R/A đều được ghi trước current response update. Mastery/ready/action còn phản ánh lịch sử và trạng thái policy; preview có thể chọn concept khác bài đang hỏi. Vì thế không đọc các conditional rates như “đổi P tại eventt gây đổi M/R/A ngay eventt”. P giữ/A đổi không là causality violation hoặc hidden-path bug; R giữ/A đổi có thể phù hợp scores/ranking khác dù membership bằng nhau, nhưng bảng này chưa nhận dạng nguyên nhân đó bằng intervention.

| Comparison với graph-free | N paired events | P khác | M event(any concept) | Mastery concept crossings / concept decisions | R khác | A concept preview khác |
|---|---:|---:|---:|---:|---:|---:|
|Full graph package|1.080|964|90|90/30.240|60|22|
|Empty-graph package|1.080|37|0|0/30.240|0|0|

**90M events được tính riêng từ trace, không lấy số90concept crossings gán thành events.** Hai số trùng nhau trong dữ liệu này vì mỗi snapshot có mastery difference chỉ đổi1concept; không phải quy tắc chung và không phải90learners mới đạt mastery.30.240concept decisions=1.080×28, có denominator khác event-level tables.

Empty-graph package vẫn có local adaptation theo hồ sơ nguồn.37probability changes không có concept preview changes ở fixed stream là control quan trọng: package difference không tự là edge effect. Đây không chứng minh edges hoặc local pathway neutral/equivalent ngoài stream này.

## Bảng conditional: cùng snapshot, không nested funnel

Mọi dòng dưới dùng denominator **event pairs thỏa điều kiện ở cột đầu**, không dùng mastery concept count. N eligible=1.080, không có unsupported probability pair trong nguồn này. Nếu condition rỗng, analyzer xuất fraction=null, không tự gán0.

| Điều kiện — full package | Outcome trong cùng snapshot | Count / denominator | Tỷ lệ mô tả |
|---|---|---:|---:|
|P khác|M event khác|81/964|8,40%|
|P giữ|M event khác|9/116|7,76%|
|M event khác|R khác|60/90|66,67%|
|M event giữ|R khác|0/990|0%|
|R khác|A concept khác|5/60|8,33%|
|R giữ|A concept khác|17/1.020|1,67%|
|P khác|A concept khác|20/964|2,07%|
|P khác|A concept giữ|944/964|97,93%|
|P giữ|A concept khác|2/116|1,72%|

60/90 ở đây hợp lệ như tỷ lệ **event-level** vừa join: denominator là90M events được đếm độc lập, không phải lấy60ready changes chia trực tiếp90concept crossings của aggregate cũ. Toàn bộ4cells cho mỗi cặp và16patterns P/M/R/A nằm trong JSON/CSV, gồm các cells0. Có17action changes khi ready membership giữ; do đó không ép mọi A change nằm sau một R change. Trong fixed source cũng có1snapshot chỉ A khác trong cả4flags; các flags không tóm tắt toàn bộ numerical policy state.

## Phân bố theo trajectory clusters

Mỗi dòng là120paired snapshots; bảng giữ đủ seeds/profiles, không chọn seed thuận lợi. Các counts giúp thấy pooled22action changes không phân bố đều.

| Seed/profile — full package | P khác | M event khác | R khác | A concept khác |
|---|---:|---:|---:|---:|
|20000/PG|104|0|0|0|
|20000/PY|104|0|0|0|
|20000/PYH|104|0|0|0|
|20001/PG|108|18|0|15|
|20001/PY|108|0|0|2|
|20001/PYH|108|0|0|0|
|20002/PG|110|68|56|5|
|20002/PY|109|0|0|0|
|20002/PYH|109|4|4|0|

Không dùng khác nhau giữa PG/PY/PYH làm kiểm định ability moderation, hoặc xem90/60/22là bằng chứng profile nào có learning benefit. Chưa có uncertainty/inference plan hoặc independent final seeds cho kết luận đó.

## Hai trường hợp truy vết cụ thể

Examples được lấy theo thứ tự deterministic(seed,profile,event_id), tối đa3case/loại, không tìm case có effect lớn nhất. IDs là snapshot IDs của synthetic trace, không human learner IDs.

- **P khác, concept preview giữ:** full package, `20000-PG/event0`: p0,5→0,4941767101; M/R giữ, cả hai preview`BatPhuongTrinhBacHaiMotAn`. Đây là counterexample trực tiếp với suy luận “mọi prediction change phải đổi action”.
- **Concept preview khác khi ready giữ:** full package, `20001-PG/event11`: p0,3916974857→0,3887804755; M/R giữ, graph-free preview`PhuongTrinhQuyVePhuongTrinhBacHai`, package preview`HamSoBacHaiVaDoThi`. Nó xác nhận action-ranking outcome có thể khác trong cùng membership set; chưa xác định pathway gây khác.

Empty-graph example `20000-PG/event107` có p0,4795199144→0,4798308222 nhưng cùng preview`HieuKhaiNiemCoBanVeHamSo`, M/R giữ. JSON lưu exact floats và ready/mastered set differences để đối chiếu, không dùng current correctness label giải thích causal outcome.

## Closed loop: served action có thể khác, full chain còn thiếu

Closed-loop input có27trajectories×120=3.240served events. Mỗi comparison ở bảng là3seed pairs×120=360timestep comparisons/profile; không phải360independent learners hoặc cùng-target predictive trials sau khi histories khác.

| Profile | Full package served concept disagreements /360 | Empty package served concept disagreements /360 |
|---|---:|---:|
|PG|208|0|
|PY|200|2|
|PYH|72|2|

Question identity disagreement counts trong nguồn này bằng concept disagreement counts; analyzer kiểm cả concept/question và clock theo timestep, cùng actual action sequences trong stored outcomes. `closed_loop_action_audit.csv` giữ từng seed/profile và first-divergence step. Không tính paired probability contrasts hoặc calibration từ các rows đã chọn những items/histories khác nhau.

Closed trace **không có mastered/ready**: analyzer báo missing, không lấy`theta_before`, `p_true` hoặc latent diagnostics suy thành KT mastery và không fabricate full transition chain. Unit test perturb oracle diagnostic values không đổi observable action audit. Số action differences closed loop không được chia cho22fixed-stream preview differences để diễn giải amplification: hai modes có histories/logging khác nhau. Empty package fixed preview0không đồng nghĩa closed-loop served action luôn0; đã thấy2+2differences trong hai profiles ở mode khác.

## Kiểm thử, tái lập và bảo toàn bằng chứng

Tệp mới: `scripts/research/analyze_rq1_transitions.py` và `tests/shared_kt/test_rq1_transitions.py`. CLI không flags chỉ đọc/in JSON; không tạo run, không import/execute simulator hoặc model. `--run-id` mới tạo directory exclusive bằng evidence helper; run cũ không overwrite. CLI có budget60s, bounded gzip records/size; outer launchers cũng timeout60s. Không thêm/cài dependency. Matplotlib không có trong project `.venv`, nên dùng CSV/Markdown tables, không tạo plot thay thế không kiểm chứng.

25tests kiểm keyed join không phụ thuộc row order; duplicate/missing identities; label/domain/clock mismatch; explicit M event vs concept denominator; unknown P không bị gánfalse; empty-condition=null; identity zero arithmetic; oracle exclusion; closed action/outcome reconciliation. Trial01 PASS25/0,24s; sau bổ sung wording scalar P/bytecode read-only, final trial02 PASS25/0,21s(wall0,8662s). Không có failed analysis/test trial trong gói này. Logs/invocations ban đầu giữ ở `artifacts/akt/local-tests/parallel-rq1-transitions-20261108-{01,02}/`.

Default read-only analysis đã chạy0,4068s. Final exclusive analysis/archive chạy wall0,5891s, **12outputs verified**, gồm source/test snapshots và final targeted log/XML. Source chỉ dùng stored traces/aggregates và legacy comparator; không simulator/train rerun.

```powershell
# Default: stdout JSON, không ghi run.
& .venv\Scripts\python.exe -B scripts/research/analyze_rq1_transitions.py

# Tạo bằng chứng mới; phải chọn run-id chưa tồn tại.
& .venv\Scripts\python.exe -B scripts/research/analyze_rq1_transitions.py --run-id <run-id-moi> --test-evidence-dir artifacts/akt/local-tests/parallel-rq1-transitions-20261108-02
```

| Source/output | SHA-256 |
|---|---|
|Analyzer source|`0a79f45fd7ef9bea9deddaab0644e1b652e1dd945d6caa6577ce5bd67b1e1d59`|
|Tests source|`26f52e9d842f6653f66c9568690b6020cf29fcc8b4ef0698e0d5ca170367fef1`|
|New analysis.json|`597d4ce320af4601665d206b7ffe1fe1250ebd96114893e87a53e70ff49d3d28`|
|New run manifest|`ff09520a20c7d0b6cbe18bdbfad3d4017e3106ca8628aa9cd2d38a4cb6591827`|
|Fixed stored trace gzip|`22b065e8e0206403d2bcd41d175eeb1d686ed8bbf204c64f74d0e93d2aca0497`|

Input/output hashes đầy đủ nằm trong analysis/manifest. Không chuyển/sửa old runs hoặc root index/state/Git. Hai source/test additions làm source-bound Gate cũ stale; chưa chạy full software gate mới ở tiểu tác vụ này.

## Câu được phép và chưa được phép kết luận

**Có thể viết:** “Trong fixed-stream synthetic diagnostic đã lưu,944/964snapshots có p(correct) current query khác nhưng concept preview giữ. Conditional event tables cho thấy prediction/mastery/ready/action differences không tạo một nested funnel; kết quả mô tả cần được phân biệt với learning efficacy và causal mediation.”

**Chưa được viết:** “Graph cải thiện học tập97,93%”, “2P giữ/A đổi chứng minh bug”, “90learners đạt mastery”, “empty graph chứng minh edges vô ích”, “closed-loop causal chain đã được xác nhận” hoặc “RQ1 đã hoàn tất”. Muốn vượt mức bằng chứng này cần full state/query instrumentation, component ablations/interventions, outcome validity/calibration và protocol/inference được chốt trước dữ liệu xác nhận mới.
