# Đóng gói fixture đã chạy, chỉ copy byte/SHA, không chạy lại test hoặc Git.
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$target = Join-Path $workspace 'research_tracking/runs/rq1-native-panel-recorder-engineering-20261110-01'
if (Test-Path -LiteralPath $target) { throw 'Bundle đã tồn tại' }
$selected = @(
    'native_panel_observer_candidate01.py',
    'test_native_panel_observer_candidate01.py',
    'run_native_panel_pure01.py',
    'RQ1_GLOBAL_CONCEPT_TIME_PANEL_AUDIT01.md',
    'native-panel-pure01/allocation.json',
    'native-panel-pure01/cases.jsonl',
    'native-panel-pure01/result.json',
    'native-panel-pure01/stderr.log',
    'native-panel-pure01/stdout.log',
    'archive_native_panel_candidate01.ps1'
)
function Pin([string]$path) {
    $item = Get-Item -LiteralPath $path
    if ($item.Length -gt 32768) { throw 'File vượt32KiB' }
    return @{ sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant(); bytes=$item.Length }
}
function Save([string]$name, $value) {
    $path = Join-Path $target $name
    if (Test-Path -LiteralPath $path) { throw 'Không ghi đè output' }
    [IO.File]::WriteAllText($path, ($value | ConvertTo-Json -Depth 12)+"`n", [Text.UTF8Encoding]::new($false))
}
$before = @{}
foreach ($name in $selected) { $before[$name] = Pin (Join-Path $PSScriptRoot $name) }
$result = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'native-panel-pure01/result.json') -Raw | ConvertFrom-Json
if ($result.status -cne 'ACCEPTED_SIX_MANUFACTURED_PANEL_FIXTURES' -or $result.counts.tests -ne 6 -or
    $result.counts.failures -ne 0 -or $result.counts.errors -ne 0 -or $result.counts.skipped -ne 0 -or
    $result.counts.expected_failures -ne 0 -or $result.counts.unexpected_successes -ne 0 -or
    $result.denied.Count -ne 0 -or $result.heavy_imports.Count -ne 0 -or $null -ne $result.error) { throw 'Không đủ acceptance fixture' }
$ids = @($result.collected_ids)
if ($ids.Count -ne 6 -or @($ids | Select-Object -Unique).Count -ne 6 -or
    ($ids -join "`n") -cne ($result.started_ids -join "`n") -or
    ($ids -join "`n") -cne ($result.completed_ids -join "`n")) { throw 'Không đủ6IDs exact' }
foreach ($name in @('native_panel_observer_candidate01.py','test_native_panel_observer_candidate01.py')) {
    if ($before[$name].sha256 -cne $result.source_before.$name -or
        $before[$name].sha256 -cne $result.source_after.$name) { throw 'Nguồn khác nguồn đã test' }
}
if ($before['run_native_panel_pure01.py'].sha256 -cne $result.runner_before_sha256 -or
    $result.runner_before_sha256 -cne $result.runner_after_sha256) { throw 'Runner drift' }
foreach ($property in $result.outputs.PSObject.Properties) {
    $actual = $before['native-panel-pure01/'+$property.Name]
    if ($actual.sha256 -cne $property.Value.sha256 -or $actual.bytes -ne $property.Value.bytes) { throw 'Raw output drift' }
}
New-Item -ItemType Directory -Path $target | Out-Null
Save 'inventory-before-copy.json' $before
$copies = @{}
foreach ($name in $selected) {
    $destinationName = $name.Replace('/', '__')
    $source = Join-Path $PSScriptRoot $name
    $destination = Join-Path $target $destinationName
    [IO.File]::Copy($source, $destination, $false)
    $copyPin = Pin $destination
    $afterPin = Pin $source
    if ($copyPin.sha256 -cne $before[$name].sha256 -or $afterPin.sha256 -cne $before[$name].sha256 -or
        $copyPin.bytes -ne $before[$name].bytes -or $afterPin.bytes -ne $before[$name].bytes) { throw 'SHA trước/copy/sau khác nhau' }
    $copies[$destinationName] = @{ source_relative=$name; before=$before[$name]; copy=$copyPin; after=$afterPin }
}
Save 'copy-verification.json' $copies
$note = @'
# Recorder native panel · kiểm engineering candidate

Sáu fixture dựng tay đã đạt, đủ sáu ID collected/started/completed, 0 failure/error/skip hoặc expected/unexpected. Raw result ghi 0,233953 giây trước ghi final. Root quan sát terminal khoảng0,309 giây. Các thời gian khác phạm vi, không cộng nhau. Không nạp framework, policy Paper2 thật, world hoặc oracle.

Candidate dự kiến ghi θ/π lưu/M từ first-pass getter sẵn có của ready_set, không thêm getter/predict/RNG/update. Đã kiểm trên fake3nodes, gồm fallback, ngưỡng binary64, lỗi first pass, rollback cài đặt và cancellation đi cùng lỗi cleanup. Các upper bounds10fakepolicies/14capture/44getter là giới hạn tĩnh, chưa là measured native ledger.

Đây là candidate trong prep. Chưa áp dụng canonical hoặc kiểm parity native 28concept. Chưa có latent toàn miền, chưa chạy global panel hoặc áp dụng phương pháp nghiên cứu mới. Audit sidecar môi trường vẫn là đề xuất. Không suy accuracy, calibration, hiệu quả hoặc hoàn tất RQ từ sáu fixture.

Inventory trước copy và proof copy/sau nằm trong bundle. Manifest completed chỉ xác nhận đóng gói hồ sơ. Nguồn và raw cũ giữ nguyên. Không có Git hoặc chạy lại test trong thao tác archive.
'@
[IO.File]::WriteAllText((Join-Path $target 'README.md'), $note+"`n", [Text.UTF8Encoding]::new($false))
$outputs = @{}
foreach ($file in Get-ChildItem -LiteralPath $target -File) { $outputs[$file.Name] = (Pin $file.FullName).sha256 }
Save 'manifest.json' @{ schema_version=1; status='completed'; kind='manufactured_native_panel_recorder_candidate_engineering';
    scientific_scope='CANDIDATE_ONLY_NOT_APPLIED_NO_NATIVE_PANEL_OR_TRUTH'; sources_before=$before;
    outputs_sha256=$outputs; tests=6; new_scientific_observations=0 }
foreach ($property in $outputs.GetEnumerator()) {
    if ((Pin (Join-Path $target $property.Key)).sha256 -cne $property.Value) { throw 'Manifest output mismatch' }
}
[PSCustomObject]@{ status='VERIFIED_ARCHIVE_ONLY'; manifest=(Pin (Join-Path $target 'manifest.json')).sha256; outputs=$outputs.Count; path=$target } | ConvertTo-Json
