# Sổ quyết định và vấn đề mở

## Quyết định nhóm08/11 — S04-A/S05-Plan B development đã adopt

Chỉ thị user hiện hành, root chuyển tiếp: **“Phương pháp nào an toàn và tiết kiệm tiền thì chọn, ko chờ chốt”.** Theo quyền này, nhóm/root chọn [ProtocolV1](21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md) và [source/authority map](21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.sources.json). Không tiếp tục chờ advisor cho routine method engineering; không gán lựa chọn nhóm thành phê duyệt GVHD hoặc bỏ required deliverables. Các đoạn S04/S05 “cần chốt/chưa adopt” và “mọi đề xuất chưa được phê duyệt” bên dưới là snapshot trước mốc mới này.

| ID | Quyết định hiện hành | Scope/giới hạn |
|---|---|---|
| D30 | User giao nhóm chọn phương pháp an toàn, tiết kiệm; root chọn S04-A/S05-PlanB | Group method adoption, không data/cloud/fullCV/Holdout/paid execution authority mới |
| D31 | S04-A:3equal reference items; tau_ref0,5637150147511514; one-temperature response calibration; common controller targetsuccess0,70 | Fit80/selection10/calibration10; raw selector/independentA0 trước refit90%; calibration10 sau refit; không P(K), oracle features hoặc reselect trên learners đã train |
| D32 | S05-B staged:1trainingseed, frozenJunyi fold4, đủ BKT/GAM/Graph-GAM/AKT/SAKT/GKT và A0–A3/expert/learned ở hai environments |9simulator neural fits/18Junyi neural phases; historical baselines giữ scope; không5fold/trainingseedvariance/RQcompletion |
| D33 | H_dev30 cho resourcebounded development; finalH500 chỉ historicalalignment proposal theo Paper2fullsource | Không claim history>50/longhorizon; final horizon cần measuredbudget/prefreeze. Q_dev3.402.000logicalresponses, finalH500illustration56.700.000; không independentN/kernelcalls/runtimeforecast |

Next critical path là research-mode corpus/split/calibration/controller/selected-trainer wiring; không thêm toy-only milestones để thay evidence. Numerical first-corpus/neural/epoch/resource configs còn phải chọn và pin trước execution, không sửa frozenAKT hyperparameters qua protocol. Root điều phối theo user authority đã có; không trì hoãn routine choices vì chưa có advisor sign-off. Final proposal-completion vẫn phải audit đủ models/environments/learnedgraph/noise/history/replicates/horizon/demo/article và giới hạn scientificclaims; không tự waive. Budget30USDfree/net0, Colab trướcModal, no automatic paidfallback giữ nguyên.


## Mốc hiện hành08/11 — phân biệt nghiệm thu kỹ thuật và quyết định nghiên cứu

- **D25, supported/engineering:** A0–A3 prototype đã có confidence theo cạnh và gate explicit (`4a256a4`). GRAPH04 vừa kiểm actual train–selection–checkpoint/reload/export trên toy: một graph complete epoch/8train targets, selection4=3scored+1OOV, reload delta0; một partial epoch giữ ledger và không publish checkpoint. Tổng bốn updates gồm hai baseline kiểm tương thích. Actual suite45PASS/1FAIL giữ nguyên; test inventory kỳ vọng thiếu hai helper đã sửa và kiểm riêng bằng stored artifact/0fit. Gói GRAPH04 đã đóng và commit `f8e9ab0`,89outputs raw Git verified; không gọi fitted CG-AKT nghiên cứu hoặc full Gate PASS.
- **D26, supported:** disable graph tái hiện backbone của cùng model, chưa chuyển sang một checkpoint A0 độc lập. Confidence0,25/0,75 của fixture là khai báo structural, chưa là reliability đã estimate/calibrate. Gate trainable đã được cập nhật không đồng nghĩa gate hữu ích hoặc ổn định. S04/S05 vẫn cần chốt reference/mastery/calibration, estimator provenance, allocation và protocol trước research fit.
- **D27, supported:** demo closed-loop đã commit source `22b3522`, bundle `b9eaaab`,83tests và UI QA; xem [báo cáo](../../research_tracking/reports/demo_closed_loop_readiness_20261108.md). Đây là trình xem bằng chứng đã lưu, một phần E11; không live fitted AKT/CG-AKT hoặc kết luận causal. Không cần chờ full training để viết phần kiểm toán và trình diễn cơ chế đã quan sát.
- **D28, supported:** preparation GPU-host đã commit `c1d93ec`,102outputs raw Git verified; bốn scopes mock không thay actual fresh-host/CUDA/Volume proof. Gate24 là snapshot trước source mới, không current worktree. Controller Colab30957 đã kết thúc; không coi runtime hoặc job còn live khi chưa có handle mới xác nhận. Không rerun job cũ để lấy lại bằng chứng đã tải.
- **D29, binding:** ngân sách hiện hành vẫn30USD free credits/0USD trả thêm, Colab trước Modal; credential đăng nhập do user thiết lập không cấp quyền chạy paid job. Không xin lại token/password hoặc coi bảng giá giả định là throughput đã đo. Mốc auth/notebook/private-config cũ phía dưới là lịch sử, không trạng thái account hiện tại đã kiểm lại.

Điểm chốt trước nghiên cứu tiếp theo: S04 cần tách rõ native B-score, reference concept probe và served-item P (P được tính sau selection trong source closed-loop này); S05 cần chốt model×environment×graph conditions và independent evaluation. Không bỏ SAKT/GKT hoặc Junyi comparison để vừa ngân sách mà không duyệt phạm vi. [Bản thảo14claims](../../research_tracking/reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md) cung cấp evidence để trao đổi, không tự phê duyệt protocol.

Mọi đề xuất phương pháp dưới đây chưa được phê duyệt chỉ bởi việc xuất hiện trong tài liệu. User đã cho phép inspection/planning/synthetic checks. Không có approval cloud, real-data pilot, full CV hoặc Test.

| ID | Evidence và quyết định | Trạng thái/confidence | Tradeoff/owner |
|---|---|---|---|
|D01 |Đề cương tìm thấy tại paper2, dùng wording trang2–5 thay tracking cũ thiếu proposal |Supported/high, trạng thái approved theo user |Cả hai, chữ ký bản scan chưa xác thực |
|D02 |Paper1 notebook khác PDF, không dùng source này tái lập kết quả paper50seeds |Supported/high |Dương tìm đúng revision, không dựng lại rồi gọi reproduction |
|D03 |Graph-GAM có trong P2, benchmark KLTN hiện graph-free |Supported/high |Reuse source, thêm parity adapter |
|D04 |Paper2 graph-package có local adaptation, root-control cần thiết |Supported/high |Factorial isolation tăng số conditions CPU nhỏ |
|D05 |G14=e^(-.84)Gfinal khi no practice/homogeneous decay |Supported/high theo algebra/source |Giữ metric bắt buộc, thêm sensitivity independent dynamics |
|D06 |Junyi checkpoint không map Grade10 vocabulary |Supported/high |Train riêng, tăng fit count nhưng bảo đảm semantics |
|D07 |Gate2 05/11 là164 pass, hashes hiện khớp |Supported/high historical snapshot |Không tự nâng GPU readiness |
|D08 |Current synthetic retry161pass15fail, link publish và notebook path blocker |Supported/high current log |Sang xử filesystem contract, Dương provenance, chưa biết OS sandbox vs general platform |
|D09 |Minimal residual confidence/gate, A0 fallback checkpoint riêng |Proposed/medium |Advisor/Sang duyệt architecture và threshold semantics |
|D10 |Paired mechanism factorial thay DiD High-vs-Low |Proposed/high validity rationale |Advisor xác nhận estimand simulator-conditional |
|D11 |Giữ outer5fold và inner10% learner epoch selection, không innerKfold |Proposed/medium feasibility |Advisor duyệt cost, current code đã có outer refit |
|D12 |Không full Cartesian models×noise×history×profile |Proposed/high need, allocation unresolved |Advisor duyệt exact model/dataset coverage, không bỏ required baseline |
|D13 |PlanB conditional measured cost và capacity |Proposed/medium |Nhóm duyệt available person-days và dollar ceiling |
|D14 |Modern models primary, BKT là reference |Supported/high proposal trang4 |Không dành critical path rerun EM |
|D15 |Graph learning train-only, reliability không tự là causal confidence |Proposed/high methodology |Dương chốt estimator và calibration graph split |
|D16 |Final simulator audit seeds mới sau freeze, published seeds reference |Proposed/high |Dương quản seeds, advisor approve independent final interpretation |

## Các quyết định cần advisor

S01 chốt source Paper1 nào đại diện submitted paper, phương án xử lý exact reproduction nếu không còn source. S02 chấp thuận diagnostic-v1 và primary net gain với retained14 giải thích redundancy. S03 estimand factorial ψ và causal interpretation conditional simulator. S04 mastery reference bank/calibration/threshold dùng true state trên simulator Dev, proxy confidence và oracle boundaries. S05 phạm vi train/eval SAKT/GKT và graph-learned trên hai environments, core seeds, Junyi full CV allocation. S06 final evaluation sau BKT Holdout đã xem, access ledger và freeze selection. S07 PlanA contingency nếu budget/deadline vượt. Không bỏ model, RQ, demo, article draft hoặc learned graph âm thầm.

Budget owner xác nhận B00 mức USD tổng, stage ladder allocation, platform/payment/quota, workspace usage cap và net spend cap. Số150/300/600 trong roadmap là đề xuất envelope, chưa approval hoặc measured estimate.

## Câu hỏi mở cần evidence

Q01 đúng Paper1 code+outputs+seed manifest ở đâu, deadline12/11, Dương. Q02 hard-link failure chỉ sandbox Windows hay portable pipeline, T07 Stage2 filesystem tests, Sang. Q03 query mastery AKT có hỗ trợ reference difficulty ngoài84 item hay phải dùng fixed bank, T05, cả hai. Q04 coverage simulator-generated logs có đủ cho AKT và GKT, T10 learning curve. Q05 estimated edge confidence có generalize sang graph realization mới, T12. Q06 throughput/cost/risk GPU thực, T15. Q07 exact allocation model×dataset được advisor đồng ý chưa, T02. Q08 capacity hai sinh viên thực tế, tuần đầu. Q09 graph map36 rows có duplicates ảnh hưởng28 concept hay chỉ extra metadata, T04. Q10 holdout access history ngoài artifacts được cung cấp, chưa độc lập xác minh toàn bộ human viewing.

## Alternatives bị loại hoặc hoãn

Rebuild simulator toàn bộ bị loại vì mất lịch sử và effort. Merge P1/P2 dynamics bị loại vì semantics khác. Junyi checkpoint numeric-index mapping sang simulator bị loại vì không semantic crosswalk. High/Low observational DiD bị loại vì counterfactual assumption không bảo đảm. Inner5fold nested mỗi outer bị hoãn vì không requirement và compute lớn. Full hyperparameter sweep, learned neural confidence, third dataset, production LMS bị hoãn vì proposal không đòi và làm trễ evidence. Bỏ SAKT/GKT chỉ vì tiện là REMOVE-WITH-APPROVAL, chưa được quyết định.

Kiểm chứng cuối Q09 đã giải quyết. `evidence/planning_validation.json` xác nhận map36ID duy nhất, đủ28nodes,8extraIDs, không missing/duplicate. Advanced31edges=28intra+3cross, baseline25intra, không missing endpoints/isolated nodes trong inputs P2. Không suy provenance Paper1 từ việc graph counts giống PDF.

## Interface engineering07/11

D17 supported: model-domain/item-bank/vocab/recipe identity và predict-before-update/session/probe contracts đã kiểm CPU, xem18 và report simulator_kt_interface_20261107.md. Không lấy implementation acceptance làm phê duyệt mastery protocol. D08 filesystem và Q02 có engineering remediation/Gate2 mới; historical failure records giữ nguyên.

D18 proposed: chốt graph-context history scope trong S04/S05. A0 chỉ nhìn effective window dù session giữ full replay history. Default đề xuất primary cùng effective window; full-cache cần graph-free information-matched control, không chỉ real-vs-noisy edges. Không silently adopt phần này.

Q03 được thu hẹp: AKT item84 query bridge đã kiểm, không có numeric difficulty1250 ngoài trained items. Calibrator/reference weights/threshold/controller vẫn chưaaccepted. Q04 diversity/split/coverage của generated training trajectories chưa giải quyết bằng arithmetic engineering labels. Q06 chưa đo GPU hoặc d256 closed-loop inference; include reference-query workload trong budget.

## Data/graph-boundary engineering07/11

D19 supported: split/schema4roles và graph-context effective-window audit có70targeted tests, không là trained CG-AKT; xem19 và report simulator_data_graph_boundaries_20261107.md. Full-history context có thể dùng thông tin baseline không có; D18 vẫn proposed về primary comparison.

D20 supported/source: Paper2 persona_base_abilities có parent-smoothed latent ability; replay item difficulty được chọn từ theta thật (notebook cell9/17). Collector mới phải tách oracle sidecar và ghi logging-policy provenance, không tự tái dùng replay generator làm corpus deployment-like. Paired mechanism comparisons cần giữ base realization khi thay learning-edge mechanism; exact protocol vẫn S03/S05. Clock unit và response/learning RNG channels là prerequisite bổ sung ở19.

## Modal budget theo user07/11

D21 binding: user báo cóModal với30USD/tháng, yêu cầu chuẩn bị kỹ và hướng dẫn quyền truy cập. Tạm trần tổngusage30USD, chưa xác minhcredit/out-of-pocket/workspace/remaining/reset. Các150/300/600USD cũ chỉproposal, không làauthorization. Không fullCV hoặc cloudrun tự động. Phân bổ2readiness+3benchmark+20training+5reserve là đề xuất, không per-run approval. Sourcebound401CPU vàlocalSDK không chứng minhbudget/actualCUDAready.

D22 supported: ModalSDK1.6.3 cài27newpackages trongprojectvenv,30existingversions vàAKTlock unchanged;localCLI/pipcheckPASS, noauth/jobs. SupplementalWindowsclientlock không thayLinuxCUDAimagelock. UserđăngnhậpbrowserquaCLI vớiignoredprivateconfig, khônggửitoken/passwordtrongchat. Handoff `docs/akt-modal-setup.md`; officialbudgets/config/token sources ởtài liệunày.

D23 — Ràng buộc từ câu trả lời user ngày07/11: workspace `honguyenminhsang2005`, còn30USD free credits, kỳ bắt đầu07/11/2026 và reset “tháng kế”; không trả thêm tiền. Thay giả định chưa rõ loại ngân sách ở D21 bằng FREE_CREDITS_ONLY: trần tổng sử dụng30USD, trần tiền trả thêm0USD. Balance/start do user cung cấp, chưa đối chiếu tài khoản; ngày/giờ reset chính xác chưa biết. Không hỏi lại workspace/loại credits đã trả lời; không tự đăng nhập hoặc chạy job từ việc biết hạn mức tháng. Private config hiện chưa có; chủ tài khoản cần áp dụng và xác minh usage limit30/spend limit0 trước compute.

D24 — Chỉ thị user07/11: ưu tiên GPUColab cho kiểm thử trước khi dùng Modal credits. Thứ tự localCPU→Colabfree→Modal; không tự fallback paid khi Colab thiếuquota. Colab smoke/checkpointreload pass chỉ giúp giảm debug, không thay revalidation của image/Volume Modal hoặc chứng minh mid-epochCUDAresume. Quỹ readiness2USD chuyển thành reserve cho kiểm đặc thù Modal sau Colab nếu cần, không autochi. Notebook hiện chưa actualremoteexecution;8mockguardcases/1bundlepytest chỉ local engineering evidence.
