# Nguồn gốc và bản vá CAHLR/pyBKT

## Bản upstream

- Dự án: [CAHLR/pyBKT](https://github.com/CAHLR/pyBKT), phiên bản package `1.4.3`.
- Remote: `https://github.com/CAHLR/pyBKT.git`.
- HEAD tại thời điểm đóng gói: `cc1682e6e65241d5aaa7a286a01c4b76cd0da167` (`master`, khớp `origin/master`).
- Checkout là shallow (`.git/shallow` chỉ chứa HEAD), có một commit/nhánh, không có tag, commit local chưa đẩy, submodule hay LFS metadata. Vì vậy lịch sử upstream trước commit này vốn không có trong checkout local.
- Trước refactor: 3 file tracked modified, 2 test untracked; không có staged change. Các file build và `pyBKT.egg-info` bị ignore.

## Thay đổi local được giữ

| Tệp | Thay đổi | SHA-256 |
|---|---|---|
| `source-py/pyBKT/fit/EM_fit.py` | Dùng `.item()` để chuyển likelihood 1×1 thành scalar Python tương thích NumPy 2; không đổi EM. | `A18E6FCD293CCAF8E8C33A9CFA298291212FEB86D1F16323864427333447A271` |
| `source-cpp/pyBKT/fit/EM_fit.py` | Mặc định `tol=0.005` theo thí nghiệm và dừng an toàn nếu likelihood không hữu hạn. | `3FF8D17865D33A7BE96DC357032883D5C3F62E2C4B1440A645CD4D609D07AC35` |
| `source-cpp/pyBKT/fit/E_step.cpp` | Trả `total_loglike` qua `PyFloat_FromDouble`, kiểm tra lỗi và quản lý reference khi lỗi. | `A9D5E9D8ED77B834C77B129849EE707FDF6BA7E181CAABE08F9885A3E77723B2` |
| `source-cpp/pyBKT/test/test_e_step_likelihood.py` | Test likelihood âm/dương có phần thập phân qua binding C++. | `64281C28B579BA6CCD2B4E181B4D1E30433117E82227077D71A1171CC148BAE9` |
| `source-cpp/pyBKT/test/test_em_fit_guards.py` | Test tol mặc định và guard likelihood không hữu hạn. | `BF6DEBF4BE6626799C7327E3DA48A820212AD6BAF843EA95D22B46131BC6E824` |

Unified diff cho ba file tracked nằm tại [`pybkt-local-changes.patch`](pybkt-local-changes.patch), SHA-256 `2A921859147EB9EB3A18540283210A150E9925BE49B1A24164D450B9E1411CC2`. Hai test untracked được bảo toàn nguyên dạng trong vendor và được liệt kê ở trên.

## Backup và giới hạn khôi phục

Bản backup độc lập trước refactor được giữ ngoài repository. Inventory ghi 1.808 file / 16.327.823 byte cùng SHA-256; hash source và backup đã được đối chiếu. Git object store của bản backup đã qua `git fsck --full`. Bản `.git` theo trạng thái local (gồm shallow marker, refs, config, index và pack) vẫn nằm trong backup, không nằm trong repo public. Đường dẫn máy cục bộ được lược khỏi tài liệu này.

Trong working tree mới, `third_party/pyBKT/` là source vendored thông thường, không chứa `.git`. Do checkout nguồn chỉ shallow một commit, không khẳng định đã lưu lịch sử upstream trước commit này. Muốn truy cập lịch sử đầy đủ sau này cần fetch lại upstream; bản backup giữ nguyên checkout đã có để khôi phục chính xác.

## Cài đặt

`requirements.txt` tham chiếu `./third_party/pyBKT`. Trước refactor, Windows `venv/` có pyBKT 1.4.3 dạng cài đặt thường (không editable); metadata `direct_url.json` trong môi trường cũ ghi source ở checkout trước khi tái cấu trúc, còn module runtime được nạp từ `site-packages`. Sau khi chuyển, import vẫn từ `site-packages` và file `EM_fit.py` đã cài có SHA-256 giống source Python vendored. Không có `.pth`/`.egg-link` editable trỏ về checkout cũ; `direct_url.json` là metadata nguồn cài đặt cũ, không tham gia resolution của import. Metadata này được giữ nguyên để tránh rebuild/cài lại pyBKT trên Windows và không được đưa vào repo.

Windows không có extension C++ trong package đã cài, như trước refactor; pipeline nặng dùng extension Linux riêng trong WSL. WSL import-only smoke xác nhận `.so` được nạp từ môi trường Python riêng của distro; hash của E-step và predictor bằng đúng hash trong manifest CV, và source patch tại `third_party/pyBKT` khớp các hash frozen. Không rebuild hay nâng cấp dependency trong bước cấu trúc.
