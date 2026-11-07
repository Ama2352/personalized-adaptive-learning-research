# Pilot closed-loop Paper2 trên CPU

Dùng definitions/dynamics/selector nguồn với graph môi trường và controller cố định. Ba variant graph-free, full graph-package và empty-graph package dùng cùng latent starts, cùng uniforms theo step. Khi actions khác nhau thì labels cũng có thể khác.

closed_loop_outcomes.json chứa net gain, retained gain, coverage và actual action sequences. traces.jsonl.gz chứa events thật được phục vụ trong simulator trước update. Lịch gap6h và72h mỗi28steps theo nguồn. Đây là pilot ngắn, chưa tái lập bảng500steps của Paper2.

Không diễn giải differences prediction như paired same-target metrics. Không gán toàn bộ package effect cho edges. Retention theta gain sau14ngày được kiểm bằng hệ số exp(-.84) trên từng run, nên không là outcome độc lập với final theta gain trong điều kiện này. Chưa thực hiện inference/CI hoặc kết luận causal ngoài simulator.
