# Preflight archive dừng trước copy

Lượt pack đầu thực tế exit1 tại assertion SHA của `source__reference_controller.py`;0copies, chưa tạo runbundle. Current controller đã đổi từ trial02 `8f4795e3e236c08a33f12bfd9c5047264fef82e7113493ade5c9e37cb35a6cfc` sang parent-owned `a955a076e41f5baf54e18dfe994d95503a9613824157e83a7a0062667a4024df`. Không là test/model failure.

Giải pháp: archive nguồn controller8f479 từ byte-exact snapshot có sẵn `trial02/3-reference_controller.py.before`, không lấy current bytes để dựng lại lịch sử. `pack_preflight01.py.before` giữ helper trước sửa. Không rerun/relabel39PASS hay khẳng định currentcontroller a955 đã được integrationtest này kiểm. Ghi chú này suy từ actual tool traceback, không giả thành raw stderr file đã được redirect tại thời điểm chạy.
