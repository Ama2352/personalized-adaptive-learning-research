# CPU outer numeric → dự đoán raw/calibrated và metrics chung

## Thành phần hoàn thiện

scripts/akt/outer_numeric_cpu_export.py không nạp native model hoặc Torch. Public numeric replay ghép xác suất GPU đã đóng với cửa sổ/sidecar dựng lại từ outer reader, kiểm checkpoint/phase/encoding/source và số window/target. Dòng event độc lập đối chiếu chính xác learner,exercise,time,source_row,correct,suggested,fold. Known/OOV và toàn bộ warm-up/context reset được giữ. Chuẩn outer yêu cầu full39.616learner nếu chạy cohort thật, không dùng engineering cache reader cho outer.

Calibrator vẫn mang binding D22 cũ. Với source7c mới, helper reuse free_outer_evaluation.validate_compatibility để kiểm đủ77source map và đúng một guard delta, checkpoint và calibrator identity. Domain calibration phải khác outer và khớp binding calibrator, còn model/checkpoint/vocabulary/split/bank/reference giữ bằng nhau. Public iter_calibrated_predictions được mở một lần cho toàn stream, không hash source lại từng target. Không fit lại T hoặc tune model bằng labels outer.

## Đầu vào

Request template trong bundle chỉ mô tả schema, chưa chạy được khi còn placeholder. CLI nhận --request và --request-sha256, chạy bằng ROOT/.venv/Scripts/python.exe -B. Trước import KT, source7c/src phải đứng đầu sys.path và source_root đúng packet riêng trong artifacts/akt/local-calibration. Portable MODEL_INDEX/SUPPORT chỉ đọc metadata. Không cần weights, optimizer hoặc graph model inference mới.

Cần pin outer canonical/assignments/manifest/split, refit90encoding/roles qua export, cache receipt và manifest/admission, numeric GPU COMPLETE receipt cùng tất cả manifest/NPZ, temperature đã Drive accepted và compatibility receipt variant đầy đủ. path_map đổi địa chỉ file khi chuyển cloud→D, giữ nguyên bytes/SHA receipts và numeric members. Keys path_map là chuỗi POSIX gốc, kể cả khi chạy Windows. Không sửa metadata nguồn để dời đường dẫn.

## Đầu ra và completion

Mỗi shard Parquet tối đa32.768row, giữ toàn bộ cột PredictionRecord. prediction và raw_prediction cùng xác suất raw; calibrated_prediction là xác suất sau public applier. OOV giữ null cả hai, với prediction_kind/history/support như public replay. config.json giữ binding/calibrator/pins/path-map, COMPLETE.json chỉ xuất sau full coverage/source recheck và đóng đủ shards. COMPLETE có SHA từng Parquet, source-key digest, model/source/phase/calibrator identities và helper SHA. Không dùng learner-atomic39.616file hoặc cập nhật manifest sau mỗi learner. Đây là export mới từ numeric checkpoint đã có, không resume từng learner. Khi thất bại không ghi COMPLETE và giữ input/checkpoint nguyên vẹn.

score_export là phase CPU tùy chọn. Hàm chỉ materialize3cột numeric correct/raw/calibrated, reuse knowledge_tracing.gam_kt.evaluation._metrics nên giữ cùng AUC,LogLoss,Brier,ECE15,accuracy0,5. OOV bị loại khỏi metric numerator/denominator có ghi coverage riêng. Không materialize4triệu Python PredictionRecord. Retain user_id/source_row để ghép baseline/paired-learner CI sau. So sánh matched-row với BKT/GAM và bootstrap/CI là phần còn thiếu riêng, chưa được gọi benchmark hoàn chỉnh.

## Kiểm thử và giới hạn

Lượt nguồn cuối tests04 đạt21ca trong5,84giây, gồm13ca worker và8ca exact source compatibility có sẵn.2learner6target gồm4known/2OOV, chronological target order, raw/calibrated exact public scalar applier, nhiều compact shards, metrics chung, source/phase/checkpoint/calibrator/cache/count/coverage/numeric tamper failures và POSIX→Windows path relocation được kiểm. CLI import không tải Torch. Guard requested variant phải khớp export model đã nằm trong nguồn cuối tests04. Chưa có lượt end-to-end CLI với actual frozen assets từ nhánh này.

Không chạy outer cohort thật, cloud/GPU, training hoặc calibration từ bundle này. Chưa đo wall/RSS đầy đủ4,137triệutarget. Root giữ ownership thực thi/cache/GPU/output Drive và phải nghiệm thu request cùng runtime source7c trước chạy. Nguồn helper ngoài KT, không thay source packet hoặc artifacts đang chạy.
