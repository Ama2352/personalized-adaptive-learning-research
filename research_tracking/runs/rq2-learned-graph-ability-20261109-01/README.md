# RQ2 — nguồn đồ thị learned trong controlled ability world

19 world hoàn tất gồm18 learned và1 expert sentinel. Ba seedblocks được dùng lại,
new independent N bằng0. Q18/K9 giữ toàn bộ dấu và zero. Scope là native GAM,
không neural fit hoặc hoàn tất RQ2/RQ3. Có2280 adaptive policy updates thực tế.

Đọc report_draft.md, native__graph_source_contrasts.json,
native__conditional_lambda_contrasts.json và independent_verification.json.
19 initial snapshots cùng raw observables/oracle/endpoints giữ ở scientific output,
được dẫn bằng SHA/size trong reference_sources.json. Oracle chỉ là evaluator/world.

Old initial state có scope SOURCE_RECONSTRUCTED_INITIAL_STATE, không có raw old
initial-policy hash. Sentinel120rows và endpoint exact là điều kiện ghép. Learned
confidence không P(edge true), không được dùng làm GAM weights. Không causal/human,
CI/p-value, graph-quality ranking hoặc true-graph recovery claim.

verify_results.ps1 là mã kiểm metadata sau run, không phải preregistration.
Archiver chỉ đóng bằng chứng có sẵn, không chạy lại world/model.
