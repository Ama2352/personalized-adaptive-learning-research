# Chỉ chạy danh sách 416 file được người dùng duyệt ngày 16/11/2026.
$ErrorActionPreference = 'Stop'
$repoRoot = 'D:\Dev\KLTN'
$evidenceRoot = Join-Path $repoRoot 'research_tracking\runs\artifact-retention-audit-20261116-01'
$inventoryPath = Join-Path $evidenceRoot 'STORAGE_CLEANUP_REVIEW02.json'
$journalPath = Join-Path $evidenceRoot 'STORAGE_DELETE04_JOURNAL.jsonl'
$receiptPath = Join-Path $evidenceRoot 'STORAGE_DELETE04_RESULT.json'
if ((Test-Path -LiteralPath $journalPath) -or (Test-Path -LiteralPath $receiptPath)) {
    throw 'Lượt này đã có hồ sơ. Phải kiểm trạng thái trước khi tiếp tục.'
}
if ((Get-FileHash -LiteralPath $inventoryPath -Algorithm SHA256).Hash -ne '8876259701831DE86D8C3EE7D6138033B88D17DEE1D821794A2D2BDD49B1A02A') {
    throw 'Inventory đã đổi.'
}
$inventory = Get-Content -LiteralPath $inventoryPath -Raw | ConvertFrom-Json
if ($inventory.candidates.Count -ne 416) { throw 'Sai số file.' }

# Python trong .venv chỉ đọc: kiểm identity, bản giữ và gói bằng chứng.
Push-Location $repoRoot
try {
    $preflight = @'
import hashlib,json
from pathlib import Path
r=Path.cwd(); b=r/'research_tracking/runs/artifact-retention-audit-20261116-01'
def sha(p):
 with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
inflight=set()
for name in ('drive-offload-duplicates-20261116-01','drive-offload-history-20261116-01'):
 for p in (r/'experiments/akt/results'/name).rglob('*'):
  if p.is_file():
   s=p.stat(); inflight.add((s.st_dev,s.st_ino))
a=json.loads((b/'STORAGE_CLEANUP_REVIEW02.json').read_text())
assert len(a['candidates'])==416 and sum(x['bytes'] for x in a['candidates'])==3564916775
for row in a['candidates']:
 p=r/row['path']; s=p.stat()
 assert (s.st_dev,s.st_ino,s.st_nlink)==(row['volume_id'],row['file_id'],row['links'])
 assert (s.st_dev,s.st_ino) not in inflight
 assert s.st_size==row['bytes'] and sha(p)==row['sha256']
old=r/'experiments/akt/results/artifact-offload-20261116-01'
proofs=json.loads((old/'TRANSFER_PARTS_VERIFIED.json').read_text())
keepers={x['archive']:x['archive_sha256'] for x in proofs}
parts=json.loads((old/'drive-transfer-parts-20261116-01/DRIVE_PARTS_MANIFEST.json').read_text())
keepers.update({x['source']:x['sha256'] for x in parts['archives']})
for name,h in keepers.items(): assert sha(r/name)==h
p=json.loads((b/'STORAGE_SMALL_PACKAGE02.json').read_text())
receipt=json.loads((b/'STORAGE_SMALL_DRIVE_RECEIPT02.json').read_text())
assert sha(r/p['path'])==p['sha256']==receipt['sha256']
assert receipt['status']=='REMOTE_BYTES_VERIFIED'
print(json.dumps(dict(status='PASS',retained_archives=keepers,candidates=416,inflight_overlap=0)))
'@ | & (Join-Path $repoRoot '.venv\Scripts\python.exe') -B -
    if ($LASTEXITCODE -ne 0) { throw 'Preflight thất bại.' }
    $preflight | Set-Content -LiteralPath (Join-Path $evidenceRoot 'STORAGE_DELETE04_PREFLIGHT.json') -Encoding utf8

    $allowedRoots = @(
        'experiments\akt\results\artifact-offload-20261116-01\drive-transfer-parts-20261116-01',
        'experiments\akt\results\model-export-a3-refit-recovery-20261115-06',
        'artifacts\akt\runtime\a1-compact-adapter-tests-20261113-01',
        'artifacts\akt\runtime\a1-fastpath-tests-20261113-01',
        'artifacts\akt\runtime\refit-pipeline-tests-20261114-04',
        'artifacts\akt\runtime\refit-pipeline-tests-20261114-03'
    ) | ForEach-Object { [IO.Path]::GetFullPath((Join-Path $repoRoot $_)) }
    $checkedPaths = @()
    foreach ($row in $inventory.candidates) {
        $target = [IO.Path]::GetFullPath((Join-Path $repoRoot $row.path))
        $inside = @($allowedRoots | Where-Object { $target.StartsWith($_ + '\', [StringComparison]::OrdinalIgnoreCase) })
        if ($inside.Count -ne 1) { throw "Ngoài phạm vi đã duyệt: $target" }
        $node = Get-Item -LiteralPath $target -Force
        if ($node.PSIsContainer) { throw 'Không được xóa thư mục.' }
        while ($null -ne $node) {
            if (($node.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Có reparse point.' }
            if ($node.FullName -eq $repoRoot) { break }
            if ($node.PSIsContainer) { $node = $node.Parent }
            else { $node = $node.Directory }
        }
        $checkedPaths += $target
    }
    $freeBefore = (Get-PSDrive -Name D).Free
    $deletedCount = 0
    [long]$deletedBytes = 0
    $status = 'FAILED_PARTIAL'
    $errorText = $null
    try {
        for ($i = 0; $i -lt $inventory.candidates.Count; $i++) {
            $row = $inventory.candidates[$i]
            $target = $checkedPaths[$i]
            $item = Get-Item -LiteralPath $target -Force
            if ($item.Length -ne $row.bytes -or (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $row.sha256) { throw "File đã đổi: $target" }
            @{ action='DELETE_INTENT'; path=$row.path; bytes=$row.bytes; sha256=$row.sha256; at=[DateTime]::UtcNow.ToString('o') } | ConvertTo-Json -Compress | Add-Content -LiteralPath $journalPath -Encoding utf8
            Remove-Item -LiteralPath $target -ErrorAction Stop
            if (Test-Path -LiteralPath $target) { throw "File vẫn còn: $target" }
            $deletedCount++
            $deletedBytes += $row.bytes
            @{ action='DELETED'; path=$row.path; at=[DateTime]::UtcNow.ToString('o') } | ConvertTo-Json -Compress | Add-Content -LiteralPath $journalPath -Encoding utf8
        }
        $status = 'COMPLETE'
    } catch {
        $errorText = $_.Exception.Message
        throw
    } finally {
        @{ status=$status; files_deleted=$deletedCount; logical_bytes_deleted=$deletedBytes; free_before=$freeBefore; free_after=(Get-PSDrive -Name D).Free; error=$errorText; authorization_vi='Người dùng xác nhận: vậy bạn xóa đi'; limitation_vi='Dung lượng trống còn chịu ảnh hưởng hoạt động khác trên ổ D.' } | ConvertTo-Json | Set-Content -LiteralPath $receiptPath -Encoding utf8
    }
    Get-Content -LiteralPath $receiptPath
} finally {
    Pop-Location
}
