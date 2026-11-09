# Outer publication Gate07 — source handoff

10/11/2026. Chưa chạy Python/AST, owned process, preflight/Git, publisher hoặc viết index. Full Gate07 của ROOT đang ở lượt riêng. Không có SHA actual outer/report/log mới được gán trong source prep này.

`run_publish_gate07_main_index01.py` SHAa1c4738d2f1aa4028a51c9d6ed13805a4d248d515f38241e88f64f7dc9a90818. Derive từ old outer05 SHAbfd34eed3dd7fbbf536ad7fafa3cac2ed8daa466267d9256ef9d20ec8fa23def, giữ nguyên old source. Worker mới được ghim SHA340af758aca41252dcb99f28ede0894744961237086d1f6b3902cd53c2e135c2.

Diff chỉ đổi fixed Gate07 paths/status/worker pin, chuyển các Gate input SHA/build-map SHA/global-pointer SHA cũ thành required CLI arguments. Prefix `--gate-...` tách rõ source controller của full Gate với `--controller-sha256` của publication outer. Không có SHA placeholder/default cho actual Gate tương lai.

Giữ whole30/owned≤27 gồm cleanup3/worker24, original helper0dc, per-process RSS1GiB và free floor2GiB được monitor. Đây là polling resource profile cũ, không hard OS memory quota hoặc instantaneous whole-family summed peak. Giữ exact original10Git commands trong worker, source/data/network/import guards và independent outer public reader.

Caller profile được kiểm trước thay đổi. Chỉ `GH_PAGER`/`GIT_PAGER` thuộc display variables đã duyệt được loại tạm thời, các Git/GH biến khác phải khớp reviewed profile hoặc bị từ chối. Ba Git config vẫn là fsmonitor=false, safe.directory đúng physical upstream và autocrlf=true. Environment caller được restore trong finally. Runtime packet e4d97a... và actual accepted schema2 receipt a5fb17... là hồ sơ đã tồn tại, không viết lại. Outer mới cố ý dùng cùng schema2 runtime3fddd... đã được actual runtime acceptance đó ghim.

Worker viết exclusive index mới `artifacts/akt/preflight/gate2-main183-win-current-gate-20261110-07.json` sau genuine preflight, rồi public reader và all-input/source/global-pointer posthash. Outer kiểm lại exact năm trường index và gọi public reader độc lập. Nếu postcheck thất bại, giữ files rejected, không sửa report/index thành PASS hoặc thay global pointer. Không chạy lại suite để tạo index.

## ROOT command sau actual accepted Gate và source review

Các dấu `<...>` phải được ROOT thay bằng SHA actual đã kiểm. Không dispatch khi full Gate chưa accepted.

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_publish_gate07_main_index01.py --controller-sha256 a1c4738d2f1aa4028a51c9d6ed13805a4d248d515f38241e88f64f7dc9a90818 --gate-outer-receipt-sha256 <ACTUAL_ACCEPTED_GATE07_OUTER_SHA> --gate-report-sha256 <ACTUAL_GATE07_REPORT_SHA> --gate-log-sha256 <ACTUAL_GATE07_LOG_SHA> --gate-packet-sha256 7f4e9f405d886bf4bbd5ee01b55407a0c45d2d061f9586a5843135c6ca3d8fce --gate-worker-sha256 ba0f288de881eb17a315eda844753f9dc7f8363b43bb012957509b620602d729 --gate-controller-sha256 0fb3c15e940f2425ef4599d2329a2675a50c9436a0a2c1cacc1bc674b0555a3d --gate-runtime-sha256 3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b --gate-lock-sha256 3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a --build-map-sha256 <ACTUAL_CANONICAL_REPORT_BUILD_MAP_SHA> --global-pointer-sha256 <ACTUAL_GLOBAL_POINTER_BEFORE_SHA> --approval-reference <ROOT_PUBLICATION_REVIEW_REFERENCE>
```

Output mới chỉ xuất hiện khi ROOT chạy. Các path là `P/gate07-main-index-publication01-owned/final.json`, `P/gate07-main-index-publication01/result.json` và index mới. Trước lượt này cả ba chưa có. Publication chỉ xác nhận metadata index, không cấp main fit/resume/GPU authority.

## Review prose E11 riêng

Đã đọc mục14 của `research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md`, SHAf271493ef805ca55a2b99e0e95f2cb9346b94ccefa62a9edca9671be0739cb9d, cùng writing bundle/source map, descriptive statistics và independent review SHAd75d20fff7686dd68d8910a606c44e6a3d51393955b283c81938722c627fc68a.

Scoped prose PASS, chưa thấy material correction. Các K means/ranges/signs làm tròn khớp nguồn. Công thức expert−learned và lambda-on−off rõ, không dùng parallel-trends trên người học. Mười paired seed blocks tách khỏi120worlds/14.400responses; giữ một learned artifact cố định, initial-state proof mới và không pooling với E9. High K=0 được mô tả là control bất hoạt, không phủ nhận Q còn khác0. Ordinal pairs sau phân kỳ không bị dùng như shared-target LL. Logical120 tách physical121/replay30. Không thêm CI/p-value, RQ completion hoặc model efficacy. Đây là review văn bản và metadata nguồn, không chạy lại thí nghiệm hoặc kiểm thống kê mới.
