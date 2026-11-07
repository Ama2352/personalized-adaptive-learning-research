# Common-population sensitivity của Junyi order

Tái dùng graph base và cả ba controls từ run mở rộng đã được duyệt. Đọc lại đúng hash-ranked inner-train cohort và bounded prefix; không correctness/Holdout, không train model, không tạo graph mới hoặc chọn seed.

So sánh equal-weight learner, trong mỗi learner lấy trung bình các observed child có incoming edges. Giữ denominator incoming degree như nhau giữa graph. Tách parent xuất hiện trước, sau, trùng timestamp và chưa xuất hiện trong prefix. Common-coobserved sensitivity dùng cùng learner–child intersection giữa hai graph, báo attrition; vẫn không có instructional/causal interpretation. Không xuất raw learner IDs hoặc p-value/CI từ pilot.
