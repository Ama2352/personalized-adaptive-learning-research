# F041 · Kiểu scalar native trước dispatch

**SCOPED STATIC PASS.** Chỉ đọc nguồn, chưa import hoặc gọi GAM. Worker cf05cd4d, outer f8104b51 và contract00d0fbbe giữ nguyên sau handoff.

Trong đúng constructor và update Paper2 được ghim, θ, π_task và π_time tiếp tục là Python `float`, phù hợp kiểm `type(value) is float` của canonical recorder b54b. Không cần cast hoặc sửa recorder để bỏ qua validation.

| Đường nguồn | Kiểu và lý do |
|---|---|
| Notebook cell3, MODEL_INITIAL_ELO | Literal1200.0, loader dùng ast.literal_eval, nên là Python float |
| Cell13, MemoryState defaults | θ lấy constant trên, π_task literal1.0 và π_time literal0.05 |
| GAM constructor | r_pos0.60, r_neg1.00, q_time0.04 và theta_lr80.0 là literal float |
| PathwayPolicy._context | r_pos lấy self.r_pos. r_neg và decay được bọc float(np.clip), graph summary uncertainty/deficit đã được nguồn đổi thành float |
| GAM._decayed_pi | Nhánh chưa học trả stored float. Nhánh có timestamp bọc cả hai π bằng float(np.clip) |
| GAM.update gain/residual | π_task và observation_noise là Python float, nên gain là float. residual dùng float(y−p_pred) rõ ràng |
| GAM.update θ | θ += theta_lr × gain × residual chỉ có toán hạng Python float, không nhận ndarray hoặc NumPy scalar |
| GAM.update stored π | π_task được gán float(np.clip), π_time được gán self.q_time literal float |

Phép quy nạp từ initial state qua mỗi native update giữ kiểu scalar này. NumPy ndarray nằm ở `memory`, không được gán sang θ/π. `predict` cũng trả float(np.clip), nên P truyền lại update giữ scalar của nguồn. Không dùng annotation `theta: float` làm bằng chứng runtime cast, bằng chứng là default và toàn bộ phép gán đã truy ở trên.

Số dòng đối chiếu trong `docs/thesis_recovery/evidence/paper2_source.py.txt` là42–46,434–455 và502–550. `src/knowledge_tracing/gam_kt/simulator_pathways.py:17–35` chỉ override context, không thay update hoặc scalar initialization. Stub pandas `pandas/_libs/tslibs/timedeltas.pyi:111` khai báo total_seconds trả float, nhưng kết luận stored π vẫn dựa vào cast rõ ràng của nguồn sau phép decay.

Nguồn ghim gồm Notebook353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f, bản trích5f936e5908bfc2ee9a7c7b750917c7fac52bbaef44be67557e69f6408062f2f8, loadera12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1 và pathway33ad34140f7b08eb22f86e6cc3caf7b0e7c98f09e4fd74945a6f7e9718b07560. Đây là kết luận tĩnh cho source/config đã ghim, chưa là quan sát runtime hoặc parity native. Nếu runtime bất ngờ tạo NumPy scalar, operation phải dừng theo recorder hiện tại, không cast quan sát để cho qua.
