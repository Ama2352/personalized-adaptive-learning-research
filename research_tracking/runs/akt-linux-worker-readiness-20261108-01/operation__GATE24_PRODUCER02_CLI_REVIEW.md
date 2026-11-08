# Gate24 producer02: bổ sung ba LF audit arguments

Parent read-only review tìm được blocker **trước Gate dispatch**: producer01 không truyền ba arguments LF audit mà driver bắt buộc. Producer01 được giữ nguyên vì Delta request đã hợp lệ/được root thực thi; không sửa lịch sử hoặc gọi đó là actual Gate failure.8metadata tests trước đó **không kiểm producer CLI**, nên không phải bằng chứng wiring này đã đúng.

**Producer dùng cho Gate hiện tại:** `prepare_source_delta_gate24_request02.py`, SHA `5c3b63fdf82f88b03dd9fdfaa18e8bba1af2d15422fe7831c25ed4016218b8a5`. Chỉ thêm LF receipt/path/SHA/status checks, wiring vào generated argv và exclusive Gate request02/contract02. Delta source04392264… và Gate driver3c4cb7c1… không đổi.

One pure parser-contract unittest PASS0,021giây/controller0,469968giây, receipt `gate24-producer02-cli-check01/run.json`. Nó lấy đúng parser statements của frozen driver, nhận đủ generated argv; negative bỏ ba LF flags bị argparse exit2 như yêu cầu. Không gọi producer/driver operation main, không tạo request, mutate fixture hoặc chạy native suite/model. Không fake RED Gate.

Sau khi root nhận/verify actual new materialization02 và Delta result JSON, chạy producer02 với các flags đã nêu ở spec01, **thêm bốn flags local**:

```powershell
$lf = "$work/received/post-checkout-audit01-result.json"
$lfHash = (Get-FileHash -LiteralPath $lf -Algorithm SHA256).Hash.ToLowerInvariant()
$lfStatus = (Get-Content -LiteralPath $lf -Raw | ConvertFrom-Json).status
# Thêm vào command --operation gate24 của producer02:
# --upstream-audit-receipt $lf
# --upstream-audit-relative-path 'post-checkout-audit01/result.json'
# --expected-upstream-audit-sha256 $lfHash
# --accepted-upstream-audit-status $lfStatus
```

Producer yêu cầu actual LF receipt1f116d3… và đúng status `VERIFIED_LOCAL_DERIVED_LF_UPSTREAM_READONLY_NOT_LINUX_GATE`, không tạo receipt từ summary. Generated driver argv có `--upstream-audit-path`, `--upstream-audit-sha256`, `--upstream-audit-status`. Loader receipt vẫn là actual transfer03/source04; tất cả actual hashes lấy từ nguyên file local đã verify, không chép terminal. Output mới `requests/gpu09-add-linux-gate24-02.json`, contract `linux-gate24-request02-contract.json`, executed=false. Đây vẫn chỉ prepare; root review/dispatch riêng với MCP660s/native600/outer630, expected771 và prior runtime02 reuse.
