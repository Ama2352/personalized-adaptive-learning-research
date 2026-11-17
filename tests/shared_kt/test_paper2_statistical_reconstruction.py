"""Hồi quy ghép seed và Holm frozen, chỉ dữ liệu tổng hợp."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location('paper2_reconstruction', Path(__file__).resolve().parents[2]/
    'research_tracking/runs/paper2-statistical-reproduction-20261117-01/reproduce_statistics.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_holm_monotonic_restore_original_order():
    assert module.holm_values([.2,.01,.03,.04]) == [.2,.04,.09,.09]


def test_full_families_45_and_72_have_distinct_decisions():
    assert module.holm_values([.001]+[1.]*44)[0] == .045
    assert module.holm_values([.001]+[1.]*71)[0] == .072
    assert module.holm_values([.001]+[1.]*14)[0] == .015


@pytest.mark.parametrize('values',[[],[-.1],[1.1],[float('nan')],[float('inf')]])
def test_invalid_p_values_rejected(values):
    with pytest.raises(ValueError):
        module.holm_values(values)


def test_holm_ties_zero_and_cap():
    assert module.holm_values([0.,.02,.02,1.]) == [0.,.06,.06,1.]


@pytest.fixture
def pairs():
    rows = [dict(persona='PY',model=model,seed=str(seed),log_loss=str(value+seed/100000))
            for model,value in [('Graph-GAM-KT',.3),('GAM-KT',.4)] for seed in range(1000,1050)]
    contrast=dict(persona='PY',proposed='Graph-GAM-KT',baseline='GAM-KT',metric='log_loss')
    return rows,contrast


def test_paired_seed_delta_preserves_mean_and_pairing(pairs):
    rows,contrast=pairs
    result=module.paired_summary(list(reversed(rows)),contrast,'model')
    assert result['recomputed_raw_delta'] == pytest.approx(-.1,abs=1e-15)
    assert result['recomputed_proposed_mean']-result['recomputed_baseline_mean'] == pytest.approx(-.1)


@pytest.mark.parametrize('failure',['missing','duplicate','nan','foreign_seed'])
def test_pairing_never_silently_intersects_or_drops(pairs,failure):
    rows,contrast=pairs
    if failure=='missing':
        rows.pop()
    elif failure=='duplicate':
        rows.append(dict(rows[0]))
    elif failure=='nan':
        rows[0]['log_loss']='nan'
    else:
        rows[0]['seed']='9999'
    with pytest.raises(ValueError):
        module.paired_summary(rows,contrast,'model')
