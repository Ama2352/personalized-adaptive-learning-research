# ROOT review cho control intentional-resume AKT

10/11/2026. Người dùng giao engineering local và vòng làm việc năm giờ. ROOT duyệt operation chuẩn bị metadata của control A0 trên corpus engineering10×84 đã xuất bản. Đây là một phạm vi local có giới hạn, dùng để kiểm pipeline.

Corpus giữ tám người train, một selection và một calibration. Dùng current Gate183/1913 cùng index dd8bd24f và runtime schema2 đã nghiệm thu. Các giá trị d256/d_ff1024/final512, một block/tám heads, dropout0,05, lr0,0001, seed42, context100, batch4, tối đa20epochs/patience3/min_delta0,0001 được giữ theo gói engineering trước.

Metadata operation có whole60/owned57/worker50, RSS1GiB và free2GiB. Dry được đọc lại trước materialization. Actual NN dispatch cần bản review riêng sau khi có request thực, với giới hạn main540s/training300s, tối đa40Adam steps/13.440training targets và hai constructors. Admission native4GiB là lựa chọn bảo thủ cho lượt này.

Launcher chỉ cấp Git profile đã nghiệm thu cho child process. Nó kiểm các Git/GH variables thừa hoặc giá trị khác, chỉ bỏ hai biến pager đã được duyệt và giữ parent environment. Không đổi Git config toàn cục. Source worker/outer/builder được ghim đủ bốn SHA. Các artifact cũ giữ nguyên.

Control phải hoàn thành qua normal entrypoint thật trước khi chọn pause epoch. Pause/resume và crash recovery có acceptance riêng. Kết quả engineering này chưa là system winner, kết quả RQ hoặc quyền chạy fullCV/Holdout/cloud. Chưa materialize config/auth từ bản review này.
