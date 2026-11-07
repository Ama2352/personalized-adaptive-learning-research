# Notebook Colab một file cho VS Code — 07/11/2026

User yêu cầu chuẩn bị đúng notebook để kết nối. Giữ file notebooks/akt_colab_synthetic.ipynb,
nhúng nguyên ZIPv11 137files/339864bytes với SHA cố định. Không upload/download browser,
không cài global; setup chỉ dùng remote ROOT/.venv. Bản cũ giữ nguyên trong bundle trước.

20localchecks đạt: AST7codecells, actual137file extraction/hash, traversal/source-tamper/
extra/missing file guards, stale-workspace guard, setup timeout/venv-only bằng mocks,
CPU acceptance bằng mockJUnit, và actualfailureZIPexport/từngfileSHA/no-overwrite.
GPU CONNECTED_GPU trong log chỉ là MOCK GPU giả lập (MOCK_GPU), không kết quả remote.
Run đầu harness thất bại vì xét chuỗi google.colab trong comment; sửa ASTimportcheck,
không phải lỗi kernel/GPU; giữ v1source/log. Notebook chưa actualVSCode/Colab/CUDA.

Gate2 source407 vẫnvalid vì notebook/docs nằm ngoài source gate; không rerun toàn suite.
Không realdata/optimizerstep/Modal/runtime allocation hoặc credits. Không là RQbenefit.
Mở docs/akt-colab-synthetic-runbook.md, kết nối kernel, chạy cell01 rồi RunAll khi GPU sẵn;
cellcuối xuất ZIP+SHA kể cảfailures, tải quaColabContents rồi RemoveServer.
