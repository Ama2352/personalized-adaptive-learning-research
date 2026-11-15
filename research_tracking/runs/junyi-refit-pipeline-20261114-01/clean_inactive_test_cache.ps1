# Dọn fixture pytest cũ theo inventory đã kiểm; giữ nguyên các vùng nghiên cứu.
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path -LiteralPath 'D:\Dev\KLTN').Path
$bundle = Join-Path $workspace 'research_tracking\runs\junyi-refit-pipeline-20261114-01'
$base = (Resolve-Path -LiteralPath (Join-Path $workspace 'artifacts\akt\test-temp')).Path
$expectedBase = [System.IO.Path]::GetFullPath((Join-Path $workspace 'artifacts\akt\test-temp'))
if ($base -ne $expectedBase) { throw 'Đường dẫn cache khác vùng dự kiến' }
$planPath = Join-Path $bundle 'disk-cleanup-ready-20261116-01.json'
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if ($plan.status -ne 'CACHE_CLEANUP_VERIFIED_READY') { throw 'Thiếu nghiệm thu cache' }
$inventory = Join-Path $workspace $plan.input_inventory
$archive = Join-Path $workspace $plan.preserved_archive
if ((Get-FileHash -LiteralPath $inventory -Algorithm SHA256).Hash -ne $plan.input_inventory_sha256) { throw 'Inventory thay đổi' }
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $plan.preserved_archive_sha256) { throw 'Archive log thay đổi' }
$receiptPath = Join-Path $bundle 'disk-cleanup-result-20261116-01.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Đợt dọn đã có kết quả, cần đọc lại' }
$freeBefore = (Get-PSDrive -Name D).Free
$results = @()
foreach ($candidate in $plan.targets) {
    $target = [System.IO.Path]::GetFullPath($candidate.path)
    $prefix = $base + [System.IO.Path]::DirectorySeparatorChar
    if (-not $target.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Target ra ngoài vùng cache' }
    if ([System.IO.Path]::GetDirectoryName($target) -ne $base) { throw 'Target không phải thư mục con trực tiếp' }
    $item = Get-Item -LiteralPath $target -Force
    if (-not $item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { throw 'Target không phải thư mục thường' }
    $currentFiles = @(Get-ChildItem -LiteralPath $target -Recurse -Force -File)
    if ($currentFiles.Count -ne $candidate.files) { throw 'Cache thay đổi sau kiểm kê' }
    if (($currentFiles | Measure-Object -Property Length -Sum).Sum -ne $candidate.bytes) { throw 'Dung lượng cache thay đổi' }
    try {
        Remove-Item -LiteralPath $target -Recurse -Force
        $results += [ordered]@{path=$target; status='REMOVED_INACTIVE_PYTEST_FIXTURE'; bytes=$candidate.bytes; files=$candidate.files}
    } catch {
        $results += [ordered]@{path=$target; status='ERROR_PRESERVED_REMAINDER'; error=$_.Exception.Message}
        break
    }
}
$freeAfter = (Get-PSDrive -Name D).Free
$receipt = [ordered]@{
    status='BOUNDED_CACHE_CLEANUP_FINISHED'
    observed_at_utc=[DateTime]::UtcNow.ToString('o')
    free_before_bytes=$freeBefore
    free_after_bytes=$freeAfter
    observed_free_increase_bytes=($freeAfter-$freeBefore)
    preserved_archive=$plan.preserved_archive
    preserved_archive_sha256=$plan.preserved_archive_sha256
    input_inventory=$plan.input_inventory
    input_inventory_sha256=$plan.input_inventory_sha256
    results=$results
}
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding utf8
[pscustomobject]$receipt | Select-Object status,free_before_bytes,free_after_bytes,observed_free_increase_bytes | ConvertTo-Json
