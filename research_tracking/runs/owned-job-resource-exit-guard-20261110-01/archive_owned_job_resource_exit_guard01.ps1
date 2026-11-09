# Metadata archive only. Không chạy lại probe, tests, Git hoặc native A1.
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$p=[IO.Path]::GetRelativePath($root,$PSScriptRoot).Replace('\','/')
$target=Join-Path $root 'research_tracking/runs/owned-job-resource-exit-guard-20261110-01'
if(Test-Path -LiteralPath $target){throw 'Exclusive closed bundle'}
function Pin([string]$path){
    $item=Get-Item -LiteralPath $path
    if($item.PSIsContainer -or $item.Length -gt 262144){throw 'Small regular metadata/source only'}
    return @{sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$item.Length}
}
function Save([string]$name,$value){
    $path=Join-Path $target $name
    if(Test-Path -LiteralPath $path){throw 'No overwrite'}
    [IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 35)+"`n",[Text.UTF8Encoding]::new($false))
}
$map=@{}
foreach($name in @('check_a1_expert_engineering01.py','check_a1_expert_engineering02.py','check_a1_expert_engineering03.py',
    'run_a1_expert_engineering01.py','a1_expert_engineering01_request.ROOT.json',
    'a1_expert_engineering_source_inventory02.json','ROOT_A1_EXPERT_ENGINEERING_REVIEW01.md',
    'ROOT_A1_EXPERT_ENGINEERING_DRY_REVIEW01.md','ROOT_A1_EXPERT_ENGINEERING_ACTUAL_FIT_REVIEW01.md',
    'check_a1_job_resource_probe01.py','run_a1_job_resource_probe01.py','a1_job_resource_probe01_packet.json',
    'check_a1_job_resource_probe02.py','run_a1_job_resource_probe02.py','a1_job_resource_probe02_packet.json',
    'check_a1_membership_exit_probe_root01.py','run_a1_membership_exit_probe_root01.py','a1_membership_exit_probe_root01_packet.json',
    'prepare_membership_exit_probe_root01.py','test_a1_resource_wait_guard01.py',
    'run_a1_wait_guard_canaries01.py','run_a1_wait_guard_canaries02.py','archive_owned_job_resource_exit_guard01.ps1')){
    $map[$name]="$p/$name"
}
foreach($name in @('reservation.json','resource-failure.json','outer-final.json','windows-metadata.json')){
    $map['a1_failure01__'+$name]="$p/a1-expert-engineering01/$name"
}
foreach($name in @('GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log')){
    $map['a1_failure01_owned__'+$name]="$p/a1-expert-engineering01-owned/$name"
}
foreach($prefix in @('a1-job-resource-probe02','a1-membership-exit-probe-root01')){
    $map[$prefix+'__result.json']="$p/$prefix/result.json"
    $map[$prefix+'__outer-final.json']="$p/$prefix-outer/final.json"
    foreach($name in @('GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log')){
        $map[$prefix+'__owned-'+$name]="$p/$prefix-owned/$name"
    }
}
$map['guard_canary01__failure-note.json']="$p/a1-resource-wait-guard-canaries01/failure-note.json"
foreach($name in @('result.json','stdout.log','stderr.log')){$map['guard_canary02__'+$name]="$p/a1-resource-wait-guard-canaries02/$name"}
$before=@{}
foreach($alias in $map.Keys){$before[$alias]=@{source=$map[$alias];pin=(Pin (Join-Path $root $map[$alias]))}}
if($before['check_a1_expert_engineering03.py'].pin.sha256 -cne 'a6fa2e3838d27e288ad1be8ecb33058ef3f7062c0258b4d8b3fb6c765038cc42' -or
    $before['test_a1_resource_wait_guard01.py'].pin.sha256 -cne '7f7715c74c7bea80abc9d02ca9f61e6c4a0795f12ec764bd0fc9a78f4320311a'){throw 'Frozen guard/test pins'}
$facts=@{}
foreach($prefix in @('a1-job-resource-probe02','a1-membership-exit-probe-root01')){
    $outer=Get-Content -LiteralPath (Join-Path $root $map[$prefix+'__outer-final.json']) -Raw|ConvertFrom-Json
    $worker=Get-Content -LiteralPath (Join-Path $root $map[$prefix+'__result.json']) -Raw|ConvertFrom-Json
    if($outer.status -cne 'ACCEPTED_OWNED_RESOURCE_IDENTITY_PROBE_NO_MODELS' -or $null -ne $outer.error -or
        $outer.owned_receipt.accepted -ne $true -or $outer.owned_receipt.cleanup_accepted -ne $true -or
        $outer.owned_receipt.job_active_after_cleanup -ne 0 -or $outer.elapsed_seconds -ge 30 -or
        $worker.status -cne 'RESOURCE_IDENTITY_PROBE_PENDING_OUTER' -or $null -ne $worker.error -or
        $worker.cleanup_errors.Count -ne 0 -or $worker.model_calls -ne 0 -or $worker.scientific_modules_absent -ne $true -or
        $worker.query_handle_closed -ne $true -or $worker.denied.Count -ne 0 -or $worker.proof.pure_canaries.passed -ne 5 -or
        $worker.proof.git_calls -ne 4 -or $worker.proof.git_children.Count -ne 4 -or $worker.popen_handles_closed -ne 4 -or
        $worker.proof.old_WinError5_reproduced -ne $false){throw 'Accepted probe binding'}
    if(Test-Path -LiteralPath (Join-Path $root "$p/$prefix-outer/postwrite-rejection.json")){throw 'Late probe rejection'}
    $win31=0;$membership=0
    foreach($child in $worker.proof.git_children){
        if($child.WaitForSingleObject -ne 0 -or $child.GetExitCodeProcess -ne 0 -or $child.resource_identity_after_exit_exact -ne $true){throw 'Exact exit proof'}
        if($null -ne $child.old_after_exit_error){
            if($child.old_after_exit_error.winerror -ne 31 -or $child.old_after_exit_error.exit_already_proven -ne $true){throw 'Expected stored old-token error'}
            $win31++
        }
        if($prefix -eq 'a1-membership-exit-probe-root01'){
            if($child.membership_after_exit.returned -ne $true -or $null -ne $child.membership_after_exit.error){throw 'Actual membership observations'}
            $membership++
        }
    }
    if($win31 -ne 4 -or $worker.proof.old_token_after_exit_errors -ne 4){throw 'Four old-token WIN31 records, not all worked'}
    foreach($entry in $worker.source_before.PSObject.Properties){if($worker.source_after.($entry.Name) -cne $entry.Value){throw 'Probe before/after source changed'}}
    $facts[$prefix]=@{outer_sha256=$before[$prefix+'__outer-final.json'].pin.sha256;
        actual_git_children=4;pure_helper_canaries=5;old_token_Win31_after_proven_exit=$win31;old_Win5_reproduced=$false;
        IsProcessInJob_true_after_exit=$membership;elapsed_seconds=$outer.elapsed_seconds;owned_job_after_cleanup=0;
        model_calls=0;original_Win5_cause='UNRESOLVED_NOT_CONFIRMED_BY_THESE_PROBES'}
}
$unit=Get-Content -LiteralPath (Join-Path $root $map['guard_canary02__result.json']) -Raw|ConvertFrom-Json
$counts=Get-Content -LiteralPath (Join-Path $root $map['guard_canary02__stdout.log']) -Raw|ConvertFrom-Json
if($unit.returncode -ne 0 -or $unit.elapsed_seconds -gt $unit.timeout_seconds -or $unit.source_unchanged -ne $true -or
    $counts.tests -ne 9 -or $counts.failures -ne 0 -or $counts.errors -ne 0 -or $counts.skipped -ne 0 -or $counts.heavy_imports.Count -ne 0){throw 'Actual nine canaries'}
foreach($entry in $unit.source_before.PSObject.Properties){
    if($unit.source_after.($entry.Name) -cne $entry.Value -or $before[$entry.Name].pin.sha256 -cne $entry.Value){throw 'Canary tested source drift'}
}
$old=Get-Content -LiteralPath (Join-Path $root $map['a1_failure01__outer-final.json']) -Raw|ConvertFrom-Json
$failure=Get-Content -LiteralPath (Join-Path $root $map['a1_failure01__resource-failure.json']) -Raw|ConvertFrom-Json
if($old.status -cne 'REJECTED_KEEP_PARTIAL_NO_RESUME' -or $old.owned_receipt.returncode -ne 125 -or
    $old.owned_receipt.job_active_after_cleanup -ne 0 -or $old.owned_receipt.cleanup_accepted -ne $true -or
    $failure.errors.Count -ne 1 -or $failure.errors[0].type -cne 'PermissionError' -or $failure.errors[0].message -notmatch 'WinError 5'){
    throw 'Original failure preserved'
}
$request=Get-Content -LiteralPath (Join-Path $root $map['a1_expert_engineering01_request.ROOT.json']) -Raw|ConvertFrom-Json
$configPath=Join-Path $root $request.native_config_file
$config=Get-Content -LiteralPath $configPath -Raw|ConvertFrom-Json
$native=[IO.Path]::GetFullPath($config.output_dir)
$allowed=Join-Path $root 'experiments/akt/results/main-a1-expert-engineering10x84-20261110-01'
if($native -cne [IO.Path]::GetFullPath($allowed) -or (Test-Path -LiteralPath $native)){throw 'Original native output absence proof'}
$refs=@{}
foreach($path in @('scripts/research/windows_owned_worker.py','src/knowledge_tracing/akt/research_selected_runner.py')){
    $refs[$path]=Pin (Join-Path $root $path)
}
if($refs['scripts/research/windows_owned_worker.py'].sha256 -cne '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'){throw 'Canonical Kernel.token changed'}
$refs[$request.native_config_file]=Pin $configPath
foreach($dir in @('windows-owned-worker-engineering-20261108-01','owned-job-family-query-engineering-20261109-01')){
    $rel="research_tracking/runs/$dir/manifest.json";$refs[$rel]=Pin (Join-Path $root $rel)
}
New-Item -ItemType Directory -Path $target|Out-Null
Save 'inventory-before-copy.json' $before
$copies=@{}
foreach($alias in $map.Keys){
    $source=Join-Path $root $map[$alias];$dest=Join-Path $target $alias
    [IO.File]::Copy($source,$dest,$false)
    $copy=Pin $dest;$after=Pin $source
    if($copy.sha256 -cne $before[$alias].pin.sha256 -or $copy.bytes -ne $before[$alias].pin.bytes -or
        $after.sha256 -cne $copy.sha256 -or $after.bytes -ne $copy.bytes){throw 'Copy/source mismatch'}
    $copies[$alias]=@{before=$before[$alias];copy=$copy;source_after=$after}
}
foreach($path in $refs.Keys){if((Pin (Join-Path $root $path)).sha256 -cne $refs[$path].sha256){throw 'Reference source drift'}}
if(Test-Path -LiteralPath $native){throw 'Original native output changed after archive'}
Save 'copy-verification.json' $copies
Save 'reference-inputs.json' @{sources=$refs;native_failure01_output_relative=[IO.Path]::GetRelativePath($root,$native).Replace('\','/');
    original_native_output_absent_before_and_after=$true;new_A1_or_GKT_requests_copied=$false;corpus_or_model_copied=$false}
Save 'observed-facts.json' @{probes=$facts;unit_canaries=@{tests=9;failures=0;errors=0;skipped=0;elapsed_seconds=$unit.elapsed_seconds};
    original_A1_failure='WinError5_WITHOUT_CALL_TRACE_CAUSE_UNRESOLVED';original_A1_reserved_work_is_not_actual_work=$true;
    source_guard03_private_only=$true;canonical_Kernel_token_unchanged=$true;new_scientific_N=0;NN_calls_in_probes_or_canaries=0}
$note=@'
# Guard tài nguyên owned Job · bằng chứng vận hành

Bundle giữ một failure A1 trước model output, hai probe Git read-only và chín canary WinAPI chế tạo. Không chạy lại model, probe, tests hoặc Git khi đóng gói. Các request/worker GKT và request A1 tương lai không được lấy vào bundle. Source guard03 là bản private đã freeze, chưa sửa canonical Kernel.token và không tự cấp quyền native retry.

## Phân biệt ba quan sát

Lượt A1 failure01 dừng bởi PermissionError WinError5 trong bộ đo RAM. Outer rejected, worker exit125, owned cleanup đạt và Job0. Resource-failure không có traceback xác định API hoặc PID gây lỗi. Native output directory của chính allocation01 không tồn tại trước/sau archive, config/source được ghim để kiểm ranh giới. Reservation40updates là trần, không được đọc thành actual updates. Lượt này không tạo NN model output theo control-flow của source, nhưng các probe sau chưa chứng minh nguyên nhân WinError5.

Resource probe02 có bốn Git children thật, từng handle đã signaled Wait0/exit0, creation-only identity trước/sau khớp. Raw hiện ghi cả4/4 lời gọi old Kernel.token sau exit gặp WinError31 tại QueryFullProcessImageNameW. Cờ old_WinError5_reproduced=False KHÔNG có nghĩa mọi old token đều chạy được. Giữ nguyên raw lỗi31 và không gọi nó là lỗi5 ban đầu.

Membership probe Root01 cũng có4/4 old token WinError31 sau Wait0; IsProcessInJob trả True ở cả4 handle đã exit. Đây là quan sát hữu hạn, không khẳng định IsProcessInJob luôn thành công sau mọi exit. Cả hai probe accepted theo outer, Job0 và handle cleanup đạt. Thời gian outer lưu nằm trong observed-facts.json, tách khỏi quan sát terminal của Root nếu có.

## Guard và giới hạn

Guard RAM dùng query-limited cùng synchronize trên exact handle. Chỉ WaitForSingleObject trả WAIT_OBJECT_0 mới nhận trạng thái đã kết thúc. Live/unknown/WAIT_FAILED và PID/creation mismatch vẫn bị từ chối. PermissionError chỉ được ghi nhận như race kết thúc nếu chính handle đó đã được xác nhận signaled. Đóng góp RSS hiện tại bằng0 của member đã exit không phải historical peak0. RAM là telemetry lấy mẫu, không hard OS quota hoặc bằng chứng không thể có peak giữa samples.

Chín canary thực tế đạt0FES trong0,3629403giây/cap5, không heavy imports. Giữ failure controller01 trước dispatch vì sai tên file pin, controller02 và logs đã chạy. Probe01 chỉ là source review bị yêu cầu sửa cleanup trước dispatch, không một lượt actual probe thất bại. Source01/packet/outer được giữ riêng. Probe02 đã bổ sung perchild cleanup tiếp tục khi lỗi, receipt giữ primary/cleanup riêng và timer dừng.

Tài liệu API Microsoft đã đối chiếu cho quyền handle và trạng thái wait. Đây là mô tả API, không thay actual owned probe.

- [WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).
- [GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes).

Nguồn/sourcepins nhỏ được copy với inventory trước/copy/sau và manifest readback. Canonical helper cùng các bundle nền chỉ tham chiếu SHA, không nhân đôi runtime/dependency/corpus/model. Manifest completed xác nhận archive vận hành, không nghiệm thu Main fitted model, CUDA, matrix hoặc RQ.
'@
[IO.File]::WriteAllText((Join-Path $target 'README.md'),$note+"`n",[Text.UTF8Encoding]::new($false))
$outputs=@{}
foreach($file in Get-ChildItem -LiteralPath $target -File){$outputs[$file.Name]=(Pin $file.FullName).sha256}
Save 'manifest.json' @{schema_version=1;status='completed';kind='private_owned_job_resource_exit_guard_operational_evidence';
    outputs_sha256=$outputs;source_inventory_before=$before;reference_sources=$refs;
    probes=2;actual_git_children=8;pure_source_helper_checks_per_probe=5;unit_guard_tests=9;
    scientific_N=0;NN_calls=0;canonical_helper_changed=$false;original_Win5_cause_resolved=$false}
foreach($entry in $outputs.GetEnumerator()){if((Pin (Join-Path $target $entry.Key)).sha256 -cne $entry.Value){throw 'Closed output mismatch'}}
[pscustomobject]@{status='VERIFIED_METADATA_ARCHIVE_ONLY';path=$target;outputs=$outputs.Count;manifest=(Pin (Join-Path $target 'manifest.json')).sha256}|ConvertTo-Json
