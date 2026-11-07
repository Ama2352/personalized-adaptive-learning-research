# Pilot Junyi first-exposure order

Tối đa32learner inner-train của outer-fold0,120events/learner, hash-selected cohort. Chỉ đọc user/exercise/time_done/source_row, không dùng correctness labels hoặc Holdout. Metadata graph từ prerequisites của exercise catalog, không dùng relationship_annotation_testing.

order_summary.json chứa co-observation và hướng first exposure trên prefix. reverse_summary.json là sensitivity đảo cạnh, không là graph chất lượng kém đã được xác nhận. Metadata audit ghi endpoint coverage/self loops. Chưa là graph predictive comparison hoặc instructional causal effect. Prefix censoring và cohort nhỏ hạn chế diễn giải, không suy full Junyi population. Không xuất raw learner IDs.
