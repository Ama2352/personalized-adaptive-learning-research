# Development corpus worker: orchestration bằng stubs

08/11/2026. Thêm [tests độc lập](../../tests/shared_kt/test_development_corpus_worker.py) cho [driver](../../scripts/research/collect_development_corpus.py), không sửa driver/config. **19cases đạt với stubs, không actual collection/publisher/reader/model hoặc NumPy/pandas/Torch.** Manufactured counters12.600 không phải observations đã sinh. Root giữ quyền chạy mọi test/native command và Git sau lượt đầu; agent chỉ chuẩn bị source/notes/closure script.

## Nguồn và scope

Driver SHA `09c909570e94ecc5bb87fdc7f4e75848fa53b91ea1317ab20a383bac4362e192`; public metadata config `experiments/akt/configs/simulator-research-corpus01.json` SHA `8e7800482cea61a5f3ab66e4909de996fda57bcc059dd2751c2e4177dbfa263e`, giữ nguyên qua hai lượt. Tests gọi actual driver functions với ROOT tmpFS, exact config bytes và17dummy source files; không mở learner dataset hoặc native teacher.

ResearchSplitPlan/resources/collection/publisher/reader đều stub rõ tên. Fake learner IDs, fake support/publication và counts chỉ kiểm control flow, không là actual typed split/seed/source/coverage attestation hoặc generation. Các contract đó có evidence riêng; batch này không thay nghiệm thu corpus thực.

## Failure được giữ, không reset budget

| Lượt | Kết quả thực | Controller | Diễn giải |
|---|---|---:|---|
|01|19setupERROR,0test bodies|1,2762708999798633s|Long tmp_path/testname+exact Paper2 source filename vượt Windows MAX_PATH; không driver bug |
|02, ROOT thực thi|19PASS,0fail/error/skip|2,531903400027659s|Short per-case factory/basetemp; stubs và audit guards |

Cumulative **3,808174300007522s≤20s**. Root ghi terminalRC0/toolwall3,0491501s và JS outer3235ms=3,235s riêng; không thay controller timing hoặc gọi là throughput. V1 source/test snapshots, log/XML/receipt giữ nguyên. V1 controller có toolRC0 dù pytest returncode1 vì thiếu SystemExit; không dùng RC0 đó làm PASS. V1 chưa audit subprocess, nên field0process cũ **không là global process-absence proof**; không sửa raw receipt để làm đẹp lịch sử.

V1 test SHA `3539479d3971a4b2e3eb42bb8a3176312e66813043c8f0ffe030369c7cc32134`; v2 chỉ đổi fixture sang `tmp_path_factory.mktemp('c')/workspace`. Basetemp mới `artifacts/akt/local-tests/dcw02` exclusive, không rmtree artifact cũ. `planned-path-lengths03.json` tính29full planned paths/c0..c18, max189chars, không generate fixture lúc tính. Metadata calculator02 bị lỗi array/measure, retained và superseded03; không dùng để dispatch hoặc kết luận path safety. Không sửa production filename/path/registry.

Controller02 direct `pytest.main`, self-timer cho remaining cùng20s ledger, không nestedPopen. Audit hook từ chối `subprocess.Popen` trước child creation; actual denied events0. Test-only `platform._syscmd_ver` giữ caller system/release, lấy major/minor/build từ actual `sys.getwindowsversion().platform_version` và lưu provenance, tránh platform/JUnit shell fallback. Không replace Popen class, OS/architecture, clocks hoặc library/production files; restore symbol/cache cuối lượt. Scope audit là controller/test process, không toàn syscall/host hoặc runtime Gate.

Outcome/exception gốc lưu trước guarded JUnit parse/posthash; SystemExit theo code/count/source/cap verdict. Actual loaded-heavy list rỗng, import guards từ chối NumPy/pandas/Torch. Không thêm hoặc nới model/data policy để làm test xanh.

## Những điều19cases kiểm

- Protected source path giả bị exact13+4allowlist từ chối **trước open**; frozen config/profile SHA và source-byte drift không được nhận.
- Existing corpus, output/corpus/source alias và wrong owner dừng trước generation/worker-output writes. Owner dict không là cryptographic authority; actual main vẫn phải qua owned Job gate.
- RAM guard trước/sau heavy import points và sau reader không tạo success receipt; lỗi sau fake publication giữ failure/published-but-not-accepted.
- Positive fake flow chỉ trả `WORKER_COMPLETE_PENDING_OUTER_ACCEPTANCE`, giữ outer_acceptance_required, reservation12600/actual_attempts=None, final_events/model/Modal0. Counters12600 được stubs dựng, không teacher calls; profile rule kiểm train16PG/16PY/16PYH và selection/calibration2mỗi persona.
- Missing support, reader mismatch và source drift sau reader chặn pending success. RAM lỗi sau pending receipt đã ghi vẫn return1+failure override; pending marker không là final acceptance.

Test final SHA `f2d80a0a2e29f86bc42d8ccc68d8e1709f8d7202f16723697a803d36c959fbb0`; controller02 SHA `2d82045441889d837e80c55df670475578ac238d7c970e34ef9cc24b8e87fefb`. Root review rồi chạy một lần:

```powershell
.venv\Scripts\python.exe -B artifacts/akt/local-tests/development-corpus-worker-engineering-20261108-01/run_pure02.py
```

Raw evidence ở `artifacts/akt/local-tests/development-corpus-worker-engineering-20261108-01/`: hai trials, root_trial02_dispatch.json, platform fixture, path metadata và source snapshots. [Bundle engineering](../runs/development-corpus-worker-engineering-20261108-01/manifest.json) lưu SHA trước/sau copy; không copy tmp dummy trees/realdata. Agent không chạy lại tests/closure; root thực thi closure script theo ROOT-only rule.

## Giới hạn

Không actual corpus generation/publication, diversity, correctness distribution, runtime/RAM forecast, fit hoặc calibration; timer/cooperative checks không hard OS quota. Batch này không mở quyền actual12600collection/training/Holdout/cloud. Actual bounded collection dùng source/config/caps/owned Job120 do root review/dispatch riêng. Không đổi protocol/counts/profile theo kết quả test, không RQ completion hoặc independentN mới. Shared tracking/Git do root quản lý.
