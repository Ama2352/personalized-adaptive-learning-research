# Demo MVP chỉ đọc artifact — 08/11/2026

Đã hoàn thành **một phần E11**: viewer/replay pilot synthetic bằng Python stdlib trên `127.0.0.1`, giao diện tiếng Việt, không dependency mới. Đây là sản phẩm minh họa bằng chứng đã lưu, chưa là hệ thống phục vụ học tập, chưa demo CG-AKT fitted và không bổ sung kết quả thực nghiệm RQ1–RQ3.

## Mở demo

Từ repository, chạy `.\.venv\Scripts\python.exe -m src.research_demo --port 8765`, rồi mở `http://127.0.0.1:8765`. Đóng bằng Ctrl+C. CLI không có tùy chọn đường dẫn dữ liệu, host, huấn luyện hoặc xuất file. Không dùng production hosting. Xác minh nguồn thất bại thì dừng trước khi mở listening socket. Server demo bình thường chạy đến Ctrl+C; các server visual QA có giới hạn 180 giây và đã được đóng sớm bằng stop marker riêng.

Source mới chỉ ở `src/research_demo/` (4 module, 3 static assets), test ở `tests/demo/test_viewer.py`. Không có demo/app tương đương trong inventory `src/`, `scripts/`, `tests/`, `paper1/`, `paper2/` trước lần thêm này. Trong tiểu tác vụ này không sửa parent AKT, native/upstream, scripts/research, config, Gate18, dataset, chỉ mục/state hay Git. Parent quản lý tham chiếu tài liệu/chỉ mục và commit riêng.

## Nguồn được ghim

Startup kiểm SHA bytes của **3 manifest và 3 selected outputs** dưới đây, rồi kiểm `status=completed` và output SHA trong manifest. Chỉ giữ dữ liệu đã xác minh trong bộ nhớ; không mở lại file tùy query. Không tự tuyên bố tất cả outputs của mỗi bundle hoặc source/Git hiện tại đều đã được kiểm bằng startup này.

| Bundle | Output | SHA-256 output | SHA-256 manifest |
|---|---|---|---|
| cpu-rq12-20261107-03 | traces.jsonl.gz | 22b065e8e0206403d2bcd41d175eeb1d686ed8bbf204c64f74d0e93d2aca0497 | 6592a80768e6608355cde1fd545ee90f6ca4ec937b2284a1e3eb42fae4f766f0 |
| cpu-rq1-transitions-20261108-01 | analysis.json | 597d4ce320af4601665d206b7ffe1fe1250ebd96114893e87a53e70ff49d3d28 | ff09520a20c7d0b6cbe18bdbfad3d4017e3106ca8628aa9cd2d38a4cb6591827 |
| rq2-conditions-evidence-20261108-01 | conditions.json | 5bbc381f8f5bc7b86f6035c6502a05e50728f7ee7202546eee46048b6bd2d6a1 | ed31bed55099c6e360d63dee47384b366744abc2f278b89d8a009a655c7ffc61 |

RQ2 conditions.json chứa cả phần tổng hợp Junyi ở nguồn; viewer chỉ chiếu key `factorial`, không trả phần Junyi. Không đọc dataset gốc, learner Junyi/raw/Test, credentials hay checkpoint. Không chạy lại simulator hoặc mô hình. Model status AKT synthetic / CG-AKT chưa fitted / SAKT chưa xác minh là chú thích phạm vi hồ sơ của MVP, không health check hay runtime model selector; replay thực tế là GAM-KT/Paper2 diagnostic. Hồ sơ kiểm kỹ thuật AKT riêng: `research_tracking/runs/colab-cuda-synthetic-20261107-01/`, không dùng kiểm synthetic CUDA làm kết quả fit nghiên cứu.

## Hợp đồng diễn giải

- Lựa chọn đúng inventory nguồn đã xác minh: PG/PY/PYH × seed20000/20001/20002 × graph_free/graph_package/empty_graph_package × bước0–119 = 3.240 snapshot. Loader kiểm tập đầy đủ, không trùng identity; không thêm seed thuận lợi.
- `p_correct_logged_query` là scalar p(correct) cho logged query hiện tại. Trace thiếu current item/question/timestamp, nên không gán p cho concept được preview hoặc chứng nhận độc lập full query identity. So sánh cạnh snapshot trong UI ghi rõ exact equality; bảng tổng hợp RQ1 giữ kết quả/tolerance của phân tích nguồn đã đóng.
- Mastery chỉ hiển thị native boolean từ danh sách `mastered` đã lưu; không hiển thị điểm estimator số như latent mastery probability. Ready membership và ranking lựa chọn là hai thông tin khác nhau.
- Chuỗi route là **concept preview theo thứ tự fixed-stream snapshots trước cập nhật trên bản sao policy**. Không phải served action, không phải replay câu hỏi đã phục vụ, không closed-loop personalization. Giao diện không đưa outcome/oracle labels hay vector mastery score ra API.
- RQ1 hiện hai phép so sánh với graph-free, mẫu số event pairs1.080 mỗi phép so sánh; M event = any concept crossing, khác mẫu số30.240 concept decisions. Full graph package có964 P đổi nhưng944/964 concept preview giữ; empty graph package có37 P đổi và0 M/ready/preview đổi. Đây là conditional cooccurrence, không nested funnel, causal mediation hoặc graph-edge-only effect.
- RQ2 là factorial synthetic **10 seed blocks21000–21009**, tách khỏi3 seed replay. Đơn vị tương tác edge×λ và outcome Elo giữ nguyên nguồn. PYH−PY có5seed dương/5seed âm; leave-one-seed-out mean không là CI. PG không mechanism exposure và interaction0 không chứng minh equivalence.
- Không có edge confidence/gate artifact cho replay này: UI ghi thiếu, không tạo confidence, gate values, fit metrics hoặc graph benefit giả. Không suy từ oracle simulator labels.

Được nói: “Có thể xem và đối chiếu các snapshot synthetic đã lưu; prediction thay đổi thường không kéo theo concept preview thay đổi trong pilot này.” Chưa được nói: “Demo chứng minh graph/CG-AKT giúp người học thật học tốt hơn”, “đây là action được phục vụ”, “p là xác suất đã biết concept”, hoặc “RQ3 đã được chứng minh”.

## HTTP, giới hạn tải và kiểm thử

Server chỉ bind127.0.0.1; không nhận host khác. Routes cố định `/`, `/assets/demo.css`, `/assets/demo.js`, `/favicon.ico` (204), `/api/catalog`, `/api/replay`. Replay query phải có đúng4 key đơn, enum inventory và integer canonical trong range; không arbitrary file/export API. Unknown/traversal paths bị từ chối. Host và Origin kiểm loopback; không CORS. GET/HEAD, các mutation methods bị405. CSP self-only, nosniff, no-store và no-referrer. Giao diện dùng textContent/safe DOM, không innerHTML từ metadata. Đây là local read-only viewer, chưa là kiểm thử xâm nhập hoặc dịch vụ multiuser production.

Manifest tối đa256KiB, selected JSON2MiB, compressed trace256KiB, expanded gzip16MiB, line64KiB, đúng3.240rows; JSON trùng key/NaN và duplicate/invalid identity bị từ chối. Path resolution không cho nguồn allowlist symlink thoát checkout. Không hỗ trợ upload, truy vấn dataset hoặc tải file tùy ý. Không thêm package.

Lệnh cuối: `.\.venv\Scripts\python.exe artifacts/akt/local-tests/parallel-demo-20261108-01/run_checks_trial04.py` (wrapper gọi pytest chỉ `tests/demo/test_viewer.py`, timeout60s, cache tắt, basetemp trong own artifacts). **53 pass, 0fail/error/skip, pytest1,92s**; source pre/post SHA giống nhau. Tests xác minh projection của toàn bộ3.240snapshot, missing/tampered input, gzip/file bounds, schema/JSON, strict HTTP routing/query/Host/Origin, HEAD/mutation, bind restriction, không trả trường oracle/mastery score/Junyi section. Không chạy Gate18/full suite/model/GPU.

Giữ các lượt trước và source snapshots:

| Lượt | Kết quả | Diễn giải |
|---|---|---|
| trial01 | 22pass/25fail/6error,3,81s | Sandbox chặn localhost connect WinError10013 và temp mặc định ngoài workspace; một assertion nhầm chữ Junyi trong limitation với dữ liệu Junyi. Không là model failure. |
| trial02 | 52pass/1fail,1,88s | Test kỳ vọng400 nhưng http.client tự gán Host của absolute URL thành foreign host, server từ chối403 đúng; sửa fixture Host loopback để kiểm nhánh absolute URL400. |
| trial03 | 53pass,1,84s | Bản trước chỉnh visual QA. |
| trial04 | 53pass,1,92s | Bản source cuối: sửa mobile min-width, favicon204, và lấy takeaway từ conditional table nguồn. |

Localhost tests dùng exact bounded process escalation sau khi sandbox chặn socket, không mở network ngoài loopback. Playwright purpose-built, không CUA/không cài browser: desktop1037/1366px và mobile390px; chọn full graph seed20001 PG bước11 khớp p0,388780/conceptHamSoBacHaiVaDoThi/12preview nodes; PYH seed20002 empty bước119 có120nodes, p0,679172 và API/DOM parity true. Mobile trước sửa body455px; cuối width390/body375 (15px scrollbar), không page overflow; bảng rộng cuộn bên trong container. Console cuối0error/0warning. Files tên `browser-final-mobile.json`/`mobile-final.png` thực tế là viewport1037px sau tạo tab mới; bằng chứng mobile cuối đúng390px là `browser-final-390.json`/`mobile-final-390.png`. Giữ tên lịch sử, không đổi nghĩa artifact. Ảnh đã đọc kiểm trực quan. Chưa chứng nhận WCAG, mọi browser hoặc mọi kích thước màn hình.

## Đóng gói

Bằng chứng nhỏ tại `research_tracking/runs/demo-readonly-engineering-20261108-01/`: source cuối, source trước trial01–04, log/JUnit cả failure, receipts, scripts tái kiểm, input snapshots/manifest, screenshot/DOM receipts và inventory SHA trước/sau copy. Dùng helper record_evidence_run/verify_evidence_bundle; không sửa bundle sau closure. Không copy .pt/Parquet/data lớn. Các snapshots historical không tự là entrypoint hiện hành. Runtime bounded QA đã đóng; không để service nền còn chạy. Parent duyệt, cập nhật chỉ mục/REPOSITORY_MAP và commit sau closure riêng.
