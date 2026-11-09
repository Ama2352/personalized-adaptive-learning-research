# GKT selected engineering trên corpus10×84

Terminal thực tế ACCEPTED_ACTUAL_GKT_SELECTED_ONLY_ENGINEERING.

Giữ dry02 thực, materialize03, precheck02/03 stdlib và failure02 trước NN. Failure02 có primary RAM4GiB và secondary audit đọc pseudo-path <unknown> lúc định dạng traceback, không nới read guard. Mẫu admission03 đạt ngưỡng ghi trong rawfile, admission04 không đạt headroom256MiB, admission05 đạt. Raw03 ghi extra128MiB, cả ba giá trị thực vẫn trên4GiB+256MiB. Các dấu admission là snapshot, không thay kiểm RAM thật ở normal entry.

Recipe29 giữ GKT concept28/expert31/width32/BN-D5/batch4 nguyên trajectory, seed42, Adam0.001 và response-pooled binary64 log loss. Chỉ selected train80/raw selection10 trên engineering8/1/1. Không đổi hyperparameters, không Main60/refit/calibration/Junyi/Holdout/CUDA/Modal.

Lỗi CLI ROOT thiếu --materialize và dry01 tuple-call bị bắt bằng review tĩnh được phân biệt với actual failure02. Giữ raw receipt/source byte-exact và inventory trước/sau copy. Guard Win5 gốc chưa xác định nguyên nhân; probe/canary nằm bundle tham chiếu, không nhân đôi. Checkpoint .pt chỉ tham chiếu SHA, không Torch.load. Cold62/model11/trainer8/checkpoint28 và Gate183 giữ phạm vi bằng chứng riêng. Xem acceptance.json để đọc actual counts, epochs, timings và tài nguyên của terminal này.
