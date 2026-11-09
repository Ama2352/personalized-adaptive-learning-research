# Review tĩnh response-mixture RQ1

## Verdict

Scoped static PASS cho estimand và phép ghép cache. Chưa thấy deterministic scientific bug hoặc lỗi tăng population trong ba nguồn được review. Đây chưa là actual pure/native diagnostic acceptance. Không import Python, chạy tests/Git/model, đọc gzip cache hoặc oracle trong lượt review.

| Source | SHA-256 |
|---|---|
| analyze_rq1_reference_mixture01.py |52ee0f409ad6752a3413e18565e31b95908dec57574739a8f76fe5aa01121b43|
| test_rq1_reference_mixture01.py hiện hành |a6b6bc737f79489824fa4622c0b6a11ee18ebf398bca375a502d444912ec23b7|
| rq1_reference_mixture_contract01.json hiện hành |5ba4d9da4fd98aeac4dd9ead2250b7f8252cb83c076e52cc6fa4242eb94b510a|

Analyzer52ee giữ nguyên trước/sau review. Test ban đầu59c1 và contract40e5 đã được ROOT cho phép sửa trong lúc review. ROOT báo actual pure01 đạt7PASS/1FAIL ở known-answer mean3 do1ULP giữa constant folding và Python3.13sum. Tác giả đã lưu oldtest/contract trong `pre-reference-mixture-test-rounding-fix01`, đổi đúng assertion expected arithmetic sang tolerance1e-15 và cập nhật contract test pin theo phê duyệt riêng. Reviewer đọc lại narrow test hunk và current contract. Exact-wire equality trong analyzer không đổi, đây không phải nới admission tolerance hoặc thay estimand. Native cached execution chưa diễn ra tại handoff này. Không gọi revision đã giải thích là unknown race hoặc relabel lượt pure đầu thành PASS.

## Estimand và ngữ nghĩa nguồn

Historical runner402d dòng62–73 lấy qid bằng uniform integer trên fixed item list, không dùng estimator/latent state hoặc preview selector để chọn query. Loader a12e dùng đủ questions_by_concept từ bank cố định. Bank parser84–98 của analyzer yêu cầu84unique items/28concepts và đúng ba difficulties1050/1200/1350 cho từng concept. Vì thế mean3 là forecast cho response-mixture theo thiết kế logger conditional concept, không phải ba forecast được gán ba labels. Đây là lập luận nguồn về sampling design, không chứng minh PRNG samples hữu hạn độc lập hoặc thật sự cân bằng.

Native capturefc067 dòng72–104 không nhận y, tái dùng currentP và predict hai reference còn lại trên clone cùng pre-update fingerprint, rồi kiểm clone/original state không đổi. Current label chỉ được dùng tại advance sau admission ở dòng389–397. Target evaluator là một response quan sát từ mixture của ba items, không phải counterfactual outcome của từng item, latent mastery hoặc đánh giá đúng/sai của tau.

## Joins và denominator

Analyzer110–142 kiểm legacy row digest, exact query/currentP/fullpreview, C13 pairing phases, ba referenceqid/difficulty của đúng concept, current-referenceP và exact mean/criterion. Bool labels/probabilities và nonfinite probabilities bị từ chối.

Các đoạn316–354 kiểm old3240keys không mất/duplicate, native18complete gzip streams với120records/stream, EOF/CRC, trajectory receipts và stream SHA/size. Full2160arm keys được yêu cầu, rồi đủ1080query+y pairs giữa hai variants. Một response được dùng một lần cho mỗi mean3forecast/arm. Cùng1080labels được dùng lại để so hai arms, chưa tạo2160independent observations hoặc6480reference labels.

Group specs145–195 giữ16groups×2arms=32views,480bins và64tau strata. Pooled1080/arm, profile360, seed360 và trajectory120. Fixed bin rule15bins khớp baseline, p=1 nằm bin cuối, empties giữ null. ECE dùng weighted absolute signed gaps. Threshold là fixed raw-reference criterion, không là calibrated classifier hoặc masterytruth confusion matrix. Không thêm seed/model/world/teacher calls.

## Điều kiện outer và durability cần giữ rõ

Worker199–394 có7s tính từ main, bao gồm owned gate và final checks sau resultwrite. Toàn process còn có module import/startup ngoài clock main, nên ROOT whole10 phải đo từ trước launch và giữ cleanup/finalization reserve. Feasibility chưa đo, không tự retry hoặc tăng cap.18gzip streams, hai old caches và postread SHA passes đều tiêu tốn thời gian thật.

Writer379–394 tạo output directory exclusive sau khi hoàn tất tính toán/admission và source postchecks. Từng file đóng trước bước kế tiếp, nhưng chưa có explicit fsync hoặc file-readback. Output SHA được tính từ in-memory payload. Vì vậy ROOT outer phải kiểm actual four-file population, actual file hashes/sizes, final source/contract SHA, clean process exit, elapsed whole budget và owned cleanup/Job0. Worker result status riêng lẻ chưa là durable whole-operation acceptance, nhất là khi final check ném lỗi sau khi result.json đã tồn tại. Nếu muốn tuyên bố fsync durability thì cần bổ sung writer sau khi ROOT release source, không suy từ hash in-memory.

Audit chặn scientific imports, subprocess/network và oracle/corpus/Holdout opens. Đây là guard hợp tác của source path được review, không blanket filesystem sandbox. Late exception phải giữ raw stderr/partial outputs và bị outer từ chối. Không nâng worker receipt thành scientific result khi thiếu outer proof.

## Test scope

Source có8manufactured unittest methods cho bins/endpoints/tau/empties, weighting/cancellation, invalid values, exact mean3+oneY projection, duplicate/tamper/wire controls, bank shape và full32group population. Chúng không chứng minh actual CRC/source cache joins hoặc runtime feasibility. ROOT phải kiểm actual outputs riêng. Native mastery lane đã dừng không được lấy partial truth outputs hoặc gán outcome mới cho các reference không được phục vụ.
