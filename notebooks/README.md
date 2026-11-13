# Notebook nghiên cứu

## 13/11 — validation theo batch

[Hồ sơ](../research_tracking/runs/junyi-validation-batch-20261113-01/README.md) giữ 126 ca Linux đạt, hai phép kiểm T4, log và figure. Trên 12.800 target tổng hợp có tín hiệu đồ thị, A0 tăng tốc 3,88 lần, A1 2,01 lần. Chưa kiểm lại toàn selection bằng checkpoint A0. Không train epoch, không dùng Modal.

## 13/11 — kiểm Junyi trước các biến thể AKT

[Hồ sơ kiểm](../research_tracking/runs/junyi-comparison-preflight-20261113-01/README.md) có audit split/vocabulary, hợp đồng so sánh và kết quả T4 A0/A1 batch128 cùng checkpoint đã tải về D. [Notebook T4](akt_colab_junyi_comparison.ipynb) dùng gói nguồn03 và venv trong dự án. A2/A3 Junyi và ràng buộc entrypoint còn cần hoàn thiện trước training chính.


## Kiểm nguồn và dữ liệu Main trên Colab CPU

[akt_colab_main_data_preflight.ipynb](akt_colab_main_data_preflight.ipynb) dùng runtime CPU để kiểm giải nén nguồn và đọc hai corpus mô phỏng công khai bằng public reader. Notebook tạo `.venv` không có pip trong thư mục dự án, kiểm SHA trước khi đọc và xuất receipt cùng logs nhỏ. Không cần cài package cho bước này.

Gói đầu vào là `artifacts/akt/colab/akt-main-source-data-20261110-01.zip`. SHA-256 cố định trong notebook là `1eb5b613950cfc26d05f2790534ba42ece5c078ca95a9a5f91a0e6a1adbd0afc`. Gói có hai corpus.

| Corpus | Train | Selection | Calibration |
|---|---|---|---|
| Development lifecycle60 | 48 người mô phỏng · 10080 targets | 6 · 1260 | 6 · 1260 |
| Engineering10×84 | 8 người mô phỏng · 672 targets | 1 · 84 | 1 · 84 |

Cold reader đã đọc đủ hai corpus từ gói giải nén tại vị trí mới trên Windows. Bốn ô mã của notebook được kiểm cú pháp và generator tái tạo đúng byte. Các bước này chưa xác nhận notebook đã chạy trên Colab/Linux, tạo `.venv` thành công ở đó, runtime Torch, Git provenance, CUDA hoặc training. Receipt của lần chạy trên máy đích cần được lưu và nghiệm thu riêng.

[Bundle kỹ thuật](../research_tracking/runs/akt-main-source-data-preflight-20261110-01/README.md) giữ generator, metadata, notebook và logs kiểm Windows. ZIP và thành viên dữ liệu được tham chiếu bằng SHA, giữ tại vị trí pipeline ban đầu. Gói không chứa oracle, model/checkpoint, quyền huấn luyện, runtime Gate hoặc Method24 artifact lớn.
