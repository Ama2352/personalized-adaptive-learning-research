# Archive actual F041 đã review. Không chạy lại policy, evaluator hoặc Git.
$ErrorActionPreference='Stop'
$workspace=(Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$p=[IO.Path]::GetRelativePath($workspace,$PSScriptRoot).Replace('\','/')
$native='experiments/gam_kt/results/rq1-f041-native-panel-20261110-01'
$target=Join-Path $workspace 'research_tracking/runs/rq1-f041-native-panel-20261110-01'
if(Test-Path -LiteralPath $target){throw 'Bundle đã có'}
$map=@{}
foreach($name in @('worker_rq1_f041_native_panel01.py','run_rq1_f041_native_panel01.py','rq1_f041_native_panel_contract01.json',
    'RQ1_F041_NATIVE_PANEL_PLAN01.md','ROOT_RQ1_F041_NATIVE_PANEL_REVIEW01.md','F041_NATIVE_SCALAR_TYPES_STATIC_REVIEW01.md',
    'verify_f041_panel_cached01.py','archive_f041_native_panel01.ps1')){$map[$name]="$p/$name"}
$map['independent_cached_review.json']="$p/f041_independent_cached_review01.json"
$map['rq1_f041_fixed_time_native_panel_20261110.md']='research_tracking/reports/rq1_f041_fixed_time_native_panel_20261110.md'
foreach($name in @('summary.json','lineage.json','parity.json','reservation.json','native_metadata.json','resources.jsonl','result.json')){
    $map['native__'+$name]="$native/$name"
}
foreach($name in @('admission.json','final.json')){$map['outer__'+$name]="$p/rq1-f041-native-panel01-outer/$name"}
foreach($name in @('GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log')){
    $map['owned__'+$name]="$p/rq1-f041-native-panel01-owned/$name"
}
function Pin([string]$path,[int]$cap=4194304){
    $item=Get-Item -LiteralPath $path
    if($item.Length -gt $cap){throw 'Byte cap'}
    return @{sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$item.Length}
}
function Save([string]$name,$value){
    $path=Join-Path $target $name
    if(Test-Path -LiteralPath $path){throw 'No overwrite'}
    [IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 18)+"`n",[Text.UTF8Encoding]::new($false))
}
$before=@{}
foreach($alias in $map.Keys){$before[$alias]=@{source=$map[$alias];pin=(Pin (Join-Path $workspace $map[$alias]) 262144)}}
$outer=Get-Content -LiteralPath (Join-Path $workspace $map['outer__final.json']) -Raw|ConvertFrom-Json
$worker=Get-Content -LiteralPath (Join-Path $workspace $map['native__result.json']) -Raw|ConvertFrom-Json
$proof=Get-Content -LiteralPath (Join-Path $workspace $map['independent_cached_review.json']) -Raw|ConvertFrom-Json
if($before['outer__final.json'].pin.sha256 -cne '0932f7050a2edf180a8bd7340d5fb64036eaca63805f90d635a29a2d3502ed8c' -or
    $outer.status -cne 'ACCEPTED_F041_NATIVE_FIRSTPASS_AND_RECONSTRUCTED28_PANEL' -or $null -ne $outer.error -or
    $null -ne $outer.postcheck_error -or $outer.owned_receipt.cleanup_accepted -ne $true -or
    $outer.owned_receipt.job_active_after_cleanup -ne 0 -or $outer.environment_restored -ne $true){throw 'No accepted clean outer'}
if($worker.status -cne 'ACCEPTED_F041_NATIVE_PANEL_AND_SOURCE_RECONSTRUCTED_LATENT' -or $null -ne $worker.error -or
    $worker.pretruth_frozen -ne $true -or $worker.evaluator_complete -ne $true -or $worker.monitor_stopped -ne $true -or
    $worker.job_query_handle_closed -ne $true -or $worker.denied.Count -ne 0 -or $worker.memory_errors.Count -ne 0 -or
    $worker.restoration_errors.Count -ne 0 -or $proof.status -cne 'PASS_CACHED_F041_RECOUNT_AND_LATENT_STATE_RECONSTRUCTION' -or
    $proof.source_prestate_fullvars_sha_matches -ne 120 -or $proof.independent_latent_row_equations -ne 3360){throw 'Native/parity/independent review insufficient'}
$caps=@{policy_builder=1;select=120;predict=120;update=120;theta_at=3360}
foreach($name in $caps.Keys){if($worker.attempted.$name -ne $caps[$name] -or $worker.returned.$name -ne $caps[$name]){throw 'Native/evaluator count mismatch'}}
$references=@{}
foreach($entry in $worker.source_before.PSObject.Properties){
    if($worker.source_after.($entry.Name) -cne $entry.Value -or (Pin (Join-Path $workspace $entry.Name)).sha256 -cne $entry.Value){throw 'Source changed'}
    $references[$entry.Name]=@{sha256=$entry.Value;bytes=(Get-Item -LiteralPath $entry.Name).Length}
}
$large=@{}
foreach($name in @('native_panel.jsonl','joined_panel.jsonl')){
    $path="$native/$name"
    $pin=Pin (Join-Path $workspace $path)
    if($pin.sha256 -cne $outer.outputs.$name.sha256 -or $pin.bytes -ne $outer.outputs.$name.bytes){throw 'Large output inventory mismatch'}
    $large[$path]=@{sha256=$pin.sha256;bytes=$pin.bytes;rows=3360;copied=$false}
}
foreach($name in @('summary.json','lineage.json','parity.json','reservation.json','native_metadata.json','resources.jsonl','result.json')){
    $pin=$before['native__'+$name].pin
    if($pin.sha256 -cne $outer.outputs.$name.sha256 -or $pin.bytes -ne $outer.outputs.$name.bytes){throw 'Small native output mismatch'}
}
New-Item -ItemType Directory -Path $target|Out-Null
Save 'inventory-before-copy.json' $before
$copied=@{}
foreach($alias in $map.Keys){
    $source=Join-Path $workspace $map[$alias]
    $dest=Join-Path $target $alias
    [IO.File]::Copy($source,$dest,$false)
    $copy=Pin $dest
    $after=Pin $source
    if($copy.sha256 -cne $before[$alias].pin.sha256 -or $after.sha256 -cne $copy.sha256 -or
        $copy.bytes -ne $before[$alias].pin.bytes -or $after.bytes -ne $copy.bytes){throw 'Copy/source bytes mismatch'}
    $copied[$alias]=@{before=$before[$alias];copy=$copy;source_after=$after}
}
foreach($path in $references.Keys){if((Pin (Join-Path $workspace $path)).sha256 -cne $references[$path].sha256){throw 'Referenced source after copy changed'}}
foreach($path in $large.Keys){if((Pin (Join-Path $workspace $path)).sha256 -cne $large[$path].sha256){throw 'Large output after copy changed'}}
Save 'copy-verification.json' $copied
Save 'reference-inputs-and-large-outputs.json' @{input_source_references=$references;large_outputs=$large}
$note=@'
# F041 · Native first-pass và latent panel toàn miền

Một native GAM policy replay120select/predict/update với action/P và endpoint exact trước khi ghi3360native states. Latent được dựng từ actual initial/transitions,120prestep fullvarsSHA và endpoint28khái niệm đều khớp. Không world constructor/interact/newresponse/RNG/NN. OwnedJob0, source/runtime guard sạch. NativeGAMupdates120 là actual model calls, không là NN fit.

Kết quả chỉ có lớp âm. All28 TN3360, queriedTN120 và notqueriedTN3240, mọi TP/FP/FN/nativeMtrue/latenttrue/thetagatetrue/suppression đều0. Không xác nhận classifier chính xác hoặc kiểm được cổng bất định khi opportunityθgateTrue=0. Một history/block N1, khác witness PG120, không graph/casual ability hoặc calibrated S04 claim.

[Báo cáo canonical](../../reports/rq1_f041_fixed_time_native_panel_20261110.md) giải thích nguồn và giới hạn. Copy trong bundle giữ nguyên byte theo vị trí canonical. Checker độc lập tái hiện3360phương trình/120SHA/endpoint và counts bằng stdlib trên cache, không gọi lại policy/getter/world/RNG.

Hai scientificJSONL giữ nguyên native output trong experiments/gam_kt/results/rq1-f041-native-panel-20261110-01, chỉ tham chiếu SHA/size trong inventory. Không nhân đôi raw parent hoặc các bundle cũ. Metadata nhỏ, source/plan/review, rawowned/outer logs và independentproof được copy với before/copy/after SHA. Completed của manifest chỉ là archive đã đóng, không cấp nghiên cứu mới hoặc hoàn tấtRQ.
'@
[IO.File]::WriteAllText((Join-Path $target 'README.md'),$note+"`n",[Text.UTF8Encoding]::new($false))
$outputs=@{}
foreach($file in Get-ChildItem -LiteralPath $target -File){$outputs[$file.Name]=(Pin $file.FullName).sha256}
Save 'manifest.json' @{schema_version=1;status='completed';kind='one_history_native_panel_and_reconstructed_latent_criterion';
    scientific_scope='N1_ALL_NEGATIVE_NO_CLASSIFIER_OR_UNCERTAINTY_GATE_VALIDATION';source_inventory_before=$before;
    outputs_sha256=$outputs;large_outputs_not_copied=$large;native_GAM_updates=120;new_world_response_calls=0;
    concepts=28;steps=120;repeated_rows=3360;history_units=1}
foreach($entry in $outputs.GetEnumerator()){if((Pin (Join-Path $target $entry.Key)).sha256 -cne $entry.Value){throw 'Closed output mismatch'}}
[PSCustomObject]@{status='VERIFIED_ARCHIVE_ONLY';path=$target;manifest=(Pin (Join-Path $target 'manifest.json')).sha256;outputs=$outputs.Count}|ConvertTo-Json
