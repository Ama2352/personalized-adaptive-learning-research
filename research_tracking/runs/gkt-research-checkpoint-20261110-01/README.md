# GKT checkpoint cuối vòng huấn luyện đã nghiệm thu

28ca đạt0FES, gồm save/restore và các artifact bị sửa có chứng thực lại. Hai model/Adam,6forward/updates và96target exposures là workload thực. Sau restore, vòng kế tiếp khớp model/BN, Adam, owned RNG và cumulative counters với control. Đã kiểm trước mutation và poisoned state khi mutation lỗi, giữ caller RNG. Source/runtime khớp và Job0. Phạm vi same-process/same-budget-origin, chưa publicproducer/freshOS/crash/CUDA hoặc fitted baseline. Payload vẫn ở basetemp pipeline, không đưa vàoGit.
