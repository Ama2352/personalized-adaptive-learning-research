# GRAPH13 — kernel thống kê và lượt kiểm thuần đề xuất01

## Phạm vi đã đóng băng trước chạy

Chỉ hai file mới: `src/knowledge_tracing/research_selection.py` và `tests/shared_kt/test_research_selection.py`. Chưa import, chạy Python, chạy test hoặc mở prediction/corpus thật trong lúc chuẩn bị. Không sửa reader/model/trainer/source cũ, không làm external freeze và không thực hiện Git.

Kernel nhận đủ thống kê trên U chung đã được caller chứng nhận cho A0/A1_EXPERT/A1_LEARNED/A3_EXPERT/A3_LEARNED: mỗi học viên một count và năm tổng LL. Cả năm count phải bằng nhau. Học viên không góp dòng U được ghi trong coverage riêng, không đưa vào clusters bootstrap. Caller vẫn phải chứng nhận query key, label, domain/phase và toàn bộ chín candidate trước mọi main refit; kernel không chứng nhận những điều này và luôn trả `STATISTICS_ONLY_NO_EXTERNAL_FREEZE`/`external_freeze_authority=False`. Cả A2/SAKT/GKT vẫn nằm trong required allocation.

## Thuật toán hữu hạn

- Nhãn đúng/sai và xác suất binary64 finite được kiểm kiểu chính xác. Tạo hai xác suất `(1-p,p)` rồi clip riêng bằng epsilon binary64 trước `-math.log`. Sáu known-answer LL trong test được chép nguyên labels/p/mean từ `reporting-loss-parity01.json` SHA110d998297ac96e37e2c0bba03053085eee52ea3e5e6508b31d824f24d712e5f. Không gọi sklearn/NumPy để chạy lại baseline.
- Ước lượng là response-pooled LL: `fsum(per-learner_loss_sums)/sum(counts)`. Các tổng học viên đã được làm tròn binary64 nên có thể khác bit cuối so với cộng trực tiếp toàn bộ loss từng dòng/sklearn mean. Tolerance fixture đã định trước là absolute1e-12, không relative; không làm tròn và không thêm epsilon vào eligibility.
- Sắp learner ID theo thứ tự Python codepoint; một `random.Random(42)` riêng. 2.000 lần lấy mẫu n clusters có hoàn lại, dùng CHUNG multiplicities cho năm mô hình. Mỗi lần cộng loss/count có trọng số số dòng rồi lấy chênh với A0. Lưu SHA của header canonicalJSON + từng mảng chỉ số canonicalJSON có LF, không giữ chín bảng prediction đầy đủ.
- Type7 q.025/.975; graph eligible khi upper.975 thật sự `<0`. Trong các graph eligible, chọn minimum point LL; tie dùng candidate ID. Không có eligible thì chỉ đề xuất A0. U toàn cục rỗng bị reject, không tạo quyết định A0. n=1 được phép nhưng đánh dấu conditional_single_learner, không bằng chứng nhiều seed độc lập.
- Caller truyền cap số learner/full/common rows/index requests/work units/thời gian. Index requests chính xác `2000*n`; work units `5*n+2000*(7*n+4)+4`, không là số CPU instructions. Clock kiểm trước/sau stages và sau quantiles/winner; không giảm R để né cap. Đây là cooperative time guard, không hardkill/RAM attestation. ROOT launcher/owned Job cung cấp giới hạn process riêng.

## Tám ca thuần dự kiến, chưa có kết quả chạy

1. Sáu LL known-answer và type7; xác suất/label sai kiểu bị reject.
2. Cluster1/9dòng: pooledΔ+.09 khác macroΔ−.35; draws manufactured chung cho CIknown-answer−.9/.2 và kiểm đúng4.000 index requests.
3. Một cluster, tie strictnegative, negative gần zero không bị epsilon xóa; zero-contributor nằm ngoài draws; SHA trường hợp toàn[0] biết trước.
4. Equal/worse: upper0 không eligible, fallback A0 không tạo authority/all-nine admission.
5. Learner/candidate order bất biến, RNG global không đổi, đúng2.000draws/seed42.
6. U rỗng/duplicate/candidate thiếu/count mismatch/NaN/Inf/bool/coverage conflict fail closed.
7. Cap không đủ bị reject TRƯỚC private RNG, không giảm số draws.
8. Clock tăng sau quantile cuối: reject resource dù đã đủ draws, không false-complete/proposed winner.

Nếu toàn bộ ca đi hết theo source: sáu lần bootstrap (một dùng fake draws để known-answer), tổng12.000 replicate,18.000 index requests/174.069 work units. Các ca invalid khác phải dừng trước RNG. Đây là workload phần mềm, không researchN/CI từ dữ liệu nghiên cứu.

## Lượt ROOT được đề xuất

Controller `check_research_selection01.py` chạy cold import rồi đúng8unittest, sources SHA trước/sau, cấm imports scientific/model, cấm Popen/network và mở corpus/dataset/runs/experiments. Worker chỉ dùng stdlib; helper ownership có sẵn dùng psutil ở parent, không cài dependency. Không thay metadata Windows hoặc monkeypatch global clock; ca late clock chỉ đổi private `_clock` của kernel rồi restore.

Whole cap30s tính cả source checks/owned cleanup/finalization; cleanup reserve2s, giữ1s ngoài helper để kiểm và ghi verdict. Không retry tự động. Output mới duy nhất `research-selection-pure-capture01` và `research-selection-pure-owned01`; nếu đã tồn tại thì STOP.

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/check_research_selection01.py --approval-reference ROOT_REVIEWED_GRAPH13_STAT_KERNEL_PURE8_01
```

ROOT cần review pins/controller trước dispatch. Chưa có thực nghiệm selector từ CSV, terminal admission của9candidate, external freeze trên đĩa, refit hoặc efficacy. Công thức LL baseline đã được ROOT xác nhận riêng không đồng nghĩa kernel/test mới đã PASS.
