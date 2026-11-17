# Cache calibration chuẩn bị trên CPU cloud

## Đã hoàn thiện

API `scripts/akt/prepare_junyi_calibration_caches.py` chuẩn bị một window cache dùng chung A0–A3 và ba graph-context cache A1–A3. Chỉ dùng metadata portable export, encoding refit90 và confidence TRAIN80 đã có. Không nạp weights, fit confidence hoặc gọi GPU.

Lượt cuối `tests02.txt` đạt **48 kiểm thử, bỏ qua 1** trong 6,09 giây, gồm bộ window-cache cũ và các ca mới trên fixture tổng hợp. Ca bỏ qua cần quyền tạo symlink Windows để kiểm một mount alias thật. Các ca cloud-root opt-in, từ chối root ngoài Volume, pin sai và admission sai vẫn chạy đạt. `no_torch_import.txt` xác nhận import đường CPU không đưa Torch vào process.

Chưa chạy nguồn Junyi thật, chưa xây cache calibration thật, chưa đo thời gian CPU hoặc kích thước cache thật. Đây là nghiệm thu software, không phải kết quả nghiên cứu mới hay chứng nhận hiệu năng cloud.

## API CPU

`inspect_calibration_exports(export_indexes, run_id=..., budget=...)` gọi `inspect_cpu_refit_export` cho bốn MODEL_INDEX.json có SHA bên ngoài. Hàm chỉ đọc index/SUPPORT và kiểm variant, chưa nạp tensor.

`prepare_calibration_caches(assets_by_variant, paths, source_pins, population, output_root=..., artifact_root=..., max_seconds=..., max_rss_bytes=..., volume_commit=...)` tiêu thụ canonical calibration stream đúng learner. Các đối tượng assets có từ bước inspect.

- `artifact_root` cần đúng kiểu `JunyiCacheArtifactRoot` ở `src/knowledge_tracing/akt/cache_artifacts.py`.
- Worker dùng `JunyiCacheArtifactRoot(Path('/artifacts').resolve(strict=True))` và tạo output dưới root vật lý đó. Chỉ mount `/artifacts` được tin để resolve. Alias/junction ở nhánh con bị chặn.
- Mặc định các API cache cũ giữ nguyên vùng local thuộc PROJECT_ROOT/artifacts. Tham số cloud root là opt-in tường minh.
- Cần thư mục output mới, callback commit Volume và giới hạn wall/RSS. Callback được gọi sau hoàn tất window cache, admission và mỗi graph receipt. Lỗi giữ FAILURE.json và cache đã có trên cloud. Root cần timeout CPU worker để chặn cả giai đoạn strict admission.

## Binding và receipt

`CACHE_RECEIPT.json` giữ nguyên population manifest, source_pins, phase/calibration identity và encoding/refit90 identity. Hai khóa dữ liệu được phân biệt.

| Trường | Ý nghĩa |
| --- | --- |
| `source_data_sha256` | SHA canonical.parquet, làm khóa cho window cache |
| `dataset_sha256` | population.identity, làm khóa cho graph cache |
| `windows.path` | Thư mục window cache vật lý trên Volume |
| `windows.manifest_sha256` | Pin manifest window cache |
| `windows.summary` | records, windows, unseen_targets, target_rows, window_tokens, learners |
| `windows.admission_path` và `admission_sha256` | Biên nhận CPU strict kiểm toàn stream và từng shard |
| `graphs.A1/A2/A3` | path, sha256, binding, windows, targets riêng từng condition |

Biên nhận population giữ cả population_sha256 và prefix_keys_sha256. Entry kiểm identity population, phase/roles, source metadata và byte/SHA canonical/assignments trước dựng cache. Fixture đi qua đủ hai learner, 308 target, các window qua biên 100/200 và ba kiểu graph context. Graph cache mở lại cho kết quả byte bằng build context trực tiếp.

## Handoff GPU

GPU nhận checkpoint cùng cache/shard và admission đã ghim. Mở `JunyiWindowCacheSession` bằng `admission_receipt`, `expected_admission_sha256`, `artifact_root` để dùng kết quả strict CPU sau kiểm SHA. Mỗi graph cache mở bằng `GraphContextCache.open(..., dataset_sha256=receipt['dataset_sha256'], window_manifest_sha256=..., artifact_root=...)`.

Prediction window không có current-target labels. Các prior_responses là đáp án quá khứ cần thiết cho AKT. GPU stage không đọc canonical raw labels, chạy SQL join dữ liệu Junyi hay fit confidence. Việc chuyển graph SQLite thành numeric batch đầu vào GPU thuộc nhánh inference riêng. Source CPU admission đã pin thêm cache_artifacts.py, nên cần dựng lại admission sau source freeze. Cache đang dùng phải cùng phiên bản validator với GPU worker.

## Kiểm lại

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
.\.venv\Scripts\python.exe -B -m pytest tests/akt/test_junyi_calibration_cloud_caches.py tests/akt/test_junyi_window_cache.py -q -p no:cacheprovider --basetemp=artifacts/akt/runtime/calibration-cloud-caches-tests-20261117-05
```

Lượt đầu thiếu PYTHONPATH nên dừng ở collection. Sau đặt đúng đường src, các lượt đã chạy xác nhận 46 đạt, tiếp theo 47 đạt/1 bỏ qua ở tests01 và cuối 48 đạt/1 bỏ qua ở tests02. Không có training hoặc thí nghiệm dữ liệu thật trong các lượt này.
