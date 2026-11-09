# Chỉ đọc cached outputs và tính lại JSON contrasts, không model/Python/simulation.
$ErrorActionPreference = 'Stop'
$prep = $PSScriptRoot
$root = $prep
1..4 | ForEach-Object { $root = Split-Path -Parent $root }
$native = Join-Path $root 'experiments/simulator/results/rq2-learned-graph-ability-20261109-01'
$old = Join-Path $root 'research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01'
$resultPath = Join-Path $prep 'rq2_learned19_independent_verification01.json'
if (Test-Path -LiteralPath $resultPath) { throw 'Exclusive new verification receipt required' }
function Assert-That($condition, [string]$message) { if (-not $condition) { throw $message } }
function Read-Json([string]$path) { Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -Depth 100 }
function Sha([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Same-Double($left, $right) {
    [BitConverter]::DoubleToInt64Bits([double]$left) -eq [BitConverter]::DoubleToInt64Bits([double]$right)
}
function Key($block, $ability, $strength) { '{0}|{1}|{2:R}' -f [int]$block, [int]$ability, [double]$strength }
function Read-Rows([string]$path) {
    $rows = @{}
    foreach ($raw in [IO.File]::ReadLines($path)) {
        $row = $raw | ConvertFrom-Json -Depth 60
        if (-not $rows.ContainsKey($row.cell_id)) { $rows[$row.cell_id] = [Collections.Generic.List[object]]::new() }
        $rows[$row.cell_id].Add([pscustomobject]@{ Parsed = $row; Raw = $raw })
    }
    return $rows
}
$outerPath = Join-Path $prep 'rq2-learned-graph-ability01-outer/final.json'
Assert-That ((Sha $outerPath) -eq '55be940503c2f09cc5b2baf4966a14c3ac039a6ed6918d130792ef9c57b8625b') 'Accepted outer raw SHA'
$outer = Read-Json $outerPath
$worker = Read-Json (Join-Path $native 'worker_run.json')
$plan = Read-Json (Join-Path $prep 'rq2_learned_graph_ability01_plan.json')
$oldPlan = Read-Json (Join-Path $old 'plan.json')
Assert-That ($outer.status -eq 'ACCEPTED19_FINITE_LEARNED_GRAPH_SOURCE_EXTENSION') 'Actual accepted status'
Assert-That ($outer.owned_receipt.accepted -and $outer.owned_receipt.cleanup_accepted -and
    $outer.owned_receipt.job_active_after_cleanup -eq 0 -and $outer.owned_receipt.returncode -eq 0) 'Native terminal and Job0'
Assert-That ($worker.completed_cells -eq 19 -and $worker.reserved_interact_attempts -eq 2280 -and
    $worker.sentinel_pass -and $worker.monitor_stopped -and $worker.monitor_errors.Count -eq 0) 'Complete worlds/monitor'
foreach ($counter in $plan.direct_call_caps.PSObject.Properties) {
    Assert-That ($worker.direct_attempts.($counter.Name) -eq $counter.Value -and
        $worker.direct_returns.($counter.Name) -eq $counter.Value) ('Actual direct count '+$counter.Name)
}
$before = [ordered]@{}
foreach ($file in Get-ChildItem -LiteralPath $native -File | Sort-Object Name) {
    $before[$file.Name] = [ordered]@{ sha256 = Sha $file.FullName; bytes = $file.Length }
}
foreach ($pin in $worker.source_input_before_sha256.PSObject.Properties) {
    Assert-That ($worker.source_input_after_sha256.($pin.Name) -eq $pin.Value -and
        (Sha (Join-Path $root $pin.Name)) -eq $pin.Value) ('Source/input beforeafter '+$pin.Name)
}
foreach ($pin in $worker.outputs_sha256.PSObject.Properties) {
    Assert-That ($before[$pin.Name].sha256 -eq $pin.Value) ('Actual output hash '+$pin.Name)
}
$outcomes = @(Read-Json (Join-Path $native 'outcomes.json'))
$qs = @(Read-Json (Join-Path $native 'graph_source_contrasts.json'))
$ks = @(Read-Json (Join-Path $native 'conditional_lambda_contrasts.json'))
$expert = @{}
foreach ($row in @(Read-Json (Join-Path $old 'native__outcomes.json'))) {
    if ($row.graph_on) {
        $strength = if ($row.prerequisite_mechanism_on) { .55 } else { 0.0 }
        $key = Key $row.seed ([int]$row.profile.Substring(1)) $strength
        Assert-That (-not $expert.ContainsKey($key)) 'Unique old expert component'
        $expert[$key] = $row
    }
}
$learned = @{}
foreach ($row in $outcomes) {
    if ($row.graph_source -eq 'learned') {
        $key = Key $row.block $row.ability $row.mechanism_strength
        Assert-That (-not $learned.ContainsKey($key)) 'Unique new learned component'
        $learned[$key] = $row
    }
}
Assert-That ($outcomes.Count -eq 19 -and $expert.Count -eq 18 -and $learned.Count -eq 18 -and $qs.Count -eq 18 -and $ks.Count -eq 9) 'Complete finite key populations'
$qMap = @{}
foreach ($row in $qs) {
    $key = Key $row.block $row.ability $row.mechanism_strength
    Assert-That (-not $qMap.ContainsKey($key) -and $expert.ContainsKey($key) -and $learned.ContainsKey($key)) 'Q key/duplicates'
    $left, $right = $expert[$key], $learned[$key]
    Assert-That ((Same-Double $left.outcome $row.expert) -and (Same-Double $right.outcome $row.learned) -and
        (Same-Double ([double]$left.outcome-[double]$right.outcome) $row.expert_minus_learned)) 'Q exact binary64 subtraction/components'
    Assert-That ($left.latent_identity -eq $right.latent_identity -and
        $left.random_stream_identity -eq $right.uniform_identity) 'Matched source base/uniform identities'
    $qMap[$key] = $row
}
$kSeen = @{}
foreach ($row in $ks) {
    $key = Key $row.block $row.ability 0.0
    Assert-That (-not $kSeen.ContainsKey($key)) 'K unique block/ability'
    $off = $qMap[(Key $row.block $row.ability 0.0)].expert_minus_learned
    $on = $qMap[(Key $row.block $row.ability .55)].expert_minus_learned
    Assert-That (Same-Double ([double]$on-[double]$off) $row.lambda_difference) 'K exact binary64 subtraction'
    $kSeen[$key] = $row
}
$oldObs = Read-Rows (Join-Path $old 'native__observables.jsonl')
$newObs = Read-Rows (Join-Path $native 'observables.jsonl')
$oldOracle = Read-Rows (Join-Path $old 'native__oracle.jsonl')
$newOracle = Read-Rows (Join-Path $native 'oracle.jsonl')
Assert-That ($newObs.Count -eq 19 -and $newOracle.Count -eq 19) 'All19native trace cells'
foreach ($kind in @('observable', 'oracle')) {
    if ($kind -eq 'observable') { $historical, $fresh = $oldObs['c26'], $newObs['S01'] }
    else { $historical, $fresh = $oldOracle['c26'], $newOracle['S01'] }
    Assert-That ($historical.Count -eq 120 -and $fresh.Count -eq 120) 'Sentinel120raw rows'
    for ($i = 0; $i -lt 120; $i++) {
        Assert-That (($historical[$i].Raw.Replace('"cell_id":"c26"', '"cell_id":"S01"')) -ceq $fresh[$i].Raw) 'Sentinel raw serialized row exact after cell alias only'
    }
}
$oldEndpoints = Read-Rows (Join-Path $old 'native__oracle_endpoints.jsonl')
$newEndpoints = Read-Rows (Join-Path $native 'oracle_endpoints.jsonl')
Assert-That (($oldEndpoints['c26'][0].Raw.Replace('"cell_id":"c26"','"cell_id":"S01"')) -ceq $newEndpoints['S01'][0].Raw) 'Sentinel raw endpoint exact'
$high = @(Read-Json (Join-Path $native 'high_controls.json'))
Assert-That ($high.Count -eq 3 -and @($high | Where-Object {-not $_.trace_exact -or -not $_.endpoint_exact}).Count -eq 0) 'All3high controls'
$oldCellMap = @{}
foreach ($cell in $oldPlan.cells) {
    if ($cell.graph -eq 'full') { $oldCellMap[(Key $cell.block $cell.ability $cell.mechanism_strength)] = $cell.cell_id }
}
$trajectoryPairs = [Collections.Generic.List[object]]::new()
foreach ($cell in @($plan.cells | Where-Object graph -eq 'learned')) {
    $key = Key $cell.block $cell.ability $cell.mechanism_strength
    $left, $right = $oldObs[$oldCellMap[$key]], $newObs[$cell.cell_id]
    Assert-That ($left.Count -eq 120 -and $right.Count -eq 120) 'Paired120ordinal rows, not shared-query assumption'
    $itemDiff = $conceptDiff = $labelDiff = 0
    $firstItem = $firstLabel = $null
    for ($i = 0; $i -lt 120; $i++) {
        $a, $b = $left[$i].Parsed, $right[$i].Parsed
        Assert-That ($a.step -eq $i -and $b.step -eq $i -and
            $a.query.timestamp_ns -eq $b.query.timestamp_ns -and $a.query.timestamp_iso -eq $b.query.timestamp_iso) 'Exact shared clock/ordinal address'
        if ($a.query.question -cne $b.query.question) { $itemDiff++; if ($null -eq $firstItem) { $firstItem = $i } }
        if ($a.query.concept -cne $b.query.concept) { $conceptDiff++ }
        if ($a.correct -ne $b.correct) { $labelDiff++; if ($null -eq $firstLabel) { $firstLabel = $i } }
    }
    $trajectoryPairs.Add([pscustomobject][ordered]@{ block=$cell.block; ability=$cell.ability; mechanism_strength=$cell.mechanism_strength;
        old_expert_cell=$oldCellMap[$key]; learned_cell=$cell.cell_id; ordinal_rows=120; question_id_differences=$itemDiff;
        question_id_difference_fraction=([double]$itemDiff/120.0); concept_differences=$conceptDiff; observed_label_differences=$labelDiff;
        first_question_difference_step0=$firstItem; first_question_difference_ordinal1=$(if($null -eq $firstItem){$null}else{$firstItem+1});
        first_label_difference_step0=$firstLabel; labels_equal_before_first_question_difference=($null -eq $firstLabel -or ($null -ne $firstItem -and $firstLabel -ge $firstItem));
        interpretation='Descriptive ordinal overlap; after divergence these are different served queries/history, no paired responseLL.' })
}
$initial = @(Get-ChildItem -LiteralPath $native -Filter 'initial-*.json' -File)
Assert-That ($initial.Count -eq 19) 'All19initial snapshots'
$initialRows = @($initial | ForEach-Object { Read-Json $_.FullName })
Assert-That (@($initialRows.nonedge_policy_sha256 | Sort-Object -Unique).Count -eq 1 -and
    @($initialRows | Where-Object {$null -ne $_.old_policy_initial_sha256}).Count -eq 0) 'New nonedge initial equality, oldrawhash remains missing'
foreach ($file in Get-ChildItem -LiteralPath $native -File) {
    Assert-That ((Sha $file.FullName) -eq $before[$file.Name].sha256) 'Original native outputs unchanged by verification'
}
$proof = [ordered]@{status='VERIFIED_CACHED19_Q18_K9_AND_TRAJECTORY_PAIRS_NO_MODEL_CALLS';
    verification_engine='PowerShell/.NET binary64 subtraction bit equality; raw sentinel UTF8 JSONL lines alias-only comparison';
    verifier_sha256=(Sha $PSCommandPath); outer_sha256=(Sha $outerPath); old_manifest_sha256=(Sha (Join-Path $old 'manifest.json'));
    plan_sha256=(Sha (Join-Path $prep 'rq2_learned_graph_ability01_plan.json')); q_rows=18;k_rows=9;
    exact_q_components_and_binary64_subtractions=18;exact_k_binary64_subtractions=9;
    sentinel_observable_raw_rows=120;sentinel_oracle_raw_rows=120;sentinel_raw_endpoint_exact=$true;high_controls=3;
    native_output_before_after=$before;trajectory_pairs=$trajectoryPairs.ToArray();
    initial_scope='SOURCE_RECONSTRUCTED_INITIAL_STATE;19new snapshots, oldpolicyinitialrawSHA notlogged';
    interpretation='Finite reused3seedblocks, noCI/p/qualitytruth/humanability/causalmediation claim';
    new_graph_offline_neural_solver_fits=0;new_simulator_or_policy_calls=0;old_and_new_source_artifacts_modified=$false}
[IO.File]::WriteAllText($resultPath,($proof|ConvertTo-Json -Depth 20)+"`n",[Text.UTF8Encoding]::new($false))
Write-Output ([pscustomobject]@{ status=$proof.status; path=$resultPath; sha256=Sha $resultPath })
