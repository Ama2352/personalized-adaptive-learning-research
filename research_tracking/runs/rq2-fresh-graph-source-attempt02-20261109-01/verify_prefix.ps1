# Chỉ kiểm raw cached receipts/rows, không model/world/Python/RNG calls.
$ErrorActionPreference='Stop'
$prep=$PSScriptRoot
$root=$prep
1..4|ForEach-Object{$root=Split-Path -Parent $root}
$native=Join-Path $root 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02'
$resultPath=Join-Path $prep 'rq2_fresh02_prefix_verification01.json'
if(Test-Path $resultPath){throw 'exclusive verification receipt required'}
function Need($ok,[string]$message){if(-not $ok){throw $message}}
function Sha([string]$path){(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
function ReadJson([string]$path){Get-Content -LiteralPath $path -Raw|ConvertFrom-Json -AsHashtable}
function SameDouble($a,$b){[BitConverter]::DoubleToInt64Bits([double]$a)-eq[BitConverter]::DoubleToInt64Bits([double]$b)}
function Inventory{
 $map=[ordered]@{}
 foreach($f in Get-ChildItem -LiteralPath $native -File){$map[$f.Name]=[ordered]@{sha256=(Sha $f.FullName);bytes=$f.Length}}
 return $map
}
function Rows([string]$name){
 $groups=@{};$ordered=[Collections.Generic.List[object]]::new()
 foreach($raw in [IO.File]::ReadLines((Join-Path $native $name))){
  Need ($raw.Length-le16384) 'bounded row'
  $row=$raw|ConvertFrom-Json -AsHashtable
  if(-not$groups.ContainsKey($row.cell_id)){$groups[$row.cell_id]=[Collections.Generic.List[object]]::new()}
  $entry=@{row=$row;raw=$raw};$groups[$row.cell_id].Add($entry);$ordered.Add($entry)
 }
 return @{groups=$groups;ordered=$ordered}
}
$before=Inventory
Need ($before.Count-eq72) '72 native files'
$outerPath=Join-Path $prep 'rq2-fresh-graph-source02-outer/final.json'
Need ((Sha $outerPath)-eq'fb26467c7c4f58b4a678b8df2e7b326c9cc8ac8e336e4962afebea28ecdc93e9') 'root outer pin'
$outer=ReadJson $outerPath
$worker=ReadJson (Join-Path $native 'worker_run.json')
$plan=ReadJson (Join-Path $prep 'rq2_fresh_graph_source02_plan.json')
Need ($outer.status-eq'REJECTED_RETAIN_NO_RETRY' -and $worker.error.message-eq'Available1536MiB' -and $worker.error.active_cell-eq'F062') 'RAM failure scope'
Need ($worker.monitor_errors.Count-eq1 -and $worker.monitor_errors[0]-eq'ValueError: Available1536MiB' -and $worker.monitor_stopped -and $worker.job_query_handle_closed) 'sole RAM monitor failure'
$o=$outer.owned_receipt
Need ($o.returncode-eq1 -and $o.cleanup_accepted -and $o.job_active_after_cleanup-eq0 -and $o.popen_handle_closed -and $o.actual_worker_in_job_before_GO -and $o.GO_released -and $o.errors.Count-eq0) 'owned actual body/cleanup'
$pins=@{};foreach($kind in @('source_sha256','inputs_sha256')){foreach($k in $plan[$kind].Keys){$pins[$k]=$plan[$kind][$k]}}
Need ($pins.Count-eq61) '61pins'
foreach($name in $pins.Keys){
 Need ((Sha (Join-Path $root $name))-eq$pins[$name]) 'current61sourcepin'
 foreach($mapping in @($worker.source_input_before_sha256,$worker.source_input_after_sha256,$outer.source_input_before_sha256,$outer.source_input_after_sha256)){Need ($mapping.Count-eq61 -and $mapping[$name]-eq$pins[$name]) '61beforeafterpin'}
}
foreach($api in @('interact','predict','select','update','oracle_theta_probe','oracle_probability_probe')){
 Need ($worker.direct_attempts[$api]-eq7350 -and $worker.direct_returns[$api]-eq7350) 'actual7350calls'
}
foreach($entry in @(@('environment_constructor',62),@('policy_builder',62),@('snapshot',61),@('anchor_generation',10),@('uniform_array_generation',10))){
 Need ($worker.direct_attempts[$entry[0]]-eq$entry[1] -and $worker.direct_returns[$entry[0]]-eq$entry[1]) 'factory/generation actual counts'
}
Need ($worker.direct_attempts.Count-eq11 -and $worker.direct_returns.Count-eq11 -and $worker.completed_cells-eq61 -and $worker.reserved_interact_attempts-eq7440) 'counter cardinality/reservation'
$obs=Rows 'observables.jsonl';$oracle=Rows 'oracle.jsonl';$ends=Rows 'oracle_endpoints.jsonl'
Need ($obs.ordered.Count-eq7350 -and $oracle.ordered.Count-eq7350 -and $ends.ordered.Count-eq61) 'raw totals'
$ledger=@([IO.File]::ReadLines((Join-Path $native 'cell_ledger.jsonl'))|ForEach-Object{$_|ConvertFrom-Json -AsHashtable})
Need ($ledger.Count-eq123) '123 ledgerrows'
$committed=[Collections.Generic.List[string]]::new()
for($i=0;$i-lt62;$i++){
 $cell=$plan.cells[$i];$id=$cell.cell_id;$expectedCount=$(if($i-lt61){120}else{30})
 Need ($obs.groups[$id].Count-eq$expectedCount -and $oracle.groups[$id].Count-eq$expectedCount) 'percell trace count'
 $reserve=$ledger[2*$i]
 Need ($reserve.event-eq'RESERVED_BEFORE_WORLD' -and $reserve.cell.cell_id-eq$id -and $reserve.cumulative_reserved-eq120*($i+1)) 'ordered reservations'
 $initial=ReadJson (Join-Path $native ('initial-'+$id+'.json'))
 Need ($initial.cell.cell_id-eq$id -and $initial.initial_state_scope-eq'ACTUAL_FRESH_SNAPSHOT_BEFORE_RESPONSE1') 'initial snapshot binding'
 $timestamp=[long]1767225600000000000
 for($step=0;$step-lt$expectedCount;$step++){
  $a=$obs.groups[$id][$step].row;$b=$oracle.groups[$id][$step].row
  Need ($a.step-eq$step -and $b.step-eq$step -and $a.cell_id-eq$id -and $b.cell_id-eq$id) 'complete chronological prefixes'
  $timestamp += $(if($step-gt0 -and $step%28-eq0){[long]259200000000000}else{[long]21600000000000})
  Need ($a.query.timestamp_ns-eq$timestamp) 'source clock'
  Need (($a.correct-eq0-or$a.correct-eq1) -and $a.probability-ge0 -and $a.probability-le1 -and (SameDouble $b.result.p_true $b.oracle_probability) -and (SameDouble $b.result.theta_before $b.oracle_theta_before) -and $a.correct-eq$b.result.y -and $a.correct-eq[int]($b.outcome_uniform-lt$b.oracle_probability)) 'response/oracle record identity'
 }
 if($i-lt61){
  $commit=$ledger[2*$i+1];$end=$ends.groups[$id][0].row
  Need ($commit.event-eq'COMPLETED_CELL' -and $commit.cell_id-eq$id -and $commit.cumulative_returns.interact-eq120*($i+1) -and (SameDouble $commit.outcome.outcome $end.net_mean_theta_gain)) 'committed endpoint'
  Need ($end.base_sha256-eq$reserve.base_sha256 -and $commit.outcome.latent_identity-eq$reserve.base_sha256 -and $commit.outcome.uniform_identity-eq$reserve.uniform_sha256) 'committed component identities'
  $committed.Add($id)
 }else{Need (-not$ends.groups.ContainsKey($id)) 'partial no endpoint/commit'}
}
Need ($obs.groups.Count-eq62 -and $oracle.groups.Count-eq62 -and $ends.groups.Count-eq61 -and @(Get-ChildItem $native -Filter 'initial-*.json').Count-eq62) 'no hidden extra cells'
$high=[Collections.Generic.List[object]]::new()
foreach($block in 21010..21019){foreach($graph in @('full','learned')){
 $pair=@($plan.cells|Where-Object{$_.block-eq$block-and$_.graph-eq$graph-and$_.ability-eq1300})
 Need ($pair.Count-eq2) 'high key pair'
 $id0=($pair|Where-Object mechanism_strength -eq 0).cell_id;$id1=($pair|Where-Object mechanism_strength -eq 0.55).cell_id
 foreach($kind in @($obs,$oracle,$ends)){
  Need ($kind.groups[$id0].Count-eq$kind.groups[$id1].Count) 'high pair rowcount'
  for($i=0;$i-lt$kind.groups[$id0].Count;$i++){
   Need ($kind.groups[$id0][$i].raw.Replace(('"cell_id":"'+$id0+'"'), '"cell_id":"HIGH"')-ceq$kind.groups[$id1][$i].raw.Replace(('"cell_id":"'+$id1+'"'), '"cell_id":"HIGH"')) 'high exact raw semantic rows sans cell alias'
  }
 }
 foreach($r in $oracle.groups[$id0]){Need ($r.row.result.prerequisite_deficit-eq0-and$r.row.result.prereq_violation-eq0) 'high inactive mechanism'}
 $high.Add([ordered]@{block=$block;graph=$graph;observable_rows=120;oracle_rows=120;endpoint_exact=$true})
}}
$shared=ReadJson (Join-Path $native 'shared_inputs.json');$seed=ReadJson (Join-Path $native 'seed_reservation.json')
Need ($shared.blocks.Count-eq10-and$shared.global_numpy_rng_unchanged-and$seed.status-eq'RESERVED_BEFORE_ANY_DRAW') 'generated10 shared immutable inputs'
Need ([BitConverter]::IsLittleEndian) 'native Windows little-endian float64 U identity'
foreach($block in $shared.blocks){
 Need ($block.block-ge21010-and$block.block-le21019-and$block.uniform_shape[0]-eq120-and$block.uniform_shape[1]-eq2-and$block.uniform_dtype-eq'float64') 'U geometry'
 $bytes=[Collections.Generic.List[byte]]::new()
 foreach($row in $block.uniforms){foreach($u in $row){Need ([double]$u-ge0-and[double]$u-lt1) 'U finite range';$bytes.AddRange([BitConverter]::GetBytes([double]$u))}}
 $h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes.ToArray())).ToLowerInvariant()
 Need ($h-eq$block.uniform_sha256) 'saved U exact byte hash'
 foreach($ability in @('1000','1150','1300')){foreach($node in $shared.node_order){Need (SameDouble $block.bases[$ability][$node] ([double]$ability+[double]$block.centered_residual[$node])) 'stored scalar+residual'} }
}
$minimum=($worker.resources|Measure-Object available_bytes -Minimum).Minimum
$maxFamily=($worker.resources|Measure-Object family_rss_bytes -Maximum).Maximum
Need ($worker.resources.Count-eq1343-and$minimum-eq1608359936-and$minimum-lt1610612736-and$maxFamily-le536870912) 'failure resource evidence'
Need (@($worker.resources|Where-Object{$_.scope-ne'SAMPLED_EXACT_OWNED_JOB_RSS_AND_WORKER_HIGHWATER_NOT_OS_QUOTA'-or$_.job_member_count-lt1-or$_.job_member_count-gt16}).Count-eq0) 'exact Job sample scope'
$after=Inventory
foreach($name in $before.Keys){Need ($after[$name].sha256-eq$before[$name].sha256-and$after[$name].bytes-eq$before[$name].bytes) 'native source unchanged'}
$result=[ordered]@{status='VERIFIED_RAM_STOP_PREFIX61_COMPLETE_F062_PARTIAL30_NOT_PRIMARY120';verifier_sha256=(Sha $PSCommandPath);outer_sha256=(Sha $outerPath);worker_sha256=(Sha (Join-Path $native 'worker_run.json'));plan_sha256=(Sha (Join-Path $prep 'rq2_fresh_graph_source02_plan.json'));source_input_pins=61;source_before_after_current_equal=$true;raw_observables=7350;raw_oracle=7350;raw_endpoints=61;raw_ledger=123;initial_snapshots=62;committed_cell_ids=$committed.ToArray();partial_cell='F062';partial_complete_responses=30;high_pairs=$high.ToArray();shared_blocks=10;private_generation_api_returns=20;new_model_world_calls_in_this_verification=0;direct_actual_interact_returns=7350;parent_reservations=7440;unused_parent_reserved_slots=90;owned_cleanup_job0=$true;job_query_handle_closed=$true;sole_failure='Available1536MiB';resource_samples=1343;minimum_available_bytes=$minimum;max_exact_job_rss_bytes=$maxFamily;native_files_sha256_and_bytes=$before;all_native_bytes_unchanged=$true;no_primary_experiment_or_partial_QK_acceptance=$true;parent_outer_elapsed_seconds=$outer.elapsed_seconds;scope='Read-only post-run raw verification, no policy/world/RNG/Python calls'}
[IO.File]::WriteAllText($resultPath,($result|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
Write-Output ('VERIFIED '+(Sha $resultPath))