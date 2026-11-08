# Contract revision02 — tái dựng C/B và khóa chọn CID trên fixed stream

## Sửa đúng semantics bảng chương, không đổi dữ liệu hoặc phép so

Revision01 bị từ chối trước outputs tại guard `set(chapters)==set(nodes)`. Kiểm nguồn archived loadera12edc… lines61–67 cho thấy loader giữ **full dict** rồi lookup trực tiếp các node để lấy tập tên chương, không yêu cầu keyset bằng nhau và không điền mặc định. Metadata thật có28nodes,36chapterrows/36uniqueIDs,0missing requirednodes và8unused extraIDs. Đây là guard phân tích quá chặt, **không phải dữ liệu thiếu chương hoặc lỗi khoa học của nguồn**.

Revision02 giữ đủ36entries và28nodes, cho phép requirednodes⊆chapterkeys; native dict last-wins nếu duplicate và ghi coveragecertificate missing/extra/duplicate. Không drop nodes, không tự tạo chương.4fixtures mới kiểm superset, missing-required STOP, native last-wins và extras không đi vào chapter_names/tiekeys. ROOT yêu cầu chạy đủ18methods (14cũ+4mới) trên nguồn02 như regression; chưa có kết quả18ở lúc chuẩn bị source. Old14PASS chỉ áp dụng nguồn01, không tự thừa kế PASS sang02.

Nguồn01/analyzer e627…, tests711…, contracteddde…, cả hai controller và16rawcapture/ownedfiles đã inventory trước sửa tại `pre-fixed-controller-chapter-coverage-fix01/inventory-before-and-copy-verification.json` SHA42673927227f80b2e8160f0864e239228370662ca2f78cfb533ba506bacb7898; tất cả01bytes giữ nguyên. Cached01 ROOT quan sát0,9915271s và0modelcalls, không outputs; đó là failed admission, không phát hiện nghiên cứu. Source02 không tự cấp quyền chạy lại/reset allocation; ROOT review18tests và một operation cached02 max10s riêng, giữ ledger01.

**Chỉ chuẩn bị source/fixtures trong prep. Chưa chạy hoặc có kết quả mới.** Không đổi154nguồn Gate, không gọi policy/predict/update/select/teacher/RNG/trainer, không fit calibration. ROOT review pins rồi mới cân nhắc một cached run ≤10s,0model/native/simulator/newN. Đây là source-reconstructed controller analysis, không phải C/B được observer ghi trực tiếp.

## Chọn một câu hỏi có thể thay đổi diễn giải

Các marginal và cross-ready đã biết có55R đổi/preview giữ,17preview đổi khiM/R giữ và5jointchanges. Điều chưa biết là **những membership khác biệt còn có mặt trong tập C sau anti-repeat và B sau cân bằng visits không**, và native CID có được giải thích chính xác bằng khóa xếp hạng đã lưu hay không. Nếu tái dựng đúng, có thể phân biệt membership bị loại trước ranking với active pool đổi nhưng cùng thắng; không chỉ lặp số đếm R/A. Không gọi những phân loại này là causal mediation, tỷ lệ đóng góp đồ thị hoặc lợi ích giảng dạy.

Đã tìm trong transition/score-vector/full–empty/cross-ready/exposure/closed-loop-ranking reports: closed-loop có C/B và source-local ranking khác population; fixed1080chưa có phép tái dựng C/B+key này. Giữ các báo cáo/bundles đã đóng nguyên trạng, chỉ bổ sung bản phân tích mới nếu mọi parity đạt.

## Dữ liệu thật sự có và không có

Đã đọc một record thật từ mỗi gzip chỉ để kiểm schema: legacy có `variant,event_id,learner_id,correct,probability,mastery,ready,action,mastered`; `mastery` có28scores. Sidecar có actual query concept/question/difficulty/timestampISO+ns, full preview concept/question/difficulty, captured phases, update pairing và legacy-row SHA. Không có per-event theta/pi, C/B, recent/counts/chapter hoặc label cho câu hỏi tham chiếu1250. Không suy latent state còn thiếu từ P hoặc S.

Calibration-at-mastery chưa nhận dạng được: source GAM `is_mastered` dùng `theta>=1250 AND pi_task<=0.55`. S là score của virtual concept feature tại1250, khác actual query P về difficulty/item feature và time-decayed uncertainty. Một y của câu đang hỏi không là nhãn của virtual concept probe. Có thể chấm response P trên query thật nhưng việc đó không trả lời calibration của mastery; không thêm một thí nghiệm calibration không đúng ánh xạ.

## Vì sao C/B có thể tái dựng mà không thêm lời gọi khoa học?

Fixed runner gốc đã recovered Git `e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a`, rawSHA402dca…dd45. Thứ tự: original predict → deepcopy select → original S/M/R snapshot → original update → tăng counts/recent/chapter bằng **logged query**, không preview. `_init_selector` đặt visits0/recentdeque3/chapterNone. Vì các nhánh dùng cùng query prefix, tie context trước mỗi event suy được chỉ từ toàn bộ query CID quá khứ, không nhìn y hiện tại/tương lai.

Source selector cell11, SHA `fc616cb9d5067419950cfc4a5e0ae0c2a02afc0d78b6ae86dd72f87224f42310`:

1. Reconstruct R đầy đủ: unmastered frontier với parent M hoặc visits≥6; all-mastered trả allnodes; thiếu frontier trả min unresolved-parent deficit theo M, không trừ exposure.
2. C=R, rồi literal anti-repeat/escape khi3pastCID giống nhau. Escape có thể thêm concept ngoài R; không ép ownCID∈R.
3. B gồm candidates có visits≤minvisits+1.
4. CID=`min(B,key=(storedS[c],chapter_tie,visits[c],cid))`. Chapter tie đặt trước visits và lexical CID; float dùng đúng binary64 đã lưu, không tolerance/rounding/ties khác.

GAM cell13 SHA99d10d…25f1: `mastery_score/_context` chỉ đọc estimator state/features, không selector visits/recent/chapter và không mutate state; `select` chỉ cập nhật bookkeeping **sau** lựa chọn CID. Vì thế S28 của original snapshot bằng giá trị khóa trên preview copy trước bookkeeping. Không cần gọi mastery_score thêm. Controller graph vẫn full ở cả full/empty vì loader rebind mixin từ controller scope; không dùng empty estimator graph làm controller graph.

## Acceptance trước mọi diễn giải

- Exact1080keys×3variants/raw3240dòng, cùng actualquery/y/phases và11oldflags; không intersection/drop. Full/empty là2160CID cần kiểm tất cả, không chỉ22changed cases.
- Hai source M→R phải khớp storedR membership tại cả2160snapshots. Native R order không được log (frozenset); có thể tái dựng order từ nodes source nhưng chỉ gọi đó là reconstructed, không observed-order parity.
- Reconstructed min CID phải bằng cả legacy action và sidecar previewCID tại2160snapshots. B không rỗng, selected∈B⊆C; R không buộc subsetC hoặc selected∈R vì escape. Nếu bất kỳ mismatch, STOP và giữ rejection; không điền hidden state hoặc đổi threshold/order để làm khớp.
- Shared visits/recent/chapter chỉ tăng bằng query CID **sau** snapshot; validate cả3variantqueryidentity trước cập nhật. Question chooser/difficulty/ability không tái dựng: phân biệt CID changed, full tuple changed và qid-only changes. Không tự gọi17full-preview changes là ranking explanation nếu CID không đổi.
- Reconcile oldMRA128cells/16groups và pooled963P/90M/60R/22CID/fulltuple changes. Allzero/cases giữ nguyên; source pins/inputs trước=sau; no newN.

## Outputs định trước

Một pair row cho mỗi1080key: shared prehistory counts/recent/chapter, hai R/C/B reconstructed sets và chosen native key; source-mapped node indices để không nhân đôi hàng loạt tên dài. R/C/B added/removed, cross-B membership của hai chosenCID, cùng M/R/C/B/CID/fulltuple change flags. Không thực hiện hybrid-policy counterfactual hoặc thay score của một nhánh sang nhánh kia.

Summary16groups (pooled/3profile/3seed/9trajectory), tất cả32M/R/C/B/CIDsignatures kể cả0 và bốn Bsame/different×CIDsame/different cells. Trình bày riêng55Rchange-previewkept,17M/Rsame-previewchanged,5jointcases và mọi negative cases; các tập này chỉ là strata mô tả từ cùng population, không select examples theo chiều có lợi. Nếu Bsame/CIDdiff và exact native keys khớp với cùng tie context, nhãn đúng là **source-local CID ranking explanation**; không “score-only causal effect”, không giải thích item difficulty/qid hoặc outcome.

## Nguồn/pins và giới hạn triển khai

Analyzer đọc frozen full–empty bundle manifest906d16…, legacyeeef17…, sidecar6452e8…, oldflags1cdbba…, parity4636f1…; recovered runner402dca…, archived loadera12edc…. C13 historical source provenance8b296d… và notebook353f48… chứng nhận selector/GAM definitions.3simulator input CSVs chỉ nodes/edges/chaptermap, SHA6db464…/ecd910…/aa99cf…; không events corpus/realdata/Holdout. Cross-ready closed32 summarya6860a… là consistency reference, không thêm sample.

Notebook được parse JSON/AST để kiểm definition hashes/constants, không compile/exec. Analyzer và pure fixtures chỉ nằm prep; không sửa/thêm scripts/research trong lúc sourcefreeze154. Fixtures dùng sets và scores dựng tay để kiểm frontier/exposure/escape/balance/chapter/visits/lexical ties, perturbed controller graph rejection, wrongCID và immutable inputs. Không thêm testing framework hoặc NN/solver. Sau sourcefreeze, ROOT mới duyệt allocation; chưa có phép tính mới trong contract này.
