# AKT Linux CPU: điều tra source, runtime, software gate và dummy main worker — 08/11/2026

Đây là hồ sơ kiểm kỹ thuật trên Colab CPU, chưa phải kết quả baseline/RQ, CUDA, image hay dự báo chi phí. **Actual Linux full software Gate24 PASS: 771/771, không failure/error/skip** trong suite `tests/akt tests/shared_kt`; **actual CPU dummy main worker accepted**, với hai cập nhật tham số thật trên fixture synthetic. Raw text và chín bản sao local, gồm bốn binary, đã được kiểm độc lập. Báo cáo sẵn cho parent duyệt SHA cuối; bundle `akt-linux-worker-readiness-20261108-01` chỉ đóng sau phê duyệt đó.

## Chuỗi bằng chứng và failure được giữ nguyên

Nguồn gốc dưới [`gpu09-cpu-worker-kit-20261108-01`](../../artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/). Các thư mục `received-*` chứa raw text cùng receipt kiểm SHA/size; chúng không phải wheel, venv hoặc dữ liệu nghiên cứu.

| Giai đoạn | Kết quả thực tế | Ý nghĩa/giới hạn |
|---|---|---|
| Materialization ban đầu | 161 file; receipt `debb7590e8fd1247bcbdf7a479c2ea204b7d8625414c989b0a4bab5c1e831c3b` | Source-only, chưa software gate. ZIP nền SHA `b6707cfd0139898a22dd04db9095d01622c1df9b7061f05f8579ecb4ab30d233`. |
| Checkout upstream01 | `FAILED_UPSTREAM_CHECKOUT_RETAIN_NO_RETRY`, 1.5021834 s | Không sửa lịch sử thành PASS. LF audit read-only sau đó được xác minh riêng, không là Linux gate. |
| Native runtime02 | `ACCEPTED_NATIVE_RUNTIME_CPU`, 8.1894953 s, cleanup accepted | Report SHA `31974cac738a28ae6db6b609f75d596b43e993f2e51a2d5c946ed8ed65675cd6`; không chứng minh CUDA execution. |
| Gate23 | **763 PASS / 5 FAIL**, controller 261.7189893 s | Bốn case thiếu loader upstream; một case so sánh fixture ở số CPU thread khác nhau. Không có PASS report/pointer cho lần thất bại. |
| Chẩn đoán graph | Numerical observation riêng, không Gate | Với số thread khớp, tuple output khớp chính xác; không nới tolerance và không đổi native model. |
| Loader cache01 | `CACHE_MISS_NO_MUTATION_NOT_REMEDIATED` | Không giả source Git. |
| Loader source03 / transfer02 | `FAILED_TRANSFERRED_LOADER_RETAIN_PARTIAL`, 0.00144345 s | Preflight chặn pin SHA sai 65 ký tự trước child; không coi ba mock metadata trước đó là kiểm hết CLI/pin. |
| Loader source04 / transfer03 | `MATERIALIZED_TRANSFERRED_PINNED_LOADER_SOURCE_ONLY`, 0.236596972 s | Chuyển local Git blob ghim sẵn, kiểm Git object/HEAD và source identity; không network. Receipt SHA `f500a58833c4b3b7f330a565d48eb606de02786a268a14ae488972525016ff24`. |
| Fixture local | **26 PASS**, controller 13.1712854 s | Chỉ sửa test kiểm cùng thread; native graph SHA giữ `c7e9ce13a6225d60c550640b48c173275a6d5b353959eec133cd20b8c08afc84`. |
| Delta source01 | `ACCEPTED_TEST_ONLY_SOURCE_DELTA_NO_EXECUTION`, 0.099154513 s | Kiểm 161 file; đúng một test đổi, 160 file giữ nguyên. Materialization02 SHA `bde7e1366cba0a04b7a62d5ef12218b9456ff6aec4e1c272621bc5cd518a3211`. |
| Gate24 producer01 → 02 | Parent phát hiện thiếu ba argv LF audit trước dispatch; producer02 sửa wiring | Tám metadata tests không phát hiện bug CLI. Một test CLI mới parse argv bằng parser thật, kiểm thiếu ba flag bị reject; **1 PASS**, không gọi operation. |
| Gate24 actual | **771 PASS / 0 FAIL / 0 ERROR / 0 SKIP**, native **268.092342194 s ≤ 600 s**, phase **270.370416898 s ≤ 630 s** | 13 raw file/233.339 byte được kiểm SHA/size; XML 264.959 s. Cleanup accepted; native nguồn, lock, runtime và JUnit hash bind đúng. Đây là Linux software gate, chưa là worker/CUDA. |
| Prepare CPU dummy | `PREPARED_CPU_DUMMY_NOT_EXECUTION_AUTHORIZED`, **6.719945 s** | Native builder + bindings + preflight thực tế. Proposal chưa approved; execution cần authorization riêng. |
| Native CPU dummy main worker | `ACCEPTED_NATIVE_CPU_DUMMY_ENGINEERING_ONLY`, phase **26.110794024 s** | 32 raw text/198.941 byte, hai cập nhật tham số thật; native/watchdog RC0 và children cleanup accepted. Chỉ CPU dummy, không research fitted hoặc CUDA. |

## Identity và cách đóng bằng chứng

LF audit nguồn AKT ghim commit `01b7e8d7d7c862cabc9467108e3e7f2555653a88`, receipt SHA `1f116d3db2c88d2815bee73cb4471e56f6f442b744c4cd29cede7ce2a43cf952`. Loader `load_data.py` 6.428 byte, SHA `27550ccd07c1131971c4381f024c0f3795dba3d32b7f9fb4eea4ababd8bfe9e8`, Git blob `9fafe965e0b442242125250f37dc8c3f8a145edf`. Đây là bổ sung source upstream có kiểm nguồn, không là huấn luyện.

Delta chỉ đổi `tests/akt/test_graph_prototype.py`: SHA cũ `5e2aae220d1b862c337951182efab417a3ed81dd5eb6899f84af710a3cfd76ae`, mới `7a198d79b11b0c2e18af8532f26658e7119a2e352299d4bba66f859c16082f04`. ZIP nền vẫn chứa test cũ: không gọi ZIP đó là archive của 161 file nguồn mới. Hai raw JSON delta nhận đầu tiên chưa có backup/inventories; export Gate24 đã bổ sung đủ inventories trước/sau và fixture trước/sau có SHA kiểm độc lập, lấp khoảng trống archive này.

Gate24 tái dùng runtime02 có identity native producer/upstream không đổi. XML raw xác nhận 771 case thực tế, log và report cùng PASS. Report SHA `ce33155748c42de0cbaed4d1dad5762afc0f0e246a7dfa281a76d4d7545cb906`, JUnit SHA `2cfc7cdd4bd97f642468afca1ca5face4ab19a464588fb8c93daabd46372a98e`, phase result SHA `18aef3ae9340bbabcaf5e83edb826ddd6df8d5765e240039432c5a35449e8c37`. Lock Linux SHA `60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a`. Software gate có thể chạy fixture optimizer: không mô tả toàn Gate là 0 optimizer chỉ vì các kiểm metadata/offline có 0 model call.

Packager `pack_worker_readiness.py` mặc định chỉ tạo inventory mới, kiểm SHA/size các raw đã nhận, deduplicate theo SHA nhưng giữ từng group/path alias và receipt failure. Chỉ đóng bằng `record_evidence_run`/`verify_evidence_bundle` khi parent đã review report SHA và cung cấp root raw Gate24 thực tế. Worker là root tùy chọn; thiếu root phải giữ pending. Không đưa ZIP, wheel, venv, raw private MCP/base64 transport, checkpoint hoặc prediction binary vào Git.

## Actual CPU main worker: phạm vi đã chứng minh

Nguồn [`received-cpu-worker-evidence01`](../../artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/received-cpu-worker-evidence01/) có receipt SHA `dd7c9864c74a9f8fd9584fa24c14b37fb1ac3e665488372ce10be2df0bd3d874`; execution result SHA `7f932b8edc9e840de272c4b9bad60beb6617f6cbc31b93ae0578b8ed0e9fc714`; native manifest SHA `69d9a683e00fd055971c92b7548c9f644f05f8bc00549effbf5845a160d0e820`. CLI thật đi qua context, authorization, runtime/Gate24 và watchdog; đây không phải mock worker hoặc replay log.

Run `ctx-linux-20261108-01` dùng dữ liệu generator dummy, seed42, hai exercise và tám learner × tám events. Nhãn là PRNG bits, không là simulator truth RQ hay dữ liệu Junyi/Grade10. Phần thực tế được chọn gồm sáu learner train/48 target/sáu window và một learner validation/tám prediction, không unseen; không yêu cầu outer users hoặc Holdout. Native ghi hai optimizer steps, hai nonzero-gradient steps và hai parameter-update steps; completed epoch trong fixture này không chứng minh epoch selection tối ưu cho nghiên cứu. Không dùng metric dummy để kết luận chất lượng mô hình.

Caps thực tế bind vào authorization: CPU, smoke, tối đa hai steps, 64 target mỗi phía/128 tổng, 120 s native budget, 300 s watchdog wall, RSS 2 GiB, available RAM floor 1 GiB. Native summary **9.092991679 s**, watchdog **23.041204217 s**, controller **26.110794024 s** là ba phạm vi khác nhau. RSS train được quan sát **717.287.424 byte**, dưới cap; các mẫu available RAM trên floor. Parent kiểm ancestry public PID62650 → worker62661; watchdog completed, RC0 và controller child cleanup accepted. Đây là measurement theo process/sampling đã ghi, không whole-host accounting hay hard isolation.

Config semantic SHA `b0428ae16fc4942b155eb26cb1960f0ada46d21967ee97b8b2ef2438ecca1aba`, context SHA `42cc79d8c1fee18b1f4908de5a9c2f406a2f898b769aa2b81f9ab156e6959c4c`; context inputs, marker, LF source, lock, runtime và Gate24 records khớp authorization/native identity. Hash config native là JSON semantic của config sau chuẩn hóa path, không phải hash bytes JSON pretty-print. Check read-only đầu tiên của subagent đã sai giả định này; giữ log/source snapshot rồi sửa phép kiểm, không chạy lại worker hay sửa artifact để PASS.

Native xác nhận checkpoint reload state exact và checkpoint SHA `f77b39c6223f430c19f455c3a14d6dc42be139c4628f6f466146117921de8cc6`. Raw text ghi điều native đã kiểm; không có local model reload mới. Không coi checkpoint reload trong cùng run là resume proof qua runtime mới. Bridge hết TTL sau RPC hoàn tất; chỉ chuyển lại artifact đã có, **không rerun Gate/worker**.

## Lưu binary bền vững và lỗi transport riêng

Đích [`experiments/akt/results/ctx-linux-20261108-01/`](../../experiments/akt/results/ctx-linux-20261108-01/) được tạo mới, không overwrite. Bốn binary gồm assignments Parquet **668 byte**, events Parquet **2.452 byte**, checkpoint **441.721 byte**, prediction shard **3.537 byte**, tổng **448.378 byte**; năm native JSON/log giữ bytes/path metadata gốc. Receipt [`transfer-copy-inventory.json`](../../experiments/akt/results/ctx-linux-20261108-01/transfer-copy-inventory.json) SHA `1dedfa324488daa47c0604d2f1b81748ed3890b48a182a6ec9767d2c1cbcb8e8` bind inventory trước copy SHA `d3cb187a4568fd5cf3e2b34c08a9d60fe5aa7b3cf46a14d68e752401b7793a4a`. Kiểm độc lập chín destination: SHA trước/sau và kích thước khớp input context/native outputs ghim sẵn. Không load Parquet/checkpoint, không local fit.

Lần truyền binary01 dùng một base64 response quá cỡ bị **WSS1009**; normalized receipt `binary01-transport-failure-normalized.json` được kiểm độc lập từ prefix log riêng 1.703 byte, SHA `987ed7b7e6f90d539961fa227a92096cb961af0b3ffed85d0b41b3e23467a65d`, với hai tín hiệu `1009`, một `message too big`, một `max_size`. Không xuất raw log riêng. Client TimeoutError/disconnect là quan sát riêng của parent, không giả là field log server. Đây là lỗi vận chuyển, không phải lỗi model/Gate, và không tạo lại job. Cách truyền02 giữ nguyên giới hạn WSS, chia ZIP **339.800 byte** thành tám frame, tối đa **48.000 byte/frame**. Metadata các frame, hash sau ghép và CRC ZIP được kiểm; archive SHA `1982edc5ed1d2eac24990b961ac8110ceaab8ae113b1f250290b9fb4c87c6e71`. Giữ hai loại failure tách biệt: kết quả execution đã accepted trước lỗi transport, sau đó chỉ lấy lại bytes tồn tại.

**Ngữ nghĩa receipt quan trọng:** `transfer-copy-inventory.json.transport_sha256` là SHA của **envelope receiver01 được lắp và xác minh local**, không phải SHA raw MCP response. Receiver01 được giữ nguyên, nên không sửa receipt đã tạo để đổi cách diễn giải. Proof transport chunk02 nằm ở `transfer-cpu-worker-binary02/{acceptance.json,plan.json,first-receipt.json,chunk-*.receipt.json}`; local envelope được hash đối chiếu nhưng không đưa vào Git. Bundle chỉ giữ receipt/inventory/source/check nhỏ; ZIP, frame binary, envelope/base64, venv, checkpoint và Parquet ở ngoài Git.

## Acceptance còn thiếu

1. Parent duyệt SHA báo cáo rồi đóng một bundle thống nhất, giữ các failure lịch sử và receipt durability đã kiểm. Worker đã accepted từ native artifacts riêng, không suy từ Gate hoặc synthetic throughput.
2. Linux CUDA execution, GPU worker lifecycle, resume qua môi trường mới, refit, image/Modal, dự báo chi phí và benchmark/CV vẫn cần bằng chứng riêng. Windows Gate22 hay package Torch có CUDA metadata không thay thế chúng. Không có kết luận hiệu quả học tập/nhân quả từ hồ sơ này.

Các failure và limitation trên được giữ trong báo cáo và phải giữ trong archive. Chỉ mục/state/Git do parent quản lý; báo cáo không tự là chứng nhận archive đã đóng.
