# Kiểm tra collection của Gate — hồ sơ vận hành ngày09/11/2026

**Nội dung hồ sơ vận hành đã chốt; cả5lượt collection đều bị từ chối, không có full Gate PASS từ batch này.** ROOT đã dừng thử thêm. Báo cáo được freeze trước khi đóng raw bundle; xác nhận closure và manifest sẽ theo chỉ mục/bundle thực tế, không phải một lần collection được chấp nhận. Không chạy lại collection, test hoặc mô hình khi viết báo cáo, không sửa current Gate pointer hoặc các kết quả trước. Đây không phải bằng chứng nghiên cứu mới.

## Mục đích và ranh giới

Gate phải chạy đủ các tests trên các nhóm process riêng vì một số fixtures yêu cầu chưa import Torch, trong khi các module khác import Torch từ lúc collection. Trước khi bỏ thời gian cho full Gate, collection kiểm danh tính process và inventory test nodes của ba nhóm: stdlib, no-torch và remaining. **Thu được tên test không có nghĩa test đã chạy hoặc PASS.** Module tops vẫn có thể được thực thi trong collection; worker chặn test bodies, constructor neural, backward/optimizer, solver fit, teacher/data parsing và network.

Packet ROOT cố định154source bindings,69test modules và lock/upstream inputs. Mỗi trial có một ngân sách60giây cho cả ba nhóm, cleanup và posthash; không đặt lại60giây cho mỗi child. Admission RAM4GiB, available floor1GiB và quan sát RSS tối đa3GiB mỗi process được giữ. Đây là resource polling hợp tác, không quota RAM cứng hoặc bằng chứng GPU sẵn sàng.

## Các lượt đã quan sát

| Lượt | Thời gian lưu trong outer final | Kết quả vận hành | Điều thực sự biết được |
|---|---:|---|---|
|01|1,84325999999419s/60|REJECTED_COLLECTION; chưa có child result|Guard ancestry từ chối trước pytest. stderr giữ nguyên; không có số test PASS.|
|02|1,65571510000154s/60|REJECTED_COLLECTION; chẩn đoán ancestry|Parent và thứ tự creation time đúng; psutil trả path shim thiếu drive, khiến so sánh exact path sai. Không được suy đây là lỗi timestamp hoặc import denial.|
|03|53,991140099999s/60|REJECTED_COLLECTION; remainingRC124|Nhóm stdlib thu19nodes, no-torch271nodes; remaining không có result cuối. Không có inventory toàn bộ hoặc full Gate PASS.|
|04|38,97974491119385s/60|REJECTED_COLLECTION;3import errors|stdlib19/no-torch271 đã có result; remaining thu984node IDs nhưng lỗi import ở3modules, nên toàn lượt không được chấp nhận.|
|05|2,2571663856506348s/60|REJECTED_COLLECTION trước pytest;0collected|Normal imports của hai subnamespace đã trỏ đúng repository, nhưng assertion parent namespace phải độc quyền một path bị vi phạm bởi path `win32/scripts` trong môi trường.|

ROOT quan sát terminal lần lượt1,8486731s;1,6587846s;53,9976515s. Đây là ranh giới quan sát khác với elapsed trước ghi outer receipt trong bảng; không thay bytes raw hoặc dựng lại một terminal log chưa lưu. Builder chỉ dùng thời gian có trong receipts để kiểm resource contract; optional observation ROOT nếu có được giữ nguyên riêng.

Với04, ROOT quan sát terminal38,9863628s/60. Việc tắt terminal reporter đi kèm thời gian ngắn hơn03, nhưng không đủ để quy toàn bộ chênh lệch thời gian cho thao tác đó. Không có phép đo cô lập overhead hoặc benchmark lặp.

Với05, ROOT quan sát terminal2,2594246s/60; outer final lưu ranh giới trước ghi receipt2,2571663856506348s. Không cộng thời gian từng child thành một phép benchmark hoặc coi các trial là các nghiên cứu độc lập.

### Danh tính shim được sửa hẹp, không bỏ guard

Lượt02 lưu `exact_parent=true`, `creation_order=true`, `exact_venv_entry=false`. Path psutil là `\Dev\KLTN\.venv\Scripts\python.exe`, thiếu `D:`, còn đường dẫn entry đầy đủ có drive. Lượt03 dùng `QueryFullProcessImageNameW`, process ID và FILETIME từ handle thật, đồng thời giữ PPID/thứ tự thời gian, binding exact named Job và yêu cầu đóng query handles. Không tự thêm prefix drive, không chấp nhận suffix tương tự, không nới tolerance thời gian.

ROOT đã quan sát8pure shim checks PASS trước dispatch03. Đây là unit checks cho predicate, không8research samples hoặc bằng chứng đủ native collection. Root review ghi rõ đó là quan sát terminal; không có XML/log nguyên bản để tự tạo thêm. Các child receipts của ba lượt đều giữ thông tin owned cleanup, Job active0 và handle closure riêng, kể cả childRC1/124.

### Phần còn thiếu sau03

Hai group results của03 có trạng thái `COLLECTED_ONLY_PENDING_OUTER`; outer giữ290node IDs của hai nhóm. Không cộng chúng với output partial của remaining hoặc gọi290tests PASS. RemainingRC124 và thiếu `result.json` chỉ cho biết không hoàn tất trong phân bổ; **chưa xác lập nguyên nhân timeout** từ các dữ kiện đó. Counter kết thúc riêng của child thiếu result không được tự điền0. Nguồn chỉ cho phép collection và chặn các công việc mô hình; không có lời gọi full test suite, neural training hoặc research fit được dispatch ở đây.

Ở04, cả remaining result và counters đã được lưu:3collection errors liên quan `scripts.akt`/`scripts.research` trong `test_runtime`, `test_synthetic_context_builder`, `test_rq2_controls`. Counters đều0, profiler restored và monitor stopped theo result của04; không gán ngược telemetry này sang03.984nodes chỉ là inventory thu được giữa các import errors, không984tests PASS, và không cộng với290nodes để tuyên bố inventory hoàn chỉnh đã được chấp nhận.

ROOT yêu cầu05 thêm repository ROOT vào sys.path để phản ánh cách gọi Python module. `scripts-namespace-before.json` của05 xác nhận import thật của `scripts.akt` và `scripts.research` có search paths duy nhất tương ứng dưới repository. Tuy nhiên, namespace cha `scripts` có hai paths: repository/scripts và `.venv/Lib/site-packages/win32/scripts`. Assertion yêu cầu cả namespace cha cũng chỉ có một path đã từ chối trước pytest. Đây là vấn đề admission của controller; chưa phải lỗi test source hoặc lỗi mô hình. Result05 lưu0collected/pytest_exit_code=null, zero-body counters0, profiler restored và monitor stopped; owned cleanup Job0 được giữ.

**Bước hợp lệ tiếp theo là kiểm provenance của namespace ngoài, chưa sửa hoặc chạy lại trong batch này.** Cần đọc metadata/RECORD và cấu hình đường dẫn của pywin32 trong `.venv`, đối chiếu hash/origin của path `win32/scripts`, rồi xem namespace đó có thể che các submodules được yêu cầu hay không. Sự có mặt của tên thư mục chưa tự chứng nhận nguồn package; snapshot05 chỉ chứng minh path đã được import. Sau source review mới chốt predicate phù hợp: giữ xác minh origins của target subnamespaces, không tự bỏ guard, xóa `.pth`, sửa package/globalPython hoặc giả namespace để qua collection.

Một full Gate mới vẫn cần chạy toàn bộ test bodies với resource/source/coverage checks và publisher/reader hợp lệ; inventory collection không thay điều kiện đó. Batch01–05 kết thúc với **chưa có collection toàn bộ được chấp nhận**, không full Gate/currentPASS. Không tiếp tục retry hoặc tăng cap bằng hồ sơ đóng gói này.

## Bằng chứng và cách lưu

Prep hiện tại: `artifacts/akt/local-tests/akt-research-runner-20261108-01/`.

- `gate_collection01_packet.ROOT.json`, SHA `bacc6e49d14d244396b7be03cf68c62daefa8c14adf056b1f0c5cde8b8f1ed90`, cùng template ban đầu và ROOT reviews01–05.
- Các `gate_collection_worker01–05.py`, `run_gate_collection01–05.py`; `GATE_COLLECTION01_REVIEW.md`, `GATE_COLLECTION03_FIX.md`, `GATE_COLLECTION04_REPORTING_HYPOTHESIS.md`, `GATE_COLLECTION05_ROOT_PATH.md`, `test_gate_collection_shim03.py` giữ source và giới hạn đã duyệt.
- `gate-collection01–05/` giữ child metadata/import inventory/collection logs nếu đã tạo; `gate-collection01–05-outer/` giữ before/final, từng owned launch/ready/GO/receipt/stdout/stderr. Không bổ sung result còn thiếu hoặc sửa failure. Namespace snapshot05 giữ đủ các paths đã quan sát, không viết lại cho khớp mong đợi.
- ROOT đã đối chiếu đủ154raw Git blobs tại commit `2c337d4` với packet và worktree: `gate_frozen154_raw_git01.json`, trạng thái `FROZEN154_RAW_GIT_AND_WORKTREE_VERIFIED`, SHA `b940fadffb25a4f93bc6733c23ae9005aeb68f1caa16c0410a0253367feba833`. Mã verifier `verify_gate_frozen_git01.py` SHA `0bf0d01fd100579efbcf649c69db45478077c8745444d440eed52e16d61bd589` được giữ cùng proof; archiver không chạy lại Git verifier. Không có source exception cần snapshot riêng.
- Archiver dự kiến `archive_gate_collection_trials01.py` bắt buộc explicit final trialset01–05; không tự thêm lượt vì thư mục mới xuất hiện. Sau ROOT review dry mới được đóng một run riêng; SHA/size scratchcontrollers/reviews/rawoutcomes và copy được đối chiếu trước/sau, rồi dùng `verify_evidence_bundle` kiểm outputs.154production sources/notebooks đã có commit và SHA nên **không nhân đôi vào bundle**; lock/upstream chỉ giữ hash pointers trong packet. Nếu các scratch inputs drift, dừng để ROOT review; không cập nhật packet nhằm che drift.

Không file count, test-node count hoặc unit checks nào là independent research N. Hồ sơ này là bằng chứng vận hành về ranh giới import/process và failure hữu ích; không thêm phát hiện RQ1–RQ3, fitted model, CUDA readiness hoặc full Gate/current PASS.
