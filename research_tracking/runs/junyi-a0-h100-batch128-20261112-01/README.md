# A0 Junyi batch128 trênH100

Người dùng yêu cầu chạyH100 choA0 và chọnbatch128 trực tiếp, không benchmark batch riêng. Lượt mới từseed42, protocol akt-nr-exercise-v2-batch128. Giữ optimizer/lr/split/window/FP32/early stopping như cũ, chỉ batch và hardware đổi theo yêu cầu. Sáu epochbatch4 giữ làm lịch sử riêng. Không coi lịch sử batch4 là epoch của lượtbatch128. Các model so sánh sau cần cùng công thức batch128.

TRAIN80 126.774learner/13.347.331target, selection10 15.847learner/1.600.343target, 717exercise, không calibration/outer-validation/Holdout. Tối đa20epoch, patience3,min_delta0,0001. Batch128 tạo1.818update/epoch trên232.662window, tối đa36.360update.

Kiểm nguồn và cấu hình trênCPU trướcGPU. Không có lượt benchmarkGPU riêng. Training thật theo dõi GPU/VRAM/throughput/loss và checkpoint. NếuOOM hoặc sai input dừng, giữ log. Đặt trầnA0selected đợt đầu3USD trong trần toànKLTN30USD và vẫn chừa ngân sách cho phần còn lại. Phầnrefit/calibration cần đầu vào cùng công thức đã đóng băng và được theo dõi riêng.
