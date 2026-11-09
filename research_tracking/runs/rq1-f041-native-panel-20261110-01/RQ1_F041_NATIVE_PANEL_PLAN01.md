# RQ1 · First-pass native panel trên F041 đã lưu

**SOURCE-ONLY. Chưa chạy hoặc cấp allocation thực thi.** Root chọn một policy trên lịch sử F041 đã có. Không chạy OFF variant hoặc ghép quần thể này với witness PG120 cũ. Main panel protocol và mastery S04 của hệ thống mới vẫn có phạm vi riêng.

## Vì sao chọn F041

F041 là cell đầu tiên ngoài high-controls trong thứ tự plan fresh120 đã đóng, có block21010, năng lực nền1000, graph estimator full, λ0, S/P bật và L tắt. Chọn theo thứ tự thiết kế, chưa dựa dấu hoặc accuracy của panel. Cell này thuộc61 cell parent02 hoàn tất, được recovery03 kiểm và tái dùng trong primary120. Parent02 vẫn giữ status failure của toàn operation cũ. Không đổi nó thành completed run.

Khác CPU09 witness cũ, F041 có actual initial snapshot đủ28 base/theta/last_seen dưới encoding float_hex, cùng full environment state SHA trước mỗi interact và endpoint cuối. Vì vậy có đường dựng lại latent toàn miền từ chuyển trạng thái đã ghi, không tạo lại persona hoặc world. Chỉ metadata/keys/schema/SHA đã được đọc cho bản plan này, chưa tính latent panel hoặc accuracy.

## Luồng native một policy

1. Kiểm actual recovery acceptance, parent proof61 và đầy đủ SHA các nguồn/input. Nạp source Paper2 qua loader definitions hiện có, không chạy notebook top-level. Dùng graph full và `build_pathway_policy(signal=True,parent_adaptation=True,local_adaptation=False)`. Kiểm initial policy fingerprint bằng initial snapshot F041 cùng namespace/source/graph identities. Không load learned estimator, fit confidence hoặc import Torch.
2. Strict reader đọc bounded JSONL, chỉ chiếu120 dòng observable của F041 thành immutable query, timestamp, P đã lưu và current Y giữ ngoài getter/predict. Kiểm unique steps0–119, bank concept/question/difficulty, timestamp ISO/ns và source clock6/72giờ. Không lấy F062 partial hoặc ghép dòng từ cell khác.
3. Với từng bước, gọi `with recorder.capture(step=t,timestamp=logged_iso): selected=policy.select()`. Dùng canonical recorder b54b để lấy đúng first28 native M getter returns đang có, không thêm `is_mastered`, score, predict, ready_set hoặc shadow-select.
4. Selected concept/question/difficulty phải khớp byte/binary64 với query gốc. Gọi predict thật đúng một lần và so P binary64 exact. Sau đó mới truyền current Y và P vào update thật đúng một lần. Ghi3360 snapshot concept–thời điểm từ recorder, giữ θ, stored π, attempts/last_timestamp và boolean gates. Hết mỗi capture phải phục hồi descriptors, không stale/pending/cleanup error.
5. Đủ120 actions/P/updates, attempts tổng120, source/static/RNG và cuối policy fingerprint khớp endpoint gốc trước admission. Raw native panel cùng parity receipt được đóng trước khi evaluator join latent. Không diễn giải partial timeline nếu bất kỳ assertion hoặc cap nào fail.

Native M là `theta >= 1250.0 && pi_task_stored <= 0.55`. Không thay π lưu bằng π decayed hoặc biến getter M thành xác suất. Không gọi thêm decayed getter cho28 concept. Score/response calibration của S04 chưa được kiểm ở đây.

## Evaluator latent từ actual stored transitions

Giải mã base và theta bằng `float.fromhex`, last_seen từ saved initial, yêu cầu đủ28 đúng node order. Đây là container trạng thái evaluator, không tạo `LatentStudentEnvironment` hoặc result giả. Có thể gọi unbound source `LatentStudentEnvironment.theta_at(container,cid,t)` nguyên bản sau khi kiểm globals/source. Phương thức chỉ cần base/theta/last_seen, không gọi interact hoặc RNG. Điều này phải được chứng minh tĩnh trước dispatch.

Tại mỗi t, trước khi áp dụng transition đã lưu, canonicalize toàn bộ container bằng helper state_data nguồn đã đóng và so SHA với `environment_readonly_probe_sha256` của đúng oracle row F041. Tính θ_at cho cả28. Concept đang hỏi phải khớp `oracle_theta_before` và `result.theta_before` exact. Criterion latent là θ_at≥1250, cùng ngưỡng θ của native getter, không dùng ngưỡng1150 của learning deficit.

Sau khi ghi panel prestate, cập nhật container chỉ bằng hai phép gán nguyên nguồn đã có dữ liệu.

```python
theta[cid] = min(1600.0, recorded_theta_before + recorded_learning_gain)
last_seen[cid] = logged_timestamp
```

Không tính lại outcome, challenge, deficit hoặc learning gain. Không dùng uniforms hoặc Y tương lai để thay transition. Sau120 bước, so full final environment_state với endpoint, và cả28 giá trị θ_at tại timestamp cuối với `final_snapshot`, exact binary64. Như vậy mỗi prestate đều có fullvars hash admission, không chỉ kiểm concept đã hỏi.

Toàn bộ3360 rows phải có native/source identity và timestamp khớp. Các giá trị latent toàn miền là **dựng lại bằng phương trình nguồn từ initial/transitions đã ghi**, không ghi trực tiếp trong trace lịch sử và không backfill artifact cũ. Trường hợp hash hoặc endpoint không khớp phải STOP, không tolerance, sửa nhãn, bỏ concept hoặc tự chạy lại world.

## Output và diễn giải hữu hạn

Giữ raw panel3360 dòng, parity và evaluator lineage/endpoint receipt. Một bảng joint3360 gồm queried flag, native gates/M và latent criterion. Summary giữ số concept/time, confusion2×2 cho all28 và subset120 queried, cùng denominator và zero cells, không AUC nếu class support không đủ. Không metric calibration từ current item Y. Không ép phải có positive class hoặc uncertainty suppression opportunity.

Đơn vị là một lịch sử của một block, **N1**,3360 repeated measurements. So queried với all28 trong cùng lịch sử nhằm phát hiện conditioning của việc policy chỉ hỏi một số concept. Đây không phải causal effect của việc chọn concept hoặc 3360 người học độc lập. Không graph comparison, CI/p-value hoặc suy lợi ích dạy học. Không thay main S04 hoặc full RQDIAG23 population.

## Call/resource ledger đề xuất

- Một policy builder,120 select,120 predict và120 native update thật.120 capture tickets,3360 first-pass native M observations. Parent/getter calls lặp trong selector giữ nguyên, chỉ count theo scope, không coi là thêm rows. Getter M trong update nằm ngoài capture.
-3360 pure theta_at evaluator calls,0 environment constructor/interact/persona generator/world RNG/NN/optimizer. Không tạo response mới. Không dùng saved uniforms làm input policy.
- Cap mới đề xuất whole60giây, worker50, owned55 gồm cleanup3 và outer finalization5. FamilyRSS512MiB, free1536MiB, admission hệ thống2GiB. Root review/đo lại trước GO, không tự nới cap hoặc retry. Các lane cũ giữ nguyên lịch sử.
- Input oracle JSONL≤4MiB, observables≤2MiB, endpoints≤1MiB, initial≤32KiB. Bounded line16KiB và filter exact120 chỉ giữ một cell trong bộ nhớ. Không dump oracle lớn hoặc copy raw inputs vào bundle.
- Readouts lớn giữ `experiments/gam_kt/results/rq1-f041-native-panel-20261110-01`, path mới độc quyền. Mỗi JSONL≤4MiB, tổng output≤12MiB, metadata≤256KiB. Outer/owned logs ở prep. Không source hoặc runtime changes trong worker.

## Source/input pins

Parent native directory là `experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02`.

| File | SHA-256 |
|---|---|
| initial-F041.json | `094ad79478f7d028f03219055b0aa4dd1b9e9492fbad45ff3044ebfdd683c10c` |
| observables.jsonl | `bebfc34e228e5d914ea46b6745aa8f282841308fc8b11c2d07e755b5ab420515` |
| oracle.jsonl | `7405bc63484927790e3e624b1a3ed15f861d0fa2db7e36514a412dacfacb43b8` |
| oracle_endpoints.jsonl | `e2d599b94cdb835c3771d33f68f362aa44157a1d68ee788fdce46ed677e8366d` |
| worker_run.json | `0d31ee04abbebb6dc69c8d66ac040f1f4c233047be7381567bb678a07b438b1e` |
| shared_inputs.json, metadata origin only | `f14e91731535a351ca91d83d69ebe7aa287def900a71bb9de85d6fb9717ebc64` |

Recovery plan `P/rq2_fresh_graph_recovery03_plan.json` SHA `59cf05947f0d2ff184af99070b5b58fe771b5e3134fb1e1c71241d3eb46a7ea2` ghim các file parent này và parent proof `9551e0b85ca48cb5fe05236b6ee8bc75e0c471fc2e17d48c5f751a23ff845f95`. Recovery bundle manifest `deff815a7360ab9d0ffcaf06e986ff2fc14ed07aa0ab8366880ade34445df11e` đóng plan cùng acceptance, nhận61 parent cells sau kiểm đầy đủ. Không giả parent failed operation đã hoàn tất toàn bộ.

Recorder canonical SHA `b54b5f9a0899ec46b3e90d98b283fb34c84adaae5d2f47a581e405962bc936ba`, canonical test SHA `17918e2d7d1ac4e39788af78a608bbfeff07e5bc9fd9bb9d2d1cef6c2de937f6`, canonical bundle manifest `b7678408278acc87eb8c96da2039fdd8681c78553c736bb71ebfbd96d81e3817`.

Notebook SHA `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f`, loader `a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1`, pathways `33ad34140f7b08eb22f86e6cc3caf7b0e7c98f09e4fd74945a6f7e9718b07560`. state_data/fingerprint có nguồn `research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/worker.py` SHA `973a1973da7982aac9a44b4112786915a127447ac57c6bce07f51c06e381f119`, chỉ chọn definitions cần thiết, không thực thi worker lịch sử.

Initial F041 ghi environment SHA `02a3c803a3d6da64ff3df9cbabfa2e0a003326c667bef28d9f1ff873928860da`, policy SHA `1b3057bf6f694835739d670702876908caa654cea05c7aa0428ddcf2650372fa` và treatment SHA `dd493cea969361b6b7fb143faaf8e1d266728d226839647be3f6267f8fd02a96`. Các SHA này cần được tính lại từ actual state tại admission, không dùng shape hoặc hash-shaped string làm evidence.

`P` là `artifacts/akt/local-tests/akt-research-runner-20261108-01`. Worker/outer chưa được viết hoặc chạy trong bản plan này. Root cần review source và allocation cụ thể trước dispatch.
