# Copy hồ sơ cached đã review, không tính lại bootstrap hoặc gọi Git.
$ErrorActionPreference='Stop'
$workspace=(Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$target=Join-Path $workspace 'research_tracking/runs/rq2-fresh-block-uncertainty-20261110-01'
if(Test-Path -LiteralPath $target){throw 'Bundle đã có'}
$prepRelative=[IO.Path]::GetRelativePath($workspace,$PSScriptRoot).Replace('\','/')
$map=@{
    'analyze_rq2_fresh_block_uncertainty01.py'="$prepRelative/analyze_rq2_fresh_block_uncertainty01.py"
    'RQ2_FRESH_BLOCK_UNCERTAINTY_SPEC01.md'="$prepRelative/RQ2_FRESH_BLOCK_UNCERTAINTY_SPEC01.md"
    'ROOT_RQ2_EXPLORATORY_UNCERTAINTY_REVIEW01.md'="$prepRelative/ROOT_RQ2_EXPLORATORY_UNCERTAINTY_REVIEW01.md"
    'run_rq2_fresh_block_uncertainty01.py'="$prepRelative/run_rq2_fresh_block_uncertainty01.py"
    'verify_rq2_fresh_uncertainty_independent01.py'="$prepRelative/verify_rq2_fresh_uncertainty_independent01.py"
    'independent_numeric_review.json'="$prepRelative/rq2_fresh_uncertainty_independent01.json"
    'summary.json'="$prepRelative/rq2-fresh-block-uncertainty01/summary.json"
    'bootstrap_means.csv'="$prepRelative/rq2-fresh-block-uncertainty01/bootstrap_means.csv"
    'result.json'="$prepRelative/rq2-fresh-block-uncertainty01/result.json"
    'outer__allocation.json'="$prepRelative/rq2-fresh-block-uncertainty01-outer/allocation.json"
    'outer__result.json'="$prepRelative/rq2-fresh-block-uncertainty01-outer/result.json"
    'outer__stdout.log'="$prepRelative/rq2-fresh-block-uncertainty01-outer/stdout.log"
    'outer__stderr.log'="$prepRelative/rq2-fresh-block-uncertainty01-outer/stderr.log"
    'rq2_fresh_block_uncertainty_20261110.md'='research_tracking/reports/rq2_fresh_block_uncertainty_20261110.md'
    'archive_rq2_fresh_uncertainty01.ps1'="$prepRelative/archive_rq2_fresh_uncertainty01.ps1"
}
function Pin([string]$path){
    $file=Get-Item -LiteralPath $path
    if($file.Length -gt 1048576){throw 'File vượt1MiB'}
    return @{sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$file.Length}
}
function Save([string]$name,$value){
    $path=Join-Path $target $name
    if(Test-Path -LiteralPath $path){throw 'Không ghi đè'}
    [IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 15)+"`n",[Text.UTF8Encoding]::new($false))
}
$before=@{}
foreach($alias in $map.Keys){$before[$alias]=@{source=$map[$alias];pin=(Pin (Join-Path $workspace $map[$alias]))}}
$required=@{
    'analyze_rq2_fresh_block_uncertainty01.py'='21dce940bf8c3ddd9114eccde5952c5bbcaea86f90b88e462f8fa89d39463938'
    'RQ2_FRESH_BLOCK_UNCERTAINTY_SPEC01.md'='83f6cfde91ecbd12053de14da1f16295846aded1f798d0592b4cd61aa4b67da8'
    'ROOT_RQ2_EXPLORATORY_UNCERTAINTY_REVIEW01.md'='f5f931bbcc4e14dcbb2f0d5c87c4bb55628ee826094f3529438f688bc8b33042'
    'run_rq2_fresh_block_uncertainty01.py'='5e927ec6d8b32f52df6af2530353d6a5f1ec747583f2c9468cf40f0f853d121b'
    'verify_rq2_fresh_uncertainty_independent01.py'='3bc714ff0a33df01d9fc0d5323974d9856fe046b6efee959be05e798648eb07e'
    'independent_numeric_review.json'='c71b161cc194b11f091bbd2192b462a1f13991c8534dd136991e967007ec3f57'
    'outer__result.json'='91a869a890b7ac233cbce112f08bd215c0fd5eea6b5307f85eabf1d04da1c6b3'
    'rq2_fresh_block_uncertainty_20261110.md'='10ead22b8eeb032cdfab84dce9b802362364791c250a1b3649852ac70c3d18c9'
}
foreach($name in $required.Keys){if($before[$name].pin.sha256 -cne $required[$name]){throw "Source drift $name"}}
$worker=Get-Content -LiteralPath (Join-Path $workspace $map['result.json']) -Raw|ConvertFrom-Json
$outer=Get-Content -LiteralPath (Join-Path $workspace $map['outer__result.json']) -Raw|ConvertFrom-Json
$proof=Get-Content -LiteralPath (Join-Path $workspace $map['independent_numeric_review.json']) -Raw|ConvertFrom-Json
if($worker.status -cne 'ACCEPTED_CACHED_EXPLORATORY_STATISTICS_ONLY' -or $outer.accepted -ne $true -or
    $outer.returncode -ne 0 -or $null -ne $outer.error -or $worker.blocks -ne 10 -or $worker.replicates -ne 10000 -or
    $worker.estimates -ne 3 -or $worker.new_world_model_response_calls -ne 0 -or
    $proof.status -cne 'PASS_INDEPENDENT_DECIMAL_RECOUNT_NO_REDRAWS' -or $proof.csv_rows -ne 10000 -or
    $proof.random_calls -ne 0 -or $proof.bootstrap_redraws -ne 0){throw 'Acceptance/review chưa đủ'}
foreach($name in @('script','plan','kernel')){if($worker.source_before.$name -cne $worker.source_after.$name){throw 'Source prepost drift'}}
foreach($name in @('summary.json','bootstrap_means.csv')){
    if($before[$name].pin.sha256 -cne $worker.outputs.$name.sha256 -or $before[$name].pin.bytes -ne $worker.outputs.$name.bytes){throw 'Cached output drift'}
}
$referenceRoot='research_tracking/runs/rq2-fresh-graph-recovery-20261110-01/'
$references=@{($referenceRoot+'manifest.json')='deff815a7360ab9d0ffcaf06e986ff2fc14ed07aa0ab8366880ade34445df11e';
    'src/knowledge_tracing/research_selection.py'='0e3cf12d15626a76000c6cdc04779ac769806aae2a5e52f769d4c70f3580a348'}
foreach($entry in $worker.input_pins.PSObject.Properties){$references[$referenceRoot+$entry.Name]=$entry.Value}
foreach($name in $references.Keys){if((Pin (Join-Path $workspace $name)).sha256 -cne $references[$name]){throw 'Referenced input drift'}}
New-Item -ItemType Directory -Path $target|Out-Null
Save 'inventory-before-copy.json' $before
$copyProof=@{}
foreach($alias in $map.Keys){
    $source=Join-Path $workspace $map[$alias]
    $destination=Join-Path $target $alias
    [IO.File]::Copy($source,$destination,$false)
    $copy=Pin $destination
    $after=Pin $source
    if($copy.sha256 -cne $before[$alias].pin.sha256 -or $after.sha256 -cne $copy.sha256 -or
        $copy.bytes -ne $before[$alias].pin.bytes -or $after.bytes -ne $copy.bytes){throw 'Copy SHA/size mismatch'}
    $copyProof[$alias]=@{before=$before[$alias];copy=$copy;source_after=$after}
}
foreach($name in $references.Keys){if((Pin (Join-Path $workspace $name)).sha256 -cne $references[$name]){throw 'Reference changed after copy'}}
Save 'copy-verification.json' $copyProof
Save 'reference-inputs-not-duplicated.json' $references
$note=@'
# RQ2 · Bất định thăm dò theo paired block

Một cached operation đã đạt, không thêm world/model/response. Ba estimands dùng10000shared block draws, n10 và Bonferroni percentile intervals98,333% mỗi khoảng, mức đồng thời95% danh nghĩa xấp xỉ. K1300 chỉ là structural control không kiểm định. E9 không gộp. Các kết quả đã được xem nên đây là thăm dò sau kết quả, chưa confirmatory hoặc hoàn tất RQ.

[Báo cáo kỹ thuật canonical](../../reports/rq2_fresh_block_uncertainty_20261110.md) trình bày đủ ba hàng và giới hạn. Bản copy trong bundle giữ nguyên byte với link theo vị trí canonical. K1150 có khoảng dương, nhưng khoảng của K1150−K1000 vẫn chứa0, chưa kết luận hai mức năng lực khác nhau.

CSV giữ đủ10000vector, không redraw trong kiểm độc lập. Decimal precision60 kiểm ba means/min/max/signs và sáu quantiles với sai khác tối đa1,13050e−16, tolerance số học1e−12. Không tính lại hoặc xác nhận lại draw stream SHA bằng RNG trong checker. Root báo manufactured checks đã đạt nhưng không có raw fixture receipt riêng để copy, không tạo log thay thế hoặc cộng test count.

Raw worker/outer result, stdout/stderr, nguồn/đặc tả/review và checker/proof được giữ. Không có failure của operation cached này. Nguồn fresh120 và kernel chỉ tham chiếu SHA, không copy dataset/traces/checkpoints. Inventory trước/copy/sau được kiểm. Status completed xác nhận đóng hồ sơ này, không cấp authority phương pháp hoặc nghiên cứu mới.
'@
[IO.File]::WriteAllText((Join-Path $target 'README.md'),$note+"`n",[Text.UTF8Encoding]::new($false))
$outputs=@{}
foreach($file in Get-ChildItem -LiteralPath $target -File){$outputs[$file.Name]=(Pin $file.FullName).sha256}
Save 'manifest.json' @{schema_version=1;status='completed';kind='posthoc_paired_block_uncertainty_cached_analysis';
    scientific_scope='EXPLORATORY_APPROXIMATE_INTERVALS_NO_RQ_COMPLETION';reference_inputs=$references;
    source_inventory_before=$before;outputs_sha256=$outputs;new_world_model_response_calls=0;family_size=3;blocks=10;replicates=10000}
foreach($entry in $outputs.GetEnumerator()){if((Pin (Join-Path $target $entry.Key)).sha256 -cne $entry.Value){throw 'Manifest mismatch'}}
[PSCustomObject]@{status='VERIFIED_ARCHIVE';path=$target;manifest=(Pin (Join-Path $target 'manifest.json')).sha256;outputs=$outputs.Count}|ConvertTo-Json
