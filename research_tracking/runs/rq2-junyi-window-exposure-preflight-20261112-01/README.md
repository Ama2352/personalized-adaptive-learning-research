# Preflight đối chứng thứ tự trong native window TRAIN80

**Trạng thái mới nhất** — Root đã duyệt và chạy fullscan. Kiểm toàn bộTRAIN80 đạt, kết quả và giới hạn ở [FINDINGS.md](FINDINGS.md). Checker độc lập đã đối chiếu64windows và tổngCSV. Các phần preflight/admission bên dưới được giữ theo diễn tiến, không mô tả trạng thái hiện hành thay cho cập nhật này.

## Verdict

Nguồn và schema đủ để đo exposure đồ thị trong đúng context của AKT, chỉ dùng cache TRAIN80 outer4. Chưa chạy scan NPZ hoặc đọc correctness trong lượt này. Phạm vi runtime180giây chưa được đo cho analyzer mới, nên **chưa cho phép tuyên bố fullscan sẵn sàng hoặc tự dispatch**. Bước tiếp theo sau Root review là một admission/throughput nhỏ có cap, rồi quyết định scan đầy đủ bằng thời gian còn lại.

## Đầu vào đã xác định

| Nguồn | Identity và phạm vi |
|---|---|
| `artifacts/akt/window-cache/full-train80-20261112-02/manifest.json` | COMPLETE, select_train80,232.662windows,13.347.331targets,126.774learners,23.936.131windowtokens,0OOV.909shards, tổng1.332.294.249byte |
| `artifacts/akt/window-cache/full-train80-20261112-02/COMPLETE.json` | Trỏ manifestSHA43f48045370b6811e537d7936ed307291e1dee88be313c111e4879198556a839 |
| `artifacts/akt/window-cache/full-train80-20261112-02.encoding.json` | Vocabulary717exercise, encodingidentity0555833f58150121f1149ac7d3c4d0f0cad057b2dc530331e5ffbe83fc040ba1 trong cachekey |
| `research_tracking/runs/cpu-junyi-graph-reconstruction-20261107-01/graph.json` |835nodes/976correctededges, cùng byte với corrected_graph.json của controls mở rộng |
| `research_tracking/runs/cpu-junyi-controls-20261107-02-expanded/matched_controls.json` | Ba graph cố định seed0/1/2, mỗi graph976edges và40symmetric-difference entries so base |
| `research_tracking/runs/junyi-throughput-20261112-01/full-strict-result.json` | Strict admission lịch sử đạt232.662records/13.347.331targets trong87,08giây, sampledRSSkhoảng64MiB. Đây là benchmark reader khác, chưa phải analyzer exposure |

Preflight chỉ đọc manifest, encoding, graph và receipt nhỏ. Không mở shard, parquet hoặc danh sách nhãn. `metadata-check.json` giữ pins và phép đếm topology/vocabulary. Base có890cạnh với cả hai endpoint fitted,28cạnh parentkhôngfitted nhưngchildfitted và58cạnh childkhôngfitted. Ba control có lần lượt40/38/37changedentries với cả hai endpoint fitted. Fulltopology976cạnh phải được giữ trong bảng, kể cả cạnh không có support.

## Entry point tối thiểu cần cài sau review

Một analyzer riêng trong bundle thực nghiệm kế tiếp là đủ. Không sửa productioncache hoặc confidencefitter. Dùng `.venv`, NumPy hiện có và stdlib, không Torch. Hai mode của cùng script là admission nhỏ rồi fullscan, với cùng recipe đã freeze. Output tạo exclusive, có progress/counts và trạng thái partial nếu cap dừng. Một manifest fullscan chỉ hoàn tất khi đủ909shards/232.662windows/13.347.331targets/126.774learners và mọi inputpin giữ nguyên.

Không gọi `_load_shard`, `_parts` hoặc `JunyiWindowCacheSession` cho phép phân tích label-free này. `_load_shard` materialize cả `targets` và `prior_responses`, các bước validation tiếp theo cũng đọc chúng. Thay vào đó, dùng `np.load(...,allow_pickle=False)` ở chế độ đọc chọn lọc đúng `offsets`, `metadata`, `item_ids`, `target_mask` và nếu cần `global_ranks`. Không truy cập hai array nhãn nói trên. Manifest/shard SHA vẫn được đối chiếu, ZIP membernames/dtypes/shape/expansion/offset bounds vẫn phải kiểm. Hash byte toàn shard phục vụ integrity, không giải mã hoặc dùng nội dung correctness. Ghi rõ đây là label-free exposure audit, không thay strict production admission đầy đủ.

Mỗi window bắt đầu lại prefix rỗng. Tại target vị tríj chỉ xét itemids[:j], đúng semantics `research_junyi_graph._prefix_evidence`. Nativecontext100/targetblock100 có thể tạo prefix tới199event, nên không dùng lịch sử toàn learner hoặc cửa sổ trượt100tự viết. Chỉ các vị trí targetmask được tính vào mẫu số. Context lặp qua windows không tạo thêm target. OOVbarrier đã nằm trong cachegeometry. TRAIN80 hiện không cóOOV, nhưng analyzer vẫn từ chối id ngoài encoding.

Để giảm CPU, có thể dựng bitset vị trí từng item cho window tối đa200token. Với cặp parent→child, tạo bitset các target của child. Parent có mặt trước target khi vị trí target lớn hơn vị trí parent đầu tiên trong window. Dịch bitset rồi bit_count cho đúng số target đủexposure, không cần quét13triệu×976cạnh. Số lượng parentobservations hoặc meanresponse không thuộc phép kiểm này. Nếu cần supportmultiplicity về sau, phải thêm đại lượng riêng thay vì suy ra từ firstoccurrence.

## Đại lượng và nghiệm thu

- Với mọi declared/control edge, lưu số target của child, số target có parent trong effectiveprefix và số TRAINlearner góp target đủexposure. Cạnh unsupported vẫn giữ0vàreason. Tính learnerunique bằng setcạnh hữu hạn cho learner hiện hành rồi cộng khi learner kết thúc, tránh learner×edge tensor.
- Với từng symmetricdifference, tách added/removed và endpointsupport. Tại mỗi target, đo có ít nhất một changededge thực sự cóparentprefix hay không. Đây là changededgeexposure, khác số node/edge topology bị đổi.
- Bảng so sánh phải giữ cùng13.347.331targets, không lọc mỗi graph theo một population khác. Báo cả alltargets và targets cóincomingedges. Nếu thêm exposedintersection thì báo attrition riêng.
- Identitycontrolbase-versus-base phải có0changedentries/0affectedtargets. Fixture item tại current/futureposition không được tính làm priorparent. Fixture windowrollover phải mất parent ở ngoài nativewindow. Output không có accuracy/LL, không causal instructional claim.
- Đơn vị mô tả gồm target và learner, không có kiểm địnhp hoặc chọn graph theo lợi thế metric. Nếu đủsupport cho predictive controls, phải freeze control trước dùng selection/evaluation.

## Giới hạn thời gian và RAM

RSScap256MiB, outertimeout180giây, không thực hiện cùng lúc với tác vụ local ăn RAM của nhánh chính. Admission đọc đúng first16shards đã định trước, cap15giây, ghi bytes/windows/targets/RSS và wall gồm kiểmSHA. Đây là kiểm workload riêng, không phải kết quả fullTRAIN. Chỉ tiếp tục scan đầy đủ sau Root review nếu ngoại suy bảo thủ từ bytes và windowtokens, kèm headroom, nằm trong cap180giây. Nếu vượt cap hoặc chưa chắc, dừng và đề xuất scan resumable/chunkbudget riêng. Không giảm coverage hoặc gọi partiallàcomplete để vừa cap. Số87,08giây của reader cũ chỉ là căn cứ khả thi sơ bộ, chưa đủ bảo đảm runtime.

## Cảnh báo provenance của negative controls

Ba control cũ được dựng trên outerfold0innertrainprefix256×300, gồm các bins support từ cohort đó. Phân tích chúng trên TRAIN80outer4 là sensitivity với graph cố định kế thừa. Không được gọi chúng là control được dựng riêng từ TRAIN80outer4. Để dùng trong benchmark leakage-controlled hiện hành, cần freeze recipe và tạo matchedcontrols theo support TRAIN80outer4 hoặc mô tả rõ nguồn ngoại sinh đã nhìn dữ liệu nào. Không tự chuyển quyền/phạm vi của pilot cũ thành quyền scan mới.

Hai cách mã hóaSHAgraph đang cùng tồn tại. `corrected_edge_set_sha256` chỉ đại diện edge-set theo serializer của reconstruction. `graph_controls.graph_fingerprint` gồm nodes/edges/direction và được các control dùng làm originalSHA. Preflight đã tính đúng fingerprint4002d378692761d68d0e2ec69afc4857a4d73e22850cf33c03ad15b16001899c và xác nhận cả ba control cùngbase. Không coi hai loạiSHAkhác nhau là graphmismatch.

## Phần chưa thực hiện

Chưa admission16shards, chưa fullTRAINexposure, chưa tạo graph mới, chưa confidencefit, chưa predictivecontrol và chưa sửa protocol. Root cần review khả năng đọc chọn lọc array và thời gian mẫu trước khi cho chạy. Bộ preflight này không thêm sourceproduction, training hoặc cloudjob.

## Admission đã được Root duyệt và thực hiện

Phần này cập nhật trạng thái preflight ở trên. Root cho phép đọc16shards đầu, cap15giây/RSS256MiB, catalogbase duy nhất. `analyze_exposure.py` đã chạy admission và lưu `admission01/result.json`, `inputs.json`, `progress.json`, `edge-exposure.csv` cùng log. Có4.096windows,247.190targets,447.390windowtokens và2.094learner xuất hiện trong phần này. Learner cuối có thể chưa đầy đủ. Những số này không đại diện toàn TRAIN80.

Lượt thực thi hoàn tất0,389giây, peakRSS38.862.848byte. Cả6fixture kiểm current/futureparent, contextmask, resetwindow và ranh giới priorj đều đạt. Reader chỉ materialize offsets/metadata/item_ids/target_mask/global_ranks. Không mở arrays targets/prior_responses, không Torch hoặc cloud. Hash nguyên bytes của16shards đối chiếu manifest. Có604/976cạnh có ít nhất một target quan sát parent trong effectiveprefix của admission, chưa suy lực kiểm định hoặc đủ support cho benchmark chính.

`runtime-projection.json` dùng tỷ lệ lớn nhất giữa bytes/windows/tokens/targets để ngoại suy tuyến tính khoảng22,1giây. Mức lập kế hoạch bảo thủ bằng3lần cộng15giây là81,3giây, dưới cap180giây. Đây là dự phóng từ prefix có khả năng hưởng diskcache. Chưa đo fullscan hoặc bảo đảm thời gian. Script có `--mode full` và yêu cầu `--full-review-reference`, nhưng chưa được chạy mode này. Root cần review trước bước tiếp theo.

Command đã chạy là `.venv\Scripts\python.exe -B research_tracking/runs/rq2-junyi-window-exposure-preflight-20261112-01/analyze_exposure.py --mode admission --output-name admission01`. Script tạo outputdirectory mới để tránh ghi đè. Nếu lỗi hoặc vượt cap, ghi failure và giữ progress. Không import code mô hình. `execution-proof.json` ghi command/source pin và outcome, còn `manifest.json` giữ inventory bundle đang mở chờ nhánh chính nghiệm thu.

## Fullscan và kiểm độc lập đã đạt

Nhánh chính review qua `root-full-review.json`, chạy modefull và lưu kết quả tại `full01/`. Đã kiểm đủ909shards/232.662windows/13.347.331targets/126.774learners, runtime21,3538giây và peakRSS49.938.432byte. Catalog có876cạnh với priorparentexposure,58cạnh childunfitted,28cạnh parentunfitted-childfitted và14cạnh cảhai fitted chưa cóexposure. Không chạy controls cũ hoặc model trong phép này.

`check_exposure.py` dùng seen-set độc lập, kiểm64windows từshards0/129/259/389/519/649/779/908,8window phân bố đều trong mỗi shard. Nó chỉ mởoffsets/item_ids/target_mask, đối chiếu bitset từngedge/window và kiểm số họcCSVfull976rows. Đạt3.827sampletargets, runtime0,0721giây và peakRSS36.425.728byte trongcap30giây/256MiB. Giữ `independent-full-check.json` và log. Không rerunfullscan.

Figure duy nhất `junyi-native-window-edge-coverage.svg/.pdf/.png` và `figure-data.csv` trình bày bốn nhóm cạnh tách biệt. `build_figure.py` dùngmatplotlibtrong.venv, palette/quyướcfigures4papers đã có, khôngcài global. PNG đã được mở để kiểm nhãn số/trục/tiêu đề/chú thích, không thấy đè/cắt chữ. Giữ source và phiên bản vector để tích hợp report. Đây là figure về exposure, không đồ thị chất lượng dự báo.

## Nghiệm thu Root sau fullscan

Đã đối chiếu toàn bộ27file trong inventory mở, sourcehashkhớp bản duyệt trướcfullscan, fullcoverage vàruntime/RSS, bốnnhóm976edges vàhai tổngedge–target từCSV. Checker64windows vàfigurePNG đã đượcRootđọc. Chấp nhận phạmvi potentialexposure trênTRAIN80, không predictivebenefit hoặc edge truth. Bundle đượcđóng, kếtquả cóthểtríchqua FINDINGS.md vàcặp báo cáo hiệnhành.
