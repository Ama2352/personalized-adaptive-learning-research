# Wrapper outer native, kế hoạch nhỏ ngày17/11

Mục tiêu là đóng hợp đồng admission/coverage cho nguồn KT frozen, không thực thi outer thật. Reuse native batched inference và consumer temperature hiện có. Không thay model, binding cũ hay protocol thống kê.

- [x] Test trước cho fullouterrole/refitencoding, source/domainpins, cross-domaincalibrator giữ7field còn lại, OOVnull và coverage/rowkeys.
- [x] `scripts/akt/free_outer_evaluation.py` cung cấp admission và iterator native có receipt chỉ complete khi tiêu thụ hết. Đầu vào là predictor đã attach, learnerfactory và caps/counts chính xác. Không nạp weights hoặc cấp GPU.
- [x] Chạy tests tổng hợp bằng `.venv`, giữ red/green và nguồnSHA. Đối chiếu Protocol21/Recipe26, ghi phần final family còn thiếu.
- [ ] Trả root review/commit. Output thực sau này phải Drive; wrapper native này chưa là worker CPU/GPU tách biệt đã đo.
