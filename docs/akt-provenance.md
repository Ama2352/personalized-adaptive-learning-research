# Provenance AKT graph-free

## Nguồn đã kiểm tra

- Repository: https://github.com/arghosh/AKT.git
- Commit: `01b7e8d7d7c862cabc9467108e3e7f2555653a88`; Git tree: `904863502337ef2eefd1769d14836b62e3c3804a`.
- Đường dẫn checkout: `artifacts/akt/dependencies/upstream/`; checkout detached và sạch tại thời điểm kiểm tra.
- License: MIT, copyright Aritra Ghosh 2020; notice và license đầy đủ được giữ trong checkout.
- SHA-256 `akt.py`: `be2788c20cac602e86ef3a51e5294b37dd7b200f818be4e173dbd69069a3ec6d`.
- SHA-256 `README.md`: `df8eea9919dcdb343f3a841540af18e2039b8b0c33af449ca9c752d11f56ee8b`.
- SHA-256 `LICENSE`: `891133edce0d8693f5b916d4257ce70b71a02aa110cb02cc5d47326544ea4522`.

Commit này chứa bản sửa softmax được ghi trong README upstream. Source được giữ nguyên; tương thích import được xác nhận tại Gate 1, còn numerical parity và hành vi kiến trúc tổng hợp được kiểm tại Gate 2. Không sử dụng Holdout hay huấn luyện Junyi khi kiểm tra provenance.

## Runtime candidate — chưa xác nhận Gate 1

Windows CPython 3.13.5 64-bit; `.venv` riêng, pip 25.1.1. Chỉ mục CPU chính thức có wheel `torch-2.7.1+cpu-cp313-cp313-win_amd64.whl`, SHA-256 `b66f77f6f67317344ee083aa7ac4751a14395fcb38060d564bf513978d267153`. Các candidate NumPy, pandas, DuckDB, scikit-learn, psutil và pytest được pin theo phiên bản đã có ở môi trường project cũ; khả dụng trong môi trường mới còn chờ resolver/import. Chưa xem các pin này là tương thích chỉ từ wheel metadata.

Nguồn wheel: https://download.pytorch.org/whl/cpu/torch/. README upstream mô tả PyTorch 1.2.0 trên Linux; tổ hợp Windows/Python/Torch mới cần kiểm thực tế và parity. Chưa thay đổi source upstream.

## Gate 1: import đã xác minh

- Runtime: `D:/Dev/KLTN/.venv/Scripts/python.exe`, Python 3.13.5, PyTorch 2.7.1+cpu và NumPy 2.5.4; module origins của Torch/NumPy nằm trong `.venv`.
- `requirements-akt.lock.txt` SHA-256: `3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a`; pip 25.1.1 đã cài 29 wheel từ lock bằng `--require-hashes`.
- `pip check`: `No broken requirements found.` Import class AKT từ checkout pinned trên CPU thành công; source checkout vẫn sạch và hashes khớp. Evidence: `artifacts/akt/preflight/runtime-v2.json`.
- `torch.cuda.is_available()` trả false với bản Torch CPU; kết quả này không xác định máy có GPU vật lý hay không. Forward/backward và parity đã được kiểm trên fixture tổng hợp; chưa chạy thực nghiệm Junyi.
- Review độc lập đã rà kiểm soát project root, vùng output, module origins, wheel hosts, direct requirements và source content. Các test tổng hợp provenance/runtime hiện tại: 18 passed.

## Parity tổng hợp ban đầu

Với cấu hình nhỏ CPU FP32, dropout=0 và cùng state_dict, wrapper khớp source gốc về logits, xác suất, summed loss, số targets và gradients tại tolerance `1e-6` (`tests/akt/test_upstream_parity.py`: 4 passed). Causality, windowing, OOV, coverage và metrics cũng đã được kiểm riêng bằng synthetic tests; chưa chạy benchmark hay đánh giá trên Junyi.

Paper: A. Ghosh, N. Heffernan, A. S. Lan, “Context-Aware Attentive Knowledge Tracing”, KDD 2020, DOI 10.1145/3394486.3403282.
