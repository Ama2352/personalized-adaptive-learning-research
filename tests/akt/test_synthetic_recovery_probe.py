"""Kiểm probe recovery tổng hợp; actualCUDA vẫn cần Colab runtime."""

from pathlib import Path
import runpy

import pytest
import torch


@pytest.fixture
def module():
    return runpy.run_path('scripts/akt/synthetic_recovery_probe.py')


@pytest.mark.parametrize('name', ['dataset/run','artifacts/bkt_baseline/run','experiments/akt/results/nested/run'])
def test_recovery_probe_rejects_output_outside_direct_results_child(module, name):
    with pytest.raises(ValueError,match='direct child'):
        module['validate_output'](Path(name))


def test_state_comparison_checks_optimizer_rng_shape_and_numeric_tolerance(module):
    compare=module['compare_tree']
    base={'model':torch.tensor([1.,2.]),'optimizer':{'step':torch.tensor(5.)},
          'rng':[torch.tensor([1,2],dtype=torch.uint8)],'metadata':('fixed',17)}
    assert compare(base,base,atol=0,rtol=0)==0
    other={**base,'model':torch.tensor([1.000001,2.])}
    with pytest.raises(ValueError,match='floating'):
        compare(base,other,atol=0,rtol=0)
    assert compare(base,other,atol=1e-5,rtol=1e-5)>0
    bad={**base,'rng':[torch.tensor([1,3],dtype=torch.uint8)]}
    with pytest.raises(ValueError,match='RNG'):
        compare(base,bad,atol=1,rtol=1)
    with pytest.raises(ValueError,match='shape'):
        compare(torch.ones(2),torch.ones(3),atol=1,rtol=1)
    with pytest.raises(ValueError,match='nonfinite'):
        compare(torch.tensor([float('nan')]),torch.tensor([float('nan')]),atol=1,rtol=1)


def test_invalid_device_fails_before_creating_output(module):
    with pytest.raises(ValueError,match='explicit cpu/cuda'):
        module['run_probe'](Path('experiments/akt/results/unused-invalid-device'),'automatic')
