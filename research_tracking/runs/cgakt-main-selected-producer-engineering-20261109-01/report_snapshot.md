# CG-AKT main selected-only: module đã triển khai, kiểm tra orchestration bằng mocks

Ngày09/11/2026. Trạng thái: **MODULES_IMPLEMENTED_ONLY_MOCK_ORCHESTRATION_VERIFIED**. Hai module mới đã được import và16 trường hợp kiểm kỹ thuật đạt ở attempt02. Chưa có actual main authorization, actual guard/Gate/corpus admission hay model fit được kiểm trong batch này. Test không đi hết success path của public entry.

## Phần vừa bổ sung và vì sao cần

Pilot A0 cũ tự đi tiếp sang refit/calibration; không được dùng như producer cho chín candidate trước external freeze. Batch này giữ pilot nguyên vẹn, thêm guard và runner riêng cho **selected-fit80 → raw selection10**. Trong mỗi epoch, selection10 được dùng để chọn epoch; final best export là bước riêng. Không thực hiện system winner, external freeze, refit90 hoặc temperature calibration.

| Phần | Implementation mới | Bằng chứng trong batch | Chưa chứng minh |
|---|---|---|---|
| Guard | Concrete spec; auth schema đóng; actual runtime/lock/Gate/source/public-corpus/graph validators trong conditional path | Reject scope/phase/caps/authority sai; thiếu auth dừng trước reader; metadata class và schema mocks | Chưa gọi thành công guard bằng actual approved auth/runtime/Gate/corpus |
| Windows Git profile | Root-bound native03 profile; pin Git/EOL/upstream bytes; giữ nguyên genuine preflight/Gate calls | Profile metadata hợp lệ và extra transport/config/root mismatch negatives | Không chạy Git, không actual runtime/Gate; không Linux-portability claim |
| Optimization | Reuse native train_epoch, graph collate và GraphAdam participation; cumulative reservation/body-return/commit/targets | Mocked callbacks kiểm train-only phase, counters và final progress không double-charge | Không actual model, loss/backward/Adam/gradient hoặc complete-epoch receipt |
| Epoch selection | Per-epoch read-only raw selection entitlement; native BCE/EarlyStopping config không đổi | Predictor fake trả đủ query trước khi join nhãn; OOV null và full denominator giữ nguyên | Không actual selection metrics hoặc đủ các epoch |
| Best state/export | Save theo train index, fresh owned best reload, raw-best exports/ArtifactClaims trong source | Delegation/quota/constructor-limit/counter tests bằng objects giả | Chưa actual checkpoint serialization/reload/exports hoặc full public-entry success |

Mã mới: [research_main_execution.py](../../src/knowledge_tracing/akt/research_main_execution.py), [research_selected_runner.py](../../src/knowledge_tracing/akt/research_selected_runner.py); tests: [guard](../../tests/akt/test_research_main_execution.py), [orchestration](../../tests/akt/test_research_selected_runner.py). Entry tự gọi factory actual guard **một lần bên trong hàm**; không nhận caller guard/callable/MainStageNOAUTH làm quyền chạy hoặc đặt lại đồng hồ. Source giữ configmaxepochs20/dropout.05/patience3/min_delta.0001, không giảm recipe để vừa test.

## Kết quả đã quan sát, gồm lỗi test đầu tiên

| Attempt | Raw JUnit/pytest | Worker receipt | Outer stored pre-receipt | Kết luận |
|---|---|---|---|---|
|01|16 chạy:15PASS,1FAIL,0error/skip; pytest1.21s|4.000526666641235s|5.231323480606079s/60|REJECTED; lỗi assertion JSON representation trong test |
|02|16PASS,0failure/error/skip; pytest0.72s|3.29028069996275s|4.403451681137085s/60|ACCEPTED_16_MOCKED_MAIN_PRODUCER_ENGINEERING_ONLY |

Outer01 `counts=null` vì từ chối worker RC1 trước khi lấy counts; raw child/JUnit thực sự đã chạy16, không phải0test. Failure duy nhất so object Python từ `asdict` với auth file đã decode: `caps.git_profile.upstream_files_sha256` tuple-of-tuples được JSON đổi thành list-of-lists. Revision02 chỉ sửa expected test thành **toàn bộ wire JSON/caps/identity**; giữ negative cap drift, production guard/runner không đổi. Không nới schema, không bỏ field hoặc fake grant.

ROOT báo thời gian terminal quan sát01 là5.236512999981642s; terminal invocation02 là5.1072546s và stdout cuối02 là4.408845399972051s. Đây là các mốc quan sát khác nhau, không thay stored outer/worker timings trong bảng. Controller02 giữ prior charge01 và maximum cộng allocation65.23651299998164s, không reset chi phí lỗi.

Hai lượt giữ before=after source/runtime fingerprints; real cached caller/module class identity ổn định, không reload/alias. Native Windows metadata dùng thật `platform.uname` + `platform.processor`, mỗi lượt quan sát **một** system cmd literal `ver` trong bootstrap, sau đó phase đóng;0Popen attempts sau phase. Vì vậy không nói0process tổng thể. Temp environment trỏ owned runtime-temp trước pytest imports, plugin autoload tắt; monitored peak RSS02=50,909,184bytes, minimum free RAM=4,725,043,200bytes trong bounds1GiB/2GiB. Monitor dừng, selected environment được restore; cả hai owned receipts xác nhận cleanup accepted/Job active0/handle closed.01 vẫn rejected vì test RC1, không vì cleanup.

Không import NumPy/Torch/pandas/model; denied attempts rỗng,0NN/optimizer/actual corpus/Git/preflight.16testcase executions không là16mẫu nghiên cứu, và lặp01/02 không tăng independent N.

## Giới hạn và bước còn thiếu

1. Success path đầy đủ của `run_main_selected_candidate` chưa được test đi xuyên suốt; source đã được import qua fixtures, không phải thực thi các conditional model branches.16PASS không certificate actual training API integration. Cần actual approved input/auth và một allocation do ROOT chốt riêng trước khi chạy.
2. Matching Windows Git profile vẫn phải qua **genuine current Gate/runtime/source**; profile metadata tests không actual Gate acceptance. Nguồn mới làm Gate derivative cần refresh sau khi các source batches freeze. Batch này không tuyên bố current Gate hợp lệ.
3. Implementation đầu tiên chỉ Grade10 simulator CPU A0–A3. SAKT/GKT/Junyi bị reject trước data/model; **vẫn là phần bắt buộc** của required9/two-environment protocol, không được bỏ. Expert topology/Method24 artifact phải là actual pinned inputs ở lượt thực; fixtures không thay chúng.
4. Module receipt/ArtifactClaim/MainStage là consistency metadata, không external freeze authority. Chưa all9 actual terminal file admission, system selection, main refit/calibration, lifetime resume, fitted efficacy hay RQ completion.
5. Wall/RAM sampling là cooperative checks cộng owned Job cleanup, không blanket OS sandbox/hard RAM quota. Actual conditional success vẫn cần post-budget/source/output/failure checks của outer; không suy quyền chạy chỉ từ spec hoặc16PASS.

Raw01/02, pre-wire-fix source snapshots, controller/packet, cold imports, JUnit và copy-SHA được chuẩn bị cho bundle `cgakt-main-selected-producer-engineering-20261109-01`. Actual closure/integrity được xác nhận riêng bằng manifest sau ROOT review; không chạy lại tests/model để đóng gói. Runtime/corpus/dependencies chỉ giữ fingerprints/pointers, không copy vào bundle. Báo cáo này không thay hai tệp báo cáo GVHD hiện hành.
