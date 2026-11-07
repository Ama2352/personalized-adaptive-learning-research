# Bảng đồng biến fixed-stream đã lưu

Đơn vị event snapshot trước update; không causal/temporal funnel. Action là preview.

| Package | N event pairs | P đổi | M event(any concept) | M concept crossings / concept pairs | R đổi | A preview đổi |
|---|---:|---:|---:|---:|---:|---:|
|graph_package|1080|964|90|90/30240|60|22|
|empty_graph_package|1080|37|0|0/30240|0|0|

Các denominator conditional cụ thể trong conditional_tables.csv; không lấy R/M concept crossings làm tỷ lệ chuyển tiếp.
Closed-loop thiếu mastered/ready, không dựng full chain từ oracle. Xem analysis.json cho missing fields, clusters và examples.
