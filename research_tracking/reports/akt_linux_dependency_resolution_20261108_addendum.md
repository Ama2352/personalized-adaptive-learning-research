# Bổ sung phạm vi acceptance sau Linux dependency resolution — 08/11/2026

Bổ sung này làm rõ bước tiếp theo của [báo cáo đã đóng](akt_linux_dependency_resolution_20261108.md), mục 5.1. Không thay bytes báo cáo hoặc [bundle `akt-linux-dependency-resolution-20261108-01`](../runs/akt-linux-dependency-resolution-20261108-01/README.md), không ghi thêm kết quả thực thi.

**Wheelhouse lưu riêng là tùy chọn, không phải điều kiện bắt buộc trước isolated install.** Stage tiếp theo, nếu được cấp phép và budget riêng, có thể dùng trực tiếp 44 exact wheel URLs và hashes trong [candidate lock](../runs/akt-linux-dependency-resolution-20261108-01/candidate-linux-cuda.lock.txt) với `pip --require-hashes` để cài vào project venv cô lập, ghi install report rồi kiểm `pip check`, versions và origins. Cần ràng buộc toàn bộ selection theo lock, không fallback sang dependency chưa có hash, sdist/build hoặc Python global. Không suy riêng từ pip exit thành chứng nhận độc lập về wheel bytes đã giữ lại. Nếu cần retained wheelhouse và inventory SHA độc lập thì đó là một stage riêng, có dung lượng và acceptance riêng.

Lượt resolution hiện tại vẫn chỉ là candidate metadata closure: 44 packages, gồm 29 root pins, 14 NVIDIA packages và Triton; 0 installs, 0 GPU model steps, 0 Modal calls. Kiểm độc lập local xác nhận 14 raw files/512.166 bytes và 46 active dependency constraints. Chưa có installed-import/origin acceptance, wheelhouse-byte attestation, image digest, CUDA runtime/main-worker readiness hay kết quả nghiên cứu mới. Budget resolver 180 giây/256 MiB cooperative không cấp budget cho cài đặt hoặc tải toàn bộ wheels.

## Ràng buộc phiên bản và kiểm integrity

| Tệp đã đóng | SHA-256 |
|---|---|
| Bundle `-01/manifest.json` | `eae752b3c04516020d0671167853acd5a3d55fc35e57ef992c6b960f1eb2d0ed` |
| Canonical report và snapshot `-01/resolution_report.md` | `c490974f9e0c04921cdfaf9c1fc3f0e7143e2f5a462f302c58d9733bea5ec4be` |
| Candidate lock | `60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a` |
| Independent validation | `c911eb8770c01e94c2e5759c9ccf96202618367cbc604e1e545faaa59f02828b` |

Kiểm cuối bằng `verify_evidence_bundle` xác nhận **37 outputs**; hậu kiểm danh sách thành viên không có tệp ngoài manifest, và **29 cặp bản sao** khớp SHA trước/sau với nguồn. Kiểm integrity không đồng nhất với nghiệm thu installed runtime hoặc hiệu lực khoa học. Bổ sung này chỉ là clarification của acceptance tương lai, không thay candidate profile, proposal cũ hoặc allocation tài chính; không thực hiện network/remote/install/model/GPU/Git write.
