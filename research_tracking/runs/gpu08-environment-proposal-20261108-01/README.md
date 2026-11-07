# GPU08: archive đề xuất môi trường Linux/CUDA — 08/11/2026

Bundle đã đóng về integrity; môi trường vẫn PARTIAL/proposal_only, execution tắt,
lock_complete=false. Không có Linux resolver closure, full transitive hash lock,
install report, image digest hoặc actual CUDA main-worker acceptance. Trạng thái
completed trong manifest chỉ là archive hoàn tất, không phải GPU08 hoàn thành.

Nguồn chính thức gồm https://pytorch.org/get-started/previous-versions/,
https://download.pytorch.org/whl/cu126/torch/ và
https://download.pytorch.org/whl/cu126/triton/; exact wheel/metadata URLs và index
SHA nằm trong proposal/candidate receipts. NVIDIA/Modal documentation URLs giữ
trong proposal và snapshot docs. Metadata bytes đã đối chiếu SHA với index;
wheel SHA chỉ là giá trị công bố, chưa kiểm wheel bytes và không tải wheel.

Giữ DNS failure fetch-01.json và cả hai lượt fetch-02/03:4responses265132bytes,
max147978bytes, cap1MiB/response/10MiBtotal. Offline validation đã có RC0/0.36s;
không chạy lại validation/model/resolver ở archive này. V12 Colab T4 dùng
Torch2.14.1+cu130 kế thừa packages không chứng nhận candidate Torch2.7.1+cu126
isolated venv hoặc current main worker. Windows pip--platform không tự chuyển
PEP508 platform_system/sys_platform; cần actual Linux/target-marker-aware resolve.

copy_inventory_before.json được ghi trước19copies; copy_inventory.json đối chiếu
SHA source/destination và giữ bytes. preparation_inventory.json là inventory
gốc; original_input_rechecks trong manifest phân biệt SHA lịch sử với file hiện
tại, không viết lại proposal nếu tài liệu vận hành về sau thay đổi. Snapshot
docs/proposal giữ links theo repository gốc; archive không là standalone runtime.

Chưa install, image build, Volume, GPU/Modal compute, cloud spend, auth hoặc thay
phân bổ tài chính. Không wheel/private credentials, raw data/Holdout hoặc thesis
draft trong bundle. Bản thảo luận văn/source map giữ ở canonical reports riêng.

record_evidence_run/verify_evidence_bundle đóng và kiểm bundle. git_ignore_check.json
ghi từng command Git check-ignore với path qua argv tường minh, không stdin;
force_add_paths.txt là danh sách chính xác bị ignore. Git chỉ được đọc, safe.directory
chỉ cấu hình ở process; không add/commit/push hoặc đổi config global/index/state.
