# Gỡ đúng file trong allowlist đã hash/backup; không dùng xóa đệ quy.
param([string]$PlanFile='DELETE_PLAN.json', [string]$LogStem='UNLINK', [string]$AcceptanceFile='DRIVE_ACCEPTANCE.json', [string]$EvidenceBundle=$PSScriptRoot)
$ErrorActionPreference = 'Stop'
$bundlePath = [IO.Path]::GetFullPath($EvidenceBundle)
$workspacePath = [IO.Path]::GetFullPath((Join-Path $bundlePath '..\..\..')).TrimEnd('\')
$planPath = Join-Path $bundlePath $PlanFile
$plan = Get-Content -LiteralPath $planPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($plan.status -notin @('READY_FOR_AUTHORIZED_DUPLICATE_UNLINK','READY_FOR_AUTHORIZED_BULK_OFFLOAD_UNLINK')) { throw 'Plan chưa đủ nghiệm thu.' }
if (-not [string]::Equals($workspacePath, $plan.root, [StringComparison]::OrdinalIgnoreCase)) { throw 'Workspace không khớp.' }
$remote = Get-Content -LiteralPath (Join-Path $bundlePath $AcceptanceFile) -Raw -Encoding UTF8 | ConvertFrom-Json
if ($remote.status -notin @('REMOTE_ARCHIVE_SHA256_SIZE_OWNER_PARENT_VERIFIED','ALL_BULK_REFERENCES_AND_NEW_ARCHIVES_VERIFIED')) { throw 'Chưa backup Drive.' }
$protected = Get-Content -LiteralPath (Join-Path $bundlePath 'PROTECTED_BEFORE.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$protectedSet = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($row in $protected.files) { [void]$protectedSet.Add($row.path) }
$allowedRoots = @($plan.allowed_roots | ForEach-Object { [IO.Path]::GetFullPath($_).TrimEnd('\') + '\' })
$seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$checkedDirectories = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$logPath = Join-Path $bundlePath ($LogStem + '_LOG.jsonl')
if (Test-Path -LiteralPath $logPath) { throw 'Không ghi đè nhật ký gỡ cũ.' }
$diskBefore = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($workspacePath)).AvailableFreeSpace
$deleted = 0
$deletedBytes = [long]0
$failures = 0
$writer = [IO.StreamWriter]::new($logPath, $false, [Text.UTF8Encoding]::new($false))
try {
    # Kiểm toàn allowlist trước khi gỡ file đầu tiên.
    foreach ($row in $plan.files) {
        $targetPath = [IO.Path]::GetFullPath((Join-Path $workspacePath $row.path))
        if (-not $targetPath.StartsWith($workspacePath + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Đích ngoài workspace.' }
        $isAllowed = $false
        foreach ($allow in $allowedRoots) { if ($targetPath.StartsWith($allow, [StringComparison]::OrdinalIgnoreCase)) { $isAllowed = $true; break } }
        if (-not $isAllowed -or $protectedSet.Contains($row.path) -or -not $seen.Add($targetPath)) { throw 'Allowlist không hợp lệ.' }
        if ($row.path -match '^(dataset|venv|\.venv|\.wsl|\.git|research_tracking|src|scripts|tests|third_party)/' -or $row.path -match '^artifacts/(bkt_baseline|akt/private)/') { throw 'Đích thuộc vùng bảo vệ.' }
        $parentPath = [IO.Path]::GetDirectoryName($targetPath)
        while ($parentPath -and $parentPath.Length -ge $workspacePath.Length) {
            if ($checkedDirectories.Contains($parentPath)) { break }
            $parentOperation = if ($parentPath.Length -ge 240) { '\\?\' + $parentPath } else { $parentPath }
            $dirItem = Get-Item -LiteralPath $parentOperation -Force
            if (($dirItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Không gỡ qua junction/symlink.' }
            [void]$checkedDirectories.Add($parentPath)
            $parentPath = [IO.Path]::GetDirectoryName($parentPath)
        }
        $operationPath = if ($targetPath.Length -ge 240) { '\\?\' + $targetPath } else { $targetPath }
        $item = Get-Item -LiteralPath $operationPath -Force
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $item.Length -ne [long]$row.bytes) { throw 'File khác inventory.' }
    }
    foreach ($row in $plan.files) {
        $targetPath = [IO.Path]::GetFullPath((Join-Path $workspacePath $row.path))
        try {
            $operationPath = if ($targetPath.Length -ge 240) { '\\?\' + $targetPath } else { $targetPath }
            $item = Get-Item -LiteralPath $operationPath -Force
            # Python mtime_ns và NTFS ticks có cùng độ phân giải100ns.
            $expectedTicks = [long]([decimal]$row.mtime_ns / 100) + [long]621355968000000000
            if ($item.Length -ne [long]$row.bytes -or $item.LastWriteTimeUtc.Ticks -ne $expectedTicks) { throw 'File đã thay đổi sau hash; giữ nguyên.' }
            if ($row.keeper) {
                $keeperPath = [IO.Path]::GetFullPath((Join-Path $workspacePath $row.keeper))
                if (-not $keeperPath.StartsWith($workspacePath + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Keeper ngoài workspace.' }
                $keeper = Get-Item -LiteralPath $keeperPath -Force
                if ($keeper.Length -ne [long]$row.bytes -or $seen.Contains($keeperPath)) { throw 'Keeper không hợp lệ hoặc cũng bị gỡ.' }
            }
            Remove-Item -LiteralPath $operationPath -Force
            if (Test-Path -LiteralPath $operationPath) { throw 'File còn tồn tại sau gỡ.' }
            $deleted++
            $deletedBytes += [long]$row.bytes
            $writer.WriteLine((@{path=$row.path;status='DELETED';bytes=$row.bytes;sha256=$row.sha256;category=$row.category} | ConvertTo-Json -Compress))
        } catch {
            $failures++
            $writer.WriteLine((@{path=$row.path;status='KEPT_ON_ERROR';error=$_.Exception.Message} | ConvertTo-Json -Compress))
        }
        if (($deleted + $failures) % 2000 -eq 0) { $writer.Flush(); Write-Output "UNLINKED $deleted KEPT $failures" }
    }
} finally { $writer.Flush(); $writer.Dispose() }
$diskAfter = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($workspacePath)).AvailableFreeSpace
$summary = @{status='AUTHORIZED_ALLOWLIST_UNLINK_FINISHED';files_deleted=$deleted;files_kept_on_error=$failures;logical_deleted_bytes=$deletedBytes;disk_before_bytes=$diskBefore;disk_after_bytes=$diskAfter;measured_free_delta_bytes=($diskAfter-$diskBefore);plan_sha256=(Get-FileHash -LiteralPath $planPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $bundlePath ($LogStem + '_SUMMARY.json')) -Encoding UTF8
$summary | ConvertTo-Json -Compress
