# RQ1–RQ2 — kiểm chéo và làm rõ bằng chứng đã lưu ngày17/11

Lượt này thực hiện theo phân công root trong lúc sao lưu Drive. Toàn bộ công việc là đọc lại cached CSV/JSON, giữ source/artifact gốc. Các báo cáo chẩn đoán trước được kế thừa. Đây là refinement hậu nghiệm của bằng chứng hiện có.

## Kết quả đã kiểm

- RQ1 có60cặp readyđổi, trong đó5previewđổi/55giữ. Có1020cặp readygiữ, trong đó17previewđổi/1003giữ. Phân tích từng dòng CSV khớp joint PMRA đã nghiệm thu. Các số964/90/60/22 đo các biến riêng của snapshot.
- RQ2 có58/60cặp lambdaoff/on giữ cùng nguyên chuỗi query/correct/probability/step trong120bước. Ability1150/1300 có20/20cặp mỗi mức giống nhau. Tuy nhiên, ở1150 latentgainλon−off âm trong20/20cặp. Điều này làm rõ contrast latentworld và khả năng quan sát/điều chỉnh của KT/controller trong horizon đã chạy.
- Numeric checker xác nhận120outcome keys,60Q,30K và coupling identities. Kiểm Decimal có sai số lớn nhất2,455×10⁻¹⁵ trên thangElo. Kiểm phụ dùng canonical digest toànchuỗi và đếm chéo từCSV, không import analyzer chính.

Pilot có9cụm seed–hồ sơ nằm trong3seedfamilies. Độ phụ thuộc giữa các hồ sơ cùng family cần được giữ khi suy luận. Lượt này chỉ báo số đếm/tỷ lệ mô tả cho pilot. Fresh120 giữ10pairedseedblocks theo thiết kế gốc. 7200vịtrí so cặp chỉ là số đo mô tả theo thời gian. Chưa có thí nghiệm mới hoặc nghiệm thu hoàn tất RQ.

## Chỉ mục file

| File | Vai trò |
|---|---|
| `SPEC.md` | Câu hỏi và phạm vi hậu nghiệm trước các phép đọc lại tương ứng |
| `analyze_cached_evidence.py` | CSV↔PMRA, Q từ outcomes, K từQ, Decimal |
| `audit_lambda_observables.py` | Ghép parent61/child59, đối chiếu60cặpλ; loại parentpartialF062 |
| `check_cached_results.py` | Checker phụ bằng digest canonical và số đếm CSV |
| `INPUTS.json` | SHA input cached nhỏ và số byte |
| `RESULTS.json` | Aggregate mô tả RQ1/RQ2 |
| `NUMERIC_ACCEPTANCE.json` | Kiểm số học và nguồn trước/sau |
| `LAMBDA_OBSERVABLES.json` | Counts quan sát, SHA nguồn raw trace/ledger |
| `SECONDARY_CHECK.json` | Exact observable sequences và latent-on/off contrast |
| `rq1_conditionals.csv` | Mẫu số và đếm bảng chéo |
| `rq2_block_contrasts.csv` | Đủ30block×ability contrasts |
| `rq2_ability_summary.csv` | Qoff/Qon/K và vị trí đổi câu theo ability |
| `lambda_observable_pairs.csv` | Đủ60cặpλ, đếm query/label/probability khác |
| `rq1-ready-preview-v01.svg/png/json` | Figure độc lập, nguồn và giới hạn |
| `build_ready_preview_figure.py` | Nguồn dựng figure từCSV |

Các file `*_execution.txt` và `execution.txt` giữ output terminal. Báo cáo phân tích đọc được tại [RQ12_EXISTING_EVIDENCE_20261117.md](../../reports/RQ12_EXISTING_EVIDENCE_20261117.md).

## Dựng và kiểm lại

Dùng `.venv/Scripts/python.exe -B` với từng script. Analyzer từ chối ghi đè các output đã có để giữ bundle. Muốn dựng lại, tạo run mới hoặc sao source sang vùng runtime riêng rồi thay HERE cho đích mới. Figure có dữ liệuCSV, SVGtext giữ được tiếngViệt và quy ước trình bày `figures4papers` đã dùng trong các figureAKT trước, ghi tham chiếu license/source trongJSON.

Không dùng UI/browser hoặc máy chủ preview ở lượt này. PNG đã được mở trực tiếp để kiểm bố cục. Nguồn dữ liệu lịch sử và simulator được giữ nguyên. Không đưa SHA hoặc paths kỹ thuật vào nội dung báo cáo GVHD, root sẽ tích hợp kết quả theo mạch nghiên cứu.
