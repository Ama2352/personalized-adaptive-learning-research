# Chỉ gỡ thư mục thật sự rỗng dưới các vùng đã chuyển lạnh.
param([string]$LogFile='EMPTY_DIRECTORY_PRUNE.json')
$ErrorActionPreference='Stop'
$bundle=$PSScriptRoot
$workspace=[IO.Path]::GetFullPath((Join-Path $bundle '..\..\..')).TrimEnd('\')
$roots=@((Join-Path $workspace 'artifacts\akt'),(Join-Path $workspace 'experiments\akt\results'))
$removed=[Collections.Generic.List[string]]::new()
$kept=[Collections.Generic.List[object]]::new()
function Visit-Empty([string]$directory) {
    $normal=[IO.Path]::GetFullPath($directory).TrimEnd('\')
    if (-not $normal.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Ngoài workspace.' }
    $relative=$normal.Substring($workspace.Length+1).Replace('\','/')
    if ($relative -match '^artifacts/akt/private(?:/|$)' -or $normal -match '\\(\.venv|venv)(\\|$)') { return }
    $ownedCold=Join-Path $workspace 'artifacts\akt\runtime\project-transfer-20261118-01\cold-project'
    if ($normal -match '\\\.git(\\|$)' -and -not $normal.StartsWith($ownedCold+'\',[StringComparison]::OrdinalIgnoreCase)) { return }
    $operation=if($normal.Length -ge 240){'\\?\'+$normal}else{$normal}
    try {
        $item=Get-Item -LiteralPath $operation -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { return }
        $children=@(Get-ChildItem -LiteralPath $operation -Force -ErrorAction Stop)
        foreach($child in $children) {
            if ($child.PSIsContainer) { Visit-Empty (Join-Path $normal $child.Name) }
        }
        if ($normal -in $roots) { return }
        if (@(Get-ChildItem -LiteralPath $operation -Force -ErrorAction Stop).Count -eq 0) {
            [IO.Directory]::Delete($operation,$false)
            $removed.Add($relative)
        }
    } catch { $kept.Add(@{path=$relative;reason=$_.Exception.GetType().Name}) }
}
foreach($root in $roots) { Visit-Empty $root }
@{removed_directories=$removed.Count;removed=$removed;kept_on_error=$kept} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $bundle $LogFile) -Encoding UTF8
Write-Output "EMPTY_DIRECTORIES_REMOVED $($removed.Count) KEPT_ERRORS $($kept.Count)"
