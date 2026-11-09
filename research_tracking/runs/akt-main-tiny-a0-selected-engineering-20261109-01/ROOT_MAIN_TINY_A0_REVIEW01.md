# Review Root cho metadata và allocation Main A0 tích hợp

Đã đọc diff metadata05d30f/c aaf8 so với builder đã nghiệm thu trước, hợp đồng293a650 và review độc lập worker3720a519/outera94a7126. Bộ840lượt đã được collector thật tạo và nghiệm thu. Dùng8/1/1roles672/84/84 và A0emptycondition từ chính corpus mới. Giữ20epochs/patience3/seed42 và toàn bộ recipe mô hình.

Cho phép prepare-dry trước, chưa materialize hoặc gọi fit ở bước này. Exactdry cần Root đọc riêng. Allocation dự kiến40Adam/13.440targets, training300s/mainwall540s, worker560/owned580/outer600, RSS1GiB/free2GiB, checkpoint64MiB và tổngoutput1536MiB. Helper0dc và nguồn177 giữ nguyên. Sau khi materialize, actualfit cần review từng artifact và command riêng.

Main normalentry phải gọi factory thật, không nhận caller guard/callback giả. NN observers chỉ cài qua genuine lazy_tools sau guard. Whitelist tổngGit10(N+2) đã bao gồm20constructorcommands. Không fullCV/Holdout/refit/calibration/GPU/Modal. Fixture chỉ kiểm tích hợp. Metadata và source review không là fitted research evidence.
