# Các lần thử collector và portability audit

collector-01:2failed8passed3errors do Windows paths, source snapshot cùng hash. collector-02:14pass sau canonical paths. collector-runner-03:34pass trước collator test. Các trial logs này không có source inventory toàn bộ suite ở thời điểm chạy; không suy exact replay mọi phiên bản test. Failed integration naming-collision có bundle cpu-sim-collector-20261107-01 riêng.

collector-domain-audit-01.json xác nhận full notebook hash khác khi strip outputs dù cell sources giống nhau, khiến domainv1 khác. collector-v1-before-domain-fix.py giữ code trước semantic-domain fix. Đây là lỗi compatibility mới được phát hiện trước paid run; không sửa artifacts/results Paper2. Mỗi file sao nguyên bytes và kiểm SHA.
