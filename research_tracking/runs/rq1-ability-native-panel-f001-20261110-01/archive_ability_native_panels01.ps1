# Đóng bằng chứng hai đối chứng đã nghiệm thu. Dry mặc định không ghi bundle.
param([Parameter(Mandatory=$true)][ValidateSet('F001','F081')][string]$CellId,[switch]$Close)
$ErrorActionPreference='Stop'
$workspace=(Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$p=[IO.Path]::GetRelativePath($workspace,$PSScriptRoot).Replace('\','/')
$lower=$CellId.ToLowerInvariant()
$native="experiments/gam_kt/results/rq1-ability-panel-$lower-20261110-01"
$target=Join-Path $workspace "research_tracking/runs/rq1-ability-native-panel-$lower-20261110-01"
if(Test-Path -LiteralPath $target){throw 'Bundle đã có'}
$map=@{}
foreach($name in @('worker_rq1_ability_native_panel02.py','run_rq1_ability_native_panel02.py','rq1_ability_native_panel_contract02.json',
    'RQ1_ABILITY_PANEL_CONTROLS_PLAN02.md','rq1_ability_panel_case_whitelist02.json','ROOT_RQ1_ABILITY_CONTROLS_REVIEW02.md',
    'ability-panel-derivative02-source-before.json','ability-panel-derivative02-copy-proof.json',
    'verify_ability_panels_cached01.py','ability_panel_combined_descriptive_table01.json','archive_ability_native_panels01.ps1')){
    $map[$name]="$p/$name"
}
$map['independent_cached_review.json']="$p/ability_${lower}_independent_cached_review01.json"
$map['report.md']='research_tracking/reports/rq1_fixed_time_ability_native_panels_20261110.md'
foreach($name in @('summary.json','lineage.json','parity.json','reservation.json','native_metadata.json','resources.jsonl','result.json')){
    $map['native__'+$name]="$native/$name"
}
foreach($name in @('admission.json','final.json')){$map['outer__'+$name]="$p/rq1-ability-native-panel02-$lower-outer/$name"}
foreach($name in @('GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log')){
    $map['owned__'+$name]="$p/rq1-ability-native-panel02-$lower-owned/$name"
}
function Pin([string]$path,[int]$cap=4194304){
    $item=Get-Item -LiteralPath $path
    if($item.Length -gt $cap -or $item.PSIsContainer){throw 'Byte/file cap'}
    return @{sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$item.Length}
}
function Save([string]$name,$value){
    $path=Join-Path $target $name
    if(Test-Path -LiteralPath $path){throw 'No overwrite'}
    [IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 25)+"`n",[Text.UTF8Encoding]::new($false))
}
$before=@{}
foreach($alias in $map.Keys){$before[$alias]=@{source=$map[$alias];pin=(Pin (Join-Path $workspace $map[$alias]) 262144)}}
$outer=Get-Content -LiteralPath (Join-Path $workspace $map['outer__final.json']) -Raw|ConvertFrom-Json
$worker=Get-Content -LiteralPath (Join-Path $workspace $map['native__result.json']) -Raw|ConvertFrom-Json
$proof=Get-Content -LiteralPath (Join-Path $workspace $map['independent_cached_review.json']) -Raw|ConvertFrom-Json
$outerPins=@{F001='3d271f0adaaee74b0c4d61d168e5739ef937a120ddb06b9f1679ca1004412868';F081='770418e18095a949a7385af951bec4d8e5ef73b5cb0a8ca6df0e4a275ccb67d7'}
if($before['outer__final.json'].pin.sha256 -cne $outerPins[$CellId] -or
    $outer.status -cne 'ACCEPTED_PREDECLARED_ABILITY_NATIVE_FIRSTPASS_AND_RECONSTRUCTED28_PANEL' -or
    $outer.cell_id -cne $CellId -or $null -ne $outer.error -or $null -ne $outer.postcheck_error -or
    $outer.owned_receipt.cleanup_accepted -ne $true -or $outer.owned_receipt.job_active_after_cleanup -ne 0 -or
    $outer.environment_restored -ne $true){throw 'No accepted clean outer'}
if(Test-Path -LiteralPath (Join-Path $workspace "$p/rq1-ability-native-panel02-$lower-outer/postwrite-rejection.json")){throw 'Late rejection'}
if($worker.status -cne 'ACCEPTED_PREDECLARED_ABILITY_NATIVE_PANEL_AND_SOURCE_RECONSTRUCTED_LATENT' -or
    $worker.cell_id -cne $CellId -or $null -ne $worker.error -or $worker.pretruth_frozen -ne $true -or
    $worker.evaluator_complete -ne $true -or $worker.monitor_stopped -ne $true -or $worker.job_query_handle_closed -ne $true -or
    $worker.denied.Count -ne 0 -or $worker.memory_errors.Count -ne 0 -or $worker.restoration_errors.Count -ne 0 -or
    $proof.status -cne 'PASS_CACHED_ABILITY_RECOUNT_AND_LATENT_STATE_RECONSTRUCTION' -or $proof.cell_id -cne $CellId -or
    $proof.source_prestate_fullvars_sha_matches -ne 120 -or $proof.independent_latent_row_equations -ne 3360 -or
    $proof.full_final_environment_exact -ne $true -or $proof.all28_endpoint_exact -ne $true){throw 'Incomplete parity/review'}
$caps=@{policy_builder=1;select=120;predict=120;update=120;theta_at=3360}
foreach($name in $caps.Keys){if($worker.attempted.$name -ne $caps[$name] -or $worker.returned.$name -ne $caps[$name]){throw 'Actual counts mismatch'}}
$references=@{}
foreach($entry in $worker.source_before.PSObject.Properties){
    $pin=Pin (Join-Path $workspace $entry.Name)
    if($worker.source_after.($entry.Name) -cne $entry.Value -or $pin.sha256 -cne $entry.Value){throw 'Source drift'}
    $references[$entry.Name]=$pin
}
$large=@{}
foreach($name in @('native_panel.jsonl','joined_panel.jsonl')){
    $path="$native/$name"; $pin=Pin (Join-Path $workspace $path)
    if($pin.sha256 -cne $outer.outputs.$name.sha256 -or $pin.bytes -ne $outer.outputs.$name.bytes){throw 'Large output mismatch'}
    $large[$path]=@{sha256=$pin.sha256;bytes=$pin.bytes;rows=3360;copied=$false}
}
foreach($name in @('summary.json','lineage.json','parity.json','reservation.json','native_metadata.json','resources.jsonl','result.json')){
    $pin=$before['native__'+$name].pin
    if($pin.sha256 -cne $outer.outputs.$name.sha256 -or $pin.bytes -ne $outer.outputs.$name.bytes){throw 'Native output mismatch'}
}
if(-not $Close){
    [pscustomobject]@{status='DRY_VALIDATED_NO_WRITE';cell=$CellId;copies=$map.Count;planned_outputs=($map.Count+4);
        referenced_large=2;target=$target;source_inventory=$before}|ConvertTo-Json -Depth 8
    exit 0
}
New-Item -ItemType Directory -Path $target|Out-Null
Save 'inventory-before-copy.json' $before
$copied=@{}
foreach($alias in $map.Keys){
    $source=Join-Path $workspace $map[$alias]; $dest=Join-Path $target $alias
    [IO.File]::Copy($source,$dest,$false)
    $copy=Pin $dest; $after=Pin $source
    if($copy.sha256 -cne $before[$alias].pin.sha256 -or $after.sha256 -cne $copy.sha256 -or
        $copy.bytes -ne $before[$alias].pin.bytes -or $after.bytes -ne $copy.bytes){throw 'Copy/source mismatch'}
    $copied[$alias]=@{before=$before[$alias];copy=$copy;source_after=$after}
}
foreach($path in $references.Keys){if((Pin (Join-Path $workspace $path)).sha256 -cne $references[$path].sha256){throw 'Reference drift aftercopy'}}
foreach($path in $large.Keys){if((Pin (Join-Path $workspace $path)).sha256 -cne $large[$path].sha256){throw 'Large drift aftercopy'}}
Save 'copy-verification.json' $copied
Save 'reference-inputs-and-large-outputs.json' @{input_source_references=$references;large_outputs=$large}
$note=@"
# $CellId · Native panel tại 28 khái niệm

Một lịch sử 120 bước đã nghiệm thu với action/P/update và endpoint exact trước khi ghép latent. Bảng có 3360 cặp khái niệm–thời điểm, gồm 120 queried và 3240 not queried. Một policy và 120 cập nhật GAM thực tế, không có world constructor/interact, đáp án mới, RNG hoặc NN. Checker stdlib độc lập tái hiện 3360 phương trình latent, 120 fullvars SHA và endpoint 28 khái niệm. Cả source trước/copy/sau đều được kiểm SHA.

[Báo cáo kết hợp ba lịch sử](../../reports/rq1_fixed_time_ability_native_panels_20261110.md) và bảng JSON trong bundle giữ đầy đủ ô bằng không. F041 chỉ là tham chiếu đã nghiệm thu. Ba lịch sử thuộc cùng block 21010, không tạo ba block độc lập. Không kết luận calibration, khả năng phân loại chung, pi luôn dư thừa hoặc tác động nhân quả của đồ thị.

Hai scientific JSONL giữ tại $native, được tham chiếu SHA/size, không nhân đôi. Các nguồn khoa học gốc và bundle F041/Recovery03 được tham chiếu theo pins. Completed của manifest chỉ xác nhận archive đã đóng, không hoàn tất RQ hoặc cấp quyền chạy tiếp.
"@
[IO.File]::WriteAllText((Join-Path $target 'README.md'),$note+"`n",[Text.UTF8Encoding]::new($false))
$outputs=@{}
foreach($file in Get-ChildItem -LiteralPath $target -File){$outputs[$file.Name]=(Pin $file.FullName).sha256}
Save 'manifest.json' @{schema_version=1;status='completed';kind='predeclared_one_history_ability_native_panel';cell_id=$CellId;
    source_inventory_before=$before;outputs_sha256=$outputs;large_outputs_not_copied=$large;
    native_GAM_updates=120;new_world_response_calls=0;concepts=28;steps=120;repeated_rows=3360;history_units=1;
    criterion='SIMULATOR_THETA_AT_GE1250_NOT_HUMAN_OR_S04_MASTERY';no_inference=$true}
foreach($entry in $outputs.GetEnumerator()){if((Pin (Join-Path $target $entry.Key)).sha256 -cne $entry.Value){throw 'Closed output mismatch'}}
[pscustomobject]@{status='VERIFIED_ARCHIVE_ONLY';cell=$CellId;path=$target;manifest=(Pin (Join-Path $target 'manifest.json')).sha256;outputs=$outputs.Count}|ConvertTo-Json
