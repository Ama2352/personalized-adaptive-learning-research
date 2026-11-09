param([ValidateSet('desktop','mobile')][string]$View)
$ErrorActionPreference='Stop'
$repoRoot='D:\Dev\KLTN'
$prepRoot=Join-Path $repoRoot 'artifacts\akt\local-tests\akt-research-runner-20261108-01'
$browserPath='C:\Program Files\Google\Chrome\Application\chrome.exe'
$profilePath=Join-Path $prepRoot ('supervisor-learned19-chrome-'+$View+'01')
$imagePath=Join-Path $prepRoot ('supervisor_learned19_'+$View+'01.png')
$outPath=Join-Path $prepRoot ('supervisor_learned19_'+$View+'01.stdout.log')
$errPath=Join-Path $prepRoot ('supervisor_learned19_'+$View+'01.stderr.log')
if ((Test-Path -LiteralPath $profilePath) -or (Test-Path -LiteralPath $imagePath)) { throw 'Fresh owned QA namespace required' }
if ($View -eq 'desktop') { $windowSize='1280,2200' } else { $windowSize='390,3200' }
$arguments=@('--headless=new','--disable-gpu','--disable-background-networking','--no-first-run','--no-default-browser-check',
    ('--user-data-dir='+$profilePath),('--screenshot='+$imagePath),('--window-size='+$windowSize),
    '--hide-scrollbars','--virtual-time-budget=2000',
    'file:///D:/Dev/KLTN/research_tracking/supervisor_reports/2026-11-09/01_tien_do/BAO_CAO_NGHIEN_CUU.html#chang-13')
$stopwatch=[Diagnostics.Stopwatch]::StartNew()
$process=$null
$result=[ordered]@{view=$View;window=$windowSize;budget_seconds=30;url=$arguments[-1];owned_profile=$profilePath}
try {
    $process=Start-Process -FilePath $browserPath -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput $outPath -RedirectStandardError $errPath
    $result.pid=$process.Id
    $result.start_utc=$process.StartTime.ToUniversalTime().ToString('o')
    if (-not $process.WaitForExit(30000)) { throw 'Owned headless browser exceeded30seconds' }
    $result.exit_code=$process.ExitCode
    if ($process.ExitCode -ne 0) { throw 'Headless browser failed' }
    if (-not (Test-Path -LiteralPath $imagePath)) { throw 'Screenshot not produced' }
    $result.image_sha256=(Get-FileHash -LiteralPath $imagePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $result.image_bytes=(Get-Item -LiteralPath $imagePath).Length
    $result.status='RENDERED_PENDING_ROOT_VISUAL_REVIEW'
} finally {
    if ($null -ne $process) {
        if (-not $process.HasExited) { $process.Kill($true); $process.WaitForExit(5000) | Out-Null }
        $result.owned_browser_exited=$process.HasExited
        $process.Dispose()
    }
    $result.elapsed_seconds=$stopwatch.Elapsed.TotalSeconds
    $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $prepRoot ('supervisor_learned19_'+$View+'01.render.json')) -Encoding utf8
}
$result | ConvertTo-Json -Depth 6
