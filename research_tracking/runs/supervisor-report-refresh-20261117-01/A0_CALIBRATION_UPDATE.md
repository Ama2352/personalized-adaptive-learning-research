# Cập nhật báo cáo bằng đầu ra A0 thật ngày17/11

Hai file báo cáo hiện hành được cập nhật đồng bộ, giữ ngữ cảnh Paper1/Paper2 và các phát hiện RQ1/RQ2 đã có. Bổ sung mốc17/11 tính đủ dự báo A0 cho phần calibration Junyi, giải thích vì sao cần nhóm người học riêng để hiệu chỉnh xác suất và phân biệt đầu ra số đã có với kết quả fit/đánh giá độc lập còn chờ nghiệm thu.

Nguồn metadata nhỏ trong `junyi-calibration-real-20261117-01` gồm A0_GPU_RESULT01, A0_GPU_USAGE_SUMMARY01, A0_NUMERIC_DIAGNOSTICS01 và CPU_CACHE_RESULT02. Kiểm độc lập các trường target1621484,learner15847,OOV0,worker57.913s,core12.054s,inference6.876s,55sampleNVMLmean6.236/max43. Báo cáo làm tròn58s,12s,6.88s,6.2% và43%. Không gọi58s là thời gian tính mô hình thuần, không gán nguyên nhân phần host còn thiếu số đo. Các con số utilization không chứng minh đạt50%.

Bảng Sprint4 và công việc kế tiếp ghi A0 đã có đầu ra cho hiệu chỉnh, còn A1–A3, fit hiệu chỉnh, đánh giá độc lập và Grade10. Giữ rõ giới hạn RQ3 chưa có kết luận so sánh độc lập. Không thêm tỷ lệ hoàn thành RQ hoặc claim CG-AKT tốt hơn. Không thêm figure vì các số mới mô tả một lượt thực thi; figure RQ1 đã có giữ nguyên nguồn/SVG.

`check_a0_update.py` đọc metadata và kiểm claims trong cả hai báo cáo, tag HTML/ID/anchor cùng tính tự chứa của SVG hiện có. `QA04.json` ghi PASS. Script dùng `.venv`, không truy cập dataset/model/predictions, không gọi cloud hoặc mở browser. Không kiểm giao diện trực quan mới, đoạn cập nhật dùng bố cục văn bản/table hiện hữu. `MANIFEST04.json` ghim nguồn, báo cáo và checker theo phiên bản này.

Trong lượt rà test kèm theo, root ban đầu thiếu PYTHONPATH, sau đó ZIP fixture chạm MAX_PATH Windows260ký tự ở default sandboxTemp. Không sửa source để chữa cấu hình test. Khi dùng PYTHONPATH=src và basetemp ngắn dưới artifacts/akt/test-temp, hai file test controller/input cùng đạt61ca trong4.35s tại CROSS_TESTS02 trong bundle controller. Đây là bằng chứng kỹ thuật, không đưa vào báo cáo khoa học.
