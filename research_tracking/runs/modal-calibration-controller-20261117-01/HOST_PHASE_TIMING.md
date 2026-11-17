# Phân rã thời gian host trong gpu_predict

Root ghi nhận A0 full calibration inference đã hoàn tất trên image bất biến trước lượt sửa này. 1.621.484target,28.653window,224shard. Thời gian worker57,91s, gpu_predict54,65s, core receipt13,893s. 55sample NVML có mean6,236%, max43%, VRAM1835/81559MiB. Các số này do root cung cấp từ artifact thực, không được đo lại trong nhánh code này. Khoảng thời gian ngoài core chưa đủ dữ liệu phân rã, không gán nguyên nhân khi chưa có số đo từng bước và không tuyên bố GPU usage đạt50%.

Chỉ bổ sung timing vào `gpu_predict`, không sửa KT source, tham số, dữ liệu, schema shard hoặc toán học. Trường `host_phase_seconds` gồm request_validation,imports,cache_receipt_read,load_inputs,source_checks,window_session,graph_cache,numeric_binding,configure_cuda,numeric_core,config_write,volume_commit. Đây là các đoạn liên tiếp, tổng bằng worker_seconds của hàm. numeric_core bao gồm setup/model của wrapper và inference, có thể phân rã tiếp bằng timings trong core receipt. Thời gian process startup/CLI trước gpu_predict và parent NVML/commit sau child vẫn thuộc thời gian function tổng, không nằm trong partition này.

`volume_commit_seconds` tái dùng duration của phase volume_commit. GPU receipt/shards cũ không sửa. Timing nằm trong result của worker mới. Source identity mô hình d22f…c96c không bị đổi vì chỉ script wrapper thay đổi, root tiếp tục pin script SHA theo image mới.

`TESTS11.txt` ghi42ca đạt trong6,86giây. Hai ca mới dùng fake CUDA/cache/core cho A0 và A1, kiểm phase đủ/không âm/tổng khớp, giữ batch128, variant/graph binding, config nguyên vẹn và chỉ commit một lần. Không benchmark/cloud hoặc GPU thực trong lượt này. Root sẽ lấy timing actual từ A1–A3 cùng recipe để hoàn tất inference, không mở nhánh tối ưu kiến trúc mới từ lượt sửa này.
