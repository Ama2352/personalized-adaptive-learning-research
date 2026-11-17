# Parent environment và request metadata qua RPC

Root đã xác nhận preflight02 thực đạt runtime/upstream/source identity, chưa GPU. Bổ sung lần này xử lý parent process của Modal cần import validation/sink trước hoặc sau subprocess `.venv`.

Image khai báo PYTHONPATH gồm `/opt/kltn/src`, `/opt/kltn/scripts/akt` và `/opt/kltn/.venv/lib/python3.13/site-packages`. Đây là đường dẫn trong cloud image, không thay Python local/global. Parent preflight nhập CachedNumericBudget, Drive sink và google.auth, bắt buộc Torch chưa bị import trong parent. Runtime Torch/source Git vẫn kiểm trong child `.venv` CPU riêng. Root phải gọi lại actual preflight trên image mới, local tests chưa chứng minh native NumPy hoặc dependency resolution của parent cloud.

`create_app()` bổ sung key `put_request`. Function CPU1core/1024MiB/timeout120, không GPU/Secret. Gọi `put_request.remote(request_dict, 'requests/<run>-<stage>.json')` để truyền JSON nhỏ qua function arguments, tránh đường storage upload đang lỗi DNS trên host. Trả pin path/SHA/bytes sau Volume commit. API chỉ nhận request schema hợp lệ, metadata tối đa2MiB, đường POSIX dưới `requests/`, không traversal hoặc alias. File được flush/fsync và công bố atomic, cùng nội dung gọi lại trả cùng pin, nội dung khác bị từ chối. Không upload model/data bằng RPC này.

`TESTS08.txt` ghi31ca đạt trong2,60giây, gồm immutable/idempotent request, đường sai, metadata quá lớn, image PYTHONPATH và function không Secret/GPU. Không gọi cloud trong nhánh sửa. `MANIFEST04.json` ghim source/log mới, hồ sơ cũ giữ nguyên. Source wrapper/worker đã freeze để root tạo image và chạy lại preflight trước C0.
