# Đặc tả chuẩn bị thí nghiệm CPU09 và CPU10

Ngày07/11/2026. DRAFT cần chốt trước execution cho kết luận nghiên cứu. Các diagnostic lịch sử đã thực hiện không trở thành final evaluation. Thay đổi simulator chỉ ở variant có version riêng, giữ source lịch sử.

## CPU09 — tách graph package và learner ability

Mục đích là phân biệt cạnh tiên quyết với local adaptation, sau đó kiểm tác động khi môi trường có hoặc không có prerequisite learning penalty. Model source Paper2 hiện có ba nhóm pathways cần tách.

| Pathway | Biểu thức nguồn | Bật/tắt độc lập |
|---|---|---|
| Parent signal | graph_weight × mean parent theta signal | S |
| Parent adaptation | q_task thêm .025×parent uncertainty+.020×parent deficit, decay thêm .004×parent deficit | P |
| Local adaptation | r_neg×.90 khi struggling, decay thêm .004×times_forgotten | L |

Acceptance trước run là S=P=L=1 trùng full package gốc từng predict/update, S=P=L=0 trùng graph-free gốc. Empty graph không đủ kiểm local pathways vì cần history kích hoạt struggling/forgetting. Fixtures phải bao gồm learner đã5attempts, recent outcomes và mastery→forgotten transition. Clamp/context nguyên nguồn phải được giữ đúng thứ tự.

Giai đoạn ablation nhỏ gồm baseline000, signal100, parent010, local001 và full111. Giữ G_env và G_controller cố định. So sánh graph-specific phải giữ L bằng nhau giữa treatment/control. Full111−000 được gọi package contrast. Không dùng nó thay edge-only contrast.

Giai đoạn ability dùng paired randomized factorial. Treatment là bật S/P với L giữ bằng nhau; control tắt S/P. Môi trường variant-v1 dùng lambda0 hoặc.55 trong prerequisite factor, các phương trình còn lại giữ nguyên. Cùng base_theta, item bank, timestamp và noise uniforms theo step giữa4cells. Không regenerate base_theta theo candidate graph. Phân tầng PG/PY/PYH, không dùng high làm untreated cho low.

Estimand mỗi profile là E[(Y_edge_on,lambda.55−Y_edge_off,lambda.55)−(Y_edge_on,lambda0−Y_edge_off,lambda0)]. Đây là interaction của interventions trong simulator. Initial ability gốc có graph correlation nên cần báo conditional interpretation. Không gọi automatic time-DiD. Primary outcome đề xuất net mean theta gain, secondary retained theta gain có redundancy và coverage. Mọi môi trường/variant có identity riêng.

Pilot đề xuất10paired seeds/profile,120steps,4cells, tổng14400events, timeout120s và khôngGPU. Seed list mới phải đăng ký trước run, không dùng pilot làm untouched final. Pilot để kiểm support/runtime và artifact contract. Số seed confirmatory, CI/test families và độ chính xác mong muốn cần chốt sau đo variability, không chọn theo p-value mong muốn.

## CPU10 — Junyi practice order

Catalog junyi_Exercise_table có prerequisites/topic/area. relationship_annotation_training có Exercise_A/B và rating, không tự coi rating là directed gold DAG. Cần chốt hướng/threshold/aggregation và cycle handling riêng trước graph-quality comparison. Không đọc relationship_annotation_testing để học graph.

Đề xuất bước đầu chỉ descriptive, không train model. Chọn một outer fold và chỉ inner-train learners từ assignments frozen. Cố định hash-selected cohort tối đa32learners, tối đa120events chronological/learner. Dùng user_id/exercise/time_done/source_row. Không cần labels correct để đo order. Không query Holdout hoặc outer/inner validation. DuckDB512MB, threads2, timeout120s, kết quả chỉ aggregate/privacy-safe cohort hash.

Mỗi cạnh u→v đo số learner quan sát cả hai, số first(u)<first(v), đảo chiều và exposure support. Báo missing endpoint/zero support và phân bố theo topic/area. Đây là first-exposure order alignment, không trực tiếp là predictive benefit hay instructional effect. Cần kiểm biến thể nearest preceding exposures nếu câu hỏi scientific yêu cầu, đăng ký trước analysis.

Negative controls gồm empty graph, reversed-edge sensitivity có cycle audit, constrained rewiring giữ in/out-degree và topic-pair counts, và support-bin matching dùng train-only exposure counts. Junyi dùng topic/area, không gọi đó là chapter Grade10. Tool hiện có degree/chapter matching nhưng chưa support-bin matching. Order-derived placebo graph fit từ inner-train, mọi evaluation predictive sau đó phải trên learner tách biệt.

Acceptance cho descriptive run là chronology/scope đúng, target cap và số learner khớp, không xuất raw learner IDs, manifest/hash/note đầy đủ. Mọi causal instructional claim trên Junyi vẫn không được nhận dạng từ logged-order contrast này.

## Quyết định cần chốt

Chốt scope/cells ablation, lambda intervention và primary outcome; chốt cách dựng Junyi graph, outer fold/cohort và train-only support bins; chốt statistical families và final seeds. Có thể viết unit tests và chuẩn bị adapter trước quyết định, chưa phát hành kết luận từ phương pháp chưa chốt.
