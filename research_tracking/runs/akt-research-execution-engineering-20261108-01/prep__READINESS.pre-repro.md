# BATCH2 — guard CPU A0 simulator-research, chưa execution

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
