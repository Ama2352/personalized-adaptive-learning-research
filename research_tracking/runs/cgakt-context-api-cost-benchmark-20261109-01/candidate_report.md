# Chi phí vận hành API for_windows trên complete simulator TRAIN80

09/11/2026 — **operational CPU data-only benchmark, không model/epoch/GPU throughput**.

Đợt02 đã hoàn tất144calls ABBA và kiểm evidence parity, source/input stability, owned Job cleanup. Kết quả cho thấy bỏ full-cache JSON khỏi đường truy cập selected windows có hiệu quả trên **API và workload cụ thể này**. Nó không đo collate, neural forward/backward, optimizer, toàn epoch hoặc training end-to-end; không cho phép dự báo GPU cost hay lợi ích CG-AKT.

## Dữ liệu và phương pháp

Canonical `read_public_research_corpus` audit đủ ba simulator Development roles/DONE/public9files để xác minh provenance. Sau đó chỉ TRAIN80 được dùng để fit encoding dữ liệu và dựng context:48learners×210events=10080targets,144canonical windows,36groups×4windows. Không slice/relabel cohort; không dùng selection/calibration để fit/evaluate/select/tune model. Đây là corpus mô phỏng đã có, không Junyi/Holdout/final/oracle; không gọi teacher, solver hoặc neural model.

Hai nhánh dùng **cùng index, cùng thứ tự window groups và cùng nguồn**. ABBA cố định là full→fast→fast→full, mỗi pass đi đủ36groups. Full dùng `for_windows` default với full index audit; fast dùng process-local access seal, header/source guards và full selected-record/input hashes. Build/seal và parity checks ghi thời gian riêng; không loại iteration chậm, không yêu cầu nhanh hơn để pass. Source/runtime/input pins được kiểm trước/sau; mã producer raw và corpus không đổi.

## Kết quả đọc từ raw receipts

| Pass | API mode | Calls | Tổng thời gian gọi API (s) | Full-cache payload calls | Selected-record hashes |
|---|---|---:|---:|---:|---:|
|0|full|36|20,1733682|36|0|
|1|fast|36|1,0972125|0|144|
|2|fast|36|1,2281469|0|144|
|3|full|36|20,4438635|36|0|

Đây là bốn quan sát theo thứ tự trong một process, không bốn independent replications, CI hoặc benchmark nhiều máy. Các tổng trên chỉ gồm thời gian gọi API. Parity hashing, resource guards, journal fsync, imports, source/I/O và setup vẫn nằm trong whole-operation accounting; không cộng nhầm các pass sums thành end-to-end runtime.

Các stages đã lưu: canonical provenance reader0,5136367s; train80 encoding/context build23,0528367s; full attach/manifest seal1,4398383s; full final boundary audit0,5184612s. Observed worker peak RSS131141632bytes, minimum system available RAM4620050432bytes; đây là observed/cooperative guard, không chứng minh hard OS RAM quota hoặc mọi workload sẽ vừa512MiB.

Toàn144calls giữ cùng selected evidence hashes cho cùng group và cùng window IDs qua cả bốn pass. Source guards vẫn chạy, fast calls không gọi full serializer; full boundary audit cuối PASS. Owned receipt02: returncode0, cleanup accepted, active process count0, handle closed. Không Torch được load; không model fitted hoặc evaluation metric nào được tạo.

## Failure01 và accounting không reset

Attempt01 **REJECTED** sau khi đã audit public roles, dựng index10080targets/144windows và return first full API body. Journal gọi `event(...,seconds=seconds)` trong khi hàm tự tạo `seconds=elapsed()`, gây TypeError duplicate keyword. `completed_calls=1` nhưng `bench_calls=[]`; không có timing/speedup được nghiệm thu từ lượt này. Toàn source/config/log/Job receipt/result01 được giữ, không relabel là PASS.

Attempt02 chỉ sửa caller journal thành `call_seconds` và paths mới. Trước dispatch, ROOT chạy2stdlib AST regressions lấy đúng hàm event và actual callsite keyword schema của worker01/02: lỗi01 tái hiện,02ghi đúng row. Memory journal/fsync stub được ghi rõ; không import data/NumPy/Torch ở regression. Receipt regression lưu0,0825212s; ROOT quan sát terminal0,0937658s — hai ranh giới đo khác nhau.

ROOT quan sát terminal02 **78,6461785000s là charged controller**, đã gồm reservation5s cho regression; không phải pure wall và không cộng5s lần nữa. Outer final lưu78,6444866657s tại thời điểm tạo field, worker result lưu72,9724705219s. Cumulative-charge field raw lưu105,3503249000s, dưới ceiling206,7053s; các field được chụp tại các thời điểm khác nhau nên không ép equality bằng phép cộng số đã làm tròn. Prior failure được charge bảo thủ26,7053s, new stage180s gồm regression reserve; owned ceiling177s/cleanup3s, worker ceiling173s. Không reset budget hoặc automatic retry.

## Giới hạn và bước tiếp theo

Full default vẫn audit toàn cache; fast chỉ phát hiện nested tamper ở selected records trước dùng. Unselected tamper được phát hiện khi record được chọn hoặc full boundary. Không gọi lazy check là chứng thực chống hostile caller. O(W) lookup/manifest dict rebuild và source I/O vẫn còn; kết quả hiện tại cho phép đánh giá thực dụng ở workload đã đo, không chứng minh chúng luôn không đáng kể.

Đây là evidence chi phí API, không tự đóng toàn main-training readiness. Cần checkpoint/save/load, selected-only/external-freeze lifecycle, resource accounting và neural throughput riêng trước research fit. Không đổi recipe26/geometry/corpus/labels hoặc yêu cầu một kết quả khoa học thuận lợi để tối ưu này được chấp nhận.

## Nguồn có thể kiểm

- [Raw calls02](../runs/cgakt-context-api-cost-benchmark-20261109-01/attempt02__bench_calls.json), [worker result02](../runs/cgakt-context-api-cost-benchmark-20261109-01/attempt02__result.json), [outer acceptance02](../runs/cgakt-context-api-cost-benchmark-20261109-01/owned02__final.json), [ROOT readout](../runs/cgakt-context-api-cost-benchmark-20261109-01/root_readout02.json). Bundle là đích đóng gói do ROOT review/close riêng; candidate này không khẳng định archive đã đóng.
- Readout SHA `12e3cb08e0adb85e2d9ec6ebdadc7a1bc75d255da67e0d11c16dd214251455dc`; worker result02 `8547a2e3613d0bb4b5bd49e74b535b4e44b8208e09822ef2e8b46687885e7588`; outer02 `8a2e547e0cbd5a8b210176c983fe2bf11ea9d5fcdef33509119e93c1e2447819`.
- Regression SHA `0b51efd70692b1a16831664df854777fd7bb154ba05526cafa47bef88f65afd5`. Config02 `c5cc433a4368e9e13fea354b608172bdfc06684be7de8bb4f59f3d35d8265ba3` giữ41source/runtime pins,10public-input SHAs và16historical01source/raw SHAs; không copy whole `.venv`, corpus hoặc dependencies.
- Source context đã có trong [hotpath41outputs](../runs/cgakt-context-model-hotpath-engineering-20261109-01/README.md), manifest `38ce2196a3472a674dad94bef48f79b7a248f126729c85651d6dac8559dfd6ef`, commitf8b90fb. Source8bfe0dca…92bb029 được tham chiếu đúng, không copy lại toàn bundle41. Main neural correctness và benchmark API là các mức bằng chứng khác nhau.
