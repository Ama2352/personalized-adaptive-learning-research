import importlib.util
from pathlib import Path

import numpy as np

from knowledge_tracing.paired_bootstrap import PairedFoldSufficientStats,paired_cluster_bootstrap


def load_module():
    root=Path(__file__).resolve().parents[2]
    path=root/'research_tracking/runs/junyi-outer-real-20261117-01/analyze_outer01.py'
    spec=importlib.util.spec_from_file_location('outer_analysis_test',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_primary_bootstrap_matches_existing_response_weighted_estimator():
    module=load_module()
    count=np.array([1,10,100],dtype=np.int64)
    a0_ll=np.array([.4,3.,20.]);a1_ll=np.array([.5,3.5,19.])
    a0_br=np.array([.1,1.,5.]);a1_br=np.array([.15,1.2,4.9])
    losses={model:{state:dict(log_loss=ll,brier=br) for state in ('raw','calibrated')}
        for model,ll,br in [('A0',a0_ll,a0_br),('A1',a1_ll,a1_br)]}
    actual=module.bootstrap_losses(count,losses,replicates=60,seed=42)
    zeros=np.zeros(3);bins=np.zeros((3,15))
    stats=PairedFoldSufficientStats(np.array(['a','b','c']),count,a0_ll,a1_ll,a0_br,a1_br,
        zeros,zeros,bins,bins,bins,bins)
    expected=paired_cluster_bootstrap([stats],replicates=60,seed=42)
    for row in actual:
        assert np.isclose(row['estimate'],expected[row['metric']]['estimate'],atol=1e-14)
        assert np.allclose(row['ci95'],expected[row['metric']]['ci95'],atol=1e-14)
        assert 1/61<=row['centered_bootstrap_p']<=row['holm_p']<=1
    assert np.isclose(actual[0]['estimate'],-.4/111)


def test_zero_contrasts_keep_unit_null_probability():
    module=load_module()
    count=np.array([1,2],dtype=np.int64)
    value=np.array([.5,.8])
    losses={model:{state:dict(log_loss=value,brier=value) for state in ('raw','calibrated')}
        for model in ('A0','A1','A2','A3')}
    rows=module.bootstrap_losses(count,losses,replicates=20,seed=42)
    assert len(rows)==24
    assert all(row['estimate']==0 and row['ci95']==[0,0] and row['holm_p']==1
        and row['centered_bootstrap_p']==1 for row in rows)
