# GRAPH11 — xử lý review và giới hạn bằng chứng

Không sửa lại review01 hoặc artifacts cũ. Review01 dựa trên source a2f9/test538;
source hiện hành f40b/test332 chỉ hoàn thiện contract/checks và sửa budget fixture.

- Protocol21 trước đây chỉ kiểm shape SHA trong profile; inventory checkpoint cũ
  cũng chưa liệt kê docs21. Factory mới pin byte source21 và yêu cầu profile trùng
  source đó. Đây là consistency, không execution/selector authority.
- `_owned` kiểm default dtype FP32 trước Adam body. Native testcase đổi dtype thực
  sang float64 và phục hồi bằng finally; chỉ gọi validator, không thêm optimizer.
- RNG/modes: fixture cố ý đổi cả Python, NumPy, Torch CPU RNG và đảo từng module
  mode; sau restore so sánh trực tiếp trước evaluation/continuation. Sáu payload
  âm tính được hash lại đúng format và bị từ chối trước cả hai mutators.
- Erratum diễn đạt: review01 nói fixture có dropout0. Thực tế helper kế thừa
  frozen simulator-research dropout0.05; production và config không đổi. Direct
  assertions mới không phụ thuộc suy luận từ dropout/continuation parity.
- Bộ dữ liệu fixture tự tạo có metadata/provenance giả minh bạch. Profile native
  dùng docs21 thật; điều này không biến fixture thành corpus/fit được chứng nhận.
- Native01 chết vì monitor stat `.pending` vừa được atomic publish, không vì RAM.
  Native02 bị inner fixture cap512MiB trong khi outer review1GiB. Chỉ hai giá trị
  budget trong test đổi thành1GiB/free2GiB ở native03; production f40 không đổi.
- Tracker post-hook vẫn quét full model/Adam tensors. Native03 đo riêng body,
  pre/post hook và state validation; không coi bookkeeping miễn phí, không dùng
  timing toy để suy GPU throughput/full-corpus cost.

Root là người thực thi các lượt kiểm tra. Tác giả source/archive không chạy lại
model hoặc tests trong lần đóng gói này. Review source không thay actual logs.
