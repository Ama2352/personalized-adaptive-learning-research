# Guard A0 simulator-research: cấu hình và quyền chạy trước model

Đã thêm guard CPU-first cho scopeA0 simulator-research theo [protocol21](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md): newphase trong [config](../../src/knowledge_tracing/akt/config.py), [research_execution.py](../../src/knowledge_tracing/akt/research_execution.py) và [tests](../../tests/akt/test_research_execution.py). **Final85kiểm tra thuần metadata đạt,0Torch/model/optimizer calls**. Parent đã review finalsource và không còn identifiedblocker trướcarchive. Chưa actualruntime/Gate, generatedcorpus, researchtrainer hoặc fittedcheckpoint; unitmocks không cấp quyền chạy thực tế.

## Scope được triển khai

Phase`simulator-research` chỉ CPUA0: frozen seed42/batch4/maxepochs20/patience3/min_delta0,0001 cùng nativeNonRasch geometry/Adam recipe. Không graph/CUDA/recovery/resume, không mượn phasepreflight/fold hoặc nới d32engineering. Native outer_fold0 chỉ là legacyunusedfield; identity ghi simulator/noJunyiFold, không fakefoldrecords.

Dataclassfields/defaults không đổi. GoldenAST và serializeddefaultasdict trước/sau byte-identical, SHA `f46eb29594ff7a468e2cd7f8d149cc909a8453372701cd68ce216648f1d4f8c5`. Oldphasechecks giữ nguyên;6purelegacyconfig cases cũng đã đạt ở trial03. Không sửa model/upstream math, legacy authorization/context/runner/CLI, dữ liệu hoặc artifacts lịch sử.

`ResearchResourceBudget` bắt16fields riêng, gồm exact rolelearner/targetcounts, maxevents/learner, cumulativeoptimizersteps/optimizedtargets, train/wall/RSS/freeRAM và input/checkpoint/exportbytes. Không None/bool/NaN/Inf/defaultbudget; native9caps phải khớp budgetprojection có refitunion90. FlooravailableRAM≥1GiB. Root dự kiến60development=48/6/6,210events/learner là allocation tương lai, **không moduledefault hoặc actualexecution trong batch này**.

`ResearchRuntimeEvidence` ghim3paths(runtime/selectedlock/Gatepointer)+5expectedSHA. Guard reuse nativepreflight/Gatevalidators bằng explicitpaths; không gọi defaultBKTidentity hoặc existingdevelopment-inner-only authorization. Newresearch đòi schema2CPUreport/cuda_availableFalse, actualsameROOT/.venv/path/origin/source/lock/Gatechecks và currentbuildhashes khi gọi thực. Paths reject traversal/symlink/junction; inheritedGit/GH redirection bị chặn. Đây không full44packagebytes/hostnetworkattestation; actuallauncher/environment acceptance còn riêng.

`prepare_research_identity` không mkdir/modelimport. `require_research_authorization` đòi externalartifactSHA+closedschema+scope/run/config/spec/fullidentity/exacttypedcaps/requestedphases+approvalreference và freshoutput. Không suy authority từ approvedboolean, GatePASS hay decisionstring đơn lẻ. Typedreceipt có revalidate để kiểm lại artifact/source/input/runtime; là consistency binding hợp tác, không capability chống giả hoặc nonresettableglobalquota. Low-levelAKTAdapter hiện vẫn không tự kiểmauthorization; BATCH3 phải consume/revalidate guard trước lazyTorch/modelimport và allocation.

Purpose ghi **a0_single_candidate_lifecycle_pilot**, chỉallocationA0; mainmatrixsystemselector **chưa chạy**. Mainmatrix phải thu toàncandidate rawselectionpredictions rồi freeze systemselector trước **bất kỳ** refit90/calibration nào, không nhìn kết quảrefit/calibration rồi chọncandidate. Không gọi A0singlecandidate là independent-A0 graphwinner.

## Corpus contract có thể restart

Sharedfixedpath `artifacts/simulator/corpora/<id>/` có9modelinputs: corpus.json,bank.json,plan.json,3observableJSONL và3rolemanifests. Guard chỉ streamhash JSONLbytes, không parse nhãn/đọc oracle/ hoặc finaleventfiles. Actual ObservableTrajectory/schema/target/source-row/support re-audit bắt buộc trướcmodel ở BATCH3. FixtureJSONL cố ý không hợp lệ để kiểm rõ ranh giới này, không được gọi là validgeneratedcorpus.

[Schema cuối](../runs/akt-research-execution-engineering-20261108-01/CORPUS_SCHEMA_V1.json) SHA `ba4a3d8ca412395b4b3841da010c736f1ceac3d5bd1a67e5de87ef7c7287e578` được root và publisherowner thống nhất trước realpublication. Corpus14keys ghim actualdocs21rawSHA/protocolID, sourceinventory/G_env/sharednormalizedrecipe/clock/bank/plan và rolecounts/targets/profileSHA. Roleprofiles có thể khác; không ép originalcollectorcomposite recipeSHA bằng nhau.

**Parent review đã phát hiện gap thật ở schema ban đầu:** opaqueplanmanifest thiếu namespace/root_seed; rolesummary thiếu typedprovenance nên không thể dựng lại dữ liệu saurestart mà không đoán. Đã giữ oldschema/source61PASS và sửa prospectiveV1 trước publication: planexact3keys `{schema_version,recipe,manifest}`, recipe5constructorfields; guard dựng actualResearchSplitPlan và so toàn declaredmanifest. Rolemanifest16keys thêm actualasdictResearchProvenance+identity; guard dựng typedobject, kiểm role/plan/split/domain/G_env/UTC/policy/sourcebindings. Explicit environmentsemanticsSHA phải giốngcrossroles. Không dùng oracle hoặc `object.__new__` để lách reconstruction.

Compositecollectionrecipe kiểm bằng documentedsource-pinned scalarformula từ raw4recipefields+collectorversion/clock+roleprofileSHA. Guard không import collector/NumPy/pandas. Rawcollectorreceipts giữ nguyên; normalizedsharedrecipe là descriptor mới rõ nguồn, không viết lại lịch sử.

Publisher ghi/fsync/readback9inputs và oracle tách riêng trước DONE-last. DONEexact4keys, gắn corpusSHA và9rawinputSHA; guard đòi DONE và **không failure.json**, ghim DONEbytes vào identity. DONE là logicalcompletion, không filesystemtransaction/crashguarantee; actualsuccessfulpublisher receipt và outerpostelapsed acceptance vẫn cần, đặc biệt khi failuremarker không thể persist. Parent/platformpublisher kiểm riêng31cases trên historicalguard72; không relabel thành finalguard5ea3 và không nhân đôi bundlepublisher tại đây.

## Actual kiểm chứng, giữ mọi phiên bản

| Lượt | Kết quả thực tế | Controllerelapsed | Nguồn/scope |
|---|---:|---:|---|
| pure01 |60PASS/1FAIL/0error/skip |6,860790899954736s |Guard8a/oldschemaf61; fixture dùng chung dict với fakeGate, production vẫn reject ở check sau |
| pure02 |61PASS/0failure/error/skip |6,20958269998664s |Chỉ táchdictfixture; không đổi productionguard |
| defaults01 |AST+defaultasdict giống hệt |helper0,08363039995310828s; toolwall0,5529794s |Directpureproof, không giảJUnit/fullsuite |
| pure03 |87PASS/0failure/error/skip |10,262182235717773s |Full81revisedguard+6legacyconfig, guard72/schema ba4 |
| pure04 |85PASS/0failure/error/skip |8,471940279006958s |Full85finalguard, chỉ thêmjunctioncheck/canaries;6legacykhông đổi không rerun |

Root nâng totalcap30→60s **trước trial03**, giữspent13,623352999941377s, để kiểm full revisedparser/restartscope thay vì chỉ chọnpassingcases. Finalcumulative **32,357475514666106/60s**, không reset. Console04 8,04s/JUnit7,870s; không gọi trainingthroughput hoặc cộngtrials thành independentN. Raw01failure/old61PASS/old87PASS đều giữ nguyên với exactsnapshots. Không có actualjunctioncreation;3portableancestorcanaries corpus/auth/evidence có fileopen-tripwire chứng minh rejecttrướcread.

Trên toàn các lượt:0Torch/model/optimizer/innerprocess; nativepreflight/Gate là explicitunitmocks, fixture .venv chỉemptydirectory dướipytesttmp, không tạo interpreter/environment. SourceSHA trước=sau từngtrial, rawlogs/XML/receipts/controllers/budgetrevision và before/afteraliases đều trong [bundle](../runs/akt-research-execution-engineering-20261108-01/README.md), [copyinventory](../runs/akt-research-execution-engineering-20261108-01/copy_inventory.json). Không giữ pytesttmp/syntheticJSONL như thể actualcorpus.

FinalconfigSHA `beb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f`; finalguard `5ea3d7283f6d8da6eab712d4e4fedb48cd41717f99cd3ae51fb7b8651b16c7b6`; finaltest `9289f3aa4c8948f3e62344d11f01ea596764f78a42f1e2291aafc92178f72ba4`. [Receipt04](../runs/akt-research-execution-engineering-20261108-01/trial04__receipt.json) và [JUnit04](../runs/akt-research-execution-engineering-20261108-01/trial04__junit.xml) là bằng chứng finalpurestage.

## Việc còn thiếu

Parent finalsource review đã kiểm reconstruction/compositerecipe/source/G_env/DONE/scope/authorization/nooracle và junctionfix, nhưng chưa thay freshsourcekit/Gate, actualsame-runtime acceptance, corpuspublication và authorization từ exactcounts/caps thực tế; rồi BATCH3 selectedfit→freshrefit90→frozencalibration10/export/checkpoint/domainattestation. Guard không chứng minh generator/predictor thực tế đúng chỉ từ metadata, không cấp paid/GPU/Holdout/fullCV/quyền thực thi rộng hơn. Không có fittedresearchmodel/calibrationefficacy/RQcompletion claim trong batch này; không sửa roottracking/Git.
