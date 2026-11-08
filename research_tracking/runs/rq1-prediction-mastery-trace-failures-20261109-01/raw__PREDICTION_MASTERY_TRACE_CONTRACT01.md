# Chuẩn bị trace θ/pi và ba reference items — chưa chạy

Đây là implementation trong prep hiện có, không sửa nguồn Gate154 hoặc artifact cũ. ROOT xem source/pins rồi tự dispatch; không cần xin lại user cho engineering đã giao. Không có native/tests/import do agent chạy trong lần chuẩn bị này.

## Phạm vi và admission

Nguồn fixed runner đã phục hồi từ Git e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a; SHA402dca…dd45. Hai enabled variants full/empty, cùng9stream20000–20002×PG/PY/PYH×120. Full/empty chỉ đổi estimator edges; controller graph và source loader nguyên bản. Không dùng giới hạn missing-runner của nhánh closed-loop cho nhánh fixed này.

Worker đọc cả3240legacy và3240sidecar để kiểm toàn bộ key/CRC; chỉ replay2160rows full/empty. Các query và cached y phải exact-join1080keys giữa hai variants. Không tạo student/environment/persona, không draw RNG, không NN/optimizer, không oracle/corpus/final/Holdout. Các native class definitions được load bằng allowlist loader cũ; instantiate duy nhất18GAM policies.

Trước current y update: đọc θ,pi_task và hai predicate/all28concepts; call currentpredict một lần; deepcopy frozenstate; thêm đúng2predict cho2reference items còn lại của queriedconcept. Currentquery là1trong3real items1050/1200/1350 nên reuse probability, không gọi lại. Probeclone statehash không đổi. Gọi preview select trên clone; sourceoriginal không thay state; ghi S28/M/R/P/fullpreview sau exact đối chiếu2160rows. Sau đó mới native update với cached y và literal logged-item bookkeeping. Snapshot không chứa current answer; legacy hash chỉ là reference integrity. Profiles chỉ định danh nhóm cũ, không model inputs.

**Admission toàn bộ hoặc STOP:** exact2160P/S28/M/R/CID/fullpreview,18initial và18finalstate fingerprints đối chiếu C13,18×120updates; không rowdrop/tolerance/filling-hidden-state. 2160state snapshots mới chỉ được diễn giải nếu outer accepted và cleanup accepted. Không fit/calibrate/đổi selector hoặc dùng referencecriterion điều khiển.

## Ledger và tài nguyên

- Direct exact: constructors18; currentpredict2160; referencepredict4320; update2160; previewselect2160; ready_set2160; mastery_score60480; is_mastered60480.
- Native all-call counters qua code-ID profile: predict6480,update2160,select2160,ready_set4320 exact; mastery_score60480..120960 (bao gồm key calls trong selector), is_mastered≤451440 (bao gồm ready predicates/update). Callback không fingerprint fullvars; fingerprint ngoài callback để kiểm frozen probes và endpoint.
- Reserve toàn bộ direct work bền vững trước native constructor. Khi hardkill chỉ biết actualUNKNOWN≤reserved, không coi0. Có cumulative attempted/returned counters và trajectory receipts sau mỗi120events; không retry/reset.
- Cumulative60s: **reserve bảo thủ10s cho pure12** (dù thực tế ít hơn), còn native outer≤50s, gồm owned Job cleanup2s và finalization2s. Worker allowance tính từ remaining thực tế,≤45.9s; không forecast runtime, không nới trên timeout. Hai phase có outputfresh cố định riêng, không chạy native nếu pure cùngplan chưa accepted.
- RSS/peak≤512MiB, freeRAM≥1GiB; kiểm trước/sau heavyimports và mỗi10events/trajectory/final. Cooperative checks giữa operator; outer owned Job enforce wall/cleanup. Đây không là chứng minh hard RSS containment giữa samples.
- Input thường≤4MiB/file; gzip decompressed≤16MiBlegacy+8MiBsidecar,3240records mỗi stream,≤64KiB/record, CRC EOF. Outputfile≤4MiB,total≤16MiB,trace unpacked≤16MiB,2160records≤32KiB/record. Worker profile phải trống trước khi install và được restore. Không network/subprocess trong worker; nếu NumPy/Pandas cần metadata subprocess trên host thì STOP trước native, không fake metadata hay tự mở guard.

## Fixtures nhỏ nhất có ích

12unittest functions, chỉ stdlib/FakePolicy, không cache/native data: θ/pi inclusive boundaries/nonfinite;3realrefs identity/duplicate/difficulty/currentmembership; onecurrent+twoprobes count; no y argument/original unchanged; mutation rejection; nativeM khác raw3ref criterion; exact signedzero/fullpreview admission; update-before-literalbookkeeping; all8zero-preserving predicate cells. Không claim native parity từ fakefixtures; native toàn2160 là admission riêng.

## Outputs và diễn giải

Native `prediction-mastery-trace-attempt01/`: dispatch/reservation,trace.jsonl.gz,18trajectory receipts,worker_run.json; outer ownedlogs/cleanup/finalsourcehash. Không summary chọn số mới hay inference ở bước trace. Các nested `native_state` có thứ tự `[theta,pi_task,theta_gate,pi_gate,M]` theo node order trong C13 source. Rawrefcriterion mean≥0.5637150147511514 chỉ raw response readout, **chưa calibratedV1/mastery truth**. Bước kế tiếp sau acceptance mới tính partition30240pairedconcept snapshots, giữ8cells/allgroups. Reused9streams/newN0, preview không served, không causal mediation/learning benefit.

Source/input hashes nằm trong `prediction_mastery_trace_plan01.json`; plan giữ cả bound loader snapshot và currentloader cùngSHA, notebook/4CSV, archived recoveredrunner/parity/legacy/sidecar/provenance và fingerprint serializer source C13. Không copy154Gate files. Source worker/outer/tests đều mới, version01; không sửa note/source/archive cũ.

## CLI ROOT sau review pins

Dùng `.venv\Scripts\python.exe -B <prep>/run_prediction_mastery_trace01.py --phase pure --plan-sha256 <SHA_PLAN> --approval-reference <ROOT_REF>`; sau pure accepted, cùngCLI `--phase native`. Chưa có dispatch từ note này. Mọi failure giữ nguyên và STOP.
