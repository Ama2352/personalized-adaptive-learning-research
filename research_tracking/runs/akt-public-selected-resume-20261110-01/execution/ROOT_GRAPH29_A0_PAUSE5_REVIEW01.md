# ROOT scope parent tạm dừng sau vòng5

10/11/2026. Continuous control thực đã được nghiệm thu qua normal entrypoint, dừng ở vòng7 và chọn checkpoint vòng4. Vòng5 là continuing nonbest đầu tiên. ROOT chọn pause5 để kiểm latest5 khác best4, giữ max_epochs20 và toàn bộ cấu hình, seed, corpus10×84.

Nguồn parent builder/metadata outer/native worker/native outer đã được đọc và ghim theo handoff. ROOT duyệt kiểm metadata dry trước. Actual materialization và NN cần review riêng dựa trên output thật.

Parent native có toàn lượt180s, owned170s và worker160s. Charge wall180 được chọn trước để giữ conservative lineage540s. Child sau này có tối đa360s, giữ global training300s/40steps/13.440targets. Model constructors trong cả parent–child tối đa3, gồm1parent và2child. Parent5epochs gồm10steps/3360training targets,15forwards/5validations/420selection evaluations, bốn best saves và một latest save, không fresh-best export.

Canonical pause policy và authorization phải được kiểm thật. Parent seal chỉ xuất hiện sau owned Job0 và đúng receipt/source/counters. Future child cần actual sealed-parent SHA, không cấp giả parent proof. Giữ scope intentional complete-epoch, còn phase2 crash/partial-epoch recovery trước long paid training. Chưa cấp quyền GPU/Holdout/CV hoặc thay protocol nghiên cứu.
