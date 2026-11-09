# Hồ sơ áp dụng và sáu fixture canonical, không apply/test/Git lần nữa.
$ErrorActionPreference='Stop'
$workspace=(Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$target=Join-Path $workspace 'research_tracking/runs/rq1-native-panel-canonical-20261110-01'
if(Test-Path -LiteralPath $target){throw 'Bundle đã có'}
$relative=[IO.Path]::GetRelativePath($workspace,$PSScriptRoot).Replace('\','/')
$map=@{
    'native_panel_observer.py'='src/knowledge_tracing/gam_kt/native_panel_observer.py'
    'test_native_panel_observer.py'='tests/gam_kt/test_native_panel_observer.py'
    'apply_native_panel_recorder01.py'="$relative/apply_native_panel_recorder01.py"
    'apply__inventory_before_copy.json'="$relative/native-panel-canonical-apply01/inventory_before_copy.json"
    'apply__result.json'="$relative/native-panel-canonical-apply01/result.json"
    'tests__result.json'="$relative/native-panel-canonical-tests01/result.json"
    'tests__stdout.log'="$relative/native-panel-canonical-tests01/stdout.log"
    'tests__stderr.log'="$relative/native-panel-canonical-tests01/stderr.log"
    'archive_native_panel_canonical01.ps1'="$relative/archive_native_panel_canonical01.ps1"
}
function Pin([string]$path){
    $file=Get-Item -LiteralPath $path
    if($file.Length -gt 32768){throw 'File vượt32KiB'}
    return @{sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$file.Length}
}
function Save([string]$name,$value){
    $path=Join-Path $target $name
    if(Test-Path -LiteralPath $path){throw 'Không ghi đè'}
    [IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
}
$before=@{}
foreach($alias in $map.Keys){$before[$alias]=@{source=$map[$alias];pin=(Pin (Join-Path $workspace $map[$alias]))}}
$sourceSHA='b54b5f9a0899ec46b3e90d98b283fb34c84adaae5d2f47a581e405962bc936ba'
$testSHA='17918e2d7d1ac4e39788af78a608bbfeff07e5bc9fd9bb9d2d1cef6c2de937f6'
if($before['native_panel_observer.py'].pin.sha256 -cne $sourceSHA -or
    $before['test_native_panel_observer.py'].pin.sha256 -cne $testSHA){throw 'Canonical source drift'}
$apply=Get-Content -LiteralPath (Join-Path $workspace $map['apply__result.json']) -Raw|ConvertFrom-Json
$result=Get-Content -LiteralPath (Join-Path $workspace $map['tests__result.json']) -Raw|ConvertFrom-Json
if($apply.applied -ne $true -or $apply.source_sha256 -cne $sourceSHA -or $apply.test_sha256 -cne $testSHA -or
    $result.accepted -ne $true -or $result.returncode -ne 0){throw 'Application/test acceptance thiếu'}
foreach($entry in $result.source_before.PSObject.Properties){
    if($result.source_after.($entry.Name) -cne $entry.Value -or
        (Pin (Join-Path $workspace $entry.Name)).sha256 -cne $entry.Value){throw 'Canonical pre/post/source mismatch'}
}
$stderr=Get-Content -LiteralPath (Join-Path $workspace $map['tests__stderr.log']) -Raw
if($stderr -notmatch 'Ran 6 tests' -or $stderr -notmatch '(?m)^OK\s*$' -or $stderr -match '(?m)^(FAILED|ERROR|FAIL):?'){throw 'Không có raw6PASS'}
$candidateManifest='research_tracking/runs/rq1-native-panel-recorder-engineering-20261110-01/manifest.json'
$candidateSHA='93b50bfe0aa3a0971e1e59356dc72e41dc2d528fc947e23f7ca63f528e322e5b'
if((Pin (Join-Path $workspace $candidateManifest)).sha256 -cne $candidateSHA){throw 'Candidate bundle thay đổi'}
New-Item -ItemType Directory -Path $target|Out-Null
Save 'inventory-before-copy.json' $before
$proof=@{}
foreach($alias in $map.Keys){
    $source=Join-Path $workspace $map[$alias]
    $destination=Join-Path $target $alias
    [IO.File]::Copy($source,$destination,$false)
    $copy=Pin $destination
    $after=Pin $source
    if($copy.sha256 -cne $before[$alias].pin.sha256 -or $after.sha256 -cne $copy.sha256 -or
        $copy.bytes -ne $before[$alias].pin.bytes -or $after.bytes -ne $copy.bytes){throw 'Copy mismatch'}
    $proof[$alias]=@{source=$map[$alias];before=$before[$alias].pin;copy=$copy;after=$after}
}
Save 'copy-verification.json' $proof
Save 'candidate-bundle-reference.json' @{path=$candidateManifest;sha256=$candidateSHA;copied_again=$false}
$note=@'
# Native panel recorder · áp dụng canonical và kiểm fixture

Root đã áp dụng đúng byte recorder candidate. Test chỉ đổi cách import sang module canonical và bỏ các import không dùng. Hồ sơ apply giữ trước/sau, destination và SHA. Sáu fixture canonical đã đạt trong0,4192091giây với returncode0, nguồn hai file trước–sau khớp. Raw stderr ghi Ran6tests và OK.

Trường canonical_tests_pending=true trong receipt apply là trạng thái tại thời điểm áp dụng. Result tests sau đó xác nhận sáu fixture đã đạt. native_panel_pending vẫn đúng. Đây là sáu fixture dựng tay, không chạy native policy/world hoặc panel28concept thật, không thêm latent truth hoặc áp dụng phương pháp khoa học mới.

Bundle candidate trước đó được tham chiếu qua SHA và giữ nguyên. Bundle này chỉ đóng hồ sơ application và canonical fixtures, không tự apply/test lần nữa hoặc cấp Gate/research permission. Core interface chưa là chứng cứ global mastery accuracy, calibration hoặc hiệu quả học tập. Inventory trước/copy/sau kiểm byte và SHA, không Git trong archiver.
'@
[IO.File]::WriteAllText((Join-Path $target 'README.md'),$note+"`n",[Text.UTF8Encoding]::new($false))
$outputs=@{}
foreach($file in Get-ChildItem -LiteralPath $target -File){$outputs[$file.Name]=(Pin $file.FullName).sha256}
Save 'manifest.json' @{schema_version=1;status='completed';kind='canonical_native_panel_recorder_manufactured_fixtures';
    outputs_sha256=$outputs;source_inventory_before=$before;scientific_scope='CANONICAL_ENGINEERING_ONLY_NATIVE_PANEL_PENDING';
    tests=6;new_scientific_observations=0;candidate_reference=@{path=$candidateManifest;sha256=$candidateSHA}}
foreach($entry in $outputs.GetEnumerator()){if((Pin (Join-Path $target $entry.Key)).sha256 -cne $entry.Value){throw 'Manifest output mismatch'}}
[PSCustomObject]@{status='VERIFIED_ARCHIVE_ONLY';path=$target;manifest=(Pin (Join-Path $target 'manifest.json')).sha256;outputs=$outputs.Count}|ConvertTo-Json
