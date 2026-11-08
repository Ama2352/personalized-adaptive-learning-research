# Demo: xem quyết định closed-loop và giải thích ranking đã lưu — 08/11/2026

Demo E11 một phần đã có chế độ closed-loop trên cùng trang, dùng lại profile/seed/variant/timeline. Người xem có thể chuyển trajectory, đến first common-prefix break, xem M/R/C/B, served item và native B-score/key đã archive. Đây là trình xem artifact; không gọi policy, predictor, trainer hoặc simulator mới.

Nguồn khoa học là [bundle reconstruction đã đóng](../runs/rq1-closed-loop-reconstruction-20261108-02/README.md) và [báo cáo source-local](rq1_closed_loop_reconstruction_20261108.md). Manifest `c8bd8f387e5101fca641098257dd5a99d67d2f838cefc3b53b7d9d55248bcb16`. Demo ghim riêng sáu selected outputs của bundle; candidate post-hoc ban đầu vẫn giữ status lịch sử, được đọc cùng parent review PASS và closure receipt. Không tự đổi candidate thành bằng chứng confirmatory.

## Thay đổi và ranh giới

- Thêm `/api/closed-loop` với đúng bốn selector cố định `profile/seed/variant/step`; giữ API/default fixed-preview cũ.
- Thêm hai tài liệu cache allowlist `/evidence/closed-loop/report` và `/evidence/closed-loop/sources`. Không có endpoint đọc đường dẫn tùy ý, private files, raw learner predictions hoặc Holdout.
- Gzip closed-loop có giới hạn riêng: compressed 1 MiB, expanded 32 MiB, dòng 64 KiB, đúng 3.240 rows. Decoder lịch sử vẫn 16 MiB. Các JSON/CSV khác giữ giới hạn theo artifact, manifest/file SHA phải khớp trước khi phục vụ.
- Projection không xuất đáp án hiện tại, oracle/theta, raw state hoặc trace lời gọi đầy đủ. M là native boolean; B-score không là calibrated mastery probability. Chỉ hiển thị complete ranking keys ở first break đã archive; các bước khác ghi rõ visits/chapter không archive.
- Hiển thị đủ 18 comparisons: full có tám score-choice khi membership/tie context giữ và một membership change; empty có hai score-choice và bảy negative cases không tuple break. Đây là ba seed families cũ, new independent N = 0; không phải chín seed độc lập.
- Common-prefix chỉ giữ khi toàn bộ lịch sử actual served tuple/timestamp/outcome trước bước đó còn giống. Sau divergence không so paired ΔP/loss theo ordinal timestep. Các selected tuples và keys là dữ liệu đã lưu, không rerun ranking để tạo kết quả mới.
- Native selection xảy ra trước served-item P. Giải thích post-hoc là source-local CID, không qid/difficulty, calibrated mastery, causal benefit hoặc edge-only effect. Empty estimator vẫn có controller/environment G chung; package không đồng nghĩa riêng các cạnh.

## Kiểm tra thực tế

Hai trial dùng cùng năm source SHA, không sửa code giữa hai trial. Trial01: 83 cases, 47 pass/36 fail do mọi HTTP connection tương ứng bị `WinError 10013`; giữ nguyên log/XML. Trial02 chạy lại đúng process được cấp quyền localhost: **83 pass, 0 fail/error/skip**, pytest 7,01 s, controller 8,0692843 s. Tổng controller hai trial cộng reserve 1 s là **36,1590131 s ≤ 60 s**. Không optimizer/model/research replay.

Tests đối chiếu projection toàn bộ 3.240 metadata rows, 2.160 common-prefix flags và 18 proof/comparison cases; kiểm bảy negatives, schema/tamper/duplicate/decompression caps, fixed endpoint/query/security, nguồn SHA và safe DOM. Đây là kiểm phần mềm, không tăng cỡ mẫu nghiên cứu hoặc hoàn thành RQ.

Command trial02: `.venv\Scripts\python.exe -B -m pytest tests/demo/test_viewer.py -q -p no:cacheprovider --basetemp artifacts/akt/local-tests/parallel-demo-20261108-01/c14-t2/t --junitxml artifacts/akt/local-tests/parallel-demo-20261108-01/c14-t2/pytest.xml`. Receipt giữ argv tuyệt đối thực tế và hash trước/sau.

Playwright trên localhost, không cài browser/dependency:

| Trường hợp đã kiểm | Quan sát thực tế |
|---|---|
| PG/20000/full, jump first break | Bước 61; API↔DOM P và served tuple khớp; 28 concepts, route 62 entries, 10 ranking rows; đúng nhãn source-local/post-hoc |
| PG/20000/empty | Không break trong 120 bước; jump disabled; visits/chapter ghi không archive, không điền giả |
| PY/20001/full | Bước 27; membership change, không gắn nhãn score-only |
| Chuyển về fixed-preview | Panel closed-loop ẩn; heading và P logged-query cũ được khôi phục |
| Mobile | Viewport thực tế 390×844; scrollWidth 375, không page overflow |
| Tài liệu và console | Hai endpoint tài liệu HTTP 200; 0 error/0 warning trong phiên QA02 |

Đã đọc hai screenshots QA02. File có tên `ui02-desktop1366.png` **thực tế 1037×683**, không phải 1366; receipt DOM ghi kích thước thật. Mobile là 390×844. Không tuyên bố kiểm toàn bộ browser/viewport/accessibility. Phiên QA01 chạm đúng cap server 180 s trong handoff, gây `Failed to fetch` sau khi server tự đóng; giữ receipt/screenshot failure. QA02 dùng server mới cùng source, dừng chủ động sau 117,934358 s. Tab QA riêng và server riêng đều đã đóng; không dừng app/tab của người dùng.

## Bằng chứng và phần chưa có

[Bundle kỹ thuật demo](../runs/demo-closed-loop-engineering-20261108-01/README.md) giữ snapshots năm source/test, baseline trước thay đổi, cả hai trial/log/XML, nguồn các helper, receipts/ảnh QA và SHA trước/sau copy. Input khoa học đã committed được tham chiếu bằng path/SHA thay vì nhân đôi gzip lớn. Không copy pytest temp fixtures hoặc private MCP payload.

Demo vẫn là một phần E11: GAM-KT/Paper2 synthetic stored evidence, không live fitted AKT/CG-AKT/SAKT/GKT, không confidence edge giả, không cá nhân hóa người học thật. S04/S05, calibration/mastery adoption và hiệu quả học tập vẫn cần bằng chứng/phê duyệt riêng. Kiểm phần mềm này không hoàn thành RQ1/RQ2/RQ3.
