# GAM-KT Development benchmark

Mã nguồn runner: `src/knowledge_tracing/gam_kt/`. Đặc tả protocol, cách chạy và quy tắc fallback xem [`docs/gam-kt-integration.md`](../../docs/gam-kt-integration.md).

Các kết quả GAM-KT được ghi riêng ở `experiments/gam_kt/results/wsl_cpp/`; sidecar Development và cache ở `artifacts/gam_kt/`. Không ghi vào thư mục BKT hoặc RIVF. Runner giữ nguyên frozen user/fold assignments và không có bước holdout.
