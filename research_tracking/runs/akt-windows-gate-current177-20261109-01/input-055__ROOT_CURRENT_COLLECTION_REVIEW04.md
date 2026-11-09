# ROOT review: chỉ kiểm kê test, chưa chạy test bodies

Ngày09/11/2026. Dựa trên quyền local engineering/synthetic checks người dùng đã cấp; không cấp quyền corpusfit, fullCV, Holdout, GPU, ZIP hoặc source export.

Đã đọc derivative04, metadata freeze helper, collection outer10 và các phần namespace/worker guards. Source production đã commit387b5bc/1f17f15, được đối chiếu raw Git146blobs; không thay sources sau snapshot177paths/81modules. Năm supportdocs21/22/23/26/allocation phải nguyên SHA. Các bản thảo/index mới không thuộc build population.

Cho phép đúng một lượt metadata freeze04 và collect-only10 sau đối chiếu SHA. Trần60giây toàn ba nhóm fresh processes; cần4GiB trống trước mỗi nhóm, floor1GiB, mỗi process≤3GiB RSS theo monitor. Owned helper0dc, namespace RECORD318537, exclusive output10, cleanup3giây giữ nguyên. Không retry hoặc tăng ngân sách khi lỗi.

Collector chỉ thu nodeIDs; không testbody/model/backward/Adam/solver/data/teacher/CUDA. Framework import có thể cấp tensor metadata, không tuyên bố0tensor toàn cục. Thu đủ nodeIDs/coverage và counters+source pre/post/Jobcleanup mới được accepted collection. Chưa có quyền full software Gate trong review này; cần review actual collection/counters/finite workload riêng. Không publish/currentpointer và không gán collected thànhPASS.

Đường chạy public main producer vẫn chưa được thực thi xuyên suốt,16mockPASS không thay thế integration; điều này không cản kiểm kê software tests nhưng phải giữ trong mọi readiness verdict. Browser đã đóng, không previewserver được mở trong lượt này.
