# Nhất quán Log Loss báo cáo và bootstrap — 08/11/2026

Các mô hình phải được so bằng cùng định nghĩa phép đo, ngoài việc dùng cùng quần thể tương tác. Evaluator báo cáo BKT/GAM/AKT đã dùng xác suất float64 và Log Loss của sklearn. Tuy nhiên, sufficient statistics phục vụ bootstrap AKT còn chặn xác suất ở 1e-15 thay vì epsilon float64. Ở dự báo cực đoan sai, hai cách tính có thể khác: -log(1e-15) khoảng34,5388, còn -log(epsilon64) khoảng36,0437.

Sửa duy nhất trong thuật toán thống kê là dùng np.finfo(np.float64).eps, khớp evaluator canonical và script bootstrap BKT/GAM lịch sử. Không đổi tập tương tác, trọng số learner/fold, kiểu bootstrap, ECE15, Accuracy0,5, objective training, hyperparameters hay dữ liệu. Chưa kiểm ảnh hưởng lên artifacts thật; không tính lại hoặc sửa bất kỳ bảng lịch sử nào.

## Kiểm tra thực tế

13tests trên dữ liệu tự dựng PASS,0failure/error/skip. Test mới so actual DuckDB sufficient statistics ở xác suất0/1 đúng và sai với actual canonical sklearn evaluator: kiểm tổng LL mỗi learner và chênh lệch fold sau nhân trọng số lấy mẫu[2,1]. Các kiểm cũ về OOV/null/coverage/common identities/aggregation cũng giữ nguyên. Không dùng AUC/Brier/LL fixture như kết quả AKT đã train.

Outer7,787169900s trong cap45; source5files trước/sau bằng nhau, environment restored,0Torch/NN/solver/corpus reads; actual DuckDB/NumPy/pandas/sklearn được import. Observed peak RSS196.890.624B, available RAM đầu1.714.991.104B/cuối1.644.703.744B; đây là snapshot/Windowspeak, không monitor liên tục hoặc hardmemory quota. OwnedJob cleanupaccepted/active0/handleclosed. Không chứng nhận fullGate hay longrun readiness.

Lượt trước không chạy test bodies: audit socket.* quá rộng đã chặn gethostname metadata khi collection/JUnit. XMLpartial và traceback giữ nguyên; outer còn lỗi parseXMLpartial. Controller sau chỉ cho phép gethostname metadata, vẫn chặn socket operations/Popen/dữ liệu thật, bắt parseerror thành rejected. Không sửa source/test để né lỗi. Hai allocation45s đã ghi, không tự cộng13thành26case hoặc fabricatedRED.

[Bundle nguồn, snapshots và hai lượt kiểm](../runs/akt-metric-consistency-engineering-20261108-01/README.md). Full Gate vẫn chờ source-bound run và admission RAM≥4GiB; không lấy13targeted tests làm Gate. Không Holdout/fullCV/GPU/Modal.
