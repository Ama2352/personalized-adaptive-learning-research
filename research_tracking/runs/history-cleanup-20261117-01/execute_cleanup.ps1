# Xóa đúng 35 archive qua 70 hardlink đã được user duyệt; mọi phép xóa dùng LiteralPath.
$ErrorActionPreference = 'Stop'
$repoRoot = 'D:\Dev\KLTN'
$bundle = Join-Path $repoRoot 'research_tracking\runs\history-cleanup-20261117-01'
$planPath = Join-Path $bundle 'DELETE_PLAN.json'
$journal = Join-Path $bundle 'DELETE_JOURNAL.jsonl'
$resultPath = Join-Path $bundle 'DELETE_RESULT.json'
if ((Test-Path -LiteralPath $journal) -or (Test-Path -LiteralPath $resultPath)) {
    throw 'Lượt dọn đã có nhật ký, phải đối chiếu trạng thái trước khi tiếp tục.'
}
$pin = Get-Content -LiteralPath (Join-Path $bundle 'PLAN_PIN.json') -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $planPath -Algorithm SHA256).Hash -ne $pin.sha256) { throw 'Plan đã đổi.' }
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if ($plan.groups.Count -ne 35 -or $plan.delete_paths -ne 70 -or $plan.remote_reverified -ne 35) { throw 'Sai phạm vi.' }
$originalPath = Join-Path $repoRoot 'experiments\akt\results\drive-offload-history-20261116-01\MANIFEST.json'
$original = Get-Content -LiteralPath $originalPath -Raw | ConvertFrom-Json
$expected = @()
foreach ($row in $original.files) {
    $expected += [IO.Path]::GetFullPath((Join-Path $repoRoot $row.source))
    $expected += [IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $originalPath) $row.upload_path))
}
$checked = @()
foreach ($group in $plan.groups) {
    foreach ($relative in $group.paths) {
        $target = [IO.Path]::GetFullPath((Join-Path $repoRoot $relative))
        if (-not $target.StartsWith($repoRoot + '\experiments\akt\results\', [StringComparison]::OrdinalIgnoreCase) -or
            $target -notin $expected -or [IO.Path]::GetExtension($target) -ne '.zip' -or
            [IO.Path]::GetFileName($target) -eq 'SUPPORT.zip') { throw "Ngoài allowlist archive: $target" }
        $item = Get-Item -LiteralPath $target -Force
        if ($item.PSIsContainer) { throw 'Chỉ được xóa file.' }
        $node = $item
        while ($null -ne $node) {
            if (($node.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Có reparse point.' }
            if ($node.FullName -eq $repoRoot) { break }
            if ($node.PSIsContainer) { $node = $node.Parent } else { $node = $node.Directory }
        }
        $checked += $target
    }
}
if (@($checked | Sort-Object -Unique).Count -ne 70 -or
    @(Compare-Object ($checked | Sort-Object) ($expected | Sort-Object)).Count -ne 0) { throw 'Allowlist không khớp.' }

# Preflight chỉ đọc bằng .venv, kiểm identity và toàn bộ tên hardlink ngay trước xóa.
Push-Location $repoRoot
try {
    $preflight = @'
from pathlib import Path
import importlib.util,json,hashlib,os
b=Path('research_tracking/runs/history-cleanup-20261117-01')
s=importlib.util.spec_from_file_location('cleanup',b/'prepare_cleanup.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=m.load(b/'DELETE_PLAN.json')
for g in p['groups']:
 paths=[m.checked_path(x) for x in g['paths']]
 assert {os.path.normcase(str(x)) for x in m.hardlinks(paths[0])}=={os.path.normcase(str(x)) for x in paths}
 for path in paths:
  q=path.stat();assert (q.st_dev,q.st_ino,q.st_size,q.st_mtime_ns,q.st_nlink)==(g['volume_id'],g['file_id'],g['bytes'],g['modified_ns'],2)
for r in m.load(b/'PROTECTED_FILES.json'):
 path=m.ROOT/r['path'];assert path.stat().st_size==r['bytes'] and m.sha(path)==r['sha256']
print(json.dumps(dict(status='PASS_CURRENT_IDENTITIES_AND_PROTECTED_FILES',groups=35,paths=70)))
'@ | & (Join-Path $repoRoot '.venv\Scripts\python.exe') -B -
    if ($LASTEXITCODE -ne 0) { throw 'Preflight identity thất bại.' }
    $preflight | Set-Content -LiteralPath (Join-Path $bundle 'DELETE_PREFLIGHT.json') -Encoding utf8
    $relocation = @{ storage='GOOGLE_DRIVE_SHA256_VERIFIED'; groups=$plan.groups;
        note_vi='Các đường dẫn archive cũ có bản giữ trên Drive. Tải về đúng đường dẫn cần replay và kiểm SHA trước dùng. Trạng thái xóa nằm trong DELETE_RESULT và nhật ký.' }
    $relocation | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $bundle 'RELOCATION_MANIFEST.json') -Encoding utf8
    $freeBefore = (Get-PSDrive -Name D).Free
    $deletedPaths = 0
    $deletedGroups = 0
    [long]$uniqueBytes = 0
    $status = 'FAILED_PARTIAL'
    $errorText = $null
    try {
        foreach ($group in $plan.groups) {
            $firstPath = [IO.Path]::GetFullPath((Join-Path $repoRoot $group.paths[0]))
            # Giữ handle đọc với share-delete, từ chối ghi dữ liệu trong lúc hash/unlink nhóm.
            $stream = [IO.File]::Open($firstPath, [IO.FileMode]::Open, [IO.FileAccess]::Read,
                ([IO.FileShare]::Read -bor [IO.FileShare]::Delete))
            try {
                $algorithm = [Security.Cryptography.SHA256]::Create()
                try { $hash = [Convert]::ToHexString($algorithm.ComputeHash($stream)).ToLowerInvariant() }
                finally { $algorithm.Dispose() }
                if ($hash -ne $group.sha256 -or $stream.Length -ne $group.bytes) { throw 'SHA archive đã đổi.' }
                foreach ($relative in $group.paths) {
                    $target = [IO.Path]::GetFullPath((Join-Path $repoRoot $relative))
                    if ($target -notin $checked) { throw 'Path chưa được kiểm.' }
                    if ((Get-Item -LiteralPath $target -Force).Length -ne $group.bytes) { throw 'Kích thước đã đổi.' }
                    @{action='DELETE_INTENT'; path=$relative; bytes=$group.bytes; sha256=$hash; remote_id=$group.remote_id;
                        at=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Compress | Add-Content -LiteralPath $journal -Encoding utf8
                    Remove-Item -LiteralPath $target -Force -ErrorAction Stop
                    if (Test-Path -LiteralPath $target) { throw 'Hardlink vẫn còn.' }
                    $deletedPaths++
                    @{action='DELETED'; path=$relative; at=[DateTime]::UtcNow.ToString('o')} |
                        ConvertTo-Json -Compress | Add-Content -LiteralPath $journal -Encoding utf8
                }
            } finally { $stream.Dispose() }
            $deletedGroups++
            $uniqueBytes += $group.bytes
        }
        $status = 'COMPLETE'
    } catch {
        $errorText = $_.Exception.Message
        throw
    } finally {
        @{status=$status; deleted_paths=$deletedPaths; deleted_archive_groups=$deletedGroups;
          unique_archive_bytes=$uniqueBytes; free_before=$freeBefore; free_after=(Get-PSDrive -Name D).Free;
          error=$errorText; authorization_vi='User yêu cầu xóa an toàn 35 GB lịch sử đã sao lưu và kiểm SHA trên Drive.';
          limit_vi='Chênh dung lượng trống còn chịu ảnh hưởng output calibration/hoạt động khác cùng lúc.'} |
            ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding utf8
    }
    Get-Content -LiteralPath $resultPath
} finally { Pop-Location }
