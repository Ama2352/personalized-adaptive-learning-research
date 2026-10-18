# Artifacts baseline BKT

`results/wsl_cpp/` chứa nguyên các output WSL/C++ đã hoàn thành: pilot/benchmark, 5-fold Development CV, smoke checkpoint, final Development refit và holdout Test evaluation. Không sửa các manifests, models, predictions hoặc checkpoints lịch sử.

`relocation_summary.json` là bản tóm tắt public-safe của lần di chuyển: đường dẫn tương đối cũ/mới, số file, tổng dung lượng và hash inventory. Bản `relocation_manifest.json` đầy đủ có hàng nghìn mục, hash từng file và đường dẫn máy cục bộ; bản gốc được giữ nguyên local, không đưa vào Git. `verified_after_move` có nghĩa là mọi file đã khớp path tương đối, kích thước và SHA-256 trước/sau khi di chuyển.

Các thư mục Windows `artifacts/bkt_baseline/` và dữ liệu gốc `dataset/` giữ nguyên chỗ cũ. Báo cáo kết quả đã đối chiếu trực tiếp từ các file JSON của ba run CV/refit/Test nằm trong `docs/bkt-baseline-results.md`.

Các file script phụ nằm bên trong `results/wsl_cpp/benchmark/` được giữ nguyên như một phần run archive. Một số script trong đó còn chứa đường dẫn cũ `.wsl/benchmark`; chúng không phải entrypoint hiện hành. Runner WSL hiện hành nằm ở `scripts/wsl2/`.
