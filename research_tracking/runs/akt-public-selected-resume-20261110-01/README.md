# AKT chạy tiếp qua public entry đã khớp đối chứng CPU

Corpus engineering có8 train learners với672targets,1 selection learner với84targets và1calibration learner. Calibration không chọn epoch. Giữ nguyên cấu hình d256 và seed42. Control hoàn tất7epochs, best4. Parent02 dừng sauepoch5, latest5 khácbest4 và stale1. Child nạp latest5 qua guard/inspector thật, chạy2epochs tiếp theo rồi xuất84targets từbest4. Cả7history receipts/loss/selection summaries khớp control, ba file raw selection khớp nguyên byte. Parent vàchild đều Job0, nguồn/runtime không đổi.

Giữ lỗi import trướcGO và assertion thư mục rỗng của lượt01, gồm chi phí10updates3360targets đã tiêu. Lượt01 không seal và không được dùng để resume. Checkpoint lớn giữ nguyên ở experiments/akt/results, inventory tham chiếu giữ SHA vàsize, không sao chép tensor vào bundle.

Đã nghiệm thu intentional complete-epoch resume trên Windows CPU trong corpus nhỏ. Unexpected fault/partial epoch, fresh Linux/CUDA, cloud durability, full research matrix và Holdout còn riêng. Đây là bằng chứng kỹ thuật, chưa chứng minh ưu thế mô hình hoặc đóngRQ3. Không chi Modal.
