# Pilot factorial ability/prerequisite mechanism

Được user chấp thuận tối đa10seed/profile×120steps,4cells. Treatment bật parent signal/adaptation, local pathway tắt trong cả treatment/control. G_env và G_controller giữ graph lịch sử. Lambda0/.55 là variant simulator riêng đã kiểm parity ở.55.

outcomes.json lưu4cells cùng latent/random identity mỗi seed/profile. contrasts.json tính (on-off)|lambda.55 − (on-off)|lambda0. traces.jsonl.gz lưu actual served actions và outcomes. Cùng base_theta và step-indexed uniforms, labels có thể khác khi actions khác.

Đây là interaction contrast conditional trên simulator và thiết kế này, chưa là time-DiD hoặc causal benefit trên Junyi. Initial abilities nguồn có graph correlation. Pilot không có final significance testing, không dùng seed này làm untouched final. Source_provenance.json và manifest ghi nguồn/hash/caps.
