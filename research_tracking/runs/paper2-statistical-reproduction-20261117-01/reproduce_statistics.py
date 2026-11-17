"""Tính lại mean/paired delta/Holm từ frozen Paper2, giữ p-value và CI gốc."""
import csv
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PAPER = ROOT/'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
SIM = PAPER/'frozen/simulation'
KEY = ('protocol','persona','proposed','baseline','metric')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read_csv(path):
    with path.open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))


def holm_values(values):
    """Cùng phép Holm frozen, Decimal độc lập để kiểm thứ tự/cận tích lũy."""
    numbers = [Decimal(str(value)) for value in values]
    if not numbers or any(not value.is_finite() or not 0 <= value <= 1 for value in numbers):
        raise ValueError('Finite p-values in [0,1] required')
    order = sorted(range(len(numbers)),key=lambda i:(numbers[i],i))
    result = [Decimal(0)]*len(numbers)
    running = Decimal(0)
    for rank,index in enumerate(order):
        running = max(running,min(Decimal(1),(len(numbers)-rank)*numbers[index]))
        result[index] = running
    return [float(value) for value in result]


def paired_summary(seed_rows, row, model_column):
    groups = {name:{} for name in (row['proposed'],row['baseline'])}
    for entry in seed_rows:
        if entry['persona'] != row['persona'] or entry[model_column] not in groups:
            continue
        seed = int(entry['seed'])
        group = groups[entry[model_column]]
        value = float(entry[row['metric']])
        if seed in group or not math.isfinite(value):
            raise ValueError('Duplicate or nonfinite paired seed record')
        group[seed] = value
    expected = set(range(1000,1050))
    if any(set(group) != expected for group in groups.values()):
        raise ValueError('Exact 50-seed pairing required; no intersection/drop')
    proposed = groups[row['proposed']]
    baseline = groups[row['baseline']]
    return dict(recomputed_proposed_mean=math.fsum(proposed.values())/50,
        recomputed_baseline_mean=math.fsum(baseline.values())/50,
        recomputed_raw_delta=math.fsum(proposed[seed]-baseline[seed] for seed in sorted(expected))/50)


def main():
    started = time.monotonic()
    inputs = [SIM/name for name in ('replay_metrics_by_seed.csv','closed_loop_metrics_by_seed.csv',
        'replay_paired_tests.csv','closed_loop_paired_tests.csv','all_paired_tests_holm.csv','experiment_manifest.json')]
    inputs += [PAPER/'STATISTICAL_PROTOCOL.md',PAPER/'verify_claims.py',
        ROOT/'paper2/DC KLTN0127 23520355&23521338_LeVanTuan.pdf',
        ROOT/'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md']
    before = {path.relative_to(ROOT).as_posix():dict(bytes=path.stat().st_size,sha256=sha(path)) for path in inputs}
    spec = importlib.util.spec_from_file_location('frozen_paper2_claim_verifier',PAPER/'verify_claims.py')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    result = frozen.Result()
    all_rows = read_csv(SIM/'all_paired_tests_holm.csv')
    output = []
    maximum = dict(proposed_mean=0.,baseline_mean=0.,raw_delta=0.,p_holm=0.)
    for protocol, paired_name, seed_name, model_column, metrics, size in (
        ('fixed_replay','replay_paired_tests.csv','replay_metrics_by_seed.csv','model',frozen.FIXED_METRICS,45),
        ('closed_loop','closed_loop_paired_tests.csv','closed_loop_metrics_by_seed.csv','policy',frozen.CLOSED_METRICS,72)):
        rows = read_csv(SIM/paired_name)
        seeds = read_csv(SIM/seed_name)
        frozen.verify_seed_file(seeds,model_column,seed_name,result)
        frozen.verify_family_shape(rows,protocol,metrics,size,result)
        frozen.compare_paired_files(rows,all_rows,protocol,result)
        frozen.verify_holm(rows,protocol,result)
        adjusted = holm_values([row['p_value'] for row in rows])
        for row, p_holm in zip(rows,adjusted):
            values = paired_summary(seeds,row,model_column)
            for name in ('proposed_mean','baseline_mean','raw_delta'):
                error = abs(values['recomputed_'+name]-float(row[name]))
                maximum[name] = max(maximum[name],error)
                if error > 1e-12:
                    raise ValueError('Frozen seed means/delta mismatch')
            error = abs(p_holm-float(row['p_holm']))
            maximum['p_holm'] = max(maximum['p_holm'],error)
            if error > 5e-13 or (p_holm < .05) != (row['reject_holm_05'] == 'True'):
                raise ValueError('Frozen full-family Holm mismatch')
            output.append(dict(row,**values,recomputed_p_holm=p_holm,family_size=size,
                statistical_unit='paired seed within persona',p_value_recomputed=False,ci_recomputed=False))
    assert len(output) == len(all_rows) == 117
    fields = list(output[0])
    for filename,rows in [('ALL_117_RECONCILED.csv',output),('PRIMARY_PACKAGE_CONTRAST.csv',
        [row for row in output if row['baseline']=='GAM-KT'])]:
        with (HERE/filename).open('x',encoding='utf-8',newline='') as stream:
            writer = csv.DictWriter(stream,fieldnames=fields)
            writer.writeheader();writer.writerows(rows)
    after = {path.relative_to(ROOT).as_posix():dict(bytes=path.stat().st_size,sha256=sha(path)) for path in inputs}
    if before != after:
        raise ValueError('Source artifact changed during reconstruction')
    accepted = dict(status='PASS_FROZEN_PAPER2_STATISTICAL_TABLE_RECONSTRUCTION',families={'fixed_replay':45,'closed_loop':72},
        seed_rows_each_phase=600,paired_seeds_each_persona=50,hypotheses=117,
        primary_package_rows=39,original_verifier_checks=result.checks,max_absolute_error=maximum,
        wall_seconds=time.monotonic()-started,input_pins=before,
        recomputed=['seed means','mean paired deltas','Holm full45/full72','rejection flags'],
        reused=['frozen Wilcoxon p-values','frozen3000-bootstrap confidence intervals'],
        new_simulator_runs=0,new_model_fits=0,new_bootstrap_draws=0,holdout_reads=0,
        limits_vi='Tái lập bảng thống kê từ outcome đã lưu. Chưa chạy lại simulator, Wilcoxon hoặc bootstrapCI. '
        'Cả gói context/adaptation được so với GAM-KT, chưa cô lập cạnh tiên quyết.')
    with (HERE/'ACCEPTANCE.json').open('x',encoding='utf-8') as stream:
        json.dump(accepted,stream,ensure_ascii=False,indent=2)
    print(json.dumps(accepted,ensure_ascii=False))


if __name__ == '__main__':
    main()
