# BATCH2 — guard CPU A0 simulator-research, chưa execution

**Trạng thái cuối sau junction-review:** trial04 fullnewguard **85PASS**, không chạy lại6legacyconfig không đổi. Guard5ea3d728…/test9289f3aa…/configbeb2/schema ba4; cumulative32,357475514666106/60s. Old87/61 results giữ nguyên với exactsourceversions dưới và `.pre-junction` snapshots. Không tạo junction thật, chỉ portableAPI canaries.

**Cập nhật sau parent restart-review:** trạng thái cuối là trial03 **87PASS/0failure/error/skip**, sourceguard72f5a1e9/test6379da39, schema ba4a3d8c; cumulative23,885535235659148/60s. Các đoạn61PASS/30s dưới là lịch sử trước amendment, đã giữ nguyên snapshot `READINESS.pre-repro.md` SHA4b92fc8e4319e400c8c8df4b2b7fb91178d26d3ba1ce585bcbe59b490f1df6ae cùng oldmodule/test/schema. Chưa archive/actualexecution và không relabel oldtrials.

Đã triển khai đúng scope root duyệt: narrow newphase trong `akt/config.py`, NEW `akt/research_execution.py`, NEW focused `tests/akt/test_research_execution.py`. Không đổi dataclass fields/defaults, native model/upstream/math, legacy authorization/context/runner/CLI hoặc engineeringcaps. BATCH3 trainer/model allocation chưa có.

## Actual validation và source freeze

| Bằng chứng | Kết quả | Thời gian |
|---|---|---:|
| pure01 |60PASS/1FAIL/0error/skip |controller6,860790899954736s |
| pure02 |61PASS/0failure/error/skip |controller6,20958269998664s |
| defaults01 |AST class và serialized defaultasdict byte-identical |helper0,08363039995310828s; observed toolwall0,5529794s |

Conservative cumulative dùng max helper/toolwall: **13,623352999941377/30s**. Receipt02 giữ native cumulative13,070373599941377s; direct defaultsreceipt ghi own helper cumulative13,154003999894485s, không sửa lịch sử. Không cộng60+61 thành121independenttests. Raw01 vẫn1FAIL: fixture dùng chung dict giữa corpus sourceinventory và mockedGatebuild, nên sửa input cũng sửa expectedmock; production guard vẫn reject ở crossrolecheck. Chỉ tách `dict(build)` trong fixture, không sửa production source/config hay nới guard; targeted02 giữ61cases.

Source cuối `config.py` SHA `beb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f`; `research_execution.py` `8a6221b3a7101911ad4a38e937007ef52c57921cba25467ea565f3eadff7cad9`; finaltest `77d23eb5d95854c61d159eb774c31f11a336ad5dad985619ab4e0e89998c8439`. Cả hai trial11inputs trước=sau,22snapshots/trial. Oldconfig6f972… giữ `config.py.before`; legacyserializeddefaultsSHA `f46eb29594ff7a468e2cd7f8d149cc909a8453372701cd68ce216648f1d4f8c5`. Exact sharedpublisher schema `CORPUS_SCHEMA_V1.json` f61e2d…; pre-DONE proposal6a22… giữ riêng.

Tests chỉ metadata/tmpfilesystem; **runtime/preflight/Gate là mocks rõ ràng, không actualready**. Popen/Git/legacyBKTdefaultidentity/Torch/model import canaries;0innerprocess/model/optimizer/Torch. Fixture `.venv` là empty directory dưới pytesttmp để kiểm paths, không tạo interpreter/environment. JSONL fixture cố ý chỉ bytes không hợp lệ làm ObservableTrajectory: kiểm guard không parse labels; actual schema audit bắt buộc ở BATCH3 trước model. Không generatedcorpus/realdata/Holdout/remote/install/Git mutation.

## API và guards chính

`ResearchResourceBudget` bắt16fields rõ ràng, numeric/type/finite checks, exact80/10/10 và flooravailableRAM≥1GiB; không moduledefaults60dev/210events. `SimulatorResearchSpec` chỉ phaseCPU`simulator-research`, exactfrozen A0policy seed42/batch4/maxepochs20/patience3/min_delta0,0001 và existing model/Adam fields. Cumulative native9caps phải khớp projected wrapperbudget, gồm refitunion learner/target bounds. Native outer_fold0 là legacyunused field, manifest `junyi_fold_used=False`; không fakefoldrecords. NoCUDA/graph/recovery/resume trong scope này.

`ResearchRuntimeEvidence` ghim root-relative selectedlock/runtime/Gatepointer và rawSHA; reuse actualnative preflight+Gatevalidator với explicitpaths khi actualcall. Không gọi default BKTidentity/legacyrequire_authorization. Newresearch yêu cầu schema2CPUreport/cuda_availableFalse, cùngphysicalROOT/.venv; inheritedGit/GH redirection/credentials bị reject, chỉ cho explicitreadonly safeguards. Đây không full44packagebytes audit; actuallauncher/runtime acceptance vẫn riêng. Không sửa globalGitconfig.

`prepare_research_identity` check actualdocs21bytes+adoptionmarkers/protocolID, source-bound currentGate/runtime/lock, exact corpus/bank/plan/roles/recipe/clock/G_env/source consistency, DONE và inputbytecaps. StrictJSON cấm duplicatekeys/NaN/Inf. Observable JSONL chỉ streamSHA; oracle/không list/open/hash, không nhận finaleventfile input. Guard nhận bank84/28 và planmetadatafamilydisjoint; chưa chứng minh đủ support/diversity từ actualobservations. Fixedsharedpath `artifacts/simulator/corpora/<id>/`; publisher schema f61e2d và DONEexact9inputhashes được root/platform phối hợp.

`require_research_authorization(... authorization_file,expected_authorization_sha256)` kiểm externalartifactSHA, closedschema/scope/run/config/spec/fullidentity/exacttypedcaps/requested4phases/approvalreference và freshoutputabsence. GatePASS/approvedboolean/decisionstring một mình không authority. Trả typed `AuthorizedResearchExecution` có `revalidate` để so lại artifact/input/source/runtime sau đó; token là cooperativeconsistency receipt, không unforgeablecapability hay nonresettableglobalbudget. Không mkdir/write output hoặc import model. FutureBATCH3 phải consume+revalidate trước lazyimport/allocation, kiểm reservation/durableledger/resource/corpus schema; native low-levelAKTAdapter vẫn tự nó không có authguard.

Purpose ghim **a0_single_candidate_lifecycle_pilot**, allocationA0 và `NOT_RUN_MAIN_MATRIX_DEFERRED_BEFORE_ANY_MAIN_REFIT`. Không gọi A0alone là conservativegraphsystemwinner. Mainmatrix phải chờ toàncandidate rawselectionpredictions→systemselectorfreeze→bất kỳ refit/calibration nào; không chọncandidate sau khi xem refit/calibration.

## Pending trước merge/execution

Parent fullsource review còn cần trước commit/actualexecution. Chưa sourceGate hiện hành, actualcorpuspublication, actualruntime/preflight, actualauthorization hay modelrun. Publisher độc lập đang triển khai schemađãthốngnhất; rawcollectorcomposite recipe/profileSHA vẫn giữ nguyên lịch sử, normalizedsharedrecipe không giảrawSHAequal. BATCH3 chưa được viết, phải kiểm actual ObservableTrajectory roles/targets/source-row/history/support và đủ jobbudget trước model, rồi selected/refit90/calibration wiring. Không nói guard unitPASS là fittedresearch/realdata/CUDA/Gate/RQready.

## Restart amendment trước first real publication

Parent phát hiện gap thật: oldplanwrapper chỉ manifest không đủ namespace/root_seed để dựng ResearchSplitPlan; rolemanifest cũ chỉ summary thiếu actual ResearchProvenance. Đã lưu old8a/77d/f61 thành `.pre-repro` snapshots trước sửa, không dùng oracle hoặc `object.__new__` để lách typedconstructor.

ProspectiveV1 mới, cùng9modelinputfiles và DONE4keys: `plan.json` exact `{schema_version,recipe,manifest}`; recipe exact5constructorfields(namespace,root_seed,development_learners,final_learners,protocol_sha256). Guard dựng **actual ResearchSplitPlan(**recipe)** và so toàn reconstructedmanifest với declaredmanifest, không chỉ so count/opaquehash. Rolemanifest nay16fields, thêm actual `asdict(ResearchProvenance)` và identity. Guard dựng typedprovenance sau tuple-normalization của sourcebindings rồi kiểm role/plan/split/domain/G_env/clock/policy/sourcecollector/sourceinventory và sameexplicit environmentsemanticsSHAcrossroles. Mỗi role còn giữ compositecollectionrecipeSHA riêng do profilemap khác.

Không import collector/NumPy/pandas để validate formula: derive rawrecipe4fields+collectorversion/clock theo **source-pinned formula** trong collectorbdbe7458; composite hash gồm rawrecipe, rawrecipeidentity và roleprofileSHA. Originalcollectionreceipts không đổi. Sharedpublisher đã nhận exact schema SHA `ba4a3d8ca412395b4b3841da010c736f1ceac3d5bd1a67e5de87ef7c7287e578` và guardSHA `72f5a1e981b63c3edf6ff51013a80c9b5680abe18f98d03e190da0d2ed675e5a`; không independentfields/schema drift.

Root explicitly nâng **total cumulative cap30→60s**, giữ spent13,623352999941377s và ghi `budget-revision03.json`; lý do chạy toàn revisedguard+restart/provenance cases+knownpurelegacyconfig, không pass-selectedtests sau parserchange. Actual03: **81revisedguard+6legacyconfig=87PASS**, console9,79s/JUnit9,609s/controller10,262182235717773s, tổng23,885535235659148/60. Không chạy2Gitfixturetests của test_provenance.py. Raw01/02 vẫn đúng60+1 và61PASS oldschema. Mỗi trial03 có13inputSHA trước=sau/26snapshots;0Torch/model/optimizer/innerprocess. Receipt03 `fa6a5506b07dcc977f239bd1b139d3a7009c520ed86bb7e533692032a394bd3e`, JUnit `f61a8cb93ad4c9bf2a880897ab1bb6f1e663ecdf5d3534b901b6c64c4581f199`.

FinaltestSHA `6379da3924c2ca56efb1c8d1ac177979d485893ea17951d3a8dd7d8f728caa8a`, config vẫn beb2f883… và legacyasdictgolden không đổi. Restarttest trong guard chỉ plan/provenance+metadata, JSONLfixture vẫn intentionallyunparsed; publisher riêng sẽ kiểm full observable payload roundtrip vào actual roleauditor. Không gọi điều này actual corpus/trainer/Gate-ready hoặc modelmethod adoption mới.

## Narrow junction correction và freeze cuối

Read-only đối chiếu publisher phát hiện ownreader chỉ kiểm is_symlink, có thể bỏ sót nestedWindowsjunction. Root duyệt narrowaliasfix: `_path` reject is_symlink **hoặc is_junction nếuAPIcó**, choROOT và mỗicomponent; không đổi schema/method/caps. Thêm3canaries corpus/auth/evidenceancestor với Path.open luônraise để chứng minh rejecttrướcread, một normalpathpositive/optionalAPI test; không actualOSjunction creation hoặc pathescape experiment.

ONE fullnewfile04 **85PASS/0failure/error/skip**, console8,04s/JUnit7,870s/controller8,471940279006958s. Cumulative32,357475514666106/60,0Torch/model/optimizer/innerprocess;12inputs trước=sau/24snapshots. GuardSHA `5ea3d7283f6d8da6eab712d4e4fedb48cd41717f99cd3ae51fb7b8651b16c7b6`; finaltest `9289f3aa4c8948f3e62344d11f01ea596764f78a42f1e2291aafc92178f72ba4`; receipt04 `5f21114b1e7d1cbe75a14e13a8aeaf683d783a2463ccdc6e7cbe92897ba07ec6`; XML `c77eda2a50b6c9d2b1f98f7bf7374dcdca36618795616fff04e02c6e2ccc0276`.

Publisher31PASS compatibility run bên agentplatform vẫn đúng **historicalguard72**, không relabel là5ea3; schema không đổi nên không rerun publisher chỉ để thay identity. Scope/budgetrevision/raw01failure/oldschema đều giữ cho archive. Parent cần finalsource review trướccommit/actualexecution; phần này chưa actualnativeGate/runtime/corpus/trainer.
