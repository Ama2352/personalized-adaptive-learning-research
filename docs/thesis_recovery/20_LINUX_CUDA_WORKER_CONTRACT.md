# Hợp đồng worker Linux/CUDA và thứ tự nghiệm thu

Ngày07/11/2026. Đây là thiết kế kỹ thuật và acceptance map, **không cấp quyền chạy dữ liệu thật, thay phương pháp nghiên cứu hoặc dùng Modal**. Kết quả CUDA hiện có thuộc source kitv12, không tự xác nhận các thay đổi worker sau đó.

## Hai lớp cần tách

1. **Runtime và pipeline:** interpreter/venv, source/lock identity, loader, splits, validation, checkpoint/export/resume và giới hạn tài nguyên. Có thể phát triển, kiểm negative controls và fixtures CPU local ngay.
2. **Protocol nghiên cứu và allocation:** corpus Junyi/Grade10, model variants, selection/refit, mastery/calibration và ngân sách từng run. S04/S05 cùng các execution gates hiện hành không được suy ra từ test kỹ thuật.

## Runtime contract thực hiện trong batch này

- Executable phải là entrypoint `.venv/Scripts/python.exe` trên Windows hoặc `.venv/bin/python` trên Linux; prefix đúng project venv. Linux executable có thể là symlink đến base interpreter, nên không dùng resolved target của executable để đánh đồng với việc chạy base Python. Chỉ prefix/path identity không đủ chứng minh package origins.
- Torch và NumPy vẫn phải có origin trong isolated venv. **Colab `--system-site-packages` không được nhận là runtime chính thức** chỉ vì các probe v12 đã chạy; không thêm fallback bỏ origin check.
- Runtime report mới phải bind schema/platform/project root/executable/prefix/source/lock. Linux cần report mới; báo cáo Windows hợp lệ giữ tương thích, không chuyển report Windows sang Linux.
- `inspect_runtime` nhận project root/lock cụ thể để tạo report đúng runtime; không tự dùng lock Windows CPU cho image Linux CUDA. Preflight của watchdog vẫn nhẹ, không import Torch chỉ để xác minh JSON.
- Negative controls phải chặn sai interpreter/prefix, report cũ trên Linux, schema sai, source/lock mismatch và package origin ngoài venv. Mock platform phải cục bộ, không đổi `os.name` toàn tiến trình pytest.

File runtime report chỉ là bằng chứng được tạo từ check và hash, không là chữ ký hoặc quyền chạy. Authorization vẫn bind config, nguồn, data/split manifests và caps; Gate PASS không tự tạo approval.

## Synthetic main-worker acceptance

Fixture mới phải đi qua loader Parquet, learner-disjoint inner split, cohort cap và chronological windows thật của worker. Chỉ external source/runtime/Gate/RAM fixtures được inject trong test và phải ghi rõ. Không sửa hoặc đọc dataset/protected artifacts thật. Các bước authorization/caps/model/optimizer/validation/checkpoint reload/export vẫn chạy code thật.

Nghiệm thu gồm: số learner/target expected trước chạy; identity/chronology/OOV coverage sau export; best-checkpoint evidence; output hashes và một negative control đổi assignments identity bị chặn trước loader. Smoke chỉ có selection/validation/export; không gắn nhãn refit nếu chưa chạy flow refit. Tests CLI/recovery/refit có sẵn được đối chiếu riêng, không ghép thành một end-to-end run chưa hề thực hiện.

Pass CPU fixture chứng minh pipeline trên CPU trong phạm vi fixture, chưa chứng minh actual Linux hoặc CUDA worker. CUDA probe một batch trước đó không thay phép kiểm này.

## Công việc kế tiếp, chưa tự cho phép execution

| Task | Sản phẩm cần có | Điều kiện trước chạy |
|---|---|---|
| GPU06a | Runtime schema/platform/lock guard và negative tests | Local CPU; không cloud |
| GPU06b | Synthetic Parquet main-worker lifecycle và artifacts | Local CPU; existing smoke caps |
| GPU07 | Explicit bounded GPU phase/config/authorization và VRAM/watchdog contract | Design và cap được review; không đổi CPU smoke/pilot hiện hành |
| GPU08 | Linux CUDA environment với wheel hashes/install report/image digest | Không dùng freeze thay hash lock; chỉ chuẩn bị offline trước |
| GPU09 | Actual Linux/CUDA main-worker synthetic lifecycle | Runtime và phase contracts đạt; free Colab nếu phù hợp, không tự dùng Modal |
| GPU10 | Benchmark đại diện train/validation/export/checkpoint/inference | Có warmup, target/length distribution, fixed workload/time caps và artifacts; không dùng400/0,916 để dự báo |
| GPU11 | Modal image/Volume durability và bounded allocation | Exact run spec, readback khả dụng, single GPU/container, retry0, budget reserve và human approval |

Chưa có GPU07 thì **không** đổi `device=cpu` thành `cuda` trong phase cũ hoặc gọi internal worker để né authorization. Chưa có GPU08 thì không gọi venv kế thừa Colab là môi trường training tái lập. Bảng này là dependency map; chưa tạo các execution approvals hoặc kết quả.

## Artifact và thất bại

Giữ source/input hashes, command/log/JUnit và trial lỗi quan trọng trong run bundle mới; checkpoints/predictions lớn giữ ở `experiments/akt/results/<run-id>/`. Không sửa kitv12, CUDA artifacts hoặc manifests đã đóng. Mỗi source change làm Gate2 hiện tại cần refresh; bản Gate cũ vẫn là historical evidence. Linux-only thực thi không được tuyên bố từ platform mocks trên Windows.

Nếu thiếu wheel provenance, throughput hoặc GPU phase thì ghi blocker cụ thể và tiếp tục phần local độc lập. Không nới guard, thêm skips để qua gate, tự approve budget, truy cập Holdout hoặc chọn hyperparameters bằng kết quả Test.

## Kết quả batch và phản biện khi tích hợp

Runtime targeted63cases đạt; worker Parquet2cases đạt. Gate16 có512pass/1failure: native DuckDB không mở được pending-file path264ký tự trong deep pytest directory. Contrast cùng môi trường cho path227,220và87ký tự đềuPASS. Chỉ rút gọn fixture xuống `tmp_path_factory.mktemp('wk')/'p'`, vẫn trong Gate basetemp; không đổi exporter, registry/Windows settings, assertion hoặc caps. Deep-UUID targeted2cases đạt trước Gate17. **Gate17 đạt513pass/0fail/error/skip,269,98s**, reportSHA`4501b75cad421b75987b959cf843b3edfa57334bb4e449db1aa0fbcf09198baa`; Gate16failure không bị đổi thànhPASS. Native long-path behavior bên ngoài các paths được kiểm vẫn là portability limitation, không kết luận mọi Windows path264ký tự đều thất bại.

SAKT riêng đạt89CPUcases sau hai regression về checkpoint payload. Random/unverified weights vẫn không là fitted baseline hoặc OnlineSession hoàn chỉnh. Byte payload được giới hạn và deserialize đúng bytes đã hash; đó không là peak-RAM/decompression bound.

Review độc lập không thấy authorization widening trong runtime/worker patch. Origins trong parent runtime fixture là giả lập có nhãn; không chứng nhận Colab inherited venv. Các vị trí cần xử lý ở GPU07 đã đọc tĩnh, chưa sửa:

- `watchdog.main` và runner preflight/identity/data-path helpers còn dùng defaults/globals. Cần immutable resolved worker-context truyền cùng một identity từ parent sang child, Gate1/Gate2, authorization, loader và recovery; không monkeypatch production globals.
- Các nhánh `smoke if ... else pilot` ở caps, cohort tag, target allocation và worker dispatch phải được đổi thành explicit phase mapping trước khi thêm phase. Unknown phase hiện bị whitelist chặn, nên đây là migration hazard, không active bypass.
- Không thêm default dataclass fields mà âm thầm đổi `asdict`/config hash của mọi CPU approval cũ. Context sidecar/schema riêng hoặc migration canonical serialization cần negative/golden hash tests.
- Synthetic CUDA phase phải có manifests/Parquet riêng và hash-bound authorization trước loader; không dùng protected BKT paths vì defaults có sẵn. Development-only/fold exclusions/split hashing và cumulative recovery budget giữ nguyên. Không cho resume CPU→CUDA hoặc đổi domain âm thầm.

Đây là thiết kế/technical review, không tự phê duyệt GPU07 phase, scientific protocol hoặc allocation. Phần local tiếp theo được user cho phép tiếp tục; GPU execution vẫn phải có stage contract cụ thể và đủ prerequisites.
