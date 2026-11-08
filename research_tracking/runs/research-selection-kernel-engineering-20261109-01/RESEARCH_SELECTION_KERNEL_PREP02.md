# GRAPH13 — sửa fixture percentile và mã thoát unittest, revision02

Lần01 đã được ROOT chạy: terminalRC1, whole0.8424742s/30. Log unittest ghi8cases,7PASS/1FAIL; sáu LLknown-answer đã đi qua, thất bại duy nhất là assert exact `.75` so với type7 binary64 `.7500000000000001`. Đây là assertion fixture quá chặt, không phải lỗi thuật toán kernel/eligibility. Giữ nguyên final01 với counts=null; không ghi đè thành PASS. Worker-result01 vẫn có source_after khớp toàn bộ pins lúc chạy.

Trước sửa đã chụp `pre-research-selection-quantile-exit-fix01/test_research_selection.py.before` SHA3aad1836195b65824d342a766673ab664e584f0fd6328468bb4098487e191839 và controller01 SHA728437890245e8828a01bb3606282a8b899d3da75e067e14b76a1a8309e03997. Inventory-before ghi toàn bộ raw01; copy-verification chứng minh source_before=copy=source_after. Raw01/controller01/source-freeze01/plan01 không sửa.

Thay đổi duy nhất trong test: hai known-answer type7 dùng absolute tolerance1e-14. Không đổi sáu LLfixtures/tolerance1e-12; strict CIupper<0 và ca tinynegative không thay. Kernel vẫn SHA0e3cf12d15626a76000c6cdc04779ac769806aae2a5e52f769d4c70f3580a348.

Controller02 dùng đường dẫn exclusive mới. Sửa latentexit: SystemExit(None)→0, bool→int, int giữ nguyên; kiểu khác bị reject. Worker ghi cả raw_exit_type/raw_exit_value cùng normalized_returncode; ROOT comparator kiểm provenance này. Chưa quan sát một success path mới, không tuyên bố latentfix đã PASS. Vẫn bắt buộc đúng8/OK/no-skips, sources trước/sau, cold stdlib, ownedJob cleanup0 và toàn bộ guard cũ.

Allocation mới30s được cộng vào0.8424742s đã dùng: ceiling30.8424742s, không reset lịch sử. Không retry tự động. Source-only, chưa import/test/execute/Git ở revision02.

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/check_research_selection02.py --approval-reference ROOT_REVIEWED_GRAPH13_STAT_KERNEL_PURE8_02
```

Output dự kiến riêng `research-selection-pure-capture02` và `research-selection-pure-owned02`. ROOT review và dispatch; không actual selection/corpus/model/external freeze/main refit.
