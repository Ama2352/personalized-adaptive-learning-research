# Kiểm hai tiến trình AKT dùng chung T4

## Thiết kế đã chốt trước lượt chạy

Chỉ kiểm kỹ thuật trên packet TRAIN80 Junyi đã được phép chuyển. Một T4, batch32 mỗi tiến trình, source04 và FP32 giữ nguyên. Hai seed42/43 chạy lần lượt, sau đó hai seed này chạy đồng thời trong cùng container. Mỗi tiến trình có một lượt warmup và tám lượt packet đo. Hàng rào đầu/cuối ngăn warmup và checkpoint làm nhiễu khoảng training song song.

Mỗi cách xử lý cùng901.312target đo. Tổng tối đa1.160Adam updates và2.039.032target exposures gồm warmup cùng kiểm phục hồi. Mỗi tiến trình lưu checkpoint riêng. Chưa đánh giá chất lượng độc lập, chưa đổi batch của A0 chính, chưa chạy H100.

## Hạn mức và tiêu chí

Người dùng duyệt thực hiện. Tự phân bổ tối đa0,15USD trong trần30USD toàn KLTN. Một GPU, tối đa4CPU core/12GiBRAM, timeout function420giây, startup60giây, watchdog client400giây, không retry. Cận GPU/CPU/RAM540giây gồm420giây thực thi cộng60giây startup và60giây chờ tắt khoảng0,1313USD theo đơn giá đã kiểm. Dừng App sau lượt bằng budget guard.

Chỉ cân nhắc chạy song song khi tổng thông lượng tăng ít nhất10%, model/optimizer/Torch RNG/CUDA RNG và loss từng pass khớp tuyệt đối cùng seed, bốn checkpoint đọc lại và update tiếp theo khớp. Mức tăng dưới10% ghi nhận chưa đủ lợi ích trong phép đo đơn này. Kết quả T4 cần kiểm lại trên H100 trước khi áp dụng cho H100.

Nguồn kế thừa từ bundle batch32 đã đóng. Request và reservation ghim source/data/worker SHA trước dispatch. Kết quả và figure sẽ bổ sung sau khi kiểm archive, checkpoint và dừng App.

## Diễn tiến vận hành

Lần gọi local đầu chưa có quyền mạng nên dừng trước khi tạo App. T4 attempt01 được Modal nhận nhưng không cấp container trong khoảng250giây, đã dừng và guard xác nhận. Không suy nguyên nhân từ việc chờ. Chuyển một lần sang L4, trần0,20USD, cùng dữ liệu/workload/seed và source04. Cận tài nguyên540giây khoảng0,1626USD cho L4 cùng4core/12GiB. Không chạy đồng thời hai App GPU.

CLI Modal hiện yêu cầu --yes khi dừng App qua terminal không tương tác. Đã sửa callback dừng đúng App và kiểm29/29ca watchdog. Lượt pytest đầu gặp lỗi thư mục tạm của môi trường hạn chế,18ca đạt/11lỗi setup. Đổi basetemp sang artifacts/akt/local-tests trênD và đạt29/29 trước cùng sau sửa guard. Request02/reservation02 giữ lượtL4, request/reservation và attempt01-* giữ lịch sửT4.

L4 cũng cóbacklog1 và0container, đã dừng trước fallback cuối. Request03 dùng danh sách GPU chính thứcT4/L4/A10, chỉ một container, timeout360giây, watchdog340giây. Cận480giây tài nguyên theoA10 cao nhất khoảng0,1848USD trong trần0,20USD. Đây là thay đổi giả thuyết khả dụngGPU, không suy lỗi model. Nguồn https://modal.com/docs/examples/gpu_fallbacks .

Fallback03 đã được cấpGPU, dừng trước training do config output của child nằm lồng trong parent. Native archive đã tải/kiểm vàApp đãdừng. Giữ nguyênsource trước sửa ởattempt03-*. Sửa output vềdirect named results đúngvalidate_config, archive bao gồm bốn output riêng vàsync checkpoint theo label. Không nới validator. Request04 kiểm lại.

## Kết quả đã nghiệm thu

Fallback04 được cấp TeslaT4. Mỗi model chạy một warmup và tám packet đo, batch32. Hai seed42/43 dùng đúng cùng trạng thái khởi tạo và thứ tự windows giữa chạy lần lượt và đồng thời.

| Cách chạy | Target đo | Thời gian | Tổng target/giây | GPU-Util | VRAM |
|---|---:|---:|---:|---:|---:|
| Hai model lần lượt |901.312|45.493s|19812.0|87,9%|1.542MiB|
| Hai model đồng thời |901.312|45.736s|19706.9|99,9%|3.080MiB|

Tổng thông lượng đồng thời bằng0,9947lần chạy lần lượt. Chênh lệch khoảng0,53% chậm hơn trong một phép đo, chưa đủ diễn giải thành khác biệt ổn định. Không tiếp nhận chạy hai tiến trình làm phương án tăng tốc T4. Không suy kết luận này sangH100.

Cả hai cặp seed khớp tuyệt đối model/Adam/Torch RNG/CUDA RNG và loss từng pass. Bốn checkpoint còn trùng byte theo từng seed giữa hai cách chạy. Kiểm nạp lại và Adam update tiếp theo đạt cả bốn trường hợp. Không đổi main A0 batch4, chưa full epoch và chưa kiểm chất lượng độc lập.

Archive104.716.311byte đã tải vềexperiments/akt/results/modal-junyi-concurrent-small-20261112-02/artifacts.zip trênD, kiểm SHA/CRC/toàn inventory. Volume kltn-akt-modal-junyi-concurrent-small-20261112-02 giữ bốn checkpoint đãsync. checkpoint-inventory.json chỉ vị trí từngstate.pt trong archive. Giữ archive lỗi fallback03 riêng, không thay.

Worker thành công135,13giây, remote gồm đóng gói141,94giây. Cả bốn App đã được xác nhận stopped/tasks0, container cuối rỗng. Snapshot22giờ13 ghi metered3,26858233USD, credits3,26USD, billed0USD. Tăng khoảng0,03USD so snapshot trước đợt, có thể còn độ trễ metering. Credits quy đổi còn khoảng26,74USD. Chưa dùngH100.

## Figure và cách dựng lại

concurrency-comparison.svg/pdf/png được dựng từcomparison.csv vàcomparison.json bằnganalyze.py. Hai panel cho thấy thời gian xử lý cùng target cùng mứcGPU-Util. Script kiểm toàn archive, workload, checkpoint, resume và source trước dựng hình. MởREADME này cùngcomparison.json để đọc giới hạn. Một lượt ngắn, hai seed, packet lặp trongRAM, chưa đo toàn pipeline hoặc hội tụ. Mỗi child có sampler riêng nên overhead telemetry giữa hai cách khác nhau.

## ỔC và tài nguyên local

disk-audit.json ghi ổC còn khoảng7,4GiB, pagefileWindows17,15GiB, đang dùng3.257MiB và từng đạt7.968MiB, RAM trống khoảng1,15GiB. Cache người dùng cómodel HuggingFace cũ vàpip. Chưa có baseline để quy phần dung lượng vừa giảm cho nguyên nhân cụ thể. Không xóa hoặc di chuyển cache hoặc file hệ thống. Controllerprobe mới đặtTEMP/TMP/TMPDIR riêng trongartifacts/akt/runtime/modal-client-temp trênD, kiểm đạt ởlocal-temp-routing.json. Model/artifact vẫn trênD.
