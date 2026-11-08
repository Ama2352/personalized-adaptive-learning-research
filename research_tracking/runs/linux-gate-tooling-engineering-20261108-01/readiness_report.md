# AKT: tooling chọn Linux lock và bỏ phụ thuộc target pip — 08/11/2026

**118 targeted tests PASS trên Windows CPU; chưa actual Linux Gate hoặc GPU worker.** Bản sửa chỉ chạm4files tooling/tests: runtime helper dùng public `packaging` đã pin; Gate2 publisher nhận lock tường minh, giữ nguyên default Windows và các guard nguồn/ngân sách. Không thêm pip vào target, dependency, model, hyperparameters, dữ liệu hoặc protocol nghiên cứu.

## Vấn đề đã xác minh từ nguồn

[Linux candidate44packages](akt_linux_dependency_resolution_20261108.md) có standalone `packaging`, không có pip trong isolated target `--without-pip`. Trước sửa, `check_runtime.write_lock_from_report` và hai fixtures import `pip._vendor.packaging`, nên full CPU suite trong target này sẽ thiếu tooling dù install44 thành công. Source inspection này không đồng nghĩa full suite Linux đã được chạy và thất bại.

Gate21 Windows dùng lock SHA`3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a`; Linux candidate là`60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a`. Context truyền cùng selected lock cho runtime và Gate2, nhưng producer trước sửa khóa cứng root `requirements-akt.lock.txt`. Không thể rehash/đổi nhãn Gate21 thành nghiệm thu Linux.

**Không có lỗi grammar giữa hai hashlocks:** Windows lock thực tế cũng `name @ URL --hash=sha256:...`. `inspect_runtime` chỉ hash lock và ghi runtime versions/origins; không parse `==` hay kiểm toàn44installed distributions. Kiểm installation/versions/`pip check`/origins vẫn phải có bằng chứng riêng. [Draft dependency order và entrypoints](../../artifacts/akt/colab/gpu08-linux-20261108-01/NEXT_LINUX_WORKER_GATE_DRAFT.md) ghi call sites trước sửa và addendum sau local freeze.

## Bản sửa và ranh giới

| File | Thay đổi đã kiểm |
|---|---|
| [check_runtime.py](../../scripts/akt/check_runtime.py) | Ba imports trong `write_lock_from_report` chuyển sang public `packaging.requirements/tags/utils`; giữ lazy import, wheel identity/platform/SHA và requirement parsing. Runtime inspection schema2/origin/source/device checks giữ nguyên. |
| [test_runtime.py](../../tests/akt/test_runtime.py) | Hai fixtures mock public tags; thêm positive lock-writing test chặn mọi import `pip` để mô phỏng target không có pip. Public packaging local là26.3, đúng pin44profile. |
| [refresh_gate2.py](../../scripts/akt/refresh_gate2.py) | `refresh(..., lock_file=None)` và `--lock-file`. Chọn relative/absolute file hiện hữu trong trusted ROOT: `artifacts/akt/...` hoặc root `requirements-akt*.txt`; reject outside/protected/private/directory/missing/directsymlink/junction. Default root Windows path không đổi. Selected lock được hash trước/sau, path+SHA vào payload, và **chính path đó** đi vào final reader. |
| [test_gate2_refresh.py](../../tests/akt/test_gate2_refresh.py) | Relative/absolute Linux lock, default fixture/provenance,6invalid-path cases trước child/pointer write và selected-lock drift sau fake successful child đều có positive/negative controls. Existing elapsed/strictJSON/rehash guards vẫn chạy. |

Selector kiểm path/existence/byte identity, **không** tuyên bố một text file bất kỳ là lock44packages đã kiểm. Field `lock_file` là provenance bổ sung; schema1 reader vẫn so actual selected lock SHA, không thay hash bằng tin string path. Không nới source/upstream checks, interpreter guard, suite scope, status/counts, elapsed1..600/default300 hoặc threadenv2. Không sửa authorization/context/config/model/default lock hay Gate reports/pointers trong batch này.

Remote `resolution-attempt01/candidate-linux-cuda.lock.txt` hiện ngoài allowlist. Bước tương lai cần copy độc quyền, byte-exact có inventory SHA trước/sau sang, ví dụ, `artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt`; giữ source cũ và SHA60dad… Không move/rename hoặc dùng lock Windows âm thầm. Draft chứa lệnh mẫu chưa chạy; chưa materialize canonical remote copy ở batch local này.

## Red/green thực tế và nguồn freeze

| Lượt | Kết quả | Thời gian controller | Bằng chứng |
|---|---|---:|---|
| [01 trước sửa](../../artifacts/akt/local-tests/linux-gate-tooling-trial-20261108-01/run.json) | 118tests:107PASS/11FAIL,0error/skip |14.835028s| Log/XML và4physical source snapshots;11failures thuộc các khả năng mới còn thiếu, không fake red. |
| [02 sau sửa](../../artifacts/akt/local-tests/linux-gate-tooling-trial-20261108-02/run.json) |118PASS/0fail/error/skip; JUnit13.088s|15.195849s| Before/after4source SHA khớp; receipt SHA`98cbeba165885b2085b2b32e791aadd0d2b243c3175fcd0f5ec89f3b6b34452b`. |

Tổng hai controllers **30.030877s<120s**,0optimizer/model fit. Chỉ chạy `tests/akt/test_runtime.py` và `tests/akt/test_gate2_refresh.py` bằng project `.venv`, CUDA hidden, OMP/MKL/OpenBLAS2, timeout60s/lượt, cumulative120s. Test native runtime import dùng actual local CPU Torch/upstream nhưng không tạo NN training; fixtures platform/origin còn lại có mock như đã ghi trong source. Gate publisher tests chỉ chạy fake child/temporary fake project, không phát hành Gate thật; “protected paths” của fixtures nằm dưới pytest temporary root, không chạm dataset repository.

Một test chặn pip imports là bằng chứng hành vi local khi pip bị ẩn, chưa là actual Linux installed-runtime proof. Không chạy full `tests/akt tests/shared_kt` trong batch targeted. Hai peer reviewers chỉ đọc4source/tests/receipts, không execute; cả hai scoped PASS và không phát hiện blocker còn lại. Giữ nguyên source/tests sau PASS.

| Source cuối | SHA-256 |
|---|---|
| `scripts/akt/check_runtime.py` |`4f5be1c58db40cd8875865275bb50f0b8171dc781615d4ce9f862ca598c1f795`|
| `scripts/akt/refresh_gate2.py` |`ccf192416472b6a1cda72db5350e9aaae99ca4f8a05c37787298745a8b2e6597`|
| `tests/akt/test_runtime.py` |`db07ee460182dc846a714c501343f755e7a01a15785263074119e5441bf0a113`|
| `tests/akt/test_gate2_refresh.py` |`778821106fb803a2988653785d22328d6dfc7729dbb1f044f7b1aae55b9888ea`|

[So source với Gate21](../../artifacts/akt/local-tests/linux-gate-tooling-trial-20261108-02/source_vs_gate21.json) xác minh cả4SHA đã đổi; report Gate21 gốc vẫn SHA`b74f4b96fe6a288f380b3ec69cfba2c01f95c089a8f8d98cdadc0aeb5f8d9c8e`. Nó là historical accepted757PASS tại source cũ, không chứng nhận source sau tooling. Parent chạy Gate22 Windows riêng sau freeze; verdict/output của lượt đó chưa nằm trong nghiệm thu targeted này. Không gọi code merge hoặc fullGate đang chạy là PASS trước receipts.

## Còn thiếu trước GPU09

Freeze kit mới, preserve notebook transforms/source inventory, pinned upstream clean checkout và chosen Linux lock byte-exact; actual isolated installation/ABI/import/origins proof; actual Linux **full CPU** Gate `tests/akt tests/shared_kt` trên đúng source/lock, không reuse notebook exclusions hoặc Windows Gate. Timeoutmax600 không bảo đảm Colab đủ nhanh; phải chốt budget trước, giữ failure và không tự tăng cap/retry. Sau đó mới context/authorization/public bounded CPU worker, rồi CUDA runtime report/phase/VRAM/recovery theo allocation riêng.

Bundle engineering giữ source pre/post, red/green log/XML/receipts, draft/report và lock text snapshots; không `.pt`, Parquet, install payloads, raw data hoặc fullGate results mới. Không remote/network/install/GPU/Modal/Git/root tracking writes từ batch này. S04/S05, scientific trainer/CG variants và RQs không được chấp thuận bằng tooling PASS.
