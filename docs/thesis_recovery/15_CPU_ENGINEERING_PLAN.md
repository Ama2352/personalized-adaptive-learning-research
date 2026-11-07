# Vòng engineering CPU và tổ chức bằng chứng

Ngày 07/11/2026. User cho phép triển khai các phần local/Colab CPU, sắp xếp file và commit các thay đổi hoàn thiện. Dùng .venv. Không tự đổi phương pháp đã duyệt, truy cập Holdout hoặc chạy full CV/GPU.

## Backlog và nghiệm thu

| ID | Phần việc | Phụ thuộc | Nghiệm thu |
|---|---|---|---|
| CPU01 | Kiểm kê 419 file untracked, phân biệt nguồn/tài liệu/file tạm | Không | Inventory có hash, chuyển file tạm có đối chiếu, commit có phạm vi |
| CPU02 | Chuẩn bằng chứng trong research_tracking/runs | CPU01 | Mỗi run có manifest, nguồn/hash, outputs, log và README tiếng Việt |
| CPU03 | Adapter tham chiếu Paper2 bằng AST allowlist | CPU02 | Không execute download/install hoặc toàn notebook, giữ hash từng definition |
| CPU04 | RQ1 fixed-stream trace GAM/Graph-GAM/empty-graph package | CPU03 | Predict-before-update, cùng events, explicit mastery boolean đúng source, action preview không đổi state |
| CPU05 | Retention source fixture vào evidence bundle | CPU02 | Algebra khớp actual theta_at, ghi giới hạn metric và điều kiện |
| CPU06 | Null graph khớp degree và chapter | CPU02 | DAG, node set/in/out-degree/chapter-pair counts giữ nguyên, exact requested swaps hoặc raise |
| CPU07 | Bounded diagnostic runs và test regression | CPU04–06 | Artifact complete, replay deterministic, ghi negative/positive/inconclusive đúng phạm vi |
| CPU08 | Paper1 controller/source-PDF reconciliation | CPU01 | Tìm đúng revision hoặc ghi blocker, không gọi toy counterexample là reproduction |
| CPU09 | Controlled ability factorial và package pathway ablations | CPU03–07 | Đặc tả intervention/mastery/controller/estimand được chốt trước so sánh kết luận |
| CPU10 | Junyi order-controls và inferential experiment | CPU06, accepted protocol | Train-only graph statistics, target/learner boundary, learner-level inference |
| CPU11 | AKT CLI/refit recovery và CPU regression | Source identity hiện tại | Lifecycle synthetic, full execution gates giữ nguyên |

Đây là thứ tự phụ thuộc, không tuyên bố tất cả đã hoàn thành. CPU09/10 cần chốt phương pháp. Bounded historical-source diagnostics CPU03–07 được thực hiện theo chỉ thị hiện tại. Không chạy lại toàn Paper1/2.

## Nơi lưu

Source ở src/knowledge_tracing, tests ở tests/shared_kt, entrypoint ở scripts/research. research_tracking là chỉ mục nghiên cứu. Chỉ thêm một cây runs, mỗi thư mục tương ứng một run ID bất biến. docs/thesis_recovery giữ kế hoạch và engineering test logs có trước. File tạm pytest chuyển về artifacts/akt/local-tests bằng relocation manifest. Artifact lịch sử giữ vị trí, chỉ mục tham chiếu đến chúng.

Mỗi README của run phải ghi câu hỏi, thiết kế, command, inputs, kết quả đo, claim được phép dùng, giới hạn và đường dẫn bảng/hình. Manifest ghi hashes của outputs và sources, Python executable, seed, cấu hình, Git HEAD trước run. Source chưa commit phải có hash riêng. Run thất bại được giữ log và status failed, rerun dùng ID mới.

## Dùng trong báo cáo cuối

Luận văn dẫn claim ID → run ID → bảng/kết quả → manifest/hash → source. Phân biệt bằng chứng kiểm phần mềm, chẩn đoán cơ chế và ước lượng hiệu quả thực nghiệm. Các run nhỏ chỉ là diagnostic/pilot, chưa đủ kết luận population hoặc causality. Kết quả retention algebra không chứng minh graph hữu ích hoặc mọi retention metric đều trùng.
