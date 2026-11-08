# Chuẩn bị T4: actual discovery chỉ đọc trên CPU — 08/11/2026

**Actual discovery02 đã được xác minh: `WARM_CANDIDATE_REQUIRES_AUDIT`, chưa GPU ready và không là authorization.** Máy vẫn là CPU; không chọn hardware, import Torch, truy vấn GPU, cài package hoặc chạy model trong gói này. Đây là bằng chứng chuẩn bị môi trường, không kết quả RQ/baseline. Bundle `akt-t4-discovery-engineering-20261108-01` chưa đóng, chờ parent review.

Nguồn và raw receipts tại [`gpu09.../t4-discovery01`](../../artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/t4-discovery01/). Linux software Gate24 và CPU dummy worker đã có bundle194/commit `1c52043` riêng; discovery không chạy lại chúng, không sửa bundle đó hoặc CPU installer v3.

## Chuỗi kiểm và failure được giữ nguyên

| Evidence | Kết quả thực tế, phạm vi |
|---|---|
| ABI02 fresh | Host/target Linux CPython3.13.18, x86_64, glibc2.39, cachetagcpython-313, SOABIcpython-313-x86_64-linux-gnu, extension `.cpython-313-x86_64-linux-gnu.so`, GIL-disabled0. Raw SHA `84f2393ae6a45de1a868410eed25b3be413e1928f2bea5f469010d3e18431f4b`. Source01 ABI cell đã thêm nhưng chưa chạy không được dùng thay actual02. |
| Local trial01 | **Timeout60.043531s**, partial log, không có JUnit hoàn chỉnh; không suy counts từ dấu chấm. Source/test/profile snapshots được giữ. |
| Local trial02 | **40PASS/0failure/error/skip**, XML54.225s, controller57.7544649s. Reuse161file fixture; repeated target cases dùng source-byte adapter; warm-positive/source-change/missing/lock cases vẫn filesystem thật. Tổng controller **117.7979959s≤120**; không chạy operation/target child/model. |
| Actual CPU discovery01 | **FAILED retained**, launcher0.266762478s; result SHA `23bd580d91c1efd3cbd1d604760bbedd0ade519cc711f118b59b93ab2ebf1650`. Target stderr470byte xác nhận Debian default `posix_local` chọn sai `.venv/local/lib/python3.13/dist-packages`. Không gọi đây là package/venv failure. Inner cleanup receipt bị source01 làm mất, giữ null/unknown. |
| Narrow correction02 | Source01 giữ nguyên; source02 chỉ chọn explicit `scheme='venv'` và reject khi scheme thiếu. Không sửa venv/site/origin guard hoặc profile. Focused stdlib **OLD2FAIL→NEW2PASS**, controller **0.6605037s≤cap10s mới riêng**; không rerun40 hoặc reset ledger120s cũ. |
| Actual CPU discovery02 | **WARM candidate**, source **0.195042314s**, launcher **0.269272948s**, đều≤30s. RC0, **launcher và inner target cleanup đều accepted**;165source/lock hashes trước/sau khớp.0model imports/GPU queries/install. |

## Actual identity đã khớp

Profile raw SHA **`0944dc50b1840c35d6085e5faa888b3d3370849e59077ea68e9a2397009b8228`** bind materialization02/source161, bốn upstream files, selected44versions/14NVIDIA và actual Linux ABI02. Không dùng ABI Windows hoặc sửa profile để né failure01. Source02 SHA **`51c4b98053ba4eaac42b8c8be51ac29645c0b5fdcdf243b19d07c760a8a9db5f`**, actual result SHA **`b0032f9d556d0ca3655d4bafa6d010d30feca05e1d4d6c02ac8148757d8c4ec9`**.

Actual source snapshot gồm161kit files+bốn upstream files; lock đã nằm trong kit nên tổng165 sau dedup. Semantic map digest trước/sau **`77a84e5822b2febfa87c02c67ffdd618afd5ee46b68e2981483145f0f84a2888`**. Profile/source controller cũng có raw SHA trước/sau bằng nhau. Lock giữ `60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a`.

Target được chạy `-I -S -B`, CUDA visibility rỗng. **Actual no-site prefix `/usr` được ghi nguyên**, không giả thành venv prefix: CPython3.13 chưa xử lý venv prefix qua site startup ở chế độ này. Purelib explicit venv hiện tồn tại tại `.venv/lib/python3.13/site-packages`. Probe đọc44top-level distribution metadata/RECORD fingerprints và tám package entrypoint origin fingerprints bằng stdlib/PathFinder; không import package, không thực thi `.pth/sitecustomize`. Target pip không có origin. Không sửa native runtime origin validator để chấp nhận no-site snapshot thay runtime report.

Những fingerprints này có thể dùng làm **baseline trước hardware switch**, rồi đo lại thực tế sau switch. Hash RECORD file chỉ hash bản liệt kê, chưa kiểm mọi file RECORD trỏ tới hoặc mọi installed byte; tám entrypoint hashes không bao trùm cả package. Không suy metadata persistence là toàn bộ venv persistence hay driver/CUDA tương thích.

## Giới hạn và bước tiếp theo

1. Normal-startup prefix/site-hook audit, actual44 wheel target tags, full RECORD origins và CPU import audit còn thiếu trong discovery. Đây là các nghiệm thu riêng; trạng thái warm candidate không tự cài/repair hoặc cấp quyền chạy.
2. Sau người dùng tự chọn free T4 cần discovery mới trên host thực tế; nếu venv/source/ABI không còn khớp thì dừng hoặc cold setup có approval riêng. Không đổi CPU-only guard của installer v3 để đi tiếp. GPU-host installation/audit với CUDA hidden cần source/phase mới được review.
3. Fresh CUDA runtime/hardware/sm75/one-visible-device proof và public `cuda-smoke` có exact context/auth/budgets còn thiếu; actual CUDA resume, refit, image/Modal, chi phí và nghiên cứu ngoài phạm vi. Gate24 có thể là historical CPU software evidence nếu native source/build/lock reader vẫn khớp, không là new-host/CUDA PASS.
4. Cleanup accepted02 là kết quả hai group đã kiểm ở run02. Outer launcher và target có session/group riêng: nếu outerkill trước innerfinally có thể orphan target; chưa có global failure-cleanup/recovery proof. Không dùng wrapper này cho model/paid execution. Source pre/post hashes cũng không là atomic attestation chống concurrent A→B→A writer.

Requests dùng bounded compressed source/profile; response≤48.000byte, target stderr≤4096byte mới inline, không whole binary600k hoặc đổi WSS limits. Archive đề nghị chỉ giữ source/profile/receipts/logs nhỏ, loại private RPC, request/cell có base64 payload, fixture temp, wheel/venv và binary. Manifest/inventory SHA trước/sau phải được kiểm khi parent duyệt đóng; bản báo cáo không tự chứng nhận archive completed.
