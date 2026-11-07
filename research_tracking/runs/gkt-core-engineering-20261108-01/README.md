# GKT Batch A: pure kernel engineering — 08/11/2026

Immutable run `gkt-core-engineering-20261108-01` giữ kết quả43CPUcases PASS
1,957s(controller2,827425s),0failure/error/skip; chỉ archive, không chạy lại tests.
Source/test/report freeze, source SHA trước/sau và pre/post-copy SHA được giữ.

**GKT vẫn INCOMPLETE:** aggregate_after_observation, static incoming/outgoing
message arithmetic và readout với state/embeddings/precomputed transforms do
caller cung cấp. Không h0, G_ea, GRU/recurrence, MLP/normalization, trainer,
fitted scores, checkpoint/export, sequence/OnlineSession hoặc end-to-end proof.
0optimizer/GPU/cloud/realdata/Holdout; không pseudotrained artifact hoặc efficacy.
Positive numerical fixtures CPU FP64; FP32 API chưa có positive suite riêng.
Query→observe chronology và input origin vẫn caller contract; metadata hashes
không attest training provenance. Support mask không chọn sparse recurrent policy.
S04/S05 và graph/capacity/history/model-environment allocation vẫn pending.

## Đọc bằng chứng

- [Snapshot readiness](gkt_core_readiness.md) và [report canonical](../../reports/gkt_core_readiness_20261108.md).
- [Source audit/plan](gkt_source_and_core_plan.md), [primary-source provenance](source_provenance.json).
- [Trial receipt](trial01_run.json), [log](trial01_pytest.log), [XML](trial01_pytest.xml).
- [Copy inventory trước](archive_copy_inventory_before.json) và [đối chiếu sau](archive_copy_inventory.json).
- [Selected link checks](selected_links.json), [force-add paths](force_add_paths.json).

Source snapshots `gkt_config.py`, `gkt_core.py`, `gkt_init.py`, `test_gkt_core.py`
khớp source/test snapshots của trial01; không giả đây là trial mới. Archive không
copy .pt/dataset/Parquet hoặc dependencies/runtime. Source-plan JSON giữ raw
external hashes=null: web primary text đã đọc, không downloaded PDF/visual check
hoặc author-code parity. `jhljx/GKT` không được gọi author-official implementation.

## Tái lập và giới hạn

Repo/runtime tương thích cần có để tái lập tests; snapshots là evidence, không
standalone runtime. Canonical report/plan còn dùng repository-relative links;
giữ nguyên bytes và kiểm từ original directory trong selected_links.json, không
claim mọi relative link của archived snapshot tự resolve tại đây. Test command
và env/timeout ở trial receipt; lần tái chạy phải chọn attempt/basetemp mới.
Pack script chỉ inventory/copy/hash/XML parsing/helper closure, không model/test
execution. Helper verify chỉ kiểm output integrity, không scientific validity.
Không sửa indices/state/tasks/Git/native AKT/shared hoặc chạy thêm experiment.
Không thêm/sửa file sau closure; parent quản review/index/commit riêng.
