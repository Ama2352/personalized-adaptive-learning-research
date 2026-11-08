# Cold fallback trước manual T4: contract nguồn, chưa implementation/provisioning

08/11/2026. Warm audit không chứng minh ROOT/venv sẽ còn sau CPU→T4. Chưa đổi hardware hoặc cài/provision gì trong note này. Bootstrap/installer mới cần review source/approval/budget riêng; không cộng vào validation warm30s hay tự dispatch.

## Những gì từ CPU-v3 thực sự reuse được

Source `fresh_install_verified_profile_v3.py` SHA578181... giữ nguyên. Reuse/copy có provenance: `digest`, `normalize`, bounded regular `read_owned`, `Stage` cooperative time/storage/log guards và owned-PG cleanup_once; strict `verify_effective_config` flat/nested; `select_root_metadata` top-level2parts+allRECORD origins; exact directURL/hash parser thuộc `parse_inputs`; CPU import/scalar audit. Giữ command `BASE -I -B -m pip --python TARGET install --require-hashes --no-deps --no-index --only-binary=:all: --no-cache-dir --no-compile ... --report ...` và exact44 report equality/pip-check/audit. Không chạy pip hoặc download trong source-prep.

**Không reuse old main/old descriptor PINS như fresh proof.** V3 hard-pin `venv.json` SHA `5dc1116b951942bb73e765cd180f3b99d9862295c359f02a714402d471e749be`, cfg SHA `0b85377496947675cd146fc9bcdab419ca9ab7eb4ce40d9a05df459330043366`, Python3.13.18/glibc2.39/basepip26.2.2 và reject GPU host. New source phải có explicit mode `GPU_HOST_CUDA_HIDDEN_INSTALL_EMPTY`, fresh descriptor SHA inputs, newattempt/output và user approval; originalguard không sửa. Algorithm parser reuse không nghĩa toàn `parse_inputs` hardcoded old PINS được gọi thẳng trên host mới.

## Packet offline phải chuẩn bị trước switch

1. Exact44 Linux lock **60dad3de...cc45a**, selected wheel report92a2.../resolver provenance; direct officialURLs/hashes giữ nguyên, không dùng Windows lock. Bytes có trong `gpu08.../received/resolution-attempt01/`. Actual new-target compatible tags phải kiểm **mọi44 wheel**, không chỉ Torch, trước install. IncompatibleABI/cp313t/aarch64/glibc hoặc basepip khác reviewed profile → STOP/review, không tự resolve/adopt config.
2. Source/controller/profile scripts+SHA và source manifest actual fixture mới. BaseZIPb670... vẫn chứa fixture cũ; nếu reuse thì giữ explicit delta lineage/161after inventory. Native upstream4files cần real pinned Git provenance để `verify_upstream` hoạt động; không giả `.git` từ filenames/hashes. Prepare/capture packet thật hoặc dùng separately approved bounded source checkout sau reset; không gọi source/worker ready khi phần này chưa có.
3. New actual startup preflight logic/optional reviewed facts manifest chỉ áp dụng nếu newhost bytes/linktarget/RECORD binding khớp lại. CPU metadata facts/ABI/b003/audit receipts là historical inputs, không chép thành fresh host output. PTH sau cold install có thể được ghim qua exact selected44 RECORD; unknownhook STOP trước normal import.

## Piece bootstrap nhỏ nhất cần source-prep riêng

Đề nghị file stdlib mới `gpu10_cold_bootstrap01.py`, **chưa viết trong batch warm**. Input: trustedROOT/newattempt/sourceSHA/explicit `CREATE_ISOLATED_EMPTY_VENV_ONLY` approval + reviewed profile packet. Inspect Linux/base ABI/root ownership/space first with no-site/no device queries. ROOT/venv đã partial hoặc existing → STOP, không delete/overwrite/repair. Khi thật sự absent và được approve, chỉ tạo ownedROOT/stage và `.venv` bằng base `-m venv --without-pip`; không pip/global installs.

Output phải là **fresh actual** `venv-descriptor.json`, cfg bytes+SHA, lexical target entry/base resolved binding, CPython/cachetag/SOABI/EXT_SUFFIX/GIL/glibc, basepip version/origin/effective config, distribution/spec emptiness và source/profile prepost hashes. Purelib chọn explicit scheme `venv` có tồn tại; không lặp Debian `posix_local` bug. No-site prefix `/usr` ghi đúng scope; normal-prefix probe chỉ sau reviewed startup gate (emptyvenv vẫn có system sitecustomize). Không fake sys.prefix hoặc copy oldvenv.json. Reap/cleanup và deadline/probe logs kể cả failure.

Bounded tag collector dùng actual target qua public `base pip --python TARGET debug --verbose`, không install targetpip; sanitizeenv/config, store tags digest+wheel coverage, strict parser/source review trước dispatch. Proposed bootstrap cap30s và tag probe≤15s là **hai bước có approval/budget rõ**, chưa actual timing/acceptance. Nếu thiếu actual startup/basepip/ABI facts thì descriptor chỉ là discovery pendingreview, không đủ điều kiện installer.

New hidden cold installer sau đó nhận actual descriptor/cfg/source/profile/tag proof SHA, chỉ emptyvenv và source-derived GPUhost explicit phase; giữ600s/20GiB/min30GiB cooperative guards, hashes/report/audit và zero explicit device queries. Audit startup/runtime/CUDA/context/auth/worker là các nghiệm thu tiếp theo, không auto phase. CUDA visible/runtime/2update/VRAM/resume chưa được chứng nhận bởi cold CPUimports.

**Trạng thái:** hiện warm source/mocktests đã có; cold bootstrap/target-tag/new-empty-installer source cần batch review riêng **trước manualhardware**. Không remote/network/install/provisioning/model/tests mới để viết note này; không khẳng định full T4 readiness.
