# Engineering Loop hoàn thành KLTN — đề xuất vận hành 07/11/2026

## Phạm vi và căn cứ

Yêu cầu07/11 muốn tăng tốc hoàn thiện mô hình rồi tạo bằng chứng cho ba RQ. Mục tiêu thực nghiệm là kiểm tra các giả thuyết với cả kết quả dương, âm hoặc chưa đủ bằng chứng. Đề xuất bắt đầu diagnosis RQ1/RQ2 song hành model engineering vì source Paper2 đã đủ cho nhiều controls và không phụ thuộc full Junyi AKT CV.

Nguồn hiện trạng là03_SOURCE_AND_ARTIFACT_AUDIT.md, checkpoint.py, latest result directory inventory, evidence/synthetic_tests_retry.log và Gate2 pointer. Đã đọc lại07/11. Kết quả161pass15fail là lần chạy06/11 được lưu, chưa rerun trong lần lập loop07/11. Task14 vẫn chỉ có failed14-02 trong results inventory. Runtime issues cần phân biệt sandbox capability với source defect trước sửa.

Người dùng đã yêu cầu engineering để hoàn thiện models. Các sửa local phù hợp semantics đã frozen có thể gom thành batch tự thực hiện và kiểm tra, tránh hỏi lại từng file. Các lựa chọn phương pháp trong09 còn proposed. Cloud spend, upload dữ liệu, real-data training, full CV, Holdout, scope omission và publication cần phạm vi được duyệt rõ. File kế hoạch không tự cấp quyền execution.

## Chu kỳ cho mỗi task

1. Đọc STATE, task và dependency evidence, kiểm source identities thay đổi từ lần trước.
2. Chọn task critical-path có inputs sẵn. Viết acceptance và regression cần bắt trước khi sửa.
3. Sửa nhỏ trong source/adapter tương ứng, giữ compatibility artifact cũ, lưu provenance.
4. Chạy checks từ hẹp đến integration synthetic theo entrypoint bình thường. Hạn chế lặp lại suite khi source không đổi và output đã đủ.
5. Đọc artifacts và counts, xác minh causal masks, OOV, hashes, reload/export theo contract. Exit0 chưa đủ nghiệm thu.
6. Review scientific information boundaries, historical behavior, filesystem concurrency và failure recovery.
7. Ghi log command/exit/result, source hash, artifact paths, limitation và trạng thái task. Sau đó chọn task có thể tiếp tục.

READY chỉ khi dependency và evidence đủ. IMPLEMENTED khi source có nhưng chưa runtime contract. VERIFIED khi scoped checks đạt. EXPERIMENTALLY_EVALUATED cần accepted real/sim experiment và output contracts. FAILED/BLOCKED phải có failure class và next distinguishing check. Không đánh đồng test suite xanh với benchmark hoặc trả lời RQ.

Dừng retry cùng nguyên nhân sau hai nỗ lực có chẩn đoán. Chỉ retry khi có hypothesis mới, giữ failed run riêng. Chuyển task độc lập nếu chờ tài nguyên hoặc quyết định. Budget/identity/leakage failures chặn launch, không tự thay split/E/model để vượt gate. Mỗi batch tổng hợp evidence và next task để context recovery, không tạo agent tự phê duyệt. Không giả định chat sẽ tự chạy nền sau khi lượt trả lời kết thúc.

## Luồng công việc

| Luồng | Trách nhiệm | Task hiện có | Điều kiện kết thúc |
|---|---|---|---|
|AKT systems |Sang |T07,T11,T08,T14,T15 |Publish/reload/export, mid-epoch resume, bounded CUDA lifecycle và throughput được đo |
|Simulator/graph/science |Dương |T03,T04,T06,T10,T12,T13 |Revision reconciliation,3graph identities, causal data, controls và trace |
|Modern models |Sang, Dương hỗ trợ graph |T09,T17,T18,T19 |AKT/fixed/confidence/gate, SAKT,GKT có provenance và prediction contract |
|Research evidence |Cả hai, Dương statistics |T16,T20,T22 |Paired inference/closed-loop, CI/Holm và limitations |
|Demo/writing |Cả hai, Sang demo |T21,T23,T24,T25 |Verified artifact demo, thesis/article/defense và reproducibility |

Owner chỉ trách nhiệm nhóm. File này không khẳng định có agents hoặc jobs đang chạy song song. AI có thể xử lý các task sẵn lần lượt trong từng phiên, và phối hợp với phần hai sinh viên làm độc lập.

## Đợt thực hiện và gates

B0 ưu tiên T07 và đường dẫn provenance GAM. Chẩn đoán os.link trong filesystem được hỗ trợ, sửa publish giữ no-overwrite và fail-closed, giữ checkpoint compatibility. Cập nhật test lookup notebook bằng nguồn hiện có và expected hash, không chuyển source lịch sử. Acceptance là checkpoint/export integration synthetic đạt, không còn dùng số fail cũ làm current claim sau source thay đổi. BKT runtime repair tách khỏi heavy EM.

B1 T11,T04,T05. Resume lưu optimizer/RNG/sampler/cursor/stopper đầy đủ, continuous20steps so10+resume10 có sample accounting. Song hành graph_env/graph_estimator/graph_controller schema và mastery reference items. Mastery/threshold semantics trình advisor trước scientific run.

B2 T08 và adapters. Pinned CUDA image, resource guard, explicit authorized remote entrypoint và local dry-run. Chuẩn hóa Graph-GAM từ Paper2, SAKT/GKT upstream pinned theo common input/evaluation. SAKT/GKT training allocation do advisor xác nhận. Synthetic causal/coverage/padding/learner-isolation checks.

B3 T09,T10,T12. Minimal A0–A3 augmentation, c/g/off tests, generator simulator learner-disjoint và confidence provenance. Oracle truth nằm phía evaluation, main model lấy past interactions. Không dùng vocabulary Junyi thay Grade10 numeric IDs. Architecture/main confidence cần freeze method decision.

B4 T14,T15. CUDA smoke→short training→interruption/recovery→complete small cohort→throughput→representative scale. Từng stage có accepted artifacts và ngân sách được duyệt. Có thể approve một bounded ladder allocation với rõ stages/caps, sau đó thực hiện trong allocation đó mà không hỏi lại từng optimizer step. Full matrix approval sau measured projection.

B5 T16,T19,T20,T22. Fit/eval đủ comparator theo matrix duyệt, core simulator trước, full Junyi CV theo dependency evidence và budget. Published/final data không dùng tuning. RQ1 chain trace, RQ2 mechanism factorial/noise/order controls, RQ3 paired A0–A3 và fallback stability. Chẩn đoán T13 có thể bắt đầu từ B1/B2, không chờ mọi model fit xong.

B6 demo/writing liên tục rồi final freeze. T21/T23 bắt đầu bằng fixtures/methods và thay bằng verified artifacts khi có. Giữ milestone freeze14/12 và29/12 submission, review weekly từ07/11. Các mốc08 là target theo capacity assumption, chưa measured implementation ETA.

## Định nghĩa hoàn thiện từng mô hình

BKT reuse frozen fitted artifacts và protocol, sửa environment/import nếu cần, không chọn lại config bằng Holdout. GAM giữ train-fold difficulty, source parity và graph-free reference. Graph-GAM có package-compatible reproduction và diagnostic signal/parent/local ablations riêng. AKT đạt causal windows, no scored-target loss, durable recovery và verified GPU lifecycle. SAKT/GKT có pinned upstream, correct mapping, causal export và accepted bounded lifecycle. Fixed-AKT/CG có exact same-backbone off parity, confidence provenance, gate diagnostics, independent A0 fallback và comparative trained artifacts sau approval.

Mỗi model phải có config+source+split/vocab/graph identities, tests, bounded lifecycle, checkpoint/predictions/coverage/metrics. Full-model implementation gate khác scientific evaluation gate và thesis completion gate.

## Những đầu vào cần người dùng cung cấp hoặc xác nhận

| Đầu vào | Chi tiết cần | Thời điểm chặn | Việc vẫn làm độc lập |
|---|---|---|---|
|Modal access |Workspace/account, local CLI đăng nhập, quyền chạy GPU và Volume, payment eligibility do account owner kiểm tra |Paid stage1 |Local engineering/image preparation |
|Ngân sách |Gross usage envelope, net cash ceiling, bounded ladder allocation, maxGPU concurrency và stop rule |Paid launch |Tests/code/schema |
|Upload Junyi |Phạm vi dữ liệu được phép ra cloud, pseudonymization, storage/retention/access restrictions |Real-data upload |Synthetic smoke và simulator-only development |
|Advisor decisions |S01–07 trong09, ưu tiên model×dataset allocation, mastery, confidence, paired factorial và epoch selection |Method-dependent science |Semantics-preserving engineering |
|Paper1 correct revision |Notebook/scripts, inputs, results và seed manifest nếu có ngoài repo |Exact reproduction |P2 diagnosis và source discrepancy report |
|Team capacity |Số ngày/tuần, ai phụ trách, milestones gặp advisor |Độ chắc lịch trình |Task kỹ thuật critical path |
|Recent external work |Artifacts/code đã tạo ngoài repository, checkpoints nếu có và provenance |Tránh làm trùng |Tiếp tục nguồn hiện có |
|Thesis template/rubric |Mẫu trường, định dạng báo cáo, tiêu chí demo, hạn nội bộ |Final writing/delivery |Methods, claim ledger và verified results |
|Final evaluation |Access ledger, phạm vi đọc Test và final selector authorization |Final Test only |Development-only work |

Không cần gửi token/password hoặc thông tin thẻ trong chat. Account owner đăng nhập local và cấu hình secret qua công cụ quản lý credentials, chỉ báo workspace và trạng thái sẵn sàng. Dataset lớn sẵn trong repo không cần gửi lại. Nếu tài liệu ngoài repo có thì cung cấp location hoặc file, không thay yêu cầu truy nguyên bằng nội dung phỏng đoán.

## Modal và tài chính

Official docs được đọc07/11. GPU cần payment method hợp lệ theo https://modal.com/docs/guide. Workspace owner/manager thiết lập usage budget và net spend cap theo https://modal.com/docs/guide/budgets. Secrets có dashboard/CLI và inject qua environment theo https://modal.com/docs/guide/secrets. Chưa kiểm account, balance hoặc quota cụ thể của người dùng.

Đề xuất allocation preflight ladder tối đa10USD gross,1GPU đồng thời, retries tự động0. Đây là đề xuất chờ xác nhận, full training cần measured cost model riêng. Không coi30USD starter credit là tiền chắc chắn có trong account. Envelope150/300/600USD trước đây vẫn tentative. Hạn mức cloud có thể ảnh hưởng jobs khác trong cùng workspace, cần account owner tách usage attribution và chọn cap phù hợp.

## Batch mở đầu

B0 được ưu tiên vì failed artifact publish có thể làm mọi model run mất kết quả. Sau đó B1/B2 tiếp tục phần có dependency sẵn. Chỉ đánh dấu task bắt đầu/kết thúc khi có sửa mã và output tương ứng. Lần07/11 hiện lập loop và đối chiếu trạng thái, chưa claim model implementation mới hoặc test rerun.
