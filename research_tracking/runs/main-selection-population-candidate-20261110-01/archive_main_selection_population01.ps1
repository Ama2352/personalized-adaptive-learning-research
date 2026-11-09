# Đóng evidence của candidate private và actual6tests. Không chạy lại tests/Git.
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$p=[IO.Path]::GetRelativePath($root,$PSScriptRoot).Replace('\','/')
$target=Join-Path $root 'research_tracking/runs/main-selection-population-candidate-20261110-01'
if(Test-Path -LiteralPath $target){throw 'Closed bundle already exists'}
function Pin([string]$path){
    $item=Get-Item -LiteralPath $path
    if($item.PSIsContainer -or $item.Length -gt 262144){throw 'Small regular file required'}
    return @{sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$item.Length}
}
function Save([string]$name,$value){
    $path=Join-Path $target $name
    if(Test-Path -LiteralPath $path){throw 'No overwrite'}
    [IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 25)+"`n",[Text.UTF8Encoding]::new($false))
}
$map=@{}
foreach($name in @('main_selection_population_candidate01.py','test_main_selection_population_candidate01.py',
    'MAIN_SELECTION_POPULATION_HANDOFF01.md','run_population_candidate_tests01.py',
    'MAIN_NEXT_CRITICAL_PATH_REVIEW01.md','MAIN_EXTERNAL_FREEZE_IO_SPEC01.md','archive_main_selection_population01.ps1',
    'archive_main_selection_population01.ps1.before-parser-fix','main_population_archive_startup01_note.json')){
    $map[$name]="$p/$name"
}
foreach($name in @('result.json','stdout.log','stderr.log')){$map['tests__'+$name]="$p/main-selection-population-tests01/$name"}
$before=@{}
foreach($alias in $map.Keys){$before[$alias]=@{source=$map[$alias];pin=(Pin (Join-Path $root $map[$alias]))}}
$expected=@{'main_selection_population_candidate01.py'='8709f62a4aeed14bb3bfd8581e419205a0e8695d7eb3312832c96d7b64ef1906';
    'test_main_selection_population_candidate01.py'='ce9c8626193326ab2a43ebc65da81917b49f2139da3066885bf4e11005f66627'}
$result=Get-Content -LiteralPath (Join-Path $root $map['tests__result.json']) -Raw|ConvertFrom-Json
$counts=Get-Content -LiteralPath (Join-Path $root $map['tests__stdout.log']) -Raw|ConvertFrom-Json
$stderr=Get-Content -LiteralPath (Join-Path $root $map['tests__stderr.log']) -Raw
if($before['tests__result.json'].pin.sha256 -cne 'f0f2479ec7a9077550aa6d3900bcfc54b314c61bee48c20700d4c7f3d01a70db' -or
    $result.returncode -ne 0 -or $result.elapsed_seconds -gt 10 -or $result.timeout_seconds -ne 10 -or
    $result.source_unchanged -ne $true -or $counts.tests -ne 6 -or $counts.failures -ne 0 -or
    $counts.errors -ne 0 -or $counts.skipped -ne 0 -or $counts.heavy_imports.Count -ne 0 -or
    ($stderr -split '\r?\n')[-2] -ne 'OK'){throw 'Actual six-test receipt/log mismatch'}
foreach($name in $expected.Keys){
    if($result.source_before.$name -cne $expected[$name] -or $result.source_after.$name -cne $expected[$name] -or
        $before[$name].pin.sha256 -cne $expected[$name]){throw 'Tested source drift'}
}
$refs=@{
    'src/knowledge_tracing/research_admission.py'='b8601da03a972834cfd2f5596ea6a6b9c5759437796b4f4b65720f7abc1a92f2';
    'src/knowledge_tracing/simulator_corpus_reader.py'='e582bf293e7699f1dc98096fcc693437610f2253bddb11ba4fff8952a35f6a90';
    'src/knowledge_tracing/simulator_bridge.py'='b29105acd8de84b060ca27573bb7f7cf8e85599a4596e50e4a21ab63c82329d2';
    'src/knowledge_tracing/simulator_data.py'='79e28c1a8fc9b3bd5f3283868d7aba1a5bbc7c76764725a8b01098b2ae33cd9f';
    'src/knowledge_tracing/simulator_research_data.py'='51eb7275a6a4a6b26b763a21a8fe6dc15b0973fc19b3c5557175eaa298db7e53';
    'src/knowledge_tracing/akt/research_simulator_data.py'='9596c2dc5ae86cdf89e5f68c15224a6794b6056093dabee6b26502dfabdf092b'
}
$references=@{}
foreach($path in $refs.Keys){$pin=Pin (Join-Path $root $path);if($pin.sha256 -cne $refs[$path]){throw 'Referenced source drift'};$references[$path]=$pin}
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
foreach($path in $references.Keys){if((Pin (Join-Path $root $path)).sha256 -cne $references[$path].sha256){throw 'Reference after drift'}}
Save 'copy-verification.json' $copies
Save 'reference-source-pins.json' $references
Save 'scope.json' @{task='GRAPH14';component='trusted_selection_population_expectation';supports_dependency='GRAPH13';
    actual_unittest_methods=6;new_independent_N=0;actual_corpus_reads=0;model_world_calls=0;canonical_applied=$false;
    full_nine_file_admission=$false;external_freeze_authority=$false;refit_authorized=$false;task_complete=$false;
    root_runner_name='run_population_candidate_tests01.py';test_elapsed_seconds=$result.elapsed_seconds;
    static_helper_invocations=13;static_count_scope='SOURCE_EXPECTATION_ONLY_NOT_OBSERVED_CALL_LEDGER'}
$note=@'
# Helper kỳ vọng quần thể selection · candidate private

Sáu unittest manufactured thực tế đạt0failure/error/skip trong0,4869987giây, cap10giây. Raw stdout/stderr, receipt và runner Root được giữ nguyên. Không có heavy import trong test. Không chạy lại tests khi đóng bundle.

Helper nhận PublicRoleData selection từ trusted public reader, ghim context/provenance/audit, giữ chronology để dựng observable prefix trước nhãn hiện tại và chỉ sort K cho statistical hash. Tái dùng ModelNeutralKey, PopulationExpectation và canonical record encoding. Recompute shard hash phát hiện label mutation. Các fixtures kiểm chronology khác item ordering, labels, duplicates, wrongrole/empty, caps, invalidbinary và oneclass/domain mismatch. Audit-shaped records được chế tạo cho test, không phải actual corpus hoặc proof native collection.

Đây là component subset của GRAPH14, hỗ trợ population prerequisite của GRAPH13. Chưa complete9artifactvalidator, external freeze/winner hoặc refit authority. Candidate vẫn ở prep, chưa apply vào canonical. Software Gate183 và production source không bị thay đổi bởi gói này. Các core nguồn hiện có được tham chiếu SHA, không copy lại corpus hoặc model.

MAIN_NEXT_CRITICAL_PATH_REVIEW01 và MAIN_EXTERNAL_FREEZE_IO_SPEC01 là source-only review/spec, có mức bằng chứng khác với sáu tests. Manifest completed chỉ xác nhận archive integrity, không hoàn tất GRAPH14, Main matrix hoặc RQ. Không Git hoặc human report edits trong lượt đóng gói.

Archiver startup01 bị parser từ chối trước thực thi vì hai hashtable keys .py thiếu dấu nháy. Bản source trước sửa và ghi chú từ tool transcript được giữ, không gọi ghi chú đó là raw subprocess log. Candidate/test sources và raw actual6 không đổi, chỉ archiver được sửa trước khi đóng bundle.
'@
[IO.File]::WriteAllText((Join-Path $target 'README.md'),$note+"`n",[Text.UTF8Encoding]::new($false))
$outputs=@{}
foreach($file in Get-ChildItem -LiteralPath $target -File){$outputs[$file.Name]=(Pin $file.FullName).sha256}
Save 'manifest.json' @{schema_version=1;status='completed';kind='private_selection_population_candidate_unit_evidence';
    outputs_sha256=$outputs;source_inventory_before=$before;reference_sources=$references;
    task_mapping=@{task='GRAPH14';component='population_expectation_only';dependency='GRAPH13';task_completed=$false};
    tests=6;canonical_applied=$false;full_nine_IO_admission=$false;winner_or_refit_authority=$false}
foreach($entry in $outputs.GetEnumerator()){if((Pin (Join-Path $target $entry.Key)).sha256 -cne $entry.Value){throw 'Closed manifest mismatch'}}
[pscustomobject]@{status='VERIFIED_ARCHIVE_ONLY';path=$target;outputs=$outputs.Count;manifest=(Pin (Join-Path $target 'manifest.json')).sha256}|ConvertTo-Json
