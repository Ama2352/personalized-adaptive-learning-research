# Metric sau calibration — ngày08/11

## Đã bổ sung

AKT research runner nay xuất riêng **raw canonical metrics**, **calibrated canonical metrics** và **objective nội bộ của temperature fit**. Không dùng clipping/objective Tfit thay Log Loss báo cáo. Helper join theo đầy đủ target identity, kiểm cùng population/support, giữ OOV null và không thay prediction gốc. Đánh giá trên chính calibration partition được ghi rõ là in-sample, không phải chất lượng ngoài mẫu hoặc latent mastery đã calibration.

## Bằng chứng kiểm

-36pure runner tests PASS; controller1,1420376s +2s conservative preparation charge =3,1420376s/20. Một lỗi chuẩn bị controller do newline đã giữ trước khi test;0test bodies ở lần chuẩn bị đó. Chỉ stub evaluator, không actual NN/solver.
-Một probe bổ sung dùng **pandas/sklearn evaluator thật**,5hàng tự dựng (4supported+1OOV), đảo thứ tự truth/calibrated rows để kiểm join theo identity. Raw/unsupported giữ nguyên; metric khớp evaluator trực tiếp. **Mọi AUC/LL/Brier trong probe là số liệu fixture, tuyệt đối không là kết quả AKT/CG-AKT hay minh chứng RQ.**
-Probe ở Windows owned Job trước GO, helper elapsed12,881742954s/25, cleanup accepted/job0/handles closed, peak RSS158.949.376B và available RAM cuối1.219.297.280B. Caller không persist total wall sau khi đọc/xuất receipt, nên không tuyên bố25s là end-to-end acceptance của caller. Không cần chạy lại để lấp số đo đó.
-Ngân sách memory được kiểm trước/sau imports và cuối; không phải hard OS memory quota hay đo liên tục. Package metadata/RAM snapshot trước đó3,52GB available không bảo đảm còn đủ RAM khi chạy; probe thực tế chỉ còn khoảng1,22GB sau import. Không suy đủ bộ nhớ để chạy training hoặc toàn Gate.

## Còn thiếu trước research fit

Chưa actual research-fitted model, actual temperature fit trên corpus hoặc final evaluation. Pure101PASS ở bundle trước là phiên bản trước metric export, không gộp thành137quan sát/testcases độc lập. Current full Gate chưa nghiệm thu: source inspection phát hiện xung đột collection giữa20module top-level importTorch và các pure assertions; thêm một module đòi không NumPy/pandas/Torch. Cần process isolation giữ mọi test, cùng global deadline trước khi thử Gate thật. Đây là static finding, không phải fullGate đã chạy và thất bại.

[Bundle36tests và probe evaluator](../runs/akt-calibrated-reporting-engineering-20261108-01/README.md). Không sửa snapshot báo cáo GVHD ngày08/11, không dùng Modal/Holdout/fullCV.
