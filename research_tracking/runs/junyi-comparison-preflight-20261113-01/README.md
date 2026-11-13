# Kiểm tính tương thích Junyi A0–A3 trước GPU trả phí

Ngày 13/11/2026. Đây là hồ sơ kiểm kỹ thuật và phương pháp. Mốc tham chiếu là A0 H100 batch128 đã hoàn tất chọn checkpoint, 12 epoch, selected 9. Hồ sơ nguồn A0 đã đóng được giữ ở `../junyi-a0-h100-batch128-20261112-01/`.

## Phạm vi đã kiểm local

`data-audit.json` ghi kết quả thực của `scripts/akt/audit_junyi_comparison.py`. Auditor kiểm SHA roles, encoding, receipt, manifest cửa sổ và hai file cache dữ liệu train/selection. Chỉ đọc metadata người học Development từ assignments để tái tạo roles. Cùng SHA assignments được đối chiếu với manifest A0 và hồ sơ GAM-KT CV. Vocabulary 717 khớp receipt fit train80 và identity cửa sổ. Hồ sơ độc lập trước đó `../junyi-lifecycle-20261112-01/full-encoding-independent-check.json` xác nhận native vocabulary/support bằng truy vấn train riêng.

| Vai trò | Số người học | Mục đích |
|---|---:|---|
| train80 | 126.774 | Cập nhật trọng số, fit vocabulary và graph/confidence có học |
| selection10 | 15.847 | Chọn epoch và hệ thống theo quy tắc đã chốt |
| calibration10 | 15.847 | Fit temperature ở giai đoạn tương ứng sau refit |
| outer-validation fold 4 | 39.616 | Đánh giá độc lập |

Auditor so sánh từng ID của bốn nhóm với kết quả tái dựng từ split gốc. Không đọc đáp án Holdout. Hai file cache chỉ chứa train/selection theo manifest và đã đối chiếu hash. Chưa replay toàn bộ hàng dữ liệu hoặc hash lại từng shard cache cửa sổ trong đợt này.

`local-tests02.xml/log` ghi 103 ca đạt và 11 kiểm phụ. Bộ mới kiểm đổi batch, seed, learning rate, số epoch tối đa, patience, min_delta, vocabulary/roles/cache pins, graph history, oracle labels và confidence lấy từ selection/calibration. Hợp đồng so sánh nằm tại `src/knowledge_tracing/akt/comparison_contract.py` và được auditor dùng để kiểm tham chiếu A0. Chế độ `--candidate` kiểm đặc tả, `--observed` yêu cầu thêm population digest đo từ dự báo thực. Hợp đồng hiện chưa được bắt buộc trong mọi launcher, candidate chưa được cấp trạng thái sẵn sàng training.

## BKT/GAM-KT có thể so sánh đến mức nào

BKT, GAM-KT và AKT dùng cùng canonical identity và frozen outer assignments. Tuy nhiên BKT/GAM-KT lịch sử fit thông tin trên toàn bốn outer-train folds, A0 hiện tại fit train80 bên trong bốn fold đó. A0 selection10 đã dùng chọn epoch. Vì vậy metric selection A0 chỉ mô tả tiến độ chọn checkpoint.

Đối chiếu chính thức phải dùng cùng outer-validation fold 4, join theo source_row và xác minh user/exercise/time/label, báo cả population đầy đủ và giao các hàng có dự báo fitted. Phải ghi rõ khác biệt lượng dữ liệu train giữa baseline lịch sử và protocol mới. GAM-KT có fallback cần báo riêng, BKT unsupported giữ null, AKT OOV giữ null/reason. Mọi bảng graph effect giữa A0–A3 cần cùng train/selection/calibration roles và vocabulary.

Đọc source xác nhận BKT và GAM-KT đều dùng ECE 15 khoảng đều, cùng AUC/Log Loss/Brier/Accuracy. Việc tái dùng công thức metric vẫn cần cùng target và điều kiện thông tin. Không yêu cầu BKT dùng optimizer, batch hoặc epoch của AKT. Giữ cấu hình EM BKT đã frozen. Phần so sánh cùng lượng thông tin train cần matched fit có manifest riêng nếu được thực hiện sau này.

## Quy tắc đào tạo A0–A3

- Cùng nguồn backbone upstream, cùng khởi tạo backbone seed 42, cùng train80 và target masks, thứ tự thời gian và cửa sổ context100/target100/max_length200.
- Cùng batch128, Adam/lr/betas/eps/clip, FP32/deterministic flags và cùng selection10.
- Cùng tối đa20 epoch, patience3, min_delta0,0001. Epoch được chọn có thể khác theo từng model. Đề xuất hội thoại giới hạn9 epoch cho A1–A3 chưa được áp dụng.
- Graph dùng đúng effective native-window prefix. Độ tin cậy học chỉ từ train80 và gắn đúng vocabulary, chiều cạnh, graph source. Nhãn cạnh oracle chỉ được phép ở đối chứng oracle mô phỏng có khai báo.
- Với expert topology cung cấp sẵn, cần ghi nguồn và đặc tính ngoại sinh. Learning graph/confidence vẫn phải khóa train80. Graph quality trên Junyi còn chịu ảnh hưởng thứ tự luyện quan sát được.
- Refit90 và calibration theo Protocol21 vẫn là công việc đang chờ. Đề xuất bỏ refit trong hội thoại chưa thành thay đổi protocol. Mọi thay đổi phải có phiên bản và được ghi trước lượt chạy.

## Kiểm native và các failure giữ lại

`native-tests.xml/log` giữ lỗi Git ownership trước model execution. Lượt02 dùng safe.directory ở mức tiến trình cho đúng repo upstream trên D, không sửa Git global. Lượt02 đạt29 ca rồi lỗi Windows quyền tạo hardlink checkpoint. Lượt03 chạy phần selected-runner/encoding/phase-data với quyền tạo hardlink trong vùng test, đạt32 ca. Các ca graph-model trong lượt02 đã thực thi trước lỗi hardlink. Không cộng các lần chạy trùng thành số bằng chứng độc lập.

## Colab T4

Notebook `notebooks/akt_colab_junyi_comparison.ipynb` dùng venv trong dự án, đọc thư viện sẵn có qua system-site-packages. Cài bổ sung nếu thiếu chỉ qua Python của venv. Runtime đầu CPU được ghi nhận rồi người dùng chuyển T4. Đã đo T4 thực với Torch2.14.1+cu130/CUDA13.0 trước upload.

Gói `artifacts/akt/colab/junyi-comparison-preflight-20261113-02.zip` có315file và SHA141e0dddd39d0483f9f9d97d434386caefbce746cd11af82b9cfa3bc32c8b077. Upload32phần, Colab đối chiếu toàn bộ hash rồi tạo venv. Không có dataset Junyi, token hoặc checkpoint nghiên cứu trong gói.

Lượt tạo venv đầu lỗi ensurepip trên Colab, sửa cách tạo bằng `--without-pip --system-site-packages`. Lượt pytest Colab đầu thiếu thư mục cha basetemp, giữ log và sửa notebook tạo thư mục trước. Notebook giữ log từng attempt, GPU chỉ chạy sau biến TESTS_ACCEPTED xác nhận pytest thành công.

Probe T4 mới dùng 128 cửa sổ tổng hợp, chiều dài200, target100/cửa sổ và vocabulary717. Kiểm A0/A1 chung backbone, graph-off, perturb nhãn hiện tại/tương lai, ba bước Adam gồm continuous/resumed comparison, checkpoint và dự báo. Probe này cần nghiệm thu kết quả thực trước khi ghi CUDA đạt. A2/A3 Junyi cần confidence và producer riêng. Các bước này không cấp trạng thái ready cho toàn ma trận.

## Điều kiện trước H100 tiếp theo

1. A1–A3 có candidate descriptor qua hợp đồng, graph/confidence artifact thật và kiểm byte/hash/provenance.
2. Nối kiểm bắt buộc vào entrypoint training thực, gồm cùng initial backbone và đối chiếu selection population A0 khi xuất dự báo. Thiết kế kiểm phải tách expected identity trước launch khỏi observed identity sau chạy.
3. Kiểm T4 đạt cho đúng source và variant. Source mới cần hồ sơ kiểm tương ứng. Môi trường H100 vẫn cần kiểm hữu hạn ban đầu của lượt chính.
4. Chốt ma trận và dự toán tổng fit/refit/calibration/inference trong credits còn lại, chừa dự phòng lỗi. Các mức epoch được chọn sẽ được đo theo cùng early stopping.
5. Checkpoint/optimizer/RNG/counters, manifest, source/data/config, target IDs và labels, coverage/OOV, metrics và logs có hợp đồng xuất. Sai population hoặc thiếu artifact thì dừng, giữ failure và phục hồi từ checkpoint đã kiểm.

Trạng thái hiện hành và kết quả Colab cuối được bổ sung ở phần nghiệm thu dưới đây. Trạng thái đầu đợt là DATA_LINEAGE_PASS / GPU_AND_CANDIDATE_WIRING_PENDING.


## Nghiệm thu cuối đợt

Đã đối chiếu split A0 với assignments BKT/GAM-KT, tái dựng đúng bốn nhóm người học và kiểm hash cache train/selection cùng vocabulary 717. Colab đạt 156 ca kiểm trên Linux. Kiểm CUDA tổng hợp A0/A1 trên T4 dùng batch128, chiều dài200 và vocabulary717 đã đạt trong khoảng14giây, VRAM cấp phát cao nhất4,70GiB. Backbone khởi tạo khớp chính xác với A0 H100, graph-off khớp A0 và nhãn hiện tại/tương lai giữ đúng ranh giới nhân quả. Model và Adam sau phục hồi khớp chạy liên tục. Checkpoint, dự báo kiểm, runtime và logs đã tải về D, đối chiếu SHA/CRC/inventory.

Mốc này xác nhận thêm độ tin cậy kỹ thuật cho A0/A1. A2/A3 Junyi còn thiếu confidence fitted đúng train80 và tích hợp producer. Hợp đồng so sánh mới đã có kiểm âm, còn cần nối bắt buộc vào các entrypoint trước training chính. Các variant cần cùng batch128, split/vocabulary, cửa sổ, khởi tạo backbone và quy tắc tối đa20epoch/patience3/min_delta0,0001. Epoch tốt nhất có thể khác nhau. Đề xuất giới hạn9epoch và bỏrefit trong hội thoại chưa được áp dụng vào protocol.

BKT/GAM-KT lịch sử dùng toàn outer-train, còn A0 hiện fit train80. Metric selection A0 phục vụ chọn checkpoint. Bảng so sánh chính thức cần cùng outer-validation, target identity và coverage, đồng thời công khai khác biệt dữ liệu train hoặc thực hiện matched baseline fit riêng. Các công thức AUC/LogLoss/Brier/ECE15bins được giữ tương ứng. Cả ma trận fit/refit/calibration/inference còn cần dự toán trong credits còn lại trước lượt H100 tiếp theo.

Artifact ở `experiments/akt/results/colab-junyi-comparison-20261113-01/artifacts.zip`, 25.111.987byte, 11file đã đối chiếu inventory. Gói chứa checkpoint tổng hợp của lượt đạt, dự báo, logs, JUnit, runtime và source-overlay. Failure checkpoint thiếu epoch ở lượt đầu được giữ trên Colab, log/schema lỗi giữ về D. Bản nguyên source02 và source03 vẫn ở artifacts/akt/colab. Source03 chỉ sửa progress.epoch của probe, overlay đã đối chiếu với source local. Không thay thuật toán checkpoint hoặc kiến trúc để xử lý lỗi probe.
